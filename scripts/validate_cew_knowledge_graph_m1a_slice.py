#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data/canonical/M1A_TAV05A_GROUP_REINFORCEMENT_v1.csv"
CONTRACT = ROOT / "automation/CEW_KNOWLEDGE_GRAPH_CONTRACT_v1.json"
MILESTONES = ROOT / "data/canonical/CEW_SYSTEM_MILESTONES_v1.csv"


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def epi(raw: str) -> str:
    u=(raw or "").strip().upper()
    for s in ("DOC","MIS","RIF","INF","ND"):
        if u.startswith(s): return s
    return "ND"
def valid_f5_governance(ms: dict[str,str]) -> bool:
    return ms.get("CEW-F5") in {"IN_PROGRESS","COMPLETE"}
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--projection", required=True); a=ap.parse_args()
    p=json.loads(Path(a.projection).read_text(encoding="utf-8")); c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if p.get("authority") != "DERIVED_GRAPH_PROJECTION_ONLY": raise AssertionError("authority drift")
    if c.get("projection_slices",{}).get("M1A_REINFORCEMENT") not in {"IN_SCOPE","PASS"}: raise AssertionError("M1A not authorized in contract")
    ms={r["milestone_id"].strip():r["status"].strip() for r in rows(MILESTONES)}
    if not valid_f5_governance(ms): raise AssertionError("F5 milestone governance invalid for M1A slice")
    src=rows(LEDGER); byid={r["row_id"].strip():r for r in src}
    if len(src)!=58: raise AssertionError(f"TAV05A reinforcement inventory drift: {len(src)} != 58")
    ents=p["entities"]; binds=p["bindings"]; ass=p["assertions"]
    if len(ents)!=58 or {e["entity_id"] for e in ents} != set(byid): raise AssertionError("reinforcement entity identity mismatch")
    if len(binds)!=58: raise AssertionError("exactly one group binding required per source row")
    for e in ents:
        r=byid[e["entity_id"]]
        if e["entity_class"] != r["bar_role"].strip() or e["validation_state"] != r["evidence_status"].strip(): raise AssertionError(f"entity semantics changed: {e['entity_id']}")
    for b in binds:
        r=byid[b["from_entity_id"]]
        if b["relation"] != "DOCUMENTED_IN_REINFORCEMENT_GROUP" or b["to_entity_id"] != r["group_id"].strip(): raise AssertionError(f"group binding changed: {b['from_entity_id']}")
        if b["validation_state"] != r["binding_state"].strip() or b["epistemic_state"] != epi(r["evidence_status"]): raise AssertionError(f"binding state changed: {b['from_entity_id']}")
    amap={(x["entity_id"],x["property_name"]):x for x in ass}
    for rid,r in byid.items():
        ev=epi(r["evidence_status"])
        for name in ("bar_quantity","bar_diameter_mm","shape_or_length","segment_dimensions_cm"):
            raw=(r.get(name) or "").strip(); key=(rid,name)
            if not raw or raw.upper() in {"UNKNOWN","ND","N/A"}:
                if key in amap: raise AssertionError(f"missing/UNKNOWN value invented: {rid}/{name}")
            elif key not in amap or amap[key]["value"] != raw or amap[key]["epistemic_state"] != ev or amap[key]["validation_state"] != r["evidence_status"].strip(): raise AssertionError(f"source property changed: {rid}/{name}")
    for rid in ("T5A-G01-R06","T5A-G07-R07"):
        if (rid,"bar_quantity") in amap or (rid,"bar_diameter_mm") in amap: raise AssertionError(f"unreadable quantity/diameter promoted: {rid}")
    r="T5A-G05-R04"
    if amap[(r,"segment_dimensions_cm")]["value"] != byid[r]["segment_dimensions_cm"].strip() or "..." not in amap[(r,"segment_dimensions_cm")]["value"]: raise AssertionError("G05-R04 partial dimension was completed")
    if any(b["relation"] != "DOCUMENTED_IN_REINFORCEMENT_GROUP" for b in binds): raise AssertionError("member/station binding invented")
    print("KNOWLEDGE_GRAPH_M1A_SLICE_PASS"); print("REINFORCEMENT_ENTITIES=58"); print("UNREADABLE_QUANTITY_DIAMETER_PRESERVED=2"); print("DIRECT_PARTIAL_DIMENSION_PRESERVED=1"); print("MEMBER_STATION_BINDING_NOT_INVENTED=PASS"); print("AUTHORITY=DERIVED_GRAPH_PROJECTION_ONLY"); print("POST_CLOSURE_STATE=F5_PHASE_MONOTONIC")
    return 0

if __name__ == "__main__": raise SystemExit(main())