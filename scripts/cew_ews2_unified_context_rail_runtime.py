#!/usr/bin/env python3
from __future__ import annotations

EWS2_RUNTIME_MARKER = "CEW_EWS2_UNIFIED_FOCUSED_CONTEXT_RAIL"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def augment(rendered: str, task: str) -> str:
    """Orchestrate existing OA controls as one task-focused context rail.

    EWS-2 owns presentation only. OA-2/OA-3/OA-4/OA-5/OA-G5 remain the
    owners of teaching, similarity, review and governed persistence semantics.
    """
    if EWS2_RUNTIME_MARKER in rendered or task != OA_PILOT_TASK:
        return rendered

    style = r'''
<style id="cew-ews2-unified-context-rail-style">
@media (min-width:901px){
  body.ews2-focused-rail #oaPanel{padding:0!important;overflow:hidden!important;display:flex!important;flex-direction:column!important}
  #ews2RailHeader{flex:0 0 auto;position:relative;z-index:4;background:#fff;border-bottom:1px solid var(--line);padding:10px 12px}
  .ews2-kicker{font-size:10px;font-weight:850;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
  #ews2RailHeader h2{font-size:16px;margin:2px 0 7px}
  .ews2-stage-nav{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:3px}
  .ews2-stage{min-width:0;padding:6px 3px;font-size:10px;border-radius:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .ews2-stage[aria-current="step"]{background:var(--accent);color:#fff;border-color:var(--accent)}
  .ews2-stage[disabled]{opacity:.38}
  #ews2PhaseMessage{font-size:11px;color:var(--muted);margin-top:7px;line-height:1.3}
  #ews2RailBody{flex:1 1 auto;min-height:0;overflow-y:auto;overflow-x:hidden;padding:10px 12px;overscroll-behavior:contain;scrollbar-gutter:stable}
  body.ews2-focused-rail #oaPanel>#oaHumanHeader,
  body.ews2-focused-rail #oaPanel>#oaTeach,
  body.ews2-focused-rail #oaPanel>#oaSimilar,
  body.ews2-focused-rail #oaPanel>#oaClusterReview,
  body.ews2-focused-rail #oaPanel>#oaStructuralResolver,
  body.ews2-focused-rail #oaPanel>#oaG5Review{display:none!important}
  body.ews2-mode-acquire #ews2RailBody>#oaTeach{display:block!important}
  body.ews2-mode-find #ews2RailBody>#oaSimilar{display:block!important}
  body.ews2-mode-review #ews2RailBody>#oaSimilar{display:block!important}
  body.ews2-mode-resolve #ews2RailBody>#oaStructuralResolver{display:block!important}
  body.ews2-mode-validate #ews2RailBody>#oaG5Review{display:block!important}
  body.ews2-mode-review #oaSimilar>h3,
  body.ews2-mode-review #oaSimilarReadiness,
  body.ews2-mode-review #oaSimilar>.oa3-criteria,
  body.ews2-mode-review #oaFindSimilar,
  body.ews2-mode-review #oaSimilar>.authority-note{display:none!important}
  body.ews2-focused-rail #oaTeach,
  body.ews2-focused-rail #oaSimilar,
  body.ews2-focused-rail #oaStructuralResolver,
  body.ews2-focused-rail #oaG5Review{border-top:0!important;margin-top:0!important;padding-top:0!important}
  body.ews2-mode-review .ews4-set{max-height:190px;overflow:auto;overscroll-behavior:contain;padding-right:2px}
  body.ews2-mode-review .ews4-reasons{max-height:72px}
  body.ews2-mode-review .ews4-active{margin-top:6px}
  #ews2Advance{display:none;width:100%;margin-top:10px;padding:9px 10px}
  body.ews2-mode-review.ews2-can-resolve #ews2Advance{display:block}
  #ews2BackToReview{display:none;width:100%;margin-bottom:9px}
  body.ews2-mode-resolve #ews2BackToReview,body.ews2-mode-validate #ews2BackToReview{display:block}
  #ews2ValidateAdvance{display:none;width:100%;margin-top:10px;padding:9px 10px}
  body.ews2-mode-resolve.ews2-can-validate #ews2ValidateAdvance{display:block}
  .ews2-eligibility{background:#f7f9fa;border:1px solid var(--line);border-radius:6px;padding:7px;font-size:11px;margin-top:8px}
}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    script = f'''
<script id="cew-ews2-unified-context-rail-script" data-ews2-runtime="{EWS2_RUNTIME_MARKER}">
(() => {{
const MARKER={EWS2_RUNTIME_MARKER!r};
const TASK_ID={task!r};
if(TASK_ID!={OA_PILOT_TASK!r}) return;
const MODES=['ACQUIRE','FIND_SIMILAR','REVIEW_SET','RESOLVE_IDENTITY','VALIDATE_IDENTITY'];
let current=null;
function readJson(key){{try{{return JSON.parse(sessionStorage.getItem(key)||'null')}}catch(e){{return null}}}}
function latestPrototype(){{const prefix='cew-oa2:'+TASK_ID+':';let hit=null;for(let i=0;i<sessionStorage.length;i++){{const k=sessionStorage.key(i);if(!k||!k.startsWith(prefix))continue;const row=readJson(k);if(row?.governed_receipt_id)hit=row}}return hit}}
function state(){{
 const prototype=latestPrototype();
 const similarity=readJson('cew-oa3:'+TASK_ID+':latest');
 const review=readJson('cew-oa4:'+TASK_ID+':latest');
 const identity=readJson('cew-oa5:'+TASK_ID+':latest');
 const admissible=!!review?.governed_receipt_id && (review.candidate_decisions||[]).some(d=>['CONFIRM_AS_FAMILY_CANDIDATE','MOVE_TO_OTHER_FAMILY'].includes(d.decision)&&d.family_membership_proposal_created===true);
 const reviewReady=similarity?.state==='DETERMINISTIC_SIMILARITY_CANDIDATES';
 const validateReady=identity?.governed_receipt_id && identity?.candidate_state==='READY_FOR_EXPLICIT_IDENTITY_REVIEW';
 return {{prototype:!!prototype,similarity:reviewReady,review,canResolve:admissible,identity,canValidate:!!validateReady}};
}}
function allowed(mode,s){{return mode==='ACQUIRE'||(mode==='FIND_SIMILAR'&&s.prototype)||(mode==='REVIEW_SET'&&s.similarity)||(mode==='RESOLVE_IDENTITY'&&s.canResolve)||(mode==='VALIDATE_IDENTITY'&&s.canValidate)}}
function recommended(s){{if(s.similarity)return 'REVIEW_SET';if(s.prototype)return 'FIND_SIMILAR';return 'ACQUIRE'}}
function label(mode){{return {{ACQUIRE:'Esempio',FIND_SIMILAR:'Simili',REVIEW_SET:'Rivedi',RESOLVE_IDENTITY:'Identità',VALIDATE_IDENTITY:'Valida'}}[mode]}}
function message(mode,s){{
 if(mode==='ACQUIRE')return s.prototype?'Il prototipo è già governato. Puoi consultare o insegnare un nuovo esempio.':'Seleziona un supporto e insegna esplicitamente tipo e famiglia.';
 if(mode==='FIND_SIMILAR')return 'Avvia la ricerca deterministica dei simili. Nessun risultato viene accettato automaticamente.';
 if(mode==='REVIEW_SET')return s.canResolve?'Rivedi i candidati. L’identità strutturale è disponibile solo tramite passaggio esplicito.':'Rivedi un candidato alla volta. Serve almeno una conferma OA-4 governata per passare all’identità.';
 if(mode==='RESOLVE_IDENTITY')return s.canValidate?'Candidato identità review-ready disponibile. La validazione resta un passaggio umano separato.':'Costruisci un candidato identità usando relazioni ed evidenze esplicite.';
 return 'Decidi esplicitamente sul candidato identità. Anche ACCETTA non abilita scrittura canonica.';
}}
function moveSections(){{
 const panel=document.getElementById('oaPanel');if(!panel)return null;
 let head=document.getElementById('ews2RailHeader'),body=document.getElementById('ews2RailBody');
 if(!head){{head=document.createElement('header');head.id='ews2RailHeader';head.innerHTML='<div class="ews2-kicker">Work mode · Object Acquisition</div><h2 id="ews2ModeTitle">Lavoro corrente</h2><nav class="ews2-stage-nav" aria-label="Fasi operative"></nav><div id="ews2PhaseMessage"></div>';panel.insertBefore(head,panel.firstChild)}}
 if(!body){{body=document.createElement('div');body.id='ews2RailBody';head.insertAdjacentElement('afterend',body)}}
 ['oaTeach','oaSimilar','oaClusterReview','oaStructuralResolver','oaG5Review'].forEach(id=>{{const el=document.getElementById(id);if(el&&el.parentElement!==body)body.appendChild(el)}});
 if(!document.getElementById('ews2BackToReview')){{const b=document.createElement('button');b.id='ews2BackToReview';b.type='button';b.textContent='← Torna alla revisione candidati';b.onclick=()=>setMode('REVIEW_SET',true);body.insertBefore(b,body.firstChild)}}
 if(!document.getElementById('ews2Advance')){{const b=document.createElement('button');b.id='ews2Advance';b.className='primary';b.type='button';b.textContent='Passa a identità strutturale →';b.onclick=()=>setMode('RESOLVE_IDENTITY',true);body.appendChild(b)}}
 if(!document.getElementById('ews2ValidateAdvance')){{const b=document.createElement('button');b.id='ews2ValidateAdvance';b.className='primary';b.type='button';b.textContent='Passa a revisione identità →';b.onclick=()=>setMode('VALIDATE_IDENTITY',true);body.appendChild(b)}}
 return panel;
}}
function renderNav(s){{const nav=document.querySelector('.ews2-stage-nav');if(!nav)return;nav.innerHTML=MODES.map(m=>`<button type="button" class="ews2-stage" data-ews2-mode="${{m}}" aria-current="${{m===current?'step':'false'}}" ${{allowed(m,s)?'':'disabled'}} title="${{label(m)}}">${{label(m)}}</button>`).join('');nav.querySelectorAll('[data-ews2-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.ews2Mode,true))}}
function setMode(mode,userInitiated=false){{
 const s=state();if(!allowed(mode,s))mode=recommended(s);current=mode;
 document.body.classList.remove('ews2-mode-acquire','ews2-mode-find','ews2-mode-review','ews2-mode-resolve','ews2-mode-validate','ews2-can-resolve','ews2-can-validate');
 const cls={{ACQUIRE:'ews2-mode-acquire',FIND_SIMILAR:'ews2-mode-find',REVIEW_SET:'ews2-mode-review',RESOLVE_IDENTITY:'ews2-mode-resolve',VALIDATE_IDENTITY:'ews2-mode-validate'}}[mode];document.body.classList.add(cls);if(s.canResolve)document.body.classList.add('ews2-can-resolve');if(s.canValidate)document.body.classList.add('ews2-can-validate');
 const title=document.getElementById('ews2ModeTitle'),msg=document.getElementById('ews2PhaseMessage');if(title)title.textContent=label(mode);if(msg)msg.textContent=message(mode,s);renderNav(s);
 const body=document.getElementById('ews2RailBody');if(body)body.scrollTop=0;
 window.__CEW_EWS2_RAIL__={{state:'FOCUSED_CONTEXT_RAIL_ACTIVE',mode,task:TASK_ID,user_initiated:userInitiated,canonical_write_authorized:false,engineering_authority_effect:'NONE'}};
 window.dispatchEvent(new CustomEvent('cew:ews2-mode-change',{{detail:window.__CEW_EWS2_RAIL__}}));
}}
function refresh(){{const s=state();document.body.classList.toggle('ews2-can-resolve',s.canResolve);document.body.classList.toggle('ews2-can-validate',s.canValidate);if(!current||!allowed(current,s))setMode(recommended(s));else{{renderNav(s);const msg=document.getElementById('ews2PhaseMessage');if(msg)msg.textContent=message(current,s)}}}}
function init(){{const panel=moveSections();if(!panel)return;document.body.classList.add('ews2-focused-rail');document.body.dataset.ews2ContextRail=MARKER;panel.dataset.ews2PresentationOwner='UNIFIED_FOCUSED_CONTEXT_RAIL';setMode(recommended(state()));['cew:oa2-prototype-persisted','cew:oa3-similarity-run','cew:ews4-candidate-reviewed','cew:enterprise-governed-resume'].forEach(e=>window.addEventListener(e,()=>setTimeout(refresh,0)));setInterval(refresh,700)}}
let tries=0;const timer=setInterval(()=>{{tries++;if(document.getElementById('oaPanel')&&document.getElementById('oaTeach')&&document.getElementById('oaSimilar')&&document.getElementById('oaStructuralResolver')&&document.getElementById('oaG5Review')){{clearInterval(timer);init()}}else if(tries>140)clearInterval(timer)}},80);
}})();
</script>'''
    return rendered.replace("</body>", script + "</body>", 1)
