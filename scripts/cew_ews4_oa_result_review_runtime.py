#!/usr/bin/env python3
from __future__ import annotations

EWS4_RUNTIME_MARKER = "CEW_EWS4_OA_RESULT_REVIEW_CONTROLLER"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def augment(rendered: str, task: str) -> str:
    """Replace the expanded OA similarity stack with bounded enterprise review UI.

    This layer does not compute similarity and does not persist OA decisions itself.
    It adapts the existing governed OA-3/OA-4 runtime: summary -> paged review set ->
    one active candidate. OA-4 remains the owner of decision persistence.
    """
    if EWS4_RUNTIME_MARKER in rendered:
        return rendered

    style = '''
<style id="cew-ews4-oa-result-review-style">
body.ews4-oa-review #oaClusterReview{display:none!important}
.ews4-review{border-top:1px solid var(--line);margin-top:10px;padding-top:10px}
.ews4-summary-head{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:7px}
.ews4-summary-head h3{margin:0!important}.ews4-progress{font-size:11px;color:var(--muted);white-space:nowrap}
.ews4-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin:7px 0}
.ews4-metric{border:1px solid var(--line);border-radius:6px;padding:6px;background:#f8fafb;font-size:10px}.ews4-metric b{display:block;font-size:17px;color:var(--ink)}
.ews4-filters{display:flex;gap:4px;flex-wrap:wrap;margin:7px 0}.ews4-filter{padding:5px 7px;font-size:11px}.ews4-filter[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.ews4-set{display:grid;gap:4px;margin:7px 0}.ews4-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;width:100%;text-align:left;padding:6px 7px;border:1px solid var(--line);border-radius:6px;background:#fff}.ews4-row[aria-current="true"]{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent);background:#f2f8fc}.ews4-row-main{min-width:0}.ews4-row-main b,.ews4-row-main small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ews4-row-main small{color:var(--muted);font-size:10px}.ews4-row-score{font-weight:850;font-size:13px}
.ews4-page-nav,.ews4-active-nav{display:flex;align-items:center;justify-content:space-between;gap:6px;margin:6px 0}.ews4-page-nav span,.ews4-active-nav span{font-size:11px;color:var(--muted);text-align:center;flex:1}.ews4-page-nav button,.ews4-active-nav button{padding:5px 8px}
.ews4-active{border:2px solid var(--accent);border-radius:8px;padding:9px;background:#f7fbfe;margin-top:8px}.ews4-active-kicker{font-size:10px;font-weight:850;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}.ews4-active h4{margin:3px 0 5px;font-size:15px}.ews4-active-score{font-size:22px;font-weight:900}.ews4-reasons{margin:7px 0 0;padding-left:17px;font-size:11px;color:var(--muted);max-height:108px;overflow:auto}.ews4-spatial-note{background:#fff7e8;border-left:4px solid var(--warn);padding:7px;margin:7px 0;font-size:11px}.ews4-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:5px;margin-top:8px}.ews4-actions button{padding:7px;font-size:11px}.ews4-actions .confirm{background:var(--accent);color:#fff;border-color:var(--accent)}.ews4-decision-state{font-size:11px;margin-top:7px;min-height:16px}.ews4-decision-state.ok{color:var(--ok);font-weight:750}.ews4-decision-state.error{color:var(--danger);font-weight:750}.ews4-authority{font-size:10px;color:var(--muted);border-top:1px solid var(--line);margin-top:8px;padding-top:7px}
@media(max-width:1100px) and (min-width:901px){.ews4-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    script = f'''
<script id="cew-ews4-oa-result-review-script" data-ews4-runtime="{EWS4_RUNTIME_MARKER}">
(() => {{
const EWS4_MARKER={EWS4_RUNTIME_MARKER!r};
const OA_PILOT_TASK={OA_PILOT_TASK!r};
if(TASK!==OA_PILOT_TASK)return;
document.body.classList.add('ews4-oa-review');
document.body.dataset.ews4Review=EWS4_MARKER;
const PAGE_SIZE=8;
let filter='ALL',page=0,activeId=null;
const reviewedKey='cew-ews4:'+TASK+':reviewed';
function latestRun(){{try{{return JSON.parse(sessionStorage.getItem('cew-oa3:'+TASK+':latest')||'null')}}catch(e){{return null}}}}
function reviewedMap(){{try{{return JSON.parse(sessionStorage.getItem(reviewedKey)||'{{}}')}}catch(e){{return {{}}}}}}
function saveReviewed(map){{sessionStorage.setItem(reviewedKey,JSON.stringify(map))}}
function counts(rows){{const out={{STRONG_SIMILAR:0,POSSIBLE_SIMILAR:0,WEAK:0,EXCLUDED:0}};rows.forEach(r=>{{out[r.state]=(out[r.state]||0)+1}});return out}}
function filtered(rows){{return filter==='ALL'?rows:rows.filter(r=>r.state===filter)}}
function ensureHost(){{const host=document.getElementById('oaSimilarResult');if(!host)return null;host.classList.add('ews4-review');return host}}
function candidateLabel(id){{const obj=(scene?.objects||[]).find(o=>o.object_id===id),p=obj?.properties||{{}};const support=p.support_id?('Supporto '+p.support_id):id;const section=p.section_cm?(' · '+p.section_cm):'';return support+section}}
function stateLabel(state){{return {{STRONG_SIMILAR:'Forte',POSSIBLE_SIMILAR:'Possibile',WEAK:'Debole',EXCLUDED:'Escluso'}}[state]||state}}
function activeRows(run){{return filtered(run?.candidates||[])}}
function setActive(id){{activeId=id;renderReview()}}
function moveActive(delta){{const run=latestRun(),rows=activeRows(run);if(!rows.length)return;let i=Math.max(0,rows.findIndex(r=>r.candidate_object_id===activeId));i=(i+delta+rows.length)%rows.length;activeId=rows[i].candidate_object_id;page=Math.floor(i/PAGE_SIZE);renderReview()}}
function setFilter(next){{filter=next;page=0;const rows=activeRows(latestRun());activeId=rows[0]?.candidate_object_id||null;renderReview()}}
function renderReview(){{
 const host=ensureHost(),run=latestRun();if(!host)return;
 if(!run||run.state!=='DETERMINISTIC_SIMILARITY_CANDIDATES'){{host.innerHTML='';return}}
 const all=run.candidates||[],c=counts(all),rows=activeRows(run),reviewed=reviewedMap();
 if(!activeId||!rows.some(r=>r.candidate_object_id===activeId))activeId=rows[0]?.candidate_object_id||null;
 const pageCount=Math.max(1,Math.ceil(rows.length/PAGE_SIZE));page=Math.max(0,Math.min(page,pageCount-1));const start=page*PAGE_SIZE,visible=rows.slice(start,start+PAGE_SIZE),active=all.find(r=>r.candidate_object_id===activeId)||null;
 const reviewedCount=Object.keys(reviewed).filter(id=>all.some(r=>r.candidate_object_id===id)).length;
 host.innerHTML=`<div class="ews4-summary-head"><div><div class="oa-human-kicker">Review set</div><h3>${{run.family_id||run.object_type||'Candidati simili'}}</h3></div><div class="ews4-progress">${{reviewedCount}} / ${{all.length}} revisionati</div></div>
 <div class="ews4-summary-grid"><div class="ews4-metric">Forti<b>${{c.STRONG_SIMILAR||0}}</b></div><div class="ews4-metric">Possibili<b>${{c.POSSIBLE_SIMILAR||0}}</b></div><div class="ews4-metric">Deboli<b>${{c.WEAK||0}}</b></div><div class="ews4-metric">Esclusi<b>${{c.EXCLUDED||0}}</b></div></div>
 <div class="ews4-filters" role="group" aria-label="Filtra candidati">${{[['ALL','Tutti'],['STRONG_SIMILAR','Forti'],['POSSIBLE_SIMILAR','Possibili'],['WEAK','Deboli'],['EXCLUDED','Esclusi']].map(([v,l])=>`<button class="ews4-filter" data-filter="${{v}}" aria-pressed="${{String(filter===v)}}">${{l}}</button>`).join('')}}</div>
 <div class="ews4-set" aria-label="Candidati pagina corrente">${{visible.map(r=>`<button class="ews4-row" data-candidate="${{r.candidate_object_id}}" aria-current="${{String(r.candidate_object_id===activeId)}}"><span class="ews4-row-main"><b>${{candidateLabel(r.candidate_object_id)}}</b><small>${{stateLabel(r.state)}}${{reviewed[r.candidate_object_id]?' · '+reviewed[r.candidate_object_id]:''}}</small></span><span class="ews4-row-score">${{Math.round(r.score*100)}}%</span></button>`).join('')||'<div class="oa-muted">Nessun candidato nel filtro corrente.</div>'}}</div>
 <div class="ews4-page-nav"><button id="ews4PrevPage" ${{page<=0?'disabled':''}}>←</button><span>Pagina ${{page+1}} / ${{pageCount}} · ${{rows.length}} risultati</span><button id="ews4NextPage" ${{page>=pageCount-1?'disabled':''}}>→</button></div>
 ${{active?`<article class="ews4-active"><div class="ews4-active-kicker">Candidato attivo</div><h4>${{candidateLabel(active.candidate_object_id)}}</h4><div><span class="ews4-active-score">${{Math.round(active.score*100)}}%</span> · ${{stateLabel(active.state)}}</div><div class="ews4-spatial-note">Posizione sulla tavola non registrata: nessun focus spaziale viene inventato. Il punteggio è supporto alla revisione, non autorità.</div><ul class="ews4-reasons">${{(active.reason_codes||[]).map(x=>'<li>'+String(x).replace(/[&<>]/g,'')+'</li>').join('')}}</ul><div class="ews4-active-nav"><button id="ews4PrevCandidate">← Precedente</button><span>un solo candidato primario</span><button id="ews4NextCandidate">Successivo →</button></div><div class="ews4-actions"><button class="confirm" data-decision="CONFIRM_AS_FAMILY_CANDIDATE">Conferma candidato</button><button data-decision="REJECT">Rifiuta</button><button data-decision="MARK_AMBIGUOUS">Ambiguo</button><button data-decision="DEFER_NEEDS_SOURCE">Serve fonte</button></div><div id="ews4DecisionState" class="ews4-decision-state">${{reviewed[active.candidate_object_id]?'Decisione sessione: '+reviewed[active.candidate_object_id]:''}}</div><div class="ews4-authority">Decisione esplicita per singolo candidato. Nessuna conferma implicita del cluster; OA-4 resta proprietario della receipt append-only.</div></article>`:''}}
 `;
 host.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>setFilter(b.dataset.filter));host.querySelectorAll('[data-candidate]').forEach(b=>b.onclick=()=>setActive(b.dataset.candidate));
 const prevPage=document.getElementById('ews4PrevPage'),nextPage=document.getElementById('ews4NextPage');if(prevPage)prevPage.onclick=()=>{{page--;renderReview()}};if(nextPage)nextPage.onclick=()=>{{page++;renderReview()}};
 const prev=document.getElementById('ews4PrevCandidate'),next=document.getElementById('ews4NextCandidate');if(prev)prev.onclick=()=>moveActive(-1);if(next)next.onclick=()=>moveActive(1);
 host.querySelectorAll('[data-decision]').forEach(b=>b.onclick=()=>persistActiveDecision(b.dataset.decision));
}}
function persistActiveDecision(decision){{
 const run=latestRun(),active=run?.candidates?.find(r=>r.candidate_object_id===activeId),state=document.getElementById('ews4DecisionState');if(!active||!state)return;
 const load=document.getElementById('oaLoadReview'),save=document.getElementById('oaSaveReview'),legacyHost=document.getElementById('oaReviewCandidates');if(!load||!save||!legacyHost){{state.className='ews4-decision-state error';state.textContent='Revisione governata OA-4 non disponibile.';return}}
 load.click();const rows=[...legacyHost.querySelectorAll('.oa4-candidate')];rows.forEach(r=>{{const cb=r.querySelector('.oa4-select');if(cb)cb.checked=false}});const row=rows.find(r=>r.dataset.candidate===activeId);if(!row){{state.className='ews4-decision-state error';state.textContent='Candidato non disponibile nella revisione OA-4.';return}}
 const cb=row.querySelector('.oa4-select'),choice=row.querySelector('.oa4-choice');cb.checked=true;choice.value=decision;choice.dispatchEvent(new Event('change',{{bubbles:true}}));const reviewer=document.getElementById('oaReviewReviewer'),teacher=document.getElementById('oaTeachReviewer');if(reviewer&&teacher?.value)reviewer.value=teacher.value;
 state.className='ews4-decision-state';state.textContent='Registrazione append-only in corso…';save.click();let tries=0;const timer=setInterval(()=>{{tries++;let review=null;try{{review=JSON.parse(sessionStorage.getItem('cew-oa4:'+TASK+':latest')||'null')}}catch(e){{}}const hit=review?.candidate_decisions?.find(x=>x.candidate_object_id===activeId&&x.decision===decision);if(hit&&review?.governed_receipt_id){{clearInterval(timer);const map=reviewedMap();map[activeId]=decision;saveReviewed(map);state.className='ews4-decision-state ok';state.textContent='Decisione registrata append-only.';renderReview();window.dispatchEvent(new CustomEvent('cew:ews4-candidate-reviewed',{{detail:{{candidate_object_id:activeId,decision,receipt_id:review.governed_receipt_id}}}}));}}else if(tries>50){{clearInterval(timer);state.className='ews4-decision-state error';state.textContent='Receipt non confermata. Nessuna decisione è considerata registrata.';}}}},120);
}}
function init(){{const host=ensureHost();if(!host)return;const run=latestRun();if(run?.state==='DETERMINISTIC_SIMILARITY_CANDIDATES')renderReview();window.addEventListener('cew:oa3-similarity-run',()=>{{filter='ALL';page=0;activeId=null;setTimeout(renderReview,0)}});}}
let tries=0;const timer=setInterval(()=>{{tries++;if(document.getElementById('oaSimilarResult')&&document.getElementById('oaClusterReview')){{clearInterval(timer);init()}}else if(tries>100)clearInterval(timer)}},80);
}})();
</script>'''
    return rendered.replace("</body>", script + "</body>", 1)
