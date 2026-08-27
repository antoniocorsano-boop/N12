#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import app as webapp
import cew_runtime_audit_store as audit_store

CONTRACT = ROOT / "automation/CEW_USER_WEB_PILOT_CONTRACT_v1.json"
SQL = ROOT / "automation/CEW_USER_WEB_PILOT_SUPABASE_v1.sql"
APP = ROOT / "app.py"


def main():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["user_mode"] == "SINGLE_OPERATOR_PILOT"
    assert contract["entrypoint"] == "app.py"
    assert contract["authority_invariants"]["canonical_write_authorized_by_web_pilot"] is False
    assert contract["authority_invariants"]["canonical_write_performed_by_web_pilot"] is False
    assert contract["security_invariants"]["production_submit_fails_closed_without_persistent_audit_backend"] is True

    sql = SQL.read_text(encoding="utf-8").lower()
    assert "cew_human_receipt_audit" in sql
    assert "before update or delete" in sql
    assert "append-only" in sql
    assert "revoke all" in sql

    app_text = APP.read_text(encoding="utf-8")
    assert "review_service.process_receipt" in app_text
    assert "review_service.persist_runtime_receipt = audit_store.persist_runtime_receipt" in app_text
    assert "CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY" not in app_text
    assert "data/canonical" not in app_text.replace('review_service.STATE', '').replace('review_service.ISSUES', '')

    old = dict(os.environ)
    try:
        os.environ.pop("VERCEL", None)
        os.environ.pop("CEW_AUDIT_SUPABASE_URL", None)
        os.environ.pop("CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY", None)
        assert audit_store.backend_status() == "FILESYSTEM_APPEND_ONLY"
        with tempfile.TemporaryDirectory() as td:
            receipt = {"decision_id": "VALIDATOR-LOCAL-001", "task_id": "ERW-N12-001", "residual_id": "M1E-B06-R08", "timestamp": "2026-08-27T00:00:00Z"}
            result = audit_store.persist_runtime_receipt(receipt, Path(td))
            assert result["authority"] == "RUNTIME_AUDIT_ONLY"
            assert result["canonical_write"] is False
            try:
                audit_store.persist_runtime_receipt(receipt, Path(td))
                raise AssertionError("duplicate decision id was accepted")
            except ValueError:
                pass

        os.environ["VERCEL"] = "1"
        os.environ["CEW_AUTH_DISABLED_FOR_TEST"] = "1"
        assert webapp._auth_disabled_for_test() is False
        assert audit_store.backend_status() == "UNCONFIGURED_PRODUCTION"
        with tempfile.TemporaryDirectory() as td:
            try:
                audit_store.persist_runtime_receipt({"decision_id": "PROD-NO-STORE"}, Path(td))
                raise AssertionError("production filesystem fallback was accepted")
            except ValueError as e:
                assert "not configured" in str(e)
    finally:
        os.environ.clear()
        os.environ.update(old)

    print("CEW USER WEB PILOT: PASS | auth_guard=PASS | audit_append_only=PASS | production_fail_closed=PASS | canonical_write=0")


if __name__ == "__main__":
    main()
