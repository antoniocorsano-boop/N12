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
EXPECTED_SNAPSHOTS = {
    "data/canonical/CEW_ERW_RESOLUTION_TASKS_v1.csv",
    "data/canonical/M1E_B06_REINFORCEMENT_RESIDUALS_CURRENT_v1.csv",
    "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv",
    "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv",
    "data/canonical/CEW_PROMOTION_TARGET_REGISTRY_v1.csv"
}


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--orchestration",required=True); a=ap.parse_args()
    b=json.loads(Path(a.orchestration).read_text(encoding="utf-8"))
    if b.get("milestone")!="CEW-F7" or b.get("authority")!="DERIVED_ORCHESTRATION_ONLY": raise AssertionError("orchestration authority drift")
    tasks={r["task_id"].strip():r for r in rows(TASKS)}
    q=b.get("residual_queue",[])
    if len(q)!=4 or {x["task_id"] for x in q}!=set(tasks): raise AssertionError("residual queue coverage drift")
    if any(x["current_terminal_action"]!="RETAIN_RESIDUAL" or x["status"]!="RETAINED_OPEN" for x in q): raise AssertionError("retained residual silently changed")
    if {x["blocking_scope"] for x in q}!={"M1E-B06"}: raise AssertionError("blocking scope drift")
    by={x["task_id"]:x for x in q}
    for tid in ("ERW-N12-001","ERW-N12-002","ERW-N12-003"):
        if by[tid]["action_class"]!="DIRECT_PRIMARY_SOURCE_REREAD" or by[tid]["reopen_sensitivity"]!="NO_GEOMETRY_REOPEN_EXPECTED": raise AssertionError(f"reread classification drift: {tid}")
    if by["ERW-N12-004"]["action_class"]!="DIRECT_SOURCE_BINDING_REVIEW" or "GEOMETRY_REOPEN" not in by["ERW-N12-004"]["reopen_sensitivity"]: raise AssertionError("binding residual reopen sensitivity missing")
    graph=b["dependency_graph"]; nodes=graph["nodes"]; edges=graph["edges"]
    if len(nodes)!=16 or len(edges)!=12: raise AssertionError("dependency graph count drift")
    node_ids={n["node_id"] for n in nodes}
    for x in q:
        tid=x["task_id"]; rid=x["residual_id"]; did=f"CEW-F6-CONFORMANCE-{tid}"; eid=f"PROMOTION-EVAL-{did}"
        if not {rid,tid,did,eid}.issubset(node_ids): raise AssertionError(f"dependency chain node missing: {tid}")
        expected={(rid,tid,"RESOLVED_BY_TASK"),(tid,did,"PRODUCES_DECISION"),(did,eid,"EVALUATED_BY_PROMOTION_ENGINE")}
        actual={(e["from"],e["to"],e["relation"]) for e in edges}
        if not expected.issubset(actual): raise AssertionError(f"dependency chain edge missing: {tid}")
    snap=b["canonical_snapshot_receipt"]
    if snap.get("canonical_mutation_performed") is not False or snap.get("snapshot_type")!="PRE_PROMOTION_READ_ONLY_BASELINE": raise AssertionError("snapshot receipt gained write authority")
    files={x["path"]:x for x in snap.get("files",[])}
    if set(files)!=EXPECTED_SNAPSHOTS: raise AssertionError("snapshot file set drift")
    for rel,item in files.items():
        if item["role"]!="READ_ONLY_F7_INPUT" or item["sha256"]!=sha(ROOT/rel): raise AssertionError(f"snapshot hash mismatch: {rel}")
    print("PROMOTION_ORCHESTRATION_SLICE_PASS")
    print("DEPENDENCY_CHAINS=4/4")
    print("RETAINED_RESIDUALS=4")
    print("BLOCKING_SCOPE=M1E-B06")
    print("DIRECT_SOURCE_REREAD_QUEUE=3")
    print("SOURCE_BINDING_REVIEW_QUEUE=1")
    print("CANONICAL_SNAPSHOT_HASHES=5/5_MATCH")
    print("M0G_REOPEN_SENSITIVITY=EXPLICIT")
    print("CANONICAL_MUTATION=FORBIDDEN")
    return 0

if __name__=="__main__": raise SystemExit(main())
