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

DISPLAY_IT={
'ERW-N12-001':{
'question':'Determinare quantità e diametro del richiamo TAV-05A G01-R06 senza ricorrere ad analogie.',
'known':'lunghezza = 1040 DOC','unknown':'quantità ND; diametro ND','conflict':'nessun conflitto accertato'},
'ERW-N12-002':{
'question':'Determinare quantità e diametro del richiamo TAV-05A G07-R07 senza ricorrere ad analogie.',
'known':'lunghezza = 865 DOC','unknown':'quantità ND; diametro ND','conflict':'nessun conflitto accertato'},
'ERW-N12-003':{
'question':'Risolvere le dimensioni mancanti della continuazione del sagomato intermedio direttamente visibile G05-R04.',
'known':'continuazione del sagomato intermedio DOC_DIRECT_PARTIAL','unknown':'dimensioni mancanti ND','conflict':'nessun conflitto accertato'},
'ERW-N12-004':{
'question':'Stabilire se esiste evidenza primaria diretta per associare T6A-G03 a G5-B017 o a un altro elemento canonico.',
'known':'estremi G5-B017 12–19 DOC; schema sorgente T6A-G03 DOC','unknown':'armatura specifica dell’elemento ND; associazione diretta alla sorgente ND','conflict':'TOPOLOGIA SORGENTE: T6A-G03 presenta due appoggi e uno sbalzo libero, mentre G5-B017 è appoggio-appoggio'}
}

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
        t=tasks[tid];v=viewers[tid];r=regions[v['evidence_region_id'].strip()];it=DISPLAY_IT[tid]
        entries.append({
            'task_id':tid,'residual_id':t['residual_id'].strip(),'domain':t['domain'].strip(),'question':t['question'].strip(),
            'question_it':it['question'],'known_it':it['known'],'unknown_it':it['unknown'],'conflict_it':it['conflict'],
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
    manifest={'contract_id':contract['contract_id'],'authority':'HUMAN_REVIEW_INPUT_ONLY','ui_language':'it','prefilled_decisions':0,'entries':entries}
    (out/'human_review_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    html='''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW F7 — Revisione tecnica</title><style>body{font-family:system-ui;margin:1rem;max-width:1100px}section{border:1px solid #bbb;padding:1rem;margin:1rem 0}textarea,input,select{width:100%;box-sizing:border-box;margin:.25rem 0 .75rem;padding:.45rem}button{padding:.6rem 1rem}iframe{width:100%;height:60vh;border:1px solid #888}.warn{font-weight:700}.hint{background:#f5f5f5;padding:.7rem;border-left:4px solid #777}</style></head><body><h1>CEW F7 — Revisione e decisione tecnica</h1><p class="warn">La fonte primaria è l’autorità. Nessun campo di questa schermata scrive direttamente nei dati canonici. Seleziona CONFERMATO soltanto quando hai osservato direttamente nella fonte primaria l’evidenza che sostiene la decisione.</p><p class="hint">Gli identificativi tecnici restano invariati per garantire la tracciabilità. Le etichette operative sono in italiano.</p><div id="tasks"></div><script src="app.js"></script></body></html>'''
    js=r'''const outcomes=[['',''],['CONFIRMED','CONFERMATO'],['REJECTED','RESPINTO'],['UNREADABLE','ILLEGGIBILE'],['UNBOUND','NON ASSOCIABILE'],['NEEDS_BETTER_SOURCE','SERVE UNA FONTE MIGLIORE'],['NEEDS_SITE_SURVEY','SERVE RILIEVO IN SITO'],['DEFER','RINVIA']];const states=[['',''],['ND','ND — non determinato'],['INF','INF — inferito'],['RIF','RIF — riferimento'],['MIS','MIS — misurato'],['DOC','DOC — documentato']];
async function boot(){const m=await(await fetch('human_review_manifest.json',{cache:'no-store'})).json();const root=document.getElementById('tasks');for(const e of m.entries){const s=document.createElement('section');s.innerHTML=`<h2>${e.task_id} · ${e.residual_id}</h2><p>${e.question_it}</p><p><b>Dato noto:</b> ${e.known_it||'—'}<br><b>Dato da determinare:</b> ${e.unknown_it||'—'}<br><b>Conflitto:</b> ${e.conflict_it||'—'}</p><iframe src="${e.viewer_url}" title="Fonte primaria per ${e.task_id}"></iframe><label>Revisore</label><input data-k="reviewer"><label>Esito</label><select data-k="outcome">${outcomes.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select><label>Osservazione tecnica umana</label><textarea data-k="human_observation" placeholder="Scrivi soltanto ciò che osservi direttamente nella fonte primaria."></textarea><label><input type="checkbox" data-k="direct_primary_evidence_observed" style="width:auto"> Confermo di aver osservato direttamente nella fonte primaria l’evidenza che sostiene questa decisione</label><label>Stato epistemico richiesto</label><select data-k="requested_epistemic_state">${states.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select><label>ID target di promozione (solo se CONFERMATO)</label><input data-k="target_id"><label>ID approvazione riapertura (solo se richiesto)</label><input data-k="reopen_approval_id"><label><input type="checkbox" data-k="authority_acknowledgement" style="width:auto"> Dichiaro di comprendere che questo export è una ricevuta di revisione umana e non una scrittura canonica.</label><button>Esporta decisione JSON</button>`;s.querySelector('button').onclick=()=>exp(s,e);root.appendChild(s)}}
function exp(s,e){let d=structuredClone(e.decision_template);for(const el of s.querySelectorAll('[data-k]'))d[el.dataset.k]=el.type==='checkbox'?el.checked:el.value.trim();d.decision_id=`HUMAN-${e.task_id}-${Date.now()}`;d.timestamp=new Date().toISOString();if(!d.reviewer||!d.outcome||!d.authority_acknowledgement){alert('Sono obbligatori: Revisore, Esito e dichiarazione di autorità.');return}if(d.outcome==='CONFIRMED'&&(!d.human_observation||d.direct_primary_evidence_observed!==true||!d.target_id)){alert('CONFERMATO richiede un’osservazione diretta della fonte primaria e un ID target.');return}if(d.outcome!=='CONFIRMED'&&d.target_id){alert('Un esito diverso da CONFERMATO non può selezionare un target di promozione.');return}const blob=new Blob([JSON.stringify(d,null,2)+'\n'],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=d.decision_id+'.json';a.click();URL.revokeObjectURL(a.href)}boot();'''
    (out/'index.html').write_text(html,encoding='utf-8');(out/'app.js').write_text(js,encoding='utf-8')
    print('HUMAN_REVIEW_PACK_BUILT');print('TASKS=4');print('PREFILLED_DECISIONS=0');print('UI_LANGUAGE=it');print('CANONICAL_WRITE=FORBIDDEN');return 0
if __name__=='__main__':raise SystemExit(main())
