#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from cew_mobile_review import AUTHORITY_CLOSED, PRIMARY_ACTIONS, validate_manifest

ACTION_LABELS = {
    "PILASTRO": "✅ Pilastro",
    "NON_PILASTRO": "❌ No",
    "INQUADRATO_MALE": "⚠️ Inquadrato male",
    "ALTRO_PILASTRO": "➕ Altro pilastro",
}


def build_html(manifest: dict) -> str:
    validate_manifest(manifest)
    manifest_json = json.dumps(manifest, ensure_ascii=False).replace("</", "<\\/")
    authority_json = json.dumps(AUTHORITY_CLOSED, ensure_ascii=False, separators=(",", ":"))
    action_buttons = "".join(
        f'<button class="primary-action" data-action="{action}">{html.escape(ACTION_LABELS[action])}</button>'
        for action in PRIMARY_ACTIONS
    )
    return f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>CEW — Revisione mobile</title>
<style>
:root{{--bar-height:132px;--ui-gap:8px;--border:#d7dbe1;--bg:#f5f6f8;--ink:#18212b}}
*{{box-sizing:border-box}}
html,body{{margin:0;min-height:100%;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}}
body{{padding-bottom:calc(var(--bar-height) + env(safe-area-inset-bottom) + 12px)}}
.topbar{{position:sticky;top:0;z-index:4;background:rgba(255,255,255,.96);border-bottom:1px solid var(--border);padding:8px 10px;display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center}}
.topbar button{{min-height:48px;min-width:48px;border:1px solid var(--border);border-radius:10px;background:#fff;font-weight:700}}
#progress{{text-align:center;font-weight:800;font-variant-numeric:tabular-nums}}
#candidateId{{font-size:.76rem;color:#536273;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.review-main{{max-width:980px;margin:0 auto;padding:8px}}
.prompt{{font-size:.9rem;margin:4px 2px 8px;color:#425466}}
.evidence-viewport{{background:#fff;border:1px solid var(--border);border-radius:12px;overflow:auto;min-height:58vh;display:flex;align-items:flex-start;justify-content:center;touch-action:pan-x pan-y pinch-zoom;overscroll-behavior:contain}}
.evidence-viewport.pick-mode{{outline:4px solid #c77700;outline-offset:-4px;touch-action:none}}
.evidence-stage{{position:relative;width:100%;line-height:0}}
#evidence{{display:block;width:100%;height:auto;max-width:none;user-select:none;-webkit-user-drag:none}}
.point-markers{{position:absolute;inset:0;pointer-events:none}}
.point-marker{{position:absolute;width:30px;height:30px;border:3px solid #c77700;border-radius:50%;transform:translate(-50%,-50%);background:rgba(255,255,255,.72);box-shadow:0 0 0 2px rgba(199,119,0,.2),0 1px 5px rgba(0,0,0,.25)}}
.point-marker::before,.point-marker::after{{content:'';position:absolute;background:#c77700;left:50%;top:50%;transform:translate(-50%,-50%)}}
.point-marker::before{{width:18px;height:2px}}
.point-marker::after{{width:2px;height:18px}}
.pick-hint{{display:none;position:sticky;bottom:8px;margin:8px;background:#fff3d6;border:1px solid #d99b2b;border-radius:10px;padding:10px;font-weight:700;text-align:center}}
.pick-mode + .pick-hint{{display:block}}
.optional-reason{{margin:8px 0;background:#fff;border:1px solid var(--border);border-radius:10px;padding:8px}}
.optional-reason summary{{min-height:48px;display:flex;align-items:center;font-weight:650}}
#negativeReason{{width:100%;min-height:48px;font-size:1rem}}
.status{{min-height:38px;padding:8px 4px;color:#425466;font-size:.88rem}}
.mobile-action-bar{{position:fixed;left:0;right:0;bottom:0;z-index:10;background:rgba(255,255,255,.98);border-top:1px solid var(--border);padding:8px 8px calc(8px + env(safe-area-inset-bottom));display:grid;grid-template-columns:1fr 1fr;gap:8px;min-height:var(--bar-height)}}
.primary-action{{min-height:48px;border:1px solid #bdc5cf;border-radius:12px;background:#fff;font-size:.94rem;font-weight:800;padding:6px 8px}}
.primary-action:active{{transform:scale(.99)}}
.primary-action[data-action="PILASTRO"]{{border-width:2px}}
.primary-action[data-action="NON_PILASTRO"]{{border-width:2px}}
#export{{font-size:.78rem}}
@media(min-width:700px){{:root{{--bar-height:76px}}.mobile-action-bar{{grid-template-columns:repeat(4,1fr);max-width:980px;margin:0 auto;border:1px solid var(--border);border-radius:14px 14px 0 0}}.evidence-viewport{{min-height:68vh}}}}
</style>
</head>
<body>
<header class="topbar">
  <button id="undo" type="button" aria-label="Annulla ultima scelta">↶</button>
  <div><div id="progress">1 / 1</div><div id="candidateId"></div></div>
  <button id="export" type="button" aria-label="Esporta revisione">JSON</button>
</header>
<main class="review-main">
  <div id="prompt" class="prompt"></div>
  <div id="viewport" class="evidence-viewport"><div id="evidenceStage" class="evidence-stage"><img id="evidence" alt="Evidenza da revisionare"><div id="pointMarkers" class="point-markers" aria-hidden="true"></div></div></div>
  <div class="pick-hint">Tocca direttamente il centro dell'altro pilastro visibile.</div>
  <details class="optional-reason">
    <summary>Motivo opzionale per “No”</summary>
    <select id="negativeReason">
      <option value="">— nessun motivo —</option>
      <option value="TRAVE">Trave</option>
      <option value="QUOTA">Quota</option>
      <option value="LINEA_DI_DISEGNO">Linea di disegno</option>
      <option value="RITAGLIO_INCOMPLETO">Ritaglio incompleto</option>
      <option value="ALTRO">Altro</option>
    </select>
  </details>
  <div id="status" class="status" aria-live="polite">Pronto.</div>
</main>
<nav class="mobile-action-bar" aria-label="Valutazione candidato">{action_buttons}</nav>
<script>
const MANIFEST={manifest_json};
const AUTHORITY={authority_json};
const STORAGE_KEY='cew-mobile-review:'+MANIFEST.review_id;
const TERMINAL=new Set(['PILASTRO','NON_PILASTRO','INQUADRATO_MALE']);
let model=loadModel();
let pickMode=false;

function defaultModel(){{return {{index:0,events:[]}}}}
function loadModel(){{try{{const raw=localStorage.getItem(STORAGE_KEY);if(!raw)return defaultModel();const parsed=JSON.parse(raw);return parsed&&Array.isArray(parsed.events)?parsed:defaultModel()}}catch(_e){{return defaultModel()}}}}
function saveModel(){{localStorage.setItem(STORAGE_KEY,JSON.stringify(model))}}
function eventId(){{return 'EV-'+String(model.events.length+1).padStart(5,'0')+'-'+Date.now()}}
function current(){{return MANIFEST.candidates[Math.min(model.index,MANIFEST.candidates.length-1)]}}
function appendEvent(event){{model.events.push({{schema_version:'cew-mobile-review-event-v1',event_id:eventId(),timestamp:new Date().toISOString(),...event}});saveModel()}}
function undoneIds(){{return new Set(model.events.filter(e=>e.event_type==='UNDO_LAST').map(e=>e.undoes_event_id))}}
function lastEffectiveEvent(){{const undone=undoneIds();for(let i=model.events.length-1;i>=0;i--){{const e=model.events[i];if(e.event_type!=='UNDO_LAST'&&!undone.has(e.event_id))return e}}return null}}
function effectiveAdditionalPoints(candidateId){{
 const undone=undoneIds();
 return model.events.filter(e=>e.event_type==='ADDITIONAL_OCCURRENCE'&&e.candidate_id===candidateId&&!undone.has(e.event_id)&&e.point).map(e=>e.point);
}}
function renderPointMarkers(){{
 const layer=document.getElementById('pointMarkers');layer.replaceChildren();
 effectiveAdditionalPoints(current().candidate_id).forEach((p,index)=>{{
  const marker=document.createElement('span');marker.className='point-marker';
  const x=Math.max(0,Math.min(1,Number(p.x))),y=Math.max(0,Math.min(1,Number(p.y)));
  marker.style.left=(x*100)+'%';marker.style.top=(y*100)+'%';marker.title='Altro pilastro '+(index+1);layer.appendChild(marker);
 }});
}}
function setStatus(text){{document.getElementById('status').textContent=text}}
function render(){{
 const c=current(),total=MANIFEST.candidates.length;
 document.getElementById('progress').textContent=(model.index+1)+' / '+total;
 document.getElementById('candidateId').textContent=c.candidate_id;
 document.getElementById('prompt').textContent=c.prompt||'Valuta solo l’impronta grafica proposta.';
 const img=document.getElementById('evidence');img.src=c.overlay_image_uri||c.image_uri;img.dataset.sourceUri=c.image_uri;
 document.getElementById('viewport').classList.toggle('pick-mode',pickMode);
 renderPointMarkers();
}}
function advance(){{if(model.index<MANIFEST.candidates.length-1)model.index+=1;saveModel();pickMode=false;document.getElementById('negativeReason').value='';render()}}
function decide(action){{
 const c=current();
 if(action==='ALTRO_PILASTRO'){{pickMode=true;render();setStatus('Modalità “Altro pilastro”: tocca il pilastro nell’immagine.');return}}
 const reason=action==='NON_PILASTRO'?(document.getElementById('negativeReason').value||null):null;
 appendEvent({{event_type:'CANDIDATE_DECISION',candidate_id:c.candidate_id,action,reason,terminal:true}});
 setStatus(action==='INQUADRATO_MALE'?'Positivo registrato: inquadratura da correggere.':'Scelta registrata.');
 if(TERMINAL.has(action))advance();
}}
function undoLast(){{
 const target=lastEffectiveEvent();if(!target){{setStatus('Nessuna scelta da annullare.');return}}
 appendEvent({{event_type:'UNDO_LAST',undoes_event_id:target.event_id,candidate_id:target.candidate_id,terminal:false}});
 const idx=MANIFEST.candidates.findIndex(c=>c.candidate_id===target.candidate_id);if(idx>=0)model.index=idx;saveModel();pickMode=false;render();setStatus('Ultima scelta annullata; lo storico resta append-only.');
}}
function normalizedPoint(evt,img){{const r=img.getBoundingClientRect();return {{x:Math.max(0,Math.min(1,(evt.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(evt.clientY-r.top)/r.height))}}}}
function pickAdditional(evt){{if(!pickMode)return;if(evt.pointerType==='mouse'&&evt.button!==0)return;evt.preventDefault();const img=document.getElementById('evidence');const p=normalizedPoint(evt,img);appendEvent({{event_type:'ADDITIONAL_OCCURRENCE',candidate_id:current().candidate_id,action:'ALTRO_PILASTRO',point:p,terminal:false}});pickMode=false;render();setStatus('Altro pilastro registrato e marcato. Ora valuta il candidato evidenziato in rosso.')}}
function exportBundle(){{
 const bundle={{schema_version:'cew-mobile-review-bundle-v1',review_id:MANIFEST.review_id,source:MANIFEST.source,candidate_ids:MANIFEST.candidates.map(c=>c.candidate_id),events:model.events,authority:AUTHORITY,canonical_write_authorized:false,canonical_write_performed:false}};
 const blob=new Blob([JSON.stringify(bundle,null,2)],{{type:'application/json'}}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=MANIFEST.review_id+'-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),0);setStatus('Revisione esportata in JSON.');
}}
document.querySelectorAll('.primary-action').forEach(b=>b.addEventListener('click',()=>decide(b.dataset.action)));
document.getElementById('evidence').addEventListener('pointerup',pickAdditional);
document.getElementById('undo').addEventListener('click',undoLast);
document.getElementById('export').addEventListener('click',exportBundle);
render();
</script>
</body>
</html>'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    content = build_html(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
