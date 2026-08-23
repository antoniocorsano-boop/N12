#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
MASTER = C / "PT_MASTER_CURRENT.csv"
ORIGINAL = C / "M1F_FOUNDATION_MEMBER_CANDIDATES_FROM_TAV01A_v1.csv"
CROSS = C / "M1F_TAV01A_TAV01S_CROSSCHECK_v1.csv"
TOPO = C / "M1F_FOUNDATION_TOPOLOGY_CURRENT_v1.csv"
GATE = C / "M1F_FOUNDATION_TOPOLOGY_GATE_v1.csv"

EXPECTED_SUPPORTS = {str(i) for i in range(1, 34)} | {"22'", "a", "b", "c", "d"}


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def edge(a: str, b: str):
    return frozenset((a.strip(), b.strip()))


def finish(errors, warnings, summary):
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-F foundation topology validation: {status}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for p in [MASTER, ORIGINAL, CROSS, TOPO, GATE]:
        if not p.exists():
            errors.append(f"missing artifact: {p.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    master, original, cross, topo, gate = map(read, [MASTER, ORIGINAL, CROSS, TOPO, GATE])

    # Frozen M0-G support identity is consumed, never rewritten by M1-F.
    master_ids = {r["entity_id"].strip() for r in master}
    if master_ids != EXPECTED_SUPPORTS:
        errors.append("PT_MASTER_CURRENT differs from the frozen 38-support identity contract")

    # All original TAV-01A candidates must be explicitly dispositioned by carpenteria crosscheck.
    oids = [r["candidate_id"].strip() for r in original]
    cids = [r["candidate_id"].strip() for r in cross]
    if len(original) != 44 or len(set(oids)) != 44:
        errors.append(f"expected 44 unique TAV-01A candidates, got {len(original)}")
    if len(cross) != 44 or set(cids) != set(oids):
        errors.append("crosscheck does not disposition exactly all 44 TAV-01A candidates")
    by_id = {r["candidate_id"].strip(): r for r in cross}
    if by_id.get("FND-C015", {}).get("promotion_state", "").strip() != "REJECTED_AS_PHYSICAL_EDGE":
        errors.append("FND-C015 13-22 must remain rejected as physical geometry")
    c016 = by_id.get("FND-C016", {})
    if c016.get("promotion_state", "").strip() != "TRANSFORMED_TO_PHYSICAL_PATH" or c016.get("tav01s_result", "").strip() != "SCHEMATIC_SPAN_CROSSES_22_PRIME":
        errors.append("FND-C016 22-27 must remain transformed through distinct support 22'")

    # Canonical carpenteria-led topology.
    if len(topo) != 58:
        errors.append(f"expected 58 physical foundation members, got {len(topo)}")
    mids = [r["foundation_member_id"].strip() for r in topo]
    if len(mids) != len(set(mids)):
        errors.append("duplicate foundation_member_id")
    edges = [edge(r["from_support_id"], r["to_support_id"]) for r in topo]
    eset = set(edges)
    if len(edges) != len(eset):
        errors.append("duplicate unordered foundation endpoint pair")

    for r in topo:
        a, b = r["from_support_id"].strip(), r["to_support_id"].strip()
        if a not in EXPECTED_SUPPORTS or b not in EXPECTED_SUPPORTS:
            errors.append(f"{r['foundation_member_id']}: endpoint outside frozen support set")

    # Critical source conflicts/geometry decisions.
    for forbidden in [edge("13","22"), edge("22","27"), edge("20","21")]:
        if forbidden in eset:
            errors.append(f"forbidden/nonexistent direct member promoted: {sorted(forbidden)}")
    for required in [edge("22","22'"), edge("22'","27"), edge("22'","23")]:
        if required not in eset:
            errors.append(f"required carpenteria member missing: {sorted(required)}")

    by_edge = {edge(r["from_support_id"], r["to_support_id"]): r for r in topo}
    e2222p = by_edge[edge("22","22'")]
    if e2222p["section_family_state"].strip() != "OPEN_SECTION_BINDING" or e2222p["reinforcement_binding_state"].strip() != "GROUP_CONTINUITY_RELATION_WATCH":
        errors.append("22-22' must stay DOC geometry with open section/reinforcement binding")
    e22p27 = by_edge[edge("22'","27")]
    if e22p27["section_family_state"].strip() != "FND-SEC-A_SUPPORTED" or e22p27["reinforcement_binding_state"].strip() != "SCHEMATIC_22_27_SPLIT_AT_22_PRIME":
        errors.append("22'-27 must retain supported G03 binding with schematic-span watch")

    # One connected mesh, every support degree >=2.
    adj: dict[str, set[str]] = defaultdict(set)
    for r in topo:
        a, b = r["from_support_id"].strip(), r["to_support_id"].strip()
        adj[a].add(b); adj[b].add(a)
    seen: set[str] = set()
    if adj:
        start = next(iter(adj)); seen = {start}; q = deque([start])
        while q:
            n = q.popleft()
            for m in adj[n]:
                if m not in seen:
                    seen.add(m); q.append(m)
    if set(adj) != EXPECTED_SUPPORTS or seen != EXPECTED_SUPPORTS:
        errors.append(f"foundation graph is not one component over all 38 supports (reached {len(seen)})")
    degree1 = sorted(k for k, v in adj.items() if len(v) <= 1)
    if degree1:
        errors.append(f"isolated/degree-1 supports found: {degree1}")

    direct_cross = sum(r["topology_evidence"].strip() == "DOC_TAV01S+DOC_TAV01A" for r in topo)
    no_direct_armature = sum(r["section_family_state"].strip() == "OPEN_SECTION_BINDING" for r in topo)
    if direct_cross != 42:
        errors.append(f"expected 42 directly cross-confirmed members, got {direct_cross}")
    if no_direct_armature != 15:
        errors.append(f"expected 15 carpenteria members without direct autonomous TAV-01A binding, got {no_direct_armature}")

    gate_by_id = {r["check_id"].strip(): r for r in gate}
    expected_gate = "PASS_TOPOLOGY_WITH_SECTION_REINFORCEMENT_WATCH"
    if gate_by_id.get("M1F-TOP-GATE", {}).get("actual", "").strip() != expected_gate:
        errors.append("M1-F topology gate is not at the expected PASS_WITH_WATCH state")

    section_family_watch = sum("VERIFY" in r["section_family_state"] or "WATCH" in r["section_family_state"] for r in topo)
    if no_direct_armature or section_family_watch:
        warnings.append(f"topology closed; section/reinforcement closure remains open: open_section_binding={no_direct_armature}, section_family_watch={section_family_watch}")

    summary = {
        "physical_supports": len(seen),
        "physical_members": len(topo),
        "connected_components": 1 if seen == EXPECTED_SUPPORTS else "CHECK",
        "direct_TAV01S_plus_TAV01A": direct_cross,
        "open_section_binding": no_direct_armature,
        "section_family_watch": section_family_watch,
        "rejected_direct_candidates": 1,
        "transformed_schematic_spans": 1,
    }
    return finish(errors, warnings, summary)


if __name__ == "__main__":
    sys.exit(main())
