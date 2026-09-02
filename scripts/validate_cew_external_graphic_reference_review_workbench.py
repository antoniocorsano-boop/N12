#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import cew_external_graphic_reference_review_workbench as review


def _expect_value_error(fn, marker: str) -> None:
    try:
        fn()
    except ValueError as exc:
        assert str(exc) == marker, (str(exc), marker)
    else:
        raise AssertionError(f"expected ValueError {marker}")


def main() -> None:
    acquisition, queue = review._governed()
    items = queue["review_items"]
    assert len(items) == 5
    assert acquisition["library_promotion_authorized"] is False
    assert queue["automatic_library_pack_build_authorized"] is False
    assert all(item["meaning"] is None for item in items)
    assert all(item["review_state"] == "UNREVIEWED" for item in items)

    html = review._page()
    for marker in (
        "Reference Review Workspace",
        "Accetta come riferimento",
        "Rifiuta come riferimento",
        "Calcola pack candidate",
        "EXTERNAL_REFERENCE",
    ):
        assert marker in html

    first = items[0]
    accept_payload = {
        "decision_id": "test-reference-accept-001",
        "review_item_id": first["review_item_id"],
        "state": "ACCEPT_REFERENCE_EVIDENCE",
        "reviewer": "CI-HUMAN-REVIEW-SIMULATION",
        "rationale": "Synthetic deterministic test of the human review contract; not a real content review.",
        "meaning": "SYNTHETIC_REFERENCE_MEANING_FOR_GATE_ONLY",
        "scope_description": "Synthetic scope used only to verify that the pack builder consumes explicit human fields.",
        "primitive_families": ["RECTILINEAR_CLOSED_SHAPE"],
    }
    receipt = review.build_review_receipt(accept_payload)
    assert receipt["receipt_type"] == review.RECEIPT_TYPE
    assert receipt["source_id"] == first["source_id"]
    assert receipt["source_sha256"] == first["source_sha256"]
    assert receipt["page_index"] == first["page_index"]
    assert receipt["page_text_sha256"] == first["page_text_sha256"]
    assert receipt["page_feature_sha256"] == first["page_feature_sha256"]
    assert receipt["meaning"] == "SYNTHETIC_REFERENCE_MEANING_FOR_GATE_ONLY"
    assert receipt["automatic_acceptance"] is False
    assert receipt["discovery_query_supplied_meaning"] is False
    assert receipt["authority"]["project_semantic_authority"] == "NONE"
    assert receipt["authority"]["canonical_write_authorized"] is False
    assert receipt["authority"]["structural_identity_authorized"] is False

    bad_accept = dict(accept_payload)
    bad_accept["decision_id"] = "test-reference-invalid-001"
    bad_accept["meaning"] = ""
    _expect_value_error(
        lambda: review.build_review_receipt(bad_accept),
        "REFERENCE_REVIEW_MEANING_REQUIRED",
    )

    bad_family = dict(accept_payload)
    bad_family["decision_id"] = "test-reference-invalid-family-001"
    bad_family["primitive_families"] = ["COLUMN"]
    _expect_value_error(
        lambda: review.build_review_receipt(bad_family),
        "REFERENCE_REVIEW_PRIMITIVE_FAMILY_INVALID",
    )

    _expect_value_error(
        lambda: review.render_review_page("GREF-REV-DOES-NOT-EXIST"),
        "REFERENCE_REVIEW_ITEM_UNKNOWN",
    )

    old_store = review.REVIEW_STORE
    try:
        with tempfile.TemporaryDirectory() as tmp:
            review.REVIEW_STORE = Path(tmp)
            persisted = review.persist_review_receipt(accept_payload)
            assert persisted["decision_state"] == "ACCEPT_REFERENCE_EVIDENCE"
            assert persisted["repository_library_index_written"] is False
            assert persisted["authority"]["project_semantic_authority"] == "NONE"

            _expect_value_error(
                lambda: review.persist_review_receipt({**accept_payload, "decision_id": "test-reference-duplicate-item"}),
                "REFERENCE_REVIEW_ITEM_ALREADY_DECIDED",
            )

            states = [
                "REJECT_REFERENCE_EVIDENCE",
                "DEFER",
                "REJECT_REFERENCE_EVIDENCE",
                "DEFER",
            ]
            for index, (item, state) in enumerate(zip(items[1:], states), start=2):
                payload = {
                    "decision_id": f"test-reference-decision-{index:03d}",
                    "review_item_id": item["review_item_id"],
                    "state": state,
                    "reviewer": "CI-HUMAN-REVIEW-SIMULATION",
                    "rationale": "Synthetic deterministic terminal review decision for gate validation only.",
                }
                result = review.persist_review_receipt(payload)
                assert result["decision_state"] == state
                assert result["repository_library_index_written"] is False

            status = review.review_status()
            assert status["state"] == "HUMAN_REFERENCE_REVIEW_COMPLETE"
            assert status["summary"]["UNREVIEWED"] == 0
            assert status["summary"]["ACCEPT_REFERENCE_EVIDENCE"] == 1
            assert status["summary"]["REJECT_REFERENCE_EVIDENCE"] == 2
            assert status["summary"]["DEFER"] == 2
            assert status["pack_candidate_available"] is True
            assert status["repository_library_index_written"] is False

            decisions = review.decisions_document()
            assert decisions["status"] == "HUMAN_REVIEW_COMPLETE"
            assert len(decisions["decisions"]) == 5
            assert decisions["authority"]["project_semantic_authority"] == "NONE"

            pack = review.build_pack_candidate()
            assert pack["status"] == "LIBRARY_AVAILABLE_UNVERIFIED_FOR_CONTEXT"
            assert pack["entry_count"] == 1
            assert pack["tiers_present"] == ["EXTERNAL_REFERENCE"]
            assert pack["entries"][0]["meaning"] == "SYNTHETIC_REFERENCE_MEANING_FOR_GATE_ONLY"
            assert pack["entries"][0]["tier"] == "EXTERNAL_REFERENCE"
            assert pack["entries"][0]["project_semantic_authority"] == "NONE"
            assert pack["runtime_candidate_only"] is True
            assert pack["repository_library_index_written"] is False
            assert pack["authority"]["canonical_write_authorized"] is False
            assert pack["authority"]["structural_identity_authorized"] is False

            library = json.loads(
                (review.ROOT / "knowledge" / "graphic_reference" / "CEW_GRAPHIC_REFERENCE_LIBRARY_INDEX_v1.json").read_text(encoding="utf-8")
            )
            assert library["status"] == "LIBRARY_NOT_CONFIGURED"
            assert library["entry_count"] == 0
            assert library["generation_id"] is None
    finally:
        review.REVIEW_STORE = old_store

    print("CEW_EXTERNAL_REFERENCE_REVIEW_WORKBENCH_PASS")
    print("review_items=5 human_decision_receipts=append_only duplicate_item_rejected=true")
    print("pack_candidate_requires_complete_review=true synthetic_external_reference_entries=1")
    print("repository_library_index_written=false project_semantic_authority=NONE")


if __name__ == "__main__":
    main()
