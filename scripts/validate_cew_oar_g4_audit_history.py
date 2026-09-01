#!/usr/bin/env python3
"""Regression checks for paginated/reduced OAR audit history."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import cew_oar_g4_audit_history as history
import cew_oar_g4_region_binding as binding


def _must_fail(callable_, marker: str) -> None:
    try:
        callable_()
    except ValueError as exc:
        assert marker in str(exc), (marker, str(exc))
    else:
        raise AssertionError(f"expected failure: {marker}")


def main() -> None:
    contract = binding.load_contract()
    bbox = {"x": 0.10, "y": 0.20, "w": 0.02, "h": 0.03}

    # Prove append-only history remains reconstructable beyond the generic
    # governed-read page size. Unanchored historical proposals can still reduce
    # to the latest active proposal without deleting or rewriting backend audit.
    with tempfile.TemporaryDirectory(prefix="cew-oar-history-") as tmp:
        store = Path(tmp)
        for index in range(501):
            receipt = binding.build_receipt(
                decision_id=f"history-g4-1-proposal-{index:04d}",
                support_id="1",
                bbox={"x": 0.10 + (index % 10) * 0.0001, "y": 0.20, "w": 0.02, "h": 0.03},
                action=binding.PROPOSAL_ACTION,
                timestamp=f"2026-09-01T08:{index // 60:02d}:{index % 60:02d}+00:00",
                contract=contract,
            )
            (store / f"{receipt['decision_id']}.json").write_text(
                json.dumps(receipt, sort_keys=True), encoding="utf-8"
            )
        loaded = history.load_runtime_receipts(binding.RECEIPT_TYPE, store, max_receipts=73)
        assert loaded["receipt_count"] == 501
        assert loaded["reduced_receipt_count"] == 1
        assert loaded["history_policy"] == "PAGINATED_APPEND_ONLY_ANCHOR_CLOSED_REDUCED_FOR_STATE_RECONSTRUCTION"
        report = binding.aggregate(loaded["receipts"], contract)
        row = next(item for item in report["objects"] if item["support_id"] == "1")
        assert row["state"] == "PROPOSED"
        assert report["canonical_write_authorized"] is False

    # Anchor-aware reduction must retain the complete predecessor chain required
    # by the active replacement proposal. This is the regression for the Codex
    # finding where compaction discarded a base_proposal_decision_id target.
    p0 = binding.build_receipt(
        decision_id="anchor-p0",
        support_id="1",
        bbox={"x": 0.10, "y": 0.20, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        timestamp="2026-09-01T09:00:00+00:00",
        contract=contract,
    )
    p1 = binding.build_receipt(
        decision_id="anchor-p1",
        support_id="1",
        bbox={"x": 0.11, "y": 0.20, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        base_proposal_decision_id="anchor-p0",
        timestamp="2026-09-01T09:01:00+00:00",
        contract=contract,
    )
    p2 = binding.build_receipt(
        decision_id="anchor-p2",
        support_id="1",
        bbox={"x": 0.12, "y": 0.20, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        base_proposal_decision_id="anchor-p1",
        timestamp="2026-09-01T09:02:00+00:00",
        contract=contract,
    )
    compact, total = history._reduce_history([[p0], [p1], [p2]], contract)
    assert total == 3
    assert [row["decision_id"] for row in compact] == ["anchor-p0", "anchor-p1", "anchor-p2"]
    anchor_report = binding.aggregate(compact, contract)
    anchor_row = next(item for item in anchor_report["objects"] if item["support_id"] == "1")
    assert anchor_row["state"] == "PROPOSED"
    assert anchor_row["geometry_proposal_receipt_id"] == "anchor-p2"
    assert anchor_row["bbox"] == p2["bbox"]

    proposal = binding.build_receipt(
        decision_id="authority-proposal",
        support_id="2",
        bbox=bbox,
        action=binding.PROPOSAL_ACTION,
        timestamp="2026-09-01T10:00:00+00:00",
        contract=contract,
    )
    confirmation = binding.build_receipt(
        decision_id="authority-confirm",
        support_id="2",
        bbox=bbox,
        action=binding.CONFIRM_ACTION,
        base_proposal_decision_id="authority-proposal",
        timestamp="2026-09-01T10:01:00+00:00",
        contract=contract,
    )
    divergent = dict(confirmation)
    divergent["decision_id"] = "authority-confirm-divergent"
    divergent["timestamp"] = "2026-09-01T10:02:00+00:00"
    divergent["canonical_write_authorized"] = True
    _must_fail(
        lambda: history._reduce_history([[proposal, confirmation, divergent]], contract),
        "GOVERNED_FIELD_MISMATCH_CANONICAL_WRITE_AUTHORIZED",
    )

    print("CEW_OAR_G4_AUDIT_HISTORY_PASS")
    print("append_only_receipts=501 pagination=true anchor_chain_receipts=3 self_contained=true")
    print("authority_divergent_receipt=FAILS_BEFORE_TRANSITION canonical_write_authorized=false")


if __name__ == "__main__":
    main()
