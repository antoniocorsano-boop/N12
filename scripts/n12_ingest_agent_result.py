#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import n12_orchestrator

ROOT = Path(__file__).resolve().parents[1]
RESULT_CONTRACT_PATH = ROOT / "automation" / "N12_AGENT_RESULT_CONTRACT_v1.json"
QUEUE_PATH = ROOT / "automation" / "N12_WORK_QUEUE_v1.json"
STATE_PATH = ROOT / "knowledge" / "CURRENT_STATE.json"
MANIFEST_PATH = ROOT / "knowledge" / "KNOWLEDGE_MANIFEST.json"
DEFAULT_INPUT = ROOT / "automation" / "inbox" / "N12_AGENT_RESULT.json"
RECEIPT_DIR = ROOT / "automation" / "receipts"
FPEP_WRAPPER_ID = "M1F-PRIMARY-GEOMETRY-REVALIDATION"
FPEP_QUEUE_PATH = ROOT / "automation" / "N12_FOUNDATION_WORK_QUEUE_v1.json"
FPEP_RECEIPT_DIR = ROOT / "automation" / "receipts" / "foundation"
FPEP_COMPLETION_ITEM = "FPEP-P12-RELEASE-AUDIT"
FPEP_PRIMARY_GATE = ROOT / "data" / "canonical" / "M1F_PRIMARY_GEOMETRY_GATE_v1.csv"
FPEP_RELEASE_GATE = ROOT / "data" / "canonical" / "M1F_FPEP_RELEASE_GATE_v1.csv"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def run_validator(command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
    }


def run_required_validators() -> list[dict[str, Any]]:
    checks = [
        run_validator([sys.executable, "scripts/validate_knowledge_system.py"]),
        run_validator([sys.executable, "scripts/n12_orchestrator.py", "validate"]),
        run_validator([sys.executable, "skills/pt-carpentry-reader/runner.py", "validate"]),
    ]
    if FPEP_QUEUE_PATH.exists():
        checks.append(run_validator([sys.executable, "scripts/validate_foundation_pipeline.py"]))
        checks.append(run_validator([sys.executable, "scripts/n12_foundation_orchestrator.py", "validate"]))
    return checks


def selected_context() -> tuple[dict[str, Any] | None, dict[str, Any], dict[str, dict[str, str]]]:
    status = n12_orchestrator.build_status(run_checks=False)
    manifest = read_json(MANIFEST_PATH)
    registry = n12_orchestrator.load_effective_registry(manifest)
    return status.get("selected_work_item"), status, registry


def validate_fpep_wrapper_completion(audit_paths: list[str]) -> list[str]:
    errors: list[str] = []
    if not FPEP_QUEUE_PATH.exists():
        return ["FPEP wrapper cannot be promoted: foundation subqueue is missing"]
    try:
        fpep_queue = read_json(FPEP_QUEUE_PATH)
    except Exception as exc:
        return [f"FPEP wrapper cannot be promoted: invalid foundation subqueue: {exc}"]

    items = fpep_queue.get("items", [])
    by_id = {item.get("id"): item for item in items}
    incomplete = [item.get("id") for item in items if item.get("state") != "COMPLETE"]
    if incomplete:
        errors.append(f"FPEP wrapper cannot be promoted before all sub-items are COMPLETE: {incomplete}")

    final_item = by_id.get(FPEP_COMPLETION_ITEM)
    if not final_item:
        errors.append(f"FPEP completion item missing: {FPEP_COMPLETION_ITEM}")
    elif final_item.get("completion_decision") not in {"PASS", "PASS_WITH_WATCH"}:
        errors.append(
            f"FPEP completion item lacks a passing completion_decision: {final_item.get('completion_decision')}"
        )

    if not FPEP_PRIMARY_GATE.exists():
        errors.append(f"FPEP primary geometry gate missing: {FPEP_PRIMARY_GATE.relative_to(ROOT)}")
    if not FPEP_RELEASE_GATE.exists():
        errors.append(f"FPEP release gate missing: {FPEP_RELEASE_GATE.relative_to(ROOT)}")

    receipt_candidates = sorted(FPEP_RECEIPT_DIR.glob(f"{FPEP_COMPLETION_ITEM}_*.json")) if FPEP_RECEIPT_DIR.exists() else []
    if not receipt_candidates:
        errors.append("FPEP P12 completion receipt is missing")
    else:
        accepted_receipts = {p.relative_to(ROOT).as_posix() for p in receipt_candidates}
        if not accepted_receipts.intersection(set(audit_paths)):
            errors.append(
                "parent FPEP PASS must cite the P12 foundation receipt in audit_paths; direct top-level fabrication is forbidden"
            )
    return errors


