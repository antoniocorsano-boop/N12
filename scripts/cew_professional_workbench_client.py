#!/usr/bin/env python3
from __future__ import annotations

import html
import json


CLIENT_MARKERS = {
    "authority": "canonical_write_authorized=false",
    "source_viewer": "F3_DZI_OPENSEADRAGON_REUSED",
    "technical_scene": "WORKBENCH_SCENE_OBJECTS_RENDERED_AS_SVG",
    "semantic_sync": "EXPLICIT_EVIDENCE_LINK_ONLY",
    "overlay": "OVERLAY_DISABLED_WITHOUT_VERIFIED_REGISTRATION",
    "working_edit": "OBJECT_ANCHORED_NON_CANONICAL_WORKING_EDIT",
    "reading_issue": "GRAPHICALLY_ANCHORED_NON_CANONICAL_READING_ISSUE",
    "disclosure": "WORK_EVIDENCE_PROVENANCE",
}


def build_client(task_id: str) -> str:
    task_label = html.escape(task_id, quote=True)
    task_json = json.dumps(task_id, ensure_ascii=False)
    return HTML.replace("__TASK_LABEL__", task_label).replace("__TASK_JSON__", task_json)


HTML = r'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CEW — Ambiente grafico professionale · __TASK_LABEL__</title>
<script src="/workbench/assets/source-viewer/vendor/openseadragon/openseadragon.min.js"></script>
<style>
:root{--ink:#17202a;--muted:#64717d;--line:#cfd6dc;--paper:#fff;--bg:#e9edf1;--accent:#173f5f;--accent2:#245b7a;--warn:#8a4b08;--danger:#9b2c2c;--ok:#286044;--canvas:#20262c;--focus:#ffbf47}
*{box-sizing:border-box}html,body{height:100%;margin:0}body{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg);display:flex;flex-direction:column;overflow:hidden}button,a,input,select,textarea{font:inherit}button,.button{border:1px solid #aeb9c2;background:#fff;color:var(--ink);border-radius:6px;padding:7px 10px;font-weight:700;cursor:pointer}.button{text-decoration:none;display:inline-flex;align-items:center}.primary{background:var(--accent);color:#fff;border-color:var(--accent)}button[disabled]{opacity:.52;cursor:not-allowed}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,[tabindex]:focus-visible{outline:3px solid var(--focus);outline-offset:2px}.app-header{background:#fff;border-bottom:1px solid var(--line);padding:8px 12px;display:flex;gap:12px;align-items:center;min-height:52px}.crumb{font-size:12px;color:var(--muted);white-space:nowrap}.title{font-weight:800;min-width:160px}.modebar,.tools{display:flex;gap:5px;align-items:center;flex-wrap:wrap}.modebar{margin-left:auto}.modebar button[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}.tools{background:#f7f9fa;border-bottom:1px solid var(--line);padding:6px 10px}.tools .separator{height:25px;width:1px;background:var(--line);margin:0 3px}.tools .spacer{flex:1}.status-chip{font-size:12px;border:1px solid var(--line);border-radius:999px;padding:5px 8px;background:#fff}.status-chip.warn{border-color:#d8aa72;background:#fff8ef}.workspace{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) 0;min-height:0;flex:1;transition:grid-template-columns .18s ease}.workspace.inspector-open{grid-template-columns:minmax(0,1fr) minmax(0,1fr) minmax(280px,360px)}.pane{position:relative;min-width:0;min-height:0;background:var(--canvas);border-right:1px solid #111}.pane[hidden]{display:none!important}.pane-head{position:absolute;z-index:20;left:10px;top:10px;background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:6px;padding:5px 8px;font-size:12px;font-weight:800;box-shadow:0 2px 8px rgba(0,0,0,.12)}#sourceViewport{width:100%;height:100%;background:#1f2429}#technicalViewport{width:100%;height:100%;display:block;background:#f6f7f8}.technical-object{stroke:#273746;stroke-width:2.2;vector-effect:non-scaling-stroke;cursor:pointer}.technical-object.document{stroke:#445d6e}.technical-object.structural{stroke:#173f5f;stroke-width:4}.technical-object.candidate{stroke-dasharray:8 5}.technical-object.selected{stroke:#a12622;stroke-width:6}.technical-object:focus{stroke:#a12622;stroke-width:6}.issue-marker{fill:#fff;stroke:#8a4b08;stroke-width:3;vector-effect:non-scaling-stroke}.issue-label{font-size:22px;font-weight:900;fill:#8a4b08;pointer-events:none}.empty-state{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:40px;color:#4d5963;text-align:center;background:#f6f7f8}.source-error{position:absolute;inset:50px 15px auto 15px;z-index:30;background:#fff7e8;border-left:5px solid var(--warn);padding:10px;display:none}.inspector{background:#fff;border-left:1px solid var(--line);overflow:auto;min-width:0}.inspector-inner{padding:14px;display:none}.workspace.inspector-open .inspector-inner{display:block}.inspector h2{font-size:17px;margin:4px 0 10px}.inspector h3{font-size:14px;margin:16px 0 7px}.eyebrow{font-size:11px;font-weight:850;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}.state{display:inline-flex;font-size:11px;font-weight:800;border:1px solid var(--line);border-radius:999px;padding:3px 7px}.property-grid{display:grid;grid-template-columns:minmax(95px,.7fr) minmax(0,1.3fr);gap:6px 8px;font-size:12px}.property-grid dt{font-weight:750;color:var(--muted)}.property-grid dd{margin:0;overflow-wrap:anywhere}.inspector details{border-top:1px solid #e6eaed;padding-top:9px;margin-top:11px}.inspector summary{cursor:pointer;font-weight:800}.inspector textarea,.inspector input,.inspector select{width:100%;border:1px solid #b9c3ca;border-radius:6px;padding:8px;margin:5px 0 8px}.receipt{background:#edf8f1;border-left:4px solid var(--ok);padding:8px;font-size:12px;overflow-wrap:anywhere}.authority-note{background:#fff7e8;border-left:4px solid var(--warn);padding:8px;font-size:12px}.bottom-status{background:#fff;border-top:1px solid var(--line);min-height:34px;padding:6px 10px;display:flex;gap:14px;align-items:center;font-size:12px;color:var(--muted)}.bottom-status strong{color:var(--ink)}.layer-pop{position:absolute;right:10px;top:96px;z-index:40;background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px;width:250px;box-shadow:0 8px 30px rgba(0,0,0,.18);display:none}.layer-pop.open{display:block}.layer-pop label{display:flex;align-items:flex-start;gap:8px;margin:7px 0;font-size:12px}.layer-pop small{display:block;color:var(--muted)}.mode-source .technical-pane{display:none}.mode-source .workspace{grid-template-columns:minmax(0,1fr) 0 0}.mode-source .workspace.inspector-open{grid-template-columns:minmax(0,1fr) 0 minmax(280px,360px)}.mode-technical .source-pane{display:none}.mode-technical .workspace{grid-template-columns:0 minmax(0,1fr) 0}.mode-technical .workspace.inspector-open{grid-template-columns:0 minmax(0,1fr) minmax(280px,360px)}.mode-split .source-pane,.mode-split .technical-pane{display:block}.mobile-switch{display:none}
@media(max-width:900px){.app-header{align-items:flex-start;flex-wrap:wrap}.modebar{margin-left:0}.workspace,.workspace.inspector-open{grid-template-columns:minmax(0,1fr) 0 0}.workspace .technical-pane{display:none}.workspace.mobile-tech{grid-template-columns:0 minmax(0,1fr) 0}.workspace.mobile-tech .source-pane{display:none}.workspace.mobile-tech .technical-pane{display:block}.workspace.inspector-open{grid-template-columns:minmax(0,1fr) 0 0}.workspace.inspector-open .inspector{position:absolute;right:0;top:102px;bottom:34px;width:min(92vw,380px);z-index:60;box-shadow:-8px 0 30px rgba(0,0,0,.25)}.mobile-switch{display:flex}.tools .desktop-only{display:none}}
</style>
</head>
<body data-canonical-write-authorized="false" data-engineering-authority-effect="NONE" data-client-contract="PROFESSIONAL_WORKBENCH_CLIENT_V1">
<header class="app-header">
  <a class="button" href="/" aria-label="Torna al progetto">← Progetto</a>
  <div><div class="crumb">Progetto N12 › Evidenza › __TASK_LABEL__</div><div class="title">Ambiente grafico professionale</div></div>
  <nav class="modebar" aria-label="Modalità di visualizzazione">
    <button data-mode="SOURCE" aria-pressed="false">Fonte</button>
    <button data-mode="TECHNICAL" aria-pressed="false">Tecnica</button>
    <button data-mode="SPLIT" aria-pressed="true">Divisa</button>
    <button id="overlayMode" data-mode="OVERLAY" aria-pressed="false" disabled title="Richiede registrazione spaziale verificata">Sovrapposta</button>
  </nav>
</header>
<div class="tools" role="toolbar" aria-label="Strumenti di lavoro">
  <button id="zoomIn" title="Ingrandisci la fonte">＋</button><button id="zoomOut" title="Riduci la fonte">−</button>
  <button id="fitRegion">Centra evidenza</button><button id="fitDrawing">Intera tavola</button>
  <button id="rotateLeft" aria-label="Ruota la fonte di 90 gradi in senso antiorario">↺ 90°</button><button id="rotateRight" aria-label="Ruota la fonte di 90 gradi in senso orario">↻ 90°</button>
  <span class="separator"></span>
  <span id="syncStatus" class="status-chip">Sincronizzazione: caricamento…</span>
  <button id="layersButton" aria-expanded="false">Livelli</button>
  <button id="issuesButton">Questione</button>
  <div class="mobile-switch"><button id="mobileSource">Fonte</button><button id="mobileTech">Tecnica</button></div>
  <span class="spacer"></span>
  <a id="pdfLink" class="button desktop-only" href="#" target="_blank" rel="noopener">PDF verificato</a>
</div>
<div id="layerPop" class="layer-pop" aria-label="Gestione livelli">
  <strong>Livelli</strong>
  <label><input id="layerLinework" type="checkbox" checked> <span>Geometria documentale<small id="lineworkReason"></small></span></label>
  <label><input id="layerStructural" type="checkbox" checked> <span>Oggetti strutturali governati<small id="structuralReason"></small></span></label>
  <label><input id="layerIssues" type="checkbox" checked> <span>Questioni di lettura<small>Stato di sessione non canonico</small></span></label>
  <label><input id="layerEdits" type="checkbox" checked disabled> <span>Proposte di modifica<small>Visibili quando disponibili</small></span></label>
</div>
<main id="workspace" class="workspace">
  <section class="pane source-pane" aria-label="Fonte verificata">
    <div class="pane-head">FONTE VERIFICATA</div>
    <div id="sourceError" class="source-error"></div>
    <div id="sourceViewport" tabindex="0" aria-label="Tavola sorgente con zoom e panoramica"></div>
  </section>
  <section class="pane technical-pane" aria-label="Rappresentazione tecnica">
    <div class="pane-head">RAPPRESENTAZIONE TECNICA DERIVATA</div>
    <svg id="technicalViewport" tabindex="0" role="group" aria-label="Scena tecnica selezionabile" viewBox="0 0 1000 1000"></svg>
    <div id="technicalEmpty" class="empty-state" hidden></div>
  </section>
  <aside class="inspector" aria-label="Ispettore">
    <div class="inspector-inner">
      <div class="eyebrow">Lavoro</div><h2 id="objectTitle">Nessuna selezione</h2><div id="objectState" class="state">—</div>
      <dl id="properties" class="property-grid"></dl>
      <section id="editSection" hidden><h3>Proposta di modifica</h3><div class="authority-note">La proposta modifica solo lo stato di lavoro della sessione. Fonte e dati canonici restano invariati.</div><label>Proprietà<select id="editProperty"></select></label><label>Valore proposto<input id="editValue" type="text"></label><button id="previewEdit" class="primary">Crea proposta</button><div id="editReceipt"></div></section>
      <details id="evidenceDetails"><summary>Evidenza</summary><div id="evidenceContent"></div></details>
      <details id="provenanceDetails"><summary>Provenienza</summary><div id="provenanceContent"></div></details>
      <section id="issueSection"><h3>Questione di lettura</h3><label>Domanda<textarea id="issueQuestion" placeholder="Descrivi il dato da verificare"></textarea></label><label>Stato<select id="issueState"><option>OPEN</option><option>IN_REVIEW</option><option>NOT_RESOLVABLE_FROM_CURRENT_SOURCES</option></select></label><button id="previewIssue" class="primary">Registra nella sessione</button><div id="issueReceipt"></div></section>
    </div>
  </aside>
</main>
<footer class="bottom-status"><span><strong>Fonte:</strong> <span id="sourceState">caricamento…</span></span><span><strong>Registrazione:</strong> <span id="registrationState">—</span></span><span><strong>Questioni sessione:</strong> <span id="issueCount">0</span></span><span id="modeBlocker"></span></footer>
<script>
const TASK=__TASK_JSON__;
const EDITABLE=new Set(['RecognizedText','RecognizedDimension','TechnicalObjectCandidate']);
let scene=null,viewer=null,regionOverlay=null,selected=null,issues=[],currentMode='SPLIT',renderedObjects=[];
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function jsonFetch(url,options={}){const r=await fetch(url,{cache:'no-store',...options});const body=await r.json();if(!r.ok)throw new Error(body.reason||body.state||('HTTP '+r.status));return body}
function post(url,payload){return jsonFetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})}
function registration(){return (scene?.registrations||[])[0]||null}
function showMessage(id,message){const el=$(id);el.textContent=message;el.style.display=message?'block':'none'}
function initSource(){
  if(!scene.source.managed_f3_dzi_url){showMessage('sourceError','Le tessere multirisoluzione della fonte non sono disponibili per questa revisione. Nessuna immagine sostitutiva viene inventata.');$('sourceState').textContent='non disponibile';return}
  if(typeof OpenSeadragon==='undefined'){showMessage('sourceError','Il visualizzatore multirisoluzione non è disponibile. Usa il PDF verificato.');$('sourceState').textContent='visualizzatore non disponibile';return}
  viewer=OpenSeadragon({id:'sourceViewport',prefixUrl:'/workbench/assets/source-viewer/vendor/openseadragon/images/',tileSources:scene.source.managed_f3_dzi_url,showNavigator:true,navigatorAutoFade:false,gestureSettingsMouse:{clickToZoom:false},maxZoomPixelRatio:4});
  viewer.addOnceHandler('open',()=>{fitEvidence();$('sourceState').textContent='verificata · multirisoluzione pronta'});
  $('sourceViewport').addEventListener('keydown',e=>{if(!viewer)return;const d=0.08;const p=viewer.viewport.getCenter();if(e.key==='ArrowLeft'){p.x-=d;e.preventDefault()}else if(e.key==='ArrowRight'){p.x+=d;e.preventDefault()}else if(e.key==='ArrowUp'){p.y-=d;e.preventDefault()}else if(e.key==='ArrowDown'){p.y+=d;e.preventDefault()}else if(e.key==='+'||e.key==='='){viewer.viewport.zoomBy(1.2);e.preventDefault();return}else if(e.key==='-'){viewer.viewport.zoomBy(0.8);e.preventDefault();return}else{return}viewer.viewport.panTo(p);viewer.viewport.applyConstraints()});
}
function evidenceRect(){if(!viewer||!viewer.world.getItemCount())return null;const b=scene.source.evidence_bbox_normalized,i=viewer.world.getItemAt(0),s=i.getContentSize();return i.imageToViewportRectangle(b.x*s.x,b.y*s.y,b.width*s.x,b.height*s.y)}
function fitEvidence(){const r=evidenceRect();if(!r)return;if(regionOverlay)viewer.removeOverlay(regionOverlay);regionOverlay=document.createElement('div');regionOverlay.style.cssText='border:4px solid #a12622;background:rgba(161,38,34,.10);box-sizing:border-box;pointer-events:none';regionOverlay.setAttribute('aria-label','Regione di evidenza verificata');viewer.addOverlay({element:regionOverlay,location:r});viewer.viewport.fitBounds(r,true)}
function fitDrawing(){if(viewer)viewer.viewport.goHome(true)}
function technicalSpace(objects){for(const s of ['SOURCE_PAGE_PT','TECHNICAL_2D','STRUCTURAL_MODEL_XY'])if(objects.some(o=>o.coordinate_space===s))return s;return null}
function layerVisible(obj){if(obj.object_family==='DocumentGraphicPrimitive')return $('layerLinework').checked;if(obj.object_family==='GovernedStructuralObjectProjection')return $('layerStructural').checked;return true}
function renderTechnical(){
  const svg=$('technicalViewport');svg.innerHTML='';const all=(scene.objects||[]).filter(layerVisible);const space=technicalSpace(all);const objects=space?all.filter(o=>o.coordinate_space===space&&o.geometry?.type==='LINE'):[];renderedObjects=objects;
  if(!objects.length){$('technicalEmpty').hidden=false;$('technicalEmpty').textContent='Rappresentazione tecnica non disponibile per questa evidenza/revisione. La fonte resta utilizzabile; nessuna geometria sostitutiva viene inventata.';return}$('technicalEmpty').hidden=true;
  const pts=objects.flatMap(o=>[o.geometry.a,o.geometry.b]);let minX=Math.min(...pts.map(p=>Number(p[0]))),maxX=Math.max(...pts.map(p=>Number(p[0]))),minY=Math.min(...pts.map(p=>Number(p[1]))),maxY=Math.max(...pts.map(p=>Number(p[1])));if(maxX===minX){maxX+=1;minX-=1}if(maxY===minY){maxY+=1;minY-=1}const scale=Math.min(880/(maxX-minX),880/(maxY-minY)),ox=(1000-(maxX-minX)*scale)/2,oy=(1000-(maxY-minY)*scale)/2;const map=p=>[ox+(Number(p[0])-minX)*scale,1000-(oy+(Number(p[1])-minY)*scale)];
  for(const obj of objects){const [x1,y1]=map(obj.geometry.a),[x2,y2]=map(obj.geometry.b);const line=document.createElementNS('http://www.w3.org/2000/svg','line');line.setAttribute('x1',x1);line.setAttribute('y1',y1);line.setAttribute('x2',x2);line.setAttribute('y2',y2);line.setAttribute('tabindex','0');line.setAttribute('role','button');line.setAttribute('aria-label',obj.object_family+' '+obj.object_id);line.dataset.objectId=obj.object_id;line.classList.add('technical-object',obj.object_family==='DocumentGraphicPrimitive'?'document':'structural');if(obj.binding_state==='UNBOUND')line.classList.add('candidate');line.addEventListener('click',()=>selectObject(obj));line.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();selectObject(obj)}});svg.appendChild(line)}renderIssueMarkers(map)
}
function renderIssueMarkers(map){if(!$('layerIssues').checked)return;for(const issue of issues){const obj=renderedObjects.find(o=>o.object_id===issue.anchor_object_id);if(!obj)continue;const a=map(obj.geometry.a),b=map(obj.geometry.b),cx=(a[0]+b[0])/2,cy=(a[1]+b[1])/2;const c=document.createElementNS('http://www.w3.org/2000/svg','circle');c.setAttribute('cx',cx);c.setAttribute('cy',cy);c.setAttribute('r','14');c.classList.add('issue-marker');$('technicalViewport').appendChild(c);const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',cx);t.setAttribute('y',cy+8);t.setAttribute('text-anchor','middle');t.classList.add('issue-label');t.textContent='?';$('technicalViewport').appendChild(t)}}
function familyLabel(obj){return ({DocumentGraphicPrimitive:'Geometria documentale estratta',GovernedStructuralObjectProjection:'Oggetto strutturale governato',RecognizedText:'Testo riconosciuto',RecognizedDimension:'Quota riconosciuta',TechnicalObjectCandidate:'Oggetto tecnico candidato'})[obj.object_family]||obj.object_family}
function selectObject(obj){selected=obj;for(const el of document.querySelectorAll('.technical-object'))el.classList.toggle('selected',el.dataset.objectId===obj.object_id);$('workspace').classList.add('inspector-open');$('objectTitle').textContent=familyLabel(obj);$('objectState').textContent=obj.binding_state||obj.authority_state||'DERIVATO';const props=obj.properties||{};$('properties').innerHTML=Object.entries(props).map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(typeof v==='object'?JSON.stringify(v):v)}</dd>`).join('');renderEvidence(obj);renderProvenance(obj);renderEdit(obj)}
function renderEvidence(obj){const links=(scene.evidence_links||[]).filter(l=>l.target_object_id===obj.object_id);let out=links.length?links.map(l=>`<p><b>${esc(l.link_type)}</b> · ${esc(l.binding_state||'')}</p>`).join(''):'<p>Nessun collegamento esplicito a evidenza è registrato per questo oggetto.</p>';out+=`<p><a class="button" href="/evidence/review?task=${encodeURIComponent(TASK)}">Apri evidenza sorgente</a></p>`;$('evidenceContent').innerHTML=out;if(links.length&&viewer)fitEvidence();$('syncStatus').textContent=links.length?'Sincronizzazione: semantica':'Sincronizzazione: non disponibile'}
function renderProvenance(obj){const p=obj.provenance||{};const s=scene.source;$('provenanceContent').innerHTML=`<dl class="property-grid"><dt>Oggetto</dt><dd>${esc(obj.object_id)}</dd><dt>Fonte versione</dt><dd>${esc(s.source_version_id)}</dd><dt>Pagina</dt><dd>${esc(s.page_id)}</dd><dt>Regione evidenza</dt><dd>${esc(s.evidence_region_id)}</dd><dt>Hash fonte</dt><dd>${esc(s.source_sha256)}</dd><dt>Origine proiezione</dt><dd>${esc(p.projection_origin||p.artifact_role||'—')}</dd><dt>Scrittura canonica</dt><dd>false</dd></dl>`}
function renderEdit(obj){const section=$('editSection');if(!EDITABLE.has(obj.object_family)){section.hidden=true;return}const props=Object.keys(obj.properties||{});section.hidden=!props.length;$('editProperty').innerHTML=props.map(p=>`<option>${esc(p)}</option>`).join('');if(props.length)$('editValue').value=typeof obj.properties[props[0]]==='object'?JSON.stringify(obj.properties[props[0]]):String(obj.properties[props[0]]??'')}
async function previewEdit(){if(!selected)return;const property=$('editProperty').value;try{const result=await post('/api/workbench/working-edit/preview',{task:TASK,target_object_id:selected.object_id,property_name:property,proposed_value:$('editValue').value,author_session:'browser-session',state:'DRAFT'});$('editReceipt').innerHTML=`<p class="receipt"><b>Proposta di lavoro creata.</b><br>${esc(result.working_edit_id)}<br>Scrittura canonica: false</p>`;$('layerEdits').disabled=false;$('layerEdits').checked=true}catch(e){$('editReceipt').innerHTML=`<p class="authority-note">${esc(e.message)}</p>`}}
async function previewIssue(){const q=$('issueQuestion').value.trim();if(!q){$('issueReceipt').innerHTML='<p class="authority-note">Inserisci la domanda tecnica da verificare.</p>';return}const payload={task:TASK,question:q,state:$('issueState').value,evidence_link_ids:selected?(scene.evidence_links||[]).filter(l=>l.target_object_id===selected.object_id).map(l=>l.evidence_link_id):[]};if(selected)payload.anchor_object_id=selected.object_id;else payload.anchor_geometry={coordinate_space:'SOURCE_NORMALIZED_0_1',type:'BBOX',...scene.source.evidence_bbox_normalized};try{const issue=await post('/api/workbench/reading-issue/preview',payload);issues.push(issue);$('issueCount').textContent=String(issues.length);$('issueReceipt').innerHTML=`<p class="receipt"><b>Questione ancorata nella sessione.</b><br>${esc(issue.reading_issue_id)}<br>Scrittura canonica: false</p>`;renderTechnical();$('workspace').classList.add('inspector-open')}catch(e){$('issueReceipt').innerHTML=`<p class="authority-note">${esc(e.message)}</p>`}}
async function requestMode(mode){const reg=registration();try{const result=await post('/api/workbench/view/resolve',{task:TASK,requested_mode:mode,requested_sync_mode:(scene.evidence_links||[]).length?'SEMANTIC':'OFF',registration_id:reg?.registration_id||null});applyMode(result.effective_mode,result.blocked_actions||[])}catch(e){$('modeBlocker').textContent=e.message}}
function applyMode(mode,blockers=[]){currentMode=mode;document.body.classList.remove('mode-source','mode-technical','mode-split');document.body.classList.add(mode==='SOURCE'?'mode-source':mode==='TECHNICAL'?'mode-technical':'mode-split');for(const b of document.querySelectorAll('[data-mode]'))b.setAttribute('aria-pressed',String(b.dataset.mode===mode));$('modeBlocker').textContent=blockers.length?'Limitazione: '+blockers.join(' · '):'';if(viewer)setTimeout(()=>viewer.viewport.applyConstraints(),60)}
function configureLayers(){const docCount=(scene.objects||[]).filter(o=>o.object_family==='DocumentGraphicPrimitive').length,structCount=(scene.objects||[]).filter(o=>o.object_family==='GovernedStructuralObjectProjection').length;$('lineworkReason').textContent=docCount?`${docCount} oggetti disponibili`:'Nessun oggetto pubblicabile per questa regione';$('structuralReason').textContent=structCount?`${structCount} oggetti disponibili`:'Nessun oggetto governato collegato';$('layerLinework').disabled=!docCount;$('layerStructural').disabled=!structCount}
async function boot(){
  try{scene=await jsonFetch('/api/workbench/scene?task='+encodeURIComponent(TASK))}catch(e){showMessage('sourceError','Scena professionale non disponibile: '+e.message);$('technicalEmpty').hidden=false;$('technicalEmpty').textContent='Scena tecnica non disponibile. Nessuna geometria viene ricostruita per continuità visiva.';$('sourceState').textContent='errore di scena';return}
  $('pdfLink').href='/api/source/pdf/'+encodeURIComponent(scene.source.source_id);const reg=registration();$('registrationState').textContent=reg?.state||'UNAVAILABLE';$('overlayMode').disabled=true;$('overlayMode').title=reg?.state==='VERIFIED'?'Modalità sovrapposta ancora bloccata in questo candidato: renderer registrato non validato':'Richiede registrazione spaziale verificata';$('syncStatus').textContent=(scene.evidence_links||[]).length?'Sincronizzazione: semantica':'Sincronizzazione: non disponibile';configureLayers();initSource();renderTechnical();requestMode('SPLIT')
}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{if(!b.disabled)requestMode(b.dataset.mode)}));
$('zoomIn').onclick=()=>viewer&&viewer.viewport.zoomBy(1.2);$('zoomOut').onclick=()=>viewer&&viewer.viewport.zoomBy(.8);$('fitRegion').onclick=fitEvidence;$('fitDrawing').onclick=fitDrawing;$('rotateLeft').onclick=()=>viewer&&viewer.viewport.setRotation((viewer.viewport.getRotation()-90)%360);$('rotateRight').onclick=()=>viewer&&viewer.viewport.setRotation((viewer.viewport.getRotation()+90)%360);
$('layersButton').onclick=()=>{const p=$('layerPop');p.classList.toggle('open');$('layersButton').setAttribute('aria-expanded',String(p.classList.contains('open')))};['layerLinework','layerStructural','layerIssues'].forEach(id=>$(id).addEventListener('change',renderTechnical));
$('issuesButton').onclick=()=>{$('workspace').classList.add('inspector-open');$('issueQuestion').focus()};$('previewIssue').onclick=previewIssue;$('previewEdit').onclick=previewEdit;$('editProperty').onchange=()=>{if(selected){const v=selected.properties[$('editProperty').value];$('editValue').value=typeof v==='object'?JSON.stringify(v):String(v??'')}};
$('mobileSource').onclick=()=>$('workspace').classList.remove('mobile-tech');$('mobileTech').onclick=()=>$('workspace').classList.add('mobile-tech');
boot();
</script>
</body>
</html>'''


if __name__ == "__main__":
    print(build_client("ERW-N12-001"))
