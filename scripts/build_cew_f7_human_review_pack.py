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
'title':'G01-R06 — armatura del filare',
'element':'FILARE DA LOCALIZZARE SU TAV-05S · richiamo G01-R06',
'known':'Lunghezza 1040 — DOC sulla TAV-05A.',
'missing':'Filare corrispondente su TAV-05S; quantità dei ferri; diametro.',
'technical':'Usa TAV-05A per il richiamo G01-R06 e TAV-05S per localizzare il filare. Leggi la notazione direttamente sul filare; non trasferire dati da filari vicini e non usare analogie.',
'fallback':'Se il filare non è localizzabile o la notazione non è leggibile, scegli ILLEGGIBILE oppure SERVE UNA FONTE MIGLIORE.',
'context_source':'TAV-05S'},
'ERW-N12-002':{
'title':'G07-R07 — armatura del filare',
'element':'FILARE DA LOCALIZZARE SU TAV-05S · richiamo G07-R07',
'known':'Lunghezza 865 — DOC sulla TAV-05A.',
'missing':'Filare corrispondente su TAV-05S; quantità dei ferri; diametro.',
'technical':'Usa TAV-05A per il richiamo G07-R07 e TAV-05S per localizzare il filare. Leggi la notazione direttamente sul filare; non trasferire dati da filari vicini e non usare analogie.',
'fallback':'Se il filare non è localizzabile o la notazione non è leggibile, scegli ILLEGGIBILE oppure SERVE UNA FONTE MIGLIORE.',
'context_source':'TAV-05S'},
'ERW-N12-003':{
'title':'G05-R04 — sagomato intermedio',
'element':'Sagomato G05-R04 · TAV-05A',
'known':'Continuazione intermedia del sagomato direttamente visibile — DOC_DIRECT_PARTIAL.',
'missing':'Quote/dimensioni mancanti; oppure conferma che l’intero sagomato pertinente è completamente quotato.',
'technical':'Segui l’intero sagomato sulla TAV-05A fino a entrambe le estremità. Non dichiarare una quota mancante solo perché cade fuori dal crop e non completare per simmetria, proporzione o analogia.',
'fallback':'Se resta un tratto, una piega o un’estremità non quotata o non leggibile, indica esattamente quale parte resta irrisolta.',
'context_source':'TAV-05S'},
'ERW-N12-004':{
'title':'T6A-G03 — localizzazione strutturale',
'element':'Schema T6A-G03 · TAV-06A · binding attuale UNBOUND',
'known':'Schema T6A-G03 documentato; G5-B017 ha estremi 12–19 documentati nel modello.',
'missing':'Evidenza primaria che consenta di associare T6A-G03 a G5-B017 o a un altro membro canonico; altrimenti conferma NON ASSOCIABILE.',
'technical':'Confronta TAV-06A e TAV-06S per continuità grafica, appoggi, orientamento e sbalzo. La compatibilità metrica o un candidato geometrico non costituiscono da soli una prova di binding e non autorizzano correzioni del modello.',
'fallback':'Se la carpenteria non rende univoca la linea o restano più candidati, scegli NON ASSOCIABILE e descrivi ciò che resta ambiguo.',
'context_source':'TAV-06S'}
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
            'task_id':tid,'residual_id':t['residual_id'].strip(),'domain':t['domain'].strip(),
            'title_it':it['title'],'element_it':it['element'],'known_it':it['known'],'missing_it':it['missing'],
            'technical_it':it['technical'],'fallback_it':it['fallback'],'context_source':it['context_source'],
            'evidence_region_id':r['evidence_region_id'].strip(),'source_version_id':v['source_version_id'].strip(),
            'viewer_url':'source-viewer/index.html?task='+tid,
            'context_viewer_url':'source-viewer/index.html?source='+it['context_source'],
            'decision_template':{
                'schema_version':'1.0','decision_id':'','task_id':tid,'residual_id':t['residual_id'].strip(),'review_mode':'HUMAN_REVIEW',
                'reviewer':'','timestamp':'','outcome':'','human_observation':'','evidence_regions':[r['evidence_region_id'].strip()],
                'source_versions':[v['source_version_id'].strip()],'direct_primary_evidence_observed':None,'requested_epistemic_state':'',
                'target_id':'','reopen_approval_id':'','authority_acknowledgement':False
            }
        })
    manifest={'contract_id':contract['contract_id'],'authority':'HUMAN_REVIEW_INPUT_ONLY','ui_language':'it','guided_review':True,'compact_review':True,'prefilled_decisions':0,'entries':entries}
    (out/'human_review_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    html='''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW F7 — Revisione tecnica essenziale</title><style>
body{font-family:system-ui;margin:1rem;max-width:1500px;color:#202124;background:#f7f8fa}h1{margin-bottom:.25rem}.intro{margin:0 0 1rem;color:#4b5563}section{background:#fff;border:1px solid #c9ced6;padding:1rem;margin:1rem 0;border-radius:10px}section h2{margin:.1rem 0}.ids{color:#6b7280}.compact-grid{display:grid;grid-template-columns:1.1fr 1fr 1fr;gap:.65rem;margin:.9rem 0}.fact{border:1px solid #d7dbe1;border-radius:7px;padding:.75rem;min-height:5rem}.fact b{display:block;font-size:.78rem;letter-spacing:.04em;margin-bottom:.35rem}.element{border-left:5px solid #44546a}.known{border-left:5px solid #3b7a57}.missing{border-left:5px solid #b7791f}.decision{border-top:1px solid #d7dbe1;padding-top:.8rem}.decision h3{margin:.2rem 0 .6rem}.response-grid{display:grid;grid-template-columns:1fr 1fr;gap:.65rem}textarea,input,select{width:100%;box-sizing:border-box;margin:.2rem 0 .65rem;padding:.55rem}textarea{min-height:5rem}button{padding:.6rem 1rem}.viewers{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-top:.7rem}.viewer-card{border:1px solid #aaa;padding:.5rem}.viewer-card h3{margin:.2rem 0 .5rem}iframe{width:100%;height:62vh;border:2px solid #555}details{margin:.7rem 0}summary{cursor:pointer;font-weight:650}.technical{background:#f8f9fb;padding:.6rem;border-radius:6px}.governance{border-top:1px dashed #aaa;padding-top:.6rem;margin-top:.6rem}@media(max-width:1000px){.compact-grid,.response-grid,.viewers{grid-template-columns:1fr}iframe{height:55vh}}</style></head><body><h1>CEW F7 — Revisione tecnica essenziale</h1><p class="intro">Per ogni caso: identifica l’elemento, verifica ciò che è già noto e compila soltanto il dato mancante osservato sulla fonte primaria.</p><div id="tasks"></div><script src="app.js"></script></body></html>'''
    js=r'''const outcomes=[['','— scegli —'],['CONFIRMED','CONFERMATO — dato verificato'],['REJECTED','RESPINTO — la fonte contraddice la proposta'],['UNREADABLE','ILLEGGIBILE'],['UNBOUND','NON ASSOCIABILE'],['NEEDS_BETTER_SOURCE','SERVE UNA FONTE MIGLIORE'],['NEEDS_SITE_SURVEY','SERVE RILIEVO IN SITO'],['DEFER','RINVIA']];const states=[['','— lascia vuoto se non necessario —'],['ND','ND — non determinato'],['INF','INF — inferito'],['RIF','RIF — riferimento'],['MIS','MIS — misurato'],['DOC','DOC — documentato']];
async function boot(){const m=await(await fetch('human_review_manifest.json',{cache:'no-store'})).json();const root=document.getElementById('tasks');for(const e of m.entries){const s=document.createElement('section');s.innerHTML=`<h2>${e.title_it}</h2><small class="ids">${e.task_id} · ${e.residual_id}</small><div class="compact-grid"><div class="fact element"><b>FILARE / ELEMENTO</b>${e.element_it}</div><div class="fact known"><b>GIÀ RICONOSCIUTO</b>${e.known_it}</div><div class="fact missing"><b>DA COMPLETARE</b>${e.missing_it}</div></div><details><summary>Apri tavole di verifica</summary><div class="viewers"><div class="viewer-card"><h3>Tavola d’armatura / schema</h3><iframe src="${e.viewer_url}" title="Tavola armatura ${e.task_id}"></iframe></div><div class="viewer-card"><h3>Carpenteria ${e.context_source}</h3><iframe src="${e.context_viewer_url}" title="Carpenteria ${e.context_source}"></iframe></div></div></details><div class="decision"><h3>RISPOSTA</h3><div class="response-grid"><div><label>Revisore</label><input data-k="reviewer" placeholder="Nome e cognome"></div><div><label>Esito</label><select data-k="outcome">${outcomes.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select></div></div><label>Dato letto / verifica eseguita</label><textarea data-k="human_observation" placeholder="Trascrivi il dato esatto e indica la tavola su cui lo hai osservato."></textarea><label><input type="checkbox" data-k="direct_primary_evidence_observed" style="width:auto"> Ho verificato direttamente la fonte primaria</label><details class="technical"><summary>Dettagli tecnici</summary><p>${e.technical_it}</p><p><b>Se non determinabile:</b> ${e.fallback_it}</p><p><b>Provenienza:</b> ${e.evidence_region_id} · ${e.source_version_id}</p><div class="governance"><label>Stato epistemico richiesto</label><select data-k="requested_epistemic_state">${states.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select><label>ID target di promozione</label><input data-k="target_id"><label>ID approvazione riapertura</label><input data-k="reopen_approval_id"><label><input type="checkbox" data-k="authority_acknowledgement" style="width:auto"> Confermo che l’export registra una revisione umana e non scrive direttamente nei dati canonici.</label></div></details><button>Esporta la decisione in JSON</button></div>`;s.querySelector('button').onclick=()=>exp(s,e);root.appendChild(s)}}
function exp(s,e){let d=structuredClone(e.decision_template);for(const el of s.querySelectorAll('[data-k]'))d[el.dataset.k]=el.type==='checkbox'?el.checked:el.value.trim();d.decision_id=`HUMAN-${e.task_id}-${Date.now()}`;d.timestamp=new Date().toISOString();if(!d.reviewer||!d.outcome||!d.authority_acknowledgement){alert('Sono obbligatori Revisore, Esito e dichiarazione finale nei Dettagli tecnici.');return}if(d.outcome==='CONFIRMED'&&(!d.human_observation||d.direct_primary_evidence_observed!==true||!d.target_id)){alert('CONFERMATO richiede osservazione diretta, conferma della fonte primaria e target di promozione nei Dettagli tecnici.');return}if(d.outcome!=='CONFIRMED'&&d.target_id){alert('Un esito diverso da CONFERMATO non può selezionare un target.');return}const blob=new Blob([JSON.stringify(d,null,2)+'\n'],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=d.decision_id+'.json';a.click();URL.revokeObjectURL(a.href)}boot();'''
    (out/'index.html').write_text(html,encoding='utf-8');(out/'app.js').write_text(js,encoding='utf-8')
    print('HUMAN_REVIEW_PACK_BUILT');print('TASKS=4');print('PREFILLED_DECISIONS=0');print('UI_LANGUAGE=it');print('COMPACT_REVIEW=YES');print('CARPENTERIA_CONTEXT=YES');print('CANONICAL_WRITE=FORBIDDEN');return 0
if __name__=='__main__':raise SystemExit(main())
