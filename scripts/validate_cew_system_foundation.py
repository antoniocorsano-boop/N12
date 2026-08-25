#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_SYSTEM_FOUNDATION_CONTRACT_v1.json"
MILESTONES = ROOT / "data" / "canonical" / "CEW_SYSTEM_MILESTONES_v1.csv"
ARCH = ROOT / "docs" / "ARCHITECTURE" / "CEW_SYSTEM_FOUNDATION_v1.md"

EXPECTED_EPISTEMIC = ["DOC", "MIS", "RIF", "INF", "ND"]
EXPECTED_AUTHORITY = [
    "PRIMARY_SOURCE",
    "OBSERVATION",
    "CANONICAL_KNOWLEDGE",
    "ANALYSIS_ASSUMPTION",
    "CALCULATION_MODEL",
    "RESULT",
]
EXPECTED_MILESTONES = [
    "CEW-F0", "CEW-F1", "CEW-F2", "CEW-F3", "CEW-F4",
    "CEW-F5", "CEW-F6", "CEW-F7", "CEW-F8", "CEW-M1", "CEW-M2",
]
ALLOWED_STATUS = {"COMPLETE", "IN_PROGRESS", "PLANNED"}


def main() -> int:
    if not ARCH.exists():
        raise AssertionError("missing CEW system foundation architecture")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-SYSTEM-FOUNDATION-v1":
        raise AssertionError("unexpected foundation contract id")
    if contract.get("epistemic_states") != EXPECTED_EPISTEMIC:
        raise AssertionError("canonical epistemic states changed")
    if contract.get("authority_flow") != EXPECTED_AUTHORITY:
        raise AssertionError("authority flow changed")

    frozen = contract.get("frozen_rules", {})
    required_frozen = {
        "m0g_geometry_reopen_required": True,
        "conversation_is_authority": False,
        "derived_visual_is_primary_evidence": False,
        "calculation_result_can_establish_documentary_fact": False,
        "unrelated_residuals_block_global_progress": False,
    }
    if frozen != required_frozen:
        raise AssertionError("foundation frozen rules changed")

    prohibited = set(contract.get("ai_may_not_directly_produce", []))
    required_prohibited = {
        "CanonicalAssertion",
        "FrozenCanonicalMutation",
        "EpistemicPromotionAboveCeiling",
    }
    if prohibited != required_prohibited:
        raise AssertionError("AI direct-authority prohibition changed")

    with MILESTONES.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = [r["milestone_id"].strip() for r in rows]
    if ids != EXPECTED_MILESTONES:
        raise AssertionError(f"milestone sequence changed: {ids}")

    status = {r["milestone_id"].strip(): r["status"].strip() for r in rows}
    bad_status = {mid: value for mid, value in status.items() if value not in ALLOWED_STATUS}
    if bad_status:
        raise AssertionError(f"invalid milestone status values: {bad_status}")

    active = [mid for mid in ids if status[mid] == "IN_PROGRESS"]
    if len(active) != 1:
        raise AssertionError(f"exactly one milestone must be IN_PROGRESS, got {active}")
    active_id = active[0]
    active_index = ids.index(active_id)

    for idx, mid in enumerate(ids):
        expected = "COMPLETE" if idx < active_index else "IN_PROGRESS" if idx == active_index else "PLANNED"
        if status[mid] != expected:
            raise AssertionError(
                f"milestone lifecycle must be a COMPLETE prefix, one IN_PROGRESS item, then PLANNED suffix: "
                f"{mid}={status[mid]} expected={expected}"
            )

    rows_by_id = {r["milestone_id"].strip(): r for r in rows}
    deps = [d.strip() for d in rows_by_id[active_id]["depends_on"].split(";") if d.strip()]
    unknown_deps = [d for d in deps if d not in status]
    if unknown_deps:
        raise AssertionError(f"active milestone has unknown dependencies: {unknown_deps}")
    incomplete_deps = [d for d in deps if status[d] != "COMPLETE"]
    if incomplete_deps:
        raise AssertionError(f"active milestone dependencies are not COMPLETE: {incomplete_deps}")

    if any(not r["acceptance_gate"].strip() for r in rows):
        raise AssertionError("every milestone requires an acceptance gate")
    if any(not r["required_deliverables"].strip() for r in rows):
        raise AssertionError("every milestone requires deliverables")

    completed = [mid for mid in ids if status[mid] == "COMPLETE"]
    print("CEW SYSTEM FOUNDATION = PASS")
    print("Completed milestones: " + ", ".join(completed))
    print(f"Active milestone: {active_id}")
    print("Epistemic regime: DOC/MIS/RIF/INF/ND")
    print("Authority flow: PRIMARY_SOURCE -> OBSERVATION -> CANONICAL_KNOWLEDGE -> ANALYSIS_ASSUMPTION -> CALCULATION_MODEL -> RESULT")
    print(f"Milestones validated: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
