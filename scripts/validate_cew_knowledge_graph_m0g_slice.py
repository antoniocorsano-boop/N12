#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_KNOWLEDGE_GRAPH_CONTRACT_v1.json"
MEMBERS = ROOT / "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
HANDOFF = ROOT / "data/canonical/M0G_GEOMETRY_HANDOFF_v1.json"
MILESTONES = ROOT / "data/canonical/CEW_SYSTEM_MILESTONES_v1.csv"
ORDER = {"ND": 0, "INF": 1, "RIF": 2, "MIS": 3, "DOC": 4}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def epi(raw: str) -> str:
    raw = (raw or "").strip().upper()
    for state in ("DOC", "MIS", "RIF", "INF", "ND"):
        if raw.startswith(state):
            return state
    return "ND"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--projection", required=True)
    args = ap.parse_args()
    projection = json.loads(Path(args.projection).read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-KNOWLEDGE-GRAPH-v1":
        raise AssertionError("unexpected knowledge graph contract")
    if any(contract["authority_invariants"][k] is not False for k in (
        "projection_may_modify_source_ledger", "projection_may_reopen_m0g",
        "projection_may_raise_epistemic_state", "projection_may_invent_missing_property",
        "projection_may_collapse_distinct_evidence_states", "graph_is_primary_evidence"
    )):
        raise AssertionError("knowledge graph authority boundary weakened")

    status = {r["milestone_id"].strip(): r["status"].strip() for r in rows(MILESTONES)}
    if status.get("CEW-F5") != "IN_PROGRESS" or any(status.get(x) != "COMPLETE" for x in ("CEW-F0","CEW-F1","CEW-F2","CEW-F3","CEW-F4")):
        raise AssertionError("F5 milestone governance invalid")

    members = rows(MEMBERS)
    source = {r["member_id"].strip(): r for r in members}
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    expected = int(handoff["frozen_inventory"]["ordinary_structural_members"])
    if len(source) != expected:
        raise AssertionError("source member count differs from frozen handoff")

    entities = projection["entities"]
    bindings = projection["bindings"]
    assertions = projection["assertions"]
    if projection.get("authority") != "DERIVED_GRAPH_PROJECTION_ONLY":
        raise AssertionError("graph projection authority drift")
    if len(entities) != expected or len({e["entity_id"] for e in entities}) != expected:
        raise AssertionError("entity projection count/identity mismatch")
    if len(bindings) != expected * 2:
        raise AssertionError("each member must preserve exactly two endpoint bindings")

    for e in entities:
        r = source[e["entity_id"]]
        if e["entity_class"] != r["member_class"].strip() or e["storey_id"] != r["storey_id"].strip():
            raise AssertionError(f"entity semantics changed: {e['entity_id']}")
        if e["validation_state"] != r["validation_state"].strip() or e["temporal_state"] != "CURRENT":
            raise AssertionError(f"entity state changed: {e['entity_id']}")

    by_member = {}
    for b in bindings:
        by_member.setdefault(b["from_entity_id"], []).append(b)
    for mid, r in source.items():
        bs = by_member.get(mid, [])
        endpoints = {(b["relation"], b["to_entity_id"]) for b in bs}
        expected_endpoints = {("STARTS_AT_NODE", r["node_i"].strip()), ("ENDS_AT_NODE", r["node_j"].strip())}
        if endpoints != expected_endpoints:
            raise AssertionError(f"endpoint binding changed: {mid}")
        if any(b["epistemic_state"] != epi(r["connectivity_evidence"]) for b in bs):
            raise AssertionError(f"connectivity evidence promoted/collapsed: {mid}")

    expected_sections = {mid: r for mid, r in source.items() if r["section_cm"].strip()}
    if len(assertions) != len(expected_sections):
        raise AssertionError("section assertion count mismatch")
    for a in assertions:
        r = expected_sections[a["entity_id"]]
        if a["property_name"] != "section_cm" or a["value"] != r["section_cm"].strip():
            raise AssertionError(f"section value changed: {a['entity_id']}")
        if a["epistemic_state"] != epi(r["section_evidence"]):
            raise AssertionError(f"section evidence changed: {a['entity_id']}")
        if a["validation_state"] != r["validation_state"].strip():
            raise AssertionError(f"section validation state changed: {a['entity_id']}")

    missing_section_entities = [mid for mid, r in source.items() if not r["section_cm"].strip()]
    asserted_ids = {a["entity_id"] for a in assertions}
    if any(mid in asserted_ids for mid in missing_section_entities):
        raise AssertionError("graph invented missing section property")

    print("KNOWLEDGE_GRAPH_M0G_SLICE_PASS")
    print(f"STRUCTURAL_ENTITIES={len(entities)}")
    print(f"ENDPOINT_BINDINGS={len(bindings)}")
    print(f"SECTION_ASSERTIONS={len(assertions)}")
    print(f"MISSING_SECTION_PROPERTIES_NOT_INVENTED={len(missing_section_entities)}")
    print("AUTHORITY=DERIVED_GRAPH_PROJECTION_ONLY")
    print("M0G_REOPEN=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
