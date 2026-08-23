#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
GFI = C / "M1F_GROUND_FLOOR_INTERFACE_CURRENT_v1.csv"
GFI_GATE = C / "M1F_GROUND_FLOOR_INTERFACE_GATE_v1.csv"
AD = C / "M1F_AD_HISTORICAL_MODEL_DELTA_AUDIT_v1.csv"
AD_GATE = C / "M1F_AD_HISTORICAL_MODEL_DELTA_GATE_v1.csv"
GEO = C / "M1F_CURRENT_GEOTECHNICAL_REQUIREMENTS_v1.csv"
GEO_GATE = C / "M1F_CURRENT_GEOTECHNICAL_GATE_v1.csv"
ELEV_GATE = C / "M1F_FOUNDATION_ELEVATION_GATE_v1.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [GFI, GFI_GATE, AD, AD_GATE, GEO, GEO_GATE, ELEV_GATE]
    for p in required:
        if not p.exists():
            errors.append(f"missing artifact: {p.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    gfi = read(GFI)
    gfi_gate = read(GFI_GATE)
    ad = read(AD)
    ad_gate = read(AD_GATE)
    geo = read(GEO)
    geo_gate = read(GEO_GATE)
    elev_gate = read(ELEV_GATE)

    if len(gfi) != 7:
        errors.append(f"expected 7 ground-floor interface rows, got {len(gfi)}")
    gfi_by = {r["interface_id"].strip(): r for r in gfi}
    for rid in ("M1F-GFI-003", "M1F-GFI-004", "M1F-GFI-005"):
        r = gfi_by.get(rid, {})
        for field in ("thickness_m", "unit_weight_kN_m3", "surface_load_kN_m2"):
            if r.get(field, "").strip():
                errors.append(f"{rid}: {field} must remain ND/blank until evidenced")
    if gfi_by.get("M1F-GFI-006", {}).get("load_or_geometry_state", "").strip() != "OPEN_LOAD_PATH":
        errors.append("ground-floor load path must remain explicitly OPEN_LOAD_PATH")
    if "ZF_COMMON" not in gfi_by.get("M1F-GFI-001", {}).get("model_rule", ""):
        errors.append("ground-floor interface lost symbolic ZF_COMMON foundation rule")

    gg = {r["check_id"].strip(): r for r in gfi_gate}
    expected_gfi = {
        "M1F-GFI-G03": "0",
        "M1F-GFI-G04": "0",
        "M1F-GFI-G05": "NO",
        "M1F-GFI-G06": "NO",
        "M1F-GFI-G07": "NO",
        "M1F-GFI-GATE": "PASS_PARAMETRIC_GROUND_FLOOR_INTERFACE_WITH_LOAD_AND_DATUM_WATCH",
    }
    for cid, expected in expected_gfi.items():
        if gg.get(cid, {}).get("actual", "").strip() != expected:
            errors.append(f"{cid}: expected actual={expected!r}")

    if len(ad) != 6:
        errors.append(f"expected 6 a-d audit rows, got {len(ad)}")
    adg = {r["check_id"].strip(): r for r in ad_gate}
    if adg.get("M1F-AD-G01", {}).get("actual", "").strip() != "CONFIRMED":
        errors.append("a-d documented/as-built foundation presence must remain CONFIRMED")
    if adg.get("M1F-AD-G03", {}).get("actual", "").strip() != "NO":
        errors.append("a-d must not be removed from current/as-built model")
    if adg.get("M1F-AD-G04", {}).get("actual", "").strip() != "NO":
        errors.append("historical omission must remain not directly proven until source evidence is registered")
    if adg.get("M1F-AD-GATE", {}).get("actual", "").strip() != "PASS_BUILT_PRESENCE_WITH_HISTORICAL_OMISSION_WATCH":
        errors.append("a-d historical delta gate state mismatch")

    if len(geo) != 10:
        errors.append(f"expected 10 geotechnical requirement rows, got {len(geo)}")
    geog = {r["check_id"].strip(): r for r in geo_gate}
    if geog.get("M1F-GEO-G03", {}).get("actual", "").strip() != "NO":
        errors.append("historical allowable pressure must not be used as current design resistance")
    if geog.get("M1F-GEO-G08", {}).get("actual", "").strip() != "NO":
        errors.append("epsilon=1 must not be converted directly to solver soil stiffness")
    if geog.get("M1F-GEO-GATE", {}).get("actual", "").strip() != "REQUIREMENTS_DEFINED_CURRENT_GEOTECHNICAL_EVIDENCE_OPEN":
        errors.append("current geotechnical gate state mismatch")

    eg = {r["check_id"].strip(): r for r in elev_gate}
    for cid, expected in (("M1F-ELEV-G07", "38"), ("M1F-ELEV-G08", "58")):
        if eg.get(cid, {}).get("actual", "").strip() != expected:
            errors.append(f"{cid}: symbolic 3D inventory metric missing or changed")
    if eg.get("M1F-ELEV-G05", {}).get("actual", "").strip() != "NO":
        errors.append("numeric ZF_COMMON must remain unregistered")

    warnings.extend([
        "numeric ZF_COMMON remains ND pending G1/local-ground datum evidence",
        "ground-floor layer thicknesses, unit weights and structural load path remain open",
        "a-d historical calculation omission remains reported but not directly source-proven",
        "current geotechnical site parameters remain open",
    ])

    return finish(errors, warnings, {
        "ground_floor_interface_rows": len(gfi),
        "ad_audit_rows": len(ad),
        "geotechnical_requirement_rows": len(geo),
        "symbolic_nodes_3d": eg.get("M1F-ELEV-G07", {}).get("actual", ""),
        "symbolic_members_3d": eg.get("M1F-ELEV-G08", {}).get("actual", ""),
        "numeric_ZF_COMMON": "ND",
    })


def finish(errors, warnings, summary):
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-F ground-interface/residual validation: {status}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
