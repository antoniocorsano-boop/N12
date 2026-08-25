#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, html, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
TASKS = C / "CEW_ERW_RESOLUTION_TASKS_v1.csv"
RESIDUALS = C / "M1E_B06_REINFORCEMENT_RESIDUALS_CURRENT_v1.csv"
OBSERVATIONS = C / "CEW_OBSERVATION_REGISTRY_v1.csv"
VIEWER = C / "CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
REGIONS = C / "CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
MEMBERS = C / "M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
CONTRACT = ROOT / "automation" / "CEW_ERW_CONTRACT_v1.json"

EXPECTED = {
    "ERW-N12-001": {"residual":"M1E-B06-R08", "reference":"T5A-G01/G01-R06", "outcome":"UNREADABLE", "requested":"ND_QTY_DIAMETER"},
    "ERW-N12-002": {"residual":"M1E-B06-R09", "reference":"T5A-G07/G07-R07", "outcome":"UNREADABLE", "requested":"ND_QTY_DIAMETER"},
    "ERW-N12-003": {"residual":"M1E-B06-R10", "reference":"T5A-G05/G05-R04", "outcome":"UNREADABLE", "requested":"DOC_DIRECT_PARTIAL+ND_REMAINDER"},
    "ERW-N12-004": {"residual":"M1E-B06-R11", "reference":"T6A-G03", "outcome":"UNBOUND", "requested":"ND_MEMBER_BINDING"},
}

def rows(p):
    with p.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def one(items,key,val):
    m=[r for r in items if r.get(key,"").strip()==val]
    if len(m)!=1: raise AssertionError(f"expected one {key}={val}, got {len(m)}")
    return m[0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    task_rows, residual_rows, obs_rows, viewer_rows, region_rows, member_rows = map(rows,[TASKS,RESIDUALS,OBSERVATIONS,VIEWER,REGIONS,MEMBERS])
    workspaces=[]
    for tid,spec in EXPECTED.items():
        task=one(task_rows,"task_id",tid); residual=one(residual_rows,"residual_id",spec["residual"])
        obs=one(obs_rows,"reference_item",spec["reference"]); viewer=one(viewer_rows,"task_id",tid)
        region=one(region_rows,"evidence_region_id",obs["evidence_region_id"].strip())
        if task["residual_id"].strip()!=spec["residual"]: raise AssertionError("task residual drift")
        if viewer["binding_state"].strip()!="READY": raise AssertionError("viewer not READY")
        if obs["structural_binding"].strip(): raise AssertionError("source observation acquired structural binding")
        candidates=[]; model={}
        if tid in ("ERW-N12-001","ERW-N12-002"):
            candidates=[
              {"candidate_id":tid+"-CAND-INFER", "interpretation":"Fill unreadable quantity/diameter from symmetry, context or analogy", "status":"FORBIDDEN", "selectable":False},
              {"candidate_id":tid+"-CAND-UNREADABLE", "interpretation":"Retain directly readable length and keep quantity/diameter ND", "status":"SUPPORTED_DISPOSITION", "selectable":True}
            ]
        elif tid=="ERW-N12-003":
            candidates=[
              {"candidate_id":tid+"-CAND-INFER", "interpretation":"Complete missing sagomato dimensions by analogy", "status":"FORBIDDEN", "selectable":False},
              {"candidate_id":tid+"-CAND-UNREADABLE", "interpretation":"Retain DOC_DIRECT_PARTIAL graphic continuation and keep missing dimensions ND", "status":"SUPPORTED_DISPOSITION", "selectable":True}
            ]
        else:
            member=one(member_rows,"source_member_id","G5-B017")
            if (member["support_i"].strip(),member["support_j"].strip()) != ("12","19"): raise AssertionError("G5-B017 topology drift")
            model={"candidate_member":{"source_member_id":"G5-B017","support_i":"12","support_j":"19","geometric_length_m":member["geometric_length_m"].strip(),"note":member["note"].strip()}}
            candidates=[
              {"candidate_id":tid+"-CAND-BIND-G5-B017", "interpretation":"Bind T6A-G03 to G5-B017", "status":"REJECTED_BY_CURRENT_EVIDENCE", "selectable":False},
              {"candidate_id":tid+"-CAND-UNBOUND", "interpretation":"Retain T6A-G03 as documentary scheme with member binding UNBOUND", "status":"SUPPORTED_DISPOSITION", "selectable":True}
            ]
        selected=[c for c in candidates if c["selectable"]]
        if len(selected)!=1: raise AssertionError("exactly one supported reference disposition required")
        decision={"decision_id":tid+"-REFERENCE-DECISION", "task_id":tid, "outcome":spec["outcome"], "selected_candidate":selected[0]["candidate_id"], "requested_epistemic_state":spec["requested"], "review_view":viewer["deep_link"].strip(), "reviewer":"DETERMINISTIC_REFERENCE_CASE", "canonical_write":False}
        workspaces.append({"workspace_id":"CEW-F6-"+tid+"-v1","authority":contract["workspace_authority"],"task":task,"residual":residual,"source":{"observation":obs,"evidence_region":region,"viewer_binding":viewer},"model":model,"candidates":candidates,"reference_disposition_receipt":decision,"canonical_mutation":"FORBIDDEN"})
    bundle={"schema_version":"1.0","queue_id":"CEW-F6-ERW-N12-QUEUE-v1","authority":contract["workspace_authority"],"task_count":len(workspaces),"workspaces":workspaces,"canonical_mutation":"FORBIDDEN"}
    (out/"erw_queue_bundle.json").write_text(json.dumps(bundle,indent=2)+"\n",encoding="utf-8")
    cards=[]
    for w in workspaces:
        t=w["task"]; d=w["reference_disposition_receipt"]; o=w["source"]["observation"]
        cards.append(f"<section><h2>{html.escape(t['task_id'])} · {html.escape(t['residual_id'])}</h2><p>{html.escape(t['question'])}</p><p><b>Source:</b> {html.escape(o['reference_item'])} — {html.escape(o['literal_or_value'])}</p><p><b>Known:</b> {html.escape(t['known_claims'])}</p><p><b>Unknown:</b> {html.escape(t['unknown_claims'])}</p><p><b>Disposition:</b> {html.escape(d['outcome'])}</p><p><b>Viewer:</b> <code>{html.escape(d['review_view'])}</code></p></section>")
    page="<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>CEW F6 ERW Queue</title><style>body{font-family:system-ui,sans-serif;margin:2rem;max-width:1100px}section{border:1px solid #bbb;padding:1rem;margin:1rem 0}code{white-space:pre-wrap}</style></head><body><h1>CEW Evidence Resolution Workspace — N12 queue</h1><p>Derived review workspace only. No canonical write or epistemic promotion.</p>"+"".join(cards)+"</body></html>"
    (out/"index.html").write_text(page,encoding="utf-8")
    print("ERW_QUEUE_BUILT"); print("TASKS=4"); print("UNREADABLE=3"); print("UNBOUND=1"); print("CANONICAL_MUTATION=FORBIDDEN")
    return 0

if __name__=="__main__": raise SystemExit(main())
