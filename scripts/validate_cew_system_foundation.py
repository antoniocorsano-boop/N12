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
    if rows[0]["status"].strip() != "IN_PROGRESS":
        raise AssertionError("CEW-F0 must be IN_PROGRESS until this gate is integrated")
    if any(not r["acceptance_gate"].strip() for r in rows):
        raise AssertionError("every milestone requires an acceptance gate")
    if any(not r["required_deliverables"].strip() for r in rows):
        raise AssertionError("every milestone requires deliverables")

    print("CEW SYSTEM FOUNDATION = PASS")
    print("Epistemic regime: DOC/MIS/RIF/INF/ND")
    print("Authority flow: PRIMARY_SOURCE -> OBSERVATION -> CANONICAL_KNOWLEDGE -> ANALYSIS_ASSUMPTION -> CALCULATION_MODEL -> RESULT")
    print(f"Milestones validated: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
