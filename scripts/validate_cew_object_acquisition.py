#!/usr/bin/env python3
"""Deterministic validator for CEW OAR OA-0 foundation."""
from dataclasses import replace

from cew_object_acquisition import (
    CandidateState,
    EvidenceProvenance,
    HumanReview,
    ObjectCandidate,
    ObjectSignature,
    ObjectType,
    ReviewDecision,
    apply_human_review,
    deterministic_similarity,
    evaluate_cad_promotion,
)


def candidate(state=CandidateState.CANDIDATE):
    return ObjectCandidate(
        evidence_object_id="EOBJ-G4-P25",
        object_type=ObjectType.COLUMN,
        family_id="COL-40X40",
        signature=ObjectSignature(
            shape={"kind": "RECT", "ratio": 1.0},
            dimensions={"b_cm": 40, "h_cm": 40},
            orientation="ORTHOGONAL",
            context={"storey": "G4", "drawing": "TAV-05S"},
        ),
        provenance=EvidenceProvenance(
            source_version_id="SV-TAV05S",
            page_id="PAGE-1",
            evidence_region_id="ER-G4-P25",
            evidence_fingerprint="evidence-fp-001",
            registration_id="REG-TAV05S-NATIVE",
        ),
        state=state,
    )


def main():
    base = candidate()

    # 1. Candidate without human confirmation must fail closed.
    denied = evaluate_cad_promotion(
        base,
        runtime_canonical_write_authorized=False,
        cad_object_id="CAD-G4-P25",
    )
    assert not denied.eligible
    assert "HUMAN_CONFIRMATION_REQUIRED" in denied.reasons

    # 2. Human review must be bound to exact candidate + evidence fingerprints.
    bad_review = HumanReview(
        decision_id="DEC-BAD",
        decision=ReviewDecision.CONFIRM,
        reviewer_assertion="confirmed",
        candidate_fingerprint="stale",
        evidence_fingerprint=base.provenance.evidence_fingerprint,
    )
    try:
        apply_human_review(base, bad_review)
        raise AssertionError("stale review unexpectedly accepted")
    except ValueError as exc:
        assert "CANDIDATE_FINGERPRINT_MISMATCH" in str(exc)

    good_review = HumanReview(
        decision_id="DEC-001",
        decision=ReviewDecision.CONFIRM,
        reviewer_assertion="reviewed exact candidate",
        candidate_fingerprint=base.fingerprint(),
        evidence_fingerprint=base.provenance.evidence_fingerprint,
    )
    confirmed = apply_human_review(base, good_review)
    assert confirmed.state == CandidateState.HUMAN_CONFIRMED

    # 3. A valid review may make a CAD proposal eligible but current runtime
    # authority still forbids canonical engineering writes.
    guarded = evaluate_cad_promotion(
        confirmed,
        runtime_canonical_write_authorized=False,
        cad_object_id="CAD-G4-P25",
    )
    assert guarded.eligible
    assert guarded.proposal is not None
    assert guarded.proposal.structural_entity_id is None
    assert not guarded.canonical_write_authorized
    assert "CANONICAL_WRITE_AUTHORITY_NOT_GRANTED" in guarded.reasons

    # 4. Family assignment is part of classification identity. Reconstructing
    # a previously reviewed candidate in another family must stale the review.
    moved_family = replace(confirmed, family_id="COL-45X30")
    assert moved_family.fingerprint() != confirmed.fingerprint()
    stale_family_review = evaluate_cad_promotion(
        moved_family,
        runtime_canonical_write_authorized=True,
        cad_object_id="CAD-G4-P25-MOVED",
    )
    assert not stale_family_review.eligible
    assert not stale_family_review.canonical_write_authorized
    assert stale_family_review.proposal is None
    assert "STALE_REVIEW_CANDIDATE_FINGERPRINT" in stale_family_review.reasons

    # 5. Ambiguous/blocked/rejected states cannot promote.
    for state in (CandidateState.AMBIGUOUS, CandidateState.BLOCKED, CandidateState.REJECTED):
        result = evaluate_cad_promotion(
            candidate(state),
            runtime_canonical_write_authorized=True,
            cad_object_id=f"CAD-{state.value}",
        )
        assert not result.eligible, state
        assert not result.canonical_write_authorized, state

    # 6. Explainable deterministic similarity reports reasons, not authority.
    sig = base.signature
    sim = deterministic_similarity(sig, sig)
    assert sim["match_ratio"] == 1.0
    assert sim["authority"] == "CANDIDATE_SIMILARITY_ONLY"
    assert "DIMENSIONS" in sim["matching_reasons"]

    print("CEW_OBJECT_ACQUISITION_OA0_PASS")
    print("family_assignment_bound_to_candidate_fingerprint=true")
    print("canonical_write_authorized=false")
    print("structural_identity_authorized=false")


if __name__ == "__main__":
    main()
