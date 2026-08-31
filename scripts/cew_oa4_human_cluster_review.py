#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from typing import Any

ALLOWED_DECISIONS = {
    "CONFIRM_AS_FAMILY_CANDIDATE",
    "REJECT",
    "MOVE_TO_OTHER_FAMILY",
    "MARK_AMBIGUOUS",
    "DEFER_NEEDS_SOURCE",
}


def similarity_fingerprint(similarity: dict[str, Any]) -> str:
    seed = json.dumps(
        {
            "state": similarity.get("state"),
            "prototype_id": similarity.get("prototype_id"),
            "family_id": similarity.get("family_id"),
            "weights": similarity.get("weights"),
            "candidates": [
                {
                    "candidate_object_id": row.get("candidate_object_id"),
                    "score": row.get("score"),
                    "state": row.get("state"),
                    "reason_codes": row.get("reason_codes"),
                }
                for row in similarity.get("candidates", [])
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(seed).hexdigest()


def review_candidates(
    similarity: dict[str, Any],
    decisions: list[dict[str, Any]],
    reviewer: str,
    revision: str,
    source_evidence: dict[str, Any],
) -> dict[str, Any]:
    if similarity.get("state") != "DETERMINISTIC_SIMILARITY_CANDIDATES":
        raise ValueError("OA4_SIMILARITY_CANDIDATES_REQUIRED")
    if not reviewer.strip():
        raise ValueError("OA4_REVIEWER_REQUIRED")
    if not revision.strip():
        raise ValueError("OA4_REVISION_REQUIRED")
    required_evidence = {"source_version_id", "page_id", "evidence_region_id", "source_sha256"}
    if not required_evidence.issubset(source_evidence) or any(not source_evidence[k] for k in required_evidence):
        raise ValueError("OA4_SOURCE_EVIDENCE_INCOMPLETE")

    candidate_map = {row.get("candidate_object_id"): row for row in similarity.get("candidates", [])}
    if len(candidate_map) != len(similarity.get("candidates", [])):
        raise ValueError("OA4_DUPLICATE_SIMILARITY_CANDIDATE")

    seen: set[str] = set()
    reviewed = []
    fingerprint = similarity_fingerprint(similarity)
    for raw in decisions:
        candidate_id = str(raw.get("candidate_object_id", "")).strip()
        decision = str(raw.get("decision", "")).strip().upper()
        if candidate_id not in candidate_map:
            raise ValueError("OA4_DECISION_CANDIDATE_NOT_IN_SIMILARITY_RUN")
        if candidate_id in seen:
            raise ValueError("OA4_DUPLICATE_CANDIDATE_DECISION")
        seen.add(candidate_id)
        if decision not in ALLOWED_DECISIONS:
            raise ValueError("OA4_DECISION_NOT_ALLOWED")

        target_family = str(raw.get("target_family_id", "")).strip() or similarity.get("family_id")
        if decision == "MOVE_TO_OTHER_FAMILY" and not str(raw.get("target_family_id", "")).strip():
            raise ValueError("OA4_TARGET_FAMILY_REQUIRED")
        if decision in {"MARK_AMBIGUOUS", "DEFER_NEEDS_SOURCE"}:
            target_family = None

        reviewed.append(
            {
                "candidate_object_id": candidate_id,
                "decision": decision,
                "prototype_id": similarity.get("prototype_id"),
                "proposed_family_id": target_family,
                "similarity_run_fingerprint": fingerprint,
                "similarity_score": candidate_map[candidate_id].get("score"),
                "similarity_state": candidate_map[candidate_id].get("state"),
                "similarity_reason_codes": list(candidate_map[candidate_id].get("reason_codes") or []),
                "source_evidence": dict(source_evidence),
                "reviewer": reviewer,
                "revision": revision,
                "family_membership_proposal_created": decision in {"CONFIRM_AS_FAMILY_CANDIDATE", "MOVE_TO_OTHER_FAMILY"},
                "structural_identity_created": False,
                "canonical_write_authorized": False,
            }
        )

    total = len(candidate_map)
    reviewed_count = len(reviewed)
    unresolved = total - reviewed_count
    ambiguous_count = sum(row["decision"] in {"MARK_AMBIGUOUS", "DEFER_NEEDS_SOURCE"} for row in reviewed)
    if reviewed_count == 0:
        state = "REVIEW_OPEN"
    elif unresolved > 0:
        state = "REVIEW_PARTIAL"
    elif ambiguous_count:
        state = "REVIEW_COMPLETE_WITH_AMBIGUITIES"
    else:
        state = "REVIEW_COMPLETE"

    return {
        "state": state,
        "output_state": "HUMAN_REVIEWED_FAMILY_CANDIDATES",
        "prototype_id": similarity.get("prototype_id"),
        "source_evidence": dict(source_evidence),
        "similarity_run_fingerprint": fingerprint,
        "candidate_count": total,
        "reviewed_count": reviewed_count,
        "unresolved_count": unresolved,
        "ambiguous_count": ambiguous_count,
        "candidate_decisions": reviewed,
        "family_membership_proposals_created": sum(row["family_membership_proposal_created"] for row in reviewed),
        "clean_completion": state == "REVIEW_COMPLETE",
        "structural_identity_created": False,
        "canonical_write_authorized": False,
        "project_material_promotion_authorized": False,
        "engineering_authority_effect": "NONE",
        "next_gate": "OA-5_STRUCTURAL_RESOLVER",
    }
