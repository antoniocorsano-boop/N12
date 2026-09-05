#!/usr/bin/env python3
"""Deterministic gate for the human-reviewed EXTERNAL_REFERENCE pack builder."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import cew_external_graphic_reference_pack as packer
import cew_new_project_preacquisition as pre

ROOT = Path(__file__).resolve().parents[1]
ACQUISITION = ROOT / "knowledge" / "graphic_reference" / "CEW_EXTERNAL_REFERENCE_ACQUISITION_RECEIPT_v1.json"
QUEUE = ROOT / "knowledge" / "graphic_reference" / "CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1.json"
TEMPLATE = ROOT / "knowledge" / "graphic_reference" / "CEW_EXTERNAL_REFERENCE_REVIEW_DECISIONS_TEMPLATE_v1.json"


def _expect_error(fn, marker: str) -> None:
    try:
        fn()
    except ValueError as exc:
        assert str(exc) == marker, (str(exc), marker)
    else:
        raise AssertionError(f"expected ValueError {marker}")


def _base_decision(item: dict, decision_id: str, state: str, reviewed_at: str) -> dict:
    return {
        "decision_id": decision_id,
        "review_item_id": item["review_item_id"],
        "state": state,
        "source_id": item["source_id"],
        "source_sha256": item["source_sha256"],
        "page_index": item["page_index"],
        "page_text_sha256": item["page_text_sha256"],
        "page_feature_sha256": item["page_feature_sha256"],
        "reviewer": "CEW_TEST_REVIEWER",
        "rationale": "Synthetic deterministic review decision only; not a repository semantic assertion.",
        "reviewed_at": reviewed_at,
    }


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
    contract = template["decision_contract"]
    assert contract["discovery_query_may_supply_meaning"] is False
    assert contract["automatic_acceptance_forbidden"] is True
    assert contract["defer_is_terminal"] is False
    assert set(contract["terminal_states"]) == packer.TERMINAL_STATES
    assert set(contract["nonterminal_states"]) == packer.NONTERMINAL_STATES
    assert contract["append_only_followup_after_defer_allowed"] is True
    assert contract["followup_after_terminal_forbidden"] is True
    assert contract["pack_requires_terminal_decision_for_every_review_item"] is True

    empty = packer.build_pack(acquisition, queue, template)
    assert empty["schema"] == packer.LIBRARY_SCHEMA
    assert empty["status"] == "LIBRARY_EMPTY"
    assert empty["entry_count"] == 0
    assert empty["entries"] == []
    assert empty["build_state"] == "HUMAN_REVIEW_NOT_STARTED"
    assert empty["project_semantic_authority"] == "NONE"
    assert empty["canonical_write_authorized"] is False
    assert empty["structural_identity_authorized"] is False

    items = queue["review_items"]
    accepted_item = next(row for row in items if row["review_item_id"] == "GREF-REV-NPS-P059-LEGEND")

    # A single accepted decision cannot create a pack while other review items
    # remain unresolved.
    partial = copy.deepcopy(template)
    accepted_decision = _base_decision(
        accepted_item,
        "GREF-TEST-ACCEPT-001",
        "ACCEPT_REFERENCE_EVIDENCE",
        "2026-09-02T00:01:00+00:00",
    )
    accepted_decision.update(
        {
            "meaning": "TEST_GRAPHIC_REFERENCE_MEANING",
            "scope": {"discipline": "TEST_ONLY", "document_family": "TEST_ONLY"},
            "primitive_families": ["RECTILINEAR_CLOSED_SHAPE"],
            "aspect_buckets": ["SQUAREISH"],
            "area_buckets": ["SMALL"],
            "filled": False,
            "counterexample_refs": ["TEST-COUNTEREXAMPLE-001"],
        }
    )
    partial["status"] = "HUMAN_REVIEW_IN_PROGRESS"
    partial["decisions"] = [accepted_decision]
    _expect_error(lambda: packer.build_pack(acquisition, queue, partial), "REFERENCE_REVIEW_INCOMPLETE")

    # DEFER is explicitly non-terminal and cannot satisfy completeness.
    deferred = copy.deepcopy(template)
    deferred["status"] = "HUMAN_REVIEW_IN_PROGRESS"
    deferred["decisions"] = [
        _base_decision(
            items[0],
            "GREF-TEST-DEFER-001",
            "DEFER",
            "2026-09-02T00:00:10+00:00",
        )
    ]
    _expect_error(lambda: packer.build_pack(acquisition, queue, deferred), "REFERENCE_REVIEW_INCOMPLETE")

    # Complete append-only history: one item is deferred first and then resolved;
    # every other item gets exactly one terminal decision. Only the accepted page
    # becomes an EXTERNAL_REFERENCE entry.
    complete = copy.deepcopy(template)
    complete["status"] = "HUMAN_REVIEW_COMPLETE"
    history: list[dict] = []
    for index, item in enumerate(items, start=1):
        if item["review_item_id"] == accepted_item["review_item_id"]:
            history.append(
                _base_decision(
                    item,
                    "GREF-TEST-DEFER-BEFORE-ACCEPT",
                    "DEFER",
                    "2026-09-02T00:00:20+00:00",
                )
            )
            history.append(copy.deepcopy(accepted_decision))
        else:
            history.append(
                _base_decision(
                    item,
                    f"GREF-TEST-REJECT-{index:03d}",
                    "REJECT_REFERENCE_EVIDENCE",
                    f"2026-09-02T00:0{index + 1}:00+00:00",
                )
            )
    complete["decisions"] = history
    pack = packer.build_pack(acquisition, queue, complete)
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
    assert entry["source_refs"][0]["source_sha256"] == accepted_item["source_sha256"]
    assert entry["source_refs"][0]["page_feature_sha256"] == accepted_item["page_feature_sha256"]
    assert entry["review"]["reviewer"] == "CEW_TEST_REVIEWER"
    assert entry["project_semantic_authority"] == "NONE"
    assert pack["content_sha256"] == pre._library_entries_fingerprint(pack["entries"])

    # Discovery text must never be enough: an accepted terminal decision without
    # explicit human meaning fails even in a complete review history.
    missing_meaning = copy.deepcopy(complete)
    for decision in missing_meaning["decisions"]:
        if decision["state"] == "ACCEPT_REFERENCE_EVIDENCE":
            decision["meaning"] = ""
    _expect_error(lambda: packer.build_pack(acquisition, queue, missing_meaning), "REFERENCE_REVIEW_MEANING_REQUIRED")

    # Any drift from the exact acquired page fingerprint fails closed.
    drift = copy.deepcopy(complete)
    for decision in drift["decisions"]:
        if decision["state"] == "ACCEPT_REFERENCE_EVIDENCE":
            decision["page_feature_sha256"] = "0" * 64
    _expect_error(lambda: packer.build_pack(acquisition, queue, drift), "REFERENCE_REVIEW_PAGE_FEATURE_SHA256_MISMATCH")

    # A receipt after a terminal decision is invalid, even though storage is
    # append-only. Human history may be extended only while the item is deferred.
    after_terminal = copy.deepcopy(complete)
    after_terminal["decisions"].append(
        _base_decision(
            accepted_item,
            "GREF-TEST-DEFER-AFTER-ACCEPT",
            "DEFER",
            "2026-09-02T00:09:00+00:00",
        )
    )
    _expect_error(lambda: packer.build_pack(acquisition, queue, after_terminal), "REFERENCE_REVIEW_DECISION_AFTER_TERMINAL")

    # A fully terminal all-rejected review is complete but creates no entries.
    all_rejected = copy.deepcopy(template)
    all_rejected["status"] = "HUMAN_REVIEW_COMPLETE"
    all_rejected["decisions"] = [
        _base_decision(
            item,
            f"GREF-TEST-ALL-REJECT-{index:03d}",
            "REJECT_REFERENCE_EVIDENCE",
            f"2026-09-02T01:0{index}:00+00:00",
        )
        for index, item in enumerate(items, start=1)
    ]
    rejected_pack = packer.build_pack(acquisition, queue, all_rejected)
    assert rejected_pack["status"] == "LIBRARY_EMPTY"
    assert rejected_pack["entry_count"] == 0
    assert rejected_pack["build_state"] == "HUMAN_REVIEW_COMPLETE_NO_ACCEPTED_REFERENCE_EVIDENCE"

    print("CEW_EXTERNAL_GRAPHIC_REFERENCE_PACK_PASS")
    print("empty_review_creates_zero_entries=true partial_review_blocked=true")
    print("defer_nonterminal=true defer_then_terminal_allowed=true decision_after_terminal_blocked=true")
    print("complete_terminal_review_required=true exact_source_page_fingerprint_binding=true")
    print("external_reference_pack_project_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
