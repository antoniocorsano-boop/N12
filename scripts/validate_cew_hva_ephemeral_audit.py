#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import cew_hva_ephemeral_audit as adapter
import cew_runtime_audit_store as audit_store


def _clear_backend_env() -> None:
    for key in (
        "CEW_AUDIT_NEON_DATABASE_URL",
        "CEW_AUDIT_HTTPS_URL",
        "CEW_AUDIT_SHARED_SECRET",
        "CEW_AUDIT_SUPABASE_URL",
        "CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY",
        "VERCEL",
    ):
        os.environ.pop(key, None)


def main() -> None:
    saved = dict(os.environ)
    try:
        _clear_backend_env()
        os.environ["RENDER"] = "true"
        os.environ.pop("CEW_HVA_EPHEMERAL_AUDIT", None)
        adapter.install()

        assert audit_store.backend_status() == "UNCONFIGURED_PRODUCTION"

        os.environ["CEW_HVA_EPHEMERAL_AUDIT"] = "1"
        assert adapter.enabled() is True
        assert audit_store.backend_status() == "FILESYSTEM_APPEND_ONLY"

        receipt = {
            "receipt_type": "CEW_HVA_EPHEMERAL_TEST_v1",
            "decision_id": "hva-ephemeral-test-001",
            "timestamp": "2026-09-05T07:00:00+00:00",
            "authority": "RUNTIME_AUDIT_ONLY",
            "canonical_write": False,
        }
        with TemporaryDirectory() as tmp:
            store = Path(tmp)
            persisted = audit_store.persist_runtime_receipt(receipt, store)
            assert persisted["audit_backend"] == "FILESYSTEM_APPEND_ONLY"
            assert persisted["canonical_write"] is False
            loaded = audit_store.load_runtime_receipts(receipt["receipt_type"], store)
            assert loaded["receipt_count"] == 1
            assert loaded["canonical_write"] is False
            assert loaded["engineering_authority_effect"] == "NONE"

        # A real configured backend always takes precedence over the HVA fallback.
        os.environ["CEW_AUDIT_NEON_DATABASE_URL"] = "postgresql://configured-backend"
        assert audit_store.backend_status() == "NEON_APPEND_ONLY"

        # The flag is Render-only; it does not convert a Vercel production runtime.
        os.environ.pop("CEW_AUDIT_NEON_DATABASE_URL", None)
        os.environ.pop("RENDER", None)
        os.environ["VERCEL"] = "1"
        assert adapter.enabled() is False
        assert audit_store.backend_status() == "UNCONFIGURED_PRODUCTION"

        print("HVA_EPHEMERAL_AUDIT_PASS")
    finally:
        os.environ.clear()
        os.environ.update(saved)


if __name__ == "__main__":
    main()
