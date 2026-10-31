from __future__ import annotations

from typing import Any


_ALLOWED_KINDS = {
    "DOCUMENTARY_LABEL_CANDIDATE",
    "SUPPORT_NUMBER_CANDIDATE",
    "CROSS_DOCUMENT_COUNTERPART_CANDIDATE",
}


def evidence_independence_key(evidence: dict[str, Any]) -> tuple[str, ...]:
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be an object")
    root = str(evidence.get("observation_root_id") or "")
    if root:
        return ("OBSERVATION_ROOT", root)
    provenance = str(evidence.get("provenance_ref") or "")
    evidence_id = str(evidence.get("evidence_id") or "")
    if not provenance or not evidence_id:
        raise ValueError("evidence lacks independence provenance")
    return ("PROVENANCE", provenance, evidence_id)


def build_identity_hypothesis(
    *,
    occurrence_id: str,
    hypothesis_kind: str,
    candidate_value: str,
    supporting: list[dict[str, Any]],
    contradicting: list[dict[str, Any]],
) -> dict[str, Any]:
    if hypothesis_kind not in _ALLOWED_KINDS:
        raise ValueError("unapproved hypothesis kind")
    if not str(occurrence_id).startswith("COL-OCC-"):
        raise ValueError("invalid occurrence identity")
    if not str(candidate_value):
        raise ValueError("candidate value must be non-empty")

    support_ids = sorted({str(row.get("evidence_id") or "") for row in supporting if row.get("evidence_id")})
    contradiction_ids = sorted({str(row.get("evidence_id") or "") for row in contradicting if row.get("evidence_id")})
    independent_keys = sorted({evidence_independence_key(row) for row in supporting})
    ambiguous = any(row.get("ambiguous") is True for row in supporting)

    if contradiction_ids:
        state = "CONTRADICTED"
    elif ambiguous:
        state = "AMBIGUOUS"
    elif not support_ids:
        state = "UNSUPPORTED"
    elif len(independent_keys) >= 2:
        state = "MULTI_CHANNEL_SUPPORTED"
    else:
        state = "SINGLE_CHANNEL"

    independent_discriminants = ["|".join(key) for key in independent_keys]
    return {
        "hypothesis_id": f"HYP-{occurrence_id}-{hypothesis_kind}-{candidate_value}",
        "occurrence_id": str(occurrence_id),
        "hypothesis_kind": hypothesis_kind,
        "candidate_value": str(candidate_value),
        "supporting_evidence_ids": support_ids,
        "contradicting_evidence_ids": contradiction_ids,
        "independent_channel_count": len(independent_keys),
        "independent_discriminants": independent_discriminants,
        "state": state,
        "promotion_authorized": False,
        "support_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "notes": [],
    }
