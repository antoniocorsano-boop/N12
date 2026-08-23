#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv"
LINKS = ROOT / "data/canonical/M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv"
MEMBERS = ROOT / "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
ROOF = ROOT / "data/canonical/ROOF_G5_SPECIAL_FEATURES_3D_CURRENT_v1.csv"
OUT = ROOT / "data/canonical/M0G_GLOBAL_TOPOLOGY_GATE_v1.csv"
AUDIT = ROOT / "analysis/automation/M0G_GLOBAL_TOPOLOGY_GATE_AUDIT_v1.csv"

ROOF_ABSENT_G5 = {"1", "8", "9", "16", "17", "24", "31", "32", "33"}
TERRACE = {"a", "b", "c", "d"}
ADJACENT_LEVELS = {("G1", "G2"), ("G2", "G3"), ("G3", "G4"), ("G4", "G5")}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(s: str | None) -> str:
    return (s or "").strip()


def add(checks, cid, category, severity, expected, observed, ok, evidence, note):
    checks.append({
        "check_id": cid,
        "category": category,
        "severity": severity,
        "expected": str(expected),
        "observed": str(observed),
        "status": "PASS" if ok else ("WATCH" if severity == "WATCH" else "FAIL"),
        "evidence_state": evidence,
        "note": note,
    })


