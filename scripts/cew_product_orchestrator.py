#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "automation" / "CEW_PRODUCT_TRANSFORMATION_QUEUE_v1.json"
AGENT_CONTRACT_PATH = ROOT / "automation" / "CEW_PRODUCT_AGENT_CONTRACT_v1.json"
RESULT_CONTRACT_PATH = ROOT / "automation" / "CEW_PRODUCT_AGENT_RESULT_CONTRACT_v1.json"
PHASE_CONTRACT_PATH = ROOT / "automation" / "CEW_HUMAN_CENTRIC_PHASE_CONTRACT_v1.json"
TASK_OUTBOX = ROOT / "automation" / "outbox" / "CEW_PRODUCT_AGENT_TASK.json"
RESULT_INBOX = ROOT / "automation" / "inbox" / "CEW_PRODUCT_AGENT_RESULT.json"
RECEIPT_DIR = ROOT / "automation" / "receipts" / "cew-product"

ALLOWED_STATES = {
    "READY", "WAITING", "IN_PROGRESS", "RESIDUAL", "BLOCKED", "CONFLICT",
    "HUMAN_AUTHORITY_REQUIRED", "COMPLETE", "SUPERSEDED"
}
ACTIVE_PRECEDENCE = ["IN_PROGRESS", "RESIDUAL", "CONFLICT", "HUMAN_AUTHORITY_REQUIRED"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def item_map(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in queue.get("items", [])}


def deps_complete(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> bool:
    return all(by_id[dep].get("state") == "COMPLETE" for dep in item.get("dependencies", []))


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for path in [QUEUE_PATH, AGENT_CONTRACT_PATH, RESULT_CONTRACT_PATH, PHASE_CONTRACT_PATH]:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")
    if errors:
        return errors, warnings

    try:
        queue = read_json(QUEUE_PATH)
        agents = read_json(AGENT_CONTRACT_PATH)
        results = read_json(RESULT_CONTRACT_PATH)
        phases = read_json(PHASE_CONTRACT_PATH)
    except Exception as exc:
        return [f"invalid JSON: {exc}"], warnings

    if queue.get("program_goal") != "CEW-GOAL-01":
        errors.append("queue program_goal must be CEW-GOAL-01")
    if agents.get("program_goal") != queue.get("program_goal"):
        errors.append("agent contract goal differs from queue goal")
    if results.get("program_goal") != queue.get("program_goal"):
        errors.append("result contract goal differs from queue goal")
    if phases.get("development_model") != "HUMAN_CENTRED_STRUCTURAL_ENGINEERING_LIFECYCLE":
        errors.append("phase contract development model mismatch")
    if agents.get("max_work_items_per_agent_result") != 1:
        errors.append("agent contract must enforce one work item per result")
    if results.get("max_work_items_per_result") != 1:
        errors.append("result contract must enforce one work item per result")

    roles = set(agents.get("agent_roles", {}))
    items = queue.get("items", [])
    ids = [item.get("id") for item in items]
    if not items:
        errors.append("product transformation queue is empty")
    if len(ids) != len(set(ids)):
        errors.append("duplicate work item id")
    by_id = item_map(queue)

    for item in items:
        iid = item.get("id", "<missing>")
        if item.get("state") not in ALLOWED_STATES:
            errors.append(f"{iid}: invalid state={item.get('state')}")
        if item.get("agent_role") not in roles:
            errors.append(f"{iid}: unknown agent role={item.get('agent_role')}")
        if not item.get("target_outputs"):
            errors.append(f"{iid}: target_outputs empty")
        if not item.get("required_gates"):
            errors.append(f"{iid}: required_gates empty")
        for dep in item.get("dependencies", []):
            if dep not in by_id:
                errors.append(f"{iid}: unknown dependency={dep}")
            if dep == iid:
                errors.append(f"{iid}: self dependency")

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

    active = [i for i in items if i.get("state") in set(ACTIVE_PRECEDENCE)]
    if len(active) > 1:
        errors.append("more than one promotion work item is active")

    return errors, warnings


def select_next(queue: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    by_id = item_map(queue)
    ordered = sorted(queue.get("items", []), key=lambda x: (int(x.get("priority", 999999)), x.get("id", "")))

    for state in ACTIVE_PRECEDENCE:
        for item in ordered:
            if item.get("state") == state:
                return item, state

    for item in ordered:
        if item.get("state") in {"COMPLETE", "SUPERSEDED", "BLOCKED"}:
            continue
        if deps_complete(item, by_id) and item.get("state") in {"READY", "WAITING"}:
            return item, "READY" if item.get("state") == "READY" else "AUTO_RELEASED_WAITING"
    return None, "NO_ELIGIBLE_ITEM"


def status_payload() -> dict[str, Any]:
    errors, warnings = validate()
    if errors:
        return {
            "program_goal": "CEW-GOAL-01",
            "decision": "FAIL_STOP",
            "contract_errors": errors,
            "contract_warnings": warnings,
        }
    queue = read_json(QUEUE_PATH)
    selected, reason = select_next(queue)
    incomplete = [i for i in queue["items"] if i.get("state") not in {"COMPLETE", "SUPERSEDED"}]
    return {
        "program_goal": queue.get("program_goal"),
        "decision": "READY_FOR_AGENT" if selected else ("COMPLETE" if not incomplete else "BLOCKED_DEPENDENCY"),
        "selection_reason": reason,
        "selected_work_item": selected,
        "completion": {
            "complete": sum(1 for i in queue["items"] if i.get("state") == "COMPLETE"),
            "total": len(queue["items"]),
        },
        "contract_warnings": warnings,
    }


def make_task() -> dict[str, Any]:
    payload = status_payload()
    if payload.get("decision") != "READY_FOR_AGENT":
        raise RuntimeError(f"no agent task can be released: {payload.get('decision')}")
    item = payload["selected_work_item"]
    agents = read_json(AGENT_CONTRACT_PATH)
    task = {
        "schema_version": "1.0",
        "program_goal": "CEW-GOAL-01",
        "work_item_id": item["id"],
        "agent_role": item["agent_role"],
        "agent_goal": agents["agent_roles"][item["agent_role"]]["goal"],
        "objective": item["objective"],
        "dependencies": item.get("dependencies", []),
        "target_outputs": item.get("target_outputs", []),
        "required_gates": item.get("required_gates", []),
        "global_invariants": agents.get("global_invariants", []),
        "forbidden": agents["agent_roles"][item["agent_role"]].get("forbidden", []),
        "authority_boundary": "Prepare/validate only; do not exercise human engineering authority or alter N12 engineering facts unless the work item explicitly governs product state.",
        "result_contract": str(RESULT_CONTRACT_PATH.relative_to(ROOT)),
        "result_inbox": str(RESULT_INBOX.relative_to(ROOT)),
    }
    write_json(TASK_OUTBOX, task)
    return task


def ingest(result_path: Path) -> dict[str, Any]:
    errors, _ = validate()
    if errors:
        raise ValueError("cannot ingest while orchestrator contract is invalid")
    queue = read_json(QUEUE_PATH)
    selected, _ = select_next(queue)
    if not selected:
        raise ValueError("no selected work item")
    result = read_json(result_path)
    contract = read_json(RESULT_CONTRACT_PATH)

    required = contract.get("required_fields", [])
    missing = [field for field in required if field not in result]
    if missing:
        raise ValueError(f"result missing required fields: {missing}")
    if result.get("work_item_id") != selected.get("id"):
        raise ValueError("result work_item_id does not match orchestrator selection")
    if result.get("agent_role") != selected.get("agent_role"):
        raise ValueError("result agent_role does not match selected work item")
    if result.get("decision") not in contract.get("allowed_decisions", []):
        raise ValueError("result decision not allowed")
    if result.get("target_outputs") != selected.get("target_outputs"):
        raise ValueError("result target_outputs do not exactly match queue item")

    if result["decision"] in {"PASS", "PASS_WITH_WATCH"}:
        missing_outputs = [rel for rel in selected.get("target_outputs", []) if not (ROOT / rel).exists()]
        if missing_outputs:
            raise ValueError(f"PASS result has missing target outputs: {missing_outputs}")
        required_gates = set(selected.get("required_gates", []))
        validation = result.get("validation", {})
        passed = {k for k, v in validation.items() if v in {"PASS", "PASS_WITH_WATCH"}}
        missing_gates = sorted(required_gates - passed)
        if missing_gates:
            raise ValueError(f"PASS result missing required validation gates: {missing_gates}")
        selected["state"] = "COMPLETE"
        selected["completion_decision"] = result["decision"]
        selected["completed_at"] = datetime.now(timezone.utc).isoformat()
    elif result["decision"] == "HUMAN_AUTHORITY_REQUIRED":
        selected["state"] = "HUMAN_AUTHORITY_REQUIRED"
    else:
        selected["state"] = result["decision"]

    by_id = item_map(queue)
    if selected.get("state") == "COMPLETE":
        for item in queue.get("items", []):
            if item.get("state") == "WAITING" and deps_complete(item, by_id):
                item["state"] = "READY"

    queue["updated_at"] = datetime.now(timezone.utc).date().isoformat()
    write_json(QUEUE_PATH, queue)

    receipt = {
        "schema_version": "1.0",
        "program_goal": "CEW-GOAL-01",
        "work_item_id": selected["id"],
        "decision": result["decision"],
        "agent_role": result["agent_role"],
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = RECEIPT_DIR / f"{selected['id']}_{stamp}.json"
    write_json(receipt_path, receipt)
    receipt["receipt_path"] = str(receipt_path.relative_to(ROOT))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="CEW human-centred product transformation orchestrator")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sub.add_parser("status")
    sub.add_parser("make-task")
    ingest_parser = sub.add_parser("ingest")
    ingest_parser.add_argument("--result", default=str(RESULT_INBOX.relative_to(ROOT)))
    args = parser.parse_args()

    if args.cmd == "validate":
        errors, warnings = validate()
        if errors:
            print("CEW_PRODUCT_ORCHESTRATOR = FAIL")
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("CEW_PRODUCT_ORCHESTRATOR = PASS")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 0
    if args.cmd == "status":
        print(json.dumps(status_payload(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "make-task":
        print(json.dumps(make_task(), ensure_ascii=False, indent=2))
        return 0
    result_path = ROOT / args.result
    print(json.dumps(ingest(result_path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
