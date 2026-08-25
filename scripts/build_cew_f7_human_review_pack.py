#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,json,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'data/canonical'
CONTRACT=ROOT/'automation/CEW_HUMAN_DECISION_INTAKE_CONTRACT_v1.json'
TASKS=C/'CEW_ERW_RESOLUTION_TASKS_v1.csv'
VIEWER=C/'CEW_SOURCE_VIEWER_BINDINGS_v1.csv'
REGIONS=C/'CEW_EVIDENCE_REGION_REGISTRY_v1.csv'

def rows(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-viewer-dir',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    contract=json.loads(CONTRACT.read_text(encoding='utf-8'))
    tasks={r['task_id'].strip():r for r in rows(TASKS)}
    viewers={r['task_id'].strip():r for r in rows(VIEWER)}
    regions={r['evidence_region_id'].strip():r for r in rows(REGIONS)}
    expected=set(contract['reference_tasks'])
    if set(tasks).intersection(expected)!=expected or set(viewers)!=expected:raise AssertionError('reference task/viewer coverage drift')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    src=Path(a.source_viewer_dir);dest=out/'source-viewer'
    if dest.exists():shutil.rmtree(dest)
    shutil.copytree(src,dest)
    entries=[]
    for tid in contract['reference_tasks']:
        t=tasks[tid];v=viewers[tid];r=regions[v['evidence_region_id'].strip()]
        entries.append({
            'task_id':tid,'residual_id':t['residual_id'].strip(),'domain':t['domain'].strip(),'question':t['question'].strip(),
            'known_claims':t['known_claims'].strip(),'unknown_claims':t['unknown_claims'].strip(),'conflicts':t['conflicts'].strip(),
            'suggested_actions':t['suggested_actions'].strip(),'epistemic_ceiling':t['epistemic_ceiling'].strip(),
            'evidence_region_id':r['evidence_region_id'].strip(),'source_version_id':v['source_version_id'].strip(),
            'viewer_url':'source-viewer/index.html?task='+tid,
            'decision_template':{
                'schema_version':'1.0','decision_id':'','task_id':tid,'residual_id':t['residual_id'].strip(),'review_mode':'HUMAN_REVIEW',
                'reviewer':'','timestamp':'','outcome':'','human_observation':'','evidence_regions':[r['evidence_region_id'].strip()],
                'source_versions':[v['source_version_id'].strip()],'direct_primary_evidence_observed':None,'requested_epistemic_state':'',
                'target_id':'','reopen_approval_id':'','authority_acknowledgement':False
            }
        })
    manifest={'contract_id':contract['contract_id'],'authority':'HUMAN_REVIEW_INPUT_ONLY','prefilled_decisions':0,'entries':entries}
    (out/'human_review_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    html='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW F7 Human Review</title><style>body{font-family:system-ui;margin:1rem;max-width:1100px}section{border:1px solid #bbb;padding:1rem;margin:1rem 0}textarea,input,select{width:100%;box-sizing:border-box;margin:.25rem 0 .75rem;padding:.45rem}button{padding:.6rem 1rem}iframe{width:100%;height:60vh;border:1px solid #888}.warn{font-weight:700}</style></head><body><h1>CEW F7 — Human Decision Intake</h1><p class="warn">Primary source is authority. No field below is a canonical write. CONFIRMED is allowed only when you directly observe supporting evidence in the primary source.</p><div id="tasks"></div><script src="app.js"></script></body></html>'''
    js=r'''const allowed=['','CONFIRMED','REJECTED','UNREADABLE','UNBOUND','NEEDS_BETTER_SOURCE','NEEDS_SITE_SURVEY','DEFER'];const states=['','ND','INF','RIF','MIS','DOC'];
async function boot(){const m=await(await fetch('human_review_manifest.json',{cache:'no-store'})).json();const root=document.getElementById('tasks');for(const e of m.entries){const s=document.createElement('section');s.innerHTML=`<h2>${e.task_id} · ${e.residual_id}</h2><p>${e.question}</p><p><b>Known:</b> ${e.known_claims||'—'}<br><b>Unknown:</b> ${e.unknown_claims||'—'}<br><b>Conflict:</b> ${e.conflicts||'—'}</p><iframe src="${e.viewer_url}"></iframe><label>Reviewer</label><input data-k="reviewer"><label>Outcome</label><select data-k="outcome">${allowed.map(x=>`<option>${x}</option>`).join('')}</select><label>Human observation</label><textarea data-k="human_observation"></textarea><label><input type="checkbox" data-k="direct_primary_evidence_observed" style="width:auto"> I directly observed supporting evidence in the primary source</label><label>Requested epistemic state</label><select data-k="requested_epistemic_state">${states.map(x=>`<option>${x}</option>`).join('')}</select><label>Promotion target ID (CONFIRMED only)</label><input data-k="target_id"><label>Reopen approval ID (only when required)</label><input data-k="reopen_approval_id"><label><input type="checkbox" data-k="authority_acknowledgement" style="width:auto"> I acknowledge that this export is a human review receipt, not a canonical write.</label><button>Export decision JSON</button>`;s.querySelector('button').onclick=()=>exp(s,e);root.appendChild(s)}}
function exp(s,e){let d=structuredClone(e.decision_template);for(const el of s.querySelectorAll('[data-k]'))d[el.dataset.k]=el.type==='checkbox'?el.checked:el.value.trim();d.decision_id=`HUMAN-${e.task_id}-${Date.now()}`;d.timestamp=new Date().toISOString();if(!d.reviewer||!d.outcome||!d.authority_acknowledgement){alert('Reviewer, outcome and authority acknowledgement are required.');return}if(d.outcome==='CONFIRMED'&&(!d.human_observation||d.direct_primary_evidence_observed!==true||!d.target_id)){alert('CONFIRMED requires a direct primary-source observation and target ID.');return}if(d.outcome!=='CONFIRMED'&&d.target_id){alert('Non-CONFIRMED outcomes must not select a promotion target.');return}const blob=new Blob([JSON.stringify(d,null,2)+'\n'],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=d.decision_id+'.json';a.click();URL.revokeObjectURL(a.href)}boot();'''
    (out/'index.html').write_text(html,encoding='utf-8');(out/'app.js').write_text(js,encoding='utf-8')
    print('HUMAN_REVIEW_PACK_BUILT');print('TASKS=4');print('PREFILLED_DECISIONS=0');print('CANONICAL_WRITE=FORBIDDEN');return 0
if __name__=='__main__':raise SystemExit(main())
