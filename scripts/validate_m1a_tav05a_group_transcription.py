#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
INDEX = C / "M1A_TAV05A_BEAM_GROUP_INDEX_v1.csv"
REINF = C / "M1A_TAV05A_GROUP_REINFORCEMENT_v1.csv"
STAIR = C / "M1A_STAIR_TOWER_SUBSYSTEM_CURRENT_v1.csv"
GAP = C / "M1A_SPECIAL_FEATURE_REINFORCEMENT_GAP_REGISTER_v1.csv"
GATE = C / "M1A_TAV05A_GROUP_TRANSCRIPTION_GATE_v1.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def finish(errors: list[str], warnings: list[str], summary: dict[str, object]) -> int:
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-A TAV-05A group transcription validation: {status}")
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
    for path in [INDEX, REINF, STAIR, GAP, GATE]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    index = read(INDEX)
    reinf = read(REINF)
    stair = read(STAIR)
    gap = read(GAP)
    gate = read(GATE)

    indexed_ids = {row["group_id"].strip() for row in index}
    reinforced_ids = {row["group_id"].strip() for row in reinf}
    expected_ids = {f"T5A-G{i:02d}" for i in range(1, 8)}

    if len(index) != 7:
        errors.append(f"expected 7 TAV-05A indexed groups, got {len(index)}")
    if indexed_ids != expected_ids:
        errors.append(f"indexed group ids mismatch: expected={sorted(expected_ids)} actual={sorted(indexed_ids)}")
    if reinforced_ids != expected_ids:
        errors.append(f"reinforcement group coverage mismatch: expected={sorted(expected_ids)} actual={sorted(reinforced_ids)}")
    if len(reinf) != 58:
        errors.append(f"expected 58 TAV-05A reinforcement rows, got {len(reinf)}")

    unknown_rows = []
    partial_rows = []
    inferred_unreadable = []
    for row in reinf:
        rid = row["row_id"].strip()
        qty = row["bar_quantity"].strip()
        dia = row["bar_diameter_mm"].strip()
        evidence = row["evidence_status"].strip()
        note = row["note"].lower()
        if qty == "UNKNOWN" or dia == "UNKNOWN":
            unknown_rows.append(rid)
        if evidence == "DOC_DIRECT_PARTIAL":
            partial_rows.append(rid)
        if ("not inferred" in note or "not completed numerically" in note or "not promoted" in note) and evidence:
            # Explicit anti-inference notes are expected and are not errors.
            pass
        if (qty == "UNKNOWN" or dia == "UNKNOWN") and evidence == "DOC_DIRECT":
            inferred_unreadable.append(rid)

    expected_unknown = {"T5A-G01-R06", "T5A-G07-R07"}
    if set(unknown_rows) != expected_unknown:
        errors.append(f"unexpected UNKNOWN quantity/diameter rows: expected={sorted(expected_unknown)} actual={sorted(unknown_rows)}")
    if partial_rows != ["T5A-G05-R04"]:
        errors.append(f"expected only T5A-G05-R04 as DOC_DIRECT_PARTIAL, got {partial_rows}")
    if inferred_unreadable:
        errors.append(f"UNKNOWN quantity/diameter rows cannot be DOC_DIRECT: {inferred_unreadable}")

    idx_by = {row["group_id"].strip(): row for row in index}
    g03 = idx_by.get("T5A-G03", {})
    if g03.get("binding_status", "").strip() != "PARTIAL_ORDINARY_PLUS_STAIR_SUBSYSTEM":
        errors.append("T5A-G03 must remain PARTIAL_ORDINARY_PLUS_STAIR_SUBSYSTEM")
    if "SPECIAL_STAIR_CANDIDATE_20_21" not in g03.get("g4_member_ids", ""):
        errors.append("T5A-G03 must preserve SPECIAL_STAIR_CANDIDATE_20_21")

    stair_by = {row["item_id"].strip(): row for row in stair}
    stair_g4 = stair_by.get("STAIR-003", {})
    stair_text = " ".join(stair_g4.values()).lower() if stair_g4 else ""
    if "20-21" not in stair_text or "ordinary" not in stair_text:
        errors.append("STAIR-003 must preserve the recurring G4 20-21 special-subsystem interpretation")

    gap_by = {row["gap_id"].strip(): row for row in gap}
    sf011 = gap_by.get("M1A-SF-011", {})
    if sf011.get("current_decision", "").strip() != "DEDICATED_SUBSYSTEM_ACTIVE":
        errors.append("stair/torrino dedicated subsystem must remain active")

    gate_by = {row["check_id"].strip(): row for row in gate}
    expected_gate = {
        "M1A-T5-G01": "7",
        "M1A-T5-G02": "7",
        "M1A-T5-G03": "58",
        "M1A-T5-G04": "2",
        "M1A-T5-G05": "1",
        "M1A-T5-G06": "NO",
        "M1A-T5-G07": "YES",
        "M1A-T5-G08": "NO",
        "M1A-T5-G09": "NO",
        "M1A-T5-GATE": "PASS_GROUP_TRANSCRIPTION_WITH_READABILITY_AND_STAIR_WATCH",
    }
    for check_id, expected in expected_gate.items():
        actual = gate_by.get(check_id, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{check_id}: expected actual={expected!r}, got {actual!r}")

    warnings.extend([
        "T5A-G01-R06 retains L=1040 with quantity/diameter UNKNOWN",
        "T5A-G07-R07 retains L=865 with quantity/diameter UNKNOWN",
        "T5A-G05-R04 remains DOC_DIRECT_PARTIAL with an unlabelled intermediate continuation",
        "T5A-G03 20-21 remains a special stair-subsystem candidate and is not an ordinary G4 beam",
        "detailed member/station projection remains a later refinement and is not required for this group-level closure",
    ])

    return finish(errors, warnings, {
        "indexed_groups": len(index),
        "groups_with_reinforcement_rows": len(reinforced_ids),
        "reinforcement_rows": len(reinf),
        "unknown_quantity_or_diameter_rows": len(unknown_rows),
        "direct_partial_dimension_rows": len(partial_rows),
        "ordinary_20_21_created": "NO",
    })


if __name__ == "__main__":
    sys.exit(main())
