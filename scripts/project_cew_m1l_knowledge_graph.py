#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'data/canonical'
FILES=[('LOAD_MODEL',C/'M1L_LOAD_MODEL_CURRENT_v1.csv','load_id'),('LOAD_PATH',C/'M1L_LOAD_PATH_CLASSIFICATION_CURRENT_v1.csv','load_path_id'),('LOAD_DELTA',C/'M1L_HISTORICAL_VS_ASBUILT_LOAD_DELTA_REGISTER_v1.csv','delta_id')]

def rows(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def epi(raw):
    u=(raw or '').strip().upper()
    for s in ('DOC','MIS','RIF','INF','ND'):
        if u.startswith(s):return s
    if 'DOC' in u:return 'DOC'
    if 'RIF' in u:return 'RIF'
    return 'ND'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    entities=[];bindings=[];assertions=[]
    for kind,path,idcol in FILES:
        ledger=f'data/canonical/{path.name}'
        for r in rows(path):
            rid=r[idcol].strip(); ev=epi(r.get('provenance') or r.get('evidence_state') or r.get('source_basis'))
            validation=(r.get('numeric_status') or r.get('current_model_status') or r.get('delta_state') or '').strip()
            entities.append({'entity_id':rid,'entity_type':kind,'entity_class':(r.get('domain') or '').strip(),'temporal_state':'CURRENT','source_ledger':ledger,'source_record_id':rid,'validation_state':validation})
            if kind=='LOAD_PATH' and (r.get('source_zone_id') or '').strip():
                bindings.append({'binding_id':f'BIND-{rid}-ZONE','from_entity_id':rid,'relation':'CLASSIFIES_SOURCE_ZONE','to_entity_id':r['source_zone_id'].strip(),'epistemic_state':ev,'validation_state':r['current_model_status'].strip(),'source_ledger':ledger,'source_record_id':rid})
            fields=[]
            if kind=='LOAD_MODEL': fields=['model_view','load_component','application_class','numeric_status','parametric_rule','structural_binding_status','historical_model_status','current_model_status','residual','model_guard']
            elif kind=='LOAD_PATH': fields=['structural_support_class','evidence_state','historical_model_status','current_model_status','numeric_load_ready','parametric_rule','residual','model_guard']
            else: fields=['historical_model_claim','historical_omission_direct_evidence','delta_state','numeric_delta_ready','symbolic_delta_rule','required_evidence','model_rule']
            for name in fields:
                v=(r.get(name) or '').strip()
                if v: assertions.append({'assertion_id':f'ASSERT-{rid}-{name.upper()}','entity_id':rid,'property_name':name,'value':v,'unit':'source_literal','epistemic_state':ev,'validation_state':validation,'source_ledger':ledger,'source_record_id':rid})
            if kind=='LOAD_MODEL':
                nv=(r.get('numeric_value') or '').strip(); ns=(r.get('numeric_status') or '').strip().upper()
                if nv and not ns.startswith('ND') and ns not in {'NOT_NUMERIC','PARAMETRIC_ONLY','PARAMETRIC_NOT_NUMERIC'}:
                    assertions.append({'assertion_id':f'ASSERT-{rid}-NUMERIC_VALUE','entity_id':rid,'property_name':'numeric_value','value':nv,'unit':(r.get('numeric_unit') or '').strip(),'epistemic_state':ev,'validation_state':r['numeric_status'].strip(),'source_ledger':ledger,'source_record_id':rid})
    payload={'schema_version':'1.0','projection_id':'CEW-F5-M1L-LOADS-v1','authority':'DERIVED_GRAPH_PROJECTION_ONLY','entities':entities,'bindings':bindings,'assertions':assertions}
    (out/'m1l_graph_projection.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    print(f'LOAD_GRAPH_ENTITIES={len(entities)}');print(f'ZONE_BINDINGS={len(bindings)}');print(f'ASSERTIONS={len(assertions)}');print(f'NUMERIC_VALUE_ASSERTIONS={sum(1 for x in assertions if x["property_name"]=="numeric_value")}')
    return 0
if __name__=='__main__':raise SystemExit(main())
