#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data/canonical/M1A_TAV05A_GROUP_REINFORCEMENT_v1.csv"


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def epi(raw: str) -> str:
    u = (raw or "").strip().upper()
    for s in ("DOC", "MIS", "RIF", "INF", "ND"):
        if u.startswith(s): return s
    return "ND"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    src = rows(LEDGER)
    source_ledger = "data/canonical/M1A_TAV05A_GROUP_REINFORCEMENT_v1.csv"
    entities, bindings, assertions = [], [], []
    props = (("bar_quantity", "count"), ("bar_diameter_mm", "mm"), ("shape_or_length", "source_literal"), ("segment_dimensions_cm", "cm_source_literal"))
    for r in src:
        rid = r["row_id"].strip(); ev = epi(r["evidence_status"])
        entities.append({"entity_id": rid, "entity_type": "ReinforcementRecord", "entity_class": r["bar_role"].strip(), "temporal_state": "CURRENT", "source_ledger": source_ledger, "source_record_id": rid, "validation_state": r["evidence_status"].strip()})
        bindings.append({"binding_id": f"BIND-{rid}-GROUP", "from_entity_id": rid, "relation": "DOCUMENTED_IN_REINFORCEMENT_GROUP", "to_entity_id": r["group_id"].strip(), "epistemic_state": ev, "validation_state": r["binding_state"].strip(), "source_ledger": source_ledger, "source_record_id": rid})
        for name, unit in props:
            value = (r.get(name) or "").strip()
            if not value or value.upper() in {"UNKNOWN", "ND", "N/A"}: continue
            assertions.append({"assertion_id": f"ASSERT-{rid}-{name.upper()}", "entity_id": rid, "property_name": name, "value": value, "unit": unit, "epistemic_state": ev, "validation_state": r["evidence_status"].strip(), "source_ledger": source_ledger, "source_record_id": rid})
    payload = {"schema_version":"1.0","projection_id":"CEW-F5-M1A-TAV05A-REINFORCEMENT-v1","authority":"DERIVED_GRAPH_PROJECTION_ONLY","entities":entities,"bindings":bindings,"assertions":assertions}
    (out/"m1a_graph_projection.json").write_text(json.dumps(payload, indent=2)+"\n", encoding="utf-8")
    print(f"REINFORCEMENT_ENTITIES={len(entities)}"); print(f"GROUP_BINDINGS={len(bindings)}"); print(f"PROPERTY_ASSERTIONS={len(assertions)}"); print("MEMBER_STATION_BINDING=NOT_PROJECTED")
    return 0

if __name__ == "__main__": raise SystemExit(main())
