#!/usr/bin/env python3
"""Regression checks for Arena-style atomic OAR revision persistence."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

import cew_oar_g4_atomic_store as atomic_store
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
    # Force the deterministic local backend; production backends use the same
    # revision-CAS contract through Neon transaction / Supabase RPC / Netlify SQL.
    for name in (
        "CEW_AUDIT_NEON_DATABASE_URL",
        "CEW_AUDIT_HTTPS_URL",
        "CEW_AUDIT_SHARED_SECRET",
        "CEW_AUDIT_SUPABASE_URL",
        "CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY",
        "VERCEL",
        "RENDER",
    ):
        os.environ.pop(name, None)

    contract = binding.load_contract()
    unbound = binding.unbound_revision_anchor("1")

    with tempfile.TemporaryDirectory(prefix="cew-oar-atomic-") as tmp:
        store = Path(tmp)
        winner = binding.build_receipt(
            decision_id="atomic-initial-winner",
            support_id="1",
            bbox={"x": 0.10, "y": 0.20, "w": 0.02, "h": 0.03},
            action=binding.PROPOSAL_ACTION,
            base_proposal_decision_id=unbound,
            timestamp="2099-01-01T00:00:00+00:00",
            contract=contract,
        )
        winner_result = atomic_store.persist_region_receipt(winner, store)
        assert winner_result["atomic_revision"] is True
        assert winner_result["committed_receipt"]["timestamp"] != winner["timestamp"]

        confirmation = binding.build_receipt(
            decision_id="atomic-confirm-winner",
            support_id="1",
            bbox=winner["bbox"],
            action=binding.CONFIRM_ACTION,
            base_proposal_decision_id=winner["decision_id"],
            timestamp="2099-01-01T00:01:00+00:00",
            contract=contract,
        )
        atomic_store.persist_region_receipt(confirmation, store)

        # This worker was created before the winner (earlier timestamp) but is
        # delayed until after the winner was persisted and confirmed. Timestamp
        # must not let it rewrite history: the CAS rejects it before append.
        delayed_older = binding.build_receipt(
            decision_id="atomic-delayed-older-loser",
            support_id="1",
            bbox={"x": 0.15, "y": 0.20, "w": 0.02, "h": 0.03},
            action=binding.PROPOSAL_ACTION,
            base_proposal_decision_id=unbound,
            timestamp="2000-01-01T00:00:00+00:00",
            contract=contract,
        )
        _must_fail(
            lambda: atomic_store.persist_region_receipt(delayed_older, store),
            "OAR_REGION_GEOMETRY_ALREADY_CONFIRMED",
        )
        assert not (store / f"{delayed_older['decision_id']}.json").exists()

        loaded = history.load_runtime_receipts(binding.RECEIPT_TYPE, store, max_receipts=20)
        assert loaded["receipt_count"] == 2
        report = binding.aggregate(loaded["receipts"], contract)
        row = next(item for item in report["objects"] if item["support_id"] == "1")
        assert row["state"] == "GEOMETRY_CONFIRMED"
        assert row["geometry_proposal_receipt_id"] == winner["decision_id"]
        assert row["geometry_confirmation_receipt_id"] == confirmation["decision_id"]

        # Same-revision replacement race: only the first committed transition
        # can advance the revision. A sibling intent from the old proposal is
        # rejected before it can become governed history.
        p0 = binding.build_receipt(
            decision_id="atomic-p0",
            support_id="2",
            bbox={"x": 0.20, "y": 0.30, "w": 0.02, "h": 0.03},
            action=binding.PROPOSAL_ACTION,
            base_proposal_decision_id=binding.unbound_revision_anchor("2"),
            timestamp="2099-02-01T00:00:00+00:00",
            contract=contract,
        )
        atomic_store.persist_region_receipt(p0, store)
        p1 = binding.build_receipt(
            decision_id="atomic-p1",
            support_id="2",
            bbox={"x": 0.21, "y": 0.30, "w": 0.02, "h": 0.03},
            action=binding.PROPOSAL_ACTION,
            base_proposal_decision_id=p0["decision_id"],
            timestamp="2099-02-01T00:01:00+00:00",
            contract=contract,
        )
        atomic_store.persist_region_receipt(p1, store)
        sibling = binding.build_receipt(
            decision_id="atomic-p1-sibling",
            support_id="2",
            bbox={"x": 0.22, "y": 0.30, "w": 0.02, "h": 0.03},
            action=binding.PROPOSAL_ACTION,
            base_proposal_decision_id=p0["decision_id"],
            timestamp="2000-02-01T00:00:00+00:00",
            contract=contract,
        )
        _must_fail(lambda: atomic_store.persist_region_receipt(sibling, store), "OAR_REGION_REVISION_CONFLICT")
        assert not (store / f"{sibling['decision_id']}.json").exists()

        # Audit files are receipt-only; lock state is not an authority artifact.
        receipt_files = [p for p in store.glob("*.json")]
        assert len(receipt_files) == 4
        for path in receipt_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload["canonical_write_authorized"] is False
            assert payload["structural_identity_authorized"] is False
            assert payload["oar_human_confirmation"] is False
            assert payload["engineering_authority_effect"] == "NONE"

    print("CEW_OAR_G4_ATOMIC_STORE_PASS")
    print("older_timestamp_delayed_append=REJECTED_BEFORE_GOVERNED_LOG")
    print("same_revision_sibling=REVISION_CONFLICT atomic_revision=true")
    print("canonical_write_authorized=false structural_identity_authorized=false")


if __name__ == "__main__":
    main()
