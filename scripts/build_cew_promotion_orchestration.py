#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
TASKS = C / "CEW_ERW_RESOLUTION_TASKS_v1.csv"
RESIDUALS = C / "M1E_B06_REINFORCEMENT_RESIDUALS_CURRENT_v1.csv"
SNAPSHOT_FILES = [
    C / "CEW_ERW_RESOLUTION_TASKS_v1.csv",
    C / "M1E_B06_REINFORCEMENT_RESIDUALS_CURRENT_v1.csv",
    C / "M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv",
    C / "M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv",
    C / "CEW_PROMOTION_TARGET_REGISTRY_v1.csv"
]


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluations", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    evaluations = json.loads(Path(args.evaluations).read_text(encoding="utf-8"))
    eval_by_decision = {x["decision_id"]: x for x in evaluations["current_n12"]}
    task_rows = rows(TASKS)
    residual_by_id = {r["residual_id"].strip(): r for r in rows(RESIDUALS)}

    nodes = []
    edges = []
    queue = []
    for t in task_rows:
        tid = t["task_id"].strip()
        rid = t["residual_id"].strip()
        decision_id = f"CEW-F6-CONFORMANCE-{tid}"
        ev = eval_by_decision[decision_id]
        if rid not in residual_by_id:
            raise AssertionError(f"residual missing for task {tid}")
        nodes.extend([
            {"node_id": rid, "node_type": "RESIDUAL", "authority": "CANONICAL_RESIDUAL_LEDGER"},
            {"node_id": tid, "node_type": "RESOLUTION_TASK", "authority": "CANONICAL_TASK_REGISTRY"},
            {"node_id": decision_id, "node_type": "RESOLUTION_DECISION", "authority": "DERIVED_NON_HUMAN_CONFORMANCE"},
            {"node_id": ev["receipt_id"], "node_type": "PROMOTION_EVALUATION", "authority": "DERIVED_EVALUATION_ONLY"}
        ])
        edges.extend([
            {"from": rid, "to": tid, "relation": "RESOLVED_BY_TASK"},
            {"from": tid, "to": decision_id, "relation": "PRODUCES_DECISION"},
            {"from": decision_id, "to": ev["receipt_id"], "relation": "EVALUATED_BY_PROMOTION_ENGINE"}
        ])
        domain = t["domain"].strip()
        if domain == "REINFORCEMENT_SOURCE_BINDING":
            action_class = "DIRECT_SOURCE_BINDING_REVIEW"
            reopen_sensitivity = "POTENTIAL_GEOMETRY_REOPEN_IF_BINDING_CHANGES_M0G"
        else:
            action_class = "DIRECT_PRIMARY_SOURCE_REREAD"
            reopen_sensitivity = "NO_GEOMETRY_REOPEN_EXPECTED"
        queue.append({
            "task_id": tid,
            "residual_id": rid,
            "blocking_scope": t["blocking_scope"].strip(),
            "current_terminal_action": ev["terminal_action"],
            "priority_class": "BLOCKING_SCOPE_RETAINED_RESIDUAL",
            "action_class": action_class,
            "reopen_sensitivity": reopen_sensitivity,
            "suggested_actions": t["suggested_actions"].strip(),
            "status": "RETAINED_OPEN"
        })

    queue.sort(key=lambda x: (x["blocking_scope"], x["action_class"], x["task_id"]))
    snapshots = [{"path": str(p.relative_to(ROOT)), "sha256": sha(p), "role": "READ_ONLY_F7_INPUT"} for p in SNAPSHOT_FILES]
    bundle = {
        "schema_version": "1.0",
        "milestone": "CEW-F7",
        "authority": "DERIVED_ORCHESTRATION_ONLY",
        "dependency_graph": {"nodes": nodes, "edges": edges},
        "residual_queue": queue,
        "canonical_snapshot_receipt": {
            "snapshot_type": "PRE_PROMOTION_READ_ONLY_BASELINE",
            "files": snapshots,
            "canonical_mutation_performed": False
        }
    }
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out / "promotion_orchestration.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    print("CEW_PROMOTION_ORCHESTRATION_BUILT")
    print(f"DEPENDENCY_NODES={len(nodes)}")
    print(f"DEPENDENCY_EDGES={len(edges)}")
    print(f"RETAINED_RESIDUALS={len(queue)}")
    print(f"SNAPSHOT_FILES={len(snapshots)}")
    print("CANONICAL_MUTATION=FORBIDDEN")
    return 0

if __name__ == "__main__": raise SystemExit(main())
