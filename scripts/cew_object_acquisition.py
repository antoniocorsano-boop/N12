#!/usr/bin/env python3
"""CEW Object Acquisition & Recognition (OAR) domain foundation.

This module intentionally owns candidate/work-state semantics only. It does not
write canonical engineering data and it does not infer structural identity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


class ObjectType(str, Enum):
    COLUMN = "COLUMN"
    BEAM = "BEAM"
    BEAM_SECTION = "BEAM_SECTION"
    SLAB = "SLAB"
    FOUNDATION_BEAM = "FOUNDATION_BEAM"
    FOUNDATION_NODE = "FOUNDATION_NODE"
    LONGITUDINAL_REINFORCEMENT = "LONGITUDINAL_REINFORCEMENT"
    STIRRUP = "STIRRUP"
    GRID_AXIS = "GRID_AXIS"
    DIMENSION = "DIMENSION"
    CALLOUT = "CALLOUT"
    STRUCTURAL_NODE = "STRUCTURAL_NODE"
    TECHNICAL_TEXT = "TECHNICAL_TEXT"


class CandidateState(str, Enum):
    DETECTED = "DETECTED"
    CANDIDATE = "CANDIDATE"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCKED = "BLOCKED"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"
    REJECTED = "REJECTED"


class ReviewDecision(str, Enum):
    CONFIRM = "CONFIRM"
    REJECT = "REJECT"
    AMBIGUOUS = "AMBIGUOUS"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class EvidenceProvenance:
    source_version_id: str
    page_id: str
    evidence_region_id: str
    evidence_fingerprint: str
    registration_id: str | None = None

    def complete(self) -> bool:
        return all(
            value.strip()
            for value in (
                self.source_version_id,
                self.page_id,
                self.evidence_region_id,
                self.evidence_fingerprint,
            )
        )


@dataclass(frozen=True)
class ObjectSignature:
    cad_topology: Mapping[str, Any] = field(default_factory=dict)
    shape: Mapping[str, Any] = field(default_factory=dict)
    dimensions: Mapping[str, Any] = field(default_factory=dict)
    orientation: str | None = None
    associated_text: Sequence[str] = field(default_factory=tuple)
    spatial_relations: Sequence[str] = field(default_factory=tuple)
    context: Mapping[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = {
            "cad_topology": self.cad_topology,
            "shape": self.shape,
            "dimensions": self.dimensions,
            "orientation": self.orientation,
            "associated_text": list(self.associated_text),
            "spatial_relations": list(self.spatial_relations),
            "context": self.context,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ObjectPrototype:
    prototype_id: str
    object_type: ObjectType
    family_id: str
    signature: ObjectSignature
    provenance: EvidenceProvenance
    human_validated: bool


@dataclass(frozen=True)
class ObjectFamily:
    family_id: str
    object_type: ObjectType
    prototype_ids: tuple[str, ...]
    project_local: bool = True


@dataclass(frozen=True)
class HumanReview:
    decision_id: str
    decision: ReviewDecision
    reviewer_assertion: str
    candidate_fingerprint: str
    evidence_fingerprint: str


@dataclass(frozen=True)
class ObjectCandidate:
    evidence_object_id: str
    object_type: ObjectType
    signature: ObjectSignature
    provenance: EvidenceProvenance
    state: CandidateState
    family_id: str | None = None
    review: HumanReview | None = None

    def fingerprint(self) -> str:
        payload = {
            "evidence_object_id": self.evidence_object_id,
            "object_type": self.object_type.value,
            "family_id": self.family_id,
            "signature": self.signature.fingerprint(),
            "source_version_id": self.provenance.source_version_id,
            "page_id": self.provenance.page_id,
            "evidence_region_id": self.provenance.evidence_region_id,
            "evidence_fingerprint": self.provenance.evidence_fingerprint,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CanonicalCadObjectProposal:
    cad_object_id: str
    evidence_object_id: str
    object_type: ObjectType
    family_id: str | None
    candidate_fingerprint: str
    evidence_fingerprint: str
    structural_entity_id: None = None


@dataclass(frozen=True)
class PromotionResult:
    eligible: bool
    canonical_write_authorized: bool
    reasons: tuple[str, ...]
    proposal: CanonicalCadObjectProposal | None = None


def apply_human_review(candidate: ObjectCandidate, review: HumanReview) -> ObjectCandidate:
    reasons: list[str] = []
    if review.candidate_fingerprint != candidate.fingerprint():
        reasons.append("CANDIDATE_FINGERPRINT_MISMATCH")
    if review.evidence_fingerprint != candidate.provenance.evidence_fingerprint:
        reasons.append("EVIDENCE_FINGERPRINT_MISMATCH")
    if not review.decision_id.strip() or not review.reviewer_assertion.strip():
        reasons.append("INCOMPLETE_HUMAN_REVIEW")
    if reasons:
        raise ValueError(";".join(reasons))

    next_state = {
        ReviewDecision.CONFIRM: CandidateState.HUMAN_CONFIRMED,
        ReviewDecision.REJECT: CandidateState.REJECTED,
        ReviewDecision.AMBIGUOUS: CandidateState.AMBIGUOUS,
        ReviewDecision.BLOCK: CandidateState.BLOCKED,
    }[review.decision]
    return ObjectCandidate(
        evidence_object_id=candidate.evidence_object_id,
        object_type=candidate.object_type,
        signature=candidate.signature,
        provenance=candidate.provenance,
        state=next_state,
        family_id=candidate.family_id,
        review=review,
    )


def evaluate_cad_promotion(
    candidate: ObjectCandidate,
    *,
    runtime_canonical_write_authorized: bool,
    cad_object_id: str,
) -> PromotionResult:
    """Fail-closed eligibility check.

    Eligibility to materialize a CAD proposal and authority to write canonical
    engineering state are deliberately separate outcomes.
    """
    reasons: list[str] = []
    if not candidate.provenance.complete():
        reasons.append("INCOMPLETE_PROVENANCE")
    if candidate.state != CandidateState.HUMAN_CONFIRMED:
        reasons.append("HUMAN_CONFIRMATION_REQUIRED")
    if candidate.review is None or candidate.review.decision != ReviewDecision.CONFIRM:
        reasons.append("CONFIRMING_REVIEW_REQUIRED")
    elif candidate.review.candidate_fingerprint != candidate.fingerprint():
        reasons.append("STALE_REVIEW_CANDIDATE_FINGERPRINT")
    elif candidate.review.evidence_fingerprint != candidate.provenance.evidence_fingerprint:
        reasons.append("STALE_REVIEW_EVIDENCE_FINGERPRINT")

    eligible = not reasons
    proposal = None
    if eligible:
        proposal = CanonicalCadObjectProposal(
            cad_object_id=cad_object_id,
            evidence_object_id=candidate.evidence_object_id,
            object_type=candidate.object_type,
            family_id=candidate.family_id,
            candidate_fingerprint=candidate.fingerprint(),
            evidence_fingerprint=candidate.provenance.evidence_fingerprint,
        )

    canonical_write_authorized = eligible and runtime_canonical_write_authorized
    if eligible and not runtime_canonical_write_authorized:
        reasons.append("CANONICAL_WRITE_AUTHORITY_NOT_GRANTED")

    return PromotionResult(
        eligible=eligible,
        canonical_write_authorized=canonical_write_authorized,
        reasons=tuple(reasons),
        proposal=proposal,
    )


def deterministic_similarity(a: ObjectSignature, b: ObjectSignature) -> dict[str, Any]:
    """Explainable first-pass similarity; intentionally no opaque aggregate authority."""
    reasons: list[str] = []
    matched = 0
    considered = 0

    pairs = (
        ("CAD_TOPOLOGY", a.cad_topology, b.cad_topology),
        ("SHAPE", a.shape, b.shape),
        ("DIMENSIONS", a.dimensions, b.dimensions),
        ("ORIENTATION", a.orientation, b.orientation),
        ("ASSOCIATED_TEXT", tuple(a.associated_text), tuple(b.associated_text)),
        ("SPATIAL_RELATIONS", tuple(a.spatial_relations), tuple(b.spatial_relations)),
        ("CONTEXT", a.context, b.context),
    )
    for label, left, right in pairs:
        if left in ({}, (), None, "") and right in ({}, (), None, ""):
            continue
        considered += 1
        if left == right:
            matched += 1
            reasons.append(label)

    ratio = matched / considered if considered else 0.0
    return {
        "matched_signals": matched,
        "considered_signals": considered,
        "match_ratio": ratio,
        "matching_reasons": reasons,
        "authority": "CANDIDATE_SIMILARITY_ONLY",
    }
