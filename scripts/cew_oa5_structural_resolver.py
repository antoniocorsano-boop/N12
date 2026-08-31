#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from typing import Any

ALLOWED_RELATIONSHIPS = {
    "SAME_LEVEL_ALIGNMENT",
    "VERTICAL_CONTINUITY",
    "FRAME_MEMBERSHIP",
    "NODE_CONNECTIVITY",
    "SECTION_CONTINUITY",
    "EXPLICIT_DRAWING_CALLOUT",
    "CROSS_DRAWING_REGISTRATION",
}


def _candidate_id(object_id: str, family_id: str, revision: str, relationships: list[dict[str, Any]]) -> str:
    seed = json.dumps(
        {
            "object_id": object_id,
            "family_id": family_id,
            "revision": revision,
            "relationships": relationships,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "SIC-" + hashlib.sha256(seed).hexdigest()[:20].upper()


def resolve_identity_candidate(
    family_decision: dict[str, Any],
    relationships: list[dict[str, Any]],
    revision: str,
) -> dict[str, Any]:
    decision = str(family_decision.get("decision", "")).upper()
    if decision not in {"CONFIRM_AS_FAMILY_CANDIDATE", "MOVE_TO_OTHER_FAMILY"}:
        raise ValueError("OA5_HUMAN_CONFIRMED_FAMILY_CANDIDATE_REQUIRED")
    if family_decision.get("family_membership_proposal_created") is not True:
        raise ValueError("OA5_FAMILY_MEMBERSHIP_PROPOSAL_REQUIRED")
    if not revision.strip():
        raise ValueError("OA5_REVISION_REQUIRED")

    object_id = str(family_decision.get("candidate_object_id", "")).strip()
    family_id = str(family_decision.get("proposed_family_id", "")).strip()
    source_evidence = dict(family_decision.get("source_evidence") or {})
    required_evidence = {"source_version_id", "page_id", "evidence_region_id", "source_sha256"}
    if not object_id or not family_id:
        raise ValueError("OA5_OBJECT_AND_FAMILY_REQUIRED")
    if not required_evidence.issubset(source_evidence) or any(not source_evidence[k] for k in required_evidence):
        raise ValueError("OA5_SOURCE_EVIDENCE_INCOMPLETE")

    normalized = []
    seen = set()
    conflict = False
    for raw in relationships:
        rel_type = str(raw.get("relationship_type", "")).upper()
        target = str(raw.get("target_id", "")).strip()
        evidence_ref = str(raw.get("evidence_ref", "")).strip()
        relation_revision = str(raw.get("revision", "")).strip()
        if rel_type not in ALLOWED_RELATIONSHIPS:
            raise ValueError("OA5_RELATIONSHIP_TYPE_NOT_ALLOWED")
        if not target or not evidence_ref:
            raise ValueError("OA5_RELATIONSHIP_TARGET_AND_EVIDENCE_REQUIRED")
        if relation_revision != revision:
            raise ValueError("OA5_RELATIONSHIP_REVISION_MISMATCH")
        key = (rel_type, target, evidence_ref)
        if key in seen:
            continue
        seen.add(key)
        support = str(raw.get("support", "SUPPORTS")).upper()
        if support not in {"SUPPORTS", "CONFLICTS"}:
            raise ValueError("OA5_RELATIONSHIP_SUPPORT_STATE_INVALID")
        conflict = conflict or support == "CONFLICTS"
        normalized.append(
            {
                "relationship_type": rel_type,
                "target_id": target,
                "evidence_ref": evidence_ref,
                "revision": relation_revision,
                "support": support,
            }
        )

    supporting = [row for row in normalized if row["support"] == "SUPPORTS"]
    if conflict:
        state = "IDENTITY_CONFLICT"
    elif supporting:
        state = "READY_FOR_EXPLICIT_IDENTITY_REVIEW"
    else:
        state = "INSUFFICIENT_RELATIONSHIP_EVIDENCE"

    return {
        "state": "STRUCTURAL_IDENTITY_CANDIDATE",
        "candidate_state": state,
        "identity_candidate_id": _candidate_id(object_id, family_id, revision, normalized),
        "source_object_id": object_id,
        "family_id": family_id,
        "source_evidence": source_evidence,
        "relationship_evidence": normalized,
        "supporting_relationship_count": len(supporting),
        "relationship_conflict": conflict,
        "proximity_used_as_identity_evidence": False,
        "similarity_used_as_identity_authority": False,
        "family_membership_used_as_identity_authority": False,
        "accepted_structural_identity": False,
        "explicit_identity_review_required": True,
        "canonical_write_authorized": False,
        "project_material_ready": False,
        "engineering_authority_effect": "NONE",
        "revision": revision,
        "next_gate": "OA-G5_EXPLICIT_STRUCTURAL_IDENTITY_REVIEW",
    }
