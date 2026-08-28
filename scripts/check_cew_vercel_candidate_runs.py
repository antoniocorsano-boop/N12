#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "automation/CEW_VERCEL_DEPLOY_POLICY_v1.json"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_cew_vercel_candidate_runs.py <github-actions-runs.json>")
        return 2

    runs_path = Path(sys.argv[1])
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    payload = json.loads(runs_path.read_text(encoding="utf-8"))
    runs = payload.get("workflow_runs", [])

    latest_by_name: dict[str, dict] = {}
    for run in sorted(runs, key=lambda row: int(row.get("run_number", 0)), reverse=True):
        name = run.get("name")
        if name and name not in latest_by_name:
            latest_by_name[name] = run

    missing: list[str] = []
    failed: list[str] = []
    for name in policy["preview_required_workflows"]:
        run = latest_by_name.get(name)
        if run is None:
            missing.append(name)
            continue
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            failed.append(
                f"{name}: status={run.get('status')} conclusion={run.get('conclusion')} run={run.get('run_number')}"
            )

    if missing or failed:
        print("CEW_VERCEL_CANDIDATE_GATE = NOT_READY")
        for item in missing:
            print(f"MISSING: {item}")
        for item in failed:
            print(f"NOT_GREEN: {item}")
        return 1

    print("CEW_VERCEL_CANDIDATE_GATE = PASS")
    print(f"REQUIRED_WORKFLOWS = {len(policy['preview_required_workflows'])}")
    print("DEPLOYMENT_AUTHORITY_EFFECT = NONE")
    print("HVA_EFFECT = NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
