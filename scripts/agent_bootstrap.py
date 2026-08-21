#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge" / "KNOWLEDGE_MANIFEST.json"
STATE = ROOT / "knowledge" / "CURRENT_STATE.json"
REGISTRY = ROOT / "knowledge" / "ARTIFACT_REGISTRY.csv"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_registry():
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    manifest = read_json(MANIFEST)
    state = read_json(STATE)
    rows = read_registry()

    authorized = [
        r for r in rows
        if r.get("may_feed_canonical") == "YES"
        and r.get("status") not in {"SUSPENDED", "SUPERSEDED", "CONFLICT", "REOPENED", "TOMBSTONE", "HISTORICAL_ONLY"}
    ]
    conditional = [r for r in rows if r.get("may_feed_canonical") == "CONDITIONAL"]
    blocked = [
        r for r in rows
        if r.get("status") in {"SUSPENDED", "SUPERSEDED", "CONFLICT", "REOPENED", "TOMBSTONE", "HISTORICAL_ONLY"}
    ]

    payload = {
        "project": manifest.get("project"),
        "branch": manifest.get("canonical_branch"),
        "gate": state.get("gate"),
        "objective": state.get("objective"),
        "next_action": state.get("next_action"),
        "geometry_master_status": state.get("geometry_master_status"),
        "active_skills": manifest.get("active_skills", []),
        "authorized_artifacts": [
            {"id": r["artifact_id"], "path": r["path"], "domain": r["domain"], "authority": r["authority"]}
            for r in authorized
        ],
        "conditional_artifacts": [
            {"id": r["artifact_id"], "path": r["path"], "domain": r["domain"], "status": r["status"]}
            for r in conditional
        ],
        "blocked_artifacts": [
            {"id": r["artifact_id"], "path": r["path"], "status": r["status"]}
            for r in blocked
        ],
        "rule": "Use only authorized artifacts directly. Conditional artifacts require their declared validation gate. Blocked artifacts are provenance only."
    }

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
