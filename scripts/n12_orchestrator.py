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


def registry_patch_rels(manifest: dict[str, Any]) -> list[str]:
    rels: list[str] = []
    legacy = manifest.get("artifact_registry_patch")
    if legacy:
        rels.append(legacy)
    for rel in manifest.get("artifact_registry_patches", []) or []:
        if rel and rel not in rels:
            rels.append(rel)
    return rels


def load_effective_registry(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    by_path = {r.get("path", "").strip(): r for r in read_csv(BASE_REGISTRY_PATH)}
    for patch_rel in registry_patch_rels(manifest):
        if rel_exists(patch_rel):
            for row in read_csv(ROOT / patch_rel):
                by_path[row.get("path", "").strip()] = row
    return by_path


def output_status(item: dict[str, Any], registry: dict[str, dict[str, str]]) -> dict[str, Any]:
    detail: list[dict[str, Any]] = []
    for rel in item.get("target_outputs", []):
        reg = registry.get(rel)
        detail.append({
            "path": rel,
            "exists": rel_exists(rel),
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


def item_effectively_complete(item: dict[str, Any], registry: dict[str, dict[str, str]]) -> bool:
    return item.get("state") == "COMPLETE" or output_status(item, registry)["complete_detected"]


def missing_inputs(item: dict[str, Any]) -> list[str]:
    return [rel for rel in item.get("required_inputs", []) if not rel_exists(rel)]


def item_map(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in queue.get("items", [])}


def dependencies_complete(
    item: dict[str, Any], by_id: dict[str, dict[str, Any]], registry: dict[str, dict[str, str]]
) -> bool:
    return all(item_effectively_complete(by_id[dep], registry) for dep in item.get("dependencies", []))


def validate_contract() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for path in [CONTRACT_PATH, QUEUE_PATH, MANIFEST_PATH, STATE_PATH, BASE_REGISTRY_PATH]:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")
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
    if manifest.get("current_gate") != state.get("gate"):
        errors.append("manifest/state gate mismatch")

    stage_ids = [stage.get("id") for stage in contract.get("stages", [])]
    if not stage_ids or len(stage_ids) != len(set(stage_ids)):
        errors.append("automation stages missing or duplicated")
    stage_set = set(stage_ids)

    items = queue.get("items", [])
    ids = [item.get("id") for item in items]
    if not items:
        errors.append("work queue is empty")
    if len(ids) != len(set(ids)):
        errors.append("duplicate work item id in queue")
    id_set = set(ids)

    for item in items:
        iid = item.get("id", "<missing>")
        if item.get("state") not in ALLOWED_WORK_ITEM_STATES:
            errors.append(f"{iid}: invalid state={item.get('state')}")
        if item.get("stage") not in stage_set:
            errors.append(f"{iid}: unknown stage={item.get('stage')}")
        deps = item.get("dependencies", [])
        unknown = [dep for dep in deps if dep not in id_set]
        if unknown:
            errors.append(f"{iid}: unknown dependencies={unknown}")
        if iid in deps:
            errors.append(f"{iid}: self dependency")
        if not item.get("target_outputs"):
            errors.append(f"{iid}: target_outputs is empty")

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
            visit(dep)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)

    return errors, warnings


def choose_next(
    queue: dict[str, Any], registry: dict[str, dict[str, str]]
) -> tuple[dict[str, Any] | None, str]:
    by_id = item_map(queue)
    ordered = sorted(queue.get("items", []), key=lambda item: (int(item.get("priority", 999999)), item.get("id", "")))

    # Explicit human/agent states take precedence.
    for item in ordered:
        if item.get("state") in {"IN_PROGRESS", "CANDIDATE", "RESIDUAL"} and not item_effectively_complete(item, registry):
            return item, item.get("state")

    # READY and WAITING items are auto-released when dependencies have canonical outputs.
    for item in ordered:
        if item.get("state") in {"BLOCKED", "SUPERSEDED", "COMPLETE"}:
            continue
        if item_effectively_complete(item, registry):
            continue
        if not dependencies_complete(item, by_id, registry):
            continue
        if missing_inputs(item):
            continue
        if item.get("state") in {"READY", "WAITING"}:
            reason = "READY" if item.get("state") == "READY" else "AUTO_RELEASED_WAITING"
            return item, reason

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
    by_id = item_map(queue)
    selected, selection_reason = choose_next(queue, registry)

    if errors:
        decision = "FAIL_STOP"
    elif selected:
        outputs = output_status(selected, registry)
        if selected.get("state") == "RESIDUAL":
            decision = "RESIDUAL_REVIEW"
        elif outputs["candidate_detected"] or selected.get("state") == "CANDIDATE":
            decision = "READY_FOR_AGENT"
        else:
            decision = "READY_FOR_AGENT"
    else:
        incomplete = [item for item in queue.get("items", []) if not item_effectively_complete(item, registry) and item.get("state") != "SUPERSEDED"]
        decision = "COMPLETE" if not incomplete else "BLOCKED_DEPENDENCY"

    checks: list[dict[str, Any]] = []
    if run_checks and not errors:
        for check_name in ["knowledge_contracts", "agent_bootstrap", "semantic_registry", "pt_raster_status"]:
            checks.append(run_check(check_name))
        if any(check.get("status") == "FAIL" for check in checks):
            decision = "FAIL_STOP"

    selected_payload = None
    if selected:
        selected_payload = {
            **selected,
            "selection_reason": selection_reason,
            "dependencies_complete": dependencies_complete(selected, by_id, registry),
            "missing_inputs": missing_inputs(selected),
            "outputs": output_status(selected, registry),
        }

    completion = []
    for item in sorted(queue.get("items", []), key=lambda i: int(i.get("priority", 999999))):
        completion.append({
            "id": item.get("id"),
            "declared_state": item.get("state"),
            "effective_complete": item_effectively_complete(item, registry),
            "dependencies_complete": dependencies_complete(item, by_id, registry),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system_id": contract.get("system_id"),
        "branch": manifest.get("canonical_branch"),
        "gate": state.get("gate"),
        "state_status": state.get("status"),
        "decision": decision,
        "selected_work_item": selected_payload,
        "queue_completion": completion,
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
    run_parser = sub.add_parser("run", help="run deterministic gates and emit a cycle report")
    run_parser.add_argument("--output", default="analysis/automation/N12_CYCLE_REPORT.json")
    args = parser.parse_args()

    if args.cmd == "validate":
        errors, warnings = validate_contract()
        if errors:
            print("N12_AUTOMATION_CONTRACT = FAIL")
            for error in errors:
                print(f"ERROR: {error}")
            for warning in warnings:
                print(f"WARN: {warning}")
            return 1
        print("N12_AUTOMATION_CONTRACT = PASS")
        for warning in warnings:
            print(f"WARN: {warning}")
        print("Cycle contract, queue dependencies and current knowledge gate are coherent.")
        return 0

    if args.cmd == "status":
        print(json.dumps(build_status(run_checks=False), indent=2, ensure_ascii=False))
        return 0

    report = build_status(run_checks=True)
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["decision"] == "FAIL_STOP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
