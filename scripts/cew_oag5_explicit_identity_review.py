#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from typing import Any

ALLOWED_DECISIONS = {
    "ACCEPT_STRUCTURAL_IDENTITY",
    "REJECT_STRUCTURAL_IDENTITY",
    "DEFER_NEEDS_RELATIONSHIP_EVIDENCE",
}


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def candidate_fingerprint(candidate: dict[str, Any]) -> str:
    return _fingerprint(
        {
            "identity_candidate_id": candidate.get("identity_candidate_id"),
            "candidate_state": candidate.get("candidate_state"),
            "source_object_id": candidate.get("source_object_id"),
            "family_id": candidate.get("family_id"),
            "source_evidence": candidate.get("source_evidence"),
            "relationship_evidence": candidate.get("relationship_evidence"),
            "revision": candidate.get("revision"),
        }
    )


def relationship_evidence_fingerprint(candidate: dict[str, Any]) -> str:
    return _fingerprint(candidate.get("relationship_evidence") or [])


def review_identity(candidate: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("state") != "STRUCTURAL_IDENTITY_CANDIDATE":
        raise ValueError("OAG5_STRUCTURAL_IDENTITY_CANDIDATE_REQUIRED")
    if candidate.get("candidate_state") != "READY_FOR_EXPLICIT_IDENTITY_REVIEW":
        raise ValueError("OAG5_CANDIDATE_NOT_REVIEW_READY")
    if candidate.get("accepted_structural_identity") is not False:
        raise ValueError("OAG5_CANDIDATE_PREACCEPTED_INVALID")

    decision = str(receipt.get("decision", "")).upper()
    if decision not in ALLOWED_DECISIONS:
        raise ValueError("OAG5_DECISION_NOT_ALLOWED")
    if receipt.get("identity_candidate_id") != candidate.get("identity_candidate_id"):
        raise ValueError("OAG5_CANDIDATE_ID_MISMATCH")
    if receipt.get("candidate_fingerprint") != candidate_fingerprint(candidate):
        raise ValueError("OAG5_CANDIDATE_FINGERPRINT_MISMATCH")
    if receipt.get("relationship_evidence_fingerprint") != relationship_evidence_fingerprint(candidate):
        raise ValueError("OAG5_RELATIONSHIP_EVIDENCE_MISMATCH")
    if receipt.get("revision") != candidate.get("revision"):
        raise ValueError("OAG5_REVISION_MISMATCH")
    if receipt.get("source_evidence") != candidate.get("source_evidence"):
        raise ValueError("OAG5_SOURCE_EVIDENCE_MISMATCH")
    reviewer = str(receipt.get("reviewer", "")).strip()
    attestation = str(receipt.get("attestation", "")).strip()
    if not reviewer:
        raise ValueError("OAG5_REVIEWER_REQUIRED")
    if not attestation:
        raise ValueError("OAG5_ATTESTATION_REQUIRED")

    accepted = decision == "ACCEPT_STRUCTURAL_IDENTITY"
    state = (
        "HUMAN_ACCEPTED_STRUCTURAL_IDENTITY"
        if accepted
        else "HUMAN_REJECTED_STRUCTURAL_IDENTITY"
        if decision == "REJECT_STRUCTURAL_IDENTITY"
        else "HUMAN_DEFERRED_STRUCTURAL_IDENTITY"
    )
    return {
        "state": state,
        "identity_candidate_id": candidate.get("identity_candidate_id"),
        "decision": decision,
        "reviewer": reviewer,
        "attestation": attestation,
        "candidate_fingerprint": receipt.get("candidate_fingerprint"),
        "relationship_evidence_fingerprint": receipt.get("relationship_evidence_fingerprint"),
        "source_evidence": dict(candidate.get("source_evidence") or {}),
        "relationship_evidence": list(candidate.get("relationship_evidence") or []),
        "revision": candidate.get("revision"),
        "structural_identity_accepted": accepted,
        "canonical_write_authorized": False,
        "project_material_ready": False,
        "engineering_authority_effect": "HUMAN_STRUCTURAL_IDENTITY_DECISION_ONLY",
        "next_gate": "OA-6_PROJECT_MATERIAL_GATE" if accepted else "OA-G5_REVIEW_REMAINS_OPEN",
    }
