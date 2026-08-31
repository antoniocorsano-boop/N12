#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_oa1_workbench_runtime as oa1_runtime
import cew_professional_workbench_client as client

EWS1 = ROOT / "automation/CEW_EWS1_APPLICATION_FRAME_CONTRACT_v1.json"
EWS4 = ROOT / "automation/CEW_EWS4_OA_RESULT_REVIEW_CONTRACT_v1.json"
RUNTIME = ROOT / "scripts/cew_ews4_oa_result_review_runtime.py"
EWS1_RUNTIME = ROOT / "scripts/cew_ews1_application_frame_runtime.py"
PILOT = "OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    ews1 = json.loads(EWS1.read_text(encoding="utf-8"))
    ews4 = json.loads(EWS4.read_text(encoding="utf-8"))
    runtime = RUNTIME.read_text(encoding="utf-8")
    ews1_runtime = EWS1_RUNTIME.read_text(encoding="utf-8")

    require(ews1["status"] == "EWS1_COMPLETE_PASS", "EWS-1 is not complete")
    require(ews4["contract"] == "CEW_EWS4_OA_RESULT_REVIEW_CONTROLLER", "EWS-4 contract id drift")
    require(ews4["status"] == "EWS4_OA_SUBSET_COMPLETE_PASS", "EWS-4 OA subset is not frozen COMPLETE_PASS")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", ews4["validated_runtime_sha"])), "validated runtime SHA invalid")
    require(ews4["authority_effect"] == "NONE", "review UI cannot create authority")
    require(ews4["canonical_write_authorized"] is False, "canonical write drift")
    require(ews4["project_material_ready"] is False, "project material release drift")
    require(ews4["scope"]["task"] == PILOT, "pilot scope drift")
    require(ews4["hierarchy"] == ["SUMMARY", "REVIEW_SET", "ACTIVE_CANDIDATE"], "review hierarchy drift")
    require(ews4["review_set"]["progressive_paging_required"] is True, "progressive paging missing")
    require(ews4["review_set"]["page_size"] <= 12, "review page size too large")
    require(ews4["review_set"]["full_expanded_cluster_forbidden"] is True, "expanded cluster regression allowed")
    require(ews4["review_set"]["single_active_candidate"] is True, "single active candidate weakened")
    require(ews4["review_set"]["previous_next_required"] is True, "candidate navigation missing")
    require(ews4["active_candidate"]["score_is_authority"] is False, "score authority drift")
    require(ews4["active_candidate"]["source_spatial_focus_when_unregistered"] == "FORBIDDEN", "source position invention risk")

    persistence = ews4["decision_persistence"]
    require(persistence["owner"] == "OA4_HUMAN_CLUSTER_REVIEW", "OA-4 persistence ownership drift")
    require(persistence["ews4_persists_directly"] is False, "EWS-4 must not duplicate persistence")
    require(persistence["explicit_single_candidate_selection"] is True, "explicit candidate selection required")
    require(persistence["implicit_cluster_acceptance"] is False, "implicit cluster acceptance forbidden")
    require(persistence["append_only_receipt_required"] is True, "append-only receipt weakened")

    for marker in [
        "CEW_EWS4_OA_RESULT_REVIEW_CONTROLLER",
        "const PAGE_SIZE=8",
        "ews4-summary-grid",
        "ews4-set",
        "ews4-active",
        "ews4PrevCandidate",
        "ews4NextCandidate",
        "oaLoadReview",
        "oaSaveReview",
        "CONFIRM_AS_FAMILY_CANDIDATE",
        "MARK_AMBIGUOUS",
        "DEFER_NEEDS_SOURCE",
        "Posizione sulla tavola non registrata",
        "Il punteggio è supporto alla revisione, non autorità",
    ]:
        require(marker in runtime, f"runtime invariant missing: {marker}")

    require("import cew_ews4_oa_result_review_runtime as ews4_runtime" in ews1_runtime, "EWS-4 compositor import missing")
    require("import cew_enterprise_governed_resume_runtime as resume_runtime" in ews1_runtime, "governed resume compositor import missing")
    require("resume_runtime.augment(ews4_runtime.augment(rendered, task), task)" in ews1_runtime, "EWS-4 must precede governed resume")
    require("fetch('/api/workbench/object-acquisition/receipt'" not in runtime, "EWS-4 duplicated OA persistence HTTP logic")
    require("load.click()" in runtime and "save.click()" in runtime, "EWS-4 must delegate to OA-4 runtime controls")

    html = oa1_runtime.augment(client.build_client(PILOT), PILOT)
    require("CEW_EWS1_VIEWPORT_BOUND_APPLICATION_FRAME" in html, "EWS-1 frame missing from final pilot")
    require("CEW_EWS4_OA_RESULT_REVIEW_CONTROLLER" in html, "EWS-4 review controller missing from final pilot")
    require("CEW_ENTERPRISE_GOVERNED_CONTEXT_RESUME" in html, "governed resume missing downstream of EWS-4")
    require('data-ews4-runtime="CEW_EWS4_OA_RESULT_REVIEW_CONTROLLER"' in html, "EWS-4 marker not emitted")
    require("body.ews4-oa-review #oaClusterReview{display:none!important}" in html, "legacy expanded OA-4 UI not contained")
    require("PAGE_SIZE=8" in html, "bounded review page not rendered")
    require("un solo candidato primario" in html, "active candidate model not rendered")
    require("Nessuna conferma implicita del cluster" in html, "implicit-cluster warning missing")
    require("data-canonical-write-authorized=\"false\"" in html, "canonical write boundary lost")

    forbidden = set(ews4["forbidden_shortcuts"])
    for name in {
        "FULL_EXPANDED_CLUSTER_AS_PRIMARY_UI",
        "SCORE_CREATES_ACCEPTANCE",
        "AUTO_CONFIRM_CLUSTER",
        "INVENT_SOURCE_POSITION_FOR_ACTIVE_CANDIDATE",
        "DUPLICATE_OA4_PERSISTENCE_LOGIC",
        "OA_G5_RELEASE",
        "OA_6_RELEASE",
        "CANONICAL_WRITE_FROM_REVIEW_UI",
    }:
        require(name in forbidden, f"forbidden shortcut missing: {name}")

    print("CEW_EWS4_OA_RESULT_REVIEW = PASS")
    print("STATUS = EWS4_OA_SUBSET_COMPLETE_PASS")
    print("VALIDATED_RUNTIME_SHA = " + ews4["validated_runtime_sha"])
    print("HIERARCHY = SUMMARY -> REVIEW_SET -> ACTIVE_CANDIDATE")
    print("PAGE_SIZE = 8")
    print("SINGLE_ACTIVE_CANDIDATE = true")
    print("OA4_PERSISTENCE_OWNER = preserved")
    print("GOVERNED_RESUME_DOWNSTREAM = true")
    print("IMPLICIT_CLUSTER_ACCEPTANCE = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("PROJECT_MATERIAL_READY = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
