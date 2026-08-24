#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import n12_orchestrator
import n12_foundation_orchestrator

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INDEX = ROOT / "data" / "canonical" / "tavole_originali_remote_index_v1.csv"
OUTPUT = ROOT / "analysis" / "automation" / "N12_AGENT_TASK_PACKET.json"
FPEP_WRAPPER_ID = "M1F-PRIMARY-GEOMETRY-REVALIDATION"


def read_source_index() -> dict[str, dict[str, str]]:
    with SOURCE_INDEX.open("r", encoding="utf-8-sig", newline="") as f:
        return {row["id"]: row for row in csv.DictReader(f)}


def build_packet() -> dict:
    status = n12_orchestrator.build_status(run_checks=False)
    item = status.get("selected_work_item")
    sources = read_source_index()

    packet = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "system": status.get("system_id"),
        "branch": status.get("branch"),
        "gate": status.get("gate"),
        "decision": status.get("decision"),
        "mandatory_read_order": [
            "AGENTS.md",
            "knowledge/KNOWLEDGE_MANIFEST.json",
            "knowledge/CURRENT_STATE.json",
            "automation/N12_AUTOMATION_CONTRACT_v1.json",
            "automation/N12_WORK_QUEUE_v1.json",
            "automation/N12_AGENT_RESULT_CONTRACT_v1.json",
            "skills/pt-carpentry-reader/SKILL.md"
        ],
        "global_stop_conditions": [
            "primary source is unavailable or unreadable",
            "identifier or section symbol is ambiguous",
            "two primary-source observations conflict",
            "candidate would require copying a section or beam from another storey",
            "candidate would promote MIS/RIF/INF to DOC",
            "deterministic validation fails"
        ],
        "promotion_rule": "Produce a candidate with explicit provenance first. Canonical promotion requires semantic gate plus deterministic validators; unresolved rows must be INC/ND/RESIDUAL rather than guessed.",
        "result_contract": "automation/N12_AGENT_RESULT_CONTRACT_v1.json",
        "result_inbox": "automation/inbox/N12_AGENT_RESULT.json"
    }

    if not item:
        packet["work_item"] = None
        packet["agent_action"] = "NO_SPECIALIST_TASK"
        return packet

    sheet_id = item.get("source_sheet")
    source = sources.get(sheet_id) if sheet_id and sheet_id != "MULTI" else None
    packet["work_item"] = {
        "id": item.get("id"),
        "priority": item.get("priority"),
        "task": item.get("task"),
        "stage": item.get("stage"),
        "source_sheet": sheet_id,
        "source_primary": source,
        "render_artifact": "storey-source-renders-v1" if sheet_id in {"TAV-03S", "TAV-04S", "TAV-05S", "TAV-05E", "TAV-06S", "TAV-06E"} else None,
        "required_inputs": item.get("required_inputs", []),
        "target_outputs": item.get("target_outputs", []),
        "semantic_gate": item.get("semantic_gate"),
        "dependencies_complete": item.get("dependencies_complete"),
        "missing_inputs": item.get("missing_inputs", []),
        "selection_reason": item.get("selection_reason"),
    }

    if item.get("id") == FPEP_WRAPPER_ID:
        delegated = n12_foundation_orchestrator.make_task()
        packet["agent_action"] = "DELEGATE_TO_FOUNDATION_SUBORCHESTRATOR"
        packet["delegation"] = {
            "pipeline": "N12_FPEP_FOUNDATION_PRIMARY_EVIDENCE_PIPELINE",
            "contract": "automation/N12_FOUNDATION_PIPELINE_CONTRACT_v1.json",
            "queue": "automation/N12_FOUNDATION_WORK_QUEUE_v1.json",
            "result_contract": "automation/N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json",
            "result_inbox": "automation/inbox/N12_FOUNDATION_AGENT_RESULT.json",
            "orchestrator": "scripts/n12_foundation_orchestrator.py",
            "completion_item": "FPEP-P12-RELEASE-AUDIT",
            "completion_gate": "data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv",
            "delegated_task": delegated,
        }
        packet["required_result"] = {
            "max_items_per_cycle": 1,
            "contract": "automation/N12_FOUNDATION_AGENT_RESULT_CONTRACT_v1.json",
            "inbox": "automation/inbox/N12_FOUNDATION_AGENT_RESULT.json",
            "must_run": [
                "python scripts/validate_foundation_pipeline.py",
                "python scripts/n12_foundation_orchestrator.py validate",
                "python scripts/n12_foundation_orchestrator.py status"
            ],
            "on_pass": "ingest only the selected FPEP sub-item; do not submit the parent M1F wrapper until FPEP-P12 is COMPLETE and the release gate is registered",
            "on_residual": "retain the smallest unresolved FPEP claim and continue unrelated sectors only when dependencies allow",
            "on_conflict": "reopen only the conflicting claim/evidence region; never expose legacy 38/58 targets to pre-P07 agents"
        }
        return packet

    packet["agent_action"] = (
        "EXECUTE_ONE_SPECIALIST_ITEM_AND_STOP"
        if status.get("decision") == "READY_FOR_AGENT"
        else "REVIEW_RESIDUAL_AND_STOP"
        if status.get("decision") == "RESIDUAL_REVIEW"
        else "NO_SPECIALIST_TASK"
    )
    packet["required_result"] = {
        "max_items_per_cycle": 1,
        "must_write_audit_or_provenance": True,
        "contract": "automation/N12_AGENT_RESULT_CONTRACT_v1.json",
        "inbox": "automation/inbox/N12_AGENT_RESULT.json",
        "must_run": [
            "python scripts/validate_knowledge_system.py",
            "python scripts/n12_orchestrator.py validate",
            "python skills/pt-carpentry-reader/runner.py validate",
            "python scripts/n12_ingest_agent_result.py validate"
        ],
        "on_pass": "register/promote the target artifact, write the single result packet and let the deterministic ingestor advance queue/state",
        "on_watch": "retain WATCH provenance and advance only if the work-item semantic gate permits it",
        "on_residual": "record the smallest unresolved claim and leave unrelated queue branches eligible",
        "on_conflict": "stop and reopen only the conflicting claim",
        "template": {
            "schema_version": "1.0",
            "work_item_id": item.get("id"),
            "source_sheet": sheet_id,
            "decision": "PASS|PASS_WITH_WATCH|RESIDUAL|BLOCKED|CONFLICT",
            "semantic_gate": "PASS|WATCH|FAIL",
            "target_outputs": list(item.get("target_outputs", [])),
            "provenance_summary": {"DOC": 0, "MIS": 0, "RIF": 0, "INF": 0, "INC": 0, "ND": 0},
            "residuals": [],
            "audit_paths": []
        }
    }
    return packet


def main() -> int:
    packet = build_packet()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
