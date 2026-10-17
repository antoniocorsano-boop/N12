#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
AZ = C / "M1L_ARCHITECTURAL_ENVELOPE_LOAD_ZONES_v1.csv"
SPECIAL = C / "M1_SPECIAL_CONFIGURATION_LOADS_REGISTER_v1.csv"
EAVE = C / "M1A_G5_EAVE_CANTILEVER_ENDS_CURRENT_v1.csv"
GFI = C / "M1F_GROUND_FLOOR_INTERFACE_CURRENT_v1.csv"
LP = C / "M1L_LOAD_PATH_CLASSIFICATION_CURRENT_v1.csv"
DELTA = C / "M1L_HISTORICAL_VS_ASBUILT_LOAD_DELTA_REGISTER_v1.csv"
GATE = C / "M1L_LOADS_GATE_v1.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def finish(errors: list[str], warnings: list[str], summary: dict[str, object]) -> int:
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-L load validation: {status}")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [AZ, SPECIAL, EAVE, GFI, LP, DELTA, GATE]
    for path in required:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    az = read(AZ)
    special = read(SPECIAL)
    eave = read(EAVE)
    gfi = read(GFI)
    lp = read(LP)
    delta = read(DELTA)
    gate = read(GATE)

    if len(az) != 6:
        errors.append(f"expected 6 architectural load zones, got {len(az)}")
    if len(special) != 8:
        errors.append(f"expected 8 special-configuration rows, got {len(special)}")
    if len(eave) != 8:
        errors.append(f"expected 8 G5 eave overhang ends, got {len(eave)}")
    if len(lp) != 7:
        errors.append(f"expected 7 load-path classification rows, got {len(lp)}")
    if len(delta) != 6:
        errors.append(f"expected 6 historical-vs-as-built delta rows, got {len(delta)}")

    az_ids = {row["zone_id"].strip() for row in az}
    classified_az = {row["source_zone_id"].strip() for row in lp if row["source_zone_id"].strip()}
    if classified_az != az_ids:
        errors.append(
            f"architectural zone coverage mismatch: missing={sorted(az_ids - classified_az)} extra={sorted(classified_az - az_ids)}"
        )

    for row in lp:
        lid = row["load_path_id"].strip()
        if row["numeric_load_ready"].strip() != "NO":
            errors.append(f"{lid}: numeric_load_ready must remain NO until numerical evidence gate is completed")
        if not row["structural_support_class"].strip():
            errors.append(f"{lid}: missing structural support classification")
        if not row["residual"].strip():
            errors.append(f"{lid}: missing explicit residual")
        if not row["model_guard"].strip():
            errors.append(f"{lid}: missing model guard")

    eave_doc_hosts = 0
    for row in eave:
        if row["overhang_presence"].strip() == "DOC" and row["host_member_id"].strip():
            eave_doc_hosts += 1
        if row["length_evidence"].strip() == "DOC":
            errors.append(f"{row['cantilever_id']}: overhang length must not be DOC in current evidence state")
    if eave_doc_hosts != 8:
        errors.append(f"expected 8 DOC eave ends with host members, got {eave_doc_hosts}")

    gfi_by = {row["interface_id"].strip(): row for row in gfi}
    pt_path = gfi_by.get("M1F-GFI-006", {})
    if pt_path.get("load_or_geometry_state", "").strip() != "OPEN_LOAD_PATH":
        errors.append("M1F-GFI-006 must remain OPEN_LOAD_PATH")
    lp_by = {row["load_path_id"].strip(): row for row in lp}
    lp_pt = lp_by.get("M1L-LP-001", {})
    if "Do not apply the complete" not in lp_pt.get("model_guard", ""):
        errors.append("PT load-path guard against whole-build-up structural loading is missing")

    for row in delta:
        did = row["delta_id"].strip()
        if row["historical_omission_direct_evidence"].strip() != "NO":
            errors.append(f"{did}: historical omission direct evidence must remain NO until primary calculation evidence is registered")
        if row["numeric_delta_ready"].strip() != "NO":
            errors.append(f"{did}: numerical historical-vs-as-built delta is not ready")
        if not row["symbolic_delta_rule"].strip():
            errors.append(f"{did}: missing symbolic delta rule")
        if not row["model_rule"].strip():
            errors.append(f"{did}: missing historical/as-built separation rule")

    gate_by = {row["check_id"].strip(): row for row in gate}
    expected_gate_actuals = {
        "M1L-G01": "6",
        "M1L-G02": "8",
        "M1L-G03": "8",
        "M1L-G04": "NO",
        "M1L-G05": "0",
        "M1L-G06": "0",
        "M1L-G07": "YES",
        "M1L-G08": "YES",
        "M1L-G09": "NO",
        "M1L-GATE": "PASS_SEMANTIC_LOAD_PATH_AND_DELTA_FRAMEWORK_WITH_NUMERIC_WATCH",
    }
    for check_id, expected in expected_gate_actuals.items():
        actual = gate_by.get(check_id, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{check_id}: expected actual={expected!r}, got {actual!r}")

    warnings.extend(
        [
            "numerical Gk/Qk/mass assignment is not yet authorized by this semantic gate",
            "PT fill/pour/screed structural transfer remains open and must not be globally loaded onto the frame/foundations",
            "reported historical omissions remain conditional until direct primary calculation evidence is registered",
            "G5 eave overhang presence/hosts are DOC but the reported 1.50 m length remains RIF",
            "balcony/terrace/stair-tower construction layers and tributary structural geometry remain evidence residuals",
        ]
    )

    return finish(
        errors,
        warnings,
        {
            "architectural_load_zones": len(az),
            "special_configuration_rows": len(special),
            "load_path_rows": len(lp),
            "delta_rows": len(delta),
            "g5_eave_doc_hosts": eave_doc_hosts,
            "numeric_load_rows_ready": sum(1 for row in lp if row["numeric_load_ready"].strip() == "YES"),
            "numeric_delta_rows_ready": sum(1 for row in delta if row["numeric_delta_ready"].strip() == "YES"),
        },
    )


if __name__ == "__main__":
    sys.exit(main())
