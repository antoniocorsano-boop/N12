#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

RECEIPT_TYPE = "CEW_OA_GOVERNED_DECISION_RECEIPT_V1"
STAGE_ORDER = {
    "OA2_PROTOTYPE": 2,
    "OA4_CLUSTER_REVIEW": 4,
    "OA5_IDENTITY_CANDIDATE": 5,
    "OA_G5_IDENTITY_DECISION": 6,
}
PARENT_STAGE = {
    "OA2_PROTOTYPE": None,
    "OA4_CLUSTER_REVIEW": "OA2_PROTOTYPE",
    "OA5_IDENTITY_CANDIDATE": "OA4_CLUSTER_REVIEW",
    "OA_G5_IDENTITY_DECISION": "OA5_IDENTITY_CANDIDATE",
}
SOURCE_FIELDS = ("source_version_id", "page_id", "evidence_region_id", "source_sha256")
OAG5_DECISIONS = {
    "ACCEPT_STRUCTURAL_IDENTITY",
    "REJECT_STRUCTURAL_IDENTITY",
    "DEFER_NEEDS_MORE_EVIDENCE",
}


def _raw(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(_raw(value).encode("utf-8")).hexdigest()


def source_evidence_from_context(ctx: dict[str, Any]) -> dict[str, str]:
    source = ctx.get("source") or {}
    binding = ctx.get("binding") or {}
    page = ctx.get("page") or {}
    region = ctx.get("region") or {}
    evidence = {
        "source_version_id": str(binding.get("source_version_id", "")).strip(),
        "page_id": str(page.get("page_id", binding.get("page_id", ""))).strip(),
        "evidence_region_id": str(region.get("evidence_region_id", binding.get("evidence_region_id", ""))).strip(),
        "source_sha256": str(source.get("sha256", "")).strip().lower(),
    }
    if not all(evidence.values()):
        raise ValueError("OA_GOVERNED_SOURCE_EVIDENCE_INCOMPLETE")
    return evidence


def validate_source_evidence(payload: dict[str, Any], expected: dict[str, str]) -> None:
    supplied = payload.get("source_evidence")
    if not isinstance(supplied, dict):
        raise ValueError("OA_GOVERNED_SOURCE_EVIDENCE_REQUIRED")
    for field in SOURCE_FIELDS:
        if str(supplied.get(field, "")).strip().lower() != str(expected[field]).strip().lower():
            raise ValueError(f"OA_GOVERNED_SOURCE_MISMATCH_{field.upper()}")


def _authority_guards(stage: str, payload: dict[str, Any]) -> None:
    forbidden_true = (
        "canonical_write_authorized",
        "project_material_ready",
        "project_material_promotion_authorized",
    )
    for field in forbidden_true:
        if payload.get(field) is True:
            raise ValueError(f"OA_GOVERNED_FORBIDDEN_AUTHORITY_{field.upper()}")
    if stage != "OA_G5_IDENTITY_DECISION" and payload.get("accepted_structural_identity") is True:
        raise ValueError("OA_GOVERNED_IDENTITY_ACCEPTANCE_BEFORE_OAG5")
    if stage == "OA_G5_IDENTITY_DECISION":
        decision = str(payload.get("decision", "")).strip()
        if decision not in OAG5_DECISIONS:
            raise ValueError("OA_GOVERNED_OAG5_EXPLICIT_DECISION_REQUIRED")
        if decision == "ACCEPT_STRUCTURAL_IDENTITY" and payload.get("human_attestation") is not True:
            raise ValueError("OA_GOVERNED_OAG5_HUMAN_ATTESTATION_REQUIRED")


def validate_parent(stage: str, parent: dict[str, Any] | None, expected_source: dict[str, str]) -> None:
    required = PARENT_STAGE[stage]
    if required is None:
        if parent is not None:
            raise ValueError("OA_GOVERNED_OA2_PARENT_FORBIDDEN")
        return
    if not isinstance(parent, dict):
        raise ValueError("OA_GOVERNED_PARENT_REQUIRED")
    if parent.get("receipt_type") != RECEIPT_TYPE or parent.get("stage") != required:
        raise ValueError("OA_GOVERNED_PARENT_STAGE_MISMATCH")
    if parent.get("canonical_write_authorized") is not False:
        raise ValueError("OA_GOVERNED_PARENT_AUTHORITY_INVALID")
    parent_source = parent.get("source_evidence")
    if not isinstance(parent_source, dict):
        raise ValueError("OA_GOVERNED_PARENT_SOURCE_MISSING")
    for field in SOURCE_FIELDS:
        if str(parent_source.get(field, "")).strip().lower() != str(expected_source[field]).strip().lower():
            raise ValueError("OA_GOVERNED_PARENT_SOURCE_MISMATCH")


def build_receipt(
    *,
    task_id: str,
    stage: str,
    payload: dict[str, Any],
    expected_source: dict[str, str],
    revision: str,
    reviewer: str,
    parent: dict[str, Any] | None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    task_id = task_id.strip()
    revision = revision.strip()
    reviewer = reviewer.strip()
    if not task_id:
        raise ValueError("OA_GOVERNED_TASK_REQUIRED")
    if stage not in STAGE_ORDER:
        raise ValueError("OA_GOVERNED_STAGE_INVALID")
    if not isinstance(payload, dict):
        raise ValueError("OA_GOVERNED_PAYLOAD_OBJECT_REQUIRED")
    if not revision:
        raise ValueError("OA_GOVERNED_REVISION_REQUIRED")
    if not reviewer:
        raise ValueError("OA_GOVERNED_REVIEWER_REQUIRED")
    validate_source_evidence(payload, expected_source)
    validate_parent(stage, parent, expected_source)
    _authority_guards(stage, payload)

    parent_id = parent.get("decision_id") if parent else None
    parent_fp = parent.get("receipt_fingerprint") if parent else None
    payload_fp = fingerprint(payload)
    decision_seed = {
        "task_id": task_id,
        "stage": stage,
        "revision": revision,
        "reviewer": reviewer,
        "payload_fingerprint": payload_fp,
        "parent_decision_id": parent_id,
        "parent_receipt_fingerprint": parent_fp,
    }
    decision_id = "OA-" + stage.replace("_", "-") + "-" + fingerprint(decision_seed)[:20]
    receipt = {
        "receipt_type": RECEIPT_TYPE,
        "decision_id": decision_id,
        "task_id": task_id,
        "stage": stage,
        "stage_order": STAGE_ORDER[stage],
        "revision": revision,
        "reviewer": reviewer,
        "source_evidence": dict(expected_source),
        "payload_fingerprint": payload_fp,
        "payload": payload,
        "parent_decision_id": parent_id,
        "parent_receipt_fingerprint": parent_fp,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "authority": "OA_GOVERNED_AUDIT_DECISION",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "IDENTITY_REVIEW_ONLY" if stage == "OA_G5_IDENTITY_DECISION" else "NONE",
        "project_material_ready": False,
    }
    receipt["receipt_fingerprint"] = fingerprint({k: v for k, v in receipt.items() if k != "receipt_fingerprint"})
    return receipt


def index_receipts(receipts: list[dict[str, Any]], task_id: str) -> dict[str, dict[str, Any]]:
    rows = [r for r in receipts if r.get("receipt_type") == RECEIPT_TYPE and r.get("task_id") == task_id]
    rows.sort(key=lambda r: (int(r.get("stage_order", 0)), str(r.get("timestamp", "")), str(r.get("decision_id", ""))))
    return {str(r["decision_id"]): r for r in rows if r.get("decision_id")}


def latest_stage_receipt(receipts: list[dict[str, Any]], task_id: str, stage: str) -> dict[str, Any] | None:
    rows = [r for r in receipts if r.get("receipt_type") == RECEIPT_TYPE and r.get("task_id") == task_id and r.get("stage") == stage]
    rows.sort(key=lambda r: (str(r.get("timestamp", "")), str(r.get("decision_id", ""))))
    return rows[-1] if rows else None
