#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_document_drawing_workspace as workspace
import cew_source_evidence_workspace as source_workspace

METRICS = ROOT / "automation/CEW_USABILITY_METRICS_MODEL_v1.json"
PLAN = ROOT / "automation/CEW_B1_DOCUMENT_DRAWING_AGENT_PLAN_v1.json"
HUMAN_ACCEPTANCE = ROOT / "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json"
CONTRACT = ROOT / "docs/PRODUCT/CEW_DOCUMENT_DRAWING_WORKSPACE_V1_CONTRACT.md"
CODE_MODEL = ROOT / "docs/PROGRAM/CEW_CODE_DEVELOPMENT_MODEL_v2.md"
HUMAN_MODEL = ROOT / "docs/PROGRAM/CEW_HUMAN_CENTRED_GOVUK_MODEL_v2.md"
TERMINOLOGY = ROOT / "automation/CEW_TERMINOLOGY_LAYER_v1.json"
APP = ROOT / "app.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(errors: list[str]) -> int:
    print("CEW_DOCUMENT_DRAWING_FOUNDATION = FAIL")
    for error in errors:
        print(f"ERROR: {error}")
    return 1


def main() -> int:
    errors: list[str] = []
    required = [METRICS, PLAN, HUMAN_ACCEPTANCE, CONTRACT, CODE_MODEL, HUMAN_MODEL, TERMINOLOGY, APP]
    for path in required:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return fail(errors)

    metrics = load_json(METRICS)
    plan = load_json(PLAN)
    human_acceptance = load_json(HUMAN_ACCEPTANCE)
    terminology = load_json(TERMINOLOGY)
    inventory = workspace.inventory()

    source_rows = source_workspace.maps()["sources"]
    if len(inventory) != len(source_rows):
        errors.append(f"inventory/source register count mismatch {len(inventory)} != {len(source_rows)}")
    if len(inventory) < 18:
        errors.append(f"expected at least the current 18 registered original drawings, got {len(inventory)}")
    tav05 = next((x for x in inventory if x["source_id"] == "TAV-05A"), None)
    if not tav05:
        errors.append("TAV-05A missing from document/drawing inventory")
    else:
        if tav05["status"] != "DOC_PRIMARY_IMMUTABLE":
            errors.append("TAV-05A must remain primary immutable")
        if tav05["classification"] != "armature_travi":
            errors.append("TAV-05A classification drift")
        if tav05["level"] != "G4":
            errors.append("TAV-05A level drift")
        if tav05["evidence_count"] < 3:
            errors.append("TAV-05A must expose its governed evidence regions")

    nav = {x["id"]: x for x in terminology.get("navigation", [])}
    if nav.get("DOCUMENTS", {}).get("href") != "/documents":
        errors.append("Documenti navigation missing")
    if nav.get("DRAWINGS", {}).get("href") != "/drawings":
        errors.append("Tavole navigation missing")
    app_text = APP.read_text(encoding="utf-8")
    for marker in [
        'import cew_document_drawing_workspace as document_workspace',
        '@app.get("/documents"',
        '@app.get("/drawings"',
        '@app.get("/drawings/{source_id}"',
        '"document_workspace": "B11_AVAILABLE"',
    ]:
        if marker not in app_text:
            errors.append(f"runtime integration missing marker: {marker}")

    documents_html = workspace.build_document_library()
    drawings_html = workspace.build_drawing_register()
    drawing_html = workspace.build_drawing_card("TAV-05A")
    combined_user_surface = (documents_html + drawing_html).lower()

    # UX-DOC-01: semantic concepts, not brittle wording.
    required_concepts = {
        "Documenti del progetto": "documenti del progetto",
        "TAV-05A": "tav-05a",
        "reinforcement classification": "armatur",
        "primary source": "fonte primaria",
        "SHA-256": "sha-256",
    }
    for label, token in required_concepts.items():
        if token not in combined_user_surface:
            errors.append(f"UX-DOC-01 surface missing user-visible concept: {label}")

    for text in ["Tavole di progetto", "TAV-05A", "G4", "Apri"]:
        if text.lower() not in drawings_html.lower():
            errors.append(f"drawing register missing user-visible concept: {text}")
    if "ausili derivati" not in drawing_html.lower() or "pdf verificato" not in drawing_html.lower():
        errors.append("UX-DOC-04 cannot distinguish primary PDF from derived reading aids")
    if "non ancora modellata" not in drawing_html.lower():
        errors.append("DocumentMap missing state must remain explicit")

    task_ids = {x["task_id"] for x in metrics.get("initial_cew_b11_tasks", [])}
    if task_ids != {"UX-DOC-01", "UX-DOC-02", "UX-DOC-03", "UX-DOC-04"}:
        errors.append(f"usability task set drift: {sorted(task_ids)}")

    # The foundation validator must validate the foundation without pretending
    # it is still the active orchestration slice. B1.1/B1.2 are prepared but
    # explicitly non-promoted; B1.8 owns the current human-acceptance work.
    slices = {x["id"]: x for x in plan.get("slices", [])}
    if slices.get("B1.1", {}).get("state") != "PREPARED_BLOCKED_PROMOTION":
        errors.append("B1.1 must remain technically prepared and blocked from promotion")
    if slices.get("B1.2", {}).get("state") != "PREPARED_BLOCKED_PROMOTION":
        errors.append("B1.2 viewer must remain technically prepared and blocked from promotion")
    if slices.get("B1.8", {}).get("state") != "IN_PROGRESS_DESIGN_REQUIRED":
        errors.append("B1.8 Human Acceptance v2 must be the current B1 human slice")
    if slices.get("B1.8", {}).get("contract") != "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json":
        errors.append("B1.8 must bind the current Human Acceptance v2 contract")
    if "HVA_GATE" not in slices.get("B1.1", {}).get("gates", []):
        errors.append("B1.1 integrated promotion must still require Human/Visual Acceptance")
    if "HVA_GATE" not in slices.get("B1.8", {}).get("gates", []):
        errors.append("B1.8 must require HVA_GATE")
    if human_acceptance.get("production_promotion_authorized") is not False:
        errors.append("Human Acceptance v2 design must not authorize Production promotion before execution")

    forbidden = ["documenti completi", "progetto completo", "modello completo"]
    combined = (documents_html + drawings_html + drawing_html).lower()
    for phrase in forbidden:
        if phrase in combined:
            errors.append(f"false completion wording detected: {phrase}")
    if not any(token in documents_html.lower() for token in ["non li inventa", "non inventa", "non vengono inventati"]):
        errors.append("catalogue gap honesty missing")

    if errors:
        return fail(errors)

    print("CEW_DOCUMENT_DRAWING_FOUNDATION = PASS")
    print(f"REGISTERED_DOCUMENTS = {len(inventory)}")
    print(f"TAV05A_EVIDENCE_REGIONS = {tav05['evidence_count'] if tav05 else 0}")
    print("UX_DOC_01 = AUTOMATED_FIXTURE_PASS")
    print("UX_DOC_04 = AUTOMATED_FIXTURE_PASS")
    print("B1_1_STATE = PREPARED_BLOCKED_PROMOTION")
    print("B1_2_STATE = PREPARED_BLOCKED_PROMOTION")
    print("B1_8_STATE = IN_PROGRESS_DESIGN_REQUIRED")
    print("HVA_V2 = REQUIRED_NOT_SATISFIED")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