def validate_result(result: dict[str, Any]) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    contract = read_json(RESULT_CONTRACT_PATH)
    selected, status, registry = selected_context()

    for field in contract.get("required_fields", []):
        if field not in result:
            errors.append(f"missing required result field: {field}")

    if result.get("schema_version") != contract.get("schema_version"):
        errors.append(
            f"result schema_version={result.get('schema_version')} does not match contract={contract.get('schema_version')}"
        )

    decision = result.get("decision")
    if decision not in set(contract.get("allowed_decisions", [])):
        errors.append(f"invalid decision={decision}")

    semantic_gate = result.get("semantic_gate")
    if semantic_gate not in set(contract.get("allowed_semantic_gate_states", [])):
        errors.append(f"invalid semantic_gate={semantic_gate}")

    if not selected:
        errors.append(f"no selected work item is currently ingestible; orchestrator decision={status.get('decision')}")
        return errors, warnings, {"selected": None, "status": status}

    if result.get("work_item_id") != selected.get("id"):
        errors.append(
            f"result work_item_id={result.get('work_item_id')} differs from selected={selected.get('id')}"
        )

    if result.get("source_sheet") != selected.get("source_sheet"):
        errors.append(
            f"result source_sheet={result.get('source_sheet')} differs from selected={selected.get('source_sheet')}"
        )

    expected_outputs = list(selected.get("target_outputs", []))
    actual_outputs = result.get("target_outputs")
    if not isinstance(actual_outputs, list):
        errors.append("target_outputs must be a list")
    elif actual_outputs != expected_outputs:
        errors.append(f"target_outputs must exactly match queue item: expected={expected_outputs} actual={actual_outputs}")

    provenance_summary = result.get("provenance_summary")
    allowed_provenance = set(contract.get("allowed_provenance", []))
    if not isinstance(provenance_summary, dict):
        errors.append("provenance_summary must be an object")
    else:
        for key, value in provenance_summary.items():
            if key not in allowed_provenance:
                errors.append(f"unsupported provenance key={key}")
            if not isinstance(value, int) or value < 0:
                errors.append(f"provenance_summary[{key}] must be a non-negative integer")

    residuals = result.get("residuals")
    if not isinstance(residuals, list):
        errors.append("residuals must be a list")
        residuals = []

    audit_paths = result.get("audit_paths")
    if not isinstance(audit_paths, list):
        errors.append("audit_paths must be a list")
        audit_paths = []

    if decision in {"PASS", "PASS_WITH_WATCH"}:
        allowed_gate = (
            set(contract.get("pass_rules", {}).get("semantic_gate_for_PASS", []))
            if decision == "PASS"
            else set(contract.get("pass_rules", {}).get("semantic_gate_for_PASS_WITH_WATCH", []))
        )
        if semantic_gate not in allowed_gate:
            errors.append(f"decision={decision} incompatible with semantic_gate={semantic_gate}")
        if not audit_paths:
            errors.append("PASS/PASS_WITH_WATCH requires at least one audit_path")
        for rel in audit_paths:
            if not isinstance(rel, str) or not (ROOT / rel).exists():
                errors.append(f"audit path missing: {rel}")
        if selected.get("id") == FPEP_WRAPPER_ID:
            errors.extend(validate_fpep_wrapper_completion(audit_paths))
        outputs = n12_orchestrator.output_status(selected, registry)
        if not outputs.get("complete_detected"):
            errors.append(
                "target output is not canonically ingestible: it must exist, be registered, have CANONICAL/DERIVED authority, non-blocking status and may_feed_canonical YES/CONDITIONAL"
            )
    elif decision in {"RESIDUAL", "BLOCKED", "CONFLICT"}:
        if not residuals:
            errors.append(f"decision={decision} requires at least one residual entry")
        if semantic_gate == "PASS":
            warnings.append(f"decision={decision} with semantic_gate=PASS is unusual; result will not be promoted")

    context = {
        "selected": selected,
        "status": status,
        "output_status": n12_orchestrator.output_status(selected, registry),
    }
    return errors, warnings, context


