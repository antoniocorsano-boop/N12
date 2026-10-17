#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
EAVE = C / "M1A_G5_EAVE_CANTILEVER_ENDS_CURRENT_v1.csv"
GATE = C / "M1A_G5_EAVE_REINFORCEMENT_GATE_v1.csv"
RIDGE_GRONDA = C / "M1A_G5_RIDGE_GRONDA_INTERPRETATION_CURRENT_v1.csv"
BALCONY_AUDIT = C / "M1A_BALCONY_CORNICE_REINFORCEMENT_SOURCE_AUDIT_v1.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def finish(errors: list[str], warnings: list[str], summary: dict[str, object]) -> int:
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-A G5 eave reinforcement validation: {status}")
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
    for path in [EAVE, GATE, RIDGE_GRONDA, BALCONY_AUDIT]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    eave = read(EAVE)
    gate = read(GATE)
    ridge_gronda = read(RIDGE_GRONDA)
    balcony_audit = read(BALCONY_AUDIT)

    if len(eave) != 8:
        errors.append(f"expected 8 eave ends, got {len(eave)}")

    doc_presence = 0
    host_bindings = 0
    sec_30x50 = 0
    stirrup_phi6_20 = 0
    group_bindings = 0
    doc_lengths = 0
    terrace_closed = 0
    for row in eave:
        cid = row["cantilever_id"].strip()
        if row["overhang_presence"].strip() == "DOC":
            doc_presence += 1
        if row["host_member_id"].strip():
            host_bindings += 1
        if row["section_cm"].strip() == "30x50":
            sec_30x50 += 1
        if row["stirrups"].strip() == "phi6/20":
            stirrup_phi6_20 += 1
        if row["reinforcement_binding"].strip() == "TAV06A_GROUP_SCHEDULE":
            group_bindings += 1
        if row["length_evidence"].strip() == "DOC":
            doc_lengths += 1
        if row["terrace_binding_status"].strip() not in {"OPEN", ""}:
            terrace_closed += 1
        if row["length_evidence"].strip() != "RIF_USER_QUALIFIED":
            errors.append(f"{cid}: current 1.50 m length evidence must remain RIF_USER_QUALIFIED")

    if doc_presence != 8:
        errors.append(f"expected 8 DOC overhang-presence rows, got {doc_presence}")
    if host_bindings != 8:
        errors.append(f"expected 8 host-member bindings, got {host_bindings}")
    if sec_30x50 != 8:
        errors.append(f"expected 8 section 30x50 bindings, got {sec_30x50}")
    if stirrup_phi6_20 != 8:
        errors.append(f"expected 8 phi6/20 stirrup bindings, got {stirrup_phi6_20}")
    if group_bindings != 8:
        errors.append(f"expected 8 TAV06A group reinforcement bindings, got {group_bindings}")
    if doc_lengths != 0:
        errors.append("no eave overhang 1.50 m length may be promoted to DOC at current evidence state")

    gronda_rows = [r for r in ridge_gronda if r["feature_type"].strip() == "GRONDA_CORNICE_EDGE_DETAIL"]
    if len(gronda_rows) != 1:
        errors.append(f"expected one separate gronda/cornice edge-detail row, got {len(gronda_rows)}")
    elif "do not merge" not in gronda_rows[0]["model_action"].lower():
        errors.append("gronda/cornice object must remain explicitly separate from inclined rafter overhangs")

    bc_by = {r["audit_id"].strip(): r for r in balcony_audit}
    g5_bc = bc_by.get("M1A-BC-003", {})
    if "does not by itself document" not in g5_bc.get("reinforcement_search_result", ""):
        errors.append("G5 source audit must preserve the no-generalization rule from beam overhang reinforcement to slab/gronda objects")

    gate_by = {row["check_id"].strip(): row for row in gate}
    expected = {
        "M1A-EAV-G01": "8",
        "M1A-EAV-G02": "8",
        "M1A-EAV-G03": "8",
        "M1A-EAV-G04": "8",
        "M1A-EAV-G05": "8",
        "M1A-EAV-G06": "8",
        "M1A-EAV-G07": "0",
        "M1A-EAV-G08": "NO",
        "M1A-EAV-G09": "NO",
        "M1A-EAV-GATE": "PASS_REINFORCEMENT_HOST_BINDING_WITH_GEOMETRY_LOAD_WATCH",
    }
    for check_id, value in expected.items():
        actual = gate_by.get(check_id, {}).get("actual", "").strip()
        if actual != value:
            errors.append(f"{check_id}: expected actual={value!r}, got {actual!r}")

    warnings.extend([
        "the reported 1.50 m overhang length remains RIF_USER_QUALIFIED",
        "terrace/interior tributary binding remains open in M1-L",
        "gronda/cornice edge reinforcement remains a separate partially bound object and is not generalized from rafter ends",
    ])

    return finish(errors, warnings, {
        "eave_ends": len(eave),
        "doc_overhang_presence": doc_presence,
        "host_member_bindings": host_bindings,
        "section_30x50_bindings": sec_30x50,
        "phi6_20_bindings": stirrup_phi6_20,
        "reinforcement_group_bindings": group_bindings,
        "doc_1_50m_lengths": doc_lengths,
        "terrace_bindings_closed": terrace_closed,
    })


if __name__ == "__main__":
    sys.exit(main())
