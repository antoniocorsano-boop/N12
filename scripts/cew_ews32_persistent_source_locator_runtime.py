#!/usr/bin/env python3
from __future__ import annotations

import json

import cew_ews3_spatial_candidate_review_runtime as ews3_runtime

EWS32_RUNTIME_MARKER = "CEW_EWS32_PERSISTENT_SOURCE_LOCATOR"
OA_PILOT_TASK = "OA-N12-G4-COLUMN-PILOT"


def augment(rendered: str, task: str) -> str:
    """Keep a navigation-only source marker for prototype and active review object."""
    if EWS32_RUNTIME_MARKER in rendered or task != OA_PILOT_TASK:
        return rendered

    locators, meta = ews3_runtime._load_locators()
    locators_json = json.dumps(locators, ensure_ascii=False, separators=(",", ":"))
    meta_json = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))

    style = r'''
<style id="cew-ews32-persistent-source-locator-style">
#ews32LocatorBadge{position:absolute;z-index:42;left:12px;bottom:12px;max-width:min(360px,65%);background:rgba(255,255,255,.94);border:1px solid var(--line);border-left:4px solid var(--ok);border-radius:6px;padding:6px 8px;font-size:10px;box-shadow:0 2px 10px rgba(0,0,0,.18);pointer-events:none}
#ews32LocatorBadge b{display:block;font-size:11px;color:var(--ink)}
</style>'''
    rendered = rendered.replace("</head>", style + "</head>", 1)

    script = f'''
<script id="cew-ews32-persistent-source-locator-script" data-ews32-runtime="{EWS32_RUNTIME_MARKER}">
(() => {{
const MARKER={EWS32_RUNTIME_MARKER!r};
const LOCATORS={locators_json};
const REGISTRATION={meta_json};
let marker=null,lastKey='';
function readJson(key){{try{{return JSON.parse(sessionStorage.getItem(key)||'null')}}catch(e){{return null}}}}
function latestPrototype(){{const prefix='cew-oa2:'+TASK+':';let hit=null;for(let i=0;i<sessionStorage.length;i++){{const k=sessionStorage.key(i);if(!k||!k.startsWith(prefix))continue;const row=readJson(k);if(row?.governed_receipt_id&&row?.anchor_object_id)hit=row}}return hit}}
function sceneObject(id){{return (scene?.objects||[]).find(o=>o.object_id===id)||null}}
function supportForObject(id){{const p=sceneObject(id)?.properties||{{}};return p.support_id!=null?String(p.support_id):null}}
function currentMode(){{return window.__CEW_EWS2_RAIL__?.mode||'ACQUIRE'}}
function reviewObjectId(){{return document.querySelector('#oaSimilarResult [data-candidate][aria-current="true"]')?.dataset?.candidate||null}}
function currentObjectId(){{const mode=currentMode();if(mode==='REVIEW_SET')return reviewObjectId();const p=latestPrototype();return p?.anchor_object_id||null}}
function item(){{try{{return viewer?.world?.getItemAt(0)||null}}catch(e){{return null}}}}
function ensureMarker(){{let m=document.getElementById('ews3SourceMarker');if(m){{marker=m;return m}};m=document.createElement('div');m.id='ews3SourceMarker';m.setAttribute('aria-hidden','true');marker=m;return m}}
function removeMarker(){{if(!viewer||!marker)return;try{{viewer.removeOverlay(marker)}}catch(e){{}}}}
function nativePoint(locator,it){{const size=it?.getContentSize?.();if(!size)return null;const nw=Number(size.x),nh=Number(size.y),u=Number(locator?.u_px),v=Number(locator?.v_px);if(!Number.isFinite(nw)||!Number.isFinite(nh)||!Number.isFinite(u)||!Number.isFinite(v))return null;const x=nw-v,y=u;if(x<0||x>nw||y<0||y>nh)return null;return {{x,y,nw,nh}}}}
function badge(text,support){{const pane=document.querySelector('.source-pane');if(!pane)return;let b=document.getElementById('ews32LocatorBadge');if(!b){{b=document.createElement('div');b.id='ews32LocatorBadge';pane.appendChild(b)}}b.innerHTML=`<b>Supporto ${{support}} · posizione sulla fonte</b>${{text}}`;}}
function clearBadge(){{document.getElementById('ews32LocatorBadge')?.remove()}}
function syncLegacyLabels(support,located){{
 const reg=document.getElementById('registrationState');if(reg){{reg.textContent=located?'locator fonte registrato · navigazione':'posizione sulla tavola non registrata';reg.dataset.ews32State=located?'REGISTERED_DERIVED':'UNLOCATED'}}
 const human=document.querySelector('#oaHumanHeader .oa-human-status div:nth-child(2) b');if(human){{human.textContent=located?'Registrata · navigazione':'Non registrata';human.classList.toggle('oa-human-ok',located);human.classList.toggle('oa-human-warn',!located)}}
 const blocker=document.querySelector('#oaHumanHeader .oa-human-blocker');if(blocker&&located)blocker.innerHTML='<strong>Posizione disponibile per navigazione sulla fonte.</strong>Il locator aiuta a trovare il supporto sulla tavola. Non crea sincronizzazione fonte↔modello né identità strutturale.';
 const selectedCard=document.getElementById('oaHumanSelected');if(selectedCard&&located&&support){{const small=selectedCard.querySelector('small');if(small)small.textContent='Posizione sulla tavola: locator registrato per navigazione.'}}
}}
function focusCurrent(force=false){{
 const oid=currentObjectId(),support=oid?supportForObject(oid):null,locator=support?LOCATORS[support]||null:null,it=item();
 const key=(currentMode()||'')+'|'+String(oid||'')+'|'+String(support||'');if(!force&&key===lastKey)return;lastKey=key;
 if(!locator||!it){{removeMarker();clearBadge();syncLegacyLabels(support,false);return}}
 const p=nativePoint(locator,it);if(!p){{removeMarker();clearBadge();syncLegacyLabels(support,false);return}}
 const contextW=Math.max(900,p.nw*.18),contextH=Math.max(1200,p.nh*.145),x=Math.max(0,Math.min(p.nw-contextW,p.x-contextW/2)),y=Math.max(0,Math.min(p.nh-contextH,p.y-contextH/2));
 const rect=it.imageToViewportRectangle(x,y,Math.min(contextW,p.nw),Math.min(contextH,p.nh));const point=it.imageToViewportCoordinates(new OpenSeadragon.Point(p.x,p.y));
 removeMarker();viewer.addOverlay({{element:ensureMarker(),location:point,placement:OpenSeadragon.Placement.CENTER,checkResize:false}});viewer.viewport.fitBounds(rect,false);viewer.viewport.applyConstraints();
 syncLegacyLabels(support,true);badge(currentMode()==='REVIEW_SET'?'Candidato attivo':'Prototipo governato',support);
 document.body.dataset.ews32PersistentLocator='REGISTERED_DERIVED';
 window.__CEW_EWS32_LOCATOR__={{state:'PERSISTENT_SOURCE_LOCATOR_ACTIVE',mode:currentMode(),object_id:oid,support_id:support,locator_state:'REGISTERED_DERIVED',source_frame:REGISTRATION.source_frame,viewer_frame_adapter:REGISTRATION.viewer_frame_adapter,navigation_only:true,canonical_write_authorized:false,structural_identity_authorized:false}};
 window.dispatchEvent(new CustomEvent('cew:ews32-source-locator',{{detail:window.__CEW_EWS32_LOCATOR__}}));
}}
['cew:ews2-mode-change','cew:oa2-prototype-persisted','cew:governed-context-resumed','cew:enterprise-governed-resume','cew:oa3-similarity-run','cew:ews4-candidate-reviewed'].forEach(e=>window.addEventListener(e,()=>setTimeout(()=>focusCurrent(true),60)));
let tries=0;const timer=setInterval(()=>{{tries++;if(typeof viewer!=='undefined'&&viewer&&viewer.world?.getItemCount?.()>0&&typeof scene!=='undefined'&&scene){{clearInterval(timer);setTimeout(()=>focusCurrent(true),100)}}else if(tries>180)clearInterval(timer)}},100);
}})();
</script>'''
    return rendered.replace("</body>", script + "</body>", 1)
