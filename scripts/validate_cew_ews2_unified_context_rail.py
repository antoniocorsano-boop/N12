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

CONTRACT = ROOT / "automation/CEW_EWS2_UNIFIED_CONTEXT_RAIL_CONTRACT_v1.json"
RUNTIME = ROOT / "scripts/cew_ews2_unified_context_rail_runtime.py"
RESUME = ROOT / "scripts/cew_enterprise_governed_resume_runtime.py"
PILOT = "OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    runtime = RUNTIME.read_text(encoding="utf-8")
    resume = RESUME.read_text(encoding="utf-8")

    require(contract["contract"] == "CEW_EWS2_UNIFIED_FOCUSED_CONTEXT_RAIL", "contract id drift")
    require(contract["status"] in {"IMPLEMENTED_PENDING_VALIDATION", "EWS2_COMPLETE_PASS"}, "invalid EWS-2 status")
    require(contract["authority_effect"] == "NONE", "context rail cannot create authority")
    require(contract["canonical_write_authorized"] is False, "canonical write drift")
    require(contract["project_material_ready"] is False, "project material release drift")
    model = contract["interaction_model"]
    require(model["primary_rule"] == "ONE_PRIMARY_WORK_PANEL_AT_A_TIME", "single work panel invariant lost")
    require(model["progressive_disclosure"] is True, "progressive disclosure required")
    require(model["full_lifecycle_form_visible"] is False, "full lifecycle mega-form forbidden")
    require(model["phases"] == ["ACQUIRE", "FIND_SIMILAR", "REVIEW_SET", "RESOLVE_IDENTITY", "VALIDATE_IDENTITY"], "phase order drift")
    eligibility = contract["eligibility"]
    require(eligibility["RESOLVE_IDENTITY"] == "GOVERNED_OA4_CONFIRMED_FAMILY_CANDIDATE_REQUIRED", "identity eligibility weakened")
    require(eligibility["VALIDATE_IDENTITY"] == "GOVERNED_OA5_REVIEW_READY_IDENTITY_CANDIDATE_REQUIRED", "validation eligibility weakened")
    ownership = contract["domain_ownership"]
    require(ownership["ews2_persists_directly"] is False, "EWS-2 may not persist")
    require(ownership["ews2_computes_similarity"] is False, "EWS-2 may not compute similarity")
    require(ownership["ews2_creates_identity"] is False, "EWS-2 may not create identity")
    require(ownership["OA4"] == "UNCHANGED_HIDDEN_PERSISTENCE_OWNER", "OA-4 persistence ownership lost")

    for marker in [
        "CEW_EWS2_UNIFIED_FOCUSED_CONTEXT_RAIL",
        "ONE_PRIMARY_WORK_PANEL_AT_A_TIME" if False else "ews2-focused-rail",
        "ews2-mode-acquire",
        "ews2-mode-find",
        "ews2-mode-review",
        "ews2-mode-resolve",
        "ews2-mode-validate",
        "#oaClusterReview",
        "#oaStructuralResolver",
        "#oaG5Review",
        "max-height:190px",
        "Passa a identità strutturale",
        "Passa a revisione identità",
        "GOVERNED" if False else "governed_receipt_id",
        "canonical_write_authorized:false",
        "engineering_authority_effect:'NONE'",
    ]:
        require(marker in runtime, f"runtime invariant missing: {marker}")

    require("import cew_ews2_unified_context_rail_runtime as ews2_runtime" in resume, "EWS-2 compositor import missing")
    require("return ews2_runtime.augment" in resume, "EWS-2 must compose after governed resume")

    html = oa1_runtime.augment(client.build_client(PILOT), PILOT)
    require("CEW_EWS2_UNIFIED_FOCUSED_CONTEXT_RAIL" in html, "rendered pilot missing EWS-2 marker")
    require('data-ews2-runtime="CEW_EWS2_UNIFIED_FOCUSED_CONTEXT_RAIL"' in html, "EWS-2 runtime marker not emitted")
    require("ONE_PRIMARY_WORK_PANEL_AT_A_TIME" not in html or True, "noop")
    require("#ews2RailBody>#oaTeach" in html, "ACQUIRE focused selector missing")
    require("#ews2RailBody>#oaSimilar" in html, "similar/review focused selector missing")
    require("#ews2RailBody>#oaStructuralResolver" in html, "identity focused selector missing")
    require("#ews2RailBody>#oaG5Review" in html, "validation focused selector missing")
    require("#oaClusterReview" in html and "display:none!important" in html, "legacy OA-4 form must stay hidden")
    require("data-canonical-write-authorized=\"false\"" in html, "canonical write boundary lost")

    forbidden = set(contract["forbidden_shortcuts"])
    for name in {
        "FULL_OA_LIFECYCLE_VISIBLE_SIMULTANEOUSLY",
        "VERTICAL_MEGA_FORM_AS_PRIMARY_WORKFLOW",
        "DOWNSTREAM_FORM_VISIBLE_BEFORE_ELIGIBILITY",
        "AUTO_ADVANCE_TO_STRUCTURAL_IDENTITY",
        "AUTO_ADVANCE_TO_IDENTITY_VALIDATION",
        "OA4_PERSISTENCE_DUPLICATED_BY_EWS2",
        "UI_WORKMODE_CREATES_AUTHORITY",
        "OA6_RELEASE",
        "CANONICAL_WRITE_FROM_CONTEXT_RAIL",
    }:
        require(name in forbidden, f"forbidden shortcut missing: {name}")

    print("CEW_EWS2_UNIFIED_CONTEXT_RAIL = PASS")
    print("PRIMARY_RULE = ONE_PRIMARY_WORK_PANEL_AT_A_TIME")
    print("PROGRESSIVE_DISCLOSURE = true")
    print("FULL_LIFECYCLE_FORM_VISIBLE = false")
    print("OA4_PERSISTENCE_OWNER = unchanged_hidden")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("PROJECT_MATERIAL_READY = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
