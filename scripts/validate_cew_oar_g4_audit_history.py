#!/usr/bin/env python3
"""Regression checks for paginated/reduced OAR audit history."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
    # governed-read page size. Legacy unanchored proposals remain readable.
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
        assert loaded["history_policy"] == "PAGINATED_APPEND_ONLY_ANCHOR_CLOSED_SINGLE_PASS_REDUCED_FOR_STATE_RECONSTRUCTION"
        report = binding.aggregate(loaded["receipts"], contract)
        row = next(item for item in report["objects"] if item["support_id"] == "1")
        assert row["state"] == "PROPOSED"
        assert report["canonical_write_authorized"] is False

    # Anchor-aware reduction retains the complete predecessor chain required by
    # an active replacement proposal, terminating at governed UNBOUND revision 0.
    unbound = binding.unbound_revision_anchor("1")
    p0 = binding.build_receipt(
        decision_id="anchor-p0",
        support_id="1",
        bbox={"x": 0.10, "y": 0.20, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        base_proposal_decision_id=unbound,
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

    # Two workers can observe the same UNBOUND revision. If one first proposal is
    # confirmed before the delayed sibling arrives, that sibling is audit-visible
    # but stale/non-mutating rather than a permanent GEOMETRY_ALREADY_CONFIRMED poison.
    initial_anchor = binding.unbound_revision_anchor("3")
    first = binding.build_receipt(
        decision_id="unbound-first-winner",
        support_id="3",
        bbox={"x": 0.20, "y": 0.30, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        base_proposal_decision_id=initial_anchor,
        timestamp="2026-09-01T10:00:00+00:00",
        contract=contract,
    )
    first_confirm = binding.build_receipt(
        decision_id="unbound-first-confirm",
        support_id="3",
        bbox=first["bbox"],
        action=binding.CONFIRM_ACTION,
        base_proposal_decision_id=first["decision_id"],
        timestamp="2026-09-01T10:01:00+00:00",
        contract=contract,
    )
    delayed = binding.build_receipt(
        decision_id="unbound-delayed-loser",
        support_id="3",
        bbox={"x": 0.24, "y": 0.30, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        base_proposal_decision_id=initial_anchor,
        timestamp="2026-09-01T10:02:00+00:00",
        contract=contract,
    )
    race_compact, race_total = history._reduce_history([[first, first_confirm, delayed]], contract)
    assert race_total == 3
    assert [row["decision_id"] for row in race_compact] == ["unbound-first-winner", "unbound-first-confirm"]
    race_report = binding.aggregate([first, first_confirm, delayed], contract)
    race_row = next(item for item in race_report["objects"] if item["support_id"] == "3")
    assert race_row["state"] == "GEOMETRY_CONFIRMED"
    assert race_row["geometry_confirmation_receipt_id"] == "unbound-first-confirm"
    assert race_report["summary"]["stale_concurrent_transitions"] == 1

    # Complexity regression: a long anchored chain must not trigger aggregate on
    # every prefix. The reducer validates the full history once and the compact
    # self-contained history once, independent of receipt count.
    long_chain: list[dict] = []
    base_time = datetime(2026, 9, 1, 11, 0, tzinfo=timezone.utc)
    previous = binding.unbound_revision_anchor("4")
    for index in range(1000):
        receipt = binding.build_receipt(
            decision_id=f"linear-chain-{index:04d}",
            support_id="4",
            bbox={"x": 0.30 + (index % 10) * 0.0001, "y": 0.40, "w": 0.02, "h": 0.03},
            action=binding.PROPOSAL_ACTION,
            base_proposal_decision_id=previous,
            timestamp=(base_time + timedelta(seconds=index)).isoformat(),
            contract=contract,
        )
        long_chain.append(receipt)
        previous = receipt["decision_id"]

    original_aggregate = binding.aggregate
    aggregate_calls = [0]

    def counted_aggregate(*args, **kwargs):
        aggregate_calls[0] += 1
        return original_aggregate(*args, **kwargs)

    binding.aggregate = counted_aggregate
    try:
        long_compact, long_total = history._reduce_history([long_chain], contract)
    finally:
        binding.aggregate = original_aggregate
    assert long_total == 1000
    assert len(long_compact) == 1000
    assert aggregate_calls[0] == 2, aggregate_calls[0]
    long_report = binding.aggregate(long_compact, contract)
    long_row = next(item for item in long_report["objects"] if item["support_id"] == "4")
    assert long_row["geometry_proposal_receipt_id"] == "linear-chain-0999"

    proposal = binding.build_receipt(
        decision_id="authority-proposal",
        support_id="2",
        bbox=bbox,
        action=binding.PROPOSAL_ACTION,
        base_proposal_decision_id=binding.unbound_revision_anchor("2"),
        timestamp="2026-09-01T12:00:00+00:00",
        contract=contract,
    )
    confirmation = binding.build_receipt(
        decision_id="authority-confirm",
        support_id="2",
        bbox=bbox,
        action=binding.CONFIRM_ACTION,
        base_proposal_decision_id="authority-proposal",
        timestamp="2026-09-01T12:01:00+00:00",
        contract=contract,
    )
    divergent = dict(confirmation)
    divergent["decision_id"] = "authority-confirm-divergent"
    divergent["timestamp"] = "2026-09-01T12:02:00+00:00"
    divergent["canonical_write_authorized"] = True
    _must_fail(
        lambda: history._reduce_history([[proposal, confirmation, divergent]], contract),
        "GOVERNED_FIELD_MISMATCH_CANONICAL_WRITE_AUTHORIZED",
    )

    print("CEW_OAR_G4_AUDIT_HISTORY_PASS")
    print("append_only_receipts=501 pagination=true anchor_chain_receipts=3 self_contained=true")
    print("unbound_revision_race=STALE_NON_MUTATING long_chain_receipts=1000 aggregate_calls=2")
    print("authority_divergent_receipt=FAILS_BEFORE_TRANSITION canonical_write_authorized=false")


if __name__ == "__main__":
    main()
