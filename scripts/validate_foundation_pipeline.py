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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [PIPELINE, QUEUE, RESULT, PARENT_QUEUE, MANIFEST, STATE, SOURCE_ROLE, MASTER, ROOT / "scripts" / "n12_foundation_orchestrator.py"]
    for path in required:
        if not path.exists():
            errors.append(f"missing required FPEP file: {path.relative_to(ROOT)}")
    if errors:
        print(json.dumps({"status": "FAIL", "errors": errors, "warnings": warnings}, indent=2))
        return 1

    pipeline = load_json(PIPELINE)
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
    if wrapper and set(wrapper.get("target_outputs", [])) != {
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

    active_proc = set(manifest.get("active_procedures", []))
    if "docs/PROCEDURES/FOUNDATION_PRIMARY_EVIDENCE_PIPELINE_v1.md" not in active_proc:
        errors.append("FPEP procedure not registered in manifest active_procedures")
    fpep = manifest.get("foundation_primary_evidence_pipeline", {})
    if fpep.get("contract") != "automation/N12_FOUNDATION_PIPELINE_CONTRACT_v1.json":
        errors.append("manifest missing FPEP contract registration")

    if manifest.get("current_gate") != state.get("gate"):
        errors.append("manifest/state gate mismatch")
    if state.get("automation", {}).get("current_work_item") != "M1F-PRIMARY-GEOMETRY-REVALIDATION":
        warnings.append("CURRENT_STATE automation.current_work_item is not yet FPEP wrapper")

    hard = pipeline.get("hard_guardrails", {})
    mandatory_true = [
        "original_source_required_for_DOC",
        "reader_b_blind_to_reader_a",
        "foundation_readers_blind_to_M0G",
        "foundation_readers_blind_to_existing_topology_target",
        "TAV01A_cannot_generate_foundation_geometry",
        "M0G_cannot_generate_foundation_geometry",
        "historical_calculation_cannot_generate_foundation_geometry",
        "no_majority_vote",
        "derived_model_never_primary_evidence",
        "cross_validated_required_for_geometry_derivation",
        "minimum_reopen_scope",
        "all_outputs_receipt_gated",
    ]
    for key in mandatory_true:
        if hard.get(key) is not True:
            errors.append(f"hard guardrail not enabled: {key}")

    proc = subprocess.run([sys.executable, "scripts/n12_foundation_orchestrator.py", "validate"], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        errors.append("foundation sub-orchestrator validation failed: " + (proc.stdout + proc.stderr)[-4000:])

    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
