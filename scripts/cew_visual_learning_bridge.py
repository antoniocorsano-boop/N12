#!/usr/bin/env python3
"""Bridge CEW zero-prior pre-acquisition to project-local prototype learning.

The bridge never mutates the pre-acquisition report and never assigns semantics.
It produces a learning overlay for the human triage queue and can build a
LearningReceipt from an exact source-bound primitive candidate selected by the
human.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

import cew_visual_learning as learning

PREACQUISITION_SCHEMA = "CEW_NEW_PROJECT_PREACQUISITION_REPORT_v1"
OVERLAY_SCHEMA = "CEW_LEARNING_TRIAGE_OVERLAY_v1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _validate_report(report: dict[str, Any]) -> None:
    if report.get("schema") != PREACQUISITION_SCHEMA:
        raise ValueError("VISUAL_LEARNING_PREACQUISITION_SCHEMA_INVALID")
    if report.get("semantic_labels_assigned_automatically") is not False:
        raise ValueError("VISUAL_LEARNING_PREACQUISITION_AUTHORITY_DRIFT")
    authority = report.get("authority") or {}
    if authority.get("canonical_write_authorized") is not False:
        raise ValueError("VISUAL_LEARNING_PREACQUISITION_AUTHORITY_DRIFT")


def _candidate_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = report.get("primitive_candidates") or []
    index: dict[str, dict[str, Any]] = {}
    for candidate in rows:
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id or candidate_id in index:
            raise ValueError("VISUAL_LEARNING_CANDIDATE_ID_INVALID_OR_DUPLICATE")
        index[candidate_id] = candidate
    return index


def build_learning_receipt_from_candidate(
    report: dict[str, Any],
    *,
    candidate_id: str,
    project_id: str,
    concept_id: str,
    meaning: str,
    reviewer: str,
    role: str,
    page_id: str,
    rationale: str,
    decision_id: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    _validate_report(report)
    candidate = _candidate_index(report).get(str(candidate_id))
    if candidate is None:
        raise ValueError("VISUAL_LEARNING_CANDIDATE_NOT_FOUND")
    if candidate.get("source_version_id") != report.get("source_version_id"):
        raise ValueError("VISUAL_LEARNING_CANDIDATE_SOURCE_MISMATCH")
    embedding = learning.structured_embedding_from_candidate(candidate)
    evidence_fingerprint = "sha256:" + _sha256(
        {
            "report_fingerprint": report.get("report_fingerprint"),
            "source_version_id": candidate.get("source_version_id"),
            "page_index": candidate.get("page_index"),
            "candidate_id": candidate.get("candidate_id"),
            "bbox": candidate.get("bbox"),
            "feature_signature": candidate.get("feature_signature"),
        }
    )
    return learning.build_learning_receipt(
        decision_id=decision_id,
        project_id=project_id,
        concept_id=concept_id,
        meaning=meaning,
        reviewer=reviewer,
        role=role,
        candidate_id=candidate_id,
        source_version_id=str(candidate["source_version_id"]),
        page_id=page_id,
        evidence_fingerprint=evidence_fingerprint,
        embedding=embedding,
        rationale=rationale,
        timestamp=timestamp,
    )


def build_learning_overlay(
    report: dict[str, Any],
    *,
    project_id: str,
    memories: Iterable[dict[str, Any]],
    per_concept_limit: int = 100,
) -> dict[str, Any]:
    _validate_report(report)
    candidate_index = _candidate_index(report)
    candidate_to_cluster: dict[str, str] = {}
    for cluster in report.get("graphic_clusters") or []:
        cluster_id = str(cluster.get("cluster_id") or "")
        for candidate_id in cluster.get("member_candidate_ids") or []:
            if candidate_id not in candidate_index:
                raise ValueError("VISUAL_LEARNING_CLUSTER_MEMBER_UNKNOWN")
            if candidate_id in candidate_to_cluster:
                raise ValueError("VISUAL_LEARNING_CANDIDATE_IN_MULTIPLE_CLUSTERS")
            candidate_to_cluster[candidate_id] = cluster_id

    cluster_suggestions: dict[str, list[dict[str, Any]]] = {}
    memory_refs: list[dict[str, Any]] = []
    for memory in memories:
        if memory.get("schema") != learning.MEMORY_SCHEMA:
            raise ValueError("VISUAL_LEARNING_MEMORY_SCHEMA_INVALID")
        if memory.get("project_id") != project_id:
            raise ValueError("VISUAL_LEARNING_PROJECT_MISMATCH")
        if memory.get("scope") != "PROJECT_LOCAL":
            raise ValueError("VISUAL_LEARNING_NON_PROJECT_LOCAL_MEMORY_NOT_ALLOWED")
        ranked = learning.rank_preacquisition_candidates(
            memory,
            candidate_index.values(),
            limit=per_concept_limit,
        )
        memory_refs.append(
            {
                "concept_id": memory["concept_id"],
                "meaning": memory["meaning"],
                "memory_fingerprint": memory.get("memory_fingerprint"),
                "example_counts": memory.get("example_counts"),
            }
        )
        grouped: dict[str, list[dict[str, Any]]] = {}
        for result in ranked["candidates"]:
            cluster_id = candidate_to_cluster.get(result["candidate_id"])
            if cluster_id is None:
                continue
            grouped.setdefault(cluster_id, []).append(result)
        for cluster_id, rows in grouped.items():
            rows.sort(key=lambda row: (-float(row["fused_score"]), row["candidate_id"]))
            best = rows[0]
            cluster_suggestions.setdefault(cluster_id, []).append(
                {
                    "concept_id": memory["concept_id"],
                    "meaning": memory["meaning"],
                    "memory_fingerprint": memory.get("memory_fingerprint"),
                    "best_score": best["fused_score"],
                    "matched_candidate_ids": [row["candidate_id"] for row in rows[:8]],
                    "component_scores": best["component_scores"],
                    "proposal_state": "LEARNED_SIMILARITY_PROPOSAL",
                    "semantic_assignment": None,
                    "human_project_validation_required": True,
                }
            )

    triage_overlay: list[dict[str, Any]] = []
    for triage in report.get("human_triage_queue") or []:
        cluster_id = str(triage.get("cluster_id") or "")
        suggestions = cluster_suggestions.get(cluster_id, [])
        suggestions.sort(key=lambda row: (-float(row["best_score"]), row["concept_id"]))
        triage_overlay.append(
            {
                "cluster_id": cluster_id,
                "learned_prototype_suggestions": suggestions,
                "semantic_authority_before_human_action": "NONE",
                "allowed_learning_actions": [
                    "TEACH_THIS_IS",
                    "CONFIRM_POSITIVE",
                    "MARK_NEGATIVE",
                    "MARK_AMBIGUOUS",
                ],
            }
        )

    return {
        "schema": OVERLAY_SCHEMA,
        "project_id": project_id,
        "source_version_id": report["source_version_id"],
        "preacquisition_report_fingerprint": report["report_fingerprint"],
        "memory_refs": memory_refs,
        "triage_overlay": triage_overlay,
        "automatic_semantic_assignment": False,
        "authority": dict(learning.AUTHORITY),
    }
