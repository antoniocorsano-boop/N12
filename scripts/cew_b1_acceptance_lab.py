#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ROOT / "automation/CEW_USABILITY_METRICS_MODEL_v1.json"
CONTRACT = ROOT / "automation/CEW_B1_USABILITY_ACCEPTANCE_CONTRACT_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _esc(value) -> str:
    return html.escape(str(value or ""))


def task_specs() -> list[dict]:
    metrics = _load(METRICS)
    starts = {
        "UX-DOC-01": "/",
        "UX-DOC-02": "/drawings",
        "UX-DOC-03": "/drawings/TAV-05A",
        "UX-DOC-04": "/drawings/TAV-05A",
    }
    return [{**row, "start_path": starts[row["task_id"]]} for row in metrics.get("initial_cew_b11_tasks", [])]


TEMPLATE = r'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — B1 Acceptance Lab</title>
<style>
:root{--ink:#17202a;--muted:#65717e;--line:#d8dde3;--bg:#eef1f4;--accent:#173f5f;--bad:#a12622;--ok:#24613e}*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}header{background:#fff;border-bottom:1px solid var(--line);padding:14px 20px}header .row{max-width:1600px;margin:auto;display:flex;gap:14px;align-items:center;flex-wrap:wrap}h1{font-size:22px;margin:0}.brand{font-size:11px;letter-spacing:.08em;font-weight:850;color:var(--accent)}.muted{color:var(--muted)}main{max-width:1600px;margin:auto;padding:12px 20px 28px;display:grid;grid-template-columns:380px minmax(0,1fr);gap:12px}.panel{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px}#workspace{height:calc(100vh - 105px);min-height:620px;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}iframe{width:100%;height:100%;border:0}button,select,input,textarea{font:inherit}button{border:1px solid #bcc7d0;background:#fff;padding:8px 10px;border-radius:7px;font-weight:750;cursor:pointer;color:var(--ink)}button.primary{background:var(--accent);color:#fff;border-color:var(--accent)}button:disabled{opacity:.45;cursor:not-allowed}.tasklist{display:grid;gap:6px;margin:10px 0}.taskbutton{text-align:left;width:100%}.taskbutton.done{border-left:5px solid var(--ok)}.taskbutton.active{outline:2px solid var(--accent)}.prompt{background:#f7f9fb;border-left:4px solid var(--accent);padding:10px;margin:8px 0;font-size:14px}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px}label{font-size:12px;font-weight:700;color:#46515c}label input,label select,label textarea{display:block;width:100%;margin-top:3px;padding:7px;border:1px solid #cbd3da;border-radius:6px;background:#fff;color:var(--ink)}textarea{min-height:70px;resize:vertical}.checks{display:grid;gap:5px;margin:9px 0}.checks label{display:flex;align-items:flex-start;gap:7px;font-weight:600;color:var(--ink)}.checks input{width:auto;margin:2px 0 0}.counter{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}.pill{font-size:12px;background:#eef3f7;border-radius:999px;padding:5px 8px}.actions{display:flex;gap:6px;flex-wrap:wrap}#decisionBox{margin-top:12px;border-top:1px solid var(--line);padding-top:12px}.blocker{color:var(--bad);font-weight:750}.clear{color:var(--ok);font-weight:750}code{font-size:11px;overflow-wrap:anywhere}@media(max-width:950px){main{grid-template-columns:1fr}#workspace{height:70vh}}
</style></head><body>
<header><div class="row"><a href="/">← Progetto</a><div><div class="brand">CEW · B1.7 HUMAN FACTORS ACCEPTANCE</div><h1>Acceptance Lab — Documenti → Tavole → Evidenza</h1><div class="muted">Misura task reali. Non modifica dati ingegneristici e non certifica automaticamente B1.</div></div></div></header>
<main><aside class="panel"><div><b>Revisione runtime</b><br><code>__COMMIT_HTML__</code><br><span class="muted">__DEPLOYMENT_HTML__</span></div><div class="tasklist" id="taskList"></div>
<section id="taskPanel" hidden><div id="taskPrompt" class="prompt"></div><div class="counter"><span class="pill">Tempo: <b id="time">0</b>s</span><span class="pill">Interazioni: <b id="interactions">0</b></span><span class="pill">Aiuti: <b id="helps">0</b></span><span class="pill">Recuperi: <b id="backtracks">0</b></span></div><div class="actions"><button id="startBtn" class="primary">Avvia task</button><button id="helpBtn" disabled>Registra aiuto</button><button id="backBtn" disabled>Registra recupero/backtrack</button><button id="stopBtn" disabled>Concludi task</button></div>
<div id="resultForm" hidden><hr><div class="metrics"><label>Esito<select id="resultState"><option value="">— seleziona —</option>__RESULT_OPTIONS__</select></label><label>Facilità 1–5<input id="ease" type="number" min="1" max="5"></label><label>Confidenza correttezza 1–5<input id="confidence" type="number" min="1" max="5"></label><label>Tempo percepito 1–5<input id="perceived" type="number" min="1" max="5"></label></div><div class="checks"><label><input id="wrongSource" type="checkbox"> Ho selezionato fonte/versione sbagliata</label><label><input id="authorityError" type="checkbox"> Ho frainteso quale oggetto aveva autorità</label><label><input id="canonicalMisconception" type="checkbox"> Ho pensato che visualizzare/revisionare modificasse automaticamente il canonico</label><label><input id="navSuccess" type="checkbox"> Navigazione documento → evidenza riuscita (se pertinente)</label><label><input id="primaryCorrect" type="checkbox"> Ho identificato correttamente il PDF primario (se pertinente)</label><label><input id="derivedCorrect" type="checkbox"> Ho identificato correttamente l'ausilio derivato (se pertinente)</label></div><label>Commento<textarea id="comment"></textarea></label><button id="saveBtn" class="primary">Salva risultato task</button></div></section>
<section id="decisionBox"><h3>Decisione HVA</h3><div id="readiness" class="muted">Completa tutti i task.</div><label>Decisione umana<select id="hvaDecision" disabled><option value="">— non ancora —</option><option>PASS_FOR_B1</option><option>PASS_WITH_NONCRITICAL_USABILITY_RESIDUAL</option><option>FAIL_REWORK_REQUIRED</option></select></label><label>Revisore<input id="reviewer" placeholder="nome del revisore" disabled></label><label>Nota HVA<textarea id="hvaNote" disabled></textarea></label><div class="actions"><button id="exportBtn" disabled>Esporta receipt JSON</button></div><p class="muted">La receipt è prova di usability/HVA, non una scrittura canonica. Dopo un esito PASS serve ancora lo smoke Production sulla stessa revisione accettata.</p></section></aside><section id="workspace"><iframe id="journey" title="CEW task workspace" src="about:blank"></iframe></section></main>
<script>
const tasks=__TASKS_JSON__; const runtimeRevision=__COMMIT_JSON__; const runtimeDeployment=__DEPLOYMENT_JSON__; let current=null,startAt=null,timer=null,metrics={},results={};
const $=id=>document.getElementById(id); const frame=$('journey');
function renderTasks(){const root=$('taskList');root.innerHTML='';tasks.forEach(t=>{const b=document.createElement('button');b.className='taskbutton'+(results[t.task_id]?' done':'')+(current&&current.task_id===t.task_id?' active':'');b.textContent=t.task_id+' — '+t.goal;b.onclick=()=>selectTask(t);root.appendChild(b)})}
function selectTask(t){if(startAt)return;current=t;metrics={time_on_task_seconds:0,interaction_count:0,help_requests:0,backtracks_or_recovery_actions:0};$('taskPanel').hidden=false;$('taskPrompt').innerHTML='<b>'+t.task_id+'</b><br>'+t.goal+'<br><small>Successo: '+t.success_condition+'</small>';$('startBtn').disabled=false;$('resultForm').hidden=true;resetFields();renderCounters();renderTasks();frame.src='about:blank'}
function resetFields(){['resultState','ease','confidence','perceived','comment'].forEach(id=>$(id).value='');['wrongSource','authorityError','canonicalMisconception','navSuccess','primaryCorrect','derivedCorrect'].forEach(id=>$(id).checked=false)}
function renderCounters(){$('time').textContent=metrics.time_on_task_seconds;$('interactions').textContent=metrics.interaction_count;$('helps').textContent=metrics.help_requests;$('backtracks').textContent=metrics.backtracks_or_recovery_actions}
function startTask(){if(!current)return;startAt=Date.now();metrics={time_on_task_seconds:0,interaction_count:0,help_requests:0,backtracks_or_recovery_actions:0};frame.src=current.start_path;$('startBtn').disabled=true;$('stopBtn').disabled=false;$('helpBtn').disabled=false;$('backBtn').disabled=false;timer=setInterval(()=>{metrics.time_on_task_seconds=Math.round((Date.now()-startAt)/1000);renderCounters()},500)}
function stopTask(){if(!startAt)return;clearInterval(timer);metrics.time_on_task_seconds=Math.round((Date.now()-startAt)/1000);startAt=null;$('stopBtn').disabled=true;$('helpBtn').disabled=true;$('backBtn').disabled=true;$('resultForm').hidden=false;renderCounters()}
frame.addEventListener('load',()=>{try{frame.contentDocument.addEventListener('click',()=>{if(startAt){metrics.interaction_count++;renderCounters()}},true)}catch(_e){}});
$('startBtn').onclick=startTask;$('stopBtn').onclick=stopTask;$('helpBtn').onclick=()=>{metrics.help_requests++;renderCounters()};$('backBtn').onclick=()=>{metrics.backtracks_or_recovery_actions++;renderCounters()};
$('saveBtn').onclick=()=>{if(!current||!$('resultState').value)return alert('Seleziona un esito.');for(const id of ['ease','confidence','perceived']){const v=Number($(id).value);if(v<1||v>5)return alert('Le scale devono essere 1–5.')}results[current.task_id]={task_id:current.task_id,goal:current.goal,success_condition:current.success_condition,...metrics,result_state:$('resultState').value,ease_1_to_5:Number($('ease').value),confidence_correct_1_to_5:Number($('confidence').value),perceived_time_1_to_5:Number($('perceived').value),free_comment:$('comment').value,wrong_source_or_wrong_version_selection:$('wrongSource').checked,authority_boundary_errors:$('authorityError').checked,canonical_write_misconception:$('canonicalMisconception').checked,document_to_evidence_navigation_success:$('navSuccess').checked,primary_source_correctly_identified:$('primaryCorrect').checked,derived_reading_aid_correctly_identified:$('derivedCorrect').checked};current=null;$('taskPanel').hidden=true;frame.src='about:blank';renderTasks();updateReadiness()};
function blockers(){const out=[];for(const t of tasks){const r=results[t.task_id];if(!r){out.push(t.task_id+': non osservato');continue}if(r.result_state==='FALSE_SUCCESS'||r.result_state==='ABANDONED'||r.result_state==='BLOCKED_BY_PRODUCT')out.push(t.task_id+': '+r.result_state);if(r.wrong_source_or_wrong_version_selection)out.push(t.task_id+': fonte/versione sbagliata');if(r.authority_boundary_errors)out.push(t.task_id+': errore di autorità');if(r.canonical_write_misconception)out.push(t.task_id+': equivoco canonical write')}return out}
function updateReadiness(){const b=blockers();const complete=tasks.every(t=>results[t.task_id]);if(!complete){$('readiness').className='muted';$('readiness').textContent='Completa tutti i task.';return}if(b.length){$('readiness').className='blocker';$('readiness').textContent='Blocker: '+b.join(' · ')}else{$('readiness').className='clear';$('readiness').textContent='Nessun blocker critico rilevato. La decisione resta al revisore umano.'}['hvaDecision','reviewer','hvaNote','exportBtn'].forEach(id=>$(id).disabled=false)}
$('exportBtn').onclick=()=>{if(!$('hvaDecision').value||!$('reviewer').value.trim())return alert('Decisione HVA e revisore sono obbligatori.');const receipt={schema_version:'1.0',receipt_type:'CEW_B1_USABILITY_HVA',generated_at:new Date().toISOString(),runtime_revision:runtimeRevision,runtime_deployment:runtimeDeployment,journey:'Project -> Documents -> Drawings -> Drawing Viewer -> DocumentMap -> Evidence -> Drawing context',task_results:tasks.map(t=>results[t.task_id]),critical_blockers:blockers(),human_hva_decision:$('hvaDecision').value,human_reviewer:$('reviewer').value.trim(),human_note:$('hvaNote').value,production_smoke_required:true,slice_complete:false,canonical_write_authorized:false,engineering_authority_effect:'NONE'};const blob=new Blob([JSON.stringify(receipt,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='CEW_B1_HVA_RECEIPT_'+new Date().toISOString().replace(/[:.]/g,'-')+'.json';a.click();URL.revokeObjectURL(a.href)};
renderTasks();updateReadiness();
</script></body></html>'''


def build_lab() -> str:
    contract = _load(CONTRACT)
    tasks = task_specs()
    commit = os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("GITHUB_SHA") or "UNRESOLVED_RUNTIME_REVISION"
    deployment = os.getenv("VERCEL_URL") or "LOCAL_OR_UNRESOLVED_DEPLOYMENT"
    options = "".join(
        f"<option value='{_esc(state)}'>{_esc(state.replace('_', ' '))}</option>"
        for state in contract["result_states"]
    )
    return (
        TEMPLATE
        .replace("__COMMIT_HTML__", _esc(commit))
        .replace("__DEPLOYMENT_HTML__", _esc(deployment))
        .replace("__RESULT_OPTIONS__", options)
        .replace("__TASKS_JSON__", json.dumps(tasks, ensure_ascii=False).replace("</", "<\\/"))
        .replace("__COMMIT_JSON__", json.dumps(commit))
        .replace("__DEPLOYMENT_JSON__", json.dumps(deployment))
    )
