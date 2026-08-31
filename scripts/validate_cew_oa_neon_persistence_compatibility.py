#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_OA_NEON_PERSISTENCE_COMPATIBILITY_CONTRACT_v1.json"
MIGRATION = ROOT / "migrations/cew/005_oa_receipt_residual_optional_PROPOSED_NOT_APPLIED.sql"
AUDIT = ROOT / "scripts/cew_runtime_audit_store.py"
GOVERNED = ROOT / "scripts/cew_oa_governed_audit.py"
QUEUE = ROOT / "automation/CEW_OBJECT_ACQUISITION_QUEUE_v1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    migration = MIGRATION.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    governed = GOVERNED.read_text(encoding="utf-8")
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))

    require(contract["contract"] == "CEW_OA_NEON_PERSISTENCE_COMPATIBILITY", "contract id drift")
    require(contract["status"] == "PREPARED_MIGRATION_NOT_APPLIED", "migration must remain explicitly unapplied before live DB verification")
    require(contract["canonical_write_authorized"] is False, "canonical write authority drift")
    require(contract["project_material_ready"] is False, "project material must remain blocked")
    require(contract["oa6_release_authorized"] is False, "OA-6 release authority drift")

    rule = contract["domain_rule"]
    require(rule["erw_receipt_residual_id_required_by_application"] is True, "ERW residual semantics weakened")
    require(rule["oa_receipt_residual_id_required"] is False, "OA must not be modeled as ERW residual")
    require(rule["oa_fake_residual_id_forbidden"] is True, "fake OA residual ids must be forbidden")
    require(rule["shared_table_residual_id_must_be_nullable"] is True, "shared ledger nullable requirement missing")

    require("STATUS: PROPOSED_NOT_APPLIED" in migration, "migration status marker missing")
    require("ALTER COLUMN residual_id DROP NOT NULL" in migration, "required compatibility DDL missing")
    require("OA" in migration and "residual" in migration.lower(), "migration rationale missing")
    require("INSERT INTO public.cew_human_receipt_audit" in audit, "shared Neon ledger insert missing")
    require('"residual_id": receipt.get("residual_id")' in audit, "audit store must preserve absent OA residual as NULL")

    # OA governed receipts are intentionally not residual-resolution receipts.
    require('"residual_id"' not in governed, "OA governed receipt model fabricated residual identity")
    require("receipt_type" in governed and "CEW_OA_GOVERNED_DECISION_RECEIPT_V1" in governed, "OA governed receipt identity missing")

    blocks = queue.get("global_blocks") or {}
    require(blocks.get("canonical_write_authorized") is False, "queue canonical write block drift")
    require(blocks.get("project_material_ready") is False, "queue project material block drift")
    items = {row["id"]: row for row in queue.get("items", [])}
    require(items.get("OA-6", {}).get("state") == "BLOCKED_BY_OA5", "OA-6 must remain blocked")

    print("CEW_OA_NEON_PERSISTENCE_COMPATIBILITY_PREP_PASS")
    print("OA_FAKE_RESIDUAL_ID = FORBIDDEN")
    print("MIGRATION_STATE = PROPOSED_NOT_APPLIED")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("PROJECT_MATERIAL_READY = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
