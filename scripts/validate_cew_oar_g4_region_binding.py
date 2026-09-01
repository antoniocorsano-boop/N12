#!/usr/bin/env python3
"""Deterministic validation for governed G4/TAV-05S region localization."""
from __future__ import annotations

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
    assert proposal["oar_human_confirmation"] is False
    assert proposal["canonical_write_authorized"] is False

    proposed = aggregate([proposal], contract)
    row = next(item for item in proposed["objects"] if item["support_id"] == "1")
    assert row["state"] == "PROPOSED"
    assert row["bbox"] == bbox
    assert proposed["summary"]["PROPOSED"] == 1
    assert proposed["summary"]["UNBOUND"] == 33

    confirmation = build_receipt(
        decision_id="oar-g4-1-confirm",
        support_id="1",
        bbox=bbox,
        action=CONFIRM_ACTION,
        timestamp="2026-09-01T08:01:00+00:00",
        contract=contract,
    )
    assert confirmation["authority"] == "HUMAN_EVIDENCE_LOCALIZATION_ONLY"
    assert confirmation["oar_human_confirmation"] is False
    confirmed = aggregate([proposal, confirmation], contract)
    row = next(item for item in confirmed["objects"] if item["support_id"] == "1")
    assert row["state"] == "GEOMETRY_CONFIRMED"
    assert row["geometry_confirmation_receipt_id"] == "oar-g4-1-confirm"
    assert confirmed["summary"]["GEOMETRY_CONFIRMED"] == 1
    assert confirmed["summary"]["oar_human_confirmed"] == 0
    assert confirmed["summary"]["canonical_evidence_regions_materialized"] == 0

    _must_fail(lambda: normalize_bbox({"x": -0.1, "y": 0, "w": 0.1, "h": 0.1}), "OUT_OF_RANGE")
    _must_fail(lambda: normalize_bbox({"x": 0.95, "y": 0, "w": 0.1, "h": 0.1}), "EXCEEDS_PAGE")
    _must_fail(lambda: normalize_bbox({"x": 0, "y": 0, "w": 0, "h": 0.1}), "EMPTY")
    _must_fail(
        lambda: build_receipt(
            decision_id="bad-support",
            support_id="999",
            bbox=bbox,
            action=PROPOSAL_ACTION,
            contract=contract,
        ),
        "SUPPORT_NOT_IN_PILOT",
    )
    _must_fail(lambda: aggregate([confirmation], contract), "CONFIRMATION_WITHOUT_PROPOSAL")

    changed = build_receipt(
        decision_id="oar-g4-1-confirm-changed",
        support_id="1",
        bbox={"x": 0.11, "y": 0.20, "w": 0.015, "h": 0.020},
        action=CONFIRM_ACTION,
        contract=contract,
    )
    _must_fail(lambda: aggregate([proposal, changed], contract), "CONFIRMATION_BBOX_MISMATCH")
    _must_fail(lambda: aggregate([proposal, proposal], contract), "DUPLICATE_DECISION_ID")

    print("CEW_OAR_G4_REGION_BINDING_PASS")
    print("objects=34 unbound=34 initial_canonical_regions=0 oar_human_confirmed=0")
    print("geometry_confirmation_authority=HUMAN_EVIDENCE_LOCALIZATION_ONLY canonical_write_authorized=false")


if __name__ == "__main__":
    main()
