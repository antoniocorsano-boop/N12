#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
GROUPS = C / "M1F_TAV01A_GROUP_INDEX_v1.csv"
REINF = C / "M1F_TAV01A_GROUP_REINFORCEMENT_v1.csv"
PATCH = C / "M1F_TAV01A_REINFORCEMENT_CORRECTION_PATCH_v1.csv"
QUEUE = C / "M1F_REINFORCEMENT_EXTRACTION_QUEUE_v1.csv"
TOPOLOGY = C / "M1F_FOUNDATION_TOPOLOGY_CURRENT_v1.csv"
CROSSCHECK = C / "M1F_TAV01A_TAV01S_CROSSCHECK_v1.csv"
GATE = C / "M1F_FOUNDATION_REINFORCEMENT_GATE_v1.csv"
EXPECTED_GROUPS = {f"F1A-G0{i}" for i in range(1, 8)}
EXPECTED_PATCH_IDS = {f"M1F-REINF-P00{i}" for i in range(1, 8)}


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def apply_patch(base: list[dict[str, str]], patch: list[dict[str, str]], errors: list[str]):
    rows = [dict(r) for r in base]
    by_id = {r["row_id"].strip(): r for r in rows}
    if len(patch) != 7 or {r["patch_id"].strip() for r in patch} != EXPECTED_PATCH_IDS:
        errors.append("HiRes correction/partition patch must contain exactly P001-P007")
        return rows
    for p in patch:
        op = p["operation"].strip()
        target = p["target_row_id"].strip()
        new_id = p["new_row_id"].strip()
        values = {
            "group_id": p["group_id"].strip(),
            "source_id": "TAV-01A",
            "source_locator": p["source_locator"].strip(),
            "bar_role": p["bar_role"].strip(),
            "bar_quantity": p["bar_quantity"].strip(),
            "bar_diameter_mm": p["bar_diameter_mm"].strip(),
            "shape_or_length": p["shape_or_length"].strip(),
            "segment_dimensions_cm": p.get("segment_dimensions_cm", "").strip(),
            "evidence_status": p["evidence_status"].strip(),
            "binding_state": p["binding_state"].strip(),
            "note": p["reason"].strip(),
        }
        if op == "REPLACE":
            if target not in by_id or new_id != target:
                errors.append(f"invalid REPLACE patch {p['patch_id']}: target={target} new={new_id}")
                continue
            by_id[target].update(values)
        elif op == "ADD":
            if not new_id or new_id in by_id:
                errors.append(f"invalid ADD patch {p['patch_id']}: new_row_id={new_id}")
                continue
            row = {k: "" for k in base[0].keys()}
            row["row_id"] = new_id
            row.update(values)
            rows.append(row)
            by_id[new_id] = row
        else:
            errors.append(f"unknown patch operation {op!r}")
    return rows


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [GROUPS, REINF, PATCH, QUEUE, TOPOLOGY, CROSSCHECK, GATE]
    for path in required:
        if not path.exists():
            errors.append(f"missing required M1-F reinforcement artifact: {path.relative_to(ROOT)}")
    if errors:
        return report(errors, warnings, {})

    groups = read_csv(GROUPS)
    base_reinf = read_csv(REINF)
    patch = read_csv(PATCH)
    queue = read_csv(QUEUE)
    topology = read_csv(TOPOLOGY)
    crosscheck = read_csv(CROSSCHECK)
    gate = read_csv(GATE)
    reinf = apply_patch(base_reinf, patch, errors)

    group_ids = [r["group_id"].strip() for r in groups]
    if len(groups) != 7 or set(group_ids) != EXPECTED_GROUPS or len(set(group_ids)) != 7:
        errors.append(f"group index must contain exactly unique G01-G07, got {group_ids}")

    if len(base_reinf) != 47:
        errors.append(f"base reinforcement row count must remain 47, got {len(base_reinf)}")
    if len(reinf) != 51:
        errors.append(f"effective reinforcement row count must be 51, got {len(reinf)}")
    row_ids = [r["row_id"].strip() for r in reinf]
    if len(row_ids) != len(set(row_ids)):
        errors.append("duplicate effective reinforcement row_id")
    if {r["group_id"].strip() for r in reinf} != EXPECTED_GROUPS:
        errors.append("effective reinforcement rows do not cover exactly all seven groups")

    queue_by_group = {r["group_id"].strip(): r for r in queue}
    if set(queue_by_group) != EXPECTED_GROUPS or len(queue) != 7:
        errors.append("reinforcement extraction queue must contain exactly one row for G01-G07")
    complete = sum(r["reinforcement_transcription_state"].strip() == "COMPLETE_DIRECT" for r in queue)
    partial = sum(r["reinforcement_transcription_state"].strip() == "PARTIAL_DIRECT" for r in queue)
    pending = sum(r["reinforcement_transcription_state"].strip() == "PENDING" for r in queue)
    if (complete, partial, pending) != (2, 5, 0):
        errors.append(f"queue partition must be 2 complete / 5 partial / 0 pending, got {(complete, partial, pending)}")

    open_rows = [r for r in reinf if r["binding_state"].strip().startswith("OPEN_")]
    if len(open_rows) != 6:
        errors.append(f"open reinforcement transcription row count must be 6, got {len(open_rows)}")

    for group in ["F1A-G05", "F1A-G06"]:
        states = {r["binding_state"].strip() for r in reinf if r["group_id"].strip() == group}
        if not any(s.endswith("B_SIDE") for s in states) or not any(s.endswith("A_SIDE") for s in states):
            errors.append(f"{group}: B-side/A-side reinforcement regimes must remain explicit")

    g03 = [r for r in reinf if r["group_id"].strip() == "F1A-G03"]
    expected_g03 = {
        ("UPPER_STRAIGHT_BAR", "3", "16", "L=880"),
        ("UPPER_STRAIGHT_BAR", "2", "14", "L=910"),
        ("LOWER_STRAIGHT_BAR", "3", "18", "L=920"),
        ("LOWER_STRAIGHT_BAR", "3", "14", "L=960"),
    }
    actual_g03 = {(r["bar_role"].strip(), r["bar_quantity"].strip(), r["bar_diameter_mm"].strip(), r["shape_or_length"].strip()) for r in g03 if r["bar_role"].strip() in {"UPPER_STRAIGHT_BAR", "LOWER_STRAIGHT_BAR"}}
    if actual_g03 != expected_g03:
        errors.append(f"G03 direct straight-bar transcription mismatch: {sorted(actual_g03)}")
    if not any(r["binding_state"].strip() == "GROUP_BOUND_WITH_22_PRIME_CORRECTION" for r in g03):
        errors.append("G03 must preserve GROUP_BOUND_WITH_22_PRIME_CORRECTION")

    g06 = [r for r in reinf if r["group_id"].strip() == "F1A-G06"]
    expected_g06_a = {
        ("UPPER_STRAIGHT_BAR", "3", "16", "L=1180", "GROUP_BOUND_A_SIDE"),
        ("LOWER_STRAIGHT_BAR", "3", "18", "L=1260", "GROUP_BOUND_A_SIDE"),
    }
    actual_g06_a = {(r["bar_role"].strip(), r["bar_quantity"].strip(), r["bar_diameter_mm"].strip(), r["shape_or_length"].strip(), r["binding_state"].strip()) for r in g06 if r["shape_or_length"].strip() in {"L=1180", "L=1260"}}
    if actual_g06_a != expected_g06_a:
        errors.append(f"G06 A-side direct straight-bar transcription mismatch: {sorted(actual_g06_a)}")

    by_row = {r["row_id"].strip(): r for r in reinf}
    expected_g02_patch_rows = {
        "F1A-G02-R02": ("2", "14", "L=1080|L=990"),
        "F1A-G02-R02B": ("3", "16", "L=1100"),
        "F1A-G02-R03": ("3", "14", "L=1120|L=1010"),
        "F1A-G02-R03B": ("3", "16", "L=1120"),
    }
    for row_id, expected in expected_g02_patch_rows.items():
        r = by_row.get(row_id, {})
        actual = (r.get("bar_quantity", "").strip(), r.get("bar_diameter_mm", "").strip(), r.get("shape_or_length", "").strip())
        if actual != expected:
            errors.append(f"{row_id}: effective G02 patch expected {expected}, got {actual}")

    expected_g07_lower = {
        "F1A-G07-R04": ("2", "12", "BENT_PARTIAL", "70+70=140;right_diag122;left_inclined_segment_unlabelled"),
        "F1A-G07-R04B": ("2", "12", "BENT_PARTIAL", "left_diag122;70+30=100;right_diag_unlabelled"),
        "F1A-G07-R04C": ("2", "14", "BENT_PARTIAL", "left_diag122;30+70=100;right_end_segment_unlabelled"),
    }
    for row_id, expected in expected_g07_lower.items():
        r = by_row.get(row_id, {})
        actual = (
            r.get("bar_quantity", "").strip(),
            r.get("bar_diameter_mm", "").strip(),
            r.get("shape_or_length", "").strip(),
            r.get("segment_dimensions_cm", "").strip(),
        )
        if actual != expected or r.get("binding_state", "").strip() != "GROUP_BOUND":
            errors.append(f"{row_id}: G07 direct lower-sagomato partition mismatch: expected {expected}, got {actual}")

    cc = {r["candidate_id"].strip(): r for r in crosscheck}
    if cc.get("FND-C015", {}).get("promotion_state", "").strip() != "REJECTED_AS_PHYSICAL_EDGE":
        errors.append("FND-C015 13-22 must remain rejected as physical edge")
    if cc.get("FND-C016", {}).get("promotion_state", "").strip() != "TRANSFORMED_TO_PHYSICAL_PATH":
        errors.append("FND-C016 22-27 must remain transformed through distinct 22-prime")

    if len(topology) != 58:
        errors.append(f"foundation topology must contain 58 members, got {len(topology)}")
    direct = sum(r["reinforcement_binding_state"].strip() == "DIRECT_GROUP_BOUND" for r in topology)
    supported = sum(r["reinforcement_binding_state"].strip() == "SCHEMATIC_22_27_SPLIT_AT_22_PRIME" for r in topology)
    no_autonomous = len(topology) - direct - supported
    if (direct, supported, no_autonomous) != (42, 1, 15):
        errors.append(f"member binding partition must be 42 direct / 1 supported / 15 no-autonomous, got {(direct, supported, no_autonomous)}")

    gate_by_id = {r["check_id"].strip(): r for r in gate}
    expected_actuals = {
        "M1F-REINF-001": "7", "M1F-REINF-002": "7", "M1F-REINF-003": "51",
        "M1F-REINF-004": "2", "M1F-REINF-005": "5", "M1F-REINF-006": "0",
        "M1F-REINF-007": "6", "M1F-REINF-008": "2", "M1F-REINF-009": "1",
        "M1F-REINF-010": "42", "M1F-REINF-011": "1", "M1F-REINF-012": "15",
        "M1F-REINF-013": "4", "M1F-REINF-014": "3",
        "M1F-REINF-GATE": "PASS_GROUP_COVERAGE_WITH_TRANSCRIPTION_WATCHES",
    }
    for check_id, expected in expected_actuals.items():
        actual = gate_by_id.get(check_id, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{check_id}: gate actual expected {expected!r}, got {actual!r}")

    summary = {
        "groups": len(groups), "base_reinforcement_rows": len(base_reinf), "effective_reinforcement_rows": len(reinf),
        "correction_patch_rows": len(patch), "groups_complete": complete, "groups_partial": partial,
        "groups_pending": pending, "open_transcription_rows": len(open_rows),
        "members_direct_group_bound": direct, "members_supported_group_bound": supported,
        "members_without_autonomous_group": no_autonomous,
    }
    return report(errors, warnings, summary)


def report(errors: list[str], warnings: list[str], summary: dict) -> int:
    state = "PASS" if not errors else "FAIL"
    print(f"M1F_FOUNDATION_REINFORCEMENT_VALIDATION={state}")
    for key, value in summary.items():
        print(f"{key}={value}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
