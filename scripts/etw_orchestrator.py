#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "automation" / "ETW_DEVELOPMENT_QUEUE_v1.json"
AGENT_CONTRACT_PATH = ROOT / "automation" / "ETW_SPECIALIST_AGENT_CONTRACT_v1.json"
RESULT_CONTRACT_PATH = ROOT / "automation" / "ETW_AGENT_RESULT_CONTRACT_v1.json"
GATE_STATE_PATH = ROOT / "automation" / "ETW_HUMAN_GATE_STATE_v1.json"
PLAN_PATH = ROOT / "docs" / "PROGRAM" / "ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1.md"
TASK_OUTBOX = ROOT / "automation" / "outbox" / "ETW_AGENT_TASK.json"
SUPPORT_OUTBOX = ROOT / "automation" / "outbox" / "ETW_SUPPORT_AGENT_TASK.json"
RESULT_INBOX = ROOT / "automation" / "inbox" / "ETW_AGENT_RESULT.json"
RECEIPT_DIR = ROOT / "automation" / "receipts" / "etw-platform"

ALLOWED_STATES = {
    "PREP_ONLY",
    "PREPARED_BLOCKED_PROMOTION",
    "READY",
    "WAITING",
    "IN_PROGRESS",
    "RESIDUAL",
    "BLOCKED",
    "CONFLICT",
    "HUMAN_AUTHORITY_REQUIRED",
    "COMPLETE",
    "SUPERSEDED",
}
ACTIVE_PRECEDENCE = ["IN_PROGRESS", "RESIDUAL", "CONFLICT", "HUMAN_AUTHORITY_REQUIRED"]
PASS_GATE_STATES = {"PASS", "SATISFIED", "APPROVED"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def item_map(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in queue.get("items", [])}


def deps_complete(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> bool:
    return all(by_id.get(dep, {}).get("state") == "COMPLETE" for dep in item.get("dependencies", []))


def gate_map() -> dict[str, dict[str, Any]]:
    return read_json(GATE_STATE_PATH).get("gates", {})


def gate_satisfied(gate_id: str, gates: dict[str, dict[str, Any]]) -> bool:
    return gates.get(gate_id, {}).get("state") in PASS_GATE_STATES


def item_release_blockers(item: dict[str, Any], gates: dict[str, dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for gate_id, gate in gates.items():
        if item.get("id") in gate.get("blocks_release_of", []) and not gate_satisfied(gate_id, gates):
            blockers.append(gate_id)
    return sorted(blockers)


def item_promotion_blockers(item: dict[str, Any], gates: dict[str, dict[str, Any]]) -> list[str]:
    blockers = []
    for gate_id in item.get("external_promotion_dependencies", []):
        if not gate_satisfied(gate_id, gates):
            blockers.append(gate_id)
    return sorted(blockers)


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for path in [QUEUE_PATH, AGENT_CONTRACT_PATH, RESULT_CONTRACT_PATH, GATE_STATE_PATH, PLAN_PATH]:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")
    if errors:
        return errors, warnings

    try:
        queue = read_json(QUEUE_PATH)
        agents = read_json(AGENT_CONTRACT_PATH)
        results = read_json(RESULT_CONTRACT_PATH)
        gate_state = read_json(GATE_STATE_PATH)
    except Exception as exc:
        return [f"invalid JSON: {exc}"], warnings

    if queue.get("program_id") != "ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1":
        errors.append("queue program_id mismatch")
    if agents.get("program_id") != queue.get("program_id"):
        errors.append("agent contract program_id differs from queue")
    if results.get("program_id") != queue.get("program_id"):
        errors.append("result contract program_id differs from queue")
    if gate_state.get("program_id") != queue.get("program_id"):
        errors.append("gate state program_id differs from queue")
    if agents.get("max_work_items_per_agent_result") != 1:
        errors.append("one work item per owner result is mandatory")
    if results.get("max_work_items_per_result") != 1:
        errors.append("result contract must enforce one work item")

    owner_roles = set(agents.get("promotion_owner_roles", {}))
    items = queue.get("items", [])
    ids = [item.get("id") for item in items]
    if not items:
        errors.append("ETW queue is empty")
    if len(ids) != len(set(ids)):
        errors.append("duplicate work item id")

    by_id = item_map(queue)
    gates = gate_state.get("gates", {})
    for item in items:
        iid = item.get("id", "<missing>")
        if item.get("state") not in ALLOWED_STATES:
            errors.append(f"{iid}: invalid state={item.get('state')}")
        if item.get("agent_role") not in owner_roles:
            errors.append(f"{iid}: unknown promotion owner={item.get('agent_role')}")
        if iid not in agents["promotion_owner_roles"][item["agent_role"]].get("owns", []):
            errors.append(f"{iid}: role {item.get('agent_role')} does not own item")
        if not item.get("target_outputs"):
            errors.append(f"{iid}: target_outputs empty")
        if not item.get("required_gates"):
            errors.append(f"{iid}: required_gates empty")
        for dep in item.get("dependencies", []):
            if dep not in by_id:
                errors.append(f"{iid}: unknown dependency={dep}")
            if dep == iid:
                errors.append(f"{iid}: self dependency")
        for gate_id in item.get("external_promotion_dependencies", []):
            if gate_id not in gates:
                errors.append(f"{iid}: unknown external promotion dependency={gate_id}")

    for gate_id, gate in gates.items():
        for item_id in gate.get("blocks_release_of", []):
            if item_id != "ETW_PLATFORM_V1_PRODUCTION" and item_id not in by_id:
                errors.append(f"{gate_id}: blocks unknown item {item_id}")

    graph = {item["id"]: list(item.get("dependencies", [])) for item in items if item.get("id")}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            errors.append(f"dependency cycle detected at {node}")
            return
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)

    active = [item for item in items if item.get("state") in set(ACTIVE_PRECEDENCE)]
    if len(active) > agents.get("max_promotion_work_items_active", 1):
        errors.append("more than one promotion-owner work item is active")

    a0 = by_id.get("ETW-A0", {})
    if a0.get("state") in {"COMPLETE", "READY", "IN_PROGRESS"} and not gate_satisfied("CEW_PROMOTED_BASELINE", gates):
        errors.append("ETW-A0 cannot be promotion-active or COMPLETE before CEW_PROMOTED_BASELINE")

    if queue.get("baseline_policy", {}).get("cew_promoted_baseline_sha") and not gate_satisfied("CEW_PROMOTED_BASELINE", gates):
        warnings.append("queue contains CEW promoted SHA but external gate is not satisfied")

    return errors, warnings


def select_next(queue: dict[str, Any]) -> tuple[dict[str, Any] | None, str, list[str]]:
    by_id = item_map(queue)
    gates = gate_map()
    ordered = sorted(queue.get("items", []), key=lambda x: (int(x.get("priority", 999999)), x.get("id", "")))

    for state in ACTIVE_PRECEDENCE:
        for item in ordered:
            if item.get("state") == state:
                return item, state, item_release_blockers(item, gates) + item_promotion_blockers(item, gates)

    for item in ordered:
        state = item.get("state")
        if state == "PREP_ONLY" and deps_complete(item, by_id):
            return item, "PREP_ONLY", item_promotion_blockers(item, gates)

    for item in ordered:
        state = item.get("state")
        if state == "PREPARED_BLOCKED_PROMOTION" and deps_complete(item, by_id):
            blockers = item_promotion_blockers(item, gates) + item_release_blockers(item, gates)
            if not blockers:
                return item, "PROMOTION_REVALIDATION_READY", []

    for item in ordered:
        if item.get("state") not in {"READY", "WAITING"}:
            continue
        if not deps_complete(item, by_id):
            continue
        blockers = item_release_blockers(item, gates)
        if blockers:
            continue
        return item, "READY" if item.get("state") == "READY" else "AUTO_RELEASED_WAITING", []

    return None, "NO_ELIGIBLE_ITEM", []


def status_payload() -> dict[str, Any]:
    errors, warnings = validate()
    if errors:
        return {
            "program_id": "ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1",
            "decision": "FAIL_STOP",
            "contract_errors": errors,
            "contract_warnings": warnings,
        }
    queue = read_json(QUEUE_PATH)
    gates = gate_map()
    selected, reason, blockers = select_next(queue)
    incomplete = [item for item in queue["items"] if item.get("state") not in {"COMPLETE", "SUPERSEDED"}]
    final_gate_pending = not gate_satisfied("APPROVE_PRODUCTION_ACCEPTANCE", gates)
    if selected:
        decision = "READY_FOR_AGENT"
    elif not incomplete and final_gate_pending:
        decision = "HUMAN_AUTHORITY_REQUIRED"
    elif not incomplete:
        decision = "COMPLETE"
    else:
        decision = "BLOCKED_DEPENDENCY"
    return {
        "program_id": queue.get("program_id"),
        "decision": decision,
        "selection_reason": reason,
        "selected_work_item": selected,
        "promotion_blockers": blockers,
        "external_gate_state": {k: v.get("state") for k, v in gates.items()},
        "completion": {
            "complete": sum(1 for item in queue["items"] if item.get("state") == "COMPLETE"),
            "total": len(queue["items"]),
        },
        "contract_warnings": warnings,
    }


def make_task() -> dict[str, Any]:
    status = status_payload()
    if status.get("decision") != "READY_FOR_AGENT":
        raise RuntimeError(f"no ETW owner task can be released: {status.get('decision')}")
    item = status["selected_work_item"]
    queue = read_json(QUEUE_PATH)
    agents = read_json(AGENT_CONTRACT_PATH)
    role = item["agent_role"]
    reason = status.get("selection_reason")
    prep_mode = reason == "PREP_ONLY"
    validation_gates = item.get("prep_required_gates", []) if prep_mode else item.get("required_gates", [])
    task = {
        "schema_version": "1.0",
        "program_id": queue.get("program_id"),
        "work_item_id": item["id"],
        "agent_role": role,
        "execution_mode": "PREP_ONLY" if prep_mode else ("PROMOTION_REVALIDATION" if reason == "PROMOTION_REVALIDATION_READY" else "PROMOTABLE"),
        "agent_goal": agents["promotion_owner_roles"][role]["goal"],
        "objective": item["objective"],
        "dependencies": item.get("dependencies", []),
        "promotion_blockers": status.get("promotion_blockers", []),
        "target_outputs": item.get("target_outputs", []),
        "required_gates": validation_gates,
        "critical_safety_metrics": item.get("critical_safety_metrics", []),
        "global_invariants": agents.get("global_invariants", []),
        "forbidden": agents["promotion_owner_roles"][role].get("forbidden", []),
        "baseline_policy": queue.get("baseline_policy", {}),
        "authority_boundary": "Platform work may prepare/adapt product state but must not alter N12 engineering facts, CEW engineering authority, human Level-C decisions or immutable SourceVersion identity.",
        "result_contract": str(RESULT_CONTRACT_PATH.relative_to(ROOT)),
        "result_inbox": str(RESULT_INBOX.relative_to(ROOT)),
    }
    write_json(TASK_OUTBOX, task)
    return task


def make_support_task(role: str) -> dict[str, Any]:
    status = status_payload()
    selected = status.get("selected_work_item")
    if not selected:
        raise RuntimeError("no selected owner work item for support task")
    agents = read_json(AGENT_CONTRACT_PATH)
    support = agents.get("support_agent_roles", {})
    if role not in support:
        raise ValueError(f"unknown support role: {role}")
    task = {
        "schema_version": "1.0",
        "program_id": "ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1",
        "support_role": role,
        "supports_work_item_id": selected["id"],
        "goal": support[role]["goal"],
        "may_promote": False,
        "owner_agent_role": selected["agent_role"],
        "required_gates": selected.get("required_gates", []),
        "critical_safety_metrics": selected.get("critical_safety_metrics", []),
        "authority_boundary": "Independent verification/support only. This result cannot mutate queue state or promote a work item."
    }
    write_json(SUPPORT_OUTBOX, task)
    return task


def ingest(result_path: Path) -> dict[str, Any]:
    errors, _ = validate()
    if errors:
        raise ValueError("cannot ingest while ETW orchestrator contract is invalid")
    queue = read_json(QUEUE_PATH)
    selected, reason, blockers = select_next(queue)
    if not selected:
        raise ValueError("no selected ETW work item")
    result = read_json(result_path)
    contract = read_json(RESULT_CONTRACT_PATH)

    missing = [field for field in contract.get("required_fields", []) if field not in result]
    if missing:
        raise ValueError(f"result missing required fields: {missing}")
    if result.get("work_item_id") != selected.get("id"):
        raise ValueError("result work_item_id does not match orchestrator selection")
    if result.get("agent_role") != selected.get("agent_role"):
        raise ValueError("result agent_role does not match selected promotion owner")
    decision = result.get("decision")
    if decision not in contract.get("allowed_decisions", []):
        raise ValueError("result decision not allowed")
    if result.get("target_outputs") != selected.get("target_outputs"):
        raise ValueError("result target_outputs do not exactly match queue item")

    baseline = result.get("baseline", {})
    for field in contract.get("baseline_required_fields", []):
        if field not in baseline:
            raise ValueError(f"baseline missing {field}")

    critical = set(selected.get("critical_safety_metrics", []))
    usability = result.get("usability", {})
    failures = {name for name in critical if usability.get(name) in {True, "FAIL", "FAILED", "VIOLATION"}}
    if failures and decision in {"PREP_PASS", "PASS", "PASS_WITH_WATCH"}:
        raise ValueError(f"pass decision has critical safety failures: {sorted(failures)}")

    prep_mode = reason == "PREP_ONLY" or selected.get("state") == "PREP_ONLY"
    if decision == "PREP_PASS":
        if not prep_mode:
            raise ValueError("PREP_PASS only allowed for PREP_ONLY execution")
        required = set(selected.get("prep_required_gates", []))
        validation = result.get("validation", {})
        passed = {k for k, v in validation.items() if v in {"PASS", "PASS_WITH_WATCH"}}
        missing_gates = sorted(required - passed)
        if missing_gates:
            raise ValueError(f"PREP_PASS missing prep gates: {missing_gates}")
        missing_outputs = [rel for rel in selected.get("target_outputs", []) if not (ROOT / rel).exists()]
        if missing_outputs:
            raise ValueError(f"PREP_PASS has missing outputs: {missing_outputs}")
        selected["state"] = "PREPARED_BLOCKED_PROMOTION"
        selected["preparation_decision"] = "PREP_PASS"
        selected["prepared_at"] = datetime.now(timezone.utc).isoformat()
        selected["promotion_blockers"] = item_promotion_blockers(selected, gate_map())
    elif decision in {"PASS", "PASS_WITH_WATCH"}:
        if prep_mode and item_promotion_blockers(selected, gate_map()):
            raise ValueError("cannot PASS PREP_ONLY item while promotion blockers remain; use PREP_PASS")
        required = set(selected.get("required_gates", []))
        validation = result.get("validation", {})
        passed = {k for k, v in validation.items() if v in {"PASS", "PASS_WITH_WATCH"}}
        missing_gates = sorted(required - passed)
        if missing_gates:
            raise ValueError(f"PASS missing required gates: {missing_gates}")
        missing_outputs = [rel for rel in selected.get("target_outputs", []) if not (ROOT / rel).exists()]
        if missing_outputs:
            raise ValueError(f"PASS result has missing outputs: {missing_outputs}")
        selected["state"] = "COMPLETE"
        selected["completion_decision"] = decision
        selected["completed_at"] = datetime.now(timezone.utc).isoformat()
    elif decision == "HUMAN_AUTHORITY_REQUIRED":
        selected["state"] = "HUMAN_AUTHORITY_REQUIRED"
    else:
        selected["state"] = decision

    queue["updated_at"] = datetime.now(timezone.utc).date().isoformat()
    write_json(QUEUE_PATH, queue)

    receipt = {
        "schema_version": "1.0",
        "program_id": queue.get("program_id"),
        "work_item_id": selected["id"],
        "decision": decision,
        "agent_role": result["agent_role"],
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "selection_reason": reason,
        "promotion_blockers_at_ingest": blockers,
        "result": result,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RECEIPT_DIR / f"{selected['id']}_{stamp}.json"
    write_json(path, receipt)
    receipt["receipt_path"] = str(path.relative_to(ROOT))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="eTwin platform extension orchestrator")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sub.add_parser("status")
    sub.add_parser("make-task")
    support = sub.add_parser("make-support-task")
    support.add_argument("--role", required=True)
    ingest_parser = sub.add_parser("ingest")
    ingest_parser.add_argument("--result", default=str(RESULT_INBOX.relative_to(ROOT)))
    args = parser.parse_args()

    if args.cmd == "validate":
        errors, warnings = validate()
        if errors:
            print("ETW_ORCHESTRATOR = FAIL")
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("ETW_ORCHESTRATOR = PASS")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 0
    if args.cmd == "status":
        print(json.dumps(status_payload(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "make-task":
        print(json.dumps(make_task(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "make-support-task":
        print(json.dumps(make_support_task(args.role), ensure_ascii=False, indent=2))
        return 0
    result_path = ROOT / args.result
    print(json.dumps(ingest(result_path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
