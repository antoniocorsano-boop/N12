from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA_ID = "CEW_COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_REPAIR_TASKS = {
    "R01": "COL02-FP-0252",
    "R03": "COL02-FP-0073",
    "R04": "COL02-FP-0241",
    "R05": "COL02-FP-0261",
    "R06": "COL02-FP-0071",
}
EXPECTED_REJECTED_TASKS = {"R02": "COL02-FP-0106"}
CLOSED_AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "structural_identity_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)


def load_axis_aware_repair_receipt(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_id") != EXPECTED_SCHEMA_ID or payload.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ValueError("unexpected axis-aware repair receipt schema")

    authority = payload.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("repair receipt authority is missing")
    if authority.get("graphical_whole_symbol_repair_authorized") is not True:
        raise ValueError("graphical whole-symbol repair authority is not explicitly authorized")
    for key in CLOSED_AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"repair receipt authority must remain closed: {key}")

    decisions = payload.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 6:
        raise ValueError("repair receipt must contain exactly six bounded decisions")
    by_task: dict[str, dict[str, Any]] = {}
    for row in decisions:
        task_id = str(row.get("review_task_id", ""))
        if not task_id or task_id in by_task:
            raise ValueError("repair receipt review task IDs must be unique")
        by_task[task_id] = row

    if set(by_task) != set(EXPECTED_REPAIR_TASKS) | set(EXPECTED_REJECTED_TASKS):
        raise ValueError("repair receipt task set drift")

    repair_candidate_ids: list[str] = []
    for task_id, candidate_id in EXPECTED_REPAIR_TASKS.items():
        row = by_task[task_id]
        if row.get("candidate_id") != candidate_id:
            raise ValueError(f"repair receipt candidate drift for {task_id}")
        if row.get("decision") != "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY":
            raise ValueError(f"repair receipt decision drift for {task_id}")
        if row.get("axis_partition_observed") is not True or row.get("repair_eligible") is not True:
            raise ValueError(f"repair receipt eligibility drift for {task_id}")
        repair_candidate_ids.append(candidate_id)

    rejected_candidate_ids: list[str] = []
    for task_id, candidate_id in EXPECTED_REJECTED_TASKS.items():
        row = by_task[task_id]
        if row.get("candidate_id") != candidate_id:
            raise ValueError(f"repair receipt candidate drift for {task_id}")
        if row.get("decision") != "MISLOCALIZED_NOT_COLUMN" or row.get("repair_eligible") is not False:
            raise ValueError(f"repair receipt rejection drift for {task_id}")
        rejected_candidate_ids.append(candidate_id)

    result = dict(payload)
    result["repair_candidate_ids"] = repair_candidate_ids
    result["rejected_candidate_ids"] = rejected_candidate_ids
    return result
