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

import cew_project_home as project_home

STATE = ROOT / "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"
ISSUES = ROOT / "data/canonical/N12_ISSUES_CURRENT_v1.json"
TASKS = ROOT / "data/canonical/CEW_ERW_RESOLUTION_TASKS_v1.csv"
TERMINOLOGY = ROOT / "automation/CEW_TERMINOLOGY_LAYER_v1.json"
LIFECYCLE = ROOT / "automation/CEW_PROJECT_LIFECYCLE_MODEL_v1.json"
CONTRACT = ROOT / "docs/PRODUCT/CEW_PROJECT_HOME_V2_CONTRACT_v1.md"
APP = ROOT / "app.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_rows(path: Path) -> list[dict]:
    import csv
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def visible_text(page: str) -> str:
    without_style = re.sub(r"<style\b[^>]*>.*?</style>", " ", page, flags=re.I | re.S)
    without_script = re.sub(r"<script\b[^>]*>.*?</script>", " ", without_style, flags=re.I | re.S)
    return re.sub(r"<[^>]+>", " ", without_script)


def main() -> int:
    errors: list[str] = []
    for path in [STATE, ISSUES, TASKS, TERMINOLOGY, LIFECYCLE, CONTRACT, APP]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    state = load_json(STATE)
    issues = load_json(ISSUES)
    tasks = csv_rows(TASKS)
    terminology = load_json(TERMINOLOGY)
    lifecycle = load_json(LIFECYCLE)
    contract = CONTRACT.read_text(encoding="utf-8")
    app_text = APP.read_text(encoding="utf-8")
    page = project_home.build_project_home(state, issues, tasks, terminology, lifecycle)
    visible = visible_text(page)

    if terminology.get("audience") != "STRUCTURAL_ENGINEER":
        errors.append("terminology audience must be STRUCTURAL_ENGINEER")
    rules = terminology.get("rules", {})
    if rules.get("internal_ids_primary_navigation") is not False:
        errors.append("internal IDs must not be primary navigation")
    if rules.get("internal_ids_available_in_technical_detail") is not True:
        errors.append("technical provenance/detail access must remain available")
    if rules.get("human_authority_must_remain_explicit") is not True:
        errors.append("human authority rule missing")

    required_headings = ["Progetto N12", "Stato del lavoro", "Cosa richiede attenzione", "Percorso di valutazione", "Accessi di lavoro", "Autorità professionale"]
    for text in required_headings:
        if text not in page:
            errors.append(f"HF-HOME-01 missing visible orientation text: {text}")

    if "Rivedi evidenza" not in page or "/review/f7?task=" not in page:
        errors.append("HF-HOME-02 evidence-review action missing")
    if "Dettagli tecnici e audit" not in page or "/technical/control-room" not in page:
        errors.append("HF-HOME-06 technical detail route missing")

    if state.get("engineering_state", {}).get("calculation_model_ready") is False:
        if "Modello di calcolo non ancora autorizzabile" not in page:
            errors.append("HF-HOME-04 incomplete calculation state not visible")

    authority_markers = [
        "Le decisioni professionali restano dell’ingegnere responsabile",
        "non modifica automaticamente i dati ingegneristici approvati",
    ]
    for marker in authority_markers:
        if marker not in page:
            errors.append(f"HF-HOME-03 authority marker missing: {marker}")

    for pid in [f"P{i}" for i in range(17)]:
        if f'>{pid}<' not in page:
            errors.append(f"HF-HOME-05 lifecycle phase not visible: {pid}")
    if re.search(r"\b\d{1,3}\s*%", visible) or "percent complete" in visible.lower() or "percentuale di completamento" in visible.lower() or "<progress" in page.lower():
        errors.append("HF-HOME-05 false percentage/progress representation detected")
    if "non sostituisce i gate ingegneristici" not in page:
        errors.append("HF-HOME-05 engineering readiness distinction missing")

    headings = "\n".join(re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", page, re.I | re.S))
    for prefix in ["ERW-", "M1E-", "F7"]:
        if prefix in headings:
            errors.append(f"internal identifier leaked into primary heading: {prefix}")

    if "def project_home_route" not in app_text or "build_project_home" not in app_text:
        errors.append("Project Home is not integrated as runtime home")
    if '@app.get("/technical/control-room"' not in app_text:
        errors.append("legacy technical Control Room secondary route missing")
    if '"service": "CEW_USER_RUNTIME"' not in app_text:
        errors.append("runtime service identity not reconciled")

    required_contract_fixtures = ["HF-HOME-01", "HF-HOME-02", "HF-HOME-03", "HF-HOME-04", "HF-HOME-05", "HF-HOME-06"]
    for fixture in required_contract_fixtures:
        if fixture not in contract:
            errors.append(f"human-factors fixture missing from contract: {fixture}")

    current = state.get("current_product_work_item", {})
    if current.get("id") != "CEW-A2-PROJECT-HOME-HUMAN-FACTORS":
        errors.append("A2 must be current while human-factors gate is being established")

    if errors:
        print("CEW_HUMAN_FACTORS_PROJECT_HOME = FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("CEW_HUMAN_FACTORS_PROJECT_HOME = PASS")
    print("HF_HOME_01_ORIENTATION = PASS")
    print("HF_HOME_02_ACTION_CLARITY = PASS")
    print("HF_HOME_03_AUTHORITY_CLARITY = PASS")
    print("HF_HOME_04_INCOMPLETE_STATE_VISIBILITY = PASS")
    print("HF_HOME_05_LIFECYCLE_NO_FALSE_PROGRESS = PASS")
    print("HF_HOME_06_TECHNICAL_DETAIL_REACHABLE = PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
