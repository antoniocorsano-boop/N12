from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_RECONCILIATION_REPLAY_SHA256 = "b68526f71e77a072b0849d2d3cd2fcab886b03c86a99681717d7aee5cd13bf3c"
EXPECTED_REPAIR_MANIFEST_SHA256 = "e688c22753d8804edfdded8e9f89651c60b7a864a016b400a027d708329b1228"
EXPECTED_TASKS = {
    "R01": "COL02-FP-0252",
    "R02": "COL02-FP-0106",
    "R03": "COL02-FP-0073",
    "R04": "COL02-FP-0241",
    "R05": "COL02-FP-0261",
    "R06": "COL02-FP-0071",
}
EXPECTED_REPAIR_TASKS = {
    "R01": "COL02-FP-0252",
    "R03": "COL02-FP-0073",
    "R04": "COL02-FP-0241",
    "R05": "COL02-FP-0261",
    "R06": "COL02-FP-0071",
}
EXPECTED_POINT_CANDIDATES = {
    "COL02-FP-0073",
    "COL02-FP-0241",
    "COL02-FP-0261",
    "COL02-FP-0071",
}
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

EVIDENCE_ROOT = Path("evidence/cew-col02/footprint-text-binding")
RECONCILIATION_PATH = EVIDENCE_ROOT / "col02-residual-occurrence-reconciliation.json"
REPAIR_MANIFEST_PATH = EVIDENCE_ROOT / "col02-axis-aware-whole-symbol-repair.json"
RECONCILIATION_RECEIPT_PATH = Path("governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json")
GRAPHICAL_REVIEW_RECEIPT_PATH = Path("governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v2.json")
OUTPUT_PATH = EVIDENCE_ROOT / "col02-occurrence-coverage-closure.json"


def _require_closed_authority(payload: dict[str, Any], label: str) -> None:
    authority = payload.get("authority")
    if not isinstance(authority, dict):
        raise ValueError(f"{label} authority missing")
    for key in CLOSED_AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"{label} authority drift: {key}")


def _candidate_id(task: dict[str, Any]) -> str:
    value = task.get("candidate_id") or task.get("proposal_candidate_id")
    return str(value or "")


