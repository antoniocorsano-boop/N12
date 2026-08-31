#!/usr/bin/env python3
from __future__ import annotations

import cew_oa3_workbench_runtime as oa3_runtime

OA2_RUNTIME_MARKER = "CEW_OA2_RUNTIME_HUMAN_TEACHING"
OA_HUMAN_FIRST_MARKER = "CEW_OA_HUMAN_FIRST_SOURCE_PRIMARY"


def augment(rendered: str, task: str) -> str:
    """Add OA-2 human teaching and the OA human-first pilot surface.

    For the G4 pilot, source position is explicitly UNREGISTERED. In that state the
    immutable source becomes the dominant surface and the OA controls become a
    persistent operational sidebar. The browser remains only a UI cache; downstream
    OA stages require append-only governed receipts.
    """
    if OA2_RUNTIME_MARKER in rendered:
        return oa3_runtime.augment(rendered, task)

    style = '''
<style id="cew-oa2-runtime-style">
#oaTeach{border-top:1px solid var(--line);margin-top:12px;padding-top:10px}#oaTeach label{display:block;font-size:12px;font-weight:750;margin-top:7px}#oaTeach input,#oaTeach select{width:100%;border:1px solid #b9c3ca;border-radius:6px;padding:7px;margin-top:4px}.oa2-receipt{background:#edf8f1;border-left:4px solid var(--ok);padding:8px;margin-top:8px;font-size:12px}.oa2-error{background:#fff3f3;border-left:4px solid var(--danger);padding:8px;margin-top:8px;font-size:12px}.oa2-pilot-note{background:#eef5fa;border-left:4px solid var(--accent2);padding:8px;margin:8px 0;font-size:12px}.oa2-tray{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;max-height:300px;overflow:auto;padding:4px 0}.oa2-symbol{display:flex;flex-direction:column;align-items:center;gap:3px;min-height:94px;padding:6px;background:#fff}.oa2-symbol[aria-pressed="true"]{outline:3px solid var(--focus);background:#fff8df}.oa2-symbol svg{width:64px;height:52px;overflow:visible}.oa2-symbol rect{fill:none;stroke:currentColor;stroke-width:3}.oa2-symbol small{font-size:10px;color:var(--muted)}
/* Human-first override is deliberately scoped to the OA G4 pilot only. */
body.oa-human-first #workspace.workspace,body.oa-human-first.mode-source #workspace.workspace,body.oa-human-first.mode-source #workspace.workspace.inspector-open{grid-template-columns:minmax(0,1fr) minmax(340px,400px)!important;gap:0}
body.oa-human-first .technical-pane,body.oa-human-first #workspace>.inspector{display:none!important}
body.oa-human-first #oaPanel{position:relative!important;inset:auto!important;display:block!important;width:auto!important;max-height:none!important;height:100%;overflow:auto;border:0!important;border-left:1px solid var(--line)!important;border-radius:0!important;box-shadow:none!important;padding:14px;background:#fff}
body.oa-human-first .source-pane .pane-head,body.oa-human-first .technical-pane .pane-head{display:none!important}
body.oa-human-first [data-mode="SPLIT"],body.oa-human-first [data-mode="OVERLAY"],body.oa-human-first #gapReviewLink,body.oa-human-first #geometryAcceptanceLink,body.oa-human-first #oaPanelButton,body.oa-human-first label[for="oaType"]{display:none!important}
body.oa-human-first .source-pane{border-right:0;background:var(--canvas)}
body.oa-human-first #sourceViewport{inset:0;width:100%;height:100%}
.oa-human-header{border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:12px}.oa-human-kicker{font-size:11px;font-weight:850;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}.oa-human-header h2{margin:3px 0 8px;font-size:19px}.oa-human-status{display:grid;gap:5px;font-size:12px}.oa-human-status div{display:flex;justify-content:space-between;gap:12px;border-top:1px solid #edf0f2;padding-top:5px}.oa-human-status b{font-weight:800}.oa-human-ok{color:var(--ok)}.oa-human-warn{color:var(--warn)}
.oa-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px;margin:10px 0 12px}.oa-step{border:1px solid var(--line);border-radius:6px;padding:6px;font-size:11px;background:#f8fafb}.oa-step.current{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent);background:#eef5fa}.oa-step.done{border-color:#9bc1aa;background:#edf8f1}.oa-step b{display:block;font-size:10px;color:var(--muted)}
.oa-human-blocker{border-left:4px solid var(--warn);background:#fff7e8;padding:9px;margin:8px 0;font-size:12px;line-height:1.35}.oa-human-blocker strong{display:block;margin-bottom:3px}.oa-selected-card{border:2px solid var(--accent);border-radius:8px;padding:9px;margin:8px 0;background:#f6fbff}.oa-selected-card.empty{border-color:var(--line);background:#f8fafb;color:var(--muted)}.oa-selected-card b{display:block}.oa-selected-card small{display:block;margin-top:3px}.oa-primary-action{width:100%;padding:10px 12px;font-size:15px;margin-top:8px}.oa-secondary-details{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}.oa-secondary-details summary{font-size:12px;font-weight:800;cursor:pointer}
body.oa-human-first #oaPanel>h2,body.oa-human-first #oaPanel>.oa-muted,body.oa-human-first #oaPassTitle,body.oa-human-first #oaSummary,body.oa-human-first #oaPanel>h3,body.oa-human-first #oaFamilies,body.oa-human-first #oaBlockers,body.oa-human-first #oaObjects,body.oa-human-first #oaPanel>p,body.oa-human-first #oaPanel>.authority-note{display:none}
body.oa-human-first #oaTeach{border-top:0;margin-top:0;padding-top:0}body.oa-human-first #oaTeach>h3,body.oa-human-first #oaTeach>.oa-muted{display:none}body.oa-human-first #oaPilotTrayBlock{display:block!important}body.oa-human-first #oaPilotTray{max-height:250px}body.oa-human-first #oaTeachCreate{width:100%;padding:10px;font-size:15px}
body.oa-human-first #syncStatus{white-space:normal;max-width:260px}body.oa-human-first .bottom-status{font-size:12px}
@media(max-width:900px){body.oa-human-first #workspace.workspace,body.oa-human-first.mode-source #workspace.workspace{display:block!important;overflow:auto}body.oa-human-first .source-pane{height:62vh}body.oa-human-first #oaPanel{height:auto;border-left:0!important;border-top:1px solid var(--line)!important}.oa-steps{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>'''
    rendered = rendered.replace('</head>', style + '</head>', 1)

    section = '''
<section id="oaTeach" data-oa2-runtime="CEW_OA2_RUNTIME_HUMAN_TEACHING">
  <h3>Insegna al sistema</h3>
  <div class="oa-muted">Seleziona un oggetto e dichiarane esplicitamente il significato. La geometria non determina il tipo.</div>
  <div id="oaPilotTrayBlock" hidden>
    <div class="oa2-pilot-note"><b>Catalogo supporti G4.</b> I simboli rappresentano le sezioni documentate. La loro posizione nel catalogo NON è la posizione sulla tavola.</div>
    <div id="oaPilotTray" class="oa2-tray" aria-label="Supporti G4 disponibili per insegnamento"></div>
    <div id="oaPilotSelection" class="oa-muted">Nessun supporto selezionato.</div>
  </div>
  <label>Questo è un…
    <select id="oaTeachType">
      <option value="COLUMN">Pilastro</option><option value="BEAM">Trave</option><option value="BEAM_SECTION_SYMBOL">Sezione trave</option><option value="SLAB">Solaio</option><option value="FOUNDATION_BEAM">Trave di fondazione</option><option value="LONGITUDINAL_REBAR">Armatura longitudinale</option><option value="STIRRUP">Staffa</option><option value="GRID_AXIS">Asse</option><option value="DIMENSION">Quota</option><option value="CALLOUT">Richiamo</option><option value="NODE">Nodo</option><option value="TECHNICAL_TEXT">Testo tecnico</option>
    </select>
  </label>
  <label>Famiglia del progetto<input id="oaTeachFamily" type="text" placeholder="es. 40x40"></label>
  <label>Revisore<input id="oaTeachReviewer" type="text" value="HUMAN_OPERATOR"></label>
  <button id="oaTeachCreate" class="primary oa-primary-action" type="button">Conferma: questo è un…</button>
  <div id="oaTeachResult"></div>
  <div class="authority-note">Il prototipo entra nella catena OA solo dopo registrazione append-only. sessionStorage è soltanto cache UI.</div>
</section>'''

    script = '''
<script id="cew-oa2-runtime-script">
(() => {
const OA2_MARKER='CEW_OA2_RUNTIME_HUMAN_TEACHING';
const OA_HUMAN_FIRST_MARKER='CEW_OA_HUMAN_FIRST_SOURCE_PRIMARY';
const OA_PILOT_TASK='OA-N12-G4-COLUMN-PILOT';
const allowed=new Set(['COLUMN','BEAM','BEAM_SECTION_SYMBOL','SLAB','FOUNDATION_BEAM','LONGITUDINAL_REBAR','STIRRUP','GRID_AXIS','DIMENSION','CALLOUT','NODE','TECHNICAL_TEXT']);
const slug=v=>String(v||'').trim().toUpperCase().replace(/[^A-Z0-9]+/g,'_').replace(/^_+|_+$/g,'').slice(0,64);
const hex=buf=>Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('').toUpperCase();
function stepState(n){document.querySelectorAll('.oa-step').forEach(el=>{const k=Number(el.dataset.step);el.classList.toggle('done',k<n);el.classList.toggle('current',k===n)})}
function setHumanSelected(obj){const card=document.getElementById('oaHumanSelected');if(!card)return;if(!obj){card.className='oa-selected-card empty';card.innerHTML='<b>Nessun oggetto selezionato</b><small>Scegli un supporto dal catalogo.</small>';return}const p=obj.properties||{};card.className='oa-selected-card';card.innerHTML='<b>Supporto '+String(p.support_id||obj.object_id)+'</b><span>Sezione documentata: '+String(p.section_cm||'—')+'</span><small>Posizione sulla tavola: non registrata.</small>';stepState(3)}
function initHumanFirst(){
  if(TASK!==OA_PILOT_TASK)return;
  document.body.classList.add('oa-human-first');document.body.dataset.oaHumanFirst=OA_HUMAN_FIRST_MARKER;
  const panel=document.getElementById('oaPanel'),workspace=document.getElementById('workspace');if(panel&&workspace&&panel.parentElement!==workspace)workspace.appendChild(panel);panel?.classList.add('open');
  const header=document.createElement('div');header.id='oaHumanHeader';header.className='oa-human-header';header.innerHTML='<div class="oa-human-kicker">Acquisizione oggetti · Pilot G4 / TAV-05S</div><h2>Pilastri: insegna un esempio al sistema</h2><div class="oa-human-status"><div><span>Fonte</span><b class="oa-human-ok">Verificata</b></div><div><span>Posizione sulla tavola</span><b class="oa-human-warn">Non registrata</b></div><div><span>Passo corrente</span><b id="oaHumanCurrentStep">Scegli un oggetto</b></div></div><div class="oa-steps" aria-label="Percorso di lavoro"><div class="oa-step done" data-step="1"><b>1</b>Leggi la fonte</div><div class="oa-step current" data-step="2"><b>2</b>Scegli un oggetto</div><div class="oa-step" data-step="3"><b>3</b>Questo è un…</div><div class="oa-step" data-step="4"><b>4</b>Famiglia</div><div class="oa-step" data-step="5"><b>5</b>Trova simili</div><div class="oa-step" data-step="6"><b>6</b>Rivedi candidati</div></div><div class="oa-human-blocker"><strong>Posizione dei supporti sulla tavola non ancora registrata.</strong>Puoi insegnare tipo e famiglia e cercare simili per sezione/orientamento. Non puoi sincronizzare spazialmente né accettare identità strutturali.</div><div id="oaHumanSelected" class="oa-selected-card empty"><b>Nessun oggetto selezionato</b><small>Scegli un supporto dal catalogo.</small></div>';
  panel?.insertBefore(header,panel.firstChild);
  const teach=document.getElementById('oaTeach');if(teach&&header.nextSibling!==teach)header.insertAdjacentElement('afterend',teach);
  const type=document.getElementById('oaType');if(type)type.value='COLUMN';
  const reg=document.getElementById('registrationState');if(reg)reg.textContent='posizione sulla tavola non registrata';
  const sync=document.getElementById('syncStatus');if(sync)sync.textContent='Sincronizzazione spaziale non disponibile';
  if(typeof requestMode==='function')requestMode('SOURCE');
}
function initPilotTray(){
  if(TASK!==OA_PILOT_TASK)return;
  const block=document.getElementById('oaPilotTrayBlock'),host=document.getElementById('oaPilotTray');block.hidden=false;
  const candidates=(scene?.objects||[]).filter(o=>o.object_family==='TechnicalObjectCandidate'&&o.properties?.storey_id==='G4'&&o.properties?.source_sheet==='TAV-05S');
  host.innerHTML=candidates.map(o=>{const p=o.properties||{},sx=Number(p.section_x_cm||1),sy=Number(p.section_y_cm||1),scale=Math.min(44/Math.max(sx,1),34/Math.max(sy,1)),w=Math.max(7,sx*scale),h=Math.max(7,sy*scale),x=(64-w)/2,y=(48-h)/2;return '<button type="button" class="oa2-symbol" data-oa-object="'+o.object_id+'" aria-pressed="false"><svg viewBox="0 0 64 48" aria-hidden="true"><rect x="'+x.toFixed(2)+'" y="'+y.toFixed(2)+'" width="'+w.toFixed(2)+'" height="'+h.toFixed(2)+'"></rect></svg><b>'+p.support_id+'</b><small>'+p.section_cm+'</small></button>'}).join('');
  host.querySelectorAll('[data-oa-object]').forEach(btn=>btn.onclick=()=>{const obj=candidates.find(o=>o.object_id===btn.dataset.oaObject);if(!obj)return;host.querySelectorAll('[data-oa-object]').forEach(b=>b.setAttribute('aria-pressed','false'));btn.setAttribute('aria-pressed','true');if(typeof selectObject==='function')selectObject(obj);else selected=obj;if(typeof requestMode==='function')requestMode('SOURCE');document.getElementById('oaTeachFamily').value=obj.properties?.section_cm||'';document.getElementById('oaPilotSelection').textContent='Supporto '+obj.properties.support_id+' · sezione '+obj.properties.section_cm+' · posizione sorgente non registrata.';setHumanSelected(obj);document.getElementById('oaHumanCurrentStep').textContent='Dichiara tipo e famiglia';});
}
async function persistOA2(proposal,reviewer){const response=await fetch('/api/workbench/object-acquisition/receipt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:TASK,stage:'OA2_PROTOTYPE',revision:proposal.revision,reviewer,payload:proposal,parent_decision_id:null})});const body=await response.json();if(!response.ok)throw new Error(body.reason||body.state||'OA2_GOVERNED_PERSISTENCE_FAILED');proposal.governed_receipt_id=body.runtime_receipt_id;proposal.governed_receipt_fingerprint=body.receipt_fingerprint;proposal.governed_audit_backend=body.audit_backend;proposal.governed_persistence_state=body.state;return proposal}
async function createProposal(){
  const result=document.getElementById('oaTeachResult'),anchor=(typeof selected!=='undefined'&&selected)?selected:null,objectType=document.getElementById('oaTeachType').value,familyLabel=document.getElementById('oaTeachFamily').value.trim(),reviewer=document.getElementById('oaTeachReviewer').value.trim();
  if(!anchor){result.innerHTML='<div class="oa2-error">Scegli prima un supporto dal catalogo.</div>';return}if(!allowed.has(objectType)||!familyLabel||!reviewer){result.innerHTML='<div class="oa2-error">Tipo, famiglia e revisore sono obbligatori.</div>';return}
  const source=scene?.source||{},evidence={source_version_id:source.source_version_id,page_id:source.page_id,evidence_region_id:source.evidence_region_id,source_sha256:source.source_sha256};if(Object.values(evidence).some(v=>!v)){result.innerHTML='<div class="oa2-error">Provenienza incompleta: la proposta è bloccata.</div>';return}
  const familyId=objectType+'_'+slug(familyLabel),revision=source.build_revision||scene?.build_revision||scene?.revision||scene?.scene_revision||'RUNTIME_SCENE',seed=JSON.stringify({anchor:anchor.object_id,type:objectType,family:familyId,source:evidence,revision}),digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(seed));
  const proposal={state:'HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE',prototype_id:'OAP-'+hex(digest).slice(0,16),object_type:objectType,family_id:familyId,family_label:familyLabel,anchor_object_id:anchor.object_id,anchor_source_position_state:anchor.properties?.source_position_state||null,source_evidence:evidence,human_decision:{decision:'THIS_IS_A',reviewer,explicit_object_type:objectType,family_label:familyLabel},revision,geometry_used_to_infer_type:false,find_similar_authorized:false,structural_identity_created:false,canonical_write_authorized:false,project_material_ready:false,engineering_authority_effect:'NONE',next_gate:'OA3_DETERMINISTIC_SIMILARITY'};
  result.innerHTML='<div class="oa2-receipt">Registrazione append-only del prototipo…</div>';try{await persistOA2(proposal,reviewer)}catch(error){result.innerHTML='<div class="oa2-error"><b>Prototipo non registrato.</b><br>'+String(error.message||error)+'<br>La ricerca dei simili resta bloccata.</div>';return}
  sessionStorage.setItem('cew-oa2:'+TASK+':'+proposal.prototype_id,JSON.stringify(proposal));result.innerHTML='<div class="oa2-receipt"><b>Prototipo registrato</b><br>'+proposal.object_type+' · '+proposal.family_label+'<br>Ora puoi cercare i simili.</div>';if(TASK===OA_PILOT_TASK){stepState(5);document.getElementById('oaHumanCurrentStep').textContent='Trova oggetti simili'}window.dispatchEvent(new CustomEvent('cew:oa2-prototype-persisted',{detail:{task:TASK,prototype_id:proposal.prototype_id,receipt_id:proposal.governed_receipt_id}}));
}
function initOA2(){const panel=document.getElementById('oaPanel');if(!panel||document.getElementById('oaTeach'))return;panel.insertAdjacentHTML('beforeend',OA2_SECTION);document.getElementById('oaTeachCreate').onclick=createProposal;initHumanFirst();initPilotTray()}
const OA2_SECTION=''' + repr(section) + ''';
let tries=0;const timer=setInterval(()=>{tries++;if(document.getElementById('oaPanel')&&typeof scene!=='undefined'&&scene){clearInterval(timer);initOA2()}else if(tries>80)clearInterval(timer)},100);
})();
</script>'''
    rendered = rendered.replace('</body>', script + '</body>', 1)
    return oa3_runtime.augment(rendered, task)