#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import n12_foundation_orchestrator as fpep

ROOT = Path(__file__).resolve().parents[1]
AUDIT_REL = "analysis/fpep/FPEP_STATE_COHERENCE_AUDIT_v1.json"
AUDIT_PATH = ROOT / AUDIT_REL
RESULT_PATH = ROOT / "automation" / "inbox" / "N12_FOUNDATION_AGENT_RESULT.json"
EXPECTED_ITEM = "FPEP-P00-STATE-CONSISTENCY"
BLOCKING_STATES = {"CONFLICT", "REOPENED", "SUPERSEDED", "TOMBSTONE", "HISTORICAL_ONLY", "SUSPENDED"}


def check(check_id: str, condition: bool, severity: str, fact: str, expected: str | None = None, actual: Any = None) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": "PASS" if condition else "FAIL",
        "severity": severity,
        "fact": fact,
        "expected": expected,
        "actual": actual,
    }


def registry_descriptor(rel: str, registry: dict[str, dict[str, str]]) -> tuple[str, str]:
    row = registry.get(rel)
    if not row:
        return "UNREGISTERED_NON_AUTHORITATIVE", "UNREGISTERED"
    return row.get("authority") or "UNKNOWN", row.get("status") or "UNKNOWN"


def extract_repo_references(markdown: str) -> list[str]:
    refs: set[str] = set()
    prefixes = ("data/", "knowledge/", "automation/", "analysis/", "docs/", "scripts/", "skills/", ".github/")
    for token in re.findall(r"`([^`]+)`", markdown):
        clean = token.strip().split(" @ ", 1)[0].strip()
        if clean.startswith(prefixes) and not any(ch in clean for ch in "*?{}"):
            refs.add(clean)
    return sorted(refs)


