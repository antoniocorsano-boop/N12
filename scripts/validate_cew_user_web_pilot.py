#!/usr/bin/env python3
from __future__ import annotations

import csv
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
OAR_ATOMIC_SQL = ROOT / "sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql"
PROVISIONING = ROOT / "docs/ARCHITECTURE/CEW_USER_WEB_PILOT_v1.md"
REGISTRY = ROOT / "knowledge/ARTIFACT_REGISTRY_CEW_PROMOTION_ENGINE_PATCH_v1.csv"
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

    atomic_sql = OAR_ATOMIC_SQL.read_text(encoding="utf-8")
    assert "cew_oar_append_region_receipt_v1" in atomic_sql
    assert "cew_oar_read_region_receipts_v1" in atomic_sql
    assert "cew_oar_region_revision_heads" in atomic_sql
    assert "pg_advisory_xact_lock" in atomic_sql
    assert "OAR_REGION_REVISION_CONFLICT" in atomic_sql
    assert "language sql" in atomic_sql.lower()
    assert "stable" in atomic_sql.lower()
    assert "canonical_write" in atomic_sql and "false" in atomic_sql

    provisioning = PROVISIONING.read_text(encoding="utf-8")
    audit_pos = provisioning.index("automation/CEW_USER_WEB_PILOT_SUPABASE_v1.sql")
    atomic_pos = provisioning.index("sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql")
    assert audit_pos < atomic_pos
    assert "cew_oar_append_region_receipt_v1" in provisioning
    assert "cew_oar_read_region_receipts_v1" in provisioning
    assert "cew_oar_region_revision_heads" in provisioning
    assert "snapshot MVCC" in provisioning
    assert "non provisionato" in provisioning.lower()

    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    atomic_row = next((row for row in rows if row["artifact_id"] == "SCHEMA-CEW-OAR-ATOMIC-001"), None)
    assert atomic_row is not None
    assert atomic_row["path"] == "sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql"
    assert atomic_row["authority"] == "PROCEDURE"
    assert atomic_row["status"] == "CURRENT"
    assert "SCHEMA-CEW-WEB-AUDIT-001" in atomic_row["replaces_or_relates"]
    assert "CONTRACT-CEW-OAR-G4-REGION-001" in atomic_row["replaces_or_relates"]

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

    print("CEW USER WEB PILOT: PASS | auth_guard=PASS | audit_append_only=PASS | oar_atomic_supabase_provisioning=PASS | oar_mvcc_snapshot_rpc=PASS | production_fail_closed=PASS | canonical_write=0")


if __name__ == "__main__":
    main()
