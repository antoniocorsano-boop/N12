#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
GFI = C / "M1F_GROUND_FLOOR_INTERFACE_CURRENT_v1.csv"
GFI_GATE = C / "M1F_GROUND_FLOOR_INTERFACE_GATE_v1.csv"
GFS = C / "M1F_GROUND_FLOOR_BUILDUP_SOURCE_AVAILABILITY_v1.csv"
AD = C / "M1F_AD_HISTORICAL_MODEL_DELTA_AUDIT_v1.csv"
AD_GATE = C / "M1F_AD_HISTORICAL_MODEL_DELTA_GATE_v1.csv"
HCS = C / "M1F_HISTORICAL_CALC_SOURCE_AVAILABILITY_v1.csv"
GEO = C / "M1F_CURRENT_GEOTECHNICAL_REQUIREMENTS_v1.csv"
GEO_GATE = C / "M1F_CURRENT_GEOTECHNICAL_GATE_v1.csv"
GSA = C / "M1F_GEOTECHNICAL_SOURCE_AVAILABILITY_v1.csv"
EXT = C / "M1F_EXTERNAL_EVIDENCE_ACQUISITION_QUEUE_v1.csv"
ELEV_GATE = C / "M1F_FOUNDATION_ELEVATION_GATE_v1.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [GFI, GFI_GATE, GFS, AD, AD_GATE, HCS, GEO, GEO_GATE, GSA, EXT, ELEV_GATE]
    for p in required:
        if not p.exists():
            errors.append(f"missing artifact: {p.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    gfi = read(GFI)
    gfi_gate = read(GFI_GATE)
    gfs = read(GFS)
    ad = read(AD)
    ad_gate = read(AD_GATE)
    hcs = read(HCS)
    geo = read(GEO)
    geo_gate = read(GEO_GATE)
    gsa = read(GSA)
    ext = read(EXT)
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
        "M1F-GFI-G08": "YES",
        "M1F-GFI-G09": "NO",
        "M1F-GFI-GATE": "PASS_PARAMETRIC_GROUND_FLOOR_INTERFACE_WITH_LOAD_AND_DATUM_WATCH",
    }
    for cid, expected in expected_gfi.items():
        if gg.get(cid, {}).get("actual", "").strip() != expected:
            errors.append(f"{cid}: expected actual={expected!r}")

    if len(gfs) != 6:
        errors.append(f"expected 6 PT build-up source-availability rows, got {len(gfs)}")
    gfs_by = {r["search_id"].strip(): r for r in gfs}
    gfs_status = gfs_by.get("M1F-GFS-006", {})
    if gfs_status.get("evidence_state", "").strip() != "SOURCE_AVAILABILITY_AUDIT_COMPLETE":
        errors.append("PT build-up source search must remain completed for the current inventory")
    if "CLOSED_CURRENT_INVENTORY" not in gfs_status.get("decision", ""):
        errors.append("PT build-up source search must remain closed until source inventory changes")
    if "Never transfer" not in gfs_by.get("M1F-GFS-004", {}).get("decision", ""):
        errors.append("foundation-to-PT concrete-property non-transfer guard is missing")

    if len(ad) != 6:
        errors.append(f"expected 6 a-d audit rows, got {len(ad)}")
    adg = {r["check_id"].strip(): r for r in ad_gate}
    if adg.get("M1F-AD-G01", {}).get("actual", "").strip() != "CONFIRMED":
        errors.append("a-d documented/as-built foundation presence must remain CONFIRMED")
    if adg.get("M1F-AD-G03", {}).get("actual", "").strip() != "NO":
        errors.append("a-d must not be removed from current/as-built model")
    if adg.get("M1F-AD-G04", {}).get("actual", "").strip() != "NO":
        errors.append("historical omission must remain not directly proven until source evidence is registered")
    if adg.get("M1F-AD-G07", {}).get("actual", "").strip() != "YES":
        errors.append("current repository source inventory for historical a-d omission evidence must remain completed")
    if adg.get("M1F-AD-G08", {}).get("actual", "").strip() != "NO":
        errors.append("new primary historical calculation source must remain NO until one is explicitly registered")
    if adg.get("M1F-AD-GATE", {}).get("actual", "").strip() != "PASS_BUILT_PRESENCE_WITH_HISTORICAL_OMISSION_WATCH":
        errors.append("a-d historical delta gate state mismatch")

    if len(hcs) != 5:
        errors.append(f"expected 5 historical calculation source-availability rows, got {len(hcs)}")
    hby = {r["search_id"].strip(): r for r in hcs}
    hs = hby.get("M1F-HCS-005", {})
    hs_text = (hs.get("decision", "") + " " + hs.get("result", "")).lower()
    if "not_directly_proven" not in hs_text and "not directly proven" not in hs_text:
        errors.append("historical source availability audit must keep a-d omission not directly proven")
    if hs.get("evidence_state", "").strip() != "DOC_BUILT_PLUS_ND_HISTORICAL_CALC_SOURCE":
        errors.append("historical source availability evidence state changed unexpectedly")

    if len(geo) != 10:
        errors.append(f"expected 10 geotechnical requirement rows, got {len(geo)}")
    geog = {r["check_id"].strip(): r for r in geo_gate}
    expected_geo = {
        "M1F-GEO-G03": "NO",
        "M1F-GEO-G08": "NO",
        "M1F-GEO-G10": "YES",
        "M1F-GEO-G11": "NO",
        "M1F-GEO-GATE": "REQUIREMENTS_DEFINED_CURRENT_GEOTECHNICAL_EVIDENCE_OPEN",
    }
    for cid, expected in expected_geo.items():
        if geog.get(cid, {}).get("actual", "").strip() != expected:
            errors.append(f"{cid}: expected actual={expected!r}")

    if len(gsa) != 5:
        errors.append(f"expected 5 geotechnical source-availability rows, got {len(gsa)}")
    gsa_by = {r["search_id"].strip(): r for r in gsa}
    gsa_status = gsa_by.get("M1F-GSA-005", {})
    if gsa_status.get("evidence_state", "").strip() != "SOURCE_AVAILABILITY_AUDIT_COMPLETE":
        errors.append("geotechnical source search must remain completed for current inventory")
    if "CLOSED_CURRENT_INVENTORY" not in gsa_status.get("decision", ""):
        errors.append("geotechnical repository search must remain closed until source inventory changes")

    if len(ext) != 8:
        errors.append(f"expected 8 external-evidence queue rows, got {len(ext)}")
    ext_by = {r["task_id"].strip(): r for r in ext}
    gate = ext_by.get("M1F-EXT-GATE", {})
    if gate.get("status", "").strip() != "QUEUE_READY":
        errors.append("external evidence queue gate must remain QUEUE_READY")
    if "No unresolved M1-F item triggers restart" not in gate.get("promotion_condition", ""):
        errors.append("external evidence queue lost anti-restart promotion rule")
    required_tasks = {f"M1F-EXT-{i:03d}" for i in range(1, 8)} | {"M1F-EXT-GATE"}
    if set(ext_by) != required_tasks:
        errors.append("external evidence queue task IDs changed or are incomplete")
    for tid in ("M1F-EXT-001", "M1F-EXT-002", "M1F-EXT-003", "M1F-EXT-006", "M1F-EXT-007"):
        if not ext_by.get(tid, {}).get("acceptable_evidence", "").strip():
            errors.append(f"{tid}: acceptable evidence criteria missing")

    eg = {r["check_id"].strip(): r for r in elev_gate}
    for cid, expected in (("M1F-ELEV-G07", "38"), ("M1F-ELEV-G08", "58")):
        if eg.get(cid, {}).get("actual", "").strip() != expected:
            errors.append(f"{cid}: symbolic 3D inventory metric missing or changed")
    if eg.get("M1F-ELEV-G05", {}).get("actual", "").strip() != "NO":
        errors.append("numeric ZF_COMMON must remain unregistered")

    warnings.extend([
        "numeric ZF_COMMON remains ND pending direct G1/foundation datum evidence",
        "PT layer thicknesses/unit weights and structural load path remain external-evidence residuals; current source search is closed",
        "a-d historical calculation omission remains reported but not directly source-proven; current repository search is closed until a new primary source is registered",
        "current geotechnical site parameters remain external-document/new-investigation residuals; current repository search is closed",
    ])

    return finish(errors, warnings, {
        "ground_floor_interface_rows": len(gfi),
        "pt_build_up_source_inventory_rows": len(gfs),
        "ad_audit_rows": len(ad),
        "historical_source_inventory_rows": len(hcs),
        "geotechnical_requirement_rows": len(geo),
        "geotechnical_source_inventory_rows": len(gsa),
        "external_evidence_queue_rows": len(ext),
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
