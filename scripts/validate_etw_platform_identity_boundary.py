#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import etw_cew_source_inventory_adapter as inventory_adapter
import etw_scope_context as scope_runtime

BASELINE = ROOT / "automation/ETW_CEW_CONTRACT_BASELINE_v1.json"
SCOPE_MODEL = ROOT / "automation/ETW_PLATFORM_SCOPE_MODEL_v1.json"
USABILITY = ROOT / "automation/ETW_A0_USABILITY_TASKS_v1.json"
IDENTITY_CONTRACT = ROOT / "docs/ARCHITECTURE/ETW_PLATFORM_IDENTITY_BOUNDARY_v1.md"
WORK_PACKAGE = ROOT / "automation/ETW_A0_WORK_PACKAGE_v1.json"
QUEUE = ROOT / "automation/ETW_DEVELOPMENT_QUEUE_v1.json"
PREP_RECEIPT = ROOT / "automation/receipts/etw-platform/ETW-A0-PREP-PASS_v1.json"
SOURCE_REGISTRY = ROOT / "data/canonical/tavole_originali_remote_index_v1.csv"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(errors: list[str]) -> int:
    print("ETW_PLATFORM_IDENTITY_PREP = FAIL")
    for error in errors:
        print(f"ERROR: {error}")
    return 1


