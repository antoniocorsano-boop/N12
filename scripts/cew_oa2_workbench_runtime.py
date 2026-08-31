#!/usr/bin/env python3
from __future__ import annotations

import cew_oa3_workbench_runtime as oa3_runtime

OA2_RUNTIME_MARKER = "CEW_OA2_RUNTIME_HUMAN_TEACHING"


def augment(rendered: str, task: str) -> str:
    """Add OA-2 human teaching, then chain OA-3 on the same Workbench panel.

    The browser object is only a UI cache. A taught prototype becomes usable by
    downstream OA stages only after the governed append-only receipt is stored.
    """
    if OA2_RUNTIME_MARKER in rendered:
        return oa3_runtime.augment(rendered, task)

    style = '''
<style id="cew-oa2-runtime-style">
#oaTeach{border-top:1px solid var(--line);margin-top:12px;padding-top:10px}#oaTeach label{display:block;font-size:12px;font-weight:750;margin-top:7px}#oaTeach input,#oaTeach select{width:100%;border:1px solid #b9c3ca;border-radius:6px;padding:7px;margin-top:4px}.oa2-receipt{background:#edf8f1;border-left:4px solid var(--ok);padding:8px;margin-top:8px;font-size:12px}.oa2-error{background:#fff3f3;border-left:4px solid var(--danger);padding:8px;margin-top:8px;font-size:12px}.oa2-pilot-note{background:#eef5fa;border-left:4px solid var(--accent2);padding:8px;margin:8px 0;font-size:12px}.oa2-tray{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;max-height:300px;overflow:auto;padding:4px 0}.oa2-symbol{display:flex;flex-direction:column;align-items:center;gap:3px;min-height:94px;padding:6px;background:#fff}.oa2-symbol[aria-pressed="true"]{outline:3px solid var(--focus);background:#fff8df}.oa2-symbol svg{width:64px;height:52px;overflow:visible}.oa2-symbol rect{fill:none;stroke:currentColor;stroke-width:3}.oa2-symbol small{font-size:10px;color:var(--muted)}
</style>'''
    rendered = rendered.replace('</head>', style + '</head>', 1)

    section = '''
<section id="oaTeach" data-oa2-runtime="CEW_OA2_RUNTIME_HUMAN_TEACHING">
  <h3>Insegna al sistema</h3>
  <div class="oa-muted">Seleziona un oggetto nella vista tecnica e dichiarane esplicitamente il significato. La geometria non determina il tipo.</div>
  <div id="oaPilotTrayBlock" hidden>
    <div class="oa2-pilot-note"><b>Pilot G4 · TAV-05S.</b> I simboli sotto rappresentano le sezioni documentate nel registro supporti. La loro posizione nel tray NON è la posizione sulla tavola: <code>source_position_state=UNREGISTERED</code>.</div>
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
  <button id="oaTeachCreate" class="primary" type="button">Questo è un…</button>
  <div id="oaTeachResult"></div>
  <div class="authority-note">Il prototipo entra nella catena OA solo dopo registrazione append-only. sessionStorage è soltanto cache UI.</div>
</section>'''

    script = '''
<script id="cew-oa2-runtime-script">
(() => {
const OA2_MARKER='CEW_OA2_RUNTIME_HUMAN_TEACHING';
const OA_PILOT_TASK='OA-N12-G4-COLUMN-PILOT';
const allowed=new Set(['COLUMN','BEAM','BEAM_SECTION_SYMBOL','SLAB','FOUNDATION_BEAM','LONGITUDINAL_REBAR','STIRRUP','GRID_AXIS','DIMENSION','CALLOUT','NODE','TECHNICAL_TEXT']);
const slug=v=>String(v||'').trim().toUpperCase().replace(/[^A-Z0-9]+/g,'_').replace(/^_+|_+$/g,'').slice(0,64);
const hex=buf=>Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('').toUpperCase();
function initPilotTray(){
  if(TASK!==OA_PILOT_TASK)return;
  const block=document.getElementById('oaPilotTrayBlock'),host=document.getElementById('oaPilotTray');
  block.hidden=false;
  const candidates=(scene?.objects||[]).filter(o=>o.object_family==='TechnicalObjectCandidate'&&o.properties?.storey_id==='G4'&&o.properties?.source_sheet==='TAV-05S');
  host.innerHTML=candidates.map(o=>{const p=o.properties||{},sx=Number(p.section_x_cm||1),sy=Number(p.section_y_cm||1),scale=Math.min(44/Math.max(sx,1),34/Math.max(sy,1)),w=Math.max(7,sx*scale),h=Math.max(7,sy*scale),x=(64-w)/2,y=(48-h)/2;return '<button type="button" class="oa2-symbol" data-oa-object="'+o.object_id+'" aria-pressed="false"><svg viewBox="0 0 64 48" aria-hidden="true"><rect x="'+x.toFixed(2)+'" y="'+y.toFixed(2)+'" width="'+w.toFixed(2)+'" height="'+h.toFixed(2)+'"></rect></svg><b>'+p.support_id+'</b><small>'+p.section_cm+'</small></button>'}).join('');
  host.querySelectorAll('[data-oa-object]').forEach(btn=>btn.onclick=()=>{const obj=candidates.find(o=>o.object_id===btn.dataset.oaObject);if(!obj)return;host.querySelectorAll('[data-oa-object]').forEach(b=>b.setAttribute('aria-pressed','false'));btn.setAttribute('aria-pressed','true');if(typeof selectObject==='function')selectObject(obj);else selected=obj;document.getElementById('oaTeachFamily').value=obj.properties?.section_cm||'';document.getElementById('oaPilotSelection').textContent='Supporto '+obj.properties.support_id+' · sezione documentata '+obj.properties.section_cm+' · posizione sorgente NON registrata.';});
}
async function persistOA2(proposal,reviewer){
  const response=await fetch('/api/workbench/object-acquisition/receipt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:TASK,stage:'OA2_PROTOTYPE',revision:proposal.revision,reviewer,payload:proposal,parent_decision_id:null})});
  const body=await response.json();
  if(!response.ok)throw new Error(body.reason||body.state||'OA2_GOVERNED_PERSISTENCE_FAILED');
  proposal.governed_receipt_id=body.runtime_receipt_id;
  proposal.governed_receipt_fingerprint=body.receipt_fingerprint;
  proposal.governed_audit_backend=body.audit_backend;
  proposal.governed_persistence_state=body.state;
  return proposal;
}
async function createProposal(){
  const result=document.getElementById('oaTeachResult');
  const anchor=(typeof selected!=='undefined'&&selected)?selected:null;
  const objectType=document.getElementById('oaTeachType').value;
  const familyLabel=document.getElementById('oaTeachFamily').value.trim();
  const reviewer=document.getElementById('oaTeachReviewer').value.trim();
  if(!anchor){result.innerHTML='<div class="oa2-error">Seleziona prima un oggetto nella vista tecnica o nel tray.</div>';return}
  if(!allowed.has(objectType)||!familyLabel||!reviewer){result.innerHTML='<div class="oa2-error">Tipo, famiglia e revisore sono obbligatori.</div>';return}
  const source=scene?.source||{};
  const evidence={source_version_id:source.source_version_id,page_id:source.page_id,evidence_region_id:source.evidence_region_id,source_sha256:source.source_sha256};
  if(Object.values(evidence).some(v=>!v)){result.innerHTML='<div class="oa2-error">Provenienza incompleta: la proposta è bloccata.</div>';return}
  const familyId=objectType+'_'+slug(familyLabel);
  const revision=source.build_revision||scene?.build_revision||scene?.revision||scene?.scene_revision||'RUNTIME_SCENE';
  const seed=JSON.stringify({anchor:anchor.object_id,type:objectType,family:familyId,source:evidence,revision});
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(seed));
  const proposal={state:'HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE',prototype_id:'OAP-'+hex(digest).slice(0,16),object_type:objectType,family_id:familyId,family_label:familyLabel,anchor_object_id:anchor.object_id,anchor_source_position_state:anchor.properties?.source_position_state||null,source_evidence:evidence,human_decision:{decision:'THIS_IS_A',reviewer,explicit_object_type:objectType,family_label:familyLabel},revision,geometry_used_to_infer_type:false,find_similar_authorized:false,structural_identity_created:false,canonical_write_authorized:false,project_material_ready:false,engineering_authority_effect:'NONE',next_gate:'OA3_DETERMINISTIC_SIMILARITY'};
  result.innerHTML='<div class="oa2-receipt">Registrazione append-only del prototipo…</div>';
  try{
    await persistOA2(proposal,reviewer);
  }catch(error){result.innerHTML='<div class="oa2-error"><b>Prototipo non registrato.</b><br>'+String(error.message||error)+'<br>La catena downstream resta bloccata.</div>';return}
  const key='cew-oa2:'+TASK+':'+proposal.prototype_id;sessionStorage.setItem(key,JSON.stringify(proposal));
  result.innerHTML='<div class="oa2-receipt"><b>Prototipo registrato append-only</b><br>'+proposal.prototype_id+'<br>'+proposal.object_type+' · '+proposal.family_label+'<br>Receipt: '+proposal.governed_receipt_id+'<br>Scrittura canonica: false</div>';
}
function initOA2(){const panel=document.getElementById('oaPanel');if(!panel||document.getElementById('oaTeach'))return;panel.insertAdjacentHTML('beforeend',OA2_SECTION);document.getElementById('oaTeachCreate').onclick=createProposal;initPilotTray();}
const OA2_SECTION=''' + repr(section) + ''';
let tries=0;const timer=setInterval(()=>{tries++;if(document.getElementById('oaPanel')&&typeof scene!=='undefined'&&scene){clearInterval(timer);initOA2()}else if(tries>80)clearInterval(timer)},100);
})();
</script>'''
    rendered = rendered.replace('</body>', script + '</body>', 1)
    return oa3_runtime.augment(rendered, task)
