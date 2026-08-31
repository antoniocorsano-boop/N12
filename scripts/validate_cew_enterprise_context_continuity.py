#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

CONTRACT = ROOT / "automation/CEW_ENTERPRISE_CONTEXT_CONTINUITY_CONTRACT_v1.json"
API = ROOT / "scripts/cew_oa_governed_api.py"
RESUME = ROOT / "scripts/cew_enterprise_governed_resume_runtime.py"
EWS1 = ROOT / "scripts/cew_ews1_application_frame_runtime.py"
PILOT = "OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    api = API.read_text(encoding="utf-8")
    resume = RESUME.read_text(encoding="utf-8")
    ews1 = EWS1.read_text(encoding="utf-8")

    require(contract["contract"] == "CEW_ENTERPRISE_CONTEXT_CONTINUITY", "contract id drift")
    require(contract["authority_effect"] == "NONE", "resume cannot create authority")
    require(contract["canonical_write_authorized"] is False, "canonical write drift")
    require(contract["project_material_ready"] is False, "project material release drift")
    inv = contract["invariants"]
    require(inv["ledger_is_source_of_truth"] is True, "ledger authority weakened")
    require(inv["session_storage_role"] == "UI_CACHE_ONLY", "sessionStorage role drift")
    require(inv["resume_is_read_only"] is True, "resume must be read-only")
    require(inv["same_semantic_decision_replay"] == "RETURN_EXISTING_RECEIPT_NO_NEW_WRITE", "idempotency drift")
    require(inv["decision_id_collision"] == "FAIL_CLOSED", "collision guard missing")
    require(inv["stale_source_receipt"] == "FAIL_CLOSED", "stale source guard missing")

    for marker in [
        '@router.get("/api/workbench/object-acquisition/resume")',
        "OA_GOVERNED_RECEIPT_RESUMED_READ_ONLY",
        "OA_GOVERNED_RECEIPT_ALREADY_PERSISTED",
        "idempotent_replay",
        "_same_semantic_decision",
        "OA_GOVERNED_DECISION_ID_COLLISION",
        "OA_GOVERNED_STALE_SOURCE_RECEIPT_PRESENT",
    ]:
        require(marker in api, f"API invariant missing: {marker}")

    # The existing receipt must be returned before persistence is invoked.
    existing_pos = api.find("existing = governed.index_receipts")
    persist_pos = api.find("persisted = audit_store.persist_runtime_receipt")
    require(existing_pos >= 0 and persist_pos > existing_pos, "idempotent replay must precede append-only write")

    for marker in [
        "CEW_ENTERPRISE_GOVERNED_CONTEXT_RESUME",
        "/api/workbench/object-acquisition/resume?task=",
        "resumed_from_governed_ledger:true",
        "sessionStorage.setItem('cew-oa2:'",
        "cew:oa2-prototype-persisted",
        "nessuna nuova scrittura",
    ]:
        require(marker in resume, f"resume runtime invariant missing: {marker}")
    require("/api/workbench/object-acquisition/receipt" not in resume, "resume adapter may not POST receipts")
    require("canonical_write_authorized" not in resume or "true" not in resume, "resume runtime authority drift")

    require("import cew_enterprise_governed_resume_runtime as resume_runtime" in ews1, "resume compositor import missing")
    require("resume_runtime.augment(ews4_runtime.augment(rendered, task), task)" in ews1, "resume must compose after EWS-4")

    html = oa1_runtime.augment(client.build_client(PILOT), PILOT)
    require("CEW_ENTERPRISE_GOVERNED_CONTEXT_RESUME" in html, "rendered pilot missing resume adapter")
    require('data-resume-runtime="CEW_ENTERPRISE_GOVERNED_CONTEXT_RESUME"' in html, "resume marker not emitted")
    require("data-canonical-write-authorized=\"false\"" in html, "canonical write boundary lost")

    forbidden = set(contract["forbidden_shortcuts"])
    for name in {
        "SESSION_STORAGE_AS_GOVERNED_AUTHORITY",
        "DUPLICATE_APPEND_ONLY_WRITE_FOR_IDENTICAL_DECISION",
        "IGNORE_SOURCE_REVISION_ON_RESUME",
        "INVENT_RECEIPT_ON_CLIENT",
        "MUTATE_EXISTING_RECEIPT",
        "CANONICAL_WRITE_FROM_RESUME",
    }:
        require(name in forbidden, f"forbidden shortcut missing: {name}")

    print("CEW_ENTERPRISE_CONTEXT_CONTINUITY = PASS")
    print("LEDGER_SOURCE_OF_TRUTH = true")
    print("SESSION_STORAGE_ROLE = UI_CACHE_ONLY")
    print("IDENTICAL_DECISION_REPLAY = RETURN_EXISTING_NO_WRITE")
    print("GOVERNED_RESUME = READ_ONLY")
    print("OA3_RESUME_EVENT = enabled")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
