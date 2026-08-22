#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "automation" / "N12_AUTOMATION_CONTRACT_v1.json"
QUEUE_PATH = ROOT / "automation" / "N12_WORK_QUEUE_v1.json"
MANIFEST_PATH = ROOT / "knowledge" / "KNOWLEDGE_MANIFEST.json"
STATE_PATH = ROOT / "knowledge" / "CURRENT_STATE.json"
BASE_REGISTRY_PATH = ROOT / "knowledge" / "ARTIFACT_REGISTRY.csv"

BLOCKING_ARTIFACT_STATES = {
    "CONFLICT", "REOPENED", "SUPERSEDED", "TOMBSTONE", "HISTORICAL_ONLY", "SUSPENDED"
}
ALLOWED_WORK_ITEM_STATES = {
    "READY", "WAITING", "IN_PROGRESS", "CANDIDATE", "RESIDUAL", "BLOCKED", "COMPLETE", "SUPERSEDED"
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rel_exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def load_effective_registry(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    rows = read_csv(BASE_REGISTRY_PATH)
    by_path = {r.get("path", "").strip(): r for r in rows}
    patch_rel = manifest.get("artifact_registry_patch")
    if patch_rel and rel_exists(patch_rel):
        for r in read_csv(ROOT / patch_rel):
            by_path[r.get("path", "").strip()] = r
    return by_path


def validate_contract() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required = [CONTRACT_PATH, QUEUE_PATH, MANIFEST_PATH, STATE_PATH, BASE_REGISTRY_PATH]
    for p in required:
        if not p.exists():
            errors.append(f"missing required file: {p.relative_to(ROOT)}")
    if errors:
        return errors, warnings

    try:
        contract = read_json(CONTRACT_PATH)
        queue = read_json(QUEUE_PATH)
        manifest = read_json(MANIFEST_PATH)
        state = read_json(STATE_PATH)
    except Exception as exc:
        return [f"invalid JSON: {exc}"], warnings

    if contract.get("entrypoint") != "scripts/n12_orchestrator.py":
        errors.append("automation contract entrypoint must be scripts/n12_orchestrator.py")
    if contract.get("queue") != "automation/N12_WORK_QUEUE_v1.json":
        errors.append("automation contract queue path mismatch")
    if contract.get("canonical_branch") != manifest.get("canonical_branch"):
        errors.append("automation contract branch differs from knowledge manifest canonical_branch")

    stage_ids = [s.get("id") for s in contract.get("stages", [])]
    if not stage_ids or len(stage_ids) != len(set(stage_ids)):
        errors.append("automation stages missing or duplicated")
    stage_set = set(stage_ids)

    items = queue.get("items", [])
    item_ids = [i.get("id") for i in items]
    if not items:
        errors.append("work queue is empty")
    if len(item_ids) != len(set(item_ids)):
        errors.append("duplicate work item id in queue")
    item_set = set(item_ids)

    for item in items:
        iid = item.get("id", "<missing>")
        state_value = item.get("state")
        if state_value not in ALLOWED_WORK_ITEM_STATES:
            errors.append(f"{iid}: invalid state={state_value}")
        if item.get("stage") not in stage_set:
            errors.append(f"{iid}: unknown stage={item.get('stage')}")
        deps = item.get("dependencies", [])
        unknown_deps = [d for d in deps if d not in item_set]
        if unknown_deps:
            errors.append(f"{iid}: unknown dependencies={unknown_deps}")
        if iid in deps:
            errors.append(f"{iid}: self dependency")
        if not item.get("target_outputs"):
            errors.append(f"{iid}: target_outputs is empty")
        for rel in item.get("required_inputs", []):
            if not rel_exists(rel):
                warnings.append(f"{iid}: input currently missing: {rel}")

    # Detect simple dependency cycles.
    graph = {i["id"]: list(i.get("dependencies", [])) for i in items if i.get("id")}
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
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)

    if manifest.get("current_gate") != state.get("gate"):
        errors.append("manifest/state gate mismatch")

    return errors, warnings


def item_map(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {i["id"]: i for i in queue.get("items", [])}


def dependencies_complete(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> bool:
    return all(by_id[d].get("state") == "COMPLETE" for d in item.get("dependencies", []))


def missing_inputs(item: dict[str, Any]) -> list[str]:
    return [rel for rel in item.get("required_inputs", []) if not rel_exists(rel)]


def output_status(item: dict[str, Any], registry: dict[str, dict[str, str]]) -> dict[str, Any]:
    outputs = item.get("target_outputs", [])
    detail = []
    for rel in outputs:
        exists = rel_exists(rel)
        reg = registry.get(rel)
        detail.append({
            "path": rel,
            "exists": exists,
            "registered": bool(reg),
            "authority": reg.get("authority") if reg else None,
            "status": reg.get("status") if reg else None,
            "may_feed_canonical": reg.get("may_feed_canonical") if reg else None,
        })
    complete = bool(detail) and all(
        d["exists"]
        and d["registered"]
        and d["authority"] in {"CANONICAL", "DERIVED"}
        and d["status"] not in BLOCKING_ARTIFACT_STATES
        and d["may_feed_canonical"] in {"YES", "CONDITIONAL"}
        for d in detail
    )
    candidate = bool(detail) and all(d["exists"] for d in detail) and not complete
    return {"detail": detail, "complete_detected": complete, "candidate_detected": candidate}


def choose_next(queue: dict[str, Any], registry: dict[str, dict[str, str]]) -> tuple[dict[str, Any] | None, str]:
    by_id = item_map(queue)
    ordered = sorted(queue.get("items", []), key=lambda i: (int(i.get("priority", 999999)), i.get("id", "")))

    # First honor an explicit active state.
    for item in ordered:
        if item.get("state") in {"IN_PROGRESS", "CANDIDATE", "RESIDUAL"}:
            return item, item.get("state")

    for item in ordered:
        if item.get("state") != "READY":
            continue
        if not dependencies_complete(item, by_id):
            continue
        if missing_inputs(item):
            continue
        return item, "READY"

    # Detect items whose outputs have already become promotable even if queue was not advanced.
    for item in ordered:
        if item.get("state") in {"WAITING", "READY"}:
            out = output_status(item, registry)
            if out["complete_detected"]:
                return item, "COMPLETE_DETECTED"

    return None, "NO_ELIGIBLE_ITEM"


def run_check(name: str) -> dict[str, Any]:
    commands = {
        "knowledge_contracts": [sys.executable, "scripts/validate_knowledge_system.py"],
        "agent_bootstrap": [sys.executable, "scripts/agent_bootstrap.py"],
        "semantic_registry": [sys.executable, "skills/pt-carpentry-reader/runner.py", "validate"],
        "pt_raster_status": [sys.executable, "skills/pt-raster-grid-reconstructor/runner.py", "status"],
    }
    cmd = commands.get(name)
    if not cmd:
        return {"check": name, "status": "SKIPPED_UNKNOWN_CHECK", "returncode": None, "stdout": "", "stderr": ""}
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "check": name,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
    }


def build_status(run_checks: bool = False) -> dict[str, Any]:
    contract = read_json(CONTRACT_PATH)
    queue = read_json(QUEUE_PATH)
    manifest = read_json(MANIFEST_PATH)
    state = read_json(STATE_PATH)
    registry = load_effective_registry(manifest)
    errors, warnings = validate_contract()

    selected, selected_reason = choose_next(queue, registry)
    by_id = item_map(queue)

    if errors:
        decision = "FAIL_STOP"
    elif selected is None:
        incomplete = [i for i in queue.get("items", []) if i.get("state") not in {"COMPLETE", "SUPERSEDED"}]
        decision = "COMPLETE" if not incomplete else "BLOCKED_DEPENDENCY"
    else:
        out = output_status(selected, registry)
        miss = missing_inputs(selected)
        deps_ok = dependencies_complete(selected, by_id)
        if selected.get("state") == "RESIDUAL":
            decision = "RESIDUAL_REVIEW"
        elif not deps_ok:
            decision = "BLOCKED_DEPENDENCY"
        elif miss:
            decision = "BLOCKED_INPUT"
        elif out["complete_detected"]:
            decision = "PASS_ADVANCE"
        elif out["candidate_detected"] or selected.get("state") == "CANDIDATE":
            decision = "READY_FOR_AGENT"
        else:
            decision = "READY_FOR_AGENT"

    checks: list[dict[str, Any]] = []
    if run_checks and not errors:
        for name in ["knowledge_contracts", "agent_bootstrap", "semantic_registry", "pt_raster_status"]:
            checks.append(run_check(name))
        if any(c.get("status") == "FAIL" for c in checks):
            decision = "FAIL_STOP"

    selected_payload = None
    if selected:
        selected_payload = {
            **selected,
            "dependencies_complete": dependencies_complete(selected, by_id),
            "missing_inputs": missing_inputs(selected),
            "outputs": output_status(selected, registry),
            "selection_reason": selected_reason,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_id": contract.get("system_id"),
        "branch": manifest.get("canonical_branch"),
        "gate": state.get("gate"),
        "state_status": state.get("status"),
        "decision": decision,
        "selected_work_item": selected_payload,
        "contract_errors": errors,
        "contract_warnings": warnings,
        "checks": checks,
        "rules": {
            "no_blind_extrusion": contract.get("global_rules", {}).get("no_blind_extrusion"),
            "no_cross_storey_section_copy": contract.get("global_rules", {}).get("no_cross_storey_section_copy"),
            "no_cross_storey_beam_copy": contract.get("global_rules", {}).get("no_cross_storey_beam_copy"),
            "no_mis_to_doc_promotion": contract.get("global_rules", {}).get("no_mis_to_doc_promotion"),
            "reopen_smallest_conflicting_claim_only": contract.get("global_rules", {}).get("reopen_smallest_conflicting_claim_only"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="N12 controlled cyclic structural-analysis orchestrator")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="validate automation contract and persistent work queue")
    sub.add_parser("status", help="print current cycle decision and next eligible work item")
    p_run = sub.add_parser("run", help="run deterministic gates and emit a cycle report")
    p_run.add_argument("--output", default="analysis/automation/N12_CYCLE_REPORT.json")
    args = parser.parse_args()

    if args.cmd == "validate":
        errors, warnings = validate_contract()
        if errors:
            print("N12_AUTOMATION_CONTRACT = FAIL")
            for e in errors:
                print(f"ERROR: {e}")
            for w in warnings:
                print(f"WARN: {w}")
            return 1
        print("N12_AUTOMATION_CONTRACT = PASS")
        for w in warnings:
            print(f"WARN: {w}")
        print("Cycle contract, queue dependencies and current knowledge gate are coherent.")
        return 0

    if args.cmd == "status":
        print(json.dumps(build_status(run_checks=False), indent=2, ensure_ascii=False))
        return 0

    report = build_status(run_checks=True)
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["decision"] == "FAIL_STOP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
