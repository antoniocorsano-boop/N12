from __future__ import annotations

from typing import Any

from experiments.cew_col02.residual_occurrence_reconciliation import replay_mobile_review


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

PROTOTYPE_RECEIPT_PATH = "governance/cew-col02/COLUMN_FOOTPRINT_HUMAN_REVIEW_v1.json"
PROTOTYPE_GUIDED_RECEIPT_PATH = "governance/cew-col02/COL02_PROTOTYPE_GUIDED_HUMAN_REVIEW_v1.json"
MOBILE_RECEIPT_PATH = "governance/cew-col02/COL02_RESIDUAL_MOBILE_HUMAN_REVIEW_v1.json"
RECONCILIATION_RECEIPT_PATH = "governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json"
REPAIR_REVIEW_RECEIPT_PATH = "governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v2.json"
REJECTED_CANDIDATE_ID = "COL02-FP-0106"


def _authority_mapping(payload: dict[str, Any], label: str) -> dict[str, Any]:
    authority = payload.get("authority")
    if not isinstance(authority, dict):
        authority = payload.get("governance")
    if not isinstance(authority, dict):
        raise ValueError(f"{label} authority/governance missing")
    return authority


def validate_col03a_input_authority(payload: dict[str, Any], label: str) -> None:
    authority = _authority_mapping(payload, label)
    for key in CLOSED_AUTHORITY_KEYS:
        if authority.get(key) is not False:
            raise ValueError(f"{label} authority drift: {key}")
    if "canonical_write_authorized" in payload and payload.get("canonical_write_authorized") is not False:
        raise ValueError(f"{label} top-level canonical_write_authorized drift")
    if "canonical_write_performed" in payload and payload.get("canonical_write_performed") is not False:
        raise ValueError(f"{label} top-level canonical_write_performed drift")


def _base_item(
    *,
    evidence_id: str,
    candidate_id: str,
    evidence_class: str,
    graphical_decision: str,
    discovery_path: str,
    human_review_receipt: str,
    repair_id: str | None = None,
    human_added_point_event_ids: list[str] | None = None,
    lineage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "evidence_class": evidence_class,
        "graphical_decision": graphical_decision,
        "discovery_path": discovery_path,
        "human_review_receipt": human_review_receipt,
        "repair_id": repair_id,
        "human_added_point_event_ids": list(human_added_point_event_ids or []),
        "lineage": dict(lineage or {}),
    }


def _candidate_from_task(task: dict[str, Any]) -> str:
    return str(task.get("candidate_id") or task.get("proposal_candidate_id") or "")


