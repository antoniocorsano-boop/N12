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

CONTRACT = ROOT / "automation/CEW_B1_USABILITY_ACCEPTANCE_CONTRACT_v1.json"
METRICS = ROOT / "automation/CEW_USABILITY_METRICS_MODEL_v1.json"
APP = ROOT / "app.py"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def blockers(results: dict[str, dict], task_ids: list[str]) -> list[str]:
    out: list[str] = []
    for task_id in task_ids:
        row = results.get(task_id)
        if not row:
            out.append(f"{task_id}:NOT_OBSERVED")
            continue
        if row.get("result_state") in {"FALSE_SUCCESS", "ABANDONED", "BLOCKED_BY_PRODUCT"}:
            out.append(f"{task_id}:{row['result_state']}")
        if row.get("wrong_source_or_wrong_version_selection"):
            out.append(f"{task_id}:WRONG_SOURCE_OR_VERSION")
        if row.get("authority_boundary_errors"):
            out.append(f"{task_id}:AUTHORITY_ERROR")
        if row.get("canonical_write_misconception"):
            out.append(f"{task_id}:CANONICAL_WRITE_MISCONCEPTION")
    return out


def good_result(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "result_state": "SUCCESS",
        "time_on_task_seconds": 30,
        "interaction_count": 4,
        "help_requests": 0,
        "backtracks_or_recovery_actions": 0,
        "ease_1_to_5": 4,
        "confidence_correct_1_to_5": 5,
        "perceived_time_1_to_5": 4,
        "free_comment": "",
        "wrong_source_or_wrong_version_selection": False,
        "authority_boundary_errors": False,
        "canonical_write_misconception": False,
    }


def main() -> int:
    errors: list[str] = []
    for path in [CONTRACT, METRICS, APP, ROOT / "scripts/cew_b1_acceptance_lab.py"]:
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        for e in errors: print("ERROR:", e)
        return 1

    contract = load(CONTRACT)
    metrics = load(METRICS)
    tasks = lab.task_specs()
    task_ids = [t["task_id"] for t in tasks]
    expected = ["UX-DOC-01", "UX-DOC-02", "UX-DOC-03", "UX-DOC-04"]
    if task_ids != expected:
        errors.append(f"task sequence drift: {task_ids}")
    if contract.get("task_ids") != expected:
        errors.append("contract task_ids drift")
    if contract.get("acceptance_rules", {}).get("human_hva_decision_required") is not True:
        errors.append("human HVA decision must remain mandatory")
    if contract.get("acceptance_rules", {}).get("production_smoke_after_hva_required") is not True:
        errors.append("Production smoke must remain mandatory after HVA")
    authority = contract.get("authority", {})
    for key in [
        "acceptance_lab_is_engineering_authority",
        "receipt_is_canonical_engineering_write",
        "receipt_changes_epistemic_state",
        "receipt_changes_f2_geometry",
        "receipt_creates_structural_binding",
        "canonical_write_authorized",
    ]:
        if authority.get(key) is not False:
            errors.append(f"authority rule must remain false: {key}")

    html = lab.build_lab()
    required_markers = [
        "Acceptance Lab",
        "Documenti → Tavole → Evidenza",
        "iframe",
        "FALSE_SUCCESS",
        "fonte/versione sbagliata",
        "errore di autorità",
        "production_smoke_required:true",
        "slice_complete:false",
        "canonical_write_authorized:false",
        "engineering_authority_effect:'NONE'",
    ]
    for marker in required_markers:
        if marker not in html:
            errors.append(f"lab missing marker: {marker}")
    if "fetch('/api" in html or 'fetch("/api' in html:
        errors.append("Acceptance Lab must not persist or promote receipt through an API in preparation slice")

    app_text = APP.read_text(encoding="utf-8")
    for marker in [
        "import cew_b1_acceptance_lab as acceptance_lab",
        '@app.get("/acceptance/b1"',
        '"b1_acceptance_lab": "B17_PREP_AVAILABLE_NOT_PROMOTED"',
    ]:
        if marker not in app_text:
            errors.append(f"runtime marker missing: {marker}")

    good = {task_id: good_result(task_id) for task_id in expected}
    if blockers(good, expected):
        errors.append("clean representative results unexpectedly blocked")
    false_success = {k: dict(v) for k, v in good.items()}
    false_success["UX-DOC-01"]["result_state"] = "FALSE_SUCCESS"
    if not blockers(false_success, expected):
        errors.append("FALSE_SUCCESS must block acceptance")
    authority_error = {k: dict(v) for k, v in good.items()}
    authority_error["UX-DOC-04"]["authority_boundary_errors"] = True
    if not blockers(authority_error, expected):
        errors.append("authority error must block acceptance")
    wrong_source = {k: dict(v) for k, v in good.items()}
    wrong_source["UX-DOC-01"]["wrong_source_or_wrong_version_selection"] = True
    if not blockers(wrong_source, expected):
        errors.append("wrong source/version must block acceptance")

    result_states = set(metrics.get("task_result_states", []))
    if "FALSE_SUCCESS" not in result_states or "SUCCESS_WITH_HELP" not in result_states:
        errors.append("usability result-state model incomplete")

    if errors:
        print("CEW_B1_USABILITY_ACCEPTANCE = FAIL")
        for error in errors: print("ERROR:", error)
        return 1

    print("CEW_B1_USABILITY_ACCEPTANCE = PASS")
    print("TASKS = UX-DOC-01,UX-DOC-02,UX-DOC-03,UX-DOC-04")
    print("FALSE_SUCCESS = BLOCKING")
    print("AUTHORITY_ERROR = BLOCKING")
    print("WRONG_SOURCE_OR_VERSION = BLOCKING")
    print("HUMAN_HVA_DECISION_REQUIRED = true")
    print("PRODUCTION_SMOKE_AFTER_HVA_REQUIRED = true")
    print("SLICE_COMPLETE = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
