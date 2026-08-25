#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; C=ROOT/'data/canonical'
SOURCES=[('LOAD_MODEL',C/'M1L_LOAD_MODEL_CURRENT_v1.csv','load_id'),('LOAD_PATH',C/'M1L_LOAD_PATH_CLASSIFICATION_CURRENT_v1.csv','load_path_id'),('LOAD_DELTA',C/'M1L_HISTORICAL_VS_ASBUILT_LOAD_DELTA_REGISTER_v1.csv','delta_id')]
CONTRACT=ROOT/'automation/CEW_KNOWLEDGE_GRAPH_CONTRACT_v1.json'; MILESTONES=C/'CEW_SYSTEM_MILESTONES_v1.csv'
def rows(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def epi(raw):
    u=(raw or '').strip().upper()
    for s in ('DOC','MIS','RIF','INF','ND'):
        if u.startswith(s):return s
    if 'DOC' in u:return 'DOC'
    if 'RIF' in u:return 'RIF'
    return 'ND'
def valid_f5_governance(ms):
    return ms.get('CEW-F5') in {'IN_PROGRESS','COMPLETE'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--projection',required=True);a=ap.parse_args();p=json.loads(Path(a.projection).read_text(encoding='utf-8'))
    contract=json.loads(CONTRACT.read_text(encoding='utf-8'))
    if contract.get('projection_slices',{}).get('M1L_LOADS') not in {'IN_SCOPE','PASS'}:raise AssertionError('M1L not authorized')
    if p.get('authority')!='DERIVED_GRAPH_PROJECTION_ONLY':raise AssertionError('authority drift')
    ms={r['milestone_id'].strip():r['status'].strip() for r in rows(MILESTONES)}
    if not valid_f5_governance(ms):raise AssertionError('F5 milestone governance invalid for M1L slice')
    src={}; expected_kind={}
    for kind,path,idcol in SOURCES:
        for r in rows(path):
            rid=r[idcol].strip();src[rid]=r;expected_kind[rid]=kind
    if (sum(1 for k in expected_kind.values() if k=='LOAD_MODEL'),sum(1 for k in expected_kind.values() if k=='LOAD_PATH'),sum(1 for k in expected_kind.values() if k=='LOAD_DELTA'))!=(16,7,6):raise AssertionError('M1L source inventory drift')
    ents=p['entities'];binds=p['bindings'];ass=p['assertions']; ids={e['entity_id'] for e in ents}
    if len(ents)!=29 or ids!=set(src):raise AssertionError('M1L entity identity/count mismatch')
    for e in ents:
        r=src[e['entity_id']]
        if e['entity_type']!=expected_kind[e['entity_id']] or e['entity_class']!=(r.get('domain') or '').strip():raise AssertionError(f'entity changed: {e["entity_id"]}')
    expected_zone={(rid,r['source_zone_id'].strip()) for rid,r in src.items() if expected_kind[rid]=='LOAD_PATH' and (r.get('source_zone_id') or '').strip()}
    actual_zone={(b['from_entity_id'],b['to_entity_id']) for b in binds if b['relation']=='CLASSIFIES_SOURCE_ZONE'}
    if actual_zone!=expected_zone or len(binds)!=len(expected_zone):raise AssertionError('source-zone binding drift/invention')
    numeric=[x for x in ass if x['property_name']=='numeric_value']; source_numeric=[]
    for rid,r in src.items():
        if expected_kind[rid]!='LOAD_MODEL':continue
        nv=(r.get('numeric_value') or '').strip(); ns=(r.get('numeric_status') or '').strip().upper()
        if nv and not ns.startswith('ND') and ns not in {'NOT_NUMERIC','PARAMETRIC_ONLY','PARAMETRIC_NOT_NUMERIC'}:source_numeric.append((rid,nv))
    if source_numeric:raise AssertionError(f'current source unexpectedly contains ready numeric loads: {source_numeric}')
    if numeric:raise AssertionError('numeric load value invented from ND/parametric records')
    amap={(x['entity_id'],x['property_name']):x for x in ass}
    for rid,r in src.items():
        kind=expected_kind[rid]; ev=epi(r.get('provenance') or r.get('evidence_state') or r.get('source_basis'))
        fields={'LOAD_MODEL':['numeric_status','parametric_rule','structural_binding_status','historical_model_status','current_model_status','residual','model_guard'],'LOAD_PATH':['structural_support_class','evidence_state','historical_model_status','current_model_status','numeric_load_ready','parametric_rule','residual','model_guard'],'LOAD_DELTA':['historical_omission_direct_evidence','delta_state','numeric_delta_ready','symbolic_delta_rule','model_rule']}[kind]
        for f in fields:
            v=(r.get(f) or '').strip()
            if v and ((rid,f) not in amap or amap[(rid,f)]['value']!=v or amap[(rid,f)]['epistemic_state']!=ev):raise AssertionError(f'classification/rule changed: {rid}/{f}')
    if any((r.get('numeric_delta_ready') or '').strip().upper()!='NO' for rid,r in src.items() if expected_kind[rid]=='LOAD_DELTA'):raise AssertionError('numeric delta readiness drift')
    print('KNOWLEDGE_GRAPH_M1L_SLICE_PASS');print('LOAD_MODEL_ENTITIES=16');print('LOAD_PATH_ENTITIES=7');print('LOAD_DELTA_ENTITIES=6');print(f'ZONE_BINDINGS={len(expected_zone)}');print('NUMERIC_LOAD_ASSERTIONS=0');print('NUMERIC_DELTA_READY=0');print('ND_AND_PARAMETRIC_STATE_PRESERVED=PASS');print('AUTHORITY=DERIVED_GRAPH_PROJECTION_ONLY');print('POST_CLOSURE_STATE=F5_PHASE_MONOTONIC')
    return 0
if __name__=='__main__':raise SystemExit(main())