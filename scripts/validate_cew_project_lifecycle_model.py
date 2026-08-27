#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "automation/CEW_PROJECT_LIFECYCLE_MODEL_v1.json"
PHASE_CONTRACT = ROOT / "automation/CEW_HUMAN_CENTRIC_PHASE_CONTRACT_v1.json"
STATE = ROOT / "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"
QUEUE = ROOT / "automation/CEW_PRODUCT_TRANSFORMATION_QUEUE_v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    for path in [MODEL, PHASE_CONTRACT, STATE, QUEUE]:
        if not path.exists():
            errors.append(f"missing required artifact: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    model = load(MODEL)
    contract = load(PHASE_CONTRACT)
    state = load(STATE)
    queue = load(QUEUE)

    if model.get("program_goal") != "CEW-GOAL-01":
        errors.append("lifecycle model must bind CEW-GOAL-01")
    if model.get("source_contract") != "automation/CEW_HUMAN_CENTRIC_PHASE_CONTRACT_v1.json":
        errors.append("lifecycle source contract mismatch")
    if model.get("engineering_state_authority") != "knowledge/CURRENT_STATE.json":
        errors.append("engineering authority must remain knowledge/CURRENT_STATE.json")
    if model.get("product_state_authority") != "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json":
        errors.append("product authority path mismatch")

    required_primitives = {
        "ProjectPhase", "PhaseGate", "PhaseDeliverable", "EngineeringDecision",
        "InformationRequirement", "EngineeringRulePackReference", "WorkPackage"
    }
    primitives = model.get("primitive_schemas", {})
    if set(primitives) != required_primitives:
        errors.append(f"primitive set mismatch: {sorted(set(primitives))}")

    for primitive, schema in primitives.items():
        if not schema.get("required"):
            errors.append(f"{primitive}: required fields missing")
        if not any(key in schema for key in ("states", "approval_states", "authority_levels")):
            errors.append(f"{primitive}: state/authority enumeration missing")
        if primitive in {"EngineeringDecision", "EngineeringRulePackReference"} and "human" not in json.dumps(schema).lower():
            errors.append(f"{primitive}: human authority boundary missing")

    templates = model.get("phase_templates", [])
    contract_phases = contract.get("phases", [])
    expected_ids = [f"P{i}" for i in range(17)]
    ids = [p.get("phase_id") for p in templates]
    if ids != expected_ids:
        errors.append(f"phase templates must be exactly P0-P16, got {ids}")
    if len(contract_phases) != 17:
        errors.append("source phase contract must contain 17 phases")

    by_contract = {p["id"]: p for p in contract_phases}
    by_model = {p["phase_id"]: p for p in templates if p.get("phase_id")}
    for pid in expected_ids:
        c = by_contract.get(pid)
        m = by_model.get(pid)
        if not c or not m:
            continue
        comparisons = {
            "name": c.get("name"),
            "dominant_question": c.get("dominant_question"),
            "workspace_id": c.get("primary_workspace"),
            "gate_id": c.get("gate"),
            "dependencies": c.get("dependencies"),
            "deliverable_ids": c.get("deliverables"),
            "primary_authority": c.get("primary_human_authority"),
        }
        for field, expected in comparisons.items():
            if m.get(field) != expected:
                errors.append(f"{pid}: {field} drift from phase contract")

    graph = {p["phase_id"]: list(p.get("dependencies", [])) for p in templates}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            errors.append(f"dependency cycle at {node}")
            return
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep not in graph:
                errors.append(f"{node}: unknown phase dependency {dep}")
            else:
                visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)

    transition = model.get("transition_policy", {})
    if transition.get("automatic_phase_completion_forbidden") is not True:
        errors.append("automatic phase completion must be forbidden")
    if transition.get("human_authority_stop_state") != "HUMAN_AUTHORITY_REQUIRED":
        errors.append("human authority stop state mismatch")
    if transition.get("local_residuals_do_not_block_unrelated_scopes") is not True:
        errors.append("local residual isolation rule missing")
    if transition.get("parallel_work") is not True:
        errors.append("parallel scoped work must remain allowed")

    rules = "\n".join(model.get("cross_phase_rules", [])).lower()
    for required in [
        "not a forced linear wizard",
        "stable cew entity identity",
        "information requirements",
        "human-factor acceptance",
        "engineeringrulepack",
        "calculation-model readiness",
    ]:
        if required not in rules:
            errors.append(f"missing cross-phase invariant: {required}")

    n12 = model.get("n12_projection", {})
    if n12.get("authority_path") != "knowledge/CURRENT_STATE.json":
        errors.append("N12 projection authority path mismatch")
    if n12.get("policy") != "READ_BY_REFERENCE_ONLY":
        errors.append("N12 projection must be reference-only")
    if n12.get("calculation_model_ready") is not False:
        errors.append("A1 may not mark N12 calculation model ready")

    items = {i["id"]: i for i in queue.get("items", [])}
    a0 = items.get("CEW-A0-STATE-RECONCILIATION", {})
    a1 = items.get("CEW-A1-PRODUCT-SPINE", {})
    if a0.get("state") != "COMPLETE":
        errors.append("A0 must be COMPLETE before lifecycle validation")
    if a1.get("state") not in {"READY", "IN_PROGRESS", "COMPLETE"}:
        errors.append(f"A1 has invalid lifecycle validation state: {a1.get('state')}")
    if a1.get("state") == "COMPLETE":
        receipt = a1.get("result_receipt")
        if not receipt:
            errors.append("completed A1 must declare result_receipt")
        elif not (ROOT / receipt).exists():
            errors.append(f"completed A1 receipt missing: {receipt}")

    current = state.get("current_product_work_item", {})
    if current.get("id") == "CEW-A1-PRODUCT-SPINE":
        if current.get("agent_role") != "PRODUCT_STATE_AGENT":
            errors.append("A1 current agent role mismatch")
    elif a1.get("state") != "COMPLETE":
        errors.append("A1 can stop being current only after COMPLETE")

    forbidden_keys = {
        "analytical_nodes", "ordinary_members", "support_count", "foundation_members",
        "reinforcement_values", "material_values", "load_values", "geotechnical_values"
    }
    text = json.dumps(model).lower()
    for key in forbidden_keys:
        if f'"{key}"' in text:
            errors.append(f"lifecycle model duplicates engineering detail key: {key}")

    if errors:
        print("CEW_PROJECT_LIFECYCLE_MODEL = FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("CEW_PROJECT_LIFECYCLE_MODEL = PASS")
    print("PHASES = P0-P16")
    print("PRIMITIVES = 7")
    print(f"A1_STATE = {a1.get('state')}")
    print("ENGINEERING_AUTHORITY = knowledge/CURRENT_STATE.json")
    print("AUTOMATIC_PHASE_COMPLETION = FORBIDDEN")
    print("N12_CALCULATION_MODEL_READY = false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
