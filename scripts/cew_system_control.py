from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "automation" / "CEW_SYSTEM_COMPLETENESS_MATRIX_v0.json"
QUEUE_PATH = ROOT / "automation" / "CEW_PLATFORM_WORK_QUEUE_v0.json"
STATE_PATH = ROOT / "automation" / "CEW_PLATFORM_WORK_STATE_v0.json"
REGISTRY_PATH = ROOT / "automation" / "CEW_AGENT_CAPABILITY_REGISTRY_v0.json"

TERMINAL_OR_BLOCKED = {"COMPLETE", "WAITING", "READY", "BLOCKED_EVIDENCE", "BLOCKED_CANONICAL_GATE", "BLOCKED_HUMAN_DECISION", "FAIL_STOP"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def effective_statuses(queue: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    runtime = state.get("items", {})
    return {item["id"]: runtime.get(item["id"], {}).get("status", item.get("status", "UNKNOWN")) for item in queue.get("items", [])}


def capability_owners(queue: dict[str, Any]) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = {}
    for item in queue.get("items", []):
        for capability in item.get("requires_capabilities", []):
            owners.setdefault(capability, set()).add(item["id"])
    return owners


def validate(matrix: dict[str, Any], queue: dict[str, Any], state: dict[str, Any], registry: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    workstreams = matrix.get("workstreams", {})
    expected = {f"W{i}" for i in range(9)}
    actual = set(workstreams)
    if actual != expected:
        errors.append(f"workstream coverage mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
    queue_items = {x["id"]: x for x in queue.get("items", [])}
    runtime = state.get("items", {})
    capabilities = registry.get("capabilities", {})
    if set(queue_items) != set(runtime):
        errors.append("queue/runtime work-item sets differ")
    for wid, runtime_entry in runtime.items():
        if runtime_entry.get("status") not in TERMINAL_OR_BLOCKED:
            errors.append(f"{wid}: unknown runtime status {runtime_entry.get('status')}")
    for stream, spec in workstreams.items():
        if not spec.get("required_capabilities"):
            errors.append(f"{stream}: no required capabilities")
        if not spec.get("owning_work_items"):
            errors.append(f"{stream}: no owning work items")
        for capability in spec.get("required_capabilities", []):
            if capability not in capabilities:
                errors.append(f"{stream}: unknown capability {capability}")
        for wid in spec.get("owning_work_items", []):
            if wid not in queue_items:
                errors.append(f"{stream}: unknown owning work item {wid}")
    owners = capability_owners(queue)
    if matrix.get("reporting", {}).get("fail_on_unowned_domain_or_system_capability", False):
        for name, spec in capabilities.items():
            if spec.get("class") in {"CEW_DOMAIN_CAPABILITY", "CEW_SYSTEM_CAPABILITY"} and not owners.get(name):
                errors.append(f"unowned {spec.get('class')} capability: {name}")
    boundary = matrix.get("canonical_boundary", {})
    queue_boundary = queue.get("canonical_boundary", {})
    if boundary.get("cew_f2") != "IN_PROGRESS" or queue_boundary.get("cew_f2") != "IN_PROGRESS":
        errors.append("experimental Platform OS may not declare CEW-F2 closed")
    if boundary.get("canonical_promotion") != "DISABLED":
        errors.append("system completeness control must keep canonical promotion disabled")
    return not errors, errors


def health(matrix: dict[str, Any], queue: dict[str, Any], state: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    ok, errors = validate(matrix, queue, state, registry)
    statuses = effective_statuses(queue, state)
    by_status = Counter(statuses.values())
    workstreams: dict[str, Any] = {}
    for stream, spec in matrix["workstreams"].items():
        item_states = {wid: statuses.get(wid, "UNKNOWN") for wid in spec["owning_work_items"]}
        blockers = {wid: status for wid, status in item_states.items() if status.startswith("BLOCKED_") or status == "FAIL_STOP"}
        workstreams[stream] = {"title": spec["title"], "work_items": item_states, "blockers": blockers, "complete_items": sum(status == "COMPLETE" for status in item_states.values()), "item_count": len(item_states)}
    owners = capability_owners(queue)
    optional_unscheduled = sorted(name for name, spec in registry.get("capabilities", {}).items() if spec.get("class") == "SPECIALIST_PORT" and not owners.get(name))
    return {"status": "PASS" if ok else "FAIL", "schema_version": matrix.get("schema_version"), "workstreams_total": len(workstreams), "workstreams": workstreams, "runtime_status_counts": dict(sorted(by_status.items())), "optional_specialist_ports_not_yet_scheduled": optional_unscheduled, "errors": errors, "canonical_boundary": matrix["canonical_boundary"], "next_system_candidates": [wid for wid, status in statuses.items() if status in {"READY", "WAITING"}]}


def main() -> None:
    parser = argparse.ArgumentParser(description="CEW W0-W8 system completeness control")
    parser.add_argument("command", choices=["validate", "health"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    matrix, queue, state, registry = map(load, (MATRIX_PATH, QUEUE_PATH, STATE_PATH, REGISTRY_PATH))
    payload = health(matrix, queue, state, registry)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if args.command == "validate" and payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
