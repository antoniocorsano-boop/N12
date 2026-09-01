#!/usr/bin/env python3
"""Prove a committed OAR receipt is acknowledged without post-commit refresh."""
from __future__ import annotations

import cew_oar_g4_region_binding as binding
import cew_oar_g4_region_workbench as workbench


def main() -> None:
    contract = binding.load_contract()
    pre_report = binding.aggregate([], contract)
    calls = {"load_report": 0, "persist": 0}

    original_load_report = workbench._base.load_report
    original_loader = workbench._base.audit_store.load_runtime_receipts
    original_persist = workbench._atomic_store.persist_region_receipt
    try:
        def one_read_only():
            calls["load_report"] += 1
            if calls["load_report"] > 1:
                raise ValueError("SIMULATED_POST_COMMIT_REFRESH_OUTAGE")
            return pre_report

        workbench._base.load_report = one_read_only
        workbench._base.audit_store.load_runtime_receipts = lambda *args, **kwargs: {
            "receipts": [], "receipt_count": 0, "reduced_receipt_count": 0,
            "audit_backend": "FILESYSTEM_APPEND_ONLY",
        }

        def committed(receipt, store):
            calls["persist"] += 1
            value = dict(receipt)
            value["timestamp"] = "2026-09-01T17:00:00+00:00"
            return {
                "runtime_receipt_id": value["decision_id"],
                "sha256": "a" * 64,
                "audit_backend": "TEST_ATOMIC_APPEND_ONLY",
                "atomic_revision": True,
                "committed_receipt": value,
            }

        workbench._atomic_store.persist_region_receipt = committed
        result = workbench.persist_action({
            "decision_id": "commit-ack-proposal",
            "support_id": "1",
            "action": binding.PROPOSAL_ACTION,
            "bbox": {"x": 0.1, "y": 0.2, "w": 0.02, "h": 0.03},
        })
        assert calls == {"load_report": 1, "persist": 1}, calls
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

    print("CEW_OAR_G4_COMMIT_ACK_PASS")
    print("atomic_commit=ACKNOWLEDGED post_commit_load_report_calls=0 refresh=SEPARATE")
    print("canonical_write_authorized=false engineering_authority_effect=NONE")


if __name__ == "__main__":
    main()
