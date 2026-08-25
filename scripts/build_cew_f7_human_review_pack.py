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
'title':'Leggere quantità e diametro del richiamo G01-R06',
'question':'Nella zona evidenziata di TAV-05A, individua il richiamo G01-R06 e verifica se sono leggibili quantità e diametro dell’armatura.',
'known':'La lunghezza 1040 è già documentata: non devi ricontrollarla.',
'unknown':'Mancano soltanto quantità e diametro.',
'conflict':'Nessun conflitto accertato.',
'where':'Guarda dentro la zona evidenziata del viewer. Usa “Centra evidenza”; poi aumenta lo zoom finché il testo del richiamo è leggibile.',
'look_for':'Cerca la notazione del richiamo G01-R06 e trascrivi soltanto il numero di barre e il diametro effettivamente leggibili accanto al richiamo.',
'dont':'Non ricavare quantità o diametro da armature vicine, da schemi simili o per analogia.',
'confirmed':'Scegli CONFERMATO solo se quantità e diametro sono entrambi leggibili direttamente nella tavola.',
'fallback':'Se uno dei due dati non è leggibile con sicurezza, scegli ILLEGGIBILE oppure SERVE UNA FONTE MIGLIORE.'},
'ERW-N12-002':{
'title':'Leggere quantità e diametro del richiamo G07-R07',
'question':'Nella zona evidenziata di TAV-05A, individua il richiamo G07-R07 e verifica se sono leggibili quantità e diametro dell’armatura.',
'known':'La lunghezza 865 è già documentata: non devi ricontrollarla.',
'unknown':'Mancano soltanto quantità e diametro.',
'conflict':'Nessun conflitto accertato.',
'where':'Guarda dentro la zona evidenziata del viewer. Usa “Centra evidenza”; poi aumenta lo zoom sul testo associato a G07-R07.',
'look_for':'Cerca la notazione del richiamo G07-R07 e trascrivi soltanto il numero di barre e il diametro effettivamente leggibili.',
'dont':'Non usare richiami adiacenti o dettagli simili come sostituti della lettura diretta.',
'confirmed':'Scegli CONFERMATO solo se quantità e diametro sono entrambi leggibili direttamente nella tavola.',
'fallback':'Se uno dei due dati resta incerto, scegli ILLEGGIBILE oppure SERVE UNA FONTE MIGLIORE.'},
'ERW-N12-003':{
'title':'Leggere le dimensioni mancanti del sagomato G05-R04',
'question':'Nella zona evidenziata di TAV-05A, individua la continuazione del sagomato intermedio G05-R04 e verifica quali quote dimensionali sono realmente leggibili.',
'known':'La presenza della continuazione del sagomato intermedio è già documentata come parzialmente leggibile.',
'unknown':'Mancano alcune dimensioni del sagomato.',
'conflict':'Nessun conflitto accertato.',
'where':'Centra la zona evidenziata e segui graficamente il sagomato G05-R04 fino alle quote poste direttamente sul suo tracciato o immediatamente associate ad esso.',
'look_for':'Leggi soltanto le quote che possono essere associate senza ambiguità al sagomato G05-R04.',
'dont':'Non trasferire quote da sagomati vicini e non completare geometricamente quote mancanti per simmetria o proporzione.',
'confirmed':'Scegli CONFERMATO soltanto se le dimensioni che risolvono il residuo sono leggibili e chiaramente riferibili a G05-R04.',
'fallback':'Se la continuità è visibile ma le quote restano ambigue, scegli ILLEGGIBILE e descrivi quali parti riesci comunque a vedere.'},
'ERW-N12-004':{
'title':'Verificare a quale elemento appartiene lo schema T6A-G03',
'question':'Nella zona evidenziata di TAV-06A, verifica se esiste un’indicazione diretta che colleghi lo schema T6A-G03 a G5-B017 oppure a un altro elemento identificabile.',
'known':'Lo schema T6A-G03 è documentato. G5-B017 collega gli appoggi 12–19.',
'unknown':'Non è documentata un’associazione diretta fra lo schema di armatura e uno specifico elemento canonico.',
'conflict':'Lo schema T6A-G03 mostra due appoggi e uno sbalzo libero, mentre G5-B017 è appoggio-appoggio.',
'where':'Osserva prima l’intero contesto dello schema, poi centra la zona evidenziata. Cerca sigle, riferimenti, continuità grafiche o indicazioni testuali che identifichino l’elemento a cui appartiene.',
'look_for':'Serve un collegamento documentale diretto: sigla, riferimento o contesto univoco. La sola somiglianza geometrica non basta.',
'dont':'Non associare T6A-G03 a G5-B017 solo perché è un candidato già noto o perché la forma appare simile.',
'confirmed':'Scegli CONFERMATO solo se la tavola fornisce un legame diretto e non ambiguo con uno specifico elemento.',
'fallback':'Se la tavola non consente un legame univoco, scegli NON ASSOCIABILE. Questo è un esito valido, non un errore di review.'}
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
            'title_it':it['title'],'question_it':it['question'],'known_it':it['known'],'unknown_it':it['unknown'],'conflict_it':it['conflict'],
            'where_it':it['where'],'look_for_it':it['look_for'],'dont_it':it['dont'],'confirmed_it':it['confirmed'],'fallback_it':it['fallback'],
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
    manifest={'contract_id':contract['contract_id'],'authority':'HUMAN_REVIEW_INPUT_ONLY','ui_language':'it','guided_review':True,'prefilled_decisions':0,'entries':entries}
    (out/'human_review_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    html='''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW F7 — Revisione tecnica guidata</title><style>body{font-family:system-ui;margin:1rem;max-width:1180px;color:#202124}section{border:1px solid #bbb;padding:1rem;margin:1.3rem 0;border-radius:8px}textarea,input,select{width:100%;box-sizing:border-box;margin:.25rem 0 .75rem;padding:.55rem}button{padding:.6rem 1rem}iframe{width:100%;height:62vh;border:2px solid #555}.warn{font-weight:700}.intro{background:#f5f7f8;padding:.9rem;border-left:5px solid #555}.goal{font-size:1.1rem;background:#eef5ff;padding:.8rem;border-radius:6px}.guide{border:1px solid #ccc;background:#fffdf6;padding:.8rem 1rem;margin:.8rem 0}.guide h3{margin-top:0}.step{margin:.55rem 0}.stop{background:#fff0f0;padding:.6rem;border-left:4px solid #a00}.ok{background:#eef8ee;padding:.6rem;border-left:4px solid #287a28}.fallback{background:#f6f6f6;padding:.6rem;border-left:4px solid #777}.advanced{margin-top:1rem;border-top:1px dashed #aaa;padding-top:.5rem}.advanced summary{cursor:pointer;font-weight:600}.decision{background:#f8f8f8;padding:.9rem;margin-top:1rem;border-radius:6px}</style></head><body><h1>CEW F7 — Revisione tecnica guidata</h1><p class="warn">La tavola originale è l’autorità. Il tuo compito è leggere o verificare soltanto ciò che è indicato nella scheda: non devi ricostruire il modello né interpretare i codici del repository.</p><div class="intro"><b>Come si usa:</b> 1) leggi “Cosa devi controllare”; 2) nel viewer premi <b>Centra evidenza</b> e fai zoom; 3) cerca esattamente l’informazione descritta; 4) scegli l’esito. Se il dato non è chiaro, dichiararlo ILLEGGIBILE o NON ASSOCIABILE è un risultato corretto.</div><div id="tasks"></div><script src="app.js"></script></body></html>'''
    js=r'''const outcomes=[['','— scegli —'],['CONFIRMED','CONFERMATO — ho letto/verificato il dato'],['REJECTED','RESPINTO — la fonte contraddice la proposta'],['UNREADABLE','ILLEGGIBILE — il dato non si legge con sicurezza'],['UNBOUND','NON ASSOCIABILE — manca un legame univoco'],['NEEDS_BETTER_SOURCE','SERVE UNA FONTE MIGLIORE'],['NEEDS_SITE_SURVEY','SERVE RILIEVO IN SITO'],['DEFER','RINVIA']];const states=[['','— lascia vuoto se non necessario —'],['ND','ND — non determinato'],['INF','INF — inferito'],['RIF','RIF — riferimento'],['MIS','MIS — misurato'],['DOC','DOC — documentato']];
async function boot(){const m=await(await fetch('human_review_manifest.json',{cache:'no-store'})).json();const root=document.getElementById('tasks');for(const e of m.entries){const s=document.createElement('section');s.innerHTML=`<h2>${e.title_it}</h2><div><small>${e.task_id} · ${e.residual_id}</small></div><div class="goal"><b>Cosa devi controllare</b><br>${e.question_it}</div><div class="guide"><h3>Indicazioni sulla tavola</h3><div class="step"><b>1. Dove guardare:</b> ${e.where_it}</div><div class="step"><b>2. Cosa cercare:</b> ${e.look_for_it}</div><div class="stop"><b>Non fare questo:</b> ${e.dont_it}</div><div class="ok"><b>Quando puoi confermare:</b> ${e.confirmed_it}</div><div class="fallback"><b>Se non riesci a verificarlo:</b> ${e.fallback_it}</div></div><p><b>Già noto:</b> ${e.known_it||'—'}<br><b>Ancora da determinare:</b> ${e.unknown_it||'—'}<br><b>Eventuale conflitto:</b> ${e.conflict_it||'—'}</p><iframe src="${e.viewer_url}" title="Fonte primaria per ${e.task_id}"></iframe><div class="decision"><h3>Registra il risultato della tua lettura</h3><label>Revisore</label><input data-k="reviewer" placeholder="Nome e cognome"><label>Esito</label><select data-k="outcome">${outcomes.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select><label>Cosa hai letto o verificato nella tavola?</label><textarea data-k="human_observation" placeholder="Esempio di forma: “Nel richiamo ... leggo ...”. Non aggiungere deduzioni o analogie."></textarea><label><input type="checkbox" data-k="direct_primary_evidence_observed" style="width:auto"> Confermo di aver controllato direttamente la tavola primaria mostrata sopra</label><details class="advanced"><summary>Parametri di governance avanzati</summary><p>Questi campi servono al motore CEW dopo la lettura tecnica. Non descrivono ciò che devi cercare sulla tavola.</p><label>Stato epistemico richiesto</label><select data-k="requested_epistemic_state">${states.map(([v,l])=>`<option value="${v}">${l}</option>`).join('')}</select><label>ID target di promozione (necessario solo per CONFERMATO)</label><input data-k="target_id"><label>ID approvazione riapertura (solo se richiesto)</label><input data-k="reopen_approval_id"></details><label><input type="checkbox" data-k="authority_acknowledgement" style="width:auto"> Dichiaro di comprendere che questo export registra la mia revisione e non modifica direttamente i dati canonici.</label><br><button>Esporta la decisione in JSON</button></div>`;s.querySelector('button').onclick=()=>exp(s,e);root.appendChild(s)}}
function exp(s,e){let d=structuredClone(e.decision_template);for(const el of s.querySelectorAll('[data-k]'))d[el.dataset.k]=el.type==='checkbox'?el.checked:el.value.trim();d.decision_id=`HUMAN-${e.task_id}-${Date.now()}`;d.timestamp=new Date().toISOString();if(!d.reviewer||!d.outcome||!d.authority_acknowledgement){alert('Sono obbligatori: Revisore, Esito e dichiarazione finale.');return}if(d.outcome==='CONFIRMED'&&(!d.human_observation||d.direct_primary_evidence_observed!==true||!d.target_id)){alert('Per CONFERMATO devi descrivere ciò che hai letto, confermare la verifica diretta della tavola e indicare il target di promozione nei parametri avanzati.');return}if(d.outcome!=='CONFIRMED'&&d.target_id){alert('Con un esito diverso da CONFERMATO il target di promozione deve restare vuoto.');return}const blob=new Blob([JSON.stringify(d,null,2)+'\n'],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=d.decision_id+'.json';a.click();URL.revokeObjectURL(a.href)}boot();'''
    (out/'index.html').write_text(html,encoding='utf-8');(out/'app.js').write_text(js,encoding='utf-8')
    print('HUMAN_REVIEW_PACK_BUILT');print('TASKS=4');print('PREFILLED_DECISIONS=0');print('UI_LANGUAGE=it');print('GUIDED_REVIEW=YES');print('CANONICAL_WRITE=FORBIDDEN');return 0
if __name__=='__main__':raise SystemExit(main())
