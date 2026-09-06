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
ATOMIC_STORE = ROOT / "scripts/cew_oar_g4_atomic_store.py"
REVISION_HEAD = ROOT / "scripts/cew_oar_g4_revision_head.py"
NETLIFY = ROOT / "netlify/functions/cew-audit.mjs"
NETLIFY_REPLAY = ROOT / "netlify/functions/cew-oar-replay.mjs"


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
    atomic_lower = atomic_sql.lower()
    assert "cew_oar_append_region_receipt_v1" in atomic_sql
    assert "cew_oar_read_region_receipts_v1" in atomic_sql
    assert "cew_oar_region_revision_heads" in atomic_sql
    assert "cew_oar_replay_region_head_v1" in atomic_sql
    assert "cew_oar_validate_g4_receipt_v1" in atomic_sql
    assert "pg_advisory_xact_lock" in atomic_sql
    assert "OAR_REGION_REVISION_CONFLICT" in atomic_sql
    assert "language sql" in atomic_lower
    assert "stable" in atomic_lower
    assert "returns jsonb" in atomic_lower
    assert "jsonb_agg" in atomic_sql
    assert "'receipt_count', count(*)" in atomic_sql
    assert "SERVER_MVCC_SINGLE_JSON_VALUE" in atomic_sql
    assert "canonical_write" in atomic_sql and "false" in atomic_sql

    # Legacy heads must be produced by anchored-transition replay and every
    # replayed/new receipt must satisfy the same G4 binding fields as the
    # canonical Python _validate_receipt_governance() predicate.
    validator_marker = "create or replace function public.cew_oar_validate_g4_receipt_v1"
    replay_marker = "create or replace function public.cew_oar_replay_region_head_v1"
    backfill_marker = "with legacy_supports as ("
    append_rpc_marker = "create or replace function public.cew_oar_append_region_receipt_v1"
    assert validator_marker in atomic_lower
    assert replay_marker in atomic_lower
    assert backfill_marker in atomic_lower
    assert append_rpc_marker in atomic_lower
    assert atomic_lower.index(validator_marker) < atomic_lower.index(replay_marker) < atomic_lower.index(backfill_marker) < atomic_lower.index(append_rpc_marker)
    assert "perform public.cew_oar_validate_g4_receipt_v1(v_receipt, p_binding_id, p_support_id)" in atomic_lower
    assert "perform public.cew_oar_validate_g4_receipt_v1(p_receipt, v_binding_id, v_support_id)" in atomic_lower
    # PostgreSQL `NULL NOT IN (...)` evaluates to NULL rather than TRUE. Both
    # the reusable governance validator and atomic RPC contract must therefore
    # reject NULL actions explicitly before any confirmation-like else branch.
    assert atomic_lower.count("v_action is null") >= 2
    assert "v_action is null or v_action not in ('propose_geometry','confirm_geometry')" in atomic_lower
    assert "oar_region_action_invalid" in atomic_lower
    for field in (
        "task_id", "residual_id", "pilot_id", "binding_id", "support_id", "evidence_object_id", "family_id",
        "source_version_id", "page_id", "derived_asset_id", "page_transform_id", "coordinate_system",
        "authority", "oar_human_confirmation", "structural_identity_authorized",
        "canonical_write_authorized", "engineering_authority_effect",
    ):
        assert f"oar_region_governed_field_mismatch_{field}" in atomic_lower
    assert "cross join lateral public.cew_oar_replay_region_head_v1" in atomic_lower
    assert "from public.cew_oar_replay_region_head_v1(v_binding_id, v_support_id)" in atomic_lower
    assert "confirmed_heads as (" not in atomic_lower
    assert "oar_region_base_proposal_mismatch" in atomic_lower
    assert "v_stale := v_stale + 1" in atomic_lower
    assert "on conflict (binding_id, support_id) do nothing" in atomic_lower

    drop_marker = "drop function if exists public.cew_oar_read_region_receipts_v1();"
    create_marker = "create function public.cew_oar_read_region_receipts_v1()"
    assert drop_marker in atomic_lower
    assert create_marker in atomic_lower
    assert atomic_lower.index(drop_marker) < atomic_lower.index(create_marker)
    assert "returns table(receipt_json jsonb)" not in atomic_lower[atomic_lower.index(create_marker):]

    # Neon and Netlify recover the current head from governed append-only replay
    # before enforcing CAS. Neon deliberately has no mutable revision-head table.
    atomic_store = ATOMIC_STORE.read_text(encoding="utf-8")
    revision_head = REVISION_HEAD.read_text(encoding="utf-8")
    netlify = NETLIFY.read_text(encoding="utf-8")
    netlify_replay = NETLIFY_REPLAY.read_text(encoding="utf-8")
    assert "binding.aggregate(existing)" in atomic_store
    assert "_assert_current_revision(receipt, existing)" in atomic_store
    assert "SELECT pg_advisory_xact_lock" in atomic_store
    assert "SELECT receipt_json FROM public.cew_human_receipt_audit" in atomic_store
    assert "binding.aggregate(receipts, contract)" in revision_head
    assert 'replayOarHead, validateOarReceiptGovernance' in netlify
    assert "validateOarReceiptGovernance(receipt, bindingId, supportId)" in netlify
    assert "legacyHead = replayOarHead" in netlify
    assert "legacyHead.receipt_count" in netlify
    assert "OAR_REGION_LEGACY_HEAD_REPLAY_FAILED" in netlify
    assert "export function validateOarReceiptGovernance" in netlify_replay
    assert "G4_FAMILY_BY_SUPPORT" in netlify_replay
    assert "G4_DOCUMENT" in netlify_replay
    assert "OAR_REGION_BASE_PROPOSAL_MISMATCH" in netlify_replay
    assert "staleTransitionCount" in netlify_replay

    provisioning = PROVISIONING.read_text(encoding="utf-8")
    audit_pos = provisioning.index("automation/CEW_USER_WEB_PILOT_SUPABASE_v1.sql")
    atomic_pos = provisioning.index("sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql")
    assert audit_pos < atomic_pos
    assert "cew_oar_append_region_receipt_v1" in provisioning
    assert "cew_oar_read_region_receipts_v1" in provisioning
    assert "cew_oar_replay_region_head_v1" in provisioning
    assert "cew_oar_region_revision_heads" in provisioning
    assert "snapshot" in provisioning.lower()
    assert "non provisionato" in provisioning.lower()
    assert "DROP FUNCTION IF EXISTS" in provisioning
    assert "return type" in provisioning.lower()
    assert "replay" in provisioning.lower()
    assert "ON CONFLICT" in provisioning
    assert "receipt legacy" in provisioning.lower()
    assert "Neon" in provisioning
    assert "Netlify" in provisioning
    assert "delayed CONFIRM(P0)" in provisioning
    assert "P1 / PROPOSED" in provisioning

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

    print("CEW USER WEB PILOT: PASS | auth_guard=PASS | audit_append_only=PASS | oar_atomic_supabase_provisioning=PASS | oar_cross_backend_revision_replay=PASS | oar_full_binding_replay_governance=PASS | oar_null_action_fail_closed=PASS | oar_mvcc_single_json_snapshot_rpc=PASS | oar_rpc_return_type_upgrade_safe=PASS | production_fail_closed=PASS | canonical_write=0")


if __name__ == "__main__":
    main()
