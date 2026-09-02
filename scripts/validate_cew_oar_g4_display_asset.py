#!/usr/bin/env python3
"""Fail-closed parity gate for the exact visual asset used by OAR G4 review."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ID = "CEW-N12-ASSET-TAV05S-P001-OAR-300DPI"
HISTORICAL_ASSET_ID = "CEW-N12-ASSET-TAV05S-P001-300DPI"
ASSET_SHA256 = "6344abae8d390ef799812c808427431e684a61cca6bb5792de331b2b9d2b6252"
SOURCE_VERSION_ID = "CEW-N12-SRC-TAV05S-V2143DBCF"
PAGE_ID = "CEW-N12-PAGE-TAV05S-P001"
TRANSFORM_ID = "CEW-N12-XFORM-TAV05S-P001-OAR"
HISTORICAL_TRANSFORM_ID = "CEW-N12-XFORM-TAV05S-P001"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _bbox_contract(sql: str) -> None:
    lower = sql.lower()
    for marker in (
        "OAR_REGION_BBOX_REQUIRED",
        "OAR_REGION_BBOX_INVALID",
        "OAR_REGION_BBOX_OUT_OF_RANGE",
        "OAR_REGION_BBOX_EMPTY",
        "OAR_REGION_BBOX_EXCEEDS_PAGE",
    ):
        assert marker in sql, marker
    assert "jsonb_typeof(p_receipt->'bbox') is distinct from 'object'" in lower
    for key in ("x", "y", "w", "h"):
        assert f"jsonb_typeof(p_receipt->'bbox'->'{key}') is distinct from 'number'" in lower
        assert f"v_{key} := (p_receipt->'bbox'->>'{key}')::numeric;" in lower
    assert "v_x < 0 or v_x > 1" in lower
    assert "v_y < 0 or v_y > 1" in lower
    assert "v_w < 0 or v_w > 1" in lower
    assert "v_h < 0 or v_h > 1" in lower
    assert "v_w <= 0 or v_h <= 0" in lower
    assert "v_x + v_w > 1 or v_y + v_h > 1" in lower


def _confirmation_bbox_cas_guard(sql_patch: str) -> None:
    lower = sql_patch.lower()
    append_marker = "create or replace function public.cew_oar_append_region_receipt_v1"
    assert append_marker in lower
    append_sql = lower[lower.index(append_marker):]

    lock_marker = "perform pg_advisory_xact_lock"
    current_proposal_marker = "into v_current_proposal"
    anchored_decision_marker = "where a.decision_id=v_current"
    proposal_action_marker = "and a.receipt_json->>'action'='propose_geometry'"
    validate_anchor_marker = "perform public.cew_oar_validate_g4_receipt_v1(v_current_proposal, v_binding_id, v_support_id)"
    bbox_guard_marker = "if p_receipt->'bbox' is distinct from v_current_proposal->'bbox' then"
    mismatch_marker = "oar_region_confirmation_bbox_mismatch"
    audit_insert_marker = "insert into public.cew_human_receipt_audit"
    head_update_marker = "update public.cew_oar_region_revision_heads set"

    for marker in (
        lock_marker,
        current_proposal_marker,
        anchored_decision_marker,
        proposal_action_marker,
        validate_anchor_marker,
        bbox_guard_marker,
        mismatch_marker,
        audit_insert_marker,
        head_update_marker,
    ):
        assert marker in append_sql, marker

    # The immutable anchored proposal must be loaded and validated under the
    # support advisory lock. A mismatched confirmation must fail before either
    # the append-only audit INSERT or GEOMETRY_CONFIRMED head mutation.
    lock_pos = append_sql.index(lock_marker)
    proposal_pos = append_sql.index(current_proposal_marker)
    validate_pos = append_sql.index(validate_anchor_marker)
    bbox_guard_pos = append_sql.index(bbox_guard_marker)
    audit_insert_pos = append_sql.index(audit_insert_marker)
    head_update_pos = append_sql.index(head_update_marker, audit_insert_pos)
    assert "state='geometry_confirmed'" in append_sql[head_update_pos:]
    assert lock_pos < proposal_pos < validate_pos < bbox_guard_pos < audit_insert_pos < head_update_pos


def main() -> None:
    binding = json.loads(read("automation/CEW_OAR_G4_COLUMN_REGION_BINDING_v1.json"))
    doc = binding["document"]
    assert doc["source_version_id"] == SOURCE_VERSION_ID
    assert doc["page_id"] == PAGE_ID
    assert doc["derived_asset_id"] == ASSET_ID
    assert doc["page_transform_id"] == TRANSFORM_ID
    assert doc["render_sha256"] == ASSET_SHA256
    assert doc["render_width_px"] == 7016
    assert doc["render_height_px"] == 12530
    assert binding["workflow"]["canonical_write_authorized"] is False

    with (ROOT / "data/canonical/CEW_DERIVED_ASSET_REGISTRY_v1.csv").open(newline="", encoding="utf-8") as handle:
        assets = {row["derived_asset_id"]: row for row in csv.DictReader(handle)}
    asset = assets[ASSET_ID]
    assert asset["source_version_id"] == SOURCE_VERSION_ID
    assert asset["page_id"] == PAGE_ID
    assert asset["asset_role"] == "OAR_FULL_PAGE_INTERACTION_RENDER"
    assert asset["format"] == "JPEG"
    assert asset["dpi"] == "300"
    assert asset["width_px"] == "7016" and asset["height_px"] == "12530"
    assert asset["generator"] == "PyMuPDF" and asset["generator_version"] == "1.26.4"
    assert ASSET_SHA256 in asset["generation_basis"]
    assert asset["authority_state"] == "DERIVED_REVIEW_AID_ONLY"
    assert asset["reproducibility_state"] == "REPRODUCIBLE_FROM_IMMUTABLE_SOURCE"

    with (ROOT / "data/canonical/CEW_PAGE_TRANSFORM_REGISTRY_v1.csv").open(newline="", encoding="utf-8") as handle:
        transforms = {row["transform_id"]: row for row in csv.DictReader(handle)}
    transform = transforms[TRANSFORM_ID]
    assert transform["page_id"] == PAGE_ID
    assert transform["derived_asset_id"] == ASSET_ID
    assert transform["normalized_to_derived_formula"] == "x_px=x_n*7016;y_px=y_n*12530"
    assert transform["derived_to_normalized_formula"] == "x_n=x_px/7016;y_n=y_px/12530"
    assert transform["readiness_state"] == "READY"
    assert ASSET_SHA256 in transform["verification_basis"]
    historical_transform = transforms[HISTORICAL_TRANSFORM_ID]
    assert historical_transform["derived_asset_id"] == HISTORICAL_ASSET_ID
    assert historical_transform["derived_asset_id"] != transform["derived_asset_id"]

    resolver = read("scripts/cew_oar_g4_source_resolver.py")
    assert f'REGISTERED_DERIVED_ASSET_ID = "{ASSET_ID}"' in resolver
    assert f'REGISTERED_RENDER_SHA256 = "{ASSET_SHA256}"' in resolver
    assert "RUNTIME_DPI = 300" in resolver
    assert "JPEG_QUALITY = 92" in resolver
    assert "pixmap.save(RUNTIME_RASTER, jpg_quality=JPEG_QUALITY)" in resolver
    assert "_verify_registered_raster(RUNTIME_RASTER)" in resolver

    netlify_replay = read("netlify/functions/cew-oar-replay.mjs")
    assert f'derived_asset_id: "{ASSET_ID}"' in netlify_replay
    assert f'page_transform_id: "{TRANSFORM_ID}"' in netlify_replay
    assert "validateOarReceiptGovernance" in netlify_replay

    sql_patch = read("sql/CEW_OAR_G4_DISPLAY_ASSET_BINDING_v1.sql")
    sql_patch_lower = sql_patch.lower()
    assert "create or replace function public.cew_oar_validate_g4_receipt_v1" in sql_patch_lower
    assert f"is distinct from '{ASSET_ID}'" in sql_patch
    assert f"is distinct from '{TRANSFORM_ID}'" in sql_patch
    assert "v_action is null or v_action not in" in sql_patch_lower
    assert "canonical_write_authorized" in sql_patch
    assert "engineering_authority_effect" in sql_patch
    _bbox_contract(sql_patch)
    _confirmation_bbox_cas_guard(sql_patch)

    # The base migration itself must already understand current receipts before
    # installing replay/backfill. Otherwise a rerun would temporarily restore
    # the historical asset predicate and abort while replaying current history.
    atomic_sql = read("sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql")
    atomic_lower = atomic_sql.lower()
    validator_marker = "create or replace function public.cew_oar_validate_g4_receipt_v1"
    replay_marker = "create or replace function public.cew_oar_replay_region_head_v1"
    backfill_marker = "with legacy_supports as ("
    validator_start = atomic_lower.index(validator_marker)
    replay_start = atomic_lower.index(replay_marker)
    backfill_start = atomic_lower.index(backfill_marker)
    base_validator = atomic_sql[validator_start:replay_start]
    assert f"is distinct from '{ASSET_ID}'" in base_validator
    assert f"is distinct from '{TRANSFORM_ID}'" in base_validator
    assert HISTORICAL_ASSET_ID not in base_validator
    assert HISTORICAL_TRANSFORM_ID + "'" not in base_validator
    _bbox_contract(base_validator)
    assert validator_start < replay_start < backfill_start
    assert "reapplying" in atomic_lower[:replay_start] or "reapplying" in atomic_lower

    validator_call = "perform public.cew_oar_validate_g4_receipt_v1(p_receipt, v_binding_id, v_support_id);"
    receipt_insert = "insert into public.cew_human_receipt_audit"
    assert validator_call in atomic_sql
    assert receipt_insert in atomic_sql
    assert atomic_sql.index(validator_call) < atomic_sql.index(receipt_insert)

    provisioning = json.loads(read("automation/CEW_OAR_G4_SUPABASE_PROVISIONING_v1.json"))
    assert provisioning["ordered_sql"] == [
        "automation/CEW_USER_WEB_PILOT_SUPABASE_v1.sql",
        "sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql",
        "sql/CEW_OAR_G4_DISPLAY_ASSET_BINDING_v1.sql",
    ]
    runtime = provisioning["required_runtime_contract"]
    assert runtime["derived_asset_id"] == ASSET_ID
    assert runtime["render_sha256"] == ASSET_SHA256
    assert runtime["confirmation_geometry_guard"] == "ATOMIC_ANCHORED_PROPOSAL_BBOX_MATCH_REQUIRED"
    assert "CONFIRM_GEOMETRY" in provisioning["activation_rule"]
    assert "advisory lock" in provisioning["activation_rule"]
    assert provisioning["authority"]["canonical_write_authorized"] is False
    assert provisioning["authority"]["structural_identity_authorized"] is False
    assert provisioning["authority"]["oar_human_confirmation"] is False
    assert provisioning["authority"]["engineering_authority_effect"] == "NONE"

    with (ROOT / "knowledge/ARTIFACT_REGISTRY_CEW_PROMOTION_ENGINE_PATCH_v1.csv").open(newline="", encoding="utf-8") as handle:
        registered = {row["artifact_id"]: row for row in csv.DictReader(handle)}
    patch = registered["SCHEMA-CEW-OAR-DISPLAY-ASSET-001"]
    procedure = registered["PROCEDURE-CEW-OAR-SUPABASE-001"]
    assert patch["path"] == "sql/CEW_OAR_G4_DISPLAY_ASSET_BINDING_v1.sql"
    assert patch["authority"] == "PROCEDURE" and patch["status"] == "CURRENT"
    assert procedure["path"] == "automation/CEW_OAR_G4_SUPABASE_PROVISIONING_v1.json"
    assert procedure["authority"] == "PROCEDURE" and procedure["status"] == "CURRENT"

    print("CEW_OAR_G4_DISPLAY_ASSET_PASS")
    print(f"derived_asset_id={ASSET_ID} transform_id={TRANSFORM_ID}")
    print(f"render_sha256={ASSET_SHA256} dimensions=7016x12530 dpi=300 generator=PyMuPDF-1.26.4")
    print("python=BOUND netlify=BOUND supabase_base=BOUND supabase_patch=BOUND provisioning=ORDERED")
    print("base_migration_current_receipt_replay=RERUN_SAFE")
    print("supabase_bbox_validation=FAIL_CLOSED before_atomic_receipt_insert=true")
    print("supabase_confirmation_bbox_guard=ATOMIC_ANCHORED_PROPOSAL_MATCH before_audit_append=true before_head_mutation=true")
    print("source_authority=IMMUTABLE_PDF display_authority=DERIVED_REVIEW_AID_ONLY canonical_write_authorized=false")


if __name__ == "__main__":
    main()
