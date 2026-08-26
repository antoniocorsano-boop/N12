from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "automation" / "CEW_PLATFORM_WORK_QUEUE_v0.json"
WORK_STATE_PATH = ROOT / "automation" / "CEW_PLATFORM_WORK_STATE_v0.json"
POLICY_PATH = ROOT / "automation" / "CEW_EXECUTION_POLICY_v0.json"
CAPABILITY_PATH = ROOT / "automation" / "CEW_AGENT_CAPABILITY_REGISTRY_v0.json"
CONTRACT_PATH = ROOT / "automation" / "CEW_AGENT_RESULT_CONTRACT_v0.json"
CHECKPOINT_PATH = ROOT / "automation" / "CEW_CHECKPOINT_CONTRACT_v0.json"

VALID_STATUSES = {
    "COMPLETE",
    "READY",
    "WAITING",
    "BLOCKED_EVIDENCE",
    "BLOCKED_CANONICAL_GATE",
    "BLOCKED_HUMAN_DECISION",
    "FAIL_STOP",
}
VALID_EXECUTION_MODES = {"SERIAL", "PARALLEL_SAFE"}
VALID_WAITING_READINESS_POLICIES = {"EXPLICIT_ONLY", "AUTO_WHEN_DEPENDENCIES_COMPLETE"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_state() -> tuple[dict[str, Any], ...]:
    return (
        load_json(QUEUE_PATH),
        load_json(POLICY_PATH),
        load_json(CAPABILITY_PATH),
        load_json(CONTRACT_PATH),
        load_json(CHECKPOINT_PATH),
    )


def load_work_state() -> dict[str, Any]:
    return load_json(WORK_STATE_PATH)


def apply_work_state(queue: dict[str, Any], work_state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = work_state if work_state is not None else load_work_state()
    runtime = state.get("items", {})
    effective = dict(queue)
    effective_items: list[dict[str, Any]] = []
    for item in queue.get("items", []):
        merged = dict(item)
        overlay = runtime.get(item["id"], {})
        if "status" in overlay:
            merged["status"] = overlay["status"]
        merged["runtime_state"] = overlay
        effective_items.append(merged)
    effective["items"] = effective_items
    return effective


def dependency_cycle(items: list[dict[str, Any]]) -> list[str] | None:
    graph = {item["id"]: item.get("depends_on", []) for item in items if item.get("id")}
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visited:
            return None
        if node in visiting:
            idx = stack.index(node)
            return stack[idx:] + [node]
        visiting.add(node)
        stack.append(node)
        for dep in graph.get(node, []):
            cycle = visit(dep)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for node in graph:
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def validate() -> tuple[bool, list[str]]:
    errors: list[str] = []
    for path in [QUEUE_PATH, WORK_STATE_PATH, POLICY_PATH, CAPABILITY_PATH, CONTRACT_PATH, CHECKPOINT_PATH]:
        if not path.is_file():
            errors.append(f"missing contract: {path}")
    if errors:
        return False, errors

    queue, policy, registry, contract, checkpoint = load_state()
    work_state = load_work_state()
    items = queue.get("items", [])
    ids = [item.get("id") for item in items]
    profiles = policy.get("profiles", {})
    capabilities = registry.get("capabilities", {})

    if not items:
        errors.append("queue has no items")
    if None in ids:
        errors.append("every work item must have id")
    if len(ids) != len(set(ids)):
        errors.append("duplicate work item ids")

    idset = {x for x in ids if x is not None}
    runtime_ids = set(work_state.get("items", {}))
    unknown_runtime = runtime_ids - idset
    missing_runtime = idset - runtime_ids
    if unknown_runtime:
        errors.append(f"runtime state contains unknown work items: {sorted(unknown_runtime)}")
    if missing_runtime:
        errors.append(f"runtime state missing work items: {sorted(missing_runtime)}")

    for item in items:
        wid = item.get("id", "<missing>")
        bootstrap_status = item.get("status")
        if bootstrap_status not in VALID_STATUSES:
            errors.append(f"{wid}: invalid bootstrap status {bootstrap_status}")
        runtime_entry = work_state.get("items", {}).get(wid, {})
        runtime_status = runtime_entry.get("status")
        if runtime_status not in VALID_STATUSES:
            errors.append(f"{wid}: invalid runtime status {runtime_status}")
        receipt = runtime_entry.get("receipt")
        checkpoint_ref = runtime_entry.get("checkpoint")
        if receipt and not (ROOT / receipt).is_file():
            errors.append(f"{wid}: receipt does not exist: {receipt}")
        if checkpoint_ref and not (ROOT / checkpoint_ref).is_file():
            errors.append(f"{wid}: checkpoint does not exist: {checkpoint_ref}")

        profile = item.get("profile")
        if profile not in profiles:
            errors.append(f"{wid}: unknown execution profile {profile}")
        priority = item.get("priority")
        if not isinstance(priority, int) or priority < 0:
            errors.append(f"{wid}: priority must be a non-negative integer")
        for dep in item.get("depends_on", []):
            if dep not in idset:
                errors.append(f"{wid}: unknown dependency {dep}")
        for capability in item.get("requires_capabilities", []):
            if capability not in capabilities:
                errors.append(f"{wid}: unknown capability {capability}")
        execution = item.get("execution", {})
        if execution.get("mode") not in VALID_EXECUTION_MODES:
            errors.append(f"{wid}: invalid execution mode {execution.get('mode')}")
        locks = execution.get("locks", [])
        if not isinstance(locks, list) or len(locks) != len(set(locks)):
            errors.append(f"{wid}: locks must be a unique list")
        if not item.get("completion"):
            errors.append(f"{wid}: no completion criteria")

    cycle = dependency_cycle(items)
    if cycle:
        errors.append(f"dependency cycle: {' -> '.join(cycle)}")

    global_policy = policy.get("global", {})
    if not isinstance(global_policy.get("max_parallel_work_items"), int) or global_policy.get("max_parallel_work_items", 0) < 1:
        errors.append("execution policy max_parallel_work_items must be >= 1")
    readiness_policy = global_policy.get("waiting_readiness_policy", "EXPLICIT_ONLY")
    if readiness_policy not in VALID_WAITING_READINESS_POLICIES:
        errors.append(f"invalid waiting_readiness_policy: {readiness_policy}")
    for name, profile in profiles.items():
        if not isinstance(profile.get("max_attempts"), int) or profile.get("max_attempts", 0) < 1:
            errors.append(f"profile {name}: max_attempts must be >= 1")

    for capability, spec in capabilities.items():
        providers = spec.get("providers", [])
        if not providers:
            errors.append(f"capability {capability}: at least one provider required")
        if len(providers) != len(set(providers)):
            errors.append(f"capability {capability}: duplicate providers")

    outcomes = set(contract.get("allowed_outcomes", []))
    required_outcomes = {
        "COMPLETE_PASS",
        "COMPLETE_PASS_WITH_REVIEW",
        "BLOCKED_HUMAN_DECISION",
        "BLOCKED_EVIDENCE",
        "BLOCKED_CANONICAL_GATE",
        "FAIL_STOP",
    }
    if missing := required_outcomes - outcomes:
        errors.append(f"result contract missing outcomes: {sorted(missing)}")

    result_fields = set(contract.get("required_fields", []))
    for field in {
        "work_item_id",
        "outcome",
        "execution_profile",
        "attempt_no",
        "head_sha",
        "input_fingerprints",
        "selected_providers",
        "outputs",
        "gates",
        "residuals",
        "checkpoint_id",
    }:
        if field not in result_fields:
            errors.append(f"result contract missing required field: {field}")

    checkpoint_fields = set(checkpoint.get("required_fields", []))
    for field in {"checkpoint_id", "work_item_id", "execution_profile", "attempt_no", "stage", "input_fingerprints", "next_step"}:
        if field not in checkpoint_fields:
            errors.append(f"checkpoint contract missing required field: {field}")

    return not errors, errors


def dependency_complete(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> bool:
    return all(by_id[dep].get("status") == "COMPLETE" for dep in item.get("depends_on", []))


def readiness_kind(
    item: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
    policy: dict[str, Any],
) -> str | None:
    if not dependency_complete(item, by_id):
        return None
    status = item.get("status")
    if status == "READY":
        return "EXPLICIT_READY"
    auto = policy.get("global", {}).get("waiting_readiness_policy") == "AUTO_WHEN_DEPENDENCIES_COMPLETE"
    if status == "WAITING" and auto and not item.get("external_gate"):
        return "DERIVED_READY"
    return None


def eligible_items(
    queue: dict[str, Any],
    work_state: dict[str, Any] | None = None,
    policy: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    effective = apply_work_state(queue, work_state)
    items = effective.get("items", [])
    by_id = {item["id"]: item for item in items}
    active_policy = policy if policy is not None else load_json(POLICY_PATH)
    eligible: list[dict[str, Any]] = []
    for item in items:
        kind = readiness_kind(item, by_id, active_policy)
        if not kind:
            continue
        planned = dict(item)
        planned["readiness"] = kind
        eligible.append(planned)
    return sorted(eligible, key=lambda x: (x.get("priority", 999999), x["id"]))


def provider_candidates(item: dict[str, Any], registry: dict[str, Any]) -> dict[str, list[str]]:
    capabilities = registry.get("capabilities", {})
    return {
        capability: list(capabilities[capability].get("providers", []))
        for capability in item.get("requires_capabilities", [])
    }


def build_plan(
    queue: dict[str, Any],
    policy: dict[str, Any],
    registry: dict[str, Any],
    max_items: int | None = None,
    work_state: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    eligible = eligible_items(queue, work_state, policy)
    if not eligible:
        return []

    global_max = policy["global"]["max_parallel_work_items"]
    limit = min(max_items or global_max, global_max)

    if eligible[0].get("execution", {}).get("mode") == "SERIAL":
        selected = [eligible[0]]
    else:
        selected: list[dict[str, Any]] = []
        active_locks: set[str] = set()
        for item in eligible:
            if len(selected) >= limit:
                break
            if item.get("execution", {}).get("mode") == "SERIAL":
                continue
            locks = set(item.get("execution", {}).get("locks", []))
            if active_locks & locks:
                continue
            selected.append(item)
            active_locks |= locks

    return [
        {
            "id": item["id"],
            "title": item["title"],
            "workstream": item["workstream"],
            "priority": item["priority"],
            "readiness": item.get("readiness", "EXPLICIT_READY"),
            "execution_profile": item["profile"],
            "execution": item["execution"],
            "requires_capabilities": item.get("requires_capabilities", []),
            "provider_candidates": provider_candidates(item, registry),
            "human_gate": item.get("human_gate", False),
            "completion": item.get("completion", []),
        }
        for item in selected
    ]


def validate_result_payload(result: dict[str, Any], queue: dict[str, Any], policy: dict[str, Any], registry: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in contract.get("required_fields", []):
        if field not in result:
            errors.append(f"missing result field: {field}")
    if errors:
        return errors

    by_id = {item["id"]: item for item in queue.get("items", [])}
    wid = result.get("work_item_id")
    if wid not in by_id:
        errors.append(f"unknown work item: {wid}")
        return errors
    item = by_id[wid]

    if result.get("outcome") not in contract.get("allowed_outcomes", []):
        errors.append(f"invalid outcome: {result.get('outcome')}")
    if result.get("execution_profile") != item.get("profile"):
        errors.append("execution_profile does not match work item")

    attempt = result.get("attempt_no")
    profile = policy.get("profiles", {}).get(item.get("profile"), {})
    if not isinstance(attempt, int) or attempt < 1 or attempt > profile.get("max_attempts", 0):
        errors.append("attempt_no is outside execution profile budget")

    selected = result.get("selected_providers")
    if not isinstance(selected, dict):
        errors.append("selected_providers must be an object keyed by capability")
    else:
        specs = registry.get("capabilities", {})
        for capability in item.get("requires_capabilities", []):
            provider = selected.get(capability)
            if provider not in specs[capability].get("providers", []):
                errors.append(f"provider for {capability} is missing or not registered")

    if result.get("outcome", "").startswith("COMPLETE_") and not result.get("gates"):
        errors.append("complete result must contain gate receipts")
    if result.get("outcome") == "BLOCKED_HUMAN_DECISION" and not result.get("human_decisions"):
        errors.append("human-decision blocker must contain decision package")

    return errors


def validate_checkpoint_payload(payload: dict[str, Any], queue: dict[str, Any], policy: dict[str, Any], checkpoint_contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in checkpoint_contract.get("required_fields", []):
        if field not in payload:
            errors.append(f"missing checkpoint field: {field}")
    if errors:
        return errors

    by_id = {item["id"]: item for item in queue.get("items", [])}
    wid = payload.get("work_item_id")
    if wid not in by_id:
        errors.append(f"unknown work item: {wid}")
        return errors
    item = by_id[wid]
    if payload.get("execution_profile") != item.get("profile"):
        errors.append("checkpoint execution_profile does not match work item")
    if payload.get("stage") not in checkpoint_contract.get("stages", []):
        errors.append(f"invalid checkpoint stage: {payload.get('stage')}")
    profile = policy.get("profiles", {}).get(item.get("profile"), {})
    attempt = payload.get("attempt_no")
    if not isinstance(attempt, int) or attempt < 1 or attempt > profile.get("max_attempts", 0):
        errors.append("checkpoint attempt_no is outside execution profile budget")
    expected_locks = set(item.get("execution", {}).get("locks", []))
    active_locks = set(payload.get("active_locks", []))
    if not active_locks.issubset(expected_locks):
        errors.append("checkpoint contains locks not declared by work item")
    return errors


def validate_runtime_receipts(
    queue: dict[str, Any],
    work_state: dict[str, Any],
    policy: dict[str, Any],
    registry: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for wid, runtime in work_state.get("items", {}).items():
        receipt_ref = runtime.get("receipt")
        if not receipt_ref:
            continue
        path = ROOT / receipt_ref
        if not path.is_file():
            errors.append(f"{wid}: missing receipt {receipt_ref}")
            continue
        receipt = load_json(path)
        if receipt.get("work_item_id") != wid:
            errors.append(f"{wid}: receipt work_item_id mismatch")
            continue
        for error in validate_result_payload(receipt, queue, policy, registry, contract):
            errors.append(f"{wid}: {error}")
        if runtime.get("status") == "COMPLETE" and not str(receipt.get("outcome", "")).startswith("COMPLETE_"):
            errors.append(f"{wid}: COMPLETE runtime state requires a COMPLETE result receipt")
    return errors


def cmd_validate(_: argparse.Namespace) -> int:
    ok, errors = validate()
    payload = {
        "status": "PASS" if ok else "FAIL",
        "queue": str(QUEUE_PATH.relative_to(ROOT)),
        "work_state": str(WORK_STATE_PATH.relative_to(ROOT)),
        "execution_policy": str(POLICY_PATH.relative_to(ROOT)),
        "capability_registry": str(CAPABILITY_PATH.relative_to(ROOT)),
        "result_contract": str(CONTRACT_PATH.relative_to(ROOT)),
        "checkpoint_contract": str(CHECKPOINT_PATH.relative_to(ROOT)),
        "errors": errors,
        "canonical_promotion": "DISABLED",
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if ok else 2


def cmd_validate_receipts(_: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue, policy, registry, contract, _ = load_state()
    receipt_errors = validate_runtime_receipts(queue, load_work_state(), policy, registry, contract)
    print(json.dumps({"status": "PASS" if not receipt_errors else "FAIL", "errors": receipt_errors}, indent=2, ensure_ascii=False))
    return 0 if not receipt_errors else 2


def cmd_status(_: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue, policy, registry, _, _ = load_state()
    work_state = load_work_state()
    effective = apply_work_state(queue, work_state)
    counts: dict[str, int] = {}
    for item in effective["items"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    eligible = eligible_items(queue, work_state, policy)
    plan = build_plan(queue, policy, registry, work_state=work_state)
    print(json.dumps({
        "status": "PASS",
        "queue_status": queue.get("status"),
        "canonical_boundary": queue.get("canonical_boundary"),
        "counts": counts,
        "eligible_count": len(eligible),
        "derived_ready_count": sum(x.get("readiness") == "DERIVED_READY" for x in eligible),
        "next_batch": plan,
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue, policy, registry, _, _ = load_state()
    plan = build_plan(queue, policy, registry, args.max_items, load_work_state())
    status = "READY_FOR_AGENTS" if plan else "NO_ELIGIBLE_WORK"
    print(json.dumps({
        "status": status,
        "parallel_count": len(plan),
        "canonical_promotion": "DISABLED",
        "work_items": plan,
    }, indent=2, ensure_ascii=False))
    return 0


def cmd_next(_: argparse.Namespace) -> int:
    args = argparse.Namespace(max_items=1)
    return cmd_plan(args)


def cmd_runtime_state(_: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue, policy, _, _, _ = load_state()
    effective = apply_work_state(queue, load_work_state())
    by_id = {item["id"]: item for item in effective["items"]}
    payload = {}
    for item in effective["items"]:
        payload[item["id"]] = {
            "status": item["status"],
            "derived_readiness": readiness_kind(item, by_id, policy),
            "receipt": item.get("runtime_state", {}).get("receipt"),
            "checkpoint": item.get("runtime_state", {}).get("checkpoint"),
        }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def result_template(item: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    return {
        "work_item_id": item["id"],
        "outcome": "",
        "execution_profile": item["profile"],
        "attempt_no": 1,
        "repository": "antoniocorsano-boop/N12",
        "branch": "",
        "head_sha": "",
        "input_generations": [],
        "input_fingerprints": [],
        "selected_providers": {
            capability: registry["capabilities"][capability]["providers"][0]
            for capability in item.get("requires_capabilities", [])
        },
        "outputs": [],
        "gates": [],
        "residuals": [],
        "human_decisions": [],
        "checkpoint_id": None,
        "next_eligible_action": "",
    }


def cmd_result_template(args: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue, _, registry, _, _ = load_state()
    by_id = {item["id"]: item for item in queue["items"]}
    if args.work_item_id not in by_id:
        print(json.dumps({"status": "FAIL", "error": "unknown work item"}, indent=2))
        return 2
    print(json.dumps(result_template(by_id[args.work_item_id], registry), indent=2, ensure_ascii=False))
    return 0


def checkpoint_template(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": "",
        "work_item_id": item["id"],
        "execution_profile": item["profile"],
        "attempt_no": 1,
        "stage": "DISCOVER",
        "repository": "antoniocorsano-boop/N12",
        "branch": "",
        "head_sha": "",
        "input_fingerprints": [],
        "completed_steps": [],
        "outputs_so_far": [],
        "active_locks": item.get("execution", {}).get("locks", []),
        "resume_preconditions": ["repository head and input fingerprints still valid"],
        "next_step": "",
    }


def cmd_checkpoint_template(args: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue, _, _, _, _ = load_state()
    by_id = {item["id"]: item for item in queue["items"]}
    if args.work_item_id not in by_id:
        print(json.dumps({"status": "FAIL", "error": "unknown work item"}, indent=2))
        return 2
    print(json.dumps(checkpoint_template(by_id[args.work_item_id]), indent=2, ensure_ascii=False))
    return 0


def cmd_validate_result(args: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue, policy, registry, contract, _ = load_state()
    payload = load_json(Path(args.path))
    payload_errors = validate_result_payload(payload, queue, policy, registry, contract)
    print(json.dumps({"status": "PASS" if not payload_errors else "FAIL", "errors": payload_errors}, indent=2, ensure_ascii=False))
    return 0 if not payload_errors else 2


def cmd_validate_checkpoint(args: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue, policy, _, _, checkpoint_contract = load_state()
    payload = load_json(Path(args.path))
    payload_errors = validate_checkpoint_payload(payload, queue, policy, checkpoint_contract)
    print(json.dumps({"status": "PASS" if not payload_errors else "FAIL", "errors": payload_errors}, indent=2, ensure_ascii=False))
    return 0 if not payload_errors else 2


def cmd_capabilities(_: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    _, _, registry, _, _ = load_state()
    print(json.dumps(registry, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CEW Platform OS deterministic policy-driven orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("validate-receipts")
    p.set_defaults(func=cmd_validate_receipts)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("runtime-state")
    p.set_defaults(func=cmd_runtime_state)

    p = sub.add_parser("plan")
    p.add_argument("--max-items", type=int, default=None)
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("next")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("capabilities")
    p.set_defaults(func=cmd_capabilities)

    p = sub.add_parser("result-template")
    p.add_argument("work_item_id")
    p.set_defaults(func=cmd_result_template)

    p = sub.add_parser("checkpoint-template")
    p.add_argument("work_item_id")
    p.set_defaults(func=cmd_checkpoint_template)

    p = sub.add_parser("validate-result")
    p.add_argument("path")
    p.set_defaults(func=cmd_validate_result)

    p = sub.add_parser("validate-checkpoint")
    p.add_argument("path")
    p.set_defaults(func=cmd_validate_checkpoint)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
