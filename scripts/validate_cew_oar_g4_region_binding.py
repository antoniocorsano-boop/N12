#!/usr/bin/env python3
"""Deterministic validation for governed G4/TAV-05S region localization."""
from __future__ import annotations

from copy import deepcopy

from cew_oar_g4_region_binding import (
    CONFIRM_ACTION,
    PROPOSAL_ACTION,
    aggregate,
    build_receipt,
    load_contract,
    normalize_bbox,
)


def _must_fail(callable_, marker: str) -> None:
    try:
        callable_()
    except ValueError as exc:
        assert marker in str(exc), (marker, str(exc))
    else:
        raise AssertionError(f"expected failure: {marker}")


def main() -> None:
    contract = load_contract()
    assert len(contract["objects"]) == 34
    assert contract["document"]["coordinate_system"] == "NORMALIZED_0_1"
    assert contract["workflow"]["interaction_surface"] == "FULL_VERIFIED_PAGE"
    assert contract["workflow"]["crop_role"] == "OPTIONAL_DERIVED_AUDIT_AID_ONLY"
    assert contract["workflow"]["canonical_write_authorized"] is False
    assert contract["workflow"]["oar_classification_authority"] == "SEPARATE_REVIEW_REQUIRED"

    empty = aggregate([], contract)
    assert empty["summary"] == {
        "total": 34,
        "UNBOUND": 34,
        "PROPOSED": 0,
        "GEOMETRY_CONFIRMED": 0,
        "stale_concurrent_transitions": 0,
        "oar_human_confirmed": 0,
        "canonical_evidence_regions_materialized": 0,
    }
    assert empty["next_gate"] == "LOCALIZE_REMAINING_OBJECTS"
    assert empty["canonical_write_authorized"] is False

    bbox = {"x": 0.10, "y": 0.20, "w": 0.015, "h": 0.020}
    proposal = build_receipt(
        decision_id="oar-g4-1-proposal",
        support_id="1",
        bbox=bbox,
        action=PROPOSAL_ACTION,
        timestamp="2026-09-01T08:00:00+00:00",
        contract=contract,
    )
    assert proposal["authority"] == "WORKING_GEOMETRY_ONLY"
    assert proposal["base_proposal_decision_id"] is None

    first_proposal_tampering = {
        "family_id": "COL-G4-TAMPERED",
        "authority": "HUMAN_EVIDENCE_LOCALIZATION_ONLY",
        "oar_human_confirmation": True,
        "structural_identity_authorized": True,
        "canonical_write_authorized": True,
        "engineering_authority_effect": "ENGINEERING_STATE_MUTATION",
    }
    for field, value in first_proposal_tampering.items():
        tampered = deepcopy(proposal)
        tampered["decision_id"] = f"tampered-proposal-{field}"
        tampered[field] = value
        _must_fail(lambda tampered=tampered: aggregate([tampered], contract), f"GOVERNED_FIELD_MISMATCH_{field.upper()}")

    proposed = aggregate([proposal], contract)
    row = next(item for item in proposed["objects"] if item["support_id"] == "1")
    assert row["state"] == "PROPOSED"
    assert row["bbox"] == bbox
    assert row["geometry_proposal_receipt_id"] == proposal["decision_id"]

    confirmation = build_receipt(
        decision_id="oar-g4-1-confirm",
        support_id="1",
        bbox=bbox,
        action=CONFIRM_ACTION,
        base_proposal_decision_id=proposal["decision_id"],
        timestamp="2026-09-01T08:01:00+00:00",
        contract=contract,
    )
    assert confirmation["authority"] == "HUMAN_EVIDENCE_LOCALIZATION_ONLY"

    first_confirmation_tampering = {
        "family_id": "COL-G4-TAMPERED",
        "authority": "WORKING_GEOMETRY_ONLY",
        "oar_human_confirmation": True,
        "structural_identity_authorized": True,
        "canonical_write_authorized": True,
        "engineering_authority_effect": "ENGINEERING_STATE_MUTATION",
    }
    for field, value in first_confirmation_tampering.items():
        tampered = deepcopy(confirmation)
        tampered["decision_id"] = f"tampered-confirm-{field}"
        tampered[field] = value
        _must_fail(lambda tampered=tampered: aggregate([proposal, tampered], contract), f"GOVERNED_FIELD_MISMATCH_{field.upper()}")

    confirmed = aggregate([proposal, confirmation], contract)
    row = next(item for item in confirmed["objects"] if item["support_id"] == "1")
    assert row["state"] == "GEOMETRY_CONFIRMED"
    assert row["geometry_confirmation_receipt_id"] == "oar-g4-1-confirm"
    assert confirmed["summary"]["GEOMETRY_CONFIRMED"] == 1
    assert confirmed["summary"]["stale_concurrent_transitions"] == 0

    _must_fail(lambda: normalize_bbox({"x": -0.1, "y": 0, "w": 0.1, "h": 0.1}), "OUT_OF_RANGE")
    _must_fail(lambda: normalize_bbox({"x": 0.95, "y": 0, "w": 0.1, "h": 0.1}), "EXCEEDS_PAGE")
    _must_fail(lambda: normalize_bbox({"x": 0, "y": 0, "w": 0, "h": 0.1}), "EMPTY")
    _must_fail(
        lambda: build_receipt(decision_id="bad-support", support_id="999", bbox=bbox, action=PROPOSAL_ACTION, contract=contract),
        "SUPPORT_NOT_IN_PILOT",
    )
    _must_fail(lambda: aggregate([confirmation], contract), "CONFIRMATION_WITHOUT_PROPOSAL")

    changed = build_receipt(
        decision_id="oar-g4-1-confirm-changed",
        support_id="1",
        bbox={"x": 0.11, "y": 0.20, "w": 0.015, "h": 0.020},
        action=CONFIRM_ACTION,
        base_proposal_decision_id=proposal["decision_id"],
        timestamp="2026-09-01T08:01:01+00:00",
        contract=contract,
    )
    _must_fail(lambda: aggregate([proposal, changed], contract), "CONFIRMATION_BBOX_MISMATCH")
    _must_fail(lambda: aggregate([proposal, proposal], contract), "DUPLICATE_DECISION_ID")

    # Normal post-confirmation mutation remains fail-closed when it is not a
    # concurrent transition anchored to the same predecessor.
    reproposal = build_receipt(
        decision_id="oar-g4-1-reproposal",
        support_id="1",
        bbox={"x": 0.12, "y": 0.20, "w": 0.015, "h": 0.020},
        action=PROPOSAL_ACTION,
        timestamp="2026-09-01T08:02:00+00:00",
        contract=contract,
    )
    _must_fail(lambda: aggregate([proposal, confirmation, reproposal], contract), "GEOMETRY_ALREADY_CONFIRMED")

    # Confirmation/confirmation race remains idempotent when both consume the
    # same proposal revision and confirm the same bbox.
    reconfirm = build_receipt(
        decision_id="oar-g4-1-reconfirm",
        support_id="1",
        bbox=bbox,
        action=CONFIRM_ACTION,
        base_proposal_decision_id=proposal["decision_id"],
        timestamp="2026-09-01T08:01:00.500000+00:00",
        contract=contract,
    )
    replayed = aggregate([proposal, confirmation, reconfirm], contract)
    row = next(item for item in replayed["objects"] if item["support_id"] == "1")
    assert row["state"] == "GEOMETRY_CONFIRMED"
    assert row["geometry_confirmation_receipt_id"] == "oar-g4-1-confirm"

    # Replacement/confirmation race, replacement wins: both workers observed
    # proposal v1. The replacement v2 sorts first, so the confirmation bound to
    # v1 becomes an audit-visible stale transition and cannot corrupt v2.
    bbox2 = {"x": 0.13, "y": 0.20, "w": 0.015, "h": 0.020}
    replacement_first = build_receipt(
        decision_id="oar-g4-1-replacement-race-a",
        support_id="1",
        bbox=bbox2,
        action=PROPOSAL_ACTION,
        base_proposal_decision_id=proposal["decision_id"],
        timestamp="2026-09-01T08:00:30+00:00",
        contract=contract,
    )
    confirm_old_second = build_receipt(
        decision_id="oar-g4-1-confirm-race-b",
        support_id="1",
        bbox=bbox,
        action=CONFIRM_ACTION,
        base_proposal_decision_id=proposal["decision_id"],
        timestamp="2026-09-01T08:00:31+00:00",
        contract=contract,
    )
    replacement_wins = aggregate([proposal, replacement_first, confirm_old_second], contract)
    row = next(item for item in replacement_wins["objects"] if item["support_id"] == "1")
    assert row["state"] == "PROPOSED"
    assert row["bbox"] == bbox2
    assert row["geometry_proposal_receipt_id"] == replacement_first["decision_id"]
    assert replacement_wins["summary"]["stale_concurrent_transitions"] == 1

    # Same race, confirmation wins: confirmation consumes v1 first; the later
    # replacement was also based on v1 and is retained only as stale audit.
    confirm_first = build_receipt(
        decision_id="oar-g4-1-confirm-race-a",
        support_id="1",
        bbox=bbox,
        action=CONFIRM_ACTION,
        base_proposal_decision_id=proposal["decision_id"],
        timestamp="2026-09-01T08:00:30+00:00",
        contract=contract,
    )
    replacement_second = build_receipt(
        decision_id="oar-g4-1-replacement-race-b",
        support_id="1",
        bbox=bbox2,
        action=PROPOSAL_ACTION,
        base_proposal_decision_id=proposal["decision_id"],
        timestamp="2026-09-01T08:00:31+00:00",
        contract=contract,
    )
    confirmation_wins = aggregate([proposal, confirm_first, replacement_second], contract)
    row = next(item for item in confirmation_wins["objects"] if item["support_id"] == "1")
    assert row["state"] == "GEOMETRY_CONFIRMED"
    assert row["bbox"] == bbox
    assert row["geometry_confirmation_receipt_id"] == confirm_first["decision_id"]
    assert confirmation_wins["summary"]["stale_concurrent_transitions"] == 1

    divergent_after_confirmation = build_receipt(
        decision_id="oar-g4-1-reconfirm-divergent",
        support_id="1",
        bbox={"x": 0.105, "y": 0.20, "w": 0.015, "h": 0.020},
        action=CONFIRM_ACTION,
        base_proposal_decision_id=proposal["decision_id"],
        timestamp="2026-09-01T08:01:00.600000+00:00",
        contract=contract,
    )
    _must_fail(lambda: aggregate([proposal, confirmation, divergent_after_confirmation], contract), "GEOMETRY_ALREADY_CONFIRMED")

    print("CEW_OAR_G4_REGION_BINDING_PASS")
    print("objects=34 initial_canonical_regions=0 oar_human_confirmed=0")
    print("replacement_confirmation_race=optimistic_revision_anchor stale_transition=audit_visible_non_mutating")
    print("geometry_confirmation_authority=HUMAN_EVIDENCE_LOCALIZATION_ONLY canonical_write_authorized=false")


if __name__ == "__main__":
    main()
