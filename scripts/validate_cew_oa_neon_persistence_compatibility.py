#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_OA_NEON_PERSISTENCE_COMPATIBILITY_CONTRACT_v1.json"
MIGRATION = ROOT / "migrations/cew/005_oa_receipt_residual_optional_PROPOSED_NOT_APPLIED.sql"
READBACK = ROOT / "automation/receipts/cew-oa/CEW_OA_NEON_SCHEMA_READBACK_2026-08-31.json"
AUDIT = ROOT / "scripts/cew_runtime_audit_store.py"
GOVERNED = ROOT / "scripts/cew_oa_governed_audit.py"
QUEUE = ROOT / "automation/CEW_OBJECT_ACQUISITION_QUEUE_v1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    migration = MIGRATION.read_text(encoding="utf-8")
    readback = json.loads(READBACK.read_text(encoding="utf-8"))
    audit = AUDIT.read_text(encoding="utf-8")
    governed = GOVERNED.read_text(encoding="utf-8")
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))

    require(contract["contract"] == "CEW_OA_NEON_PERSISTENCE_COMPATIBILITY", "contract id drift")
    require(contract["status"] == "LIVE_SCHEMA_VERIFIED_RUNTIME_RETEST_CANDIDATE_PASS", "runtime retest candidate state missing")
    require(contract["canonical_write_authorized"] is False, "canonical write authority drift")
    require(contract["project_material_ready"] is False, "project material must remain blocked")
    require(contract["oa6_release_authorized"] is False, "OA-6 release authority drift")

    rule = contract["domain_rule"]
    require(rule["erw_receipt_residual_id_required_by_application"] is True, "ERW residual semantics weakened")
    require(rule["oa_receipt_residual_id_required"] is False, "OA must not be modeled as ERW residual")
    require(rule["oa_fake_residual_id_forbidden"] is True, "fake OA residual ids must be forbidden")
    require(rule["shared_table_residual_id_must_be_nullable"] is True, "shared ledger nullable requirement missing")

    mig = contract["migration"]
    require(mig["state"] == "APPLIED_VERIFIED_MANUAL_READBACK", "migration live state not verified")
    require(mig["applied_to_project_id"] == "morning-cell-78488188", "unexpected Neon project")
    require(mig["applied_to_branch"] == "main", "migration not verified on main")
    require(mig["database"] == "neondb", "unexpected Neon database")
    require(mig["verified_postcondition"] == "residual_id IS NULLABLE", "verified postcondition drift")
    require(mig["readback_receipt"] == "automation/receipts/cew-oa/CEW_OA_NEON_SCHEMA_READBACK_2026-08-31.json", "readback receipt binding drift")

    runtime_retest = contract["runtime_retest"]
    require(runtime_retest["required"] is True, "runtime retest must remain required")
    require(runtime_retest["stage"] == "OA2_PROTOTYPE", "unexpected runtime retest stage")
    require(runtime_retest["candidate_head_sha"] == "69b85e319a818be6a7413f2e2e3a5d0130794ec0", "validated runtime candidate drift")
    require(runtime_retest["candidate_ci"] == "PASS", "runtime candidate CI not frozen PASS")
    require(runtime_retest["expected_audit_backend"] == "NEON_APPEND_ONLY", "runtime retest backend drift")
    require(runtime_retest["find_similar_unlock_requires_receipt"] is True, "Find Similar governance weakened")
    require(runtime_retest["source_primary_after_selection_required"] is True, "source-primary interaction guard missing")

    require(readback["receipt_type"] == "CEW_OA_NEON_SCHEMA_MANUAL_READBACK", "readback receipt type drift")
    require(readback["project_id"] == "morning-cell-78488188", "readback project mismatch")
    require(readback["branch"] == "main", "readback branch mismatch")
    require(readback["table"] == "public.cew_human_receipt_audit", "readback table mismatch")
    require(readback["column"] == "residual_id", "readback column mismatch")
    require(readback["observed_is_nullable"] == "YES", "residual_id is not verified nullable")
    require(readback["migration_effect_verified"] is True, "migration effect not verified")
    require(readback["canonical_write_authorized"] is False, "readback cannot authorize canonical write")
    require(readback["project_material_ready"] is False, "readback cannot release project material")

    require("STATUS: PROPOSED_NOT_APPLIED" in migration, "historical migration proposal marker missing")
    require("ALTER COLUMN residual_id DROP NOT NULL" in migration, "required compatibility DDL missing")
    require("OA" in migration and "residual" in migration.lower(), "migration rationale missing")
    require("INSERT INTO public.cew_human_receipt_audit" in audit, "shared Neon ledger insert missing")
    require('"residual_id": receipt.get("residual_id")' in audit, "audit store must preserve absent OA residual as NULL")

    require('"residual_id"' not in governed, "OA governed receipt model fabricated residual identity")
    require("receipt_type" in governed and "CEW_OA_GOVERNED_DECISION_RECEIPT_V1" in governed, "OA governed receipt identity missing")

    blocks = queue.get("global_blocks") or {}
    require(blocks.get("canonical_write_authorized") is False, "queue canonical write block drift")
    require(blocks.get("project_material_ready") is False, "queue project material block drift")
    items = {row["id"]: row for row in queue.get("items", [])}
    require(items.get("OA-6", {}).get("state") == "BLOCKED_BY_OA5", "OA-6 must remain blocked")

    print("CEW_OA_NEON_PERSISTENCE_COMPATIBILITY = PASS")
    print("LIVE_SCHEMA_READBACK = PASS")
    print("RESIDUAL_ID_NULLABLE = YES")
    print("RUNTIME_RETEST_CANDIDATE = PASS")
    print("RUNTIME_RETEST_REQUIRED = true")
    print("OA_FAKE_RESIDUAL_ID = FORBIDDEN")
    print("MIGRATION_STATE = APPLIED_VERIFIED_MANUAL_READBACK")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("PROJECT_MATERIAL_READY = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
