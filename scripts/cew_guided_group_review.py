#!/usr/bin/env python3
"""Guided batch review for CEW project-local prototype learning.

One explicit human action may validate a selected similarity group as project-local
training evidence. The receipt is append-only and replayable, but it never grants
CAD, structural, canonical, or engineering authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import secrets
from typing import Any, Iterable

import cew_runtime_audit_store as audit_store
import cew_visual_learning as learning

RECEIPT_SCHEMA = "CEW_GUIDED_GROUP_REVIEW_RECEIPT_v1"
SNAPSHOT_SCHEMA = "CEW_GUIDED_GROUP_REVIEW_SNAPSHOT_v1"
RUNTIME_STORE = Path(__file__).resolve().parents[1] / "runtime" / "guided_group_review_receipts"

ACTION_TO_ROLE = {
    "CONFIRM_SELECTED": "POSITIVE",
    "REJECT_SELECTED": "NEGATIVE",
    "MARK_SELECTED_AMBIGUOUS": "AMBIGUOUS",
}

# Display/review bands only. They are not object classifications.
HIGH_SIMILARITY_MIN = 0.85
REVIEW_BAND_MIN = 0.60

AUTHORITY = {
    "project_semantic_authority": "NONE",
    "oar_human_confirmation": False,
    "oar_classification_confirmed": False,
    "f2_registry_written": False,
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
    "human_project_validation_required": True,
}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha_json(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"GUIDED_GROUP_REVIEW_{field.upper()}_REQUIRED")
    return text


def similarity_band(score: float) -> str:
    value = float(score)
    if value >= HIGH_SIMILARITY_MIN:
        return "HIGH_SIMILARITY_PROPOSAL"
    if value >= REVIEW_BAND_MIN:
        return "REVIEW_PROPOSAL"
    return "LOW_SIMILARITY_PROPOSAL"


def build_snapshot(
    *,
    project_id: str,
    concept_id: str,
    meaning: str,
    memory_fingerprint: str,
    candidates: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    members: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in candidates:
        candidate_id = _text(raw.get("candidate_id"), "candidate_id")
        if candidate_id in seen:
            raise ValueError("GUIDED_GROUP_REVIEW_DUPLICATE_CANDIDATE")
        seen.add(candidate_id)
        score = float(raw.get("fused_score"))
        embedding = raw.get("embedding")
        if not isinstance(embedding, dict):
            raise ValueError("GUIDED_GROUP_REVIEW_EMBEDDING_REQUIRED")
        learning.validate_embedding(embedding)
        members.append(
            {
                "candidate_id": candidate_id,
                "source_version_id": _text(raw.get("source_version_id"), "source_version_id"),
                "page_id": _text(raw.get("page_id"), "page_id"),
                "page_index": int(raw.get("page_index")),
                "bbox": raw.get("bbox"),
                "primitive_family": raw.get("primitive_family"),
                "evidence_fingerprint": _text(raw.get("evidence_fingerprint"), "evidence_fingerprint"),
                "embedding": embedding,
                "fused_score": round(score, 6),
                "similarity_band": similarity_band(score),
                "is_training_example": bool(raw.get("is_training_example", False)),
            }
        )
    members.sort(key=lambda row: (-row["fused_score"], row["candidate_id"]))
    identity = {
        "project_id": _text(project_id, "project_id"),
        "concept_id": _text(concept_id, "concept_id"),
        "meaning": _text(meaning, "meaning"),
        "memory_fingerprint": _text(memory_fingerprint, "memory_fingerprint"),
        "members": [
            {
                "candidate_id": row["candidate_id"],
                "source_version_id": row["source_version_id"],
                "page_id": row["page_id"],
                "evidence_fingerprint": row["evidence_fingerprint"],
                "fused_score": row["fused_score"],
                "similarity_band": row["similarity_band"],
                "is_training_example": row["is_training_example"],
            }
            for row in members
        ],
    }
    counts = {
        "HIGH_SIMILARITY_PROPOSAL": sum(row["similarity_band"] == "HIGH_SIMILARITY_PROPOSAL" for row in members),
        "REVIEW_PROPOSAL": sum(row["similarity_band"] == "REVIEW_PROPOSAL" for row in members),
        "LOW_SIMILARITY_PROPOSAL": sum(row["similarity_band"] == "LOW_SIMILARITY_PROPOSAL" for row in members),
    }
    return {
        "schema": SNAPSHOT_SCHEMA,
        **identity,
        "group_fingerprint": "sha256:" + _sha_json(identity),
        "candidate_count": len(members),
        "band_counts": counts,
        "members": members,
        "default_selected_candidate_ids": [
            row["candidate_id"]
            for row in members
            if row["similarity_band"] == "HIGH_SIMILARITY_PROPOSAL" and not row["is_training_example"]
        ],
        "automatic_classification": False,
        "group_review_required": True,
        "authority": dict(AUTHORITY),
    }


def build_receipt(
    snapshot: dict[str, Any],
    *,
    action: str,
    selected_candidate_ids: Iterable[str],
    reviewer: str,
    rationale: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError("GUIDED_GROUP_REVIEW_SNAPSHOT_SCHEMA_INVALID")
    action = _text(action, "action").upper()
    role = ACTION_TO_ROLE.get(action)
    if role is None:
        raise ValueError("GUIDED_GROUP_REVIEW_ACTION_INVALID")
    reviewer = _text(reviewer, "reviewer")
    rationale = _text(rationale, "rationale")
    selected = [str(value).strip() for value in selected_candidate_ids if str(value).strip()]
    if not selected or len(selected) != len(set(selected)):
        raise ValueError("GUIDED_GROUP_REVIEW_SELECTION_INVALID")
    member_map = {row["candidate_id"]: row for row in snapshot.get("members") or []}
    if any(candidate_id not in member_map for candidate_id in selected):
        raise ValueError("GUIDED_GROUP_REVIEW_SELECTION_OUTSIDE_SNAPSHOT")
    if any(member_map[candidate_id].get("is_training_example") for candidate_id in selected):
        raise ValueError("GUIDED_GROUP_REVIEW_TRAINING_EXAMPLE_RESELECTION_FORBIDDEN")

    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    decision_id = "GGR-" + secrets.token_hex(16)
    child_receipts = []
    for candidate_id in sorted(selected):
        row = member_map[candidate_id]
        child_id = f"{decision_id}-{_sha_json(candidate_id)[:12]}"
        child_receipts.append(
            learning.build_learning_receipt(
                decision_id=child_id,
                project_id=snapshot["project_id"],
                concept_id=snapshot["concept_id"],
                meaning=snapshot["meaning"],
                reviewer=reviewer,
                role=role,
                candidate_id=candidate_id,
                source_version_id=row["source_version_id"],
                page_id=row["page_id"],
                evidence_fingerprint=row["evidence_fingerprint"],
                embedding=row["embedding"],
                rationale=f"Group decision {decision_id}: {rationale}",
                timestamp=timestamp,
            )
        )

    receipt = {
        "receipt_type": RECEIPT_SCHEMA,
        "schema": RECEIPT_SCHEMA,
        "decision_id": decision_id,
        "task_id": snapshot["concept_id"],
        "residual_id": snapshot["group_fingerprint"],
        "timestamp": timestamp,
        "project_id": snapshot["project_id"],
        "concept_id": snapshot["concept_id"],
        "meaning": snapshot["meaning"],
        "memory_fingerprint_before": snapshot["memory_fingerprint"],
        "group_fingerprint": snapshot["group_fingerprint"],
        "action": action,
        "learning_role": role,
        "reviewer": reviewer,
        "rationale": rationale,
        "selected_candidate_ids": sorted(selected),
        "selected_count": len(selected),
        "derived_learning_receipts": child_receipts,
        "human_group_decision": True,
        "learning_effect": "PROJECT_LOCAL_PROTOTYPE_MEMORY_ONLY",
        "canonical_write": False,
        "authority": dict(AUTHORITY),
    }
    receipt["receipt_fingerprint"] = "sha256:" + _sha_json(
        {key: value for key, value in receipt.items() if key != "receipt_fingerprint"}
    )
    return receipt


def validate_receipt(receipt: dict[str, Any]) -> None:
    if receipt.get("receipt_type") != RECEIPT_SCHEMA or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("GUIDED_GROUP_REVIEW_RECEIPT_SCHEMA_INVALID")
    if receipt.get("human_group_decision") is not True:
        raise ValueError("GUIDED_GROUP_REVIEW_HUMAN_DECISION_REQUIRED")
    if receipt.get("canonical_write") is not False:
        raise ValueError("GUIDED_GROUP_REVIEW_CANONICAL_WRITE_FORBIDDEN")
    authority = receipt.get("authority") or {}
    for key in ("canonical_write_authorized", "structural_identity_authorized", "oar_classification_confirmed"):
        if authority.get(key) is not False:
            raise ValueError(f"GUIDED_GROUP_REVIEW_AUTHORITY_DRIFT:{key}")
    expected = "sha256:" + _sha_json(
        {key: value for key, value in receipt.items() if key != "receipt_fingerprint"}
    )
    if receipt.get("receipt_fingerprint") != expected:
        raise ValueError("GUIDED_GROUP_REVIEW_RECEIPT_FINGERPRINT_MISMATCH")
    children = receipt.get("derived_learning_receipts")
    if not isinstance(children, list) or len(children) != int(receipt.get("selected_count", -1)):
        raise ValueError("GUIDED_GROUP_REVIEW_CHILD_RECEIPT_COUNT_MISMATCH")
    for child in children:
        if child.get("project_id") != receipt.get("project_id"):
            raise ValueError("GUIDED_GROUP_REVIEW_CHILD_PROJECT_MISMATCH")
        if child.get("concept_id") != receipt.get("concept_id"):
            raise ValueError("GUIDED_GROUP_REVIEW_CHILD_CONCEPT_MISMATCH")
        if child.get("role") != receipt.get("learning_role"):
            raise ValueError("GUIDED_GROUP_REVIEW_CHILD_ROLE_MISMATCH")
        if (child.get("authority") or {}).get("canonical_write_authorized") is not False:
            raise ValueError("GUIDED_GROUP_REVIEW_CHILD_AUTHORITY_DRIFT")


def persist_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    validate_receipt(receipt)
    return audit_store.persist_runtime_receipt(receipt, RUNTIME_STORE)


def load_receipts() -> dict[str, Any]:
    return audit_store.load_runtime_receipts(RECEIPT_SCHEMA, RUNTIME_STORE)


def learning_receipts_for_memory(project_id: str, concept_id: str, meaning: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for receipt in load_receipts().get("receipts", []):
        validate_receipt(receipt)
        if receipt.get("project_id") != project_id:
            continue
        if receipt.get("concept_id") != concept_id or receipt.get("meaning") != meaning:
            continue
        output.extend(receipt["derived_learning_receipts"])
    return output
