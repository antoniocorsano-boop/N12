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
'title':'Verificare l’armatura del filare collegato a G01-R06',
'question':'Controlla sulla carpenteria TAV-05S la notazione dell’armatura del filare corrispondente e trascrivi esattamente quantità e diametro indicati.',
'known':'La lunghezza 1040 del richiamo G01-R06 è già documentata sulla tavola d’armatura.',
'unknown':'La quantità e il diametro devono essere confermati dalla carpenteria primaria, non dedotti dal dettaglio isolato.',
'conflict':'Nessun conflitto accertato.',
'where':'Usa il riquadro “Carpenteria TAV-05S” e cerca il filare corrispondente. La tavola d’armatura TAV-05A a fianco serve solo per riconoscere il richiamo G01-R06.',
'look_for':'Leggi la notazione riportata direttamente sul filare in carpenteria: numero di ferri e diametro.',
'dont':'Non trasferire la notazione da un filare vicino e non usare analogie. Non considerare la tavola TAV-05A come fonte del dato se il dato è scritto in carpenteria.',
'confirmed':'Conferma solo dopo aver letto direttamente la notazione sulla carpenteria TAV-05S.',
'fallback':'Se non riesci a localizzare il filare o la notazione non è leggibile, scegli ILLEGGIBILE oppure SERVE UNA FONTE MIGLIORE.',
'context_source':'TAV-05S'},
'ERW-N12-002':{
'title':'Verificare l’armatura del filare collegato a G07-R07',
'question':'Controlla sulla carpenteria TAV-05S la notazione dell’armatura del filare corrispondente e trascrivi esattamente quantità e diametro indicati.',
'known':'La lunghezza 865 del richiamo G07-R07 è già documentata sulla tavola d’armatura.',
'unknown':'La quantità e il diametro devono essere confermati dalla carpenteria primaria, non dedotti dal dettaglio isolato.',
'conflict':'Nessun conflitto accertato.',
'where':'Usa il riquadro “Carpenteria TAV-05S” e cerca il filare corrispondente. La tavola d’armatura TAV-05A a fianco serve solo per riconoscere il richiamo G07-R07.',
'look_for':'Leggi la notazione riportata direttamente sul filare in carpenteria: numero di ferri e diametro.',
'dont':'Non trasferire la notazione da un filare vicino e non usare analogie.',
'confirmed':'Conferma solo dopo aver letto direttamente la notazione sulla carpenteria TAV-05S.',
'fallback':'Se non riesci a localizzare il filare o la notazione non è leggibile, scegli ILLEGGIBILE oppure SERVE UNA FONTE MIGLIORE.',
'context_source':'TAV-05S'},
'ERW-N12-003':{
'title':'Leggere le dimensioni mancanti del sagomato G05-R04',
'question':'Individua la continuazione del sagomato G05-R04 sulla TAV-05A e verifica quali quote dimensionali sono realmente leggibili.',
'known':'La continuazione del sagomato intermedio è già documentata come parzialmente leggibile.',
'unknown':'Mancano alcune dimensioni del sagomato.',
'conflict':'Nessun conflitto accertato.',
'where':'Centra la regione rossa sulla TAV-05A e segui il sagomato fino alle quote direttamente associate.',
'look_for':'Trascrivi soltanto le quote che puoi associare senza ambiguità al sagomato G05-R04.',
'dont':'Non trasferire quote da sagomati vicini e non completare quote mancanti per simmetria o proporzione.',
'confirmed':'Conferma soltanto se le quote che risolvono il residuo sono leggibili e chiaramente riferibili a G05-R04.',
'fallback':'Se il ferro è visibile ma le quote restano ambigue, scegli ILLEGGIBILE e descrivi ciò che riesci a vedere.',
'context_source':'TAV-05S'},
'ERW-N12-004':{
'title':'Localizzare sulla carpenteria la trave senza numeri di sostegno',
'question':'Confronta lo schema T6A-G03 della TAV-06A con la carpenteria di copertura TAV-06S e individua dove si trova realmente la trave prima di proporre qualunque binding al modello.',
'known':'T6A-G03 mostra due appoggi e uno sbalzo libero. G5-B017 è soltanto un candidato storico e non deve essere privilegiato.',
'unknown':'Non sappiamo ancora quale trave della carpenteria corrisponda allo schema senza numeri di sostegno.',
'conflict':'G5-B017 è appoggio-appoggio e quindi non coincide direttamente con la firma topologica dello schema T6A-G03.',
'where':'Usa i due viewer affiancati: a sinistra lo schema TAV-06A, a destra l’intera carpenteria TAV-06S. Cerca prima geometria e posizione, non il codice del modello.',
'look_for':'Confronta numero di appoggi, presenza e lato dello sbalzo, orientamento, rapporti fra campate, posizione sul bordo e collegamenti con elementi adiacenti.',
'dont':'Non scegliere G5-B017 perché è già noto. Non fare binding finché la localizzazione sulla carpenteria non è univoca.',
'confirmed':'Conferma soltanto quando puoi indicare una posizione univoca sulla TAV-06S e descrivere quali caratteristiche geometriche coincidono.',
'fallback':'Se più posizioni restano compatibili, scegli NON ASSOCIABILE e descrivi i candidati rimasti.',
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
            'title_it':it['title'],'question_it':it['question'],'known_it':it['known'],'unknown_it':it['unknown'],'conflict_it':it['conflict'],
            'where_it':it['where'],'look_for_it':it['look_for'],'dont_it':it['dont'],'confirmed_it':it['confirmed'],'fallback_it':it['fallback'],
            'context_source':it['context_source'],
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
    manifest={'contract_id':contract['contract_id'],'authority':'HUMAN_REVIEW_INPUT_ONLY','ui_language':'it','guided_review':True,'prefilled_decisions':0,'entries':entries}
    (out/'human_review_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    html='''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW F7 — Revisione tecnica guidata</title><style>body{font-family:system-ui;margin:1rem;max-width:1500px;color:#202124}section{border:1px solid #bbb;padding:1rem;margin:1.3rem 0;border-radius:8px}textarea,input,select{width:100%;box-sizing:border-box;margin:.25rem 0 .75rem;padding:.55rem}button{padding:.6rem 1rem}.viewers{display:grid;grid-template-columns:1fr 1fr;gap:.8rem}.viewer-card{border:1px solid #aaa;padding:.5rem}.viewer-card h3{margin:.2rem 0 .5rem}iframe{width:100%;height:62vh;border:2px solid #555}.warn{font-weight:700}.intro{background:#f5f7f8;padding:.9rem;border-left:5px solid #555}.goal{font-size:1.1rem;background:#eef5ff;padding:.8rem;border-radius:6px}.guide{border:1px solid #ccc;background:#fffdf6;padding:.8rem 1rem;margin:.8rem 0}.step{margin:.55rem 0}.stop{background:#fff0f0;padding:.6rem;border-left:4px solid #a00}.ok{background:#eef8ee;padding:.6rem;border-left:4px solid #287a28}.fallback{background:#f6f6f6;padding:.6rem;border-left:4px solid #777}.advanced{margin-top:1rem;border-top:1px dashed #aaa;padding-top:.5rem}.decision{background:#f8f8f8;padding:.9rem;margin-top:1rem;border-radius:6px}@media(max-width:1000px){.viewers{grid-template-columns:1fr}iframe{height:55vh}}</style></head><body><h1>CEW F7 — Revisione tecnica guidata</h1><p class="warn">La fonte primaria è l’autorità. Le carpenterie di destra servono per localizzare e verificare; non diventano automaticamente evidenza canonica.</p><div class="intro"><b>Procedura:</b> leggi il compito, confronta le due tavole, registra solo ciò che hai osservato direttamente. Se la carpenteria contiene l’informazione, trascrivila nel campo di osservazione; non ricavarla per analogia.</div><div id="tasks"></div><script src="app.js"></script></body></html>'''
    js=r'''const outcomes=[['','— scegli —'],['CONFIRMED','CONFERMATO — ho letto/verificato il dato'],['REJECTED','RESPINTO — la fonte contraddice la proposta'],['UNREADABLE','ILLEGGIBILE — il dato non si legge con sicurezza'],['UNBOUND','NON ASSOCIABILE — manca un legame univoco'],['NEEDS_BETTER_SOURCE','SERVE UNA FONTE MIGLIORE'],['NEEDS_SITE_SURVEY','SERVE RILIEVO IN SITO'],['DEFER','RINVIA']];const states=[['','— lascia vuoto se non necessario —'],['ND','ND — non determinato'],['INF','INF — inferito'],['RIF','RIF — riferimento'],['MIS','MIS — misurato'],['DOC','DOC — documentato']];
async function boot(){const m=await(await fetch('human_review_manifest.json',{cache:'no-store'})).json();const root=document.getElementById('tasks');for(const e of m.entries){const s=document.createElement('section');s.innerHTML=`<h2>${e.title_it}</h2><small>${e.task_id} · ${e.residual_id}</small><div class="goal"><b>Cosa devi controllare</b><br>${e.question_it}</div><div class="guide"><div class="step"><b>1. Dove guardare:</b> ${e.where_it}</div><div class="step"><b>2. Cosa cercare:</b> ${e.look_for_it}</div><div class="stop"><b>Non fare questo:</b> ${e.dont_it}</div><div class="ok"><b>Quando puoi confermare:</b> ${e.confirmed_it}</div><div class="fallback"><b>Se non riesci:</b> ${e.fallback_it}</div></div><p><b>Già noto:</b> ${e.known_it}<br><b>Ancora da determinare:</b> ${e.unknown_it}<br><b>Conflitto:</b> ${e.conflict_it}</p><div class="viewers"><div class="viewer-card"><h3>Tavola d’armatura / schema</h3><iframe src="${e.viewer_url}" title="Tavola armatura ${e.task_id}"></iframe></div><div class="viewer-card"><h3>Carpenteria ${e.context_source}</h3><iframe src="${e.context_viewer_url}" title="Carpenteria ${e.context_source}"></iframe></div></div><div class="decision"><h3>Registra il risultato</h3><label>Revisore</label><input data-k="reviewer" placeholder="Nome e cognome"><label>Esito</label><select data-k="outcome">${outcomes.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select><label>Cosa hai letto o verificato?</label><textarea data-k="human_observation" placeholder="Scrivi la lettura esatta e indica su quale tavola l’hai osservata."></textarea><label><input type="checkbox" data-k="direct_primary_evidence_observed" style="width:auto"> Confermo di aver controllato direttamente la fonte primaria</label><details class="advanced"><summary>Parametri di governance avanzati</summary><label>Stato epistemico richiesto</label><select data-k="requested_epistemic_state">${states.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select><label>ID target di promozione</label><input data-k="target_id"><label>ID approvazione riapertura</label><input data-k="reopen_approval_id"></details><label><input type="checkbox" data-k="authority_acknowledgement" style="width:auto"> Dichiaro che questo export registra una revisione umana e non scrive direttamente nei dati canonici.</label><br><button>Esporta la decisione in JSON</button></div>`;s.querySelector('button').onclick=()=>exp(s,e);root.appendChild(s)}}
function exp(s,e){let d=structuredClone(e.decision_template);for(const el of s.querySelectorAll('[data-k]'))d[el.dataset.k]=el.type==='checkbox'?el.checked:el.value.trim();d.decision_id=`HUMAN-${e.task_id}-${Date.now()}`;d.timestamp=new Date().toISOString();if(!d.reviewer||!d.outcome||!d.authority_acknowledgement){alert('Sono obbligatori Revisore, Esito e dichiarazione finale.');return}if(d.outcome==='CONFIRMED'&&(!d.human_observation||d.direct_primary_evidence_observed!==true||!d.target_id)){alert('CONFERMATO richiede osservazione diretta, conferma della fonte primaria e target di promozione.');return}if(d.outcome!=='CONFIRMED'&&d.target_id){alert('Un esito diverso da CONFERMATO non può selezionare un target.');return}const blob=new Blob([JSON.stringify(d,null,2)+'\n'],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=d.decision_id+'.json';a.click();URL.revokeObjectURL(a.href)}boot();'''
    (out/'index.html').write_text(html,encoding='utf-8');(out/'app.js').write_text(js,encoding='utf-8')
    print('HUMAN_REVIEW_PACK_BUILT');print('TASKS=4');print('PREFILLED_DECISIONS=0');print('UI_LANGUAGE=it');print('GUIDED_REVIEW=YES');print('CARPENTERIA_CONTEXT=YES');print('CANONICAL_WRITE=FORBIDDEN');return 0
if __name__=='__main__':raise SystemExit(main())
