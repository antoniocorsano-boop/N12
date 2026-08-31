#!/usr/bin/env python3
from __future__ import annotations

OA5_RUNTIME_MARKER = "CEW_OA5_RUNTIME_STRUCTURAL_RESOLVER"


def augment(rendered: str, task: str) -> str:
    """Add guided structural-identity candidate resolution to the shared Workbench.

    OA-5 consumes only governed OA-4 family-candidate decisions. Every identity
    candidate is persisted append-only before it can reach the explicit OA-G5 gate.
    """
    if OA5_RUNTIME_MARKER in rendered:
        return rendered

    style = '''
<style id="cew-oa5-runtime-style">
#oaStructuralResolver{border-top:1px solid var(--line);margin-top:12px;padding-top:10px}#oaStructuralResolver select,#oaStructuralResolver input{width:100%;border:1px solid #b9c3ca;border-radius:6px;padding:6px;margin-top:4px}.oa5-rel{border:1px solid var(--line);padding:7px;border-radius:6px;margin-top:6px;font-size:12px}.oa5-ready{background:#edf8f1;border-left:4px solid var(--ok);padding:8px;margin-top:8px}.oa5-block{background:#fff7e8;border-left:4px solid var(--warn);padding:8px;margin-top:8px}.oa5-conflict{background:#fff3f3;border-left:4px solid var(--danger);padding:8px;margin-top:8px}
</style>'''
    rendered = rendered.replace('</head>', style + '</head>', 1)

    section = '''
<section id="oaStructuralResolver" data-oa5-runtime="CEW_OA5_RUNTIME_STRUCTURAL_RESOLVER">
  <h3>Resolver identità strutturale</h3>
  <div class="oa-muted">Una famiglia confermata non è ancora identità strutturale. Aggiungi relazioni tecniche esplicite e la relativa evidenza.</div>
  <button id="oa5Load" type="button">Carica candidati confermati</button>
  <label>Candidato famiglia<select id="oa5Candidate"></select></label>
  <label>Relazione<select id="oa5RelationType"><option>VERTICAL_CONTINUITY</option><option>FRAME_MEMBERSHIP</option><option>NODE_CONNECTIVITY</option><option>SECTION_CONTINUITY</option><option>EXPLICIT_DRAWING_CALLOUT</option><option>CROSS_DRAWING_REGISTRATION</option><option>SAME_LEVEL_ALIGNMENT</option></select></label>
  <label>Target tecnico<input id="oa5Target" type="text" placeholder="es. G3-P27 / FRAME-5"></label>
  <label>Riferimento evidenza<input id="oa5EvidenceRef" type="text" placeholder="EvidenceRegion / registro / binding"></label>
  <label>Esito relazione<select id="oa5Support"><option>SUPPORTS</option><option>CONFLICTS</option></select></label>
  <button id="oa5AddRelation" type="button">Aggiungi relazione</button>
  <div id="oa5Relations"></div>
  <button id="oa5Resolve" class="primary" type="button">Costruisci candidato identità</button>
  <div id="oa5Result"></div>
  <div class="authority-note">Il candidato entra in OA-G5 solo dopo registrazione append-only. L'identità non è mai auto-accettata.</div>
</section>'''

    script = r'''
<script id="cew-oa5-runtime-script">
(() => {
const OA5_MARKER='CEW_OA5_RUNTIME_STRUCTURAL_RESOLVER';
let oa5Relations=[];
function latestOA4(){try{return JSON.parse(sessionStorage.getItem('cew-oa4:'+TASK+':latest')||'null')}catch(e){return null}}
function admissibleDecisions(){const r=latestOA4();if(!r?.governed_receipt_id)return [];return (r?.candidate_decisions||[]).filter(d=>['CONFIRM_AS_FAMILY_CANDIDATE','MOVE_TO_OTHER_FAMILY'].includes(d.decision)&&d.family_membership_proposal_created===true)}
function loadCandidates(){const sel=document.getElementById('oa5Candidate'),review=latestOA4(),rows=admissibleDecisions();sel.innerHTML=rows.map((d,i)=>'<option value="'+i+'">'+d.candidate_object_id+' · '+d.proposed_family_id+'</option>').join('');if(!review?.governed_receipt_id)document.getElementById('oa5Result').innerHTML='<div class="oa5-block">La revisione OA-4 non è registrata nel ledger governato.</div>';else if(!rows.length)document.getElementById('oa5Result').innerHTML='<div class="oa5-block">Nessun candidato famiglia confermato disponibile. Completa prima OA-4.</div>'}
function renderRelations(){document.getElementById('oa5Relations').innerHTML=oa5Relations.map((r,i)=>'<div class="oa5-rel"><b>'+r.relationship_type+'</b> → '+r.target_id+'<br>'+r.evidence_ref+' · '+r.support+' <button type="button" data-remove="'+i+'">Rimuovi</button></div>').join('');document.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>{oa5Relations.splice(Number(b.dataset.remove),1);renderRelations()})}
function addRelation(){const type=document.getElementById('oa5RelationType').value,target=document.getElementById('oa5Target').value.trim(),ref=document.getElementById('oa5EvidenceRef').value.trim(),support=document.getElementById('oa5Support').value,revision=scene?.source?.build_revision||scene?.build_revision||scene?.revision||'RUNTIME_SCENE';if(!target||!ref){document.getElementById('oa5Result').innerHTML='<div class="oa5-block">Target ed evidenza sono obbligatori.</div>';return}oa5Relations.push({relationship_type:type,target_id:target,evidence_ref:ref,revision,support});renderRelations();document.getElementById('oa5Target').value='';document.getElementById('oa5EvidenceRef').value=''}
async function idFor(seed){const buf=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(seed)));return 'SIC-'+Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('').slice(0,20).toUpperCase()}
async function persistOA5(candidate,review,reviewer,revision){const response=await fetch('/api/workbench/object-acquisition/receipt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task:TASK,stage:'OA5_IDENTITY_CANDIDATE',revision,reviewer,payload:candidate,parent_decision_id:review.governed_receipt_id})});const body=await response.json();if(!response.ok)throw new Error(body.reason||body.state||'OA5_GOVERNED_PERSISTENCE_FAILED');candidate.governed_receipt_id=body.runtime_receipt_id;candidate.governed_receipt_fingerprint=body.receipt_fingerprint;candidate.governed_audit_backend=body.audit_backend;candidate.governed_persistence_state=body.state;return candidate}
async function resolveCandidate(){const review=latestOA4(),rows=admissibleDecisions(),idx=Number(document.getElementById('oa5Candidate').value),decision=rows[idx],host=document.getElementById('oa5Result');if(!review?.governed_receipt_id){host.innerHTML='<div class="oa5-block">OA-4 non è persistita: resolver bloccato.</div>';return}if(!decision){host.innerHTML='<div class="oa5-block">Seleziona un candidato famiglia confermato.</div>';return}const revision=scene?.source?.build_revision||scene?.build_revision||scene?.revision||'RUNTIME_SCENE';const conflicts=oa5Relations.some(r=>r.support==='CONFLICTS'),supports=oa5Relations.filter(r=>r.support==='SUPPORTS');const candidateState=conflicts?'IDENTITY_CONFLICT':supports.length?'READY_FOR_EXPLICIT_IDENTITY_REVIEW':'INSUFFICIENT_RELATIONSHIP_EVIDENCE';const candidate={state:'STRUCTURAL_IDENTITY_CANDIDATE',candidate_state:candidateState,identity_candidate_id:await idFor({object:decision.candidate_object_id,family:decision.proposed_family_id,revision,relationships:oa5Relations}),source_object_id:decision.candidate_object_id,family_id:decision.proposed_family_id,source_evidence:decision.source_evidence,relationship_evidence:[...oa5Relations],supporting_relationship_count:supports.length,relationship_conflict:conflicts,proximity_used_as_identity_evidence:false,similarity_used_as_identity_authority:false,family_membership_used_as_identity_authority:false,accepted_structural_identity:false,explicit_identity_review_required:true,canonical_write_authorized:false,project_material_ready:false,engineering_authority_effect:'NONE',revision,next_gate:'OA-G5_EXPLICIT_STRUCTURAL_IDENTITY_REVIEW'};host.innerHTML='<div class="oa5-block">Registrazione append-only del candidato identità…</div>';try{await persistOA5(candidate,review,decision.reviewer||'HUMAN_OPERATOR',revision)}catch(error){host.innerHTML='<div class="oa5-conflict"><b>Candidato non registrato.</b><br>'+String(error.message||error)+'<br>OA-G5 resta bloccato.</div>';return}sessionStorage.setItem('cew-oa5:'+TASK+':latest',JSON.stringify(candidate));const cls=candidateState==='READY_FOR_EXPLICIT_IDENTITY_REVIEW'?'oa5-ready':candidateState==='IDENTITY_CONFLICT'?'oa5-conflict':'oa5-block';host.innerHTML='<div class="'+cls+'"><b>'+candidateState+'</b><br>'+candidate.identity_candidate_id+'<br>Receipt: '+candidate.governed_receipt_id+'<br>Relazioni di supporto: '+supports.length+'<br>Identità accettata: false · Materiale progettuale pronto: false</div>'}
function initOA5(){const review=document.getElementById('oaClusterReview'),panel=document.getElementById('oaPanel');if(!panel||document.getElementById('oaStructuralResolver'))return;(review||panel).insertAdjacentHTML('afterend',OA5_SECTION);document.getElementById('oa5Load').onclick=loadCandidates;document.getElementById('oa5AddRelation').onclick=addRelation;document.getElementById('oa5Resolve').onclick=resolveCandidate;loadCandidates()}
const OA5_SECTION=''' + repr(section) + r''';
let tries=0;const timer=setInterval(()=>{tries++;if(document.getElementById('oaPanel')&&typeof scene!=='undefined'&&scene){clearInterval(timer);initOA5()}else if(tries>80)clearInterval(timer)},100);
})();
</script>'''
    return rendered.replace('</body>', script + '</body>', 1)
