#!/usr/bin/env python3
"""Governed group review for acquisition-first CEW workflows.

One explicit human group action may classify many similarity candidates for
project-local prototype learning. The resulting append-only receipt keeps the
single human action and all child learning evidence together. This module does
not create EvidenceRegion identities, canonical CAD objects, structural
identity, or engineering authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import secrets
from typing import Any

import cew_document_discovery as discovery
import cew_runtime_audit_store as audit_store
import cew_visual_learning as learning

GROUP_RECEIPT_SCHEMA = "CEW_OA1_GROUP_REVIEW_RECEIPT_v1"
RUNTIME_STORE = Path(__file__).resolve().parents[1] / "runtime" / "oa1_group_review_receipts"

ACTION_TO_ROLE = {
    "CONFIRM_GROUP": "POSITIVE",
    "REJECT_GROUP": "NEGATIVE",
    "MARK_AMBIGUOUS": "AMBIGUOUS",
}

TRIAGE_THRESHOLDS = {
    "LIKELY_MATCH_MIN": 0.90,
    "REVIEW_MIN": 0.75,
}

AUTHORITY = {
    "candidate_authority": "WORKING_OBJECT_EVIDENCE_ONLY",
    "project_semantic_authority": "PROJECT_LOCAL_LEARNING_ONLY",
    "human_group_decision_recorded": True,
    "oa_g4_human_verified": False,
    "evidence_region_materialized": False,
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"OA1_GROUP_REVIEW_{field.upper()}_REQUIRED")
    return text


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: Any) -> str:
    return "sha256:" + sha256(_canonical(value).encode("utf-8")).hexdigest()


def load_group_receipts() -> dict[str, Any]:
    return audit_store.load_runtime_receipts(GROUP_RECEIPT_SCHEMA, RUNTIME_STORE)


def _project_learning_receipts(project_id: str, concept_id: str, meaning: str) -> list[dict[str, Any]]:
    loaded = learning.load_learning_receipts()
    return [
        row
        for row in loaded.get("receipts", [])
        if row.get("project_id") == project_id
        and row.get("concept_id") == concept_id
        and row.get("meaning") == meaning
    ]


def _project_group_receipts(project_id: str, concept_id: str, meaning: str) -> list[dict[str, Any]]:
    loaded = load_group_receipts()
    return [
        row
        for row in loaded.get("receipts", [])
        if row.get("project_id") == project_id
        and row.get("concept_id") == concept_id
        and row.get("meaning") == meaning
    ]


def _combined_memory(session: dict[str, Any], concept_id: str, meaning: str) -> dict[str, Any]:
    project_id = session["project_id"]
    receipts = list(_project_learning_receipts(project_id, concept_id, meaning))
    for group in _project_group_receipts(project_id, concept_id, meaning):
        children = group.get("learning_receipts") or []
        if not isinstance(children, list):
            raise ValueError("OA1_GROUP_REVIEW_CHILD_RECEIPTS_INVALID")
        receipts.extend(children)
    return learning.replay_memory(
        project_id=project_id,
        concept_id=concept_id,
        meaning=meaning,
        receipts=receipts,
    )


def _bucket(score: float) -> str:
    if score >= TRIAGE_THRESHOLDS["LIKELY_MATCH_MIN"]:
        return "LIKELY_MATCH"
    if score >= TRIAGE_THRESHOLDS["REVIEW_MIN"]:
        return "REVIEW"
    return "OUTLIER"


def proposal(session_id: str, concept_id: str, meaning: str, limit: int = 80) -> dict[str, Any]:
    session = discovery.get_session(session_id)
    concept_id = _text(concept_id, "concept_id")
    meaning = _text(meaning, "meaning")
    memory = _combined_memory(session, concept_id, meaning)
    if memory["example_counts"]["POSITIVE"] < 1:
        raise ValueError("OA1_GROUP_REVIEW_POSITIVE_PROTOTYPE_REQUIRED")

    ranked = learning.rank_preacquisition_candidates(
        memory,
        session["report"]["primitive_candidates"],
        limit=max(1, min(100, int(limit))),
    )
    candidates = discovery.candidate_map(session)
    reviewed = {row["candidate_id"] for row in memory["examples"]}
    rows: list[dict[str, Any]] = []
    for result in ranked["candidates"]:
        candidate = candidates[result["candidate_id"]]
        score = float(result["fused_score"])
        bucket = _bucket(score)
        already_reviewed = result["candidate_id"] in reviewed
        rows.append(
            {
                **result,
                "bbox": candidate["bbox"],
                "primitive_family": candidate["primitive_family"],
                "feature_signature": candidate["feature_signature"],
                "triage_bucket": bucket,
                "already_reviewed": already_reviewed,
                "recommended_selection": bucket == "LIKELY_MATCH" and not already_reviewed,
                "triage_is_classification": False,
            }
        )

    fingerprint_payload = {
        "session_id": session_id,
        "project_id": session["project_id"],
        "source_version_id": session["source_version_id"],
        "concept_id": concept_id,
        "meaning": meaning,
        "memory_fingerprint": memory.get("memory_fingerprint"),
        "candidates": [
            {
                "candidate_id": row["candidate_id"],
                "score": row["fused_score"],
                "bucket": row["triage_bucket"],
                "already_reviewed": row["already_reviewed"],
            }
            for row in rows
        ],
    }
    return {
        "schema": "CEW_OA1_GROUP_REVIEW_PROPOSAL_v1",
        "state": "GROUP_REVIEW_PROPOSAL_READY",
        "session_id": session_id,
        "project_id": session["project_id"],
        "source_id": session["source_id"],
        "source_version_id": session["source_version_id"],
        "concept_id": concept_id,
        "meaning": meaning,
        "memory_fingerprint": memory.get("memory_fingerprint"),
        "proposal_fingerprint": _fingerprint(fingerprint_payload),
        "candidate_count": len(rows),
        "candidates": rows,
        "bucket_counts": {
            name: sum(1 for row in rows if row["triage_bucket"] == name)
            for name in ("LIKELY_MATCH", "REVIEW", "OUTLIER")
        },
        "triage_thresholds": dict(TRIAGE_THRESHOLDS),
        "automatic_classification": False,
        "human_group_decision_required": True,
        "authority": dict(AUTHORITY),
    }


def _build_child_receipt(
    *,
    session: dict[str, Any],
    candidate: dict[str, Any],
    concept_id: str,
    meaning: str,
    reviewer: str,
    role: str,
    rationale: str,
    group_decision_id: str,
    index: int,
    timestamp: str,
) -> dict[str, Any]:
    page = session["page_registry"].get(int(candidate["page_index"]))
    if page is None or page.get("readiness_state") != "READY":
        raise ValueError("OA1_GROUP_REVIEW_READY_PAGE_REQUIRED")
    if candidate.get("source_version_id") != page.get("source_version_id"):
        raise ValueError("OA1_GROUP_REVIEW_SOURCE_VERSION_DRIFT")
    embedding = learning.structured_embedding_from_candidate(candidate)
    evidence_fingerprint = discovery._evidence_fingerprint(session, candidate, page)
    return learning.build_learning_receipt(
        decision_id=f"{group_decision_id}-{index:03d}",
        project_id=session["project_id"],
        concept_id=concept_id,
        meaning=meaning,
        reviewer=reviewer,
        role=role,
        candidate_id=candidate["candidate_id"],
        source_version_id=page["source_version_id"],
        page_id=page["page_id"],
        evidence_fingerprint=evidence_fingerprint,
        embedding=embedding,
        rationale=f"Group review {group_decision_id}: {rationale}",
        timestamp=timestamp,
    )


def record_group_review(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    session = discovery.get_session(session_id)
    if not session.get("teaching_enabled"):
        raise ValueError("OA1_GROUP_REVIEW_GOVERNED_SOURCE_REQUIRED")

    concept_id = _text(payload.get("concept_id"), "concept_id")
    meaning = _text(payload.get("meaning"), "meaning")
    reviewer = _text(payload.get("reviewer"), "reviewer")
    rationale = _text(payload.get("rationale"), "rationale")
    action = _text(payload.get("action"), "action").upper()
    if action not in ACTION_TO_ROLE:
        raise ValueError("OA1_GROUP_REVIEW_ACTION_INVALID")
    role = ACTION_TO_ROLE[action]

    raw_ids = payload.get("candidate_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("OA1_GROUP_REVIEW_CANDIDATES_REQUIRED")
    candidate_ids = [str(value or "").strip() for value in raw_ids]
    if any(not value for value in candidate_ids) or len(candidate_ids) > 100:
        raise ValueError("OA1_GROUP_REVIEW_CANDIDATE_SET_INVALID")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("OA1_GROUP_REVIEW_DUPLICATE_CANDIDATE")

    current = proposal(session_id, concept_id, meaning, 100)
    supplied_fingerprint = _text(payload.get("proposal_fingerprint"), "proposal_fingerprint")
    if supplied_fingerprint != current["proposal_fingerprint"]:
        raise ValueError("OA1_GROUP_REVIEW_STALE_PROPOSAL")

    proposal_rows = {row["candidate_id"]: row for row in current["candidates"]}
    candidates = discovery.candidate_map(session)
    for candidate_id in candidate_ids:
        row = proposal_rows.get(candidate_id)
        if row is None:
            raise ValueError("OA1_GROUP_REVIEW_CANDIDATE_OUTSIDE_PROPOSAL")
        if row["already_reviewed"]:
            raise ValueError("OA1_GROUP_REVIEW_CANDIDATE_ALREADY_REVIEWED")
        if candidate_id not in candidates:
            raise ValueError("OA1_GROUP_REVIEW_CANDIDATE_NOT_FOUND")

    memory = _combined_memory(session, concept_id, meaning)
    if role in {"NEGATIVE", "AMBIGUOUS"} and memory["example_counts"]["POSITIVE"] < 1:
        raise ValueError("OA1_GROUP_REVIEW_POSITIVE_PROTOTYPE_REQUIRED")

    timestamp = datetime.now(timezone.utc).isoformat()
    group_decision_id = "OA1-GROUP-" + secrets.token_hex(12)
    children = [
        _build_child_receipt(
            session=session,
            candidate=candidates[candidate_id],
            concept_id=concept_id,
            meaning=meaning,
            reviewer=reviewer,
            role=role,
            rationale=rationale,
            group_decision_id=group_decision_id,
            index=index,
            timestamp=timestamp,
        )
        for index, candidate_id in enumerate(candidate_ids, 1)
    ]

    receipt: dict[str, Any] = {
        "receipt_type": GROUP_RECEIPT_SCHEMA,
        "schema": GROUP_RECEIPT_SCHEMA,
        "group_decision_id": group_decision_id,
        "timestamp": timestamp,
        "project_id": session["project_id"],
        "source_id": session["source_id"],
        "source_version_id": session["source_version_id"],
        "source_sha256": session["source_sha256"],
        "concept_id": concept_id,
        "meaning": meaning,
        "reviewer": reviewer,
        "human_action": action,
        "learning_role": role,
        "rationale": rationale,
        "proposal_fingerprint": supplied_fingerprint,
        "candidate_ids": candidate_ids,
        "candidate_count": len(candidate_ids),
        "learning_receipts": children,
        "group_action_is_explicit_human_decision": True,
        "group_action_creates_structural_identity": False,
        "group_action_creates_canonical_cad": False,
        "group_action_satisfies_oa_g4": False,
        "oa_g4_blocker": "EVIDENCE_REGION_MATERIALIZATION_AND_GOVERNED_OBJECT_CONFIRMATION_REQUIRED",
        "next_gate": "EVIDENCE_REGION_MATERIALIZATION_REQUIRED_BEFORE_OA_G4",
        "authority": dict(AUTHORITY),
    }
    receipt["receipt_fingerprint"] = _fingerprint(
        {key: value for key, value in receipt.items() if key != "receipt_fingerprint"}
    )
    persisted = audit_store.persist_runtime_receipt(receipt, RUNTIME_STORE)
    updated = _combined_memory(session, concept_id, meaning)
    return {
        "state": "OA1_GROUP_REVIEW_RECORDED",
        "group_decision_id": group_decision_id,
        "human_action": action,
        "learning_role": role,
        "candidate_count": len(candidate_ids),
        "candidate_ids": candidate_ids,
        "example_counts": updated["example_counts"],
        "memory_fingerprint": updated["memory_fingerprint"],
        "audit_backend": persisted["audit_backend"],
        "next_gate": receipt["next_gate"],
        "authority": dict(AUTHORITY),
    }