def validate_occurrence_coverage_closure_inputs(
    *,
    reconciliation_manifest: dict[str, Any],
    reconciliation_receipt: dict[str, Any],
    repair_manifest: dict[str, Any],
    repair_manifest_bytes: bytes,
    graphical_review_receipt: dict[str, Any],
    expected_repair_manifest_sha256: str,
) -> None:
    if reconciliation_manifest.get("residual_candidate_review_complete") is not True:
        raise ValueError("residual candidate review is not complete")
    if reconciliation_manifest.get("replay_sha256") != EXPECTED_RECONCILIATION_REPLAY_SHA256:
        raise ValueError("residual reconciliation replay drift")
    if reconciliation_manifest.get("occurrence_coverage_complete") is not False:
        raise ValueError("historical reconciliation coverage state drift")
    _require_closed_authority(reconciliation_manifest, "reconciliation manifest")

    review_tasks = reconciliation_manifest.get("review_tasks")
    if not isinstance(review_tasks, list) or len(review_tasks) != len(EXPECTED_TASKS):
        raise ValueError("successor reconciliation task count drift")
    task_by_id: dict[str, dict[str, Any]] = {}
    for task in review_tasks:
        task_id = str(task.get("review_task_id", ""))
        if not task_id or task_id in task_by_id:
            raise ValueError("successor reconciliation task IDs must be unique")
        task_by_id[task_id] = task
    if set(task_by_id) != set(EXPECTED_TASKS):
        raise ValueError("successor reconciliation task set drift")
    for task_id, candidate_id in EXPECTED_TASKS.items():
        if _candidate_id(task_by_id[task_id]) != candidate_id:
            raise ValueError(f"successor reconciliation candidate drift: {task_id}")

    points = reconciliation_manifest.get("point_reconciliation")
    if not isinstance(points, list) or len(points) != 4:
        raise ValueError("human-point reconciliation count drift")
    point_candidates: list[str] = []
    for row in points:
        if row.get("status") == "HUMAN_POINT_UNBOUND":
            raise ValueError("unresolved human point remains")
        if row.get("status") != "REVIEW_REQUIRED_EXISTING_PROPOSAL":
            raise ValueError("human-point reconciliation status drift")
        candidate_id = str(row.get("proposal_candidate_id", ""))
        if not candidate_id:
            raise ValueError("human point lacks frozen proposal binding")
        point_candidates.append(candidate_id)
    if set(point_candidates) != EXPECTED_POINT_CANDIDATES or len(set(point_candidates)) != 4:
        raise ValueError("human-point proposal binding drift")

    if (
        reconciliation_receipt.get("schema_id") != "CEW_COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW"
        or reconciliation_receipt.get("schema_version") != 1
    ):
        raise ValueError("unexpected residual reconciliation review schema")
    _require_closed_authority(reconciliation_receipt, "reconciliation receipt")
    decisions = reconciliation_receipt.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != len(EXPECTED_TASKS):
        raise ValueError("terminal reconciliation decision count drift")
    decision_by_task: dict[str, dict[str, Any]] = {}
    for row in decisions:
        task_id = str(row.get("review_task_id", ""))
        if not task_id or task_id in decision_by_task:
            raise ValueError("terminal reconciliation task IDs must be unique")
        decision_by_task[task_id] = row
    if set(decision_by_task) != set(EXPECTED_TASKS):
        raise ValueError("terminal reconciliation task set drift")
    for task_id, candidate_id in EXPECTED_TASKS.items():
        row = decision_by_task[task_id]
        if row.get("candidate_id") != candidate_id:
            raise ValueError(f"terminal reconciliation candidate drift: {task_id}")
        if task_id == "R02":
            if row.get("decision") != "MISLOCALIZED_NOT_COLUMN" or row.get("repair_eligible") is not False:
                raise ValueError("R02 rejection drift")
        elif row.get("decision") != "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY" or row.get("repair_eligible") is not True:
            raise ValueError(f"repair-eligible terminal decision drift: {task_id}")

    actual_repair_digest = hashlib.sha256(repair_manifest_bytes).hexdigest()
    if actual_repair_digest != expected_repair_manifest_sha256:
        raise ValueError("reviewed repair manifest digest mismatch")
    if repair_manifest.get("proposal_count") != 611 or repair_manifest.get("original_proposal_id_space_immutable") is not True:
        raise ValueError("frozen proposal producer drift")
    if repair_manifest.get("occurrence_coverage_complete") is not False:
        raise ValueError("historical repair coverage state drift")
    if repair_manifest.get("repair_candidate_count") != 5 or repair_manifest.get("ready_for_human_review_count") != 5:
        raise ValueError("repair candidate readiness drift")
    if repair_manifest.get("unresolved_repair_count") != 0:
        raise ValueError("unresolved repair remains")
    if repair_manifest.get("rejected_candidates") != [
        {"candidate_id": "COL02-FP-0106", "reason": "MISLOCALIZED_NOT_COLUMN"}
    ]:
        raise ValueError("rejected candidate drift")
    _require_closed_authority(repair_manifest, "repair manifest")

    repairs = repair_manifest.get("repairs")
    if not isinstance(repairs, list) or len(repairs) != 5:
        raise ValueError("repair record count drift")
    repair_by_candidate = {str(row.get("source_candidate_id", "")): row for row in repairs}
    if set(repair_by_candidate) != set(EXPECTED_REPAIR_TASKS.values()):
        raise ValueError("repair source candidate set drift")
    for candidate_id, row in repair_by_candidate.items():
        if row.get("status") != "READY_FOR_HUMAN_GRAPHICAL_REVIEW":
            raise ValueError(f"repair not review-ready: {candidate_id}")

    if (
        graphical_review_receipt.get("schema_id") != "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW"
        or graphical_review_receipt.get("schema_version") != 2
    ):
        raise ValueError("unexpected final graphical review schema")
    _require_closed_authority(graphical_review_receipt, "graphical review receipt")
    graphical_decisions = graphical_review_receipt.get("decisions")
    if not isinstance(graphical_decisions, list) or len(graphical_decisions) != 5:
        raise ValueError("final graphical decision count drift")
    graphical_by_candidate: dict[str, dict[str, Any]] = {}
    for row in graphical_decisions:
        candidate_id = str(row.get("source_candidate_id", ""))
        if not candidate_id or candidate_id in graphical_by_candidate:
            raise ValueError("final graphical source candidate IDs must be unique")
        graphical_by_candidate[candidate_id] = row
    if set(graphical_by_candidate) != set(EXPECTED_REPAIR_TASKS.values()):
        raise ValueError("final graphical source candidate set drift")
    for candidate_id, row in graphical_by_candidate.items():
        if row.get("decision") != "PASS":
            raise ValueError(f"final graphical review not PASS: {candidate_id}")


