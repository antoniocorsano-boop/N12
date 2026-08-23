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
CROSS = C / "M1F_FOUNDATION_TOPOLOGY_CROSSCHECK_TAV01S_v1.csv"
BINDING = C / "M1F_TAV01A_GROUP_BINDING_CURRENT_v1.csv"
ONLY = C / "M1F_TAV01S_ONLY_MEMBER_CANDIDATES_v1.csv"
CURRENT = C / "M1F_FOUNDATION_MEMBER_CONNECTIVITY_CURRENT_v1.csv"

EXPECTED_SUPPORTS = {str(i) for i in range(1, 34)} | {"22'", "a", "b", "c", "d"}
EXPECTED_ONLY = {
    frozenset(x) for x in [
        ("5","6"),("6","7"),("7","8"),("31","28"),("28","25"),
        ("25","19"),("21","22"),("23","24"),("20","11"),("11","3"),
        ("20","21"),("19","20"),("18","19"),("23","22'"),("17","18"),
    ]
}


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def edge(a: str, b: str):
    return frozenset((a.strip(), b.strip()))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for p in [MASTER, ORIGINAL, CROSS, BINDING, ONLY, CURRENT]:
        if not p.exists():
            errors.append(f"missing artifact: {p.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    master, original, cross, binding, only, current = map(read, [MASTER, ORIGINAL, CROSS, BINDING, ONLY, CURRENT])
    master_ids = {r["entity_id"].strip() for r in master}
    if master_ids != EXPECTED_SUPPORTS:
        errors.append("PT_MASTER_CURRENT support identities differ from frozen 38-support contract")

    original_ids = [r["candidate_id"].strip() for r in original]
    cross_ids = [r["candidate_id"].strip() for r in cross]
    if len(original) != 44 or len(set(original_ids)) != 44:
        errors.append(f"expected 44 unique original TAV-01A candidates, got {len(original)}")
    if len(cross) != 44 or set(cross_ids) != set(original_ids):
        errors.append("TAV-01S crosscheck does not disposition exactly all 44 original candidates")

    by_id = {r["candidate_id"].strip(): r for r in cross}
    c15 = by_id.get("FND-C015", {})
    if c15.get("binding_state", "").strip() != "REJECTED_DERIVATION" or c15.get("promotion_state", "").strip() != "NOT_PROMOTED":
        errors.append("FND-C015 13-22 must remain rejected")
    c16 = by_id.get("FND-C016", {})
    if c16.get("binding_state", "").strip() != "REBOUND_POLYLINE_VIA_22_PRIME" or c16.get("physical_member_projection", "").strip() != "22-22'|22'-27":
        errors.append("FND-C016 must bind to 22-22' and 22'-27")

    g03 = next((r for r in binding if r["group_id"].strip() == "F1A-G03"), None)
    if not g03 or g03["armature_sequence_a"].strip() != "13-21-26-29-32" or g03["armature_sequence_b"].strip() != "22-27-30-33" or "22-22'-27-30-33" not in g03["physical_binding"]:
        errors.append("corrected G03 source/physical binding contract is not satisfied")

    only_edges = [edge(r["from_support_id"], r["to_support_id"]) for r in only]
    if len(only) != 15 or set(only_edges) != EXPECTED_ONLY or len(set(only_edges)) != 15:
        errors.append("TAV-01S-only register must contain exactly the 15 documentary physical members")
    for r in only:
        if r["topology_evidence"].strip() != "DOC_CARPENTERIA" or r["section_family_candidate"].strip() != "ND":
            errors.append(f"{r['candidate_id']}: carpenteria-only member improperly promoted beyond documentary topology")

    if len(current) != 59:
        errors.append(f"expected 59 current physical foundation members, got {len(current)}")
    ids = [r["member_id"].strip() for r in current]
    if len(ids) != len(set(ids)):
        errors.append("duplicate M1-F member_id")
    edges = [edge(r["from_support_id"], r["to_support_id"]) for r in current]
    eset = set(edges)
    if len(edges) != len(eset):
        errors.append("duplicate unordered endpoint pair")
    if edge("13","22") in eset or edge("22","27") in eset:
        errors.append("forbidden direct member 13-22 or 22-27 is present")
    if edge("22","22'") not in eset or edge("22'","27") not in eset:
        errors.append("required 22/22' physical subdivision is incomplete")
    if not EXPECTED_ONLY.issubset(eset):
        errors.append("not all 15 TAV-01S-only members were promoted")

    for r in current:
        a, b = r["from_support_id"].strip(), r["to_support_id"].strip()
        if a not in EXPECTED_SUPPORTS or b not in EXPECTED_SUPPORTS:
            errors.append(f"{r['member_id']}: endpoint outside frozen PT support set")
    only_current = [r for r in current if r["source_basis"].strip() == "DOC_TAV01S_ONLY"]
    if len(only_current) != 15:
        errors.append(f"expected 15 DOC_TAV01S_ONLY members, got {len(only_current)}")
    for r in only_current:
        if r["reinforcement_binding_status"].strip() != "ND_NOT_BOUND_FROM_TAV01A" or r["section_family_candidate"].strip() != "ND":
            errors.append(f"{r['member_id']}: TAV-01S-only reinforcement/section watch was lost")

    for pair in [edge("22","14"), edge("14","6")]:
        r = next((x for x in current if edge(x["from_support_id"], x["to_support_id"]) == pair), None)
        if not r or "22-14-6" not in r.get("note", ""):
            errors.append(f"source variant note missing for {sorted(pair)}")

    adj: dict[str, set[str]] = defaultdict(set)
    for r in current:
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
        errors.append(f"foundation graph is not one connected component over all 38 supports (covered={len(seen)})")

    section_nd = sum(r["section_family_candidate"].strip() == "ND" for r in current)
    section_watch = sum("VERIFY" in r["section_family_candidate"] or "WATCH" in r["section_family_candidate"] for r in current)
    reinf_watch = sum(r["reinforcement_binding_status"].strip() == "ND_NOT_BOUND_FROM_TAV01A" for r in current)
    if section_nd or section_watch or reinf_watch:
        warnings.append(f"topology closed; section/reinforcement watches remain: section_ND={section_nd}, section_family_watch={section_watch}, reinforcement_watch={reinf_watch}")

    summary = {
        "original_candidates": len(original),
        "rejected_derivations": sum(r["binding_state"].strip() == "REJECTED_DERIVATION" for r in cross),
        "rebound_intervals": sum(r["binding_state"].strip() == "REBOUND_POLYLINE_VIA_22_PRIME" for r in cross),
        "TAV01S_only_members": len(only),
        "current_physical_members": len(current),
        "covered_supports": len(seen),
        "connected_components": 1 if seen == EXPECTED_SUPPORTS else "CHECK",
        "section_ND": section_nd,
        "section_family_watch": section_watch,
        "reinforcement_watch": reinf_watch,
    }
    return finish(errors, warnings, summary)


def finish(errors, warnings, summary):
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-F foundation topology validation: {status}")
    for k, v in summary.items(): print(f"  {k}: {v}")
    for w in warnings: print(f"WARNING: {w}")
    for e in errors: print(f"ERROR: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
