#!/usr/bin/env python3
import argparse, json
from pathlib import Path

REQ=['reference_id','project_applicability_decision','input_parameter_sources','uncertainty_definition','units','validity_range','calibration_or_justification','human_review']

def inspect_model(m):
    missing=[]
    if not m.get('reference_id'): missing.append('reference_id')
    if m.get('calibration_state')!='CALIBRATED': missing.append('calibrated_model')
    if str(m.get('validity_range','')).upper().startswith('UNSET'): missing.append('validity_range')
    if str(m.get('parameter_provenance','')).upper().startswith('UNSET'): missing.append('input_parameter_sources')
    if str(m.get('uncertainty_model','')).upper().startswith('UNSET'): missing.append('uncertainty_definition')
    return {'model_id':m['model_id'],'mechanism':m['mechanism'],'activation_state':'BLOCKED' if missing else 'ELIGIBLE_FOR_PROJECT_ACTIVATION_REVIEW','missing_activation_requirements':missing,'scenario_output_authorized':False}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--registry',required=True,type=Path); ap.add_argument('--output',required=True,type=Path); a=ap.parse_args()
    reg=json.loads(a.registry.read_text(encoding='utf-8'))
    checks=[inspect_model(m) for m in reg['models']]
    out={'schema_version':'0.1','engine':'CEW_DEGRADATION_ENGINE_v0','status':'SAFETY_GATE_ONLY_NO_PROJECT_DEGRADATION_EXECUTED','registry_id':reg['registry_id'],'model_count':len(checks),'eligible_model_count':sum(c['activation_state'].startswith('ELIGIBLE') for c in checks),'blocked_model_count':sum(c['activation_state']=='BLOCKED' for c in checks),'models':checks,'invariants':['no project degradation values generated from scaffold models','no scenario property overlay emitted until project activation gate passes','MOD/POST outputs can never overwrite source evidence'],'next_gate':'Select technical reference and project applicability, then register calibrated/justified parameters and uncertainty definitions under human review.'}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"CEW DEGRADATION ENGINE: PASS-SAFE | models={out['model_count']} | eligible={out['eligible_model_count']} | blocked={out['blocked_model_count']}")
if __name__=='__main__': main()
