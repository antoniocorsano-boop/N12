#!/usr/bin/env python3
from __future__ import annotations

import csv,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CONTRACT=ROOT/'automation/CEW_KNOWLEDGE_GRAPH_CONTRACT_v1.json'; MANIFEST=ROOT/'knowledge/KNOWLEDGE_MANIFEST.json'; REGISTRY=ROOT/'knowledge/ARTIFACT_REGISTRY_CEW_KNOWLEDGE_GRAPH_PATCH_v1.csv'; MILESTONES=ROOT/'data/canonical/CEW_SYSTEM_MILESTONES_v1.csv'
def rows(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def run(*args):
    cp=subprocess.run([sys.executable,*args],cwd=ROOT,check=True,text=True,capture_output=True);print(cp.stdout,end='');return cp.stdout
def valid_governance(status):
    return status.get('CEW-F5') in {'IN_PROGRESS','COMPLETE'}
def main():
    c=json.loads(CONTRACT.read_text(encoding='utf-8'))
    if c.get('acceptance_gate')!='KNOWLEDGE_GRAPH_PASS':raise AssertionError('unexpected F5 acceptance gate')
    if set(c.get('projection_slices',{}))!={'M0G_MEMBERS','M1A_REINFORCEMENT','M1L_LOADS'} or any(v not in {'IN_SCOPE','PASS'} for v in c['projection_slices'].values()):raise AssertionError('F5 slice contract drift')
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8')); patch='knowledge/ARTIFACT_REGISTRY_CEW_KNOWLEDGE_GRAPH_PATCH_v1.csv'
    if patch not in manifest.get('artifact_registry_patches',[]):raise AssertionError('F5 registry patch not governed by KNOWLEDGE_MANIFEST')
    required={'CONTRACT-CEW-KG-001','RUN-CEW-KG-001','RUN-CEW-KG-002','CI-CEW-KG-001','RUN-CEW-KG-003','RUN-CEW-KG-004','CI-CEW-KG-002','RUN-CEW-KG-005','RUN-CEW-KG-006','CI-CEW-KG-003'}
    actual={r['artifact_id'].strip() for r in rows(REGISTRY)}
    if not required.issubset(actual):raise AssertionError(f'F5 artifact registry incomplete: {sorted(required-actual)}')
    status={r['milestone_id'].strip():r['status'].strip() for r in rows(MILESTONES)}
    if not valid_governance(status):raise AssertionError('F5 governance invalid for global graph gate')
    if any(status.get(x)!='COMPLETE' for x in ('CEW-F0','CEW-F1','CEW-F2','CEW-F3','CEW-F4')):raise AssertionError('upstream milestones not frozen COMPLETE')
    with tempfile.TemporaryDirectory(prefix='cew-f5-') as t:
        t=Path(t); m0=t/'m0g'; ma=t/'m1a'; ml=t/'m1l'
        run('scripts/project_cew_m0g_knowledge_graph.py','--out',str(m0)); o0=run('scripts/validate_cew_knowledge_graph_m0g_slice.py','--projection',str(m0/'m0g_graph_projection.json'))
        run('scripts/project_cew_m1a_knowledge_graph.py','--out',str(ma)); oa=run('scripts/validate_cew_knowledge_graph_m1a_slice.py','--projection',str(ma/'m1a_graph_projection.json'))
        run('scripts/project_cew_m1l_knowledge_graph.py','--out',str(ml)); ol=run('scripts/validate_cew_knowledge_graph_m1l_slice.py','--projection',str(ml/'m1l_graph_projection.json'))
        for marker,out in (('KNOWLEDGE_GRAPH_M0G_SLICE_PASS',o0),('KNOWLEDGE_GRAPH_M1A_SLICE_PASS',oa),('KNOWLEDGE_GRAPH_M1L_SLICE_PASS',ol)):
            if marker not in out:raise AssertionError(f'missing slice marker: {marker}')
    print('KNOWLEDGE_GRAPH_PASS');print('SLICES_PASS=3/3');print('M0G_REOPEN=FORBIDDEN');print('SOURCE_LEDGER_MUTATION=FORBIDDEN');print('EPISTEMIC_PROMOTION=FORBIDDEN');print('MISSING_PROPERTY_INVENTION=FORBIDDEN');print('GRAPH_AUTHORITY=DERIVED_GRAPH_PROJECTION_ONLY');print('POST_CLOSURE_STATE=F5_PHASE_MONOTONIC');return 0
if __name__=='__main__':raise SystemExit(main())