def collect_governed_positive_evidence(
    *,
    prototype_receipt: dict[str, Any],
    prototype_guided_receipt: dict[str, Any],
    mobile_receipt: dict[str, Any],
    reconciliation_manifest: dict[str, Any],
    reconciliation_receipt: dict[str, Any],
    repair_manifest: dict[str, Any],
    repair_review_receipt: dict[str, Any],
    coverage_closure: dict[str, Any],
) -> list[dict[str, Any]]:
    inputs = (
        (prototype_receipt, "prototype receipt"),
        (prototype_guided_receipt, "prototype-guided receipt"),
        (mobile_receipt, "mobile receipt"),
        (reconciliation_manifest, "reconciliation manifest"),
        (reconciliation_receipt, "reconciliation receipt"),
        (repair_manifest, "repair manifest"),
        (repair_review_receipt, "repair review receipt"),
        (coverage_closure, "coverage closure"),
    )
    for payload, label in inputs:
        validate_col03a_input_authority(payload, label)

    if coverage_closure.get("schema_id") != "CEW_COL02_OCCURRENCE_COVERAGE_CLOSURE":
        raise ValueError("unexpected COL-02 coverage closure schema")
    if coverage_closure.get("occurrence_coverage_complete") is not True:
        raise ValueError("COL-02 graphical occurrence coverage is not complete")
    if coverage_closure.get("proposal_count") != 611:
        raise ValueError("COL-02 proposal count drift")
    if coverage_closure.get("original_proposal_id_space_immutable") is not True:
        raise ValueError("COL-02 proposal ID space is not immutable")

    items: list[dict[str, Any]] = []

    panel_decisions = prototype_receipt.get("panel_decisions")
    if not isinstance(panel_decisions, list):
        raise ValueError("prototype receipt panel_decisions missing")
    for row in panel_decisions:
        if (
            row.get("column_graphic_decision") == "COLUMN_FOOTPRINT_CONFIRMED"
            and row.get("prototype_eligible") is True
        ):
            candidate_id = str(row.get("candidate_id") or "")
            panel_id = str(row.get("panel_id") or "")
            if not candidate_id or not panel_id:
                raise ValueError("prototype positive lacks panel/candidate identity")
            items.append(
                _base_item(
                    evidence_id=f"PROTO:{panel_id}:{candidate_id}",
                    candidate_id=candidate_id,
                    evidence_class="PROTOTYPE_CONFIRMED",
                    graphical_decision="COLUMN_FOOTPRINT_CONFIRMED",
                    discovery_path="HUMAN_PROTOTYPE_REVIEW",
                    human_review_receipt=PROTOTYPE_RECEIPT_PATH,
                    lineage={"panel_id": panel_id},
                )
            )

    guided_review = prototype_guided_receipt.get("human_review")
    if not isinstance(guided_review, dict) or not isinstance(guided_review.get("decisions"), list):
        raise ValueError("prototype-guided receipt decisions missing")
    for row in guided_review["decisions"]:
        if row.get("graphical_decision") == "COLUMN_FOOTPRINT_CONFIRMED":
            candidate_id = str(row.get("candidate_id") or "")
            panel_id = str(row.get("panel_id") or "")
            if not candidate_id or not panel_id:
                raise ValueError("prototype-guided positive lacks panel/candidate identity")
            items.append(
                _base_item(
                    evidence_id=f"GUIDED:{panel_id}:{candidate_id}",
                    candidate_id=candidate_id,
                    evidence_class="PROTOTYPE_GUIDED_CONFIRMED",
                    graphical_decision="COLUMN_FOOTPRINT_CONFIRMED",
                    discovery_path="PROTOTYPE_GUIDED_HUMAN_REVIEW",
                    human_review_receipt=PROTOTYPE_GUIDED_RECEIPT_PATH,
                    lineage={"panel_id": panel_id},
                )
            )

    replay = replay_mobile_review(mobile_receipt)
    for row in replay["decisions"]:
        if row.get("action") != "PILASTRO":
            continue
        candidate_id = str(row.get("candidate_id") or "")
        event_id = str(row.get("event_id") or "")
        if not candidate_id or not event_id:
            raise ValueError("residual direct positive lacks candidate/event identity")
        items.append(
            _base_item(
                evidence_id=f"RESIDUAL:{event_id}:{candidate_id}",
                candidate_id=candidate_id,
                evidence_class="RESIDUAL_DIRECT_CONFIRMED",
                graphical_decision="PILASTRO",
                discovery_path="RESIDUAL_MOBILE_DIRECT",
                human_review_receipt=MOBILE_RECEIPT_PATH,
                lineage={"event_id": event_id},
            )
        )

    decisions = reconciliation_receipt.get("decisions")
    if not isinstance(decisions, list):
        raise ValueError("reconciliation receipt decisions missing")
    eligible_by_candidate: dict[str, dict[str, Any]] = {}
    rejected_seen = False
    for row in decisions:
        candidate_id = str(row.get("candidate_id") or "")
        if row.get("repair_eligible") is True:
            if row.get("decision") != "FRAGMENTED_SYMBOL_INCOMPLETE_GEOMETRY":
                raise ValueError(f"unexpected repair-eligible decision: {candidate_id}")
            if not candidate_id or candidate_id in eligible_by_candidate:
                raise ValueError("repair-eligible candidates must be unique")
            eligible_by_candidate[candidate_id] = row
        elif candidate_id == REJECTED_CANDIDATE_ID:
            if row.get("decision") != "MISLOCALIZED_NOT_COLUMN" or row.get("repair_eligible") is not False:
                raise ValueError("COL02-FP-0106 rejection drift")
            rejected_seen = True
    if not rejected_seen:
        raise ValueError("COL02-FP-0106 terminal rejection missing")

    repairs = repair_manifest.get("repairs")
    if not isinstance(repairs, list):
        raise ValueError("repair manifest repairs missing")
    repair_by_candidate: dict[str, dict[str, Any]] = {}
    for row in repairs:
        candidate_id = str(row.get("source_candidate_id") or "")
        if not candidate_id or candidate_id in repair_by_candidate:
            raise ValueError("repair source candidates must be unique")
        repair_by_candidate[candidate_id] = row

    review_decisions = repair_review_receipt.get("decisions")
    if not isinstance(review_decisions, list):
        raise ValueError("repair review decisions missing")
    review_by_candidate: dict[str, dict[str, Any]] = {}
    for row in review_decisions:
        candidate_id = str(row.get("source_candidate_id") or "")
        if not candidate_id or candidate_id in review_by_candidate:
            raise ValueError("repair review source candidates must be unique")
        review_by_candidate[candidate_id] = row

    if set(repair_by_candidate) != set(eligible_by_candidate):
        raise ValueError("repair manifest candidate set differs from repair-eligible set")
    if set(review_by_candidate) != set(eligible_by_candidate):
        raise ValueError("repair review candidate set differs from repair-eligible set")

    tasks = reconciliation_manifest.get("review_tasks")
    if not isinstance(tasks, list):
        raise ValueError("reconciliation manifest review_tasks missing")
    task_by_candidate: dict[str, dict[str, Any]] = {}
    for task in tasks:
        candidate_id = _candidate_from_task(task)
        if candidate_id:
            if candidate_id in task_by_candidate:
                raise ValueError(f"duplicate reconciliation task candidate: {candidate_id}")
            task_by_candidate[candidate_id] = task

    points = reconciliation_manifest.get("point_reconciliation")
    if not isinstance(points, list):
        raise ValueError("reconciliation manifest point_reconciliation missing")
    point_events_by_candidate: dict[str, list[str]] = {}
    for row in points:
        candidate_id = str(row.get("proposal_candidate_id") or "")
        event_id = str(row.get("event_id") or "")
        if candidate_id and event_id and row.get("status") == "REVIEW_REQUIRED_EXISTING_PROPOSAL":
            point_events_by_candidate.setdefault(candidate_id, []).append(event_id)

    for candidate_id, decision in sorted(
        eligible_by_candidate.items(), key=lambda item: str(item[1].get("review_task_id") or "")
    ):
        repair = repair_by_candidate[candidate_id]
        review = review_by_candidate[candidate_id]
        if repair.get("status") != "READY_FOR_HUMAN_GRAPHICAL_REVIEW":
            raise ValueError(f"repair is not review-ready: {candidate_id}")
        if review.get("decision") != "PASS":
            raise ValueError(f"repair graphical review is not PASS: {candidate_id}")
        if str(review.get("repair_id") or "") != str(repair.get("repair_id") or ""):
            raise ValueError(f"repair/review lineage mismatch: {candidate_id}")

        task = task_by_candidate.get(candidate_id)
        if task is None:
            raise ValueError(f"missing reconciliation task for repaired candidate: {candidate_id}")
        task_type = str(task.get("task_type") or "")
        if task_type not in {"REFRAME_CONFIRMATION", "ADDITIONAL_OCCURRENCE_CONFIRMATION"}:
            raise ValueError(f"unsupported repaired discovery path: {candidate_id}")

        event_ids = sorted(set(point_events_by_candidate.get(candidate_id, [])))
        if task_type == "ADDITIONAL_OCCURRENCE_CONFIRMATION":
            task_event = str(task.get("event_id") or "")
            if task_event:
                event_ids = sorted(set(event_ids + [task_event]))
            if not event_ids:
                raise ValueError(f"human-added repaired occurrence lacks point lineage: {candidate_id}")
        else:
            event_ids = []

        repair_id = str(repair.get("repair_id") or "")
        if not repair_id:
            raise ValueError(f"repaired occurrence lacks repair_id: {candidate_id}")
        items.append(
            _base_item(
                evidence_id=f"REPAIR:{repair_id}:{candidate_id}",
                candidate_id=candidate_id,
                evidence_class="REPAIRED_SUCCESSOR_CONFIRMED",
                graphical_decision="PASS",
                discovery_path=task_type,
                human_review_receipt=REPAIR_REVIEW_RECEIPT_PATH,
                repair_id=repair_id,
                human_added_point_event_ids=event_ids,
                lineage={
                    "review_task_id": str(decision.get("review_task_id") or ""),
                    "reconciliation_decision": str(decision.get("decision") or ""),
                    "reconciliation_receipt": RECONCILIATION_RECEIPT_PATH,
                },
            )
        )

    if any(item["candidate_id"] == REJECTED_CANDIDATE_ID for item in items):
        raise ValueError("terminally rejected COL02-FP-0106 cannot be a COL-03A positive")
    evidence_ids = [str(item["evidence_id"]) for item in items]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("COL-03A evidence IDs must be unique")
    return items
