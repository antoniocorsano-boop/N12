#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "automation" / "N12_FOUNDATION_PIPELINE_CONTRACT_v1.json"
QUEUE_PATH = ROOT / "automation" / "N12_FOUNDATION_WORK_QUEUE_v1.json"
RESULT_CONTRACT_PATH = ROOT / "automation" / "N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json"
INBOX_PATH = ROOT / "automation" / "inbox" / "N12_FOUNDATION_AGENT_RESULT.json"
RECEIPT_DIR = ROOT / "automation" / "receipts" / "foundation"
PARENT_QUEUE_PATH = ROOT / "automation" / "N12_WORK_QUEUE_v1.json"

ALLOWED_STATES = {"READY", "IN_PROGRESS", "WAITING", "RESIDUAL", "BLOCKED", "COMPLETE"}
PASS_DECISIONS = {"PASS", "PASS_WITH_WATCH"}
NONPASS_DECISIONS = {"RESIDUAL", "BLOCKED", "CONFLICT"}
PRE_PRIMARY_GATE_ROLES = {
    "FOUNDATION_CARPENTRY_READER_A",
    "FOUNDATION_CARPENTRY_READER_B",
    "FOUNDATION_METRIC_NETWORK_SOLVER",
    "FOUNDATION_TOPOLOGY_BUILDER",
    "FOUNDATION_CONFLICT_ADJUDICATOR",
}
LEGACY_TARGET_TOKENS = {
    "existing_foundation_topology",
    "existing_38_support_count",
    "existing_58_member_count",
    "M0G_geometry",
    "PT_master_coordinates",
    "TAV01A_reinforcement_groups",
    "historical_calculation_topology",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def item_map(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in queue.get("items", [])}


def dependencies_complete(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> bool:
    return all(by_id.get(dep, {}).get("state") == "COMPLETE" for dep in item.get("dependencies", []))


def eligible_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = item_map(queue)
    active = [i for i in queue.get("items", []) if i.get("state") in {"IN_PROGRESS", "RESIDUAL"}]
    if active:
        return sorted(active, key=lambda i: (int(i.get("priority", 999999)), i.get("id", "")))
    candidates = [
        i for i in queue.get("items", [])
        if i.get("state") in {"READY", "WAITING"} and dependencies_complete(i, by_id)
    ]
    return sorted(candidates, key=lambda i: (int(i.get("priority", 999999)), i.get("id", "")))


def selected_item(queue: dict[str, Any]) -> dict[str, Any] | None:
    items = eligible_items(queue)
    return items[0] if items else None


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for p in [CONTRACT_PATH, QUEUE_PATH, RESULT_CONTRACT_PATH, PARENT_QUEUE_PATH]:
        if not p.exists():
            errors.append(f"missing required file: {p.relative_to(ROOT)}")
    if errors:
        return errors, warnings

    try:
        contract = read_json(CONTRACT_PATH)
        queue = read_json(QUEUE_PATH)
        result_contract = read_json(RESULT_CONTRACT_PATH)
        parent_queue = read_json(PARENT_QUEUE_PATH)
    except Exception as exc:
        return [f"invalid JSON: {exc}"], warnings

    if contract.get("queue") != "automation/N12_FOUNDATION_WORK_QUEUE_v1.json":
        errors.append("pipeline contract queue path mismatch")
    if contract.get("result_contract") != "automation/N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json":
        errors.append("pipeline contract result-contract path mismatch")
    if result_contract.get("inbox") != "automation/inbox/N12_FOUNDATION_AGENT_RESULT.json":
        errors.append("result contract inbox mismatch")
    if result_contract.get("max_work_items_per_result") != 1:
        errors.append("result contract must enforce one work item per result")

    items = queue.get("items", [])
    ids = [i.get("id") for i in items]
    if not items:
        errors.append("foundation work queue is empty")
    if len(ids) != len(set(ids)):
        errors.append("duplicate foundation work item id")
    by_id = item_map(queue)
    for item in items:
        iid = item.get("id", "<missing>")
        if item.get("state") not in ALLOWED_STATES:
            errors.append(f"{iid}: invalid state {item.get('state')}")
        if not item.get("agent_role"):
            errors.append(f"{iid}: missing agent_role")
        if not item.get("target_outputs"):
            errors.append(f"{iid}: target_outputs empty")
        unknown = [d for d in item.get("dependencies", []) if d not in by_id]
        if unknown:
            errors.append(f"{iid}: unknown dependencies {unknown}")
        if iid in item.get("dependencies", []):
            errors.append(f"{iid}: self dependency")
        if item.get("agent_role") in PRE_PRIMARY_GATE_ROLES:
            allowed = set(item.get("allowed_inputs", []))
            leaked = [x for x in allowed if any(tok in x for tok in LEGACY_TARGET_TOKENS)]
            if leaked:
                errors.append(f"{iid}: pre-gate allowed_inputs leak legacy target context: {leaked}")
            forbidden = set(item.get("forbidden_context", []))
            missing_barriers = sorted(LEGACY_TARGET_TOKENS - forbidden)
            if item.get("agent_role") != "FOUNDATION_CONFLICT_ADJUDICATOR" and missing_barriers:
                warnings.append(f"{iid}: not all legacy barrier tokens are explicit: {missing_barriers}")

    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            errors.append(f"dependency cycle at {node}")
            return
        visiting.add(node)
        for dep in by_id.get(node, {}).get("dependencies", []):
            visit(dep)
        visiting.remove(node)
        visited.add(node)
    for node in by_id:
        visit(node)

    parent_id = contract.get("parent_work_item")
    parent_items = {i.get("id"): i for i in parent_queue.get("items", [])}
    if parent_id not in parent_items:
        errors.append(f"parent queue missing work item {parent_id}")
    else:
        parent = parent_items[parent_id]
        required_targets = {
            "data/canonical/M1F_PRIMARY_GEOMETRY_GATE_v1.csv",
            "data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv",
        }
        if not required_targets.issubset(set(parent.get("target_outputs", []))):
            errors.append("parent FPEP work item does not require both primary and release gates")

    m1f = parent_items.get("M1F-FOUNDATION-MODEL")
    if m1f:
        if parent_id not in set(m1f.get("dependencies", [])):
            errors.append("M1F-FOUNDATION-MODEL does not depend on FPEP parent work item")
        for required in [
            "data/canonical/M1F_PRIMARY_GEOMETRY_GATE_v1.csv",
            "data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv",
        ]:
            if required not in set(m1f.get("required_inputs", [])):
                errors.append(f"M1F-FOUNDATION-MODEL missing required FPEP input {required}")

    return errors, warnings


def build_status() -> dict[str, Any]:
    errors, warnings = validate()
    queue = read_json(QUEUE_PATH) if QUEUE_PATH.exists() else {"items": []}
    selected = selected_item(queue) if not errors else None
    incomplete = [i for i in queue.get("items", []) if i.get("state") != "COMPLETE"]
    decision = "FAIL_STOP" if errors else ("READY_FOR_AGENT" if selected else ("COMPLETE" if not incomplete else "BLOCKED_DEPENDENCY"))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_id": read_json(CONTRACT_PATH).get("pipeline_id") if CONTRACT_PATH.exists() else None,
        "decision": decision,
        "selected_work_item": selected,
        "errors": errors,
        "warnings": warnings,
        "completion": [
            {"id": i.get("id"), "state": i.get("state"), "dependencies": i.get("dependencies", [])}
            for i in sorted(queue.get("items", []), key=lambda x: int(x.get("priority", 999999)))
        ],
    }


def make_task() -> dict[str, Any]:
    status = build_status()
    if status["decision"] != "READY_FOR_AGENT":
        return status
    item = status["selected_work_item"]
    return {
        "pipeline_id": read_json(CONTRACT_PATH)["pipeline_id"],
        "work_item_id": item["id"],
        "agent_role": item["agent_role"],
        "allowed_inputs": item.get("allowed_inputs", []),
        "forbidden_context": item.get("forbidden_context", []),
        "target_outputs": item.get("target_outputs", []),
        "semantic_gate": item.get("semantic_gate"),
        "instructions": [
            "Use only allowed_inputs plus the immutable primary evidence explicitly referenced by those inputs.",
            "Do not search for or load forbidden_context to improve apparent consistency.",
            "Persist residuals instead of filling gaps by analogy, symmetry or target-count matching.",
            "Return exactly one result packet conforming to automation/N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json."
        ],
    }


def validate_result(result: dict[str, Any], queue: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rc = read_json(RESULT_CONTRACT_PATH)
    for field in rc.get("required_fields", []):
        if field not in result:
            errors.append(f"missing result field: {field}")
    selected = selected_item(queue)
    if not selected:
        errors.append("no eligible FPEP work item")
        return errors
    if result.get("work_item_id") != selected.get("id"):
        errors.append(f"result work_item_id {result.get('work_item_id')} != selected {selected.get('id')}")
    if result.get("agent_role") != selected.get("agent_role"):
        errors.append("agent_role does not match selected queue item")
    if result.get("pipeline_id") != read_json(CONTRACT_PATH).get("pipeline_id"):
        errors.append("pipeline_id mismatch")
    if result.get("decision") not in set(rc.get("allowed_decisions", [])):
        errors.append(f"invalid decision {result.get('decision')}")
    if result.get("semantic_gate") not in set(rc.get("allowed_semantic_gate_states", [])):
        errors.append(f"invalid semantic_gate {result.get('semantic_gate')}")
    if set(result.get("target_outputs", [])) != set(selected.get("target_outputs", [])):
        errors.append("target_outputs do not exactly match selected work item")

    att = result.get("information_barrier_attestation", {})
    for key, required in rc.get("information_barrier_attestation_required", {}).items():
        if required and att.get(key) is not True:
            errors.append(f"information barrier attestation failed: {key}")

    decision = result.get("decision")
    if decision in PASS_DECISIONS:
        for rel in selected.get("target_outputs", []):
            if not (ROOT / rel).exists():
                errors.append(f"missing target output for PASS: {rel}")
        for rel in result.get("audit_paths", []):
            if not (ROOT / rel).exists():
                errors.append(f"missing audit path: {rel}")
        if decision == "PASS" and result.get("semantic_gate") != "PASS":
            errors.append("PASS requires semantic_gate PASS")
        if decision == "PASS_WITH_WATCH" and result.get("semantic_gate") not in {"PASS", "WATCH"}:
            errors.append("PASS_WITH_WATCH requires semantic_gate PASS or WATCH")
        if decision == "PASS":
            blocking = [r for r in result.get("residuals", []) if r.get("blocking") is True]
            if blocking:
                errors.append("PASS result contains blocking residuals")
    return errors


def ingest() -> dict[str, Any]:
    errors, warnings = validate()
    if errors:
        return {"decision": "FAIL_STOP", "errors": errors, "warnings": warnings}
    if not INBOX_PATH.exists():
        return {"decision": "BLOCKED_INPUT", "errors": [f"missing inbox {INBOX_PATH.relative_to(ROOT)}"]}
    queue = read_json(QUEUE_PATH)
    result = read_json(INBOX_PATH)
    result_errors = validate_result(result, queue)
    if result_errors:
        return {"decision": "FAIL_STOP", "errors": result_errors}

    item = item_map(queue)[result["work_item_id"]]
    decision = result["decision"]
    if decision in PASS_DECISIONS:
        item["state"] = "COMPLETE"
        item["completed_at"] = datetime.now(timezone.utc).isoformat()
        item["completion_decision"] = decision
    elif decision == "RESIDUAL":
        item["state"] = "RESIDUAL"
    else:
        item["state"] = "BLOCKED"
        item["blocking_decision"] = decision
    item["last_run_id"] = result.get("run_id")

    write_json(QUEUE_PATH, queue)
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = RECEIPT_DIR / f"{item['id']}_{stamp}.json"
    receipt = {
        "schema_version": "1.0",
        "pipeline_id": result.get("pipeline_id"),
        "work_item_id": item["id"],
        "decision": decision,
        "semantic_gate": result.get("semantic_gate"),
        "run_id": result.get("run_id"),
        "result_sha256": sha256_file(INBOX_PATH),
        "target_outputs": result.get("target_outputs", []),
        "audit_paths": result.get("audit_paths", []),
        "residuals": result.get("residuals", []),
        "information_barrier_attestation": result.get("information_barrier_attestation", {}),
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(receipt_path, receipt)
    archive = RECEIPT_DIR / "results"
    archive.mkdir(parents=True, exist_ok=True)
    shutil.copy2(INBOX_PATH, archive / f"{item['id']}_{stamp}_result.json")
    INBOX_PATH.unlink()
    return {
        "decision": "PASS_ADVANCE" if decision == "PASS" else ("PASS_WITH_WATCH_ADVANCE" if decision == "PASS_WITH_WATCH" else decision),
        "work_item_id": item["id"],
        "receipt": str(receipt_path.relative_to(ROOT)),
        "next": selected_item(queue),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="N12 FPEP foundation primary-evidence sub-orchestrator")
    parser.add_argument("command", choices=["validate", "status", "make-task", "ingest"])
    args = parser.parse_args()
    if args.command == "validate":
        errors, warnings = validate()
        print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
        return 0 if not errors else 1
    if args.command == "status":
        status = build_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0 if status["decision"] != "FAIL_STOP" else 1
    if args.command == "make-task":
        task = make_task()
        print(json.dumps(task, indent=2, ensure_ascii=False))
        return 0 if task.get("decision") != "FAIL_STOP" else 1
    result = ingest()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("decision") not in {"FAIL_STOP"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
