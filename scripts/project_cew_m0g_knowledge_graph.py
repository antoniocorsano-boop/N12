#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMBERS = ROOT / "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
HANDOFF = ROOT / "data/canonical/M0G_GEOMETRY_HANDOFF_v1.json"


def epi(raw: str) -> str:
    raw = (raw or "").strip().upper()
    for state in ("DOC", "MIS", "RIF", "INF", "ND"):
        if raw.startswith(state):
            return state
    return "ND"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with MEMBERS.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    expected = int(handoff["frozen_inventory"]["ordinary_structural_members"])
    if len(rows) != expected:
        raise AssertionError(f"M0-G member inventory drift: rows={len(rows)} expected={expected}")

    entities = []
    bindings = []
    assertions = []
    source_ledger = "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"

    for r in rows:
        mid = r["member_id"].strip()
        entities.append({
            "entity_id": mid,
            "entity_type": "StructuralMember",
            "entity_class": r["member_class"].strip(),
            "storey_id": r["storey_id"].strip(),
            "temporal_state": "CURRENT",
            "source_ledger": source_ledger,
            "source_record_id": mid,
            "validation_state": r["validation_state"].strip()
        })
        conn_epi = epi(r["connectivity_evidence"])
        for role, node in (("STARTS_AT_NODE", r["node_i"].strip()), ("ENDS_AT_NODE", r["node_j"].strip())):
            bindings.append({
                "binding_id": f"BIND-{mid}-{role}",
                "from_entity_id": mid,
                "relation": role,
                "to_entity_id": node,
                "epistemic_state": conn_epi,
                "source_ledger": source_ledger,
                "source_record_id": mid
            })
        section = r["section_cm"].strip()
        if section:
            section_epi = epi(r["section_evidence"])
            assertions.append({
                "assertion_id": f"ASSERT-{mid}-SECTION",
                "entity_id": mid,
                "property_name": "section_cm",
                "value": section,
                "unit": "cm",
                "epistemic_state": section_epi,
                "validation_state": r["validation_state"].strip(),
                "source_ledger": source_ledger,
                "source_record_id": mid
            })

    payload = {
        "schema_version": "1.0",
        "projection_id": "CEW-F5-M0G-MEMBERS-v1",
        "source_handoff": "N12_M0G_GEOMETRY_HANDOFF",
        "authority": "DERIVED_GRAPH_PROJECTION_ONLY",
        "entities": entities,
        "bindings": bindings,
        "assertions": assertions
    }
    (out / "m0g_graph_projection.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"GRAPH_ENTITIES={len(entities)}")
    print(f"GRAPH_BINDINGS={len(bindings)}")
    print(f"GRAPH_SECTION_ASSERTIONS={len(assertions)}")
    print("M0G_SOURCE_MUTATION=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
