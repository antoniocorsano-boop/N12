#!/usr/bin/env python3
"""Deterministic gate for the human-reviewed EXTERNAL_REFERENCE pack builder."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import cew_external_graphic_reference_pack as packer
import cew_new_project_preacquisition as pre

ROOT = Path(__file__).resolve().parents[1]
ACQUISITION = ROOT / "knowledge/graphic_reference/CEW_EXTERNAL_REFERENCE_ACQUISITION_RECEIPT_v1.json"
QUEUE = ROOT / "knowledge/graphic_reference/CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1.json"
TEMPLATE = ROOT / "knowledge/graphic_reference/CEW_EXTERNAL_REFERENCE_REVIEW_DECISIONS_TEMPLATE_v1.json"


def main() -> None:
    acquisition = json.loads(ACQUISITION.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    assert acquisition["schema"] == packer.ACQUISITION_SCHEMA
    assert acquisition["status"] == "PARTIAL_VERIFIED_2_OF_4"
    assert acquisition["library_promotion_authorized"] is False
    assert len(acquisition["acquired_sources"]) == 2
    assert queue["schema"] == packer.QUEUE_SCHEMA
    assert queue["status"] == "BLOCKED_HUMAN_REFERENCE_REVIEW"
    assert queue["automatic_library_pack_build_authorized"] is False
    assert all(item["meaning"] is None for item in queue["review_items"])
    assert template["schema"] == packer.DECISIONS_SCHEMA
    assert template["decisions"] == []
    assert template["decision_contract"]["discovery_query_may_supply_meaning"] is False
    assert template["decision_contract"]["automatic_acceptance_forbidden"] is True

    empty = packer.build_pack(acquisition, queue, template)
    assert empty["schema"] == packer.LIBRARY_SCHEMA
    assert empty["status"] == "LIBRARY_EMPTY"
    assert empty["entry_count"] == 0
    assert empty["entries"] == []
    assert empty["build_state"] == "NO_ACCEPTED_REFERENCE_EVIDENCE"
    assert empty["project_semantic_authority"] == "NONE"
    assert empty["canonical_write_authorized"] is False
    assert empty["structural_identity_authorized"] is False

    item = next(row for row in queue["review_items"] if row["review_item_id"] == "GREF-REV-NPS-P059-LEGEND")
    accepted = copy.deepcopy(template)
    accepted["status"] = "HUMAN_REVIEW_DECISIONS_PRESENT"
    accepted["decisions"] = [
        {
            "decision_id": "GREF-TEST-DECISION-001",
            "review_item_id": item["review_item_id"],
            "state": "ACCEPT_REFERENCE_EVIDENCE",
            "source_id": item["source_id"],
            "source_sha256": item["source_sha256"],
            "page_index": item["page_index"],
            "page_text_sha256": item["page_text_sha256"],
            "page_feature_sha256": item["page_feature_sha256"],
            "meaning": "TEST_GRAPHIC_REFERENCE_MEANING",
            "scope": {
                "discipline": "TEST_ONLY",
                "document_family": "TEST_ONLY"
            },
            "primitive_families": ["RECTILINEAR_CLOSED_SHAPE"],
            "aspect_buckets": ["SQUAREISH"],
            "area_buckets": ["SMALL"],
            "filled": False,
            "counterexample_refs": ["TEST-COUNTEREXAMPLE-001"],
            "reviewer": "CEW_TEST_REVIEWER",
            "rationale": "Synthetic gate decision only; not a repository semantic assertion.",
            "reviewed_at": "2026-09-02T00:00:00+00:00"
        }
    ]
    pack = packer.build_pack(acquisition, queue, accepted)
    assert pack["schema"] == pre.LIBRARY_SCHEMA
    assert pack["status"] == "LIBRARY_AVAILABLE_UNVERIFIED_FOR_CONTEXT"
    assert pack["generation_id"].startswith("GREF-GEN-")
    assert len(pack["content_sha256"]) == 64
    assert pack["entry_count"] == 1
    assert pack["tiers_present"] == ["EXTERNAL_REFERENCE"]
    assert pack["source_count"] == 1
    assert pack["sources"] == ["GREF-SRC-NPS-CAD-STANDARDS"]
    assert pack["project_human_validation_required_for_match"] is True
    assert pack["project_semantic_authority"] == "NONE"
    assert pack["canonical_write_authorized"] is False
    assert pack["structural_identity_authorized"] is False
    entry = pack["entries"][0]
    assert entry["meaning"] == "TEST_GRAPHIC_REFERENCE_MEANING"
    assert entry["tier"] == "EXTERNAL_REFERENCE"
    assert entry["source_refs"][0]["source_sha256"] == item["source_sha256"]
    assert entry["source_refs"][0]["page_feature_sha256"] == item["page_feature_sha256"]
    assert entry["review"]["reviewer"] == "CEW_TEST_REVIEWER"
    assert entry["project_semantic_authority"] == "NONE"

    # The output pack must be accepted by the zero-prior matcher only as an
    # advisory library generation; its content hash must cover the exact entries.
    assert pack["content_sha256"] == pre._library_entries_fingerprint(pack["entries"])

    # Discovery text must never be enough: an accepted decision with no meaning
    # is rejected even though the queue item was discovered by the word "legend".
    missing_meaning = copy.deepcopy(accepted)
    missing_meaning["decisions"][0]["meaning"] = ""
    try:
        packer.build_pack(acquisition, queue, missing_meaning)
    except ValueError as exc:
        assert str(exc) == "REFERENCE_REVIEW_MEANING_REQUIRED"
    else:
        raise AssertionError("accepted reference evidence without human meaning must fail")

    # Any drift from the exact acquired page fingerprint fails closed.
    drift = copy.deepcopy(accepted)
    drift["decisions"][0]["page_feature_sha256"] = "0" * 64
    try:
        packer.build_pack(acquisition, queue, drift)
    except ValueError as exc:
        assert str(exc) == "REFERENCE_REVIEW_PAGE_FEATURE_SHA256_MISMATCH"
    else:
        raise AssertionError("reference page fingerprint drift must fail")

    # Rejection/defer decisions never create entries.
    rejected = copy.deepcopy(template)
    rejected["decisions"] = [
        {
            "decision_id": "GREF-TEST-REJECT-001",
            "review_item_id": item["review_item_id"],
            "state": "REJECT_REFERENCE_EVIDENCE",
            "source_id": item["source_id"],
            "source_sha256": item["source_sha256"],
            "page_index": item["page_index"],
            "page_text_sha256": item["page_text_sha256"],
            "page_feature_sha256": item["page_feature_sha256"],
            "reviewer": "CEW_TEST_REVIEWER",
            "rationale": "Synthetic rejection gate.",
            "reviewed_at": "2026-09-02T00:00:00+00:00"
        }
    ]
    rejected_pack = packer.build_pack(acquisition, queue, rejected)
    assert rejected_pack["status"] == "LIBRARY_EMPTY"
    assert rejected_pack["entry_count"] == 0

    print("CEW_EXTERNAL_GRAPHIC_REFERENCE_PACK_PASS")
    print("empty_review_creates_zero_entries=true human_acceptance_required=true")
    print("exact_source_page_fingerprint_binding=true discovery_query_never_supplies_meaning=true")
    print("external_reference_pack_project_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
