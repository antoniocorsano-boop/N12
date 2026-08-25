#!/usr/bin/env python3
from __future__ import annotations

import csv, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_KNOWLEDGE_GRAPH_CONTRACT_v1.json"
MANIFEST = ROOT / "knowledge/KNOWLEDGE_MANIFEST.json"
REGISTRY = ROOT / "knowledge/ARTIFACT_REGISTRY_CEW_KNOWLEDGE_GRAPH_PATCH_v1.csv"
MILESTONES = ROOT / "data/canonical/CEW_SYSTEM_MILESTONES_v1.csv"


def rows(p: Path):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def run(*args: str) -> str:
    cp = subprocess.run([sys.executable, *args], cwd=ROOT, check=True, text=True, capture_output=True)
    print(cp.stdout, end="")
    return cp.stdout


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("acceptance_gate") != "KNOWLEDGE_GRAPH_PASS":
        raise AssertionError("unexpected F5 acceptance gate")
    if set(contract.get("projection_slices", {})) != {"M0G_MEMBERS", "M1A_REINFORCEMENT", "M1L_LOADS"}:
        raise AssertionError("F5 slice set drift")
    if any(v not in {"IN_SCOPE", "PASS"} for v in contract["projection_slices"].values()):
        raise AssertionError("all three F5 slices must be authorized")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    patch = "knowledge/ARTIFACT_REGISTRY_CEW_KNOWLEDGE_GRAPH_PATCH_v1.csv"
    if patch not in manifest.get("artifact_registry_patches", []):
        raise AssertionError("F5 registry patch not governed by KNOWLEDGE_MANIFEST")
    required_ids = {
        "CONTRACT-CEW-KG-001", "RUN-CEW-KG-001", "RUN-CEW-KG-002", "CI-CEW-KG-001",
        "RUN-CEW-KG-003", "RUN-CEW-KG-004", "CI-CEW-KG-002",
        "RUN-CEW-KG-005", "RUN-CEW-KG-006", "CI-CEW-KG-003"
    }
    actual_ids = {r["artifact_id"].strip() for r in rows(REGISTRY)}
    if not required_ids.issubset(actual_ids):
        raise AssertionError(f"F5 artifact registry incomplete: {sorted(required_ids-actual_ids)}")

    status = {r["milestone_id"].strip(): r["status"].strip() for r in rows(MILESTONES)}
    if status.get("CEW-F5") != "IN_PROGRESS":
        raise AssertionError("global pre-closure validator requires CEW-F5 IN_PROGRESS")
    if any(status.get(x) != "COMPLETE" for x in ("CEW-F0", "CEW-F1", "CEW-F2", "CEW-F3", "CEW-F4")):
        raise AssertionError("upstream CEW milestones are not frozen COMPLETE")

    with tempfile.TemporaryDirectory(prefix="cew-f5-") as td:
        td = Path(td)
        m0g, m1a, m1l = td/"m0g", td/"m1a", td/"m1l"
        run("scripts/project_cew_m0g_knowledge_graph.py", "--out", str(m0g))
        o0 = run("scripts/validate_cew_knowledge_graph_m0g_slice.py", "--projection", str(m0g/"m0g_graph_projection.json"))
        run("scripts/project_cew_m1a_knowledge_graph.py", "--out", str(m1a))
        oa = run("scripts/validate_cew_knowledge_graph_m1a_slice.py", "--projection", str(m1a/"m1a_graph_projection.json"))
        run("scripts/project_cew_m1l_knowledge_graph.py", "--out", str(m1l))
        ol = run("scripts/validate_cew_knowledge_graph_m1l_slice.py", "--projection", str(m1l/"m1l_graph_projection.json"))
        for marker, out in (("KNOWLEDGE_GRAPH_M0G_SLICE_PASS",o0),("KNOWLEDGE_GRAPH_M1A_SLICE_PASS",oa),("KNOWLEDGE_GRAPH_M1L_SLICE_PASS",ol)):
            if marker not in out: raise AssertionError(f"missing slice marker: {marker}")

    print("KNOWLEDGE_GRAPH_PASS")
    print("SLICES_PASS=3/3")
    print("M0G_REOPEN=FORBIDDEN")
    print("SOURCE_LEDGER_MUTATION=FORBIDDEN")
    print("EPISTEMIC_PROMOTION=FORBIDDEN")
    print("MISSING_PROPERTY_INVENTION=FORBIDDEN")
    print("GRAPH_AUTHORITY=DERIVED_GRAPH_PROJECTION_ONLY")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
