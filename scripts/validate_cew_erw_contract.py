#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_ERW_CONTRACT_v1.json"
TASKS = ROOT / "data" / "canonical" / "CEW_ERW_RESOLUTION_TASKS_v1.csv"
SPEC = ROOT / "docs" / "ARCHITECTURE" / "CEW_EVIDENCE_RESOLUTION_WORKSPACE_v1.md"

EXPECTED_OUTCOMES = {
    "CONFIRMED",
    "REJECTED",
    "UNREADABLE",
    "UNBOUND",
    "NEEDS_BETTER_SOURCE",
    "NEEDS_SITE_SURVEY",
    "DEFER",
}
EXPECTED_TASKS = {
    "ERW-N12-001": "M1E-B06-R08",
    "ERW-N12-002": "M1E-B06-R09",
    "ERW-N12-003": "M1E-B06-R10",
    "ERW-N12-004": "M1E-B06-R11",
}
ALLOWED_CEILINGS = {"DOC_DIRECT_ONLY", "INF_STRONG_DRAFTING_RULE", "MIS", "RIF", "ND"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    for p in [CONTRACT, TASKS, SPEC]:
        if not p.exists():
            raise AssertionError(f"missing ERW artifact: {p.relative_to(ROOT)}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-ERW-v1":
        raise AssertionError("unexpected ERW contract id")
    if contract.get("core_rule") != "NO_GRAPHICAL_CONVENIENCE_MAY_SILENTLY_INCREASE_EPISTEMIC_AUTHORITY":
        raise AssertionError("ERW epistemic authority rule changed")
    if set(contract.get("resolution_outcomes", [])) != EXPECTED_OUTCOMES:
        raise AssertionError("ERW resolution outcomes changed")

    rows = read_csv(TASKS)
    if len(rows) != 4:
        raise AssertionError(f"initial ERW N12 task count changed: {len(rows)} != 4")
    by_id = {r["task_id"].strip(): r for r in rows}
    if set(by_id) != set(EXPECTED_TASKS):
        raise AssertionError("initial ERW task ids changed")

    for task_id, residual_id in EXPECTED_TASKS.items():
        r = by_id[task_id]
        if r["residual_id"].strip() != residual_id:
            raise AssertionError(f"{task_id}: residual binding changed")
        if r["status"].strip() != "OPEN":
            raise AssertionError(f"{task_id}: initial task must remain OPEN")
        if r["epistemic_ceiling"].strip() not in ALLOWED_CEILINGS:
            raise AssertionError(f"{task_id}: invalid epistemic ceiling")
        if "BBOX_ND" not in r["source_region_state"]:
            raise AssertionError(f"{task_id}: source bbox must remain explicitly unresolved until registered")

    if by_id["ERW-N12-004"]["model_entities"].strip() != "G5-B017":
        raise AssertionError("ERW-N12-004 model binding changed")
    if "SOURCE_TOPOLOGY" not in by_id["ERW-N12-004"]["conflicts"]:
        raise AssertionError("ERW-N12-004 topology conflict missing")

    print("CEW ERW CONTRACT = PASS")
    print("initial_tasks=4")
    print("authority_rule=PASS")
    print("source_bbox_policy=PASS")
    print("promotion_boundary=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
