#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"

GROUPS = C / "M1F_TAV01A_GROUP_INDEX_v1.csv"
REINF = C / "M1F_TAV01A_GROUP_REINFORCEMENT_v1.csv"
QUEUE = C / "M1F_REINFORCEMENT_EXTRACTION_QUEUE_v1.csv"
TOPOLOGY = C / "M1F_FOUNDATION_TOPOLOGY_CURRENT_v1.csv"
CROSSCHECK = C / "M1F_TAV01A_TAV01S_CROSSCHECK_v1.csv"
GATE = C / "M1F_FOUNDATION_REINFORCEMENT_GATE_v1.csv"

EXPECTED_GROUPS = {f"F1A-G0{i}" for i in range(1, 8)}


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for path in [GROUPS, REINF, QUEUE, TOPOLOGY, CROSSCHECK, GATE]:
        if not path.exists():
            errors.append(f"missing required M1-F reinforcement artifact: {path.relative_to(ROOT)}")
    if errors:
        return report(errors, warnings, {})

    groups = read_csv(GROUPS)
    reinf = read_csv(REINF)
    queue = read_csv(QUEUE)
    topology = read_csv(TOPOLOGY)
    crosscheck = read_csv(CROSSCHECK)
    gate = read_csv(GATE)

    group_ids = [r["group_id"].strip() for r in groups]
    if len(groups) != 7 or set(group_ids) != EXPECTED_GROUPS:
        errors.append(f"group index must contain exactly G01-G07, got {group_ids}")
    if len(set(group_ids)) != len(group_ids):
        errors.append("duplicate group_id in TAV01A group index")

    row_ids = [r["row_id"].strip() for r in reinf]
    if len(reinf) != 47:
        errors.append(f"reinforcement row count must be 47, got {len(reinf)}")
    if len(set(row_ids)) != len(row_ids):
        errors.append("duplicate reinforcement row_id")
    reinf_groups = {r["group_id"].strip() for r in reinf}
    if reinf_groups != EXPECTED_GROUPS:
        errors.append(f"reinforcement rows must cover all seven groups, got {sorted(reinf_groups)}")

    queue_by_group = {r["group_id"].strip(): r for r in queue}
    if set(queue_by_group) != EXPECTED_GROUPS or len(queue) != 7:
        errors.append("reinforcement extraction queue must contain exactly one row for each G01-G07")
    complete = sum(1 for r in queue if r["reinforcement_transcription_state"].strip() == "COMPLETE_DIRECT")
    partial = sum(1 for r in queue if r["reinforcement_transcription_state"].strip() == "PARTIAL_DIRECT")
    pending = sum(1 for r in queue if r["reinforcement_transcription_state"].strip() == "PENDING")
    if (complete, partial, pending) != (1, 6, 0):
        errors.append(f"queue state partition must be 1 complete / 6 partial / 0 pending, got {(complete, partial, pending)}")

    open_rows = [r for r in reinf if r["binding_state"].strip().startswith("OPEN_")]
    if len(open_rows) != 9:
        errors.append(f"open reinforcement transcription row count must be 9, got {len(open_rows)}")

    # Section-transition regimes must remain explicitly split.
    for group in ["F1A-G05", "F1A-G06"]:
        states = {r["binding_state"].strip() for r in reinf if r["group_id"].strip() == group}
        if not any(s.endswith("B_SIDE") for s in states):
            errors.append(f"{group}: missing explicit B-side reinforcement regime")
        if not any(s.endswith("A_SIDE") for s in states):
            errors.append(f"{group}: missing explicit A-side reinforcement regime")

    # G03 must remain group-level and topology-corrected.
    g03_rows = [r for r in reinf if r["group_id"].strip() == "F1A-G03"]
    if not g03_rows:
        errors.append("G03 reinforcement rows missing")
    if not any(r["binding_state"].strip() == "GROUP_BOUND_WITH_22_PRIME_CORRECTION" for r in g03_rows):
        errors.append("G03 must preserve GROUP_BOUND_WITH_22_PRIME_CORRECTION")
    expected_g03_straights = {
        ("UPPER_STRAIGHT_BAR", "3", "16", "L=880"),
        ("UPPER_STRAIGHT_BAR", "2", "14", "L=910"),
        ("LOWER_STRAIGHT_BAR", "3", "18", "L=920"),
        ("LOWER_STRAIGHT_BAR", "3", "14", "L=960"),
    }
    actual_g03_straights = {
        (r["bar_role"].strip(), r["bar_quantity"].strip(), r["bar_diameter_mm"].strip(), r["shape_or_length"].strip())
        for r in g03_rows
        if r["bar_role"].strip() in {"UPPER_STRAIGHT_BAR", "LOWER_STRAIGHT_BAR"}
    }
    if actual_g03_straights != expected_g03_straights:
        errors.append(f"G03 direct straight-bar transcription mismatch: {sorted(actual_g03_straights)}")

    cc = {r["candidate_id"].strip(): r for r in crosscheck}
    if cc.get("FND-C015", {}).get("promotion_state", "").strip() != "REJECTED_AS_PHYSICAL_EDGE":
        errors.append("FND-C015 13-22 must remain rejected as a physical edge")
    if cc.get("FND-C016", {}).get("promotion_state", "").strip() != "TRANSFORMED_TO_PHYSICAL_PATH":
        errors.append("FND-C016 22-27 must remain transformed through distinct 22-prime")

    if len(topology) != 58:
        errors.append(f"foundation topology must contain 58 members, got {len(topology)}")
    direct = sum(1 for r in topology if r["reinforcement_binding_state"].strip() == "DIRECT_GROUP_BOUND")
    supported = sum(1 for r in topology if r["reinforcement_binding_state"].strip() == "SCHEMATIC_22_27_SPLIT_AT_22_PRIME")
    no_autonomous = len(topology) - direct - supported
    if (direct, supported, no_autonomous) != (42, 1, 15):
        errors.append(f"member reinforcement binding partition must be 42 direct / 1 supported / 15 without autonomous group, got {(direct, supported, no_autonomous)}")

    gate_by_id = {r["check_id"].strip(): r for r in gate}
    expected_actuals = {
        "M1F-REINF-001": "7",
        "M1F-REINF-002": "7",
        "M1F-REINF-003": "47",
        "M1F-REINF-004": "1",
        "M1F-REINF-005": "6",
        "M1F-REINF-006": "0",
        "M1F-REINF-007": "9",
        "M1F-REINF-008": "2",
        "M1F-REINF-009": "1",
        "M1F-REINF-010": "42",
        "M1F-REINF-011": "1",
        "M1F-REINF-012": "15",
        "M1F-REINF-GATE": "PASS_GROUP_COVERAGE_WITH_TRANSCRIPTION_WATCHES",
    }
    for check_id, expected in expected_actuals.items():
        actual = gate_by_id.get(check_id, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{check_id}: gate actual expected {expected!r}, got {actual!r}")

    summary = {
        "groups": len(groups),
        "reinforcement_rows": len(reinf),
        "groups_complete": complete,
        "groups_partial": partial,
        "groups_pending": pending,
        "open_transcription_rows": len(open_rows),
        "members_direct_group_bound": direct,
        "members_supported_group_bound": supported,
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
