#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "automation" / "N12_FOUNDATION_PIPELINE_CONTRACT_v1.json"
QUEUE = ROOT / "automation" / "N12_FOUNDATION_WORK_QUEUE_v1.json"
RESULT = ROOT / "automation" / "N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json"
PARENT_QUEUE = ROOT / "automation" / "N12_WORK_QUEUE_v1.json"
MANIFEST = ROOT / "knowledge" / "KNOWLEDGE_MANIFEST.json"
STATE = ROOT / "knowledge" / "CURRENT_STATE.json"
SOURCE_ROLE = ROOT / "data" / "canonical" / "M1F_FOUNDATION_SOURCE_ROLE_AUDIT_v1.csv"
MASTER = ROOT / "docs" / "REGISTRO_MASTER.md"
TASK_GENERATOR = ROOT / "scripts" / "n12_make_agent_task.py"
PARENT_INGESTOR = ROOT / "scripts" / "n12_ingest_agent_result.py"
SUB_ORCHESTRATOR = ROOT / "scripts" / "n12_foundation_orchestrator.py"
PARENT_WORKFLOW = ROOT / ".github" / "workflows" / "n12-analysis-orchestrator.yml"
REGISTRY_PATCH = ROOT / "knowledge" / "ARTIFACT_REGISTRY_FPEP_PATCH_v1.csv"
FPEP_WRAPPER_ID = "M1F-PRIMARY-GEOMETRY-REVALIDATION"
FPEP_COMPLETION_ITEM = "FPEP-P12-RELEASE-AUDIT"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        PIPELINE,
        QUEUE,
        RESULT,
        PARENT_QUEUE,
        MANIFEST,
        STATE,
        SOURCE_ROLE,
        MASTER,
        TASK_GENERATOR,
        PARENT_INGESTOR,
        SUB_ORCHESTRATOR,
        PARENT_WORKFLOW,
        REGISTRY_PATCH,
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required FPEP file: {path.relative_to(ROOT)}")
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors, "warnings": warnings}, indent=2))
        return 1

    pipeline = load_json(PIPELINE)
    subqueue = load_json(QUEUE)
    parent = load_json(PARENT_QUEUE)
    manifest = load_json(MANIFEST)
    state = load_json(STATE)
    source_roles = load_csv(SOURCE_ROLE)

    source_by_id = {r.get("canonical_source_id"): r for r in source_roles}
    tav01s = source_by_id.get("TAV-01S")
    tav01a = source_by_id.get("TAV-01A")
    if not tav01s or tav01s.get("canonical_role") != "FOUNDATION_CARPENTRY" or tav01s.get("provides_foundation_topology") != "YES":
        errors.append("source-role audit does not identify TAV-01S as foundation topology authority")
    if not tav01a or tav01a.get("provides_foundation_topology") != "NO":
        errors.append("source-role audit must keep TAV-01A out of foundation topology generation")

    items = {i.get("id"): i for i in parent.get("items", [])}
    wrapper = items.get(pipeline.get("parent_work_item"))
    m1f = items.get("M1F-FOUNDATION-MODEL")
    if not wrapper:
        errors.append("missing M1F-PRIMARY-GEOMETRY-REVALIDATION in parent queue")
    if not m1f:
        errors.append("missing M1F-FOUNDATION-MODEL in parent queue")
    if wrapper:
        if wrapper.get("state") not in {"READY", "IN_PROGRESS", "CANDIDATE", "RESIDUAL"}:
            warnings.append(f"FPEP parent wrapper is not currently active: state={wrapper.get('state')}")
        if set(wrapper.get("target_outputs", [])) != {
            "data/canonical/M1F_PRIMARY_GEOMETRY_GATE_v1.csv",
            "data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv",
        }:
            errors.append("FPEP parent wrapper target outputs are not the two required gates")
    if m1f:
        if pipeline.get("parent_work_item") not in set(m1f.get("dependencies", [])):
            errors.append("M1F-FOUNDATION-MODEL can bypass FPEP parent wrapper")
        for rel in ["data/canonical/M1F_PRIMARY_GEOMETRY_GATE_v1.csv", "data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv"]:
            if rel not in set(m1f.get("required_inputs", [])):
                errors.append(f"M1F-FOUNDATION-MODEL missing FPEP gate input: {rel}")

    subitems = {i.get("id"): i for i in subqueue.get("items", [])}
    if FPEP_COMPLETION_ITEM not in subitems:
        errors.append(f"foundation subqueue missing completion item {FPEP_COMPLETION_ITEM}")
    if subitems.get("FPEP-P00-STATE-CONSISTENCY", {}).get("state") not in {"READY", "IN_PROGRESS", "COMPLETE", "RESIDUAL"}:
        errors.append("foundation subqueue has no valid P00 entry state")

    active_proc = set(manifest.get("active_procedures", []))
    if "docs/PROCEDURES/FOUNDATION_PRIMARY_EVIDENCE_PIPELINE_v1.md" not in active_proc:
        errors.append("FPEP procedure not registered in manifest active_procedures")
    patches = set(manifest.get("artifact_registry_patches", []))
    if "knowledge/ARTIFACT_REGISTRY_FPEP_PATCH_v1.csv" not in patches:
        errors.append("FPEP registry patch not registered in knowledge manifest")
    fpep = manifest.get("foundation_primary_evidence_pipeline", {})
    if fpep.get("contract") != "automation/N12_FOUNDATION_PIPELINE_CONTRACT_v1.json":
        errors.append("manifest missing FPEP contract registration")
    if fpep.get("runner") != "scripts/n12_foundation_orchestrator.py":
        errors.append("manifest FPEP runner mismatch")

    if manifest.get("current_gate") != state.get("gate"):
        errors.append("manifest/state gate mismatch")
    if state.get("automation", {}).get("current_work_item") != FPEP_WRAPPER_ID:
        warnings.append("CURRENT_STATE automation.current_work_item is not FPEP wrapper")
    if state.get("foundation_primary_evidence_pipeline", {}).get("current_subtask") != "FPEP-P00-STATE-CONSISTENCY":
        warnings.append("CURRENT_STATE FPEP current_subtask is not P00")

    hard = pipeline.get("hard_guardrails", {})
    mandatory_true = [
        "original_source_required_for_DOC",
        "reader_b_blind_to_reader_a",
        "foundation_readers_blind_to_M0G",
        "foundation_readers_blind_to_existing_topology_target",
        "TAV01A_cannot_generate_foundation_geometry",
        "M0G_cannot_generate_foundation_geometry",
        "historical_calculation_cannot_generate_foundation_geometry",
        "TAV01A_binding_after_primary_geometry_gate_only",
        "M0G_crosscheck_after_primary_geometry_gate_only",
        "no_majority_vote",
        "adjudicator_cannot_create_fact",
        "canonicalizer_cannot_semantically_read_source",
        "derived_model_never_primary_evidence",
        "cross_validated_required_for_geometry_derivation",
        "minimum_reopen_scope",
        "legacy_checkpoint_preservation",
        "all_residuals_persisted",
        "all_outputs_receipt_gated",
        "canonical_targets_must_be_registered_before_pass",
        "parent_handoff_only_after_P12_complete",
        "parent_handoff_must_cite_P12_receipt",
    ]
    for key in mandatory_true:
        if hard.get(key) is not True:
            errors.append(f"hard guardrail not enabled: {key}")

    runtime = pipeline.get("runtime_handoff", {})
    if runtime.get("p12_completion_item") != FPEP_COMPLETION_ITEM:
        errors.append("runtime handoff completion item mismatch")
    if pipeline.get("runtime_workflow") != ".github/workflows/n12-analysis-orchestrator.yml":
        errors.append("FPEP runtime workflow mismatch")
    if pipeline.get("parent_result_inbox") != "automation/inbox/N12_AGENT_RESULT.json":
        errors.append("FPEP parent result inbox mismatch")

    proc = subprocess.run(
        [sys.executable, "scripts/n12_foundation_orchestrator.py", "validate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        errors.append("foundation sub-orchestrator validation failed: " + (proc.stdout + proc.stderr)[-4000:])

    task_proc = subprocess.run(
        [sys.executable, "scripts/n12_make_agent_task.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if task_proc.returncode != 0:
        errors.append("parent task generator failed: " + (task_proc.stdout + task_proc.stderr)[-4000:])
    else:
        try:
            packet = json.loads(task_proc.stdout)
        except Exception as exc:
            errors.append(f"parent task generator did not emit JSON: {exc}")
        else:
            if wrapper and wrapper.get("state") in {"READY", "IN_PROGRESS", "CANDIDATE", "RESIDUAL"}:
                if packet.get("work_item", {}).get("id") != FPEP_WRAPPER_ID:
                    errors.append("parent task generator did not select the FPEP wrapper")
                if packet.get("agent_action") != "DELEGATE_TO_FOUNDATION_SUBORCHESTRATOR":
                    errors.append("parent task generator exposes FPEP wrapper as a generic specialist task")
                delegated = packet.get("delegation", {}).get("delegated_task", {})
                if delegated.get("work_item_id") != "FPEP-P00-STATE-CONSISTENCY":
                    errors.append("parent task generator did not delegate to the current FPEP sub-item")
                if packet.get("required_result", {}).get("inbox") != "automation/inbox/N12_FOUNDATION_AGENT_RESULT.json":
                    errors.append("delegated task packet points to the wrong result inbox")

    ingestor_text = PARENT_INGESTOR.read_text(encoding="utf-8")
    required_ingestor_guards = [
        "validate_fpep_wrapper_completion",
        "FPEP-P12-RELEASE-AUDIT",
        "parent FPEP PASS must cite the P12 foundation receipt",
        "validate_foundation_pipeline.py",
    ]
    for token in required_ingestor_guards:
        if token not in ingestor_text:
            errors.append(f"parent ingestor missing FPEP anti-bypass guard: {token}")

    sub_orchestrator_text = SUB_ORCHESTRATOR.read_text(encoding="utf-8")
    required_runtime_guards = [
        "canonical_target_ingestible",
        "data/canonical/M1F_PRIMARY_GEOMETRY_GATE_v1.csv",
        "data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv",
        "FPEP-P12-RELEASE-AUDIT",
        "emit_parent_result",
        "PARENT_INBOX_PATH",
        "N12_AGENT_RESULT.json",
        "cannot emit parent FPEP result before every sub-item is COMPLETE",
    ]
    for token in required_runtime_guards:
        if token not in sub_orchestrator_text:
            errors.append(f"FPEP sub-orchestrator missing runtime handoff guard: {token}")

    workflow_text = PARENT_WORKFLOW.read_text(encoding="utf-8")
    required_workflow_bridge = [
        "automation/inbox/N12_FOUNDATION_AGENT_RESULT.json",
        "python scripts/n12_foundation_orchestrator.py ingest",
        "automation/N12_FOUNDATION_WORK_QUEUE_v1.json",
        "automation/receipts/foundation",
        "python scripts/n12_ingest_agent_result.py apply",
        "scripts/validate_foundation_pipeline.py",
    ]
    for token in required_workflow_bridge:
        if token not in workflow_text:
            errors.append(f"parent workflow missing FPEP runtime bridge: {token}")

    registry_paths = {row.get("path") for row in load_csv(REGISTRY_PATCH)}
    for rel in [
        "automation/N12_FOUNDATION_PIPELINE_CONTRACT_v1.json",
        "automation/N12_FOUNDATION_WORK_QUEUE_v1.json",
        "automation/N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json",
        "docs/PROCEDURES/FOUNDATION_PRIMARY_EVIDENCE_PIPELINE_v1.md",
        "scripts/n12_foundation_orchestrator.py",
        "scripts/validate_foundation_pipeline.py",
        ".github/workflows/validate-fpep-foundation-pipeline.yml",
    ]:
        if rel not in registry_paths:
            errors.append(f"FPEP core artifact is not registered: {rel}")

    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
