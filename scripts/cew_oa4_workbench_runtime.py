#!/usr/bin/env python3
from __future__ import annotations

import cew_oa5_workbench_runtime as oa5_runtime

OA4_RUNTIME_MARKER = "CEW_OA4_RUNTIME_HUMAN_CLUSTER_REVIEW"


def augment(rendered: str, task: str) -> str:
    """Add explicit human review of OA-3 similarity candidates.

    An OA-4 review becomes usable by OA-5 only after append-only persistence
    linked to its governed OA-2 prototype receipt.
    """
    if OA4_RUNTIME_MARKER in rendered:
        return oa5_runtime.augment(rendered, task)

    style = '''
<style id="cew-oa4-runtime-style">
#oaClusterReview{border-top:1px solid var(--line);margin-top:12px;padding-top:10px}.oa4-candidate{border:1px solid var(--line);border-radius:6px;padding:8px;margin:6px 0}.oa4-head{display:flex;gap:8px;align-items:center}.oa4-head input{width:auto}.oa4-candidate select,.oa4-candidate input[type=text]{width:100%;margin-top:5px;border:1px solid #b9c3ca;border-radius:5px;padding:6px}.oa4-decision{background:#edf8f1;border-left:4px solid var(--ok);padding:8px;margin-top:8px;font-size:12px}.oa4-warning{background:#fff7e8;border-left:4px solid var(--warn);padding:8px;margin-top:8px;font-size:12px}
</style>'''
    rendered = rendered.replace('</head>', style + '</head>', 1)

    section = '''
<section id="oaClusterReview" data-oa4-runtime="CEW_OA4_RUNTIME_HUMAN_CLUSTER_REVIEW">
  <h3>Revisione candidati</h3>
  <div class="oa-muted">Seleziona esplicitamente i candidati da decidere. Nessun candidato viene incluso automaticamente.</div>
  <button id="oaLoadReview" type="button">Carica ultimo gruppo</button>
  <div id="oaReviewCandidates"></div>
  <label>Revisore<input id="oaReviewReviewer" type="text" value="HUMAN_OPERATOR"></label>
  <button id="oaSaveReview" class="primary" type="button">Registra decisioni selezionate</button>
  <div id="oaReviewResult"></div>
  <div class="authority-note">Le decisioni entrano nella catena OA solo dopo registrazione append-only; l'identità strutturale resta OA-5/OA-G5.</div>
</section>'''

    script = r'''
<script id="cew-oa4-runtime-script">
(() => {
const OA4_MARKER='CEW_OA4_RUNTIME_HUMAN_CLUSTER_REVIEW';
const decisions=['CONFIRM_AS_FAMILY_CANDIDATE','REJECT','MOVE_TO_OTHER_FAMILY','MARK_AMBIGUOUS','DEFER_NEEDS_SOURCE'];
function latestSimilarity(){try{return JSON.parse(sessionStorage.getItem('cew-oa3:'+TASK+':latest')||'null')}catch(e){return null}}
function taughtPrototype(prototypeId){const prefix='cew-oa2:'+TASK+':';for(let i=sessionStorage.length-1;i>=0;i--){const k=sessionStorage.key(i);if(!k||!k.startsWith(prefix))continue;try{const p=JSON.parse(sessionStorage.getItem(k));if(p?.prototype_id===prototypeId&&p?.governed_receipt_id)return p}catch(e){}}return null}
function loadReview(){const host=document.getElementById('oaReviewCandidates'),run=latestSimilarity();if(!run||run.state!=='DETERMINISTIC_SIMILARITY_CANDIDATES'){host.innerHTML='<div class="oa4-warning">Esegui prima “Trova simili”.</div>';return}const parent=taughtPrototype(run.prototype_id);if(!parent){host.innerHTML='<div class="oa4-warning">Il prototipo non ha una receipt OA-2 governata. Ricrea il prototipo.</div>';return}host.innerHTML=run.candidates.map(c=>'<div class="oa4-candidate" data-candidate="'+c.candidate_object_id+'"><div class="oa4-head"><input class="oa4-select" type="checkbox" aria-label="Seleziona '+c.candidate_object_id+'"><b>'+c.candidate_object_id+'</b><span>'+Math.round(c.score*100)+'% · '+c.state+'</span></div><select class="oa4-choice">'+decisions.map(d=>'<option value="'+d+'">'+d+'</option>').join('')+'</select><input class="oa4-target" type="text" placeholder="Famiglia destinazione (solo se sposti)" hidden><div class="oa3-reasons">'+(c.reason_codes||[]).join(' · ')+'</div></div>').join('');host.querySelectorAll('.oa4-choice').forEach(sel=>sel.onchange=()=>{const target=sel.closest('.oa4-candidate').querySelector('.oa4-target');target.hidden=sel.value!=='MOVE_TO_OTHER_FAMILY'})}
async function fingerprint(run){const text=JSON.stringify({state:run.state,prototype_id:run.prototype_id,family_id:run.family_id,weights:run.weights,candidates:run.candidates.map(c=>({candidate_object_id:c.candidate_object_id,score:c.score,state:c.state,reason_codes:c.reason_codes}))});const buf=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('')}
async function persistOA4(review,reviewer,parentId,revision){const response=await fetch('/api/workbench/object-acquisition/receipt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:TASK,stage:'OA4_CLUSTER_REVIEW',revision,reviewer,payload:review,parent_decision_id:parentId})});const body=await response.json();if(!response.ok)throw new Error(body.reason||body.state||'OA4_GOVERNED_PERSISTENCE_FAILED');review.governed_receipt_id=body.runtime_receipt_id;review.governed_receipt_fingerprint=body.receipt_fingerprint;review.governed_audit_backend=body.audit_backend;review.governed_persistence_state=body.state;return review}
async function saveReview(){const host=document.getElementById('oaReviewResult'),run=latestSimilarity(),reviewer=document.getElementById('oaReviewReviewer').value.trim();if(!run){host.innerHTML='<div class="oa4-warning">Nessun gruppo disponibile.</div>';return}const parent=taughtPrototype(run.prototype_id);if(!parent){host.innerHTML='<div class="oa4-warning">Manca la receipt governata del prototipo OA-2.</div>';return}if(!reviewer){host.innerHTML='<div class="oa4-warning">Indica il revisore.</div>';return}const selected=[...document.querySelectorAll('.oa4-candidate')].filter(row=>row.querySelector('.oa4-select').checked);if(!selected.length){host.innerHTML='<div class="oa4-warning">Seleziona esplicitamente almeno un candidato.</div>';return}const fp=await fingerprint(run),source=scene?.source||{},revision=source.build_revision||scene?.build_revision||scene?.revision||'RUNTIME_SCENE',evidence={source_version_id:source.source_version_id,page_id:source.page_id,evidence_region_id:source.evidence_region_id,source_sha256:source.source_sha256};const rows=[];for(const row of selected){const candidateId=row.dataset.candidate,choice=row.querySelector('.oa4-choice').value,target=row.querySelector('.oa4-target').value.trim();if(choice==='MOVE_TO_OTHER_FAMILY'&&!target){host.innerHTML='<div class="oa4-warning">Specifica la famiglia di destinazione per '+candidateId+'.</div>';return}const candidate=run.candidates.find(c=>c.candidate_object_id===candidateId);rows.push({candidate_object_id:candidateId,decision:choice,prototype_id:run.prototype_id,proposed_family_id:['MARK_AMBIGUOUS','DEFER_NEEDS_SOURCE'].includes(choice)?null:(choice==='MOVE_TO_OTHER_FAMILY'?target:run.family_id),similarity_run_fingerprint:fp,similarity_score:candidate.score,similarity_state:candidate.state,similarity_reason_codes:candidate.reason_codes,source_evidence:evidence,reviewer,revision,family_membership_proposal_created:['CONFIRM_AS_FAMILY_CANDIDATE','MOVE_TO_OTHER_FAMILY'].includes(choice),structural_identity_created:false,canonical_write_authorized:false})}
 const review={state:'HUMAN_REVIEWED_FAMILY_CANDIDATES',source_evidence:evidence,similarity_run_fingerprint:fp,prototype_id:run.prototype_id,candidate_decisions:rows,explicit_candidate_selection:true,implicit_cluster_acceptance:false,structural_identity_created:false,accepted_structural_identity:false,canonical_write_authorized:false,project_material_ready:false,project_material_promotion_authorized:false,engineering_authority_effect:'NONE',next_gate:'OA-5_STRUCTURAL_RESOLVER'};host.innerHTML='<div class="oa4-decision">Registrazione append-only delle decisioni…</div>';try{await persistOA4(review,reviewer,parent.governed_receipt_id,revision)}catch(error){host.innerHTML='<div class="oa4-warning"><b>Revisione non registrata.</b><br>'+String(error.message||error)+'<br>OA-5 resta bloccata.</div>';return}sessionStorage.setItem('cew-oa4:'+TASK+':latest',JSON.stringify(review));host.innerHTML='<div class="oa4-decision"><b>'+rows.length+' decisioni registrate append-only.</b><br>Receipt: '+review.governed_receipt_id+'<br>Identità strutturale: false · Scrittura canonica: false</div>'}
function initOA4(){const similar=document.getElementById('oaSimilar'),panel=document.getElementById('oaPanel');if(!panel||document.getElementById('oaClusterReview'))return;(similar||panel).insertAdjacentHTML('afterend',OA4_SECTION);document.getElementById('oaLoadReview').onclick=loadReview;document.getElementById('oaSaveReview').onclick=saveReview}
const OA4_SECTION=''' + repr(section) + r''';
let tries=0;const timer=setInterval(()=>{tries++;if(document.getElementById('oaPanel')&&typeof scene!=='undefined'&&scene){clearInterval(timer);initOA4()}else if(tries>80)clearInterval(timer)},100);
})();
</script>'''
    rendered = rendered.replace('</body>', script + '</body>', 1)
    return oa5_runtime.augment(rendered, task)
