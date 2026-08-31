#!/usr/bin/env python3
from __future__ import annotations

OAG5_RUNTIME_MARKER = "CEW_OAG5_RUNTIME_EXPLICIT_IDENTITY_REVIEW"


def augment(rendered: str, task: str) -> str:
    """Add explicit human OA-G5 identity review to the shared Workbench.

    The action requires a persisted OA-5 review-ready candidate and persists the
    human decision append-only. Even ACCEPT does not enable canonical writes or
    release OA-6 project material.
    """
    if OAG5_RUNTIME_MARKER in rendered:
        return rendered

    style = '''
<style id="cew-oag5-runtime-style">
#oaG5Review{border-top:1px solid var(--line);margin-top:12px;padding-top:10px}#oaG5Review select,#oaG5Review input{width:100%;border:1px solid #b9c3ca;border-radius:6px;padding:6px;margin-top:4px}.oag5-ready{background:#edf8f1;border-left:4px solid var(--ok);padding:8px;margin-top:8px}.oag5-block{background:#fff7e8;border-left:4px solid var(--warn);padding:8px;margin-top:8px}.oag5-reject{background:#fff3f3;border-left:4px solid var(--danger);padding:8px;margin-top:8px}.oag5-attest{display:flex;gap:8px;align-items:flex-start;margin-top:8px;font-size:12px}.oag5-attest input{width:auto;margin-top:2px}
</style>'''
    rendered = rendered.replace('</head>', style + '</head>', 1)

    section = '''
<section id="oaG5Review" data-oag5-runtime="CEW_OAG5_RUNTIME_EXPLICIT_IDENTITY_REVIEW">
  <h3>OA-G5 · Revisione identità</h3>
  <div class="oa-muted">Questa è una decisione umana esplicita sull'identità strutturale candidata. Nessuna decisione viene precompilata o inferita.</div>
  <button id="oaG5Load" type="button">Carica candidato identità</button>
  <div id="oaG5Candidate"></div>
  <label>Decisione<select id="oaG5Decision"><option value="">— scegli esplicitamente —</option><option value="ACCEPT_STRUCTURAL_IDENTITY">ACCETTA IDENTITÀ</option><option value="REJECT_STRUCTURAL_IDENTITY">RIFIUTA IDENTITÀ</option><option value="DEFER_NEEDS_MORE_EVIDENCE">RINVIA — SERVE ALTRA EVIDENZA</option></select></label>
  <label>Revisore<input id="oaG5Reviewer" type="text" value="HUMAN_OPERATOR"></label>
  <label class="oag5-attest"><input id="oaG5Attestation" type="checkbox"><span>Confermo che la decisione è umana, riferita al candidato e alle relazioni mostrate. Questa attestazione è obbligatoria per ACCETTA.</span></label>
  <button id="oaG5Save" class="primary" type="button">Registra decisione identità</button>
  <div id="oaG5Result"></div>
  <div class="authority-note">Anche ACCETTA non abilita scrittura canonica e non rende pronto il materiale progettuale. OA-6 resta un gate separato.</div>
</section>'''

    script = r'''
<script id="cew-oag5-runtime-script">
(() => {
const OAG5_MARKER='CEW_OAG5_RUNTIME_EXPLICIT_IDENTITY_REVIEW';
function latestOA5(){try{return JSON.parse(sessionStorage.getItem('cew-oa5:'+TASK+':latest')||'null')}catch(e){return null}}
function loadCandidate(){const host=document.getElementById('oaG5Candidate'),c=latestOA5();if(!c?.governed_receipt_id){host.innerHTML='<div class="oag5-block">Manca un candidato OA-5 persistito nel ledger governato.</div>';return}if(c.candidate_state!=='READY_FOR_EXPLICIT_IDENTITY_REVIEW'){host.innerHTML='<div class="oag5-block"><b>'+c.candidate_state+'</b><br>Il candidato non è ammissibile alla revisione OA-G5.</div>';return}host.innerHTML='<div class="oag5-ready"><b>'+c.identity_candidate_id+'</b><br>Famiglia: '+c.family_id+'<br>Relazioni di supporto: '+c.supporting_relationship_count+'<br>Receipt OA-5: '+c.governed_receipt_id+'<br>Identità accettata: false</div>'}
async function persistDecision(payload,candidate,reviewer){const response=await fetch('/api/workbench/object-acquisition/receipt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:TASK,stage:'OA_G5_IDENTITY_DECISION',revision:candidate.revision,reviewer,payload,parent_decision_id:candidate.governed_receipt_id})});const body=await response.json();if(!response.ok)throw new Error(body.reason||body.state||'OAG5_GOVERNED_PERSISTENCE_FAILED');payload.governed_receipt_id=body.runtime_receipt_id;payload.governed_receipt_fingerprint=body.receipt_fingerprint;payload.governed_audit_backend=body.audit_backend;payload.governed_persistence_state=body.state;return payload}
async function saveDecision(){const host=document.getElementById('oaG5Result'),candidate=latestOA5(),decision=document.getElementById('oaG5Decision').value,reviewer=document.getElementById('oaG5Reviewer').value.trim(),attested=document.getElementById('oaG5Attestation').checked;if(!candidate?.governed_receipt_id||candidate.candidate_state!=='READY_FOR_EXPLICIT_IDENTITY_REVIEW'){host.innerHTML='<div class="oag5-block">Carica prima un candidato OA-5 review-ready e persistito.</div>';return}if(!decision){host.innerHTML='<div class="oag5-block">Scegli esplicitamente una decisione.</div>';return}if(!reviewer){host.innerHTML='<div class="oag5-block">Indica il revisore.</div>';return}if(decision==='ACCEPT_STRUCTURAL_IDENTITY'&&!attested){host.innerHTML='<div class="oag5-block">Per ACCETTA è obbligatoria l’attestazione umana.</div>';return}const payload={state:'EXPLICIT_STRUCTURAL_IDENTITY_REVIEW',decision,human_attestation:attested,identity_candidate_id:candidate.identity_candidate_id,identity_candidate_receipt_fingerprint:candidate.governed_receipt_fingerprint,source_object_id:candidate.source_object_id,family_id:candidate.family_id,source_evidence:candidate.source_evidence,relationship_evidence:candidate.relationship_evidence,accepted_structural_identity:decision==='ACCEPT_STRUCTURAL_IDENTITY',canonical_write_authorized:false,project_material_ready:false,project_material_promotion_authorized:false,engineering_authority_effect:'IDENTITY_REVIEW_ONLY',next_gate:'OA6_PROJECT_MATERIAL_GATE_REMAINS_SEPARATE'};host.innerHTML='<div class="oag5-block">Registrazione append-only della decisione…</div>';try{await persistDecision(payload,candidate,reviewer)}catch(error){host.innerHTML='<div class="oag5-reject"><b>Decisione non registrata.</b><br>'+String(error.message||error)+'</div>';return}sessionStorage.setItem('cew-oag5:'+TASK+':latest',JSON.stringify(payload));const cls=decision==='ACCEPT_STRUCTURAL_IDENTITY'?'oag5-ready':decision==='REJECT_STRUCTURAL_IDENTITY'?'oag5-reject':'oag5-block';host.innerHTML='<div class="'+cls+'"><b>'+decision+'</b><br>Receipt: '+payload.governed_receipt_id+'<br>Identità accettata: '+String(payload.accepted_structural_identity)+'<br>Scrittura canonica: false · Materiale progettuale pronto: false</div>'}
function initOAG5(){const oa5=document.getElementById('oaStructuralResolver'),panel=document.getElementById('oaPanel');if(!panel||document.getElementById('oaG5Review'))return;(oa5||panel).insertAdjacentHTML('afterend',OAG5_SECTION);document.getElementById('oaG5Load').onclick=loadCandidate;document.getElementById('oaG5Save').onclick=saveDecision;loadCandidate()}
const OAG5_SECTION=''' + repr(section) + r''';
let tries=0;const timer=setInterval(()=>{tries++;if(document.getElementById('oaPanel')&&typeof scene!=='undefined'&&scene){clearInterval(timer);initOAG5()}else if(tries>80)clearInterval(timer)},100);
})();
</script>'''
    return rendered.replace('</body>', script + '</body>', 1)
