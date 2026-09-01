#!/usr/bin/env python3
from __future__ import annotations

import cew_ews2_unified_context_rail_runtime as ews2_runtime
import cew_ews2_visibility_guard_runtime as ews2_guard_runtime
import cew_ews3_spatial_candidate_review_runtime as ews3_runtime
import cew_ews21_compact_context_rail_runtime as ews21_runtime
import cew_ews32_persistent_source_locator_runtime as ews32_runtime

RESUME_RUNTIME_MARKER = "CEW_ENTERPRISE_GOVERNED_CONTEXT_RESUME"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def _presentation(rendered: str, task: str) -> str:
    focused = ews2_guard_runtime.augment(ews2_runtime.augment(rendered, task), task)
    spatial = ews3_runtime.augment(focused, task)
    compact = ews21_runtime.augment(spatial, task)
    return ews32_runtime.augment(compact, task)


def augment(rendered: str, task: str) -> str:
    """Restore governed OA working context after login/reload.

    The append-only ledger remains authority for the receipt. sessionStorage is
    reconstructed only as a browser cache so existing OA-3/OA-4 presentation code
    can resume without creating a duplicate decision. EWS-2 owns focused workflow
    orchestration; EWS-3 owns navigation locators; EWS-2.1 compacts presentation;
    EWS-3.2 keeps the current source locator visible across eligible work modes.
    """
    if RESUME_RUNTIME_MARKER in rendered:
        return _presentation(rendered, task)

    script = f'''
<script id="cew-enterprise-governed-resume-script" data-resume-runtime="{RESUME_RUNTIME_MARKER}">
(() => {{
const RESUME_MARKER={RESUME_RUNTIME_MARKER!r};
const OA_PILOT_TASK={OA_PILOT_TASK!r};
if(TASK!==OA_PILOT_TASK)return;
async function resumeOA2(){{
  const host=document.getElementById('oaTeachResult');
  try{{
    const response=await fetch('/api/workbench/object-acquisition/resume?task='+encodeURIComponent(TASK)+'&stage=OA2_PROTOTYPE',{{cache:'no-store'}});
    if(response.status===404)return;
    const body=await response.json();
    if(!response.ok)throw new Error(body.reason||body.state||'OA_GOVERNED_RESUME_FAILED');
    const proposal=Object.assign({{}},body.payload||{{}},{{
      governed_receipt_id:body.runtime_receipt_id,
      governed_receipt_fingerprint:body.receipt_fingerprint,
      governed_audit_backend:body.audit_backend,
      governed_persistence_state:body.state,
      resumed_from_governed_ledger:true
    }});
    if(!proposal.prototype_id||proposal.state!=='HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE')throw new Error('OA_GOVERNED_RESUME_PAYLOAD_INVALID');
    sessionStorage.setItem('cew-oa2:'+TASK+':'+proposal.prototype_id,JSON.stringify(proposal));
    document.body.dataset.governedContextResume=RESUME_MARKER;
    if(host)host.innerHTML='<div class="oa2-receipt"><b>Prototipo ripristinato dal registro governato.</b><br>Receipt: '+body.runtime_receipt_id+'<br>'+body.audit_backend+' · nessuna nuova scrittura.</div>';
    const current=document.getElementById('oaHumanCurrentStep');if(current)current.textContent='Trova oggetti simili';
    window.dispatchEvent(new CustomEvent('cew:oa2-prototype-persisted',{{detail:{{task:TASK,prototype_id:proposal.prototype_id,receipt_id:body.runtime_receipt_id,resumed:true}}}}));
    window.dispatchEvent(new CustomEvent('cew:governed-context-resumed',{{detail:{{task:TASK,stage:'OA2_PROTOTYPE',receipt_id:body.runtime_receipt_id}}}}));
  }}catch(error){{
    if(host)host.innerHTML='<div class="oa2-error"><b>Ripresa del contesto non riuscita.</b><br>'+String(error.message||error)+'<br>Nessuna nuova decisione è stata creata.</div>';
  }}
}}
let tries=0;const timer=setInterval(()=>{{tries++;if(document.getElementById('oaTeachResult')&&typeof scene!=='undefined'&&scene){{clearInterval(timer);resumeOA2()}}else if(tries>100)clearInterval(timer)}},80);
}})();
</script>'''
    return _presentation(rendered.replace("</body>", script + "</body>", 1), task)