def main() -> int:
    queue = fpep.read_json(fpep.QUEUE_PATH)
    item = fpep.selected_item(queue)
    if not item or item.get("id") != EXPECTED_ITEM:
        print(json.dumps({"status": "NOOP", "reason": "P00 is not the selected FPEP item", "selected": item.get("id") if item else None}, indent=2))
        return 0

    manifest = fpep.read_json(fpep.MANIFEST_PATH)
    state = fpep.read_json(ROOT / "knowledge" / "CURRENT_STATE.json")
    parent_queue = fpep.read_json(fpep.PARENT_QUEUE_PATH)
    registry = fpep.load_effective_registry()
    allowed_inputs = fpep.resolved_allowed_inputs(item)
    manifest_registry_paths = [x for x in [manifest.get("artifact_registry")] + fpep.registry_patch_rels(manifest) if x]
    manifest_registry_set = set(manifest_registry_paths)

    input_artifacts: list[dict[str, str]] = []
    missing_inputs: list[str] = []
    unusable_inputs: list[str] = []
    for rel in allowed_inputs:
        path = ROOT / rel
        if rel in manifest_registry_set:
            authority, status = "REGISTRY_COMPONENT_MANIFEST_DECLARED", "CURRENT" if path.exists() else "MISSING"
        else:
            authority, status = registry_descriptor(rel, registry)
        if not path.exists():
            missing_inputs.append(rel)
            sha = "MISSING"
        else:
            sha = fpep.sha256_file(path)
        input_artifacts.append({"path": rel, "sha256": sha, "authority": authority, "status": status})
        if rel not in manifest_registry_set and (authority == "UNREGISTERED_NON_AUTHORITATIVE" or status in BLOCKING_STATES):
            unusable_inputs.append(rel)

    parent_items = {x.get("id"): x for x in parent_queue.get("items", [])}
    wrapper = parent_items.get("M1F-PRIMARY-GEOMETRY-REVALIDATION")
    downstream = parent_items.get("M1F-FOUNDATION-MODEL")

    checks: list[dict[str, Any]] = [
        check("P00-C001", manifest.get("canonical_branch") == "work/m0-global-model", "HARD", "canonical branch identity", "work/m0-global-model", manifest.get("canonical_branch")),
        check("P00-C002", manifest.get("current_gate") == state.get("gate"), "HARD", "manifest/state gate equality", str(manifest.get("current_gate")), state.get("gate")),
        check("P00-C003", state.get("automation", {}).get("current_work_item") == "M1F-PRIMARY-GEOMETRY-REVALIDATION", "HARD", "current parent work item", "M1F-PRIMARY-GEOMETRY-REVALIDATION", state.get("automation", {}).get("current_work_item")),
        check("P00-C004", bool(wrapper) and wrapper.get("state") in {"READY", "IN_PROGRESS", "CANDIDATE", "RESIDUAL"}, "HARD", "FPEP wrapper is active", "active wrapper", wrapper.get("state") if wrapper else None),
        check("P00-C005", bool(downstream) and "M1F-PRIMARY-GEOMETRY-REVALIDATION" in set(downstream.get("dependencies", [])), "HARD", "downstream M1F depends on FPEP wrapper", "dependency present", downstream.get("dependencies") if downstream else None),
        check("P00-C006", item.get("state") in {"READY", "IN_PROGRESS", "RESIDUAL"}, "HARD", "P00 is selected and executable", "READY/IN_PROGRESS/RESIDUAL", item.get("state")),
        check("P00-C007", not missing_inputs, "HARD", "all resolved P00 inputs exist", "0 missing", missing_inputs),
        check("P00-C008", not unusable_inputs, "HARD", "all non-registry-component P00 inputs have usable effective-registry authority", "0 unusable", unusable_inputs),
    ]

    missing_registry_paths = [rel for rel in manifest_registry_paths if not (ROOT / rel).exists()]
    checks.append(check("P00-C009", not missing_registry_paths, "HARD", "all manifest-declared effective registry files exist", "0 missing", missing_registry_paths))

    core_fpep_paths = [
        "automation/N12_FOUNDATION_PIPELINE_CONTRACT_v1.json",
        "automation/N12_FOUNDATION_WORK_QUEUE_v1.json",
        "automation/N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json",
        "docs/PROCEDURES/FOUNDATION_PRIMARY_EVIDENCE_PIPELINE_v1.md",
        "scripts/n12_foundation_orchestrator.py",
        "scripts/validate_foundation_pipeline.py",
        ".github/workflows/validate-fpep-foundation-pipeline.yml",
    ]
    core_unregistered = [rel for rel in core_fpep_paths if rel not in registry]
    checks.append(check("P00-C010", not core_unregistered, "HARD", "FPEP core artifacts are registered in effective registry", "0 unregistered", core_unregistered))

    master_path = ROOT / "docs" / "REGISTRO_MASTER.md"
    master_refs = extract_repo_references(master_path.read_text(encoding="utf-8")) if master_path.exists() else []
    missing_master_refs = [rel for rel in master_refs if not (ROOT / rel).exists()]
    checks.append(check("P00-C011", not missing_master_refs, "WATCH", "human Master backtick references resolve to existing repository artifacts", "0 missing", missing_master_refs))

    hard_failures = [c for c in checks if c["severity"] == "HARD" and c["status"] == "FAIL"]
    watches = [c for c in checks if c["severity"] == "WATCH" and c["status"] == "FAIL"]

    residuals: list[dict[str, Any]] = []
    for idx, c in enumerate(watches, start=1):
        residuals.append({
            "residual_id": f"P00-W{idx:03d}",
            "claim_id": c["check_id"],
            "blocking": False,
            "reason": f"{c['fact']}: {c['actual']}",
            "required_evidence": "Update or supersede the human Master reference only if it is still intended as a current operational pointer; do not substitute a guessed file."
        })
    for idx, c in enumerate(hard_failures, start=1):
        residuals.append({
            "residual_id": f"P00-B{idx:03d}",
            "claim_id": c["check_id"],
            "blocking": True,
            "reason": f"{c['fact']}: {c['actual']}",
            "required_evidence": "Repair the machine-state/registry inconsistency and rerun P00."
        })

    decision = "BLOCKED" if hard_failures else ("PASS_WITH_WATCH" if watches else "PASS")
    semantic_gate = "FAIL" if hard_failures else ("WATCH" if watches else "PASS")
    now = datetime.now(timezone.utc)
    run_id = f"FPEP-P00-{now.strftime('%Y%m%dT%H%M%SZ')}"

    audit = {
        "schema_version": "1.0",
        "pipeline_id": "N12_FPEP_FOUNDATION_PRIMARY_EVIDENCE_PIPELINE",
        "work_item_id": EXPECTED_ITEM,
        "generated_at": now.isoformat(),
        "decision": decision,
        "semantic_gate": semantic_gate,
        "resolved_allowed_inputs": allowed_inputs,
        "manifest_registry_paths": manifest_registry_paths,
        "registry_component_policy": "Manifest-declared base/patch registry files are trusted registry components after existence/hash validation and are not required to self-register circularly.",
        "checks": checks,
        "summary": {
            "hard_failures": len(hard_failures),
            "watches": len(watches),
            "missing_inputs": missing_inputs,
            "unusable_inputs": unusable_inputs,
            "missing_master_references": missing_master_refs,
            "entrypoint_unambiguous": not hard_failures,
        },
        "rule": "P00 establishes machine-state coherence only. It does not validate foundation geometry and does not expose legacy foundation target counts to downstream primary readers."
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = {
        "schema_version": "1.0",
        "pipeline_id": "N12_FPEP_FOUNDATION_PRIMARY_EVIDENCE_PIPELINE",
        "run_id": run_id,
        "work_item_id": EXPECTED_ITEM,
        "stage_id": EXPECTED_ITEM,
        "agent_role": item.get("agent_role"),
        "decision": decision,
        "semantic_gate": semantic_gate,
        "input_artifacts": input_artifacts,
        "primary_sources": [],
        "target_outputs": list(item.get("target_outputs", [])),
        "provenance_summary": {"DOC": 0, "MIS": 0, "RIF": 0, "INF": 0, "INC": len(watches), "ND": len(hard_failures)},
        "residuals": residuals,
        "audit_paths": [AUDIT_REL],
        "information_barrier_attestation": {
            "forbidden_context_not_used": True,
            "legacy_target_counts_not_used_before_primary_gate": True,
            "downstream_model_not_used_as_primary_evidence": True,
            "majority_vote_not_used_for_authority": True
        }
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"status": "GENERATED", "decision": decision, "audit": AUDIT_REL, "result": RESULT_PATH.relative_to(ROOT).as_posix(), "hard_failures": len(hard_failures), "watches": len(watches)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
