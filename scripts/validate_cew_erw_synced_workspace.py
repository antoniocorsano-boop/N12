#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
MEMBERS = C / "M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
NODES = C / "M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv"
CONTRACT = ROOT / "automation" / "CEW_ERW_CONTRACT_v1.json"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def one(items: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    m = [r for r in items if r.get(key, "").strip() == value]
    if len(m) != 1:
        raise AssertionError(f"expected one {key}={value}, got {len(m)}")
    return m[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--built-dir", required=True)
    args = ap.parse_args()
    built = Path(args.built_dir)
    manifest = json.loads((built / "sync_manifest.json").read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    if manifest.get("authority") != contract.get("workspace_authority") or manifest.get("authority") != "DERIVED_REVIEW_WORKSPACE_ONLY":
        raise AssertionError("workspace authority drift")
    if manifest.get("canonical_write") is not False or manifest.get("m0g_reopen") is not False or manifest.get("epistemic_promotion") is not False:
        raise AssertionError("forbidden authority action enabled")
    entries = manifest.get("entries", [])
    if len(entries) != 4 or {e["task_id"] for e in entries} != {f"ERW-N12-00{i}" for i in range(1,5)}:
        raise AssertionError("four-task sync coverage drift")
    if not (built / "source-viewer" / "viewer_manifest.json").exists() or not (built / "source-viewer" / "index.html").exists():
        raise AssertionError("embedded F3 source viewer missing")

    # Current canonical queue intentionally contains no structural binding.
    if any(e.get("structural_selection") is not None for e in entries):
        raise AssertionError("structural highlight introduced without canonical binding")
    if any(e.get("binding_state") != "UNBOUND" for e in entries):
        raise AssertionError("current queue binding state drift")

    e4 = one(entries, "task_id", "ERW-N12-004")
    ctx = e4.get("structural_context")
    if not ctx or ctx.get("source_member_id") != "G5-B017":
        raise AssertionError("G5-B017 candidate-comparison context missing")
    if "candidate-comparison" not in e4.get("structural_authority_note", "") or "UNBOUND" not in e4.get("structural_authority_note", ""):
        raise AssertionError("candidate context authority not explicit")

    members, nodes = rows(MEMBERS), rows(NODES)
    m = one(members, "source_member_id", "G5-B017")
    if (m["support_i"].strip(), m["support_j"].strip()) != ("12", "19"):
        raise AssertionError("G5-B017 support topology drift")
    if ctx["member_id"] != m["member_id"].strip() or ctx["node_i"]["node_id"] != m["node_i"].strip() or ctx["node_j"]["node_id"] != m["node_j"].strip():
        raise AssertionError("candidate context face-node binding drift")
    ni, nj = one(nodes, "node_id", m["node_i"].strip()), one(nodes, "node_id", m["node_j"].strip())
    expected_i = (float(ni["x_m"]), float(ni["y_m"]), float(ni["z_m"]))
    expected_j = (float(nj["x_m"]), float(nj["y_m"]), float(nj["z_m"]))
    actual_i = (ctx["node_i"]["x_m"], ctx["node_i"]["y_m"], ctx["node_i"]["z_m"])
    actual_j = (ctx["node_j"]["x_m"], ctx["node_j"]["y_m"], ctx["node_j"]["z_m"])
    if actual_i != expected_i or actual_j != expected_j:
        raise AssertionError("candidate coordinates differ from canonical analytical nodes")
    if ni["coordinate_evidence_state"].strip() != "INF" or nj["coordinate_evidence_state"].strip() != "INF":
        raise AssertionError("expected current face-node coordinate evidence INF")
    if ctx["node_i"]["coordinate_evidence_state"] != "INF" or ctx["node_j"]["coordinate_evidence_state"] != "INF":
        raise AssertionError("coordinate evidence was promoted")
    computed = math.dist(expected_i, expected_j)
    if abs(computed - float(m["geometric_length_m"])) > 5e-5:
        raise AssertionError("face-node length inconsistent with frozen member length")
    if abs(ctx["computed_face_node_length_m"] - computed) > 1e-12:
        raise AssertionError("render context recomputed length drift")

    # Preserve the ledger's explicit section state exactly. For G5-B017 it is the literal ND,
    # not a blank/null value and not a section inferred from neighboring beams.
    if ctx.get("section_cm") != m["section_cm"].strip():
        raise AssertionError("G5-B017 section state differs from frozen connectivity ledger")
    if m["section_cm"].strip() != "ND" or m["section_evidence"].strip() != "ND":
        raise AssertionError("expected current G5-B017 section state ND")

    app = (built / "app.js").read_text(encoding="utf-8")
    html = (built / "index.html").read_text(encoding="utf-8")
    if "source-viewer/index.html?task=" not in app:
        raise AssertionError("source pane is not synchronized to F3 task deep link")
    if "NOT PRIMARY EVIDENCE" not in html or "NO CANONICAL WRITE" not in html:
        raise AssertionError("derived structural authority banner missing")

    print("ERW_SYNC_WORKSPACE_PASS")
    print("TASKS=4/4")
    print("F3_SOURCE_PANE=EMBEDDED_AND_TASK_SYNCHRONIZED")
    print("CURRENT_BOUND_SELECTIONS=0")
    print("ERW_N12_004_BINDING=UNBOUND")
    print("G5_B017_CONTEXT=CANDIDATE_COMPARISON_ONLY")
    print(f"G5_B017_FACE_NODES={m['node_i'].strip()}->{m['node_j'].strip()}")
    print(f"G5_B017_LENGTH_M={computed:.7f}")
    print("COORDINATE_EVIDENCE=INF_PRESERVED")
    print("G5_B017_SECTION=ND_PRESERVED")
    print("CANONICAL_WRITE=FORBIDDEN")
    print("M0G_REOPEN=FORBIDDEN")
    print("EPISTEMIC_PROMOTION=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
