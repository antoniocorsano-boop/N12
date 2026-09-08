#!/usr/bin/env python3
"""Human-facing content refinement for CEW Professional Document Workbench MATURE_V1.

This layer changes only presentation copy and visual emphasis inside the already
validated professional panel topology. It preserves the mature shell, acquisition
engine, runtime recovery, provenance, teaching gates and authority boundaries.
Technical runtime state remains available as hover/title diagnostics rather than
being the primary operator-facing language.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_mature_panels as mature


_CONTENT_STYLE = r'''<style id="cew-mature-content-style">
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] header .provider{
  max-width:360px;
  padding:2px 0;
  border:0;
  background:transparent;
  color:#6b7780;
  font-size:10px;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] header small{
  max-width:560px;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] #preview{
  background:#eef2f4;
  color:#33434e;
  border:1px solid #cbd4db;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] #intake-message{
  color:#66737d;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] .viewer-placeholder{
  max-width:440px;
  padding:22px 24px;
  line-height:1.5;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] .cew-editor-pill{
  letter-spacing:.01em;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] .cew-statusbar{
  gap:0;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] .cew-statusbar span{
  padding:0 10px;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] #preview-pan[aria-pressed="true"]{
  background:#44515b!important;
  box-shadow:inset 0 0 0 1px #8bc4e8!important;
}
body.cew-professional-document[data-cew-panel-content="hva-refined-v1"] #preview-pan[data-pan-dragging="1"]{
  background:#53636f!important;
}
</style>'''


_CONTENT_SCRIPT = r'''<script id="cew-mature-content-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
let syncPending=false;
const panState={active:true,drag:null,x:0,y:0};
const CODE_LABELS={
  LINEAR_STROKE_GROUP:'Gruppo lineare',
  LINE_GROUP:'Gruppo lineare',
  POLYLINE_GROUP:'Gruppo polilinea',
  TEXT_GROUP:'Gruppo testuale',
  IMAGE_REGION:'Regione immagine',
  SQUAREISH:'Forma compatta',
  WIDE:'Forma orizzontale',
  TALL:'Forma verticale',
  LARGE:'Area grande',
  MEDIUM:'Area media',
  SMALL:'Area piccola'
};

function setText(el,text){if(el&&el.textContent!==text)el.textContent=text}
function setAttr(el,name,value){if(el&&el.getAttribute(name)!==String(value))el.setAttribute(name,String(value))}
function clamp(n,min,max){return Math.min(max,Math.max(min,Number(n)||0))}
function humanCode(raw){const value=String(raw||'').trim();return CODE_LABELS[value]||value.toLowerCase().replaceAll('_',' ')}

function sourceLabel(raw){
  const value=String(raw||'').trim();
  if(!value||value==='—'||value==='NESSUNA_SESSIONE')return '—';
  if(value.includes('UNREGISTERED')||value.includes('PREVIEW'))return 'PDF locale';
  if(value.includes('GOVERN')||value.includes('REGISTER')||value==='READY')return 'governata';
  return value.toLowerCase().replaceAll('_',' ');
}

function refineHeader(){
  document.title='CEW — Analisi documentale';
  setText(document.querySelector('header h1'),'CEW — Analisi documentale');
  setText(document.querySelector('header small'),'Documento → elementi grafici → gruppi candidati → verifica umana.');
  const provider=ce('provider');if(!provider)return;
  const raw=provider.textContent.trim();
  if(raw.startsWith('Analisi grafica:'))return;
  if(raw)provider.title=raw;
  const text=/READY/.test(raw)
    ? 'Analisi grafica: pronta · classificazione automatica: non attiva'
    : /caricamento stato/i.test(raw)
      ? 'Analisi grafica: verifica in corso…'
      : 'Analisi grafica: stato da verificare · classificazione automatica: non attiva';
  setText(provider,text);
}

function refineSourceOptions(){
  const source=ce('source');if(!source)return;
  for(const option of source.options){
    const raw=option.textContent.trim();
    if(!option.value){setText(option,'Apri fonte governata…');continue}
    const match=raw.match(/^(.*?)\s·\s(\d+)\sPage READY$/i);
    if(match){
      const count=Number(match[2]);
      setText(option,`${match[1]} · ${count} ${count===1?'pagina disponibile':'pagine disponibili'}`);
    }
  }
}

function refinedIntakeCopy(raw){
  let text=String(raw||'').trim();
  if(!text)return text;
  if(/^Seleziona un PDF\./i.test(text))return 'Apri una fonte governata oppure scegli un PDF locale.';
  if(/^Preview PDF: massimo /i.test(text)){
    const limit=text.match(/massimo\s+([0-9.]+\sMB)/i)?.[1];
    return `Apri una fonte governata oppure scegli un PDF locale${limit?` · limite ${limit}`:''}.`;
  }
  text=text.replaceAll('Preview PDF','Analizza PDF');
  text=text.replaceAll('Preview completata','Analisi completata');
  text=text.replaceAll('Preview inconcludente','Analisi inconcludente');
  text=text.replaceAll('pronto per la preview','pronto per l’analisi');
  text=text.replace(/\s*[.;]?\s*Training (?:bloccato|consentito)\.?/gi,'.');
  text=text.replace(/;\s*training bloccato\.?/gi,'.');
  text=text.replace(/\s+\./g,'.').replace(/\.\.+/g,'.');
  return text;
}

function refineIntake(){
  refineSourceOptions();
  const preview=ce('preview');
  setText(preview,'Analizza PDF');
  setAttr(preview,'aria-label','Analizza PDF locale');
  const analyze=ce('analyze');setAttr(analyze,'aria-label','Analizza fonte governata');
  const message=ce('intake-message');if(message)setText(message,refinedIntakeCopy(message.textContent));
}

function applyPanOffset(){
  const wrap=ce('page')?.closest('.pagewrap');
  if(!wrap)return;
  wrap.style.translate=`${Math.round(panState.x)}px ${Math.round(panState.y)}px`;
}
function resetPan(){panState.x=0;panState.y=0;applyPanOffset()}
function syncPanButton(){
  const button=ce('preview-pan'),viewer=ce('viewer');if(!button||!viewer)return;
  setAttr(button,'aria-pressed',panState.active?'true':'false');
  setAttr(button,'aria-label',panState.active?'Pan attivo: trascina per spostare la tavola':'Attiva Pan');
  button.title=panState.active?'Pan attivo · trascina la tavola':'Attiva Pan';
  viewer.dataset.cewPanMode=panState.active?'active':'inactive';
  if(!panState.drag)viewer.style.cursor=panState.active?'grab':'default';
}
function setPanActive(active){panState.active=!!active;panState.drag=null;syncPanButton()}

function wireTruePan(){
  const viewer=ce('viewer');if(!viewer||viewer.dataset.cewTruePan==='1')return;
  viewer.dataset.cewTruePan='1';
  viewer.addEventListener('pointerdown',e=>{
    if(e.button!==0||e.target.closest('#preview-view-controls')||e.target.closest('.cluster-hotspot'))return;
    if(ce('page')?.hidden)return;
    if(!panState.active){e.stopImmediatePropagation();return}
    e.preventDefault();e.stopImmediatePropagation();
    panState.drag={
      id:e.pointerId,x:e.clientX,y:e.clientY,
      left:viewer.scrollLeft,top:viewer.scrollTop,
      panX:panState.x,panY:panState.y
    };
    try{viewer.setPointerCapture?.(e.pointerId)}catch(_){}
    viewer.style.cursor='grabbing';
    const button=ce('preview-pan');if(button)button.dataset.panDragging='1';
  },true);
  viewer.addEventListener('pointermove',e=>{
    const d=panState.drag;if(!d||d.id!==e.pointerId)return;
    e.preventDefault();e.stopImmediatePropagation();
    const dx=e.clientX-d.x,dy=e.clientY-d.y;
    const maxLeft=Math.max(0,viewer.scrollWidth-viewer.clientWidth);
    const maxTop=Math.max(0,viewer.scrollHeight-viewer.clientHeight);
    const nextLeft=clamp(d.left-dx,0,maxLeft),nextTop=clamp(d.top-dy,0,maxTop);
    viewer.scrollLeft=nextLeft;viewer.scrollTop=nextTop;
    panState.x=d.panX+dx+(nextLeft-d.left);
    panState.y=d.panY+dy+(nextTop-d.top);
    applyPanOffset();
  },true);
  const end=e=>{
    const d=panState.drag;if(!d||d.id!==e.pointerId)return;
    e.preventDefault();e.stopImmediatePropagation();
    try{viewer.releasePointerCapture?.(e.pointerId)}catch(_){}
    panState.drag=null;viewer.style.cursor=panState.active?'grab':'default';
    const button=ce('preview-pan');if(button)button.dataset.panDragging='0';
  };
  viewer.addEventListener('pointerup',end,true);
  viewer.addEventListener('pointercancel',end,true);
}

function ensurePanControl(){
  const bar=ce('preview-view-controls');if(!bar)return;
  let button=ce('preview-pan');
  if(!button){
    button=document.createElement('button');button.id='preview-pan';button.type='button';button.className='secondary';button.textContent='✋';
    const after=ce('preview-overview');
    if(after?.nextSibling)bar.insertBefore(button,after.nextSibling);else bar.appendChild(button);
    button.onclick=e=>{e.preventDefault();e.stopPropagation();setPanActive(!panState.active)};
  }
  for(const id of ['preview-overview','preview-width']){
    const fit=ce(id);if(!fit||fit.dataset.cewPanReset==='1')continue;
    fit.dataset.cewPanReset='1';fit.addEventListener('click',resetPan,true);
  }
  const img=ce('page');
  if(img&&img.dataset.cewPanLoadReset!=='1'){
    img.dataset.cewPanLoadReset='1';img.addEventListener('load',resetPan);
  }
  wireTruePan();syncPanButton();
}

function refineEditor(){
  const label=ce('cew-editor-label');
  if(label&&label.textContent.trim()==='Nessun documento')setText(label,'Nessuna fonte aperta');
  const evidence=ce('cew-editor-evidence');
  if(evidence){
    const raw=evidence.textContent.trim();
    const counts=raw.match(/^(\d+) PR · (\d+) CL$/);
    if(counts)setText(evidence,`${counts[1]} elementi · ${counts[2]} gruppi`);
    else if(raw==='NESSUNA_SESSIONE')setText(evidence,'Nessuna fonte');
    else if(raw==='VERIFICA NECESSARIA')setText(evidence,'Da verificare');
    else if(raw.includes('UNREGISTERED'))setText(evidence,'PDF locale');
  }
  setText(ce('cew-editor-authority'),'Sola lettura');
  setText(ce('cew-viewport-note'),panState.active?'Pan attivo · trascina per spostare · rotella per zoom':'Pan disattivato · rotella per zoom');
}

function refineViewerEmptyState(){
  const placeholder=ce('viewer-placeholder');if(!placeholder)return;
  setText(placeholder,'Apri una tavola per iniziare. La tavola originale resta la fonte di riferimento; CEW individuerà elementi grafici e gruppi candidati da verificare.');
}

function refineClusterCards(){
  for(const card of document.querySelectorAll('#clusters .card')){
    const strong=card.querySelector('b'),meta=card.querySelector('.meta');
    if(strong){
      const raw=strong.dataset.cewRaw||strong.textContent.trim();
      if(!strong.dataset.cewRaw)strong.dataset.cewRaw=raw;
      const match=raw.match(/^(.+?)\s·\s(\d+)$/);
      if(match){
        const count=Number(match[2]);
        setText(strong,`${humanCode(match[1])} · ${count} ${count===1?'occorrenza':'occorrenze'}`);
      }
    }
    if(meta){
      const raw=meta.dataset.cewRaw||meta.innerText.trim();
      if(!meta.dataset.cewRaw)meta.dataset.cewRaw=raw;
      const lines=raw.split(/\n+/).map(x=>x.trim()).filter(Boolean);
      const buckets=(lines[0]||'').split('·').map(x=>x.trim()).filter(Boolean);
      if(buckets.length)setText(meta,buckets.map(humanCode).join(' · '));
      card.title=raw;
    }
  }
}

function refineClusterDetails(){
  const title=ce('title');
  if(title){
    const match=title.textContent.trim().match(/^Famiglia grafica\s·\s(\d+)\soccorrenze$/i);
    if(match){const count=Number(match[1]);setText(title,`Gruppo grafico · ${count} ${count===1?'occorrenza':'occorrenze'}`)}
  }
  for(const pill of document.querySelectorAll('#detail .pill')){
    const raw=pill.dataset.cewRawCode||pill.textContent.trim();
    if(!pill.dataset.cewRawCode)pill.dataset.cewRawCode=raw;
    pill.title=raw;setText(pill,humanCode(raw));
  }
  for(const hotspot of document.querySelectorAll('.cluster-hotspot')){
    hotspot.title='Seleziona gruppo candidato';
    setAttr(hotspot,'aria-label','Seleziona gruppo candidato');
  }

  const meta=ce('cew-inspector-meta'),prov=ce('cew-provenance-meta');
  const dl=meta?.querySelector('dl'),provDl=prov?.querySelector('dl');
  if(meta?.querySelector('h4')?.textContent.trim()==='Cluster selezionato')setText(meta.querySelector('h4'),'Gruppo selezionato');
  if(!dl)return;
  const rows=[...dl.querySelectorAll('dt')];
  for(const dt of rows){
    const dd=dt.nextElementSibling;if(!dd||dd.tagName!=='DD')continue;
    const label=dt.textContent.trim();
    if(label==='Famiglia'){
      const raw=dd.dataset.cewRawCode||dd.textContent.trim();
      if(!dd.dataset.cewRawCode)dd.dataset.cewRawCode=raw;
      dd.title=raw;setText(dt,'Tipo grafico');setText(dd,humanCode(raw));
    }
    if(label==='BBox'&&provDl){
      const raw=dd.textContent.trim();
      if(!provDl.querySelector('[data-cew-bbox-label="1"]')){
        const pdt=document.createElement('dt');pdt.dataset.cewBboxLabel='1';pdt.textContent='Riquadro normalizzato';
        const pdd=document.createElement('dd');pdd.dataset.cewBboxValue='1';pdd.textContent=raw;provDl.append(pdt,pdd);
      }
      dt.remove();dd.remove();
    }
  }
}

function refineInspector(){
  setText(document.querySelector('#cew-inspector-head strong'),'Dettagli');
  const title=ce('title');
  if(title&&title.textContent.trim()==='Nessun cluster selezionato')setText(title,'Nessun elemento selezionato');
  const empty=ce('cew-inspector-meta')?.querySelector('.cew-empty');
  if(empty&&/Carica una fonte o un PDF\./i.test(empty.textContent)){
    setText(empty,'Apri una tavola e seleziona un elemento per visualizzarne proprietà e provenienza.');
  }
  refineClusterCards();refineClusterDetails();
}

function refineRailSemantics(){
  const labels={pages:'Pagine',primitives:'Elementi grafici',clusters:'Gruppi candidati',verify:'Da verificare'};
  const shortcuts={pages:'Alt+1',primitives:'Alt+2',clusters:'Alt+3',verify:'Alt+4'};
  for(const button of document.querySelectorAll('#cew-activity-rail button[data-nav]')){
    const id=button.dataset.nav||'';if(!labels[id])continue;
    setAttr(button,'aria-label',labels[id]);
    setAttr(button,'title',`${labels[id]} · ${shortcuts[id]}`);
  }
}

function refineStatusBar(){
  const bar=ce('cew-statusbar');if(!bar)return;
  const raw=bar.textContent.replace(/\s+/g,' ').trim();
  if(!raw||(!raw.includes('Renderer')&&!raw.includes('Training')&&!raw.includes('Rot ')))return;
  bar.title=raw;
  const spans=[...bar.querySelectorAll(':scope > span')];
  const pick=prefix=>spans.find(span=>span.textContent.trim().startsWith(prefix))?.querySelector('strong')?.textContent.trim()||'—';
  const page=pick('Pagina'),zoom=pick('Zoom'),primitive=pick('Primitive'),cluster=pick('Cluster'),source=sourceLabel(pick('Fonte'));
  bar.innerHTML=`<span>Pagina <strong>${page}</strong></span><span>Zoom <strong>${zoom}</strong></span><span>Elementi <strong>${primitive}</strong></span><span>Gruppi <strong>${cluster}</strong></span><span>Fonte <strong>${source}</strong></span>`;
}

function syncAll(){
  document.body.dataset.cewPanelContent='hva-refined-v1';
  refineHeader();refineIntake();ensurePanControl();refineEditor();refineViewerEmptyState();refineInspector();refineRailSemantics();refineStatusBar();
}
function scheduleSync(){if(syncPending)return;syncPending=true;requestAnimationFrame(()=>{syncPending=false;syncAll()})}

syncAll();
const observer=new MutationObserver(scheduleSync);
observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['class','hidden']});
window.addEventListener('resize',scheduleSync,{passive:true});
})();
</script>'''


def _patched_page() -> str:
    html = mature._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_MATURE_CONTENT_HTML_MARKER_MISSING")
    html = html.replace("</head>", _CONTENT_STYLE + "</head>", 1)
    html = html.replace("</body>", _CONTENT_SCRIPT + "</body>", 1)
    return html


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def mature_content_page():
        return HTMLResponse(
            _patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Document-Workbench": "PROFESSIONAL_V2",
                "X-CEW-Panel-Architecture": "ACTIVITY_PRIMARY_EDITOR_AUXILIARY_STATUS",
                "X-CEW-Panel-Quality": "MATURE_V1",
                "X-CEW-Panel-Content": "HVA_REFINED_V1",
                "X-CEW-Preview-Runtime-Recovery": "BROWSER_RECONSTRUCT_V1",
            },
        )

    return router
