#!/usr/bin/env python3
import argparse, json
from pathlib import Path

IMPACT={"LOW":1,"MEDIUM":2,"HIGH":3,"VERY_HIGH":4}
INV={"ZERO":0,"LOW":1,"LOW_TO_MEDIUM":2,"MEDIUM":2,"ZERO_TO_MEDIUM":1,"MEDIUM_TO_HIGH":3,"HIGH":4,"ZERO_TO_HIGH":2}
COST={"LOW":1,"LOW_TO_MEDIUM":2,"MEDIUM":2,"MEDIUM_TO_HIGH":3,"HIGH":4}

DEFAULT_ACTIONS={
"NUMERIC_LOADS_MASSES_AND_COMBINATIONS": {"candidate_class":"DOCUMENTARY_RECOVERY","method":"recover and transcribe historical calculation load records (including RC-P13), then reconcile with current stratigraphies/use before any new physical survey","invasiveness":"ZERO","relative_cost":"LOW","expected_uncertainty_reduction":"HIGH","unlocks":["current load model","mass model","assessment combinations"]},
"FOUNDATION_SECTION_AND_REINFORCEMENT_COVERAGE": {"candidate_class":"DOCUMENTARY_RECOVERY","method":"targeted rereading of primary foundation reinforcement/detail sources for the 15 unbound P07 incidences; only unresolved incidences progress to local survey/opening","invasiveness":"ZERO_TO_MEDIUM","relative_cost":"LOW_TO_MEDIUM","expected_uncertainty_reduction":"HIGH","unlocks":["foundation member verification scope"]},
"SUPERSTRUCTURE_REINFORCEMENT_RESIDUALS": {"candidate_class":"DOCUMENTARY_RECOVERY","method":"claim-scoped HiRes rereading of only the residual reinforcement elements, followed by cover-meter/local opening solely where documentary closure fails","invasiveness":"ZERO_TO_MEDIUM","relative_cost":"LOW_TO_MEDIUM","expected_uncertainty_reduction":"HIGH","unlocks":["affected member checks"]}
}

def score(c):
    # Advisory heuristic, explicitly not VoI.
    coverage=max(1,len(c.get("potentially_closes",[])))
    red=IMPACT.get(c.get("expected_uncertainty_reduction","MEDIUM"),2)
    inv=INV.get(c.get("invasiveness","MEDIUM"),2)
    cost=COST.get(c.get("relative_cost","MEDIUM"),2)
    deps=len(c.get("dependency_ids",[]))
    return 10*coverage+4*red-2*inv-cost-deps

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--profile",type=Path,required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    p=json.loads(a.profile.read_text(encoding="utf-8"))
    blockers={b["domain"]:b for b in p["blocking_domains"]}
    candidates=[]
    for raw in p.get("investigation_candidates",[]):
        domain=raw["target_parameter_or_claim"]
        candidates.append({
            "investigation_id":raw["investigation_id"],"target_domain":domain,
            "candidate_class":"SPECIALIST_REVIEW" if domain=="CURRENT_GEOTECHNICAL_MODEL" else "NON_DESTRUCTIVE_SCREENING" if domain=="CURRENT_CONCRETE_AND_KNOWLEDGE_LEVEL" else "TARGETED_OPENING_OR_SURVEY",
            "method":raw["test_method"],"expected_uncertainty_reduction":raw["expected_uncertainty_reduction"],"invasiveness":raw["invasiveness"],
            "relative_cost":"MEDIUM_TO_HIGH" if domain=="CURRENT_GEOTECHNICAL_MODEL" else "MEDIUM",
            "dependency_ids":[],"potentially_closes":[blockers[domain]["id"]] if domain in blockers else [],"unlocks":raw["affected_outputs"],"decision_state":"CANDIDATE"
        })
    known={c["target_domain"] for c in candidates}
    for domain,b in blockers.items():
        if domain in known: continue
        d=DEFAULT_ACTIONS.get(domain)
        if not d: continue
        candidates.append({"investigation_id":"CEW-AUTO-"+b["id"],"target_domain":domain,**d,"dependency_ids":[],"potentially_closes":[b["id"]],"decision_state":"PROPOSED_EVIDENCE_RECOVERY"})
    # Staging: documentary closure first; invasive escalation remains conditional.
    for c in candidates:
        c["heuristic_information_priority_score"]=score(c)
        c["ranking_status"]="ADVISORY_NOT_VALUE_OF_INFORMATION"
    candidates.sort(key=lambda x:(-x["heuristic_information_priority_score"], x["investigation_id"]))
    for i,c in enumerate(candidates,1): c["rank_v0"]=i
    covered={x for c in candidates for x in c["potentially_closes"]}
    all_ids={b["id"] for b in blockers.values()}
    out={"schema_version":"0.1","planner":"CEW_INVESTIGATION_PLANNER_v0","project_id":p["project_id"],"status":"ADVISORY_PLAN_NOT_EVIDENCE","value_of_information_ready":False,"blocker_count":len(blockers),"covered_blocker_count":len(covered & all_ids),"uncovered_blockers":sorted(all_ids-covered),"candidates":candidates,"execution_policy":["perform documentary recovery before destructive escalation where applicable","record every real result as new evidence through the normal CEW evidence pipeline","re-run assessment and planner after each material evidence update","do not infer LC/FC, geotechnical parameters, material strength or reinforcement from the plan itself"],"next_capability_gate":"VALUE_OF_INFORMATION requires decision/loss model, priors, likelihoods, test costs and structural response model."}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if out["uncovered_blockers"]: raise SystemExit("Uncovered blockers: "+str(out["uncovered_blockers"]))
    print(f"CEW INVESTIGATION PLANNER: PASS | blockers={len(blockers)} | candidates={len(candidates)} | all-covered")
if __name__=="__main__": main()
