#!/usr/bin/env python3
from __future__ import annotations

import json

import cew_ews3_spatial_candidate_review_runtime as ews3_runtime

PR2_RUNTIME_MARKER = "CEW_PR2_STRUCTURAL_GCP_CAPTURE"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def augment(rendered: str, task: str) -> str:
    if PR2_RUNTIME_MARKER in rendered or task != OA_PILOT_TASK:
        return rendered

    locators, meta = ews3_runtime._load_locators()
    locators_json = json.dumps(locators, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))

    style = r'''
<style id="cew-pr2-structural-gcp-capture-style">
#pr2PrecisionCard{border:1px solid var(--line);border-radius:7px;background:#f8fafb;padding:8px;margin:8px 0;font-size:11px}
#pr2PrecisionCard b{display:block;font-size:12px}.pr2-row{display:flex;gap:6px;align-items:center;justify-content:space-between;margin-top:6px}.pr2-row button{padding:6px 8px;font-size:10px}.pr2-preview{margin-top:7px;padding:7px;background:#fff7e8;border-left:4px solid var(--warn)}.pr2-preview.ok{background:#edf8f1;border-left-color:var(--ok)}
body.pr2-capture-active #sourceViewport{cursor:crosshair!important}body.pr2-capture-active #ews3SourceMarker{opacity:.45}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    script = f'''
<script id="cew-pr2-structural-gcp-capture-script" data-pr2-runtime="{PR2_RUNTIME_MARKER}">
(() => {{
const MARKER={PR2_RUNTIME_MARKER!r};
const LOCATORS={locators_json};
const REGISTRATION={meta_json};
let capture=false,pending=null;
function currentSupport(){{return window.__CEW_EWS32_LOCATOR__?.support_id||null}}
function item(){{try{{return viewer?.world?.getItemAt(0)||null}}catch(e){{return null}}}}
function predicted(support){{const loc=support?LOCATORS[String(support)]:null,it=item();if(!loc||!it)return null;const size=it.getContentSize?.();if(!size)return null;const nw=Number(size.x),nh=Number(size.y),u=Number(loc.u_px),v=Number(loc.v_px),x=nw-v,y=u;if(![nw,nh,u,v,x,y].every(Number.isFinite))return null;return {{support:String(support),x,y,nw,nh,common_x:Number(loc.metric_x_m),common_y:Number(loc.metric_y_m),loc}}}}
function ensureCard(){{
 const body=document.getElementById('ews2RailBody');if(!body)return null;let card=document.getElementById('pr2PrecisionCard');if(card)return card;
 card=document.createElement('section');card.id='pr2PrecisionCard';card.innerHTML='<b>Precisione posizione</b><div id="pr2Status">Predizione globale disponibile; non ancora verificata localmente.</div><div class="pr2-row"><span id="pr2Support">—</span><button type="button" id="pr2Capture">Verifica posizione</button></div><div id="pr2Preview"></div>';body.insertBefore(card,body.firstChild);
 document.getElementById('pr2Capture').onclick=toggleCapture;return card;
}}
function refreshCard(){{const card=ensureCard();if(!card)return;const s=currentSupport(),p=predicted(s);document.getElementById('pr2Support').textContent=s?'Supporto '+s:'Nessun supporto attivo';document.getElementById('pr2Capture').disabled=!p;document.getElementById('pr2Status').textContent=p?'Locator globale: REGISTERED_GLOBAL_NEEDS_LOCAL_QA':'Nessun locator globale disponibile';}}
function toggleCapture(){{capture=!capture;pending=null;document.body.classList.toggle('pr2-capture-active',capture);const b=document.getElementById('pr2Capture');if(b)b.textContent=capture?'Annulla cattura':'Verifica posizione';const pv=document.getElementById('pr2Preview');if(pv)pv.innerHTML=capture?'<div class="pr2-preview">Clicca il centro documentale reale del supporto sulla tavola. Nessuna decisione viene salvata finché non confermi.</div>':'';}}
function sourceEvidence(){{const s=scene?.source||{{}};return {{source_version_id:s.source_version_id,page_id:s.page_id,evidence_region_id:s.evidence_region_id,source_sha256:s.source_sha256}}}}
function revision(){{const s=scene?.source||{{}};return s.build_revision||scene?.build_revision||scene?.revision||scene?.scene_revision||'RUNTIME_SCENE'}}
function reviewer(){{return document.getElementById('oaTeachReviewer')?.value?.trim()||'HUMAN_OPERATOR'}}
function clickedNative(ev){{const it=item();if(!it||!viewer)return null;const vp=viewer.viewport.pointFromPixel(ev.position);const ip=it.viewportToImageCoordinates(vp);const x=Number(ip.x),y=Number(ip.y);return Number.isFinite(x)&&Number.isFinite(y)?{{x,y}}:null}}
function onCanvasClick(ev){{
 if(!capture)return;ev.preventDefaultAction=true;const s=currentSupport(),p=predicted(s),snap=clickedNative(ev);if(!p||!snap)return;
 capture=false;document.body.classList.remove('pr2-capture-active');document.getElementById('pr2Capture').textContent='Verifica posizione';
 const dx=snap.x-p.x,dy=snap.y-p.y,norm=Math.hypot(dx,dy);pending={{support:s,predicted:p,snapped:snap,dx,dy,norm}};
 const pv=document.getElementById('pr2Preview');pv.innerHTML=`<div class="pr2-preview"><b>Controllo locale pronto</b>Predetto: ${{p.x.toFixed(1)}}, ${{p.y.toFixed(1)}} px<br>Punto umano: ${{snap.x.toFixed(1)}}, ${{snap.y.toFixed(1)}} px<br>Residuo: Δx ${{dx.toFixed(1)}} · Δy ${{dy.toFixed(1)}} · |r| ${{norm.toFixed(1)}} px<div class="pr2-row"><button type="button" id="pr2Discard">Scarta</button><button type="button" class="primary" id="pr2Confirm">Conferma GCP</button></div></div>`;
 document.getElementById('pr2Discard').onclick=()=>{{pending=null;pv.innerHTML=''}};document.getElementById('pr2Confirm').onclick=persistPending;
}}
async function persistPending(){{
 if(!pending)return;const pv=document.getElementById('pr2Preview'),evidence=sourceEvidence();if(Object.values(evidence).some(v=>!v)){{pv.innerHTML='<div class="pr2-preview">Provenienza incompleta: GCP non registrato.</div>';return}}
 const p=pending;const payload={{source_evidence:evidence,support_id:String(p.support),feature_type:'COLUMN_CENTER',predicted_native_x_px:p.predicted.x,predicted_native_y_px:p.predicted.y,snapped_native_x_px:p.snapped.x,snapped_native_y_px:p.snapped.y,common_x_m:p.predicted.common_x,common_y_m:p.predicted.common_y,selection_method:'HUMAN_EXPLICIT_POINT',human_attestation:true,navigation_only:true,canonical_write_authorized:false,canonical_geometry_authorized:false,structural_identity_authorized:false}};
 pv.innerHTML='<div class="pr2-preview">Registrazione append-only del GCP…</div>';
 try{{const r=await fetch('/api/workbench/precision/gcp',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{task:TASK,revision:revision(),reviewer:reviewer(),payload}})}});const body=await r.json();if(!r.ok)throw new Error(body.reason||body.state||'PRECISION_GCP_PERSIST_FAILED');pending=null;pv.innerHTML=`<div class="pr2-preview ok"><b>GCP registrato</b>Supporto ${{p.support}} · residuo ${{Number(body.payload.residual_norm_px).toFixed(1)}} px<br>Receipt ${{body.runtime_receipt_id}}<br>Il locator NON è ancora promosso: serve analisi del campo residuo.</div>`;window.dispatchEvent(new CustomEvent('cew:pr2-gcp-persisted',{{detail:{{support_id:p.support,receipt_id:body.runtime_receipt_id,residual_norm_px:body.payload.residual_norm_px}}}}));}}
 catch(error){{pv.innerHTML='<div class="pr2-preview"><b>GCP non registrato.</b><br>'+String(error.message||error)+'</div>'}}
}}
function init(){{document.body.dataset.pr2StructuralGcp=MARKER;ensureCard();refreshCard();viewer?.addHandler?.('canvas-click',onCanvasClick);['cew:ews32-source-locator','cew:ews2-mode-change','cew:oa3-similarity-run'].forEach(e=>window.addEventListener(e,()=>setTimeout(refreshCard,40)));window.__CEW_PR2_GCP__={{state:'STRUCTURAL_GCP_CAPTURE_AVAILABLE',receipt_type:'CEW_PRECISION_GCP_RECEIPT_V1',locator_promotion_authorized:false,canonical_write_authorized:false,engineering_authority_effect:'NONE'}};}}
let tries=0;const timer=setInterval(()=>{{tries++;if(typeof viewer!=='undefined'&&viewer&&viewer.world?.getItemCount?.()>0&&document.getElementById('ews2RailBody')){{clearInterval(timer);init()}}else if(tries>180)clearInterval(timer)}},100);
}})();
</script>'''
    return rendered.replace("</body>", script + "</body>", 1)