def main() -> None:
    ns = rows(NODES)
    ls = rows(LINKS)
    ms = rows(MEMBERS)
    rs = rows(ROOF)

    node_by_id = {norm(r["node_id"]): r for r in ns}
    node_ids = list(node_by_id)
    member_ids = [norm(r["member_id"]) for r in ms]
    link_ids = [norm(r["link_id"]) for r in ls]

    checks: list[dict[str, str]] = []

    add(checks, "GT-001", "inventory", "HARD", 627, len(ns), len(ns) == 627, "CANONICAL", "Frozen analytical-node inventory.")
    add(checks, "GT-002", "inventory", "HARD", 462, len(ls), len(ls) == 462, "CANONICAL", "Frozen rigid-link inventory.")
    add(checks, "GT-003", "inventory", "HARD", 358, len(ms), len(ms) == 358, "CANONICAL", "Frozen ordinary structural-member inventory.")
    add(checks, "GT-004", "inventory", "HARD", 6, len(rs), len(rs) == 6, "CANONICAL_WITH_WATCH", "Exactly three ridge axes plus three eaves edge sets.")
    add(checks, "GT-005", "identity", "HARD", len(ns), len(set(node_ids)), len(node_ids) == len(set(node_ids)), "CANONICAL", "No duplicate node IDs.")
    add(checks, "GT-006", "identity", "HARD", len(ms), len(set(member_ids)), len(member_ids) == len(set(member_ids)), "CANONICAL", "No duplicate member IDs.")
    add(checks, "GT-007", "identity", "HARD", len(ls), len(set(link_ids)), len(link_ids) == len(set(link_ids)), "CANONICAL", "No duplicate rigid-link IDs.")

    missing_member_nodes = []
    zero_member_pairs = []
    duplicate_pairs = Counter()
    beam_role_fail = []
    column_role_fail = []
    invalid_cross_storey = []
    terrace_vertical = []
    roof_absent_vertical = []
    roof_special_as_member = []
    g5_b036 = 0
    for m in ms:
        ni, nj = norm(m["node_i"]), norm(m["node_j"])
        if ni not in node_by_id or nj not in node_by_id:
            missing_member_nodes.append(norm(m["member_id"]))
            continue
        if ni == nj:
            zero_member_pairs.append(norm(m["member_id"]))
        duplicate_pairs[tuple(sorted((ni, nj)))] += 1
        cls = norm(m["member_class"])
        ri, rj = norm(node_by_id[ni]["node_role"]), norm(node_by_id[nj]["node_role"])
        fl, tl = norm(m["from_level"]), norm(m["to_level"])
        if cls == "ORDINARY_BEAM":
            if ri != "BEAM_SUPPORT_FACE" or rj != "BEAM_SUPPORT_FACE":
                beam_role_fail.append(norm(m["member_id"]))
            if fl != tl:
                invalid_cross_storey.append(norm(m["member_id"]))
        elif cls == "COLUMN_SEGMENT":
            if ri != "SUPPORT_CORE" or rj != "SUPPORT_CORE":
                column_role_fail.append(norm(m["member_id"]))
            if (fl, tl) not in ADJACENT_LEVELS:
                invalid_cross_storey.append(norm(m["member_id"]))
            sid = norm(m["support_i"])
            if sid in TERRACE:
                terrace_vertical.append(norm(m["member_id"]))
            if (fl, tl) == ("G4", "G5") and sid in ROOF_ABSENT_G5:
                roof_absent_vertical.append(norm(m["member_id"]))
        else:
            invalid_cross_storey.append(norm(m["member_id"]))
        smid = norm(m["source_member_id"])
        if "RIDGE" in smid or "GRONDA" in smid or "G5-RIDGE" in norm(m["note"]) or "G5-GRONDA" in norm(m["note"]):
            roof_special_as_member.append(norm(m["member_id"]))
        if smid == "G5-B036":
            g5_b036 += 1

    dup_pair_count = sum(1 for n in duplicate_pairs.values() if n > 1)
    add(checks, "GT-008", "member_connectivity", "HARD", 0, len(missing_member_nodes), not missing_member_nodes, "CANONICAL", "Every member endpoint must exist in the node registry.")
    add(checks, "GT-009", "member_connectivity", "HARD", 0, len(zero_member_pairs), not zero_member_pairs, "CANONICAL", "No zero-node-pair members.")
    add(checks, "GT-010", "member_connectivity", "HARD", 0, dup_pair_count, dup_pair_count == 0, "CANONICAL", "No duplicate undirected structural member node pairs.")
    add(checks, "GT-011", "analytical_roles", "HARD", 0, len(beam_role_fail), not beam_role_fail, "CANONICAL", "All beams terminate on beam-face incidence nodes.")
    add(checks, "GT-012", "analytical_roles", "HARD", 0, len(column_role_fail), not column_role_fail, "CANONICAL", "All columns terminate on support-core nodes.")
    add(checks, "GT-013", "storey_logic", "HARD", 0, len(invalid_cross_storey), not invalid_cross_storey, "CANONICAL", "Beams stay within a level; columns connect adjacent levels only.")
    add(checks, "GT-014", "termination", "HARD", 0, len(terrace_vertical), not terrace_vertical, "DOC", "Terrace supports a-d must not extrude above G1.")
    add(checks, "GT-015", "termination", "HARD", 0, len(roof_absent_vertical), not roof_absent_vertical, "DOC", "Roof-absent supports must not create G4-G5 columns.")
    add(checks, "GT-016", "roof_separation", "HARD", 0, len(roof_special_as_member), not roof_special_as_member, "DOC+ND", "Ridge/eaves features remain outside ordinary member connectivity.")
    add(checks, "GT-017", "roof_separation", "HARD", 1, g5_b036, g5_b036 == 1, "DOC", "Confirmed oblique member 19-26 is counted once as G5-B036.")

    missing_link_nodes = []
    link_role_fail = []
    link_support_level_fail = []
    zero_links = []
    face_link_count = Counter()
    for l in ls:
        ci, fi = norm(l["core_node_id"]), norm(l["face_node_id"])
        if ci not in node_by_id or fi not in node_by_id:
            missing_link_nodes.append(norm(l["link_id"]))
            continue
        c, f = node_by_id[ci], node_by_id[fi]
        if norm(c["node_role"]) != "SUPPORT_CORE" or norm(f["node_role"]) != "BEAM_SUPPORT_FACE":
            link_role_fail.append(norm(l["link_id"]))
        if norm(c["support_id"]) != norm(f["support_id"]) or norm(c["level_id"]) != norm(f["level_id"]):
            link_support_level_fail.append(norm(l["link_id"]))
        if ci == fi or abs(float(l["offset_length_m"] or 0.0)) <= 1e-12:
            zero_links.append(norm(l["link_id"]))
        face_link_count[fi] += 1

    face_nodes = [r for r in ns if norm(r["node_role"]) == "BEAM_SUPPORT_FACE"]
    bad_face_link_coverage = [norm(r["node_id"]) for r in face_nodes if face_link_count[norm(r["node_id"])] != 1]
    add(checks, "GT-018", "rigid_links", "HARD", 0, len(missing_link_nodes), not missing_link_nodes, "INF", "Every rigid-link endpoint exists.")
    add(checks, "GT-019", "rigid_links", "HARD", 0, len(link_role_fail), not link_role_fail, "INF", "Rigid links connect core to face only.")
    add(checks, "GT-020", "rigid_links", "HARD", 0, len(link_support_level_fail), not link_support_level_fail, "INF", "Rigid links stay within the same physical support and level.")
    add(checks, "GT-021", "centroid_substitution", "HARD", 0, len(zero_links), not zero_links, "INF", "No face incidence collapses onto its support core.")
    add(checks, "GT-022", "face_incidence", "HARD", 0, len(bad_face_link_coverage), not bad_face_link_coverage, "INF", "Every beam-face node has exactly one core-to-face rigid link.")

    beam_endpoint_use = Counter()
    for m in ms:
        if norm(m["member_class"]) == "ORDINARY_BEAM":
            beam_endpoint_use[norm(m["node_i"])] += 1
            beam_endpoint_use[norm(m["node_j"])] += 1
    bad_face_member_coverage = [norm(r["node_id"]) for r in face_nodes if beam_endpoint_use[norm(r["node_id"])] != 1]
    add(checks, "GT-023", "face_incidence", "HARD", 0, len(bad_face_member_coverage), not bad_face_member_coverage, "INF", "Every face-incidence node belongs to exactly one ordinary beam endpoint.")

    roof_type_counts = Counter(norm(r["feature_type"]) for r in rs)
    roof_member_promotions = [norm(r["feature_id"]) for r in rs if norm(r["structural_member_status"]) != "TO_VERIFY_MEMBER"]
    roof_z_assigned = [norm(r["feature_id"]) for r in rs if norm(r["z_rel_g1_m"])]
    ridge_xy_bad = [norm(r["feature_id"]) for r in rs if norm(r["feature_type"]) == "RIDGE_AXIS" and norm(r["xy_evidence_state"]) != "MIS"]
    eave_centerline_created = [norm(r["feature_id"]) for r in rs if norm(r["feature_type"]) == "GRONDA_EDGE_SET" and norm(r["xy_geometry_wkt_m"])]
    add(checks, "GT-024", "roof_separation", "HARD", "3 RIDGE_AXIS + 3 GRONDA_EDGE_SET", f"{roof_type_counts['RIDGE_AXIS']} + {roof_type_counts['GRONDA_EDGE_SET']}", roof_type_counts["RIDGE_AXIS"] == 3 and roof_type_counts["GRONDA_EDGE_SET"] == 3, "DOC", "Roof-special identity inventory preserved.")
    add(checks, "GT-025", "roof_separation", "HARD", 0, len(roof_member_promotions), not roof_member_promotions, "ND", "No roof-special feature silently promoted to structural member.")
    add(checks, "GT-026", "roof_z", "WATCH", 0, len(roof_z_assigned), not roof_z_assigned, "ND", "Global roof-special Z intentionally remains unassigned pending unique datum/endpoint binding.")
    add(checks, "GT-027", "roof_xy", "HARD", 0, len(ridge_xy_bad), not ridge_xy_bad, "MIS", "Three ridge XY traces retain MIS provenance.")
    add(checks, "GT-028", "roof_xy", "WATCH", 0, len(eave_centerline_created), not eave_centerline_created, "ND", "No unsupported eave analytical centerline is created.")

    blank_node_prov = [norm(r["node_id"]) for r in ns if not norm(r["coordinate_evidence_state"]) or not norm(r["topology_evidence_state"])]
    blank_member_prov = [norm(r["member_id"]) for r in ms if not norm(r["connectivity_evidence"]) or not norm(r["topology_evidence"])]
    blank_link_prov = [norm(r["link_id"]) for r in ls if not norm(r["link_evidence_state"])]
    add(checks, "GT-029", "provenance", "HARD", 0, len(blank_node_prov), not blank_node_prov, "MIXED", "Node coordinate/topology provenance must remain explicit.")
    add(checks, "GT-030", "provenance", "HARD", 0, len(blank_member_prov), not blank_member_prov, "MIXED", "Member connectivity/topology provenance must remain explicit.")
    add(checks, "GT-031", "provenance", "HARD", 0, len(blank_link_prov), not blank_link_prov, "INF", "Rigid-link provenance must remain explicit.")

    adjacency: dict[str, set[str]] = defaultdict(set)
    for m in ms:
        a, b = norm(m["node_i"]), norm(m["node_j"])
        if a in node_by_id and b in node_by_id:
            adjacency[a].add(b); adjacency[b].add(a)
    for l in ls:
        a, b = norm(l["core_node_id"]), norm(l["face_node_id"])
        if a in node_by_id and b in node_by_id:
            adjacency[a].add(b); adjacency[b].add(a)
    orphan_nodes = [nid for nid in node_ids if not adjacency[nid]]
    seen = set()
    components = []
    for nid in node_ids:
        if nid in seen:
            continue
        q = deque([nid]); seen.add(nid); comp = []
        while q:
            u = q.popleft(); comp.append(u)
            for v in adjacency[u]:
                if v not in seen:
                    seen.add(v); q.append(v)
        components.append(comp)
    comp_sizes = sorted((len(c) for c in components), reverse=True)
    add(checks, "GT-032", "graph", "HARD", 0, len(orphan_nodes), not orphan_nodes, "DERIVED", "Orphan analytical nodes are reported, never auto-repaired.")
    add(checks, "GT-033", "graph", "HARD", 1, len(components), len(components) == 1, "DERIVED", f"Connected-component sizes={comp_sizes[:12]}; disconnected components are reported, never bridged by inference.")

    hard_fail = any(r["status"] == "FAIL" for r in checks)
    watch_count = sum(1 for r in checks if r["severity"] == "WATCH")
    overall = "FAIL" if hard_fail else ("PASS_WITH_WATCH" if watch_count else "PASS")
    checks.append({
        "check_id": "GT-999",
        "category": "overall",
        "severity": "HARD",
        "expected": "NONBLOCKING",
        "observed": overall,
        "status": "FAIL" if hard_fail else "PASS",
        "evidence_state": "DERIVED_GATE",
        "note": "Global topology is eligible for handoff only when no HARD check fails; WATCH values remain explicit downstream constraints.",
    })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["check_id", "category", "severity", "expected", "observed", "status", "evidence_state", "note"]
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(checks)

    detail_rows = []
    details = {
        "missing_member_nodes": missing_member_nodes,
        "zero_member_pairs": zero_member_pairs,
        "duplicate_member_node_pairs": [str(k) for k, v in duplicate_pairs.items() if v > 1],
        "beam_role_failures": beam_role_fail,
        "column_role_failures": column_role_fail,
        "invalid_cross_storey_members": invalid_cross_storey,
        "terrace_vertical_segments": terrace_vertical,
        "roof_absent_g4_g5_columns": roof_absent_vertical,
        "roof_special_as_members": roof_special_as_member,
        "missing_link_nodes": missing_link_nodes,
        "link_role_failures": link_role_fail,
        "link_support_level_failures": link_support_level_fail,
        "zero_length_rigid_links": zero_links,
        "bad_face_link_coverage": bad_face_link_coverage,
        "bad_face_member_coverage": bad_face_member_coverage,
        "roof_member_promotions": roof_member_promotions,
        "roof_z_assigned": roof_z_assigned,
        "ridge_xy_bad": ridge_xy_bad,
        "eave_centerline_created": eave_centerline_created,
        "blank_node_provenance": blank_node_prov,
        "blank_member_provenance": blank_member_prov,
        "blank_link_provenance": blank_link_prov,
        "orphan_nodes": orphan_nodes,
        "component_sizes": [str(x) for x in comp_sizes],
    }
    for kind, vals in details.items():
        detail_rows.append({"detail_type": kind, "count": str(len(vals)), "values": ";".join(vals)})
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["detail_type", "count", "values"]); w.writeheader(); w.writerows(detail_rows)

    print(f"M0G_GLOBAL_TOPOLOGY_GATE={overall} checks={len(checks)} components={len(components)} orphans={len(orphan_nodes)}")
    if hard_fail:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
