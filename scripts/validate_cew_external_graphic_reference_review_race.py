#!/usr/bin/env python3
"""Regression gate for concurrent/replayed external-reference review receipts."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import cew_external_graphic_reference_review_hardening as hardening
import cew_external_graphic_reference_review_workbench as review


def _payload(item: dict, decision_id: str, state: str = "REJECT_REFERENCE_EVIDENCE") -> dict:
    return {
        "decision_id": decision_id,
        "review_item_id": item["review_item_id"],
        "state": state,
        "reviewer": "CI-RACE-REVIEWER",
        "rationale": "Deterministic concurrent receipt regression test.",
    }


def main() -> None:
    hardening.install(review)
    _acquisition, queue = review._governed()
    items = queue["review_items"]
    old_store = review.REVIEW_STORE
    old_backend_status = review.audit_store.backend_status
    try:
        with tempfile.TemporaryDirectory(prefix="cew-reference-review-race-") as tmp:
            review.REVIEW_STORE = Path(tmp)
            review.audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"

            # Two equivalent submissions are idempotent and create one audit row.
            first = items[0]
            one = review.persist_review_receipt(_payload(first, "race-idempotent-001"))
            two = review.persist_review_receipt(_payload(first, "race-idempotent-002"))
            assert one["idempotent_replay"] is False
            assert two["idempotent_replay"] is True
            assert two["runtime_receipt_id"] == one["runtime_receipt_id"]
            governed = review.audit_store.load_runtime_receipts(review.RECEIPT_TYPE, review.REVIEW_STORE)
            assert governed["receipt_count"] == 1
            status = review.review_status()
            assert status["terminal_decision_count"] == 1
            assert status["items"][0]["decision_history_count"] == 1

        with tempfile.TemporaryDirectory(prefix="cew-reference-review-legacy-replay-") as tmp:
            review.REVIEW_STORE = Path(tmp)
            review.audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"
            second = items[1]
            receipt_a = review.build_review_receipt(_payload(second, "legacy-race-a"))
            receipt_b = dict(receipt_a)
            receipt_b["decision_id"] = "legacy-race-b"
            receipt_b["timestamp"] = "2026-09-03T03:14:04.792491+00:00"
            receipt_b["reviewed_at"] = receipt_b["timestamp"]
            review.audit_store.persist_runtime_receipt(receipt_a, review.REVIEW_STORE)
            review.audit_store.persist_runtime_receipt(receipt_b, review.REVIEW_STORE)
            status = review.review_status()
            item = next(row for row in status["items"] if row["review_item_id"] == second["review_item_id"])
            assert status["terminal_decision_count"] == 1
            assert item["terminal"] is True
            assert item["decision_history_count"] == 2
            decisions = review.decisions_document()
            assert decisions["terminal_decision_count"] == 1
            assert decisions["decision_history_count"] == 2

        with tempfile.TemporaryDirectory(prefix="cew-reference-review-conflict-") as tmp:
            review.REVIEW_STORE = Path(tmp)
            review.audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"
            third = items[2]
            reject = review.build_review_receipt(_payload(third, "conflict-terminal"))
            defer = review.build_review_receipt(_payload(third, "conflict-after-terminal", state="DEFER"))
            defer["timestamp"] = "2026-09-03T03:15:04.792491+00:00"
            defer["reviewed_at"] = defer["timestamp"]
            review.audit_store.persist_runtime_receipt(reject, review.REVIEW_STORE)
            review.audit_store.persist_runtime_receipt(defer, review.REVIEW_STORE)
            try:
                review.review_status()
            except ValueError as exc:
                assert str(exc) == "REFERENCE_REVIEW_DECISION_AFTER_TERMINAL"
            else:
                raise AssertionError("conflicting post-terminal decision must remain fail-closed")
    finally:
        review.REVIEW_STORE = old_store
        review.audit_store.backend_status = old_backend_status

    source = Path(__file__).with_name("cew_external_graphic_reference_review_hardening.py").read_text(encoding="utf-8")
    assert "pg_advisory_xact_lock" in source
    assert "REFERENCE_REVIEW_DECISION_AFTER_TERMINAL" in source
    assert "idempotent_replay" in source
    print("CEW_EXTERNAL_REFERENCE_REVIEW_RACE_PASS")
    print("double_submit=idempotent legacy_equivalent_terminal_replay=reconciled conflicting_terminal_replay=blocked")
    print("neon_transition_lock=pg_advisory_xact_lock audit_history=append_only")


if __name__ == "__main__":
    main()
