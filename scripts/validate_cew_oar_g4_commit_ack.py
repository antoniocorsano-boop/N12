#!/usr/bin/env python3
"""Prove committed OAR writes ignore post-commit outages and worker-clock skew."""
from __future__ import annotations

import cew_oar_g4_region_binding as binding
import cew_oar_g4_region_workbench as workbench


def _result(receipt: dict, timestamp: str) -> dict:
    value = dict(receipt)
    value["timestamp"] = timestamp
    return {
        "runtime_receipt_id": value["decision_id"],
        "sha256": "a" * 64,
        "audit_backend": "TEST_ATOMIC_APPEND_ONLY",
        "atomic_revision": True,
        "committed_receipt": value,
    }


def _validate_commit_ack() -> None:
    contract = binding.load_contract()
    pre_report = binding.aggregate([], contract)
    calls = {"load_report": 0, "history_preflight": 0, "persist": 0}

    original_load_report = workbench._base.load_report
    original_loader = workbench._base.audit_store.load_runtime_receipts
    original_persist = workbench._atomic_store.persist_region_receipt
    try:
        def one_read_only():
            calls["load_report"] += 1
            if calls["load_report"] > 1:
                raise ValueError("SIMULATED_POST_COMMIT_REFRESH_OUTAGE")
            return pre_report

        def no_history_preflight(*args, **kwargs):
            calls["history_preflight"] += 1
            raise AssertionError("worker-timestamp transition preflight must not run")

        def committed(receipt, store):
            calls["persist"] += 1
            return _result(receipt, "2026-09-02T13:00:00+00:00")

        workbench._base.load_report = one_read_only
        workbench._base.audit_store.load_runtime_receipts = no_history_preflight
        workbench._atomic_store.persist_region_receipt = committed
        result = workbench.persist_action({
            "decision_id": "commit-ack-proposal",
            "support_id": "1",
            "action": binding.PROPOSAL_ACTION,
            "bbox": {"x": 0.1, "y": 0.2, "w": 0.02, "h": 0.03},
        })
        assert calls == {"load_report": 1, "history_preflight": 0, "persist": 1}, calls
        assert result["state"] == "OAR_REGION_RECEIPT_COMMITTED_AUDIT_ONLY"
        assert result["commit_acknowledged"] is True
        assert result["status_refresh_required"] is True
        assert result["object_state"] == "PROPOSED"
        assert result["canonical_write_authorized"] is False
        assert result["engineering_authority_effect"] == "NONE"
    finally:
        workbench._base.load_report = original_load_report
        workbench._base.audit_store.load_runtime_receipts = original_loader
        workbench._atomic_store.persist_region_receipt = original_persist


def _validate_worker_clock_skew() -> None:
    """A valid replacement must reach CAS even if the worker clock is behind."""
    contract = binding.load_contract()
    initial = binding.build_receipt(
        decision_id="clock-skew-p0",
        support_id="1",
        bbox={"x": 0.10, "y": 0.20, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        timestamp="2026-09-02T12:00:00+00:00",
        base_proposal_decision_id=binding.unbound_revision_anchor("1"),
        contract=contract,
    )
    pre_report = binding.aggregate([initial], contract)
    calls = {"load_report": 0, "history_preflight": 0, "persist": 0}

    original_load_report = workbench._base.load_report
    original_loader = workbench._base.audit_store.load_runtime_receipts
    original_persist = workbench._atomic_store.persist_region_receipt
    original_build = workbench._binding.build_receipt
    try:
        def current_report():
            calls["load_report"] += 1
            return pre_report

        def no_history_preflight(*args, **kwargs):
            calls["history_preflight"] += 1
            raise AssertionError("clock-skewed intent must not be replayed before CAS")

        def skewed_build(**kwargs):
            return original_build(timestamp="2026-09-02T11:00:00+00:00", **kwargs)

        def atomic_commit(receipt, store):
            calls["persist"] += 1
            assert receipt["timestamp"] == "2026-09-02T11:00:00+00:00"
            assert receipt["base_proposal_decision_id"] == "clock-skew-p0"
            committed = dict(receipt)
            committed["timestamp"] = "2026-09-02T13:00:00+00:00"
            # The same intent that would sort before its predecessor on the
            # worker clock is valid once the persistence boundary owns time.
            report = binding.aggregate([initial, committed], contract)
            row = next(item for item in report["objects"] if item["support_id"] == "1")
            assert row["state"] == "PROPOSED"
            assert row["geometry_proposal_receipt_id"] == "clock-skew-p1"
            return _result(receipt, "2026-09-02T13:00:00+00:00")

        workbench._base.load_report = current_report
        workbench._base.audit_store.load_runtime_receipts = no_history_preflight
        workbench._atomic_store.persist_region_receipt = atomic_commit
        workbench._binding.build_receipt = skewed_build
        result = workbench.persist_action({
            "decision_id": "clock-skew-p1",
            "support_id": "1",
            "action": binding.PROPOSAL_ACTION,
            "bbox": {"x": 0.11, "y": 0.20, "w": 0.02, "h": 0.03},
        })
        assert calls == {"load_report": 1, "history_preflight": 0, "persist": 1}, calls
        assert result["object_state"] == "PROPOSED"
        assert result["commit_acknowledged"] is True
    finally:
        workbench._base.load_report = original_load_report
        workbench._base.audit_store.load_runtime_receipts = original_loader
        workbench._atomic_store.persist_region_receipt = original_persist
        workbench._binding.build_receipt = original_build


def main() -> None:
    _validate_commit_ack()
    _validate_worker_clock_skew()
    print("CEW_OAR_G4_COMMIT_ACK_PASS")
    print("atomic_commit=ACKNOWLEDGED post_commit_load_report_calls=0 history_preflight_calls=0")
    print("worker_clock_skew=IGNORED transition_order_authority=ATOMIC_COMMIT_TIMESTAMP")
    print("canonical_write_authorized=false engineering_authority_effect=NONE")


if __name__ == "__main__":
    main()