def build_occurrence_coverage_closure(
    *,
    reconciliation_manifest: dict[str, Any],
    reconciliation_receipt: dict[str, Any],
    repair_manifest: dict[str, Any],
    repair_manifest_bytes: bytes,
    graphical_review_receipt: dict[str, Any],
    expected_repair_manifest_sha256: str,
) -> dict[str, Any]:
    validate_occurrence_coverage_closure_inputs(
        reconciliation_manifest=reconciliation_manifest,
        reconciliation_receipt=reconciliation_receipt,
        repair_manifest=repair_manifest,
        repair_manifest_bytes=repair_manifest_bytes,
        graphical_review_receipt=graphical_review_receipt,
        expected_repair_manifest_sha256=expected_repair_manifest_sha256,
    )

    terminal = []
    receipt_by_task = {row["review_task_id"]: row for row in reconciliation_receipt["decisions"]}
    for task_id, candidate_id in EXPECTED_TASKS.items():
        row = receipt_by_task[task_id]
        terminal.append({
            "review_task_id": task_id,
            "candidate_id": candidate_id,
            "terminal_decision": row["decision"],
            "repair_eligible": bool(row.get("repair_eligible")),
        })

    graphical_by_candidate = {
        row["source_candidate_id"]: row for row in graphical_review_receipt["decisions"]
    }
    repairs = [
        {
            "source_candidate_id": candidate_id,
            "decision": graphical_by_candidate[candidate_id]["decision"],
        }
        for candidate_id in EXPECTED_REPAIR_TASKS.values()
    ]

    return {
        "schema_id": "CEW_COL02_OCCURRENCE_COVERAGE_CLOSURE",
        "schema_version": 1,
        "status": "GRAPHICAL_OCCURRENCE_COVERAGE_COMPLETE",
        "reconciliation_replay_sha256": reconciliation_manifest["replay_sha256"],
        "reviewed_repair_manifest_sha256": expected_repair_manifest_sha256,
        "proposal_count": 611,
        "original_proposal_id_space_immutable": True,
        "terminal_successor_item_count": 6,
        "bound_human_point_count": 4,
        "repair_pass_count": 5,
        "rejected_candidate_count": 1,
        "terminal_successor_items": terminal,
        "human_point_bindings": [
            {
                "event_id": row.get("event_id"),
                "proposal_candidate_id": row["proposal_candidate_id"],
            }
            for row in reconciliation_manifest["point_reconciliation"]
        ],
        "final_repair_decisions": repairs,
        "rejected_candidates": [
            {"candidate_id": "COL02-FP-0106", "reason": "MISLOCALIZED_NOT_COLUMN"}
        ],
        "historical_reconciliation_occurrence_coverage_complete": False,
        "historical_repair_occurrence_coverage_complete": False,
        "occurrence_coverage_complete": True,
        "authority": {key: False for key in CLOSED_AUTHORITY_KEYS},
    }


def write_occurrence_coverage_closure(
    *,
    reconciliation_path: Path,
    reconciliation_receipt_path: Path,
    repair_manifest_path: Path,
    graphical_review_receipt_path: Path,
    output_path: Path,
    expected_repair_manifest_sha256: str,
) -> dict[str, Any]:
    reconciliation_manifest = json.loads(reconciliation_path.read_text(encoding="utf-8"))
    reconciliation_receipt = json.loads(reconciliation_receipt_path.read_text(encoding="utf-8"))
    repair_manifest_bytes = repair_manifest_path.read_bytes()
    repair_manifest = json.loads(repair_manifest_bytes.decode("utf-8"))
    graphical_review_receipt = json.loads(graphical_review_receipt_path.read_text(encoding="utf-8"))

    closure = build_occurrence_coverage_closure(
        reconciliation_manifest=reconciliation_manifest,
        reconciliation_receipt=reconciliation_receipt,
        repair_manifest=repair_manifest,
        repair_manifest_bytes=repair_manifest_bytes,
        graphical_review_receipt=graphical_review_receipt,
        expected_repair_manifest_sha256=expected_repair_manifest_sha256,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(closure, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return closure


def main() -> None:
    closure = write_occurrence_coverage_closure(
        reconciliation_path=RECONCILIATION_PATH,
        reconciliation_receipt_path=RECONCILIATION_RECEIPT_PATH,
        repair_manifest_path=REPAIR_MANIFEST_PATH,
        graphical_review_receipt_path=GRAPHICAL_REVIEW_RECEIPT_PATH,
        output_path=OUTPUT_PATH,
        expected_repair_manifest_sha256=EXPECTED_REPAIR_MANIFEST_SHA256,
    )
    print(
        "CEW_COL02_OCCURRENCE_COVERAGE_CLOSURE="
        + json.dumps(
            {
                "status": closure["status"],
                "occurrence_coverage_complete": closure["occurrence_coverage_complete"],
                "terminal_successor_item_count": closure["terminal_successor_item_count"],
                "bound_human_point_count": closure["bound_human_point_count"],
                "repair_pass_count": closure["repair_pass_count"],
                "rejected_candidate_count": closure["rejected_candidate_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
