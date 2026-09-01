#!/usr/bin/env python3
"""Deterministic validation of the real G4 / TAV-05S OAR pilot projection."""
from collections import Counter

from cew_object_acquisition import CandidateState, evaluate_cad_promotion
from cew_oar_g4_column_pilot import load_g4_column_candidates, build_g4_column_pilot_workbench

EXPECTED_FAMILIES = {
    "COL-G4-40X40": 21,
    "COL-G4-45X30": 5,
    "COL-G4-30X45": 5,
    "COL-G4-30X110": 2,
    "COL-G4-110X30": 1,
}


def main() -> None:
    candidates = load_g4_column_candidates()
    assert len(candidates) == 34
    assert len({item.evidence_object_id for item in candidates}) == 34
    assert all(item.object_type.value == "COLUMN" for item in candidates)
    assert all(item.state == CandidateState.CANDIDATE for item in candidates)
    assert all(item.review is None for item in candidates)

    counts = Counter(item.family_id for item in candidates)
    assert dict(counts) == EXPECTED_FAMILIES

    # DIRECT_REGISTERED is retained only in context as source-registration
    # evidence. It must not become OAR human confirmation.
    assert all(
        item.signature.context["source_validation_state"] == "DIRECT_REGISTERED"
        for item in candidates
    )
    assert not any(item.state == CandidateState.HUMAN_CONFIRMED for item in candidates)

    # The historical register does not contain canonical CEW region bindings.
    assert all(not item.provenance.complete() for item in candidates)
    assert all(not item.provenance.evidence_region_id for item in candidates)

    # Even if runtime write authority were hypothetically true, these real
    # pilot candidates cannot promote because provenance + human review are absent.
    for item in candidates:
        result = evaluate_cad_promotion(
            item,
            runtime_canonical_write_authorized=True,
            cad_object_id=f"CAD-{item.evidence_object_id}",
        )
        assert not result.eligible
        assert not result.canonical_write_authorized
        assert "INCOMPLETE_PROVENANCE" in result.reasons
        assert "HUMAN_CONFIRMATION_REQUIRED" in result.reasons

    view = build_g4_column_pilot_workbench()
    assert view["summary"]["total"] == 34
    assert view["summary"]["families"] == 5
    assert view["summary"]["states"] == {"proposal": 34}
    assert view["summary"]["provenance_blocking_count"] == 34
    assert view["summary"]["review_blocking_count"] == 0
    assert view["summary"]["promotion_ready_count"] == 0
    assert all(obj["reviewable"] for obj in view["objects"])
    assert not any(obj["promotion_ready"] for obj in view["objects"])
    assert view["pilot"]["oar_human_confirmation"] == "NOT_ASSERTED"
    assert view["canonical_write_authorized"] is False

    print("CEW_OAR_G4_COLUMN_PILOT_PASS")
    print("objects=34 families=5 proposals=34 provenance_blockers=34")
    print("human_confirmed=0 promotion_ready=0 canonical_write_authorized=false")


if __name__ == "__main__":
    main()
