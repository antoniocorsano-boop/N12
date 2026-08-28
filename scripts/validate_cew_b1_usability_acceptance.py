#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_b1_acceptance_lab as lab
import cew_source_evidence_workspace as source_workspace

CONTRACT = ROOT / "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json"
IMPLEMENTATION = ROOT / "scripts/cew_b1_human_acceptance_v2.py"
APP = ROOT / "app.py"
PLAN = ROOT / "docs/ACCEPTANCE/CEW_B1_HUMAN_ACCEPTANCE_V2_PLAN.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    for path in [CONTRACT, IMPLEMENTATION, APP, PLAN, ROOT / "scripts/cew_b1_acceptance_lab.py"]:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1

    contract = load(CONTRACT)
    implementation = IMPLEMENTATION.read_text(encoding="utf-8")
    app_text = APP.read_text(encoding="utf-8")
    html = lab.build_lab()
    evidence_html = source_workspace.build_evidence_workspace("ERW-N12-001")

    expected = ["UX-DOC-01", "UX-DOC-02", "UX-DOC-03", "UX-DOC-04"]
    tasks = lab.task_specs()
    task_ids = [row["task_id"] for row in tasks]
    if task_ids != expected:
        errors.append(f"B1.8 task sequence drift: {task_ids}")

    if contract.get("status") != "IMPLEMENTED_CANDIDATE_HVA_PENDING":
        errors.append("B1.8 contract must remain IMPLEMENTED_CANDIDATE_HVA_PENDING before real HVA")
    if contract.get("human_hva_state") != "REQUIRED_NOT_SATISFIED":
        errors.append("human HVA must remain unsatisfied in implementation tranche")
    if contract.get("accessibility_gate_state") != "REQUIRED_NOT_SATISFIED":
        errors.append("manual accessibility gate must remain unsatisfied")
    if contract.get("production_promotion_authorized") is not False:
        errors.append("B1.8 implementation must not authorize Production promotion")
    if contract.get("canonical_write_authorized") is not False:
        errors.append("B1.8 must not authorize canonical writes")
    if contract.get("engineering_authority_effect") != "NONE":
        errors.append("B1.8 HVA must have no engineering authority effect")

    implementation_contract = contract.get("implementation", {})
    if implementation_contract.get("route") != "/acceptance/b1":
        errors.append("participant route drift")
    if implementation_contract.get("reviewer_mode") != "#review":
        errors.append("reviewer mode must remain separate at #review")
    if implementation_contract.get("server_persistence") is not False:
        errors.append("B1.8 acceptance evidence must not silently persist server-side")

    layers = contract.get("layers", {})
    participant = layers.get("participant_surface", {})
    for key in [
        "show_internal_task_ids",
        "show_runtime_sha",
        "show_gate_state",
        "show_live_test_counters",
        "show_release_decision",
        "show_receipt_export",
    ]:
        if participant.get(key) is not False:
            errors.append(f"participant surface must keep {key}=false")
    if participant.get("one_dominant_task_at_a_time") is not True:
        errors.append("participant must receive one dominant task at a time")
    if participant.get("professional_language_first") is not True:
        errors.append("participant surface must use professional language first")

    observation = layers.get("observation_layer", {})
    if observation.get("visible_to_participant_by_default") is not False:
        errors.append("telemetry must remain invisible by default")
    for metric in [
        "time_on_task_seconds",
        "interaction_count",
        "help_requests",
        "backtracks_or_recovery_actions",
        "navigation_revisit_count",
        "navigation_path",
        "viewer_states",
        "source_scale_states",
        "task_outcome",
    ]:
        if metric not in observation.get("metrics", []):
            errors.append(f"missing B1.8 observation metric: {metric}")
    for automatic in [
        "correct_drawing_reached",
        "viewer_rotation_observed_and_reset",
        "evidence_zoom_and_pan_observed",
        "evidence_macro_context_observed_and_returned_to_micro",
    ]:
        if automatic not in observation.get("automatic_observations", []):
            errors.append(f"missing B1.8 automatic observation: {automatic}")

    reviewer = layers.get("reviewer_surface", {})
    if reviewer.get("separate_from_participant_surface") is not True:
        errors.append("reviewer must remain separate from participant")
    if reviewer.get("owns_hva_decision") is not True:
        errors.append("reviewer must own HVA decision")

    receipt = layers.get("receipt_layer", {})
    if receipt.get("generated_after_reviewer_decision") is not True:
        errors.append("receipt may be generated only after reviewer decision")
    if receipt.get("revision_bound") is not True:
        errors.append("receipt must remain revision-bound")
    if receipt.get("production_smoke_required") is not True:
        errors.append("same-revision Production smoke must remain required")
    if receipt.get("promotion_authorized") is not False:
        errors.append("receipt layer must not auto-promote B1")

    by_id = {row["task_id"]: row for row in contract.get("tasks", [])}
    expected_starts = {
        "UX-DOC-01": "/",
        "UX-DOC-02": "/drawings/TAV-05A",
        "UX-DOC-03": "/evidence/review?task=ERW-N12-001",
        "UX-DOC-04": "/drawings/TAV-05A",
    }
    for task_id, start_path in expected_starts.items():
        if by_id.get(task_id, {}).get("start_path") != start_path:
            errors.append(f"{task_id} start path drift")
    if by_id.get("UX-DOC-01", {}).get("automatic_success_signal") != "FINAL_NAVIGATION_PATH_/drawings/TAV-05A":
        errors.append("UX-DOC-01 must require the correct drawing as final context")
    if by_id.get("UX-DOC-02", {}).get("accepted_mental_model") != "DISPLAY_VIEW_ONLY":
        errors.append("UX-DOC-02 must test viewer-only mental model")
    if by_id.get("UX-DOC-03", {}).get("automatic_success_signal") != "EVIDENCE_ZOOM_PAN_OBSERVED_AND_SOURCE_SCALE_MACRO_OBSERVED_AND_FINAL_STATE_MICRO":
        errors.append("UX-DOC-03 must require real zoom/pan inspection plus MICRO/MACRO round-trip")
    if "Ingrandisci il dettaglio e spostati" not in by_id.get("UX-DOC-03", {}).get("participant_prompt_it", ""):
        errors.append("UX-DOC-03 participant prompt must exercise evidence inspection naturally")
    if by_id.get("UX-DOC-03", {}).get("accepted_mental_model") != "ROUND_TRIP_UNDERSTOOD":
        errors.append("UX-DOC-03 must test evidence/source-context round-trip comprehension")
    if by_id.get("UX-DOC-04", {}).get("accepted_mental_model") != "PRIMARY_PDF":
        errors.append("UX-DOC-04 must preserve primary-PDF authority")

    try:
        participant_source = implementation.split("function renderParticipant()", 1)[1].split("function startTask()", 1)[0]
        reviewer_source = implementation.split("function renderReviewer()", 1)[1].split("function exportReceipt", 1)[0]
    except IndexError:
        participant_source = ""
        reviewer_source = ""
        errors.append("participant/reviewer functions not structurally separable")

    for forbidden in ["Revisione runtime", "Decisione HVA", "Esporta receipt", "Tempo:", "Interazioni:", "PASS_FOR_B1"]:
        if forbidden in participant_source:
            errors.append(f"participant UI exposes internal/reviewer concept: {forbidden}")
    for required in ["Attività ${i+1} di ${TASKS.length}", "Svolgi il lavoro come faresti normalmente", "Mostra un suggerimento"]:
        if required not in html:
            errors.append(f"participant experience missing marker: {required}")
    for required in ["AREA REVISIONE HVA", "Decisione HVA", "Esporta receipt HVA", "Accessibilità manuale:"]:
        if required not in reviewer_source:
            errors.append(f"reviewer surface missing marker: {required}")

    for marker in [
        "/drawings/TAV-05A",
        "/evidence/review?task=ERW-N12-001",
        "Viewer (90|180|270)°",
        "recordSourceScaleState",
        "startsWith('MACRO')",
        "startsWith('MICRO')",
        "DISPLAY_VIEW_ONLY",
        "ROUND_TRIP_UNDERSTOOD",
        "PRIMARY_PDF",
        "FALSE_SUCCESS",
        "PRIMARY_DERIVED_AUTHORITY_CONFUSION",
        "PROVENANCE_BREAK",
        "VIEWER_STATE_MISREAD_AS_SOURCE_MUTATION",
    ]:
        if marker not in implementation:
            errors.append(f"B1.8 implementation missing critical marker: {marker}")

    for hardened_marker in [
        "Evidenza · Zoom ",
        "Pan usato",
    ]:
        if hardened_marker not in evidence_html:
            errors.append(f"B1.8 evidence surface missing inspection marker: {hardened_marker}")
    if "zoomed&&panned&&macro&&finalMicro" not in html:
        errors.append("B1.8 hardened participant logic missing zoom/pan outcome rule")

    if "fetch('/api" in implementation or 'fetch("/api' in implementation:
        errors.append("B1.8 acceptance layer must not submit receipts to runtime APIs")
    for marker in [
        "receipt_type:'CEW_B1_HUMAN_ACCEPTANCE_V2'",
        "accessibility_gate_state:'REQUIRED_NOT_SATISFIED'",
        "production_smoke_required:true",
        "production_smoke_state:'REQUIRED_NOT_SATISFIED'",
        "slice_complete:false",
        "promotion_authorized:false",
        "canonical_write_authorized:false",
        "engineering_authority_effect:'NONE'",
    ]:
        if marker not in implementation:
            errors.append(f"receipt boundary missing marker: {marker}")

    for marker in [
        "import cew_b1_acceptance_lab as acceptance_lab",
        '@app.get("/acceptance/b1"',
        '"b1_acceptance_lab": "B18_IMPLEMENTED_CANDIDATE_HVA_PENDING"',
    ]:
        if marker not in app_text:
            errors.append(f"runtime marker missing: {marker}")

    if errors:
        print("CEW_B1_HUMAN_ACCEPTANCE_V2 = FAIL")
        for error in errors:
            print("ERROR:", error)
        return 1

    print("CEW_B1_HUMAN_ACCEPTANCE_V2 = PASS")
    print("PARTICIPANT_REVIEWER_SEPARATION = PASS")
    print("LIVE_TELEMETRY_VISIBLE_TO_PARTICIPANT = false")
    print("AUTOMATIC_FALSE_SUCCESS_SIGNALS = PASS")
    print("EVIDENCE_CONTEXT_OBSERVATION = ZOOM_PAN_MICRO_MACRO_MICRO")
    print("HUMAN_HVA = REQUIRED_NOT_SATISFIED")
    print("ACCESSIBILITY_GATE = REQUIRED_NOT_SATISFIED")
    print("PRODUCTION_SMOKE_AFTER_HVA = REQUIRED")
    print("PRODUCTION_PROMOTION_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
