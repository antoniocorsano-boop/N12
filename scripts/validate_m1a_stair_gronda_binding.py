#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
STAIR = C / "M1A_STAIR_TOWER_SUBSYSTEM_CURRENT_v1.csv"
COL = C / "M1A_COLUMN_REINFORCEMENT_FAMILIES_v1.csv"
STAIR_GATE = C / "M1A_STAIR_TOWER_BINDING_GATE_v1.csv"
GRONDA = C / "M1A_G5_RIDGE_GRONDA_INTERPRETATION_CURRENT_v1.csv"
EAVE = C / "M1A_G5_EAVE_CANTILEVER_ENDS_CURRENT_v1.csv"
GRONDA_GATE = C / "M1A_G5_GRONDA_CORNICE_BINDING_GATE_v1.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def finish(errors: list[str], warnings: list[str], summary: dict[str, object]) -> int:
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-A stair/gronda binding validation: {status}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for path in [STAIR, COL, STAIR_GATE, GRONDA, EAVE, GRONDA_GATE]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    stair = read(STAIR)
    col = read(COL)
    stair_gate = read(STAIR_GATE)
    gronda = read(GRONDA)
    eave = read(EAVE)
    gronda_gate = read(GRONDA_GATE)

    if len(stair) != 6:
        errors.append(f"expected 6 stair/torrino rows, got {len(stair)}")
    stair_by = {r["item_id"].strip(): r for r in stair}
    required_stair = {"STAIR-001", "STAIR-002", "STAIR-003", "TORRINO-001", "TORRINO-002", "TORRINO-003"}
    if set(stair_by) != required_stair:
        errors.append(f"stair/torrino id set mismatch: {sorted(stair_by)}")

    if stair_by.get("STAIR-001", {}).get("evidence_status", "").strip() != "DOC_CARPENTERIA":
        errors.append("STAIR-001 geometry context must remain DOC_CARPENTERIA")
    special_candidates = [r for r in stair if r["model_class"].strip() == "SPECIAL_STAIR_MEMBER_CANDIDATE"]
    if len(special_candidates) != 2:
        errors.append(f"expected 2 recurring special stair-member candidates, got {len(special_candidates)}")
    for r in special_candidates:
        text = " ".join(r.values()).lower()
        if "20-21" not in text:
            errors.append(f"{r['item_id']}: recurring special candidate lost 20-21 identity")
        if "ordinary" not in text:
            errors.append(f"{r['item_id']}: anti-ordinary-planar-member guard missing")

    torrino2 = stair_by.get("TORRINO-002", {})
    if torrino2.get("section_fact", "").strip() != "30x40":
        errors.append("TORRINO-002 must retain documentary 30x40 family")
    if torrino2.get("current_state", "").strip() != "FAMILY_DOC_BINDING_OPEN":
        errors.append("TORRINO-002 exact member binding must remain open")
    if "not proof that every 30x40" not in torrino2.get("note", ""):
        errors.append("TORRINO-002 must retain no-blanket-assignment guard")

    v30 = [r for r in col if r["family_id"].strip() == "T7-V-02"]
    if len(v30) != 1:
        errors.append(f"expected exactly one T7-V-02 family row, got {len(v30)}")
    else:
        if v30[0]["section_drawn_cm"].strip() != "30x40":
            errors.append("T7-V-02 section must be 30x40")
        if v30[0]["evidence_status"].strip() != "DOC":
            errors.append("T7-V-02 must remain DOC")
        if v30[0]["validation_state"].strip() != "DIRECT_NUMBERED":
            errors.append("T7-V-02 must remain DIRECT_NUMBERED")

    sg = {r["check_id"].strip(): r for r in stair_gate}
    expected_sg = {
        "M1A-STR-G01": "6",
        "M1A-STR-G02": "YES",
        "M1A-STR-G03": "2",
        "M1A-STR-G04": "NO",
        "M1A-STR-G05": "YES",
        "M1A-STR-G06": "YES",
        "M1A-STR-G07": "NO",
        "M1A-STR-G08": "NO",
        "M1A-STR-G09": "NO",
        "M1A-STR-G10": "NO",
        "M1A-STR-GATE": "PASS_DEDICATED_SUBSYSTEM_IDENTIFIED_WITH_3D_AND_FOOTPRINT_WATCH",
    }
    for cid, expected in expected_sg.items():
        actual = sg.get(cid, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{cid}: expected actual={expected!r}, got {actual!r}")

    ridge_rows = [r for r in gronda if r["feature_type"].strip().startswith("RIDGE_LINE_")]
    if len(ridge_rows) != 3:
        errors.append(f"expected 3 ridge-fold rows, got {len(ridge_rows)}")
    for r in ridge_rows:
        if r["structural_member_decision"].strip() != "NO_SEPARATE_FRAME_MEMBER_BY_CURRENT_SOURCE":
            errors.append(f"{r['item_id']}: ridge line must remain non-member geometry")

    edge = [r for r in gronda if r["feature_type"].strip() == "GRONDA_CORNICE_EDGE_DETAIL"]
    if len(edge) != 1:
        errors.append(f"expected one direct gronda/cornice edge detail, got {len(edge)}")
    else:
        e = edge[0]
        if "120 cm" not in e["geometry_fact"] or "15 cm" not in e["geometry_fact"]:
            errors.append("direct gronda/cornice detail must retain 120 cm projection and 15 cm thickness")
        if "6phi10" not in e["reinforcement_fact"] or "phi6" not in e["reinforcement_fact"]:
            errors.append("direct gronda/cornice detail must retain 6phi10 and phi6 reinforcement facts")
        if e["current_state"].strip() != "PARTIAL_BINDING_OPEN":
            errors.append("gronda/cornice extent must remain PARTIAL_BINDING_OPEN")
        if "do not merge" not in e["model_action"].lower():
            errors.append("gronda/cornice detail must stay separate from inclined rafter overhangs")

    if len(eave) != 8:
        errors.append(f"expected 8 separately inventoried eave rafter ends, got {len(eave)}")

    gg = {r["check_id"].strip(): r for r in gronda_gate}
    expected_gg = {
        "M1A-GRD-G01": "3",
        "M1A-GRD-G02": "1",
        "M1A-GRD-G03": "120",
        "M1A-GRD-G04": "15",
        "M1A-GRD-G05": "6phi10",
        "M1A-GRD-G06": "long_phi6",
        "M1A-GRD-G07": "YES",
        "M1A-GRD-G08": "NO",
        "M1A-GRD-G09": "NO",
        "M1A-GRD-GATE": "PASS_DIRECT_GRONDA_DETAIL_WITH_EXTENT_BINDING_WATCH",
    }
    for cid, expected in expected_gg.items():
        actual = gg.get(cid, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{cid}: expected actual={expected!r}, got {actual!r}")

    warnings.extend([
        "recurring stair 20-21 candidates remain unbound in exact 3D role/Z path",
        "30x40 torrino family is DOC but exact tower support subset is not yet plan/section-bound",
        "torrino load/mass tributaries remain downstream M1-L residuals",
        "the direct 120x15 gronda/cornice detail is DOC but its occurrence/extent along the three gronda sets remains open",
        "no generic perimeter reinforcement is inferred from the single direct gronda/cornice detail",
    ])

    return finish(errors, warnings, {
        "stair_torrino_rows": len(stair),
        "special_20_21_candidates": len(special_candidates),
        "direct_v_order_30x40_family_rows": len(v30),
        "ridge_fold_rows": len(ridge_rows),
        "direct_gronda_cornice_details": len(edge),
        "separate_eave_rafter_ends": len(eave),
    })


if __name__ == "__main__":
    sys.exit(main())
