#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"

MASTER = C / "PT_MASTER_CURRENT.csv"
SUPPORTS = C / "PT_VECTOR_SUPPORTS_v1.csv"
NODES = C / "PT_ANALYTICAL_NODES_v1.csv"
BEAMS = C / "PT_VECTOR_BEAMS_v2.csv"
BEAM_PATCH = C / "PT_VECTOR_BEAMS_G6_PATCH_v1.csv"
OVERLAY = C / "PT_OVERLAY_QA_v1.csv"
REGEN_AUDIT = C / "PT_MASTER_REGENERATION_AUDIT_v1.csv"
HIST_SNAPSHOT = C / "PT_MASTER_PRE_G1G9_SNAPSHOT_20260821.csv"

EXPECTED_SUPPORTS = {str(i) for i in range(1, 34)} | {"22'", "a", "b", "c", "d"}
NODE_RE = re.compile(r"AN-\d{3}")
TOL = 1e-4


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def f(row, key):
    return float(row[key])


def fail(errors, message):
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in [MASTER, SUPPORTS, NODES, BEAMS, BEAM_PATCH, OVERLAY, REGEN_AUDIT, HIST_SNAPSHOT]:
        if not path.exists():
            fail(errors, f"missing required PT Master validation artifact: {path.relative_to(ROOT)}")
    if errors:
        return report(errors, warnings, {})

    master = read_csv(MASTER)
    supports = read_csv(SUPPORTS)
    nodes = read_csv(NODES)
    beams = read_csv(BEAMS)
    patch = read_csv(BEAM_PATCH)
    overlay = read_csv(OVERLAY)
    regen = read_csv(REGEN_AUDIT)

    # 1. Physical support identity/count contract.
    master_ids = [r["entity_id"].strip() for r in master]
    support_ids = [r["support_id"].strip() for r in supports]
    if len(master) != 38:
        fail(errors, f"PT Master row count must be 38, got {len(master)}")
    if len(set(master_ids)) != len(master_ids):
        fail(errors, "duplicate entity_id in PT Master")
    if set(master_ids) != EXPECTED_SUPPORTS:
        fail(errors, f"PT Master support set mismatch: missing={sorted(EXPECTED_SUPPORTS-set(master_ids))} extra={sorted(set(master_ids)-EXPECTED_SUPPORTS)}")
    if len(supports) != 38 or set(support_ids) != EXPECTED_SUPPORTS:
        fail(errors, "PT_VECTOR_SUPPORTS_v1 does not contain the same 38 physical supports as PT Master")

    support_by_id = {r["support_id"].strip(): r for r in supports}
    master_by_id = {r["entity_id"].strip(): r for r in master}

    # 2. Master physical coordinates/bounds must exactly match support-vector authority.
    numeric_fields = ["x_center_m", "y_center_m", "x_min_m", "x_max_m", "y_min_m", "y_max_m"]
    master_map = {
        "x_center_m": "x_global_m", "y_center_m": "y_global_m",
        "x_min_m": "x_min_m", "x_max_m": "x_max_m", "y_min_m": "y_min_m", "y_max_m": "y_max_m"
    }
    for sid in sorted(EXPECTED_SUPPORTS):
        s = support_by_id[sid]
        m = master_by_id[sid]
        for skey in numeric_fields:
            mkey = master_map[skey]
            if abs(float(s[skey]) - float(m[mkey])) > TOL:
                fail(errors, f"{sid}: Master {mkey} differs from PT_VECTOR_SUPPORTS ({m[mkey]} vs {s[skey]})")
        if s["metric_center_evidence"].strip() != m["metric_evidence"].strip():
            fail(errors, f"{sid}: Master metric_evidence differs from physical support registry")
        if s["center_is_analytical_node"].strip() != "NO":
            fail(errors, f"{sid}: physical support center must not be an analytical node")

    # 3. Effective beam set: base v2 minus blocked/provenance rows, then patch actions.
    nonphysical_statuses = {"BLOCKED", "PROVENANCE_ONLY", "REVOKED_SOURCE_MISMATCH"}
    effective_beams = {
        r["beam_id"].strip()
        for r in beams
        if r.get("vector_status", "").strip() not in nonphysical_statuses
    }
    for r in patch:
        action = r["action"].strip().upper()
        bid = r["beam_id"].strip()
        if action == "REVOKE":
            effective_beams.discard(bid)
        elif action == "ADD":
            effective_beams.add(bid)
        else:
            fail(errors, f"unknown G6 beam patch action {action} for {bid}")
    if len(effective_beams) != 51:
        fail(errors, f"effective physical beam count must be 51, got {len(effective_beams)}")
    for forbidden in ["B-029", "B-037", "B-044"]:
        if forbidden in effective_beams:
            fail(errors, f"{forbidden} must not be an effective physical beam")
    if "B-052" not in effective_beams:
        fail(errors, "B-052 P19-P20 must be present in effective topology")

    # 4. Analytical nodes: IDs, parent support, beam membership and exact physical-face condition.
    if len(nodes) != 102:
        fail(errors, f"analytical node row count must be 102, got {len(nodes)}")
    node_ids = [r["node_id"].strip() for r in nodes]
    if len(set(node_ids)) != len(node_ids):
        fail(errors, "duplicate analytical node_id")
    node_by_id = {r["node_id"].strip(): r for r in nodes}

    face_checks = {
        "EAST": ("x", "x_max_m"),
        "WEST": ("x", "x_min_m"),
        "NORTH": ("y", "y_min_m"),
        "SOUTH": ("y", "y_max_m"),
    }
    for n in nodes:
        nid = n["node_id"].strip()
        sid = n["support_id"].strip()
        if sid not in support_by_id:
            fail(errors, f"{nid}: unknown parent support {sid}")
            continue
        attached = [b.strip() for b in n["attached_beams"].split("|") if b.strip()]
        if not attached:
            fail(errors, f"{nid}: no attached beam")
        for bid in attached:
            if bid not in effective_beams:
                fail(errors, f"{nid}: attached beam {bid} is not in effective topology")
        face = n["face_ref"].strip().upper()
        if face not in face_checks:
            fail(errors, f"{nid}: invalid face_ref {face}")
            continue
        axis, bound_key = face_checks[face]
        coord = float(n["x_m"] if axis == "x" else n["y_m"])
        bound = float(support_by_id[sid][bound_key])
        if abs(coord - bound) > TOL:
            fail(errors, f"{nid}: {face} coordinate {coord} is not on {sid} boundary {bound_key}={bound}")
        # Other coordinate must remain within the face segment.
        if axis == "x":
            other = float(n["y_m"])
            lo, hi = f(support_by_id[sid], "y_min_m"), f(support_by_id[sid], "y_max_m")
        else:
            other = float(n["x_m"])
            lo, hi = f(support_by_id[sid], "x_min_m"), f(support_by_id[sid], "x_max_m")
        if other < lo - TOL or other > hi + TOL:
            fail(errors, f"{nid}: point lies outside {sid} {face} face segment")
        if n["node_role"].strip() != "BEAM_TO_SUPPORT_FACE":
            fail(errors, f"{nid}: unexpected node_role={n['node_role']}")

    watch_nodes = sum(1 for n in nodes if n["node_evidence_status"].strip() == "WATCH")

    # 5. Every detailed node must be referenced once by its physical support in Master.
    refs: list[str] = []
    for m in master:
        sid = m["entity_id"].strip()
        ids = NODE_RE.findall(m.get("analytical_nodes", ""))
        try:
            declared = int(m["analytical_node_count"])
        except Exception:
            declared = -1
        if declared != len(ids):
            fail(errors, f"{sid}: analytical_node_count={declared} but {len(ids)} IDs are listed")
        for nid in ids:
            refs.append(nid)
            if nid not in node_by_id:
                fail(errors, f"{sid}: Master references unknown node {nid}")
            elif node_by_id[nid]["support_id"].strip() != sid:
                fail(errors, f"{sid}: Master references {nid} belonging to support {node_by_id[nid]['support_id']}")
    if len(refs) != 102:
        fail(errors, f"Master must contain 102 analytical node references, got {len(refs)}")
    if len(set(refs)) != 102:
        fail(errors, "analytical node references in Master are not one-to-one")
    if set(refs) != set(node_ids):
        fail(errors, "Master analytical-node references do not exactly cover PT_ANALYTICAL_NODES_v1")

    # 6. Extended-support semantics must remain multi-node.
    expected_extended_counts = {"18": 3, "23": 3, "30": 3}
    for sid, expected in expected_extended_counts.items():
        actual = int(master_by_id[sid]["analytical_node_count"])
        if actual != expected:
            fail(errors, f"P{sid}: expected {expected} analytical face nodes, got {actual}")
    if master_by_id["18"]["section_cm"] != "110x30":
        fail(errors, "P18 section must be 110x30")
    if master_by_id["23"]["section_cm"] != "110x30":
        fail(errors, "P23 section must be 110x30")
    if master_by_id["30"]["section_cm"] != "30x110":
        fail(errors, "P30 section must be 30x110")

    # 7. Final G9 and regeneration gates must explicitly be PASS/READY.
    overlay_by_id = {r["qa_id"].strip(): r for r in overlay}
    if overlay_by_id.get("G9-010", {}).get("status", "").strip() != "PASS_WITH_PROVENANCE_WATCHES":
        fail(errors, "G9-010 final overlay gate is not PASS_WITH_PROVENANCE_WATCHES")
    regen_by_id = {r["audit_id"].strip(): r for r in regen}
    if regen_by_id.get("MASTER-REGEN-014", {}).get("status", "").strip() != "PASS":
        fail(errors, "MASTER-REGEN-014 promotion gate is not PASS")

    summary = {
        "master_support_rows": len(master),
        "effective_beams": len(effective_beams),
        "analytical_face_nodes": len(nodes),
        "watch_nodes": watch_nodes,
        "master_node_references": len(refs),
        "extended_nodes_P18": int(master_by_id["18"]["analytical_node_count"]),
        "extended_nodes_P23": int(master_by_id["23"]["analytical_node_count"]),
        "extended_nodes_P30": int(master_by_id["30"]["analytical_node_count"]),
    }
    return report(errors, warnings, summary)


def report(errors, warnings, summary) -> int:
    if errors:
        print("PT_MASTER_CURRENT_VALIDATION = FAIL")
        for e in errors:
            print(f"ERROR: {e}")
        for w in warnings:
            print(f"WARN: {w}")
        return 1
    print("PT_MASTER_CURRENT_VALIDATION = PASS")
    for key, value in summary.items():
        print(f"{key}={value}")
    for w in warnings:
        print(f"WARN: {w}")
    print("Master/support/beam/analytical-node contracts are coherent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