def update_state_for_result(
    state: dict[str, Any], queue: dict[str, Any], registry: dict[str, dict[str, str]], result: dict[str, Any], receipt_rel: str
) -> dict[str, Any] | None:
    by_id = n12_orchestrator.item_map(queue)
    item = by_id[result["work_item_id"]]
    decision = result["decision"]
    now = utc_now()
    now_iso = now.isoformat()

    if decision in {"PASS", "PASS_WITH_WATCH"}:
        item["state"] = "COMPLETE"
        item["completed_at"] = now_iso
        item["completion_decision"] = decision
        item["result_receipt"] = receipt_rel
    elif decision == "RESIDUAL":
        item["state"] = "RESIDUAL"
        item["last_result_at"] = now_iso
        item["result_receipt"] = receipt_rel
    else:
        item["state"] = "BLOCKED"
        item["last_result_at"] = now_iso
        item["result_receipt"] = receipt_rel

    queue["updated_at"] = now.date().isoformat()

    next_item, next_reason = n12_orchestrator.choose_next(queue, registry)
    if next_item and next_item.get("state") == "WAITING" and next_reason == "AUTO_RELEASED_WAITING":
        next_item["state"] = "READY"
        next_item["released_at"] = now_iso
        next_item["released_by"] = result["work_item_id"]
        next_item, _ = n12_orchestrator.choose_next(queue, registry)

    automation = state.setdefault("automation", {})
    automation["last_result_receipt"] = receipt_rel
    automation["last_result_decision"] = decision
    automation["last_result_at"] = now_iso
    automation["current_work_item"] = next_item.get("id") if next_item else None

    outcome_map = {
        "PASS": "PASS_ADVANCE",
        "PASS_WITH_WATCH": "PASS_WITH_WATCH_ADVANCE",
        "RESIDUAL": "RESIDUAL_REVIEW",
        "BLOCKED": "BLOCKED_INPUT",
        "CONFLICT": "CONFLICT_STOP",
    }
    automation["last_cycle_outcome"] = outcome_map[decision]
    state["updated_at"] = now.date().isoformat()

    if decision == "CONFLICT":
        state["status"] = "CONFLICT_STOP"
    elif decision == "BLOCKED":
        state["status"] = "BLOCKED_INPUT"
    elif next_item:
        state["status"] = "IN_PROGRESS_WITH_AUTOMATED_PER_STOREY_CYCLE"
    else:
        incomplete = [
            q for q in queue.get("items", [])
            if not n12_orchestrator.item_effectively_complete(q, registry) and q.get("state") != "SUPERSEDED"
        ]
        state["status"] = "CYCLIC_QUEUE_COMPLETE" if not incomplete else "BLOCKED_DEPENDENCY"

    next_action = state.setdefault("next_action", {})
    if next_item:
        next_action["phase"] = "PER-STOREY-SECTIONS-AND-BEAM-TOPOLOGY"
        next_action["work_item"] = next_item.get("id")
        next_action["task"] = next_item.get("task")
        next_action["target_outputs"] = list(next_item.get("target_outputs", []))
    else:
        next_action["work_item"] = None
        next_action["task"] = "No eligible work item. Inspect the persistent queue and the last result receipt."
        next_action["target_outputs"] = []

    return next_item


def apply_result(input_path: Path, result: dict[str, Any], warnings: list[str]) -> int:
    decision = result.get("decision")
    validators: list[dict[str, Any]] = []
    if decision in {"PASS", "PASS_WITH_WATCH"}:
        validators = run_required_validators()
        failed = [entry for entry in validators if entry["status"] != "PASS"]
        if failed:
            print(json.dumps({"status": "FAIL_STOP", "reason": "deterministic validator failure", "validators": validators}, indent=2, ensure_ascii=False))
            return 1

    queue = read_json(QUEUE_PATH)
    state = read_json(STATE_PATH)
    manifest = read_json(MANIFEST_PATH)
    registry = n12_orchestrator.load_effective_registry(manifest)
    now = utc_now()
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    receipt_path = RECEIPT_DIR / f"{result['work_item_id']}_{stamp}.json"
    receipt_rel = receipt_path.relative_to(ROOT).as_posix()

    receipt = {
        "schema_version": "1.0",
        "ingested_at": now.isoformat(),
        "work_item_id": result["work_item_id"],
        "decision": decision,
        "semantic_gate": result.get("semantic_gate"),
        "result": result,
        "warnings": warnings,
        "deterministic_validators": validators,
    }
    write_json(receipt_path, receipt)

    next_item = update_state_for_result(state, queue, registry, result, receipt_rel)
    write_json(QUEUE_PATH, queue)
    write_json(STATE_PATH, state)
    input_path.unlink(missing_ok=True)

    payload = {
        "status": "INGESTED",
        "receipt": receipt_rel,
        "decision": decision,
        "next_work_item": next_item.get("id") if next_item else None,
        "queue_state": next_item.get("state") if next_item else None,
        "warnings": warnings,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and ingest one specialist result into the N12 controlled cycle")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ["validate", "apply"]:
        p = sub.add_parser(name)
        p.add_argument("--input", default=DEFAULT_INPUT.relative_to(ROOT).as_posix())
    args = parser.parse_args()

    input_path = ROOT / args.input
    if not input_path.exists():
        print(f"N12_AGENT_RESULT = NO_INPUT ({input_path.relative_to(ROOT)})")
        return 0 if args.cmd == "validate" else 1

    try:
        result = read_json(input_path)
    except Exception as exc:
        print(f"N12_AGENT_RESULT = FAIL\nERROR: invalid JSON: {exc}")
        return 1

    errors, warnings, context = validate_result(result)
    if errors:
        print("N12_AGENT_RESULT = FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        print(json.dumps(context, indent=2, ensure_ascii=False))
        return 1

    print("N12_AGENT_RESULT = PASS")
    for warning in warnings:
        print(f"WARN: {warning}")
    if args.cmd == "validate":
        print(json.dumps(context, indent=2, ensure_ascii=False))
        return 0
    return apply_result(input_path, result, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