def main() -> int:
    errors: list[str] = []
    for path in [BASELINE, SCOPE_MODEL, USABILITY, IDENTITY_CONTRACT, WORK_PACKAGE, QUEUE, SOURCE_REGISTRY]:
        if not path.exists():
            errors.append(f"missing A0 artifact: {path.relative_to(ROOT)}")
    if errors:
        return fail(errors)

    baseline = load_json(BASELINE)
    model = load_json(SCOPE_MODEL)
    usability = load_json(USABILITY)
    queue = load_json(QUEUE)

    # W0 / DATA_GATE — frozen contract files still match their recorded content identities.
    for contract in baseline.get("contracts", []):
        path = ROOT / contract["path"]
        if not path.exists():
            errors.append(f"frozen contract missing: {contract['path']}")
            continue
        actual = git_blob_sha(path)
        if actual != contract["blob_sha"]:
            errors.append(f"frozen contract drift: {contract['id']} {actual} != {contract['blob_sha']}")
    if baseline.get("cew_contract_baseline", {}).get("promoted") is not False:
        errors.append("A0 preparation baseline must not be represented as promoted")
    if baseline.get("promotion_boundary", {}).get("a0_complete_allowed") is not False:
        errors.append("A0 complete must remain blocked during preparation")

    # W1 / DATA_GATE — exact platform identity states.
    scopes = {
        (row["project_id"], row["discipline_id"]): row
        for row in model.get("project_discipline_scopes", [])
    }
    expected_states = {
        ("N12", "STRUCTURES"): ("ACTIVE", "CEW_BOUND"),
        ("N12", "ARCHITECTURE"): ("NOT_YET_RELEASED", "DOMAIN_CONTRACT_NOT_YET_RELEASED"),
        ("TEST_PROJECT", "STRUCTURES"): ("TEST_ONLY", "TEST_ONLY"),
    }
    for key, expected in expected_states.items():
        row = scopes.get(key)
        if not row:
            errors.append(f"missing declared scope {key}")
            continue
        if (row.get("scope_state"), row.get("module_state")) != expected:
            errors.append(f"scope state drift {key}: {(row.get('scope_state'), row.get('module_state'))} != {expected}")
    if ("TEST_PROJECT", "ARCHITECTURE") in scopes:
        errors.append("A0 must not silently declare TEST_PROJECT/ARCHITECTURE")
    if model.get("scope_context_schema", {}).get("implicit_n12_fallback") is not False:
        errors.append("implicit N12 fallback must be false")
    if model.get("scope_context_schema", {}).get("default_project") is not None:
        errors.append("A0 must not define a default project")

    # W2 / DATA + AUTHORITY — source inventory is derived, read-only and does not create domain truth.
    source_hash_before = file_sha256(SOURCE_REGISTRY)
    adapter_errors = inventory_adapter.validate_adapter()
    errors.extend(f"inventory adapter: {error}" for error in adapter_errors)
    architecture = inventory_adapter.scope_inventory_projection("N12", "ARCHITECTURE")
    source_hash_after = file_sha256(SOURCE_REGISTRY)
    if source_hash_before != source_hash_after:
        errors.append("source registry changed while running read-only adapter")
    registry_rows = inventory_adapter.load_source_registry()
    expected_arch = {row["id"] for row in registry_rows if row.get("classe") == "architettonica"}
    actual_arch = {row["source_id"] for row in architecture.get("sources", [])}
    if actual_arch != expected_arch:
        errors.append("Architecture inventory is not an exact projection of classe=architettonica")
    if architecture.get("domain_contract_released") is not False:
        errors.append("Architecture domain must remain not released")
    if architecture.get("domain_entity_count") != 0 or architecture.get("domain_property_count") != 0:
        errors.append("source availability was incorrectly promoted to Architecture domain content")
    if architecture.get("project_source_binding_created") is not False:
        errors.append("A0 adapter must not create project/source binding")

    # W3 / INTEGRATION + SECURITY — context is part of every runtime isolation primitive.
    runtime_errors = scope_runtime.validate_scope_runtime()
    errors.extend(f"scope runtime: {error}" for error in runtime_errors)

    n12s = scope_runtime.resolve_scope_context("N12", "STRUCTURES")
    n12a = scope_runtime.resolve_scope_context("N12", "ARCHITECTURE")
    test = scope_runtime.resolve_scope_context("TEST_PROJECT", "STRUCTURES")
    if scope_runtime.scoped_cache_key("x", n12s, "1") == scope_runtime.scoped_cache_key("x", test, "1"):
        errors.append("SECURITY: cache collision across projects")
    if scope_runtime.scoped_cache_key("x", n12s, "1") == scope_runtime.scoped_cache_key("x", n12a, "1"):
        errors.append("SECURITY: cache collision across disciplines")
    token = scope_runtime.issue_async_token(n12s, "r1")
    if scope_runtime.async_response_matches(token, test, "r1"):
        errors.append("SECURITY: old N12 async response accepted in TEST_PROJECT")
    if scope_runtime.async_response_matches(token, n12a, "r1"):
        errors.append("SECURITY: old Structures async response accepted in Architecture")
    test_projection = inventory_adapter.scope_inventory_projection("TEST_PROJECT", "STRUCTURES")
    if test_projection.get("source_count") != 0 or test_projection.get("engineering_data_present") is not False:
        errors.append("SECURITY: TEST_PROJECT contains N12 engineering data")

    # Authority audit — A0 must not introduce downstream domain/binding contracts.
    forbidden_paths = [
        ROOT / "automation/ETW_PROJECT_SOURCE_BINDING_SCHEMA_v1.json",
        ROOT / "automation/ETW_CROSS_DISCIPLINE_RELATION_SCHEMA_v1.json",
        ROOT / "automation/ETW_ARCHITECTURAL_ENTITY_ADMISSION_v1.json",
        ROOT / "automation/ETW_PROPERTY_ASSERTION_SCHEMA_v1.json",
    ]
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"AUTHORITY: downstream object introduced in A0: {path.relative_to(ROOT)}")

    # W6 / HUMAN FACTORS prep — tasks and safety metrics exist, but HVA is not claimed.
    if usability.get("state") != "PREPARED_FOR_HVA_NOT_EXECUTED":
        errors.append("Human Factors artifact must not claim executed HVA")
    task_ids = {task.get("task_id") for task in usability.get("tasks", [])}
    if task_ids != {"ETW-A0-UX-01", "ETW-A0-UX-02", "ETW-A0-UX-03", "ETW-A0-UX-04"}:
        errors.append(f"A0 usability task set drift: {sorted(task_ids)}")
    non_compensable = set(usability.get("non_compensable_failures", []))
    for metric in ["cross_project_leakage", "cross_discipline_leakage", "cross_discipline_false_equivalence"]:
        if metric not in non_compensable:
            errors.append(f"Human Factors missing non-compensable safety metric {metric}")

    # Orchestrator boundary — supports both pre-ingest and persisted PREP_PASS states.
    by_id = {item["id"]: item for item in queue.get("items", [])}
    a0 = by_id.get("ETW-A0", {})
    a1 = by_id.get("ETW-A1", {})
    status_raw = subprocess.check_output([sys.executable, "scripts/etw_orchestrator.py", "status"], cwd=ROOT, text=True)
    status = json.loads(status_raw)
    a0_state = a0.get("state")

    if a0_state == "PREP_ONLY":
        selected = status.get("selected_work_item") or {}
        if selected.get("id") != "ETW-A0" or status.get("selection_reason") != "PREP_ONLY":
            errors.append("orchestrator is not selecting ETW-A0 PREP_ONLY")
        if "CEW_PROMOTED_BASELINE" not in status.get("promotion_blockers", []):
            errors.append("orchestrator lost CEW promoted baseline blocker")
    elif a0_state == "PREPARED_BLOCKED_PROMOTION":
        if not PREP_RECEIPT.exists():
            errors.append("persisted A0 PREP_PASS state is missing its receipt")
        if a0.get("preparation_decision") != "PREP_PASS":
            errors.append("persisted A0 state is missing PREP_PASS decision")
        if "CEW_PROMOTED_BASELINE" not in a0.get("promotion_blockers", []):
            errors.append("persisted A0 state lost CEW promoted baseline blocker")
        if a1.get("state") != "WAITING":
            errors.append("ETW-A1 was released before A0 promotion")
        if status.get("decision") != "BLOCKED_DEPENDENCY" or status.get("selected_work_item") is not None:
            errors.append("orchestrator should stop with no selected item after persisted A0 PREP_PASS")
    else:
        errors.append(f"unexpected ETW-A0 preparation state: {a0_state}")

    if errors:
        return fail(errors)

    print("ETW_PLATFORM_IDENTITY_PREP = PASS")
    print("DATA_GATE = PASS")
    print("INTEGRATION_GATE = PASS")
    print("SECURITY_GATE = PASS")
    print("AUTHORITY_AUDIT = PASS")
    print("QA_GATE = PASS")
    print(f"ARCHITECTURE_SOURCE_COUNT = {architecture.get('source_count')}")
    print("ARCHITECTURE_DOMAIN_ENTITY_COUNT = 0")
    print("TEST_PROJECT_SOURCE_COUNT = 0")
    print("CROSS_PROJECT_LEAKAGE = false")
    print("CROSS_DISCIPLINE_LEAKAGE = false")
    print(f"PERSISTED_A0_STATE = {a0_state}")
    print("HUMAN_FACTORS_GATE = PREPARED_NOT_EXECUTED")
    print("HVA_GATE = NOT_SATISFIED")
    print("PRODUCTION_SMOKE = NOT_SATISFIED")
    print("CEW_PROMOTED_BASELINE = NOT_SATISFIED")
    print("MAX_ALLOWED_OWNER_DECISION = PREP_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
