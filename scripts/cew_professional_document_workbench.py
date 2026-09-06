#!/usr/bin/env python3
"""Consolidated professional panel shell for CEW Document Discovery.

This module changes only the human inspection surface. It reuses the validated
async/bounded Document Discovery HTML and APIs, then composes a stable workbench
shell inspired by mature editor/agent workspaces: activity rail, resizable
primary sidebar, flexible document editor, resizable auxiliary inspector, and
persistent status bar.

No acquisition, semantic, learning, SourceVersion/Page, or canonical-write
boundary is changed here.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_document_discovery_async_preview as async_preview


_PROFESSIONAL_STYLE = r'''<style id="cew-professional-document-style">
:root{
  --cew-rail:46px;
  --cew-left:292px;
  --cew-right:336px;
  --cew-sash:4px;
  --cew-status:26px;
  --cew-title:44px;
  --cew-panel:#f8f9fb;
  --cew-panel-strong:#ffffff;
  --cew-border:#d5dbe1;
  --cew-border-dark:#303941;
  --cew-ink:#1f2932;
  --cew-muted:#66737d;
  --cew-select:#17628d;
  --cew-select-soft:#e5f1f8;
  --cew-canvas:#cfd6dc;
  --cew-rail-bg:#20272d;
  --cew-rail-hover:#313b43;
  --cew-warning:#7b5200;
  --cew-warning-bg:#fff3d3;
}
*{box-sizing:border-box}
body.cew-professional-document{
  margin:0;
  width:100vw;
  height:100vh;
  overflow:hidden;
  display:grid;
  grid-template-rows:auto auto minmax(0,1fr) var(--cew-status);
  background:#eef1f3;
  color:var(--cew-ink);
}
body.cew-professional-document header{
  min-height:var(--cew-title);
  padding:5px 10px 5px 12px;
  display:flex;
  align-items:center;
  gap:14px;
  background:#f8f9fa;
  border-bottom:1px solid var(--cew-border);
  min-width:0;
}
.cew-title-main{display:flex;align-items:baseline;gap:12px;min-width:0;flex:1}
body.cew-professional-document header h1{font-size:15px;margin:0;white-space:nowrap}
body.cew-professional-document header small{font-size:11px;color:var(--cew-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
body.cew-professional-document .provider{
  flex:0 1 auto;
  max-width:42vw;
  padding:3px 7px;
  border:1px solid var(--cew-border);
  border-radius:5px;
  background:#fff;
  color:#596772;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
  font-size:10px;
}
body.cew-professional-document .intake{
  display:grid;
  grid-template-columns:minmax(170px,230px) minmax(180px,270px) auto minmax(230px,1fr) auto;
  gap:6px;
  align-items:center;
  padding:6px 8px;
  background:#fff;
  border-bottom:1px solid var(--cew-border);
}
body.cew-professional-document .intake input[type=text],
body.cew-professional-document .intake select{height:34px;min-width:0;padding:6px 8px;border-radius:5px}
body.cew-professional-document .intake input[type=file]{min-width:0;max-width:100%;font-size:12px}
body.cew-professional-document .intake button{height:34px;padding:6px 11px;border-radius:5px}
body.cew-professional-document .intake-status{
  grid-column:1/-1;
  min-height:25px;
  padding:4px 7px;
  border-radius:5px;
  font-size:11px;
  line-height:1.3;
}
body.cew-professional-document .layout{
  display:grid;
  grid-template-columns:var(--cew-rail) var(--cew-left-column,var(--cew-left)) var(--cew-left-sash,var(--cew-sash)) minmax(420px,1fr) var(--cew-right-sash,var(--cew-sash)) var(--cew-right-column,var(--cew-right));
  grid-template-rows:minmax(0,1fr);
  height:auto;
  min-height:0;
  min-width:0;
  background:var(--cew-panel);
}
body.cew-professional-document aside{min-width:0;min-height:0;padding:0;background:var(--cew-panel-strong);overflow:hidden}
body.cew-professional-document aside.left{display:flex;flex-direction:column;border:0}
body.cew-professional-document aside.right{display:flex;flex-direction:column;border:0}
.cew-activity-rail{
  grid-column:1;
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:3px;
  min-width:0;
  padding:6px 5px;
  background:var(--cew-rail-bg);
  border-right:1px solid #11181d;
}
.cew-activity-rail button{
  width:34px;height:34px;min-width:34px;padding:0;
  border:0;border-radius:5px;background:transparent;color:#cfd8de;
  font-size:12px;font-weight:750;line-height:34px;position:relative;
}
.cew-activity-rail button:hover{background:var(--cew-rail-hover);color:#fff}
.cew-activity-rail button.active{background:#3a4650;color:#fff}
.cew-activity-rail button.active:before{content:'';position:absolute;left:-5px;top:7px;bottom:7px;width:2px;background:#6db0d9;border-radius:2px}
.cew-primary-head,.cew-inspector-head{
  height:34px;display:flex;align-items:center;gap:6px;padding:0 8px;
  border-bottom:1px solid var(--cew-border);background:#f5f7f9;flex:0 0 auto;
}
.cew-primary-head strong,.cew-inspector-head strong{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#4f5d67;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cew-panel-action{width:26px;height:26px;min-width:26px;padding:0;border:0;border-radius:4px;background:transparent;color:#52616c;font-weight:800}
.cew-panel-action:hover{background:#e5eaee}
.cew-primary-content{min-width:0;min-height:0;overflow:auto;padding:8px;flex:1}
.cew-nav-panel[hidden]{display:none!important}
.cew-sidebar-title{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:11px;font-weight:800;letter-spacing:.07em;color:#56636d;text-transform:uppercase;margin:2px 0 8px}
.cew-count{display:inline-flex;min-width:22px;height:18px;align-items:center;justify-content:center;padding:0 6px;border-radius:9px;background:#e6ebef;color:#53616b;font-size:10px;font-weight:750}
.cew-page-row,.cew-summary-row{width:100%;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:7px 8px;border:1px solid transparent;border-radius:5px;background:transparent;margin:0 0 3px;text-align:left;color:var(--cew-ink)}
.cew-page-row:hover,.cew-summary-row:hover{background:#eef2f5}.cew-page-row.active{background:var(--cew-select-soft);border-color:#9fc7de;color:#174f70}
.cew-kv{display:grid;grid-template-columns:minmax(82px,.8fr) minmax(0,1.25fr);gap:5px 9px;font-size:11px;line-height:1.38}
.cew-kv dt{color:#6a7780}.cew-kv dd{margin:0;font-weight:650;overflow-wrap:anywhere}
.cew-empty{padding:18px 8px;color:#6b7780;font-size:11px;text-align:center;line-height:1.45}
.cew-meta-note{padding:7px 8px;border-radius:5px;background:#f0f3f5;color:#66737d;font-size:10px;line-height:1.4}
.cew-sash{position:relative;background:#e5e9ed;cursor:col-resize;z-index:12;outline:none}
.cew-sash:after{content:'';position:absolute;top:0;bottom:0;left:1px;width:2px;background:transparent}
.cew-sash:hover:after,.cew-sash.dragging:after,.cew-sash:focus-visible:after{background:#4b9ac7}
.cew-canvas-shell{grid-column:4;display:grid;grid-template-rows:34px minmax(0,1fr);position:relative;min-width:0;min-height:0;overflow:hidden;background:var(--cew-canvas)}
.cew-editor-bar{display:flex;align-items:center;gap:8px;min-width:0;padding:0 7px;border-bottom:1px solid #b8c1c8;background:#f6f8f9;color:#42515c;font-size:11px}
.cew-editor-tab{display:flex;align-items:center;gap:6px;min-width:0;height:100%;padding:0 9px;border-left:1px solid #d8dee3;border-right:1px solid #d8dee3;background:#fff}
.cew-editor-tab strong{font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:48vw}
.cew-editor-meta{display:flex;align-items:center;gap:5px;margin-left:auto;min-width:0}
.cew-editor-pill{display:inline-flex;align-items:center;height:20px;padding:0 6px;border-radius:10px;background:#e7ecef;color:#53616c;font-size:9px;font-weight:750;white-space:nowrap}
.cew-editor-actions{display:flex;gap:2px;margin-left:4px}
body.cew-professional-document #viewer{
  grid-row:2;
  width:100%;height:100%;min-width:0;min-height:0;
  overflow:auto;background:var(--cew-canvas);padding:14px 14px 34px;
  justify-content:center;align-items:flex-start;cursor:grab;
}
body.cew-professional-document #viewer:active{cursor:grabbing}
body.cew-professional-document .pagewrap img{box-shadow:0 3px 18px #0004}
#preview-view-controls{
  position:absolute!important;z-index:18!important;left:8px!important;top:42px!important;right:auto!important;
  display:flex!important;flex-direction:column!important;flex-wrap:nowrap!important;justify-content:flex-start!important;gap:2px!important;
  width:36px!important;max-width:36px!important;padding:3px!important;background:#20272ded!important;border:1px solid #11181d!important;
  border-radius:6px!important;box-shadow:0 2px 8px #0004!important;transform:none!important;
}
#preview-view-controls button{width:28px!important;height:28px!important;min-width:28px!important;padding:0!important;border-radius:4px!important;background:transparent!important;color:#fff!important;font-size:15px!important;font-weight:700!important;line-height:28px!important;overflow:hidden!important;white-space:nowrap!important}
#preview-view-controls button:hover{background:#44515b!important}#preview-view-controls button:focus-visible{outline:2px solid #8bc4e8!important;outline-offset:1px}
#preview-zoom-reset{font-size:9px!important}
.cew-viewport-note{position:absolute;right:10px;bottom:8px;z-index:7;padding:4px 7px;border-radius:4px;background:#20272dcf;color:#eef3f6;font-size:9px;pointer-events:none}
.cew-inspector-tabs{height:32px;display:flex;gap:0;border-bottom:1px solid var(--cew-border);background:#fafbfc;flex:0 0 auto}
.cew-inspector-tabs button{height:32px;min-width:0;padding:0 10px;border:0;border-radius:0;background:transparent;color:#62707a;font-size:10px;font-weight:700;border-bottom:2px solid transparent}
.cew-inspector-tabs button:hover{background:#eef2f4}.cew-inspector-tabs button.active{color:#174f70;border-bottom-color:#2f88b8;background:#fff}
.cew-inspector-tabs button[hidden]{display:none!important}
.cew-inspector-body{min-width:0;min-height:0;overflow:auto;padding:10px;flex:1}
.cew-inspector-panel[hidden]{display:none!important}
.cew-inspector-section{border-top:1px solid var(--cew-border);padding-top:10px;margin-top:10px}.cew-inspector-section:first-child{border-top:0;padding-top:0;margin-top:0}
.cew-inspector-section h4{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#5e6b75;margin:0 0 8px}
#cew-decision-panel label{display:block}#cew-decision-panel .buttons{display:grid}
body.cew-professional-document .gate.blocked{margin:0;background:#fff4d8;border-color:#dfc175}
body.cew-professional-document .gate.ready{margin:0}
.cew-statusbar{height:var(--cew-status);display:flex;align-items:center;gap:0;background:#20272d;color:#dbe4ea;border-top:1px solid #11181d;font-size:10px;white-space:nowrap;overflow:auto;padding:0 5px;min-width:0}
.cew-statusbar span{display:inline-flex;align-items:center;height:100%;padding:0 8px;border-right:1px solid #39434b}.cew-statusbar strong{font-weight:700;color:#fff}
.intake-status.warn{background:var(--cew-warning-bg)!important;border-color:#dfbd67!important;color:var(--cew-warning)!important}
body.cew-primary-collapsed .layout{--cew-left-column:0px;--cew-left-sash:0px}
body.cew-primary-collapsed aside.left,body.cew-primary-collapsed #cew-left-sash{display:none!important}
body.cew-aux-collapsed .layout{--cew-right-column:0px;--cew-right-sash:0px}
body.cew-aux-collapsed aside.right,body.cew-aux-collapsed #cew-right-sash{display:none!important}
@media(max-width:1100px){:root{--cew-left:246px;--cew-right:286px}.cew-editor-pill.optional{display:none}}
@media(max-width:860px){
  body.cew-professional-document .intake{grid-template-columns:minmax(150px,1fr) minmax(160px,1fr) auto;}
  body.cew-professional-document .intake input[type=file]{grid-column:1/3}.cew-editor-pill.optional{display:none}
  body.cew-professional-document .layout{grid-template-columns:var(--cew-rail) minmax(0,1fr)}
  body.cew-professional-document aside.left,body.cew-professional-document aside.right,body.cew-professional-document .cew-sash{display:none!important}
  .cew-canvas-shell{grid-column:2}.cew-statusbar span.optional{display:none}
}
</style>'''


_PROFESSIONAL_SCRIPT = r'''<script id="cew-professional-document-script">
(function(){
'use strict';
const ce=q;
const WORKBENCH_STATE_KEY='cew.documentDiscovery.workbench.v2';
const DEFAULT_LAYOUT={leftWidth:292,rightWidth:336,leftVisible:true,rightVisible:true,activeNav:'clusters',activeInspector:'properties'};
const PRIMARY_VIEWS=[
  {id:'pages',label:'Pg',title:'Pagine'},
  {id:'primitives',label:'Pr',title:'Primitive'},
  {id:'clusters',label:'Cl',title:'Cluster'},
  {id:'verify',label:'!',title:'Da verificare'}
];
let wbState=loadWorkbenchState();

function clamp(n,min,max){return Math.min(max,Math.max(min,Number(n)||min))}
function loadWorkbenchState(){
  try{
    const stored=JSON.parse(localStorage.getItem(WORKBENCH_STATE_KEY)||'{}');
    return {...DEFAULT_LAYOUT,...stored,leftWidth:clamp(stored.leftWidth??DEFAULT_LAYOUT.leftWidth,220,500),rightWidth:clamp(stored.rightWidth??DEFAULT_LAYOUT.rightWidth,260,560)};
  }catch(_){return {...DEFAULT_LAYOUT}}
}
function saveWorkbenchState(){try{localStorage.setItem(WORKBENCH_STATE_KEY,JSON.stringify(wbState))}catch(_){}}
function requestViewerRelayout(){try{requestAnimationFrame(()=>renderPageGeometry(false))}catch(_){}}

function composeTopbar(){
  const header=document.querySelector('header'),provider=ce('provider');
  if(!header||header.dataset.cewComposed==='1')return;
  header.dataset.cewComposed='1';
  const h1=header.querySelector('h1'),small=header.querySelector('small');
  const main=document.createElement('div');main.className='cew-title-main';
  if(h1)main.appendChild(h1);if(small)main.appendChild(small);
  header.prepend(main);
  if(provider)header.appendChild(provider);
}

function makeCanvasShell(){
  const viewer=ce('viewer');
  if(!viewer)return null;
  if(viewer.parentElement?.classList.contains('cew-canvas-shell'))return viewer.parentElement;
  const shell=document.createElement('section');
  shell.id='cew-canvas-shell';shell.className='cew-canvas-shell';shell.setAttribute('aria-label','Tavola tecnica');
  viewer.parentElement.insertBefore(shell,viewer);shell.appendChild(viewer);
  return shell;
}

function documentLabel(){
  const f=ce('file')?.files?.[0];if(f?.name)return f.name;
  const src=ce('source');if(src?.value)return src.options[src.selectedIndex]?.textContent||src.value;
  return 'Nessun documento';
}

function makeEditorBar(){
  const shell=makeCanvasShell();if(!shell)return;
  let bar=ce('cew-editor-bar');
  if(!bar){
    bar=document.createElement('div');bar.id='cew-editor-bar';bar.className='cew-editor-bar';
    bar.innerHTML='<div class="cew-editor-tab"><span>▤</span><strong id="cew-editor-label">Nessun documento</strong></div><div class="cew-editor-meta"><span id="cew-editor-evidence" class="cew-editor-pill">NESSUNA_SESSIONE</span><span id="cew-editor-authority" class="cew-editor-pill optional">AUTORITÀ: LETTURA</span><div class="cew-editor-actions"><button id="cew-toggle-primary" class="cew-panel-action" type="button" title="Mostra/nascondi navigatore" aria-label="Mostra o nascondi navigatore">☰</button><button id="cew-toggle-aux" class="cew-panel-action" type="button" title="Mostra/nascondi ispettore" aria-label="Mostra o nascondi ispettore">◧</button></div></div>';
    shell.insertBefore(bar,ce('viewer'));
    ce('cew-toggle-primary').onclick=()=>togglePrimary();
    ce('cew-toggle-aux').onclick=()=>toggleAuxiliary();
  }
}

function compactViewportControls(){
  const bar=ce('preview-view-controls');if(!bar)return;
  const spec={
    'preview-overview':['⛶','Adatta pagina'],
    'preview-width':['↔','Adatta larghezza'],
    'preview-zoom-out':['−','Riduci zoom'],
    'preview-zoom-reset':['1:1',`Ripristina zoom · ${Math.round(Number(previewZoom||1)*100)}%`],
    'preview-zoom-in':['+','Aumenta zoom'],
    'preview-rotate-left':['↶','Ruota 90° antiorario'],
    'preview-rotate-right':['↷','Ruota 90° orario']
  };
  for(const [id,[label,title]] of Object.entries(spec)){
    const b=ce(id);if(!b)continue;b.textContent=label;b.title=title;b.setAttribute('aria-label',title);
  }
}

const baseEnsurePreviewControls=ensurePreviewControls;
ensurePreviewControls=function(){
  const bar=baseEnsurePreviewControls();
  const shell=makeCanvasShell();if(shell&&bar&&bar.parentElement!==shell)shell.appendChild(bar);
  compactViewportControls();return bar;
};
const baseUpdatePreviewControlState=updatePreviewControlState;
updatePreviewControlState=function(){baseUpdatePreviewControlState();compactViewportControls()};

function makePrimarySidebar(){
  const layout=document.querySelector('.layout'),left=document.querySelector('aside.left');
  if(!layout||!left||ce('cew-activity-rail'))return;
  const rail=document.createElement('nav');rail.id='cew-activity-rail';rail.className='cew-activity-rail';rail.setAttribute('aria-label','Viste documento');
  layout.insertBefore(rail,left);
  for(const view of PRIMARY_VIEWS){
    const b=document.createElement('button');b.type='button';b.dataset.nav=view.id;b.textContent=view.label;b.title=view.title;b.setAttribute('aria-label',view.title);
    b.onclick=()=>{if(wbState.activeNav===view.id&&wbState.leftVisible){wbState.leftVisible=false;applyWorkbenchLayout();return}wbState.activeNav=view.id;wbState.leftVisible=true;applyWorkbenchLayout();showNav(view.id)};
    rail.appendChild(b);
  }
  const status=ce('status'),clustersEl=ce('clusters');
  const head=document.createElement('div');head.className='cew-primary-head';head.innerHTML='<strong id="cew-primary-title">Navigatore</strong><button id="cew-hide-primary" class="cew-panel-action" type="button" title="Nascondi pannello" aria-label="Nascondi pannello">‹</button>';
  const content=document.createElement('div');content.id='cew-primary-content';content.className='cew-primary-content';
  const pages=document.createElement('section');pages.id='cew-nav-pages';pages.className='cew-nav-panel';
  const primitives=document.createElement('section');primitives.id='cew-nav-primitives';primitives.className='cew-nav-panel';
  const clustersPanel=document.createElement('section');clustersPanel.id='cew-nav-clusters';clustersPanel.className='cew-nav-panel';
  const verify=document.createElement('section');verify.id='cew-nav-verify';verify.className='cew-nav-panel';
  if(status)status.hidden=true;
  if(clustersEl){clustersEl.classList.remove('section');clustersPanel.appendChild(clustersEl)}
  content.append(pages,primitives,clustersPanel,verify);left.replaceChildren(head,content);
  ce('cew-hide-primary').onclick=()=>togglePrimary(false);
  showNav(wbState.activeNav);
}

function showNav(id){
  const view=PRIMARY_VIEWS.find(v=>v.id===id)||PRIMARY_VIEWS[2];wbState.activeNav=view.id;
  for(const panel of document.querySelectorAll('.cew-nav-panel'))panel.hidden=panel.id!==`cew-nav-${view.id}`;
  for(const b of document.querySelectorAll('#cew-activity-rail button'))b.classList.toggle('active',b.dataset.nav===view.id);
  const title=ce('cew-primary-title');if(title)title.textContent=view.title;
  saveWorkbenchState();
}
function togglePrimary(force){wbState.leftVisible=typeof force==='boolean'?force:!wbState.leftVisible;applyWorkbenchLayout()}
function toggleAuxiliary(force){wbState.rightVisible=typeof force==='boolean'?force:!wbState.rightVisible;applyWorkbenchLayout()}

function navTitle(text,count){return `<div class="cew-sidebar-title"><span>${h(text)}</span>${count==null?'':`<span class="cew-count">${Number(count)}</span>`}</div>`}
function renderNavigation(){
  const pages=ce('cew-nav-pages'),primitives=ce('cew-nav-primitives'),verify=ce('cew-nav-verify');if(!pages)return;
  const pageCount=Number(state?.page_count||0),pc=Number(state?.primitive_candidate_count||0),cc=Number(state?.graphic_cluster_count||0);
  pages.innerHTML=navTitle('Pagine',pageCount)+(pageCount?[...Array(pageCount)].map((_,i)=>`<button class="cew-page-row ${i===Number(currentPreviewPageIndex||0)?'active':''}" data-page="${i}"><span>Pagina ${i+1}</span><span class="meta">${i===Number(currentPreviewPageIndex||0)?'attiva':''}</span></button>`).join(''):'<div class="cew-empty">Nessuna pagina caricata.</div>');
  for(const b of pages.querySelectorAll('[data-page]'))b.onclick=()=>showPreviewPage(Number(b.dataset.page),'overview');
  primitives.innerHTML=navTitle('Primitive',pc)+(pc?`<div class="cew-summary-row"><span>Primitive grafiche</span><strong>${pc}</strong></div><div class="cew-meta-note">Evidenza geometrica non semantica. La revisione operativa avviene tramite i cluster.</div>`:'<div class="cew-empty">Nessuna primitiva grafica acquisita.</div>');
  const reg=state?.source_registration_state||'NESSUNA_SESSIONE';
  verify.innerHTML=navTitle('Da verificare')+`<dl class="cew-kv"><dt>Acquisizione</dt><dd>${pc>0||cc>0?'EVIDENZA_GRAFICA_RILEVATA':'NESSUNA_REGIONE_GRAFICA_ACQUISITA'}</dd><dt>Primitive</dt><dd>${pc}</dd><dt>Cluster</dt><dd>${cc}</dd><dt>Fonte</dt><dd>${h(reg)}</dd><dt>Training</dt><dd>${state?.teaching_enabled?'CONSENTITO':'BLOCCATO'}</dd></dl>`;
}

function makeInspector(){
  const right=document.querySelector('aside.right');if(!right||ce('cew-inspector-head'))return;
  const title=ce('title'),detail=ce('detail'),gate=ce('gate'),conceptsEl=ce('concepts'),results=ce('results'),message=ce('message');
  const labels=[...right.querySelectorAll(':scope > label')],buttonsEl=right.querySelector(':scope > .buttons');
  const head=document.createElement('div');head.id='cew-inspector-head';head.className='cew-inspector-head';head.innerHTML='<strong>Ispettore</strong><button id="cew-hide-aux" class="cew-panel-action" type="button" title="Nascondi ispettore" aria-label="Nascondi ispettore">›</button>';
  const tabs=document.createElement('div');tabs.id='cew-inspector-tabs';tabs.className='cew-inspector-tabs';tabs.innerHTML='<button type="button" data-inspector="properties">Proprietà</button><button type="button" data-inspector="provenance">Provenienza</button><button id="cew-decision-tab" type="button" data-inspector="decision">Decisione</button>';
  const body=document.createElement('div');body.className='cew-inspector-body';
  const props=document.createElement('section');props.id='cew-inspector-properties';props.className='cew-inspector-panel';
  const meta=document.createElement('div');meta.id='cew-inspector-meta';meta.className='cew-inspector-section';
  if(title)props.appendChild(title);if(detail)props.appendChild(detail);props.appendChild(meta);
  const provenance=document.createElement('section');provenance.id='cew-inspector-provenance';provenance.className='cew-inspector-panel';
  const provenanceMeta=document.createElement('div');provenanceMeta.id='cew-provenance-meta';provenanceMeta.className='cew-inspector-section';
  if(gate)provenance.appendChild(gate);provenance.appendChild(provenanceMeta);
  const decision=document.createElement('section');decision.id='cew-decision-panel';decision.className='cew-inspector-panel';
  for(const el of labels)decision.appendChild(el);if(buttonsEl)decision.appendChild(buttonsEl);if(conceptsEl)decision.appendChild(conceptsEl);if(results)decision.appendChild(results);if(message)decision.appendChild(message);
  body.append(props,provenance,decision);right.replaceChildren(head,tabs,body);
  ce('cew-hide-aux').onclick=()=>toggleAuxiliary(false);
  for(const b of tabs.querySelectorAll('[data-inspector]'))b.onclick=()=>showInspectorTab(b.dataset.inspector);
  showInspectorTab(wbState.activeInspector);
}

function showInspectorTab(id){
  const teaching=!!state?.teaching_enabled;if(id==='decision'&&!teaching)id='properties';
  wbState.activeInspector=id;
  for(const p of document.querySelectorAll('.cew-inspector-panel'))p.hidden=p.id!==`cew-inspector-${id}`&&!(id==='decision'&&p.id==='cew-decision-panel');
  for(const b of document.querySelectorAll('#cew-inspector-tabs [data-inspector]'))b.classList.toggle('active',b.dataset.inspector===id);
  const decisionTab=ce('cew-decision-tab');if(decisionTab)decisionTab.hidden=!teaching;
  const decision=ce('cew-decision-panel');if(decision)decision.hidden=id!=='decision'||!teaching;
  saveWorkbenchState();
}

function inspectorRows(){
  const c=typeof cluster==='function'?cluster():null,reg=state?.source_registration_state||'NESSUNA_SESSIONE';
  if(!state)return '<div class="cew-empty">Carica una fonte o un PDF.</div>';
  if(!c)return `<h4>Documento</h4><dl class="cew-kv"><dt>Pagine</dt><dd>${state.page_count}</dd><dt>Primitive</dt><dd>${state.primitive_candidate_count}</dd><dt>Cluster</dt><dd>${state.graphic_cluster_count}</dd><dt>Fonte</dt><dd>${h(reg)}</dd><dt>Significato</dt><dd>NON ASSEGNATO</dd></dl>`;
  const r=c.representative||{},b=r.bbox||{};
  return `<h4>Cluster selezionato</h4><dl class="cew-kv"><dt>ID</dt><dd>${h(c.cluster_id)}</dd><dt>Famiglia</dt><dd>${h(c.feature_signature?.primitive_family||'')}</dd><dt>Occorrenze</dt><dd>${Number(c.occurrence_count||0)}</dd><dt>Pagina</dt><dd>${Number(r.page_index||0)+1}</dd><dt>BBox</dt><dd>${[b.x,b.y,b.w,b.h].map(v=>Number(v||0).toFixed(4)).join(' · ')}</dd><dt>Significato</dt><dd>NON ASSEGNATO</dd><dt>Validazione</dt><dd>UMANA RICHIESTA</dd></dl>`;
}
function provenanceRows(){
  const budget=state?.preview_budget||{},mode=budget.render_boundary||budget.worker_mode||'—',reg=state?.source_registration_state||'NESSUNA_SESSIONE';
  return `<h4>Provenienza e autorità</h4><dl class="cew-kv"><dt>Sessione</dt><dd>${h(session||'—')}</dd><dt>Fonte</dt><dd>${h(reg)}</dd><dt>Pagina</dt><dd>${state?.page_count?Number(currentPreviewPageIndex||0)+1:'—'}</dd><dt>Renderer</dt><dd>${h(mode)}</dd><dt>Semantica</dt><dd>NESSUNA AUTORITÀ AUTOMATICA</dd><dt>Training</dt><dd>${state?.teaching_enabled?'CONSENTITO':'BLOCCATO'}</dd><dt>Scrittura canonica</dt><dd>BLOCCATA</dd></dl>`;
}
function renderInspector(){
  const meta=ce('cew-inspector-meta'),prov=ce('cew-provenance-meta');if(meta)meta.innerHTML=inspectorRows();if(prov)prov.innerHTML=provenanceRows();
  showInspectorTab(wbState.activeInspector);
}

function makeSashes(){
  const layout=document.querySelector('.layout'),left=document.querySelector('aside.left'),right=document.querySelector('aside.right'),shell=makeCanvasShell();if(!layout||!left||!right||!shell)return;
  if(!ce('cew-left-sash')){const s=document.createElement('div');s.id='cew-left-sash';s.className='cew-sash';s.tabIndex=0;s.setAttribute('role','separator');s.setAttribute('aria-label','Ridimensiona navigatore');left.insertAdjacentElement('afterend',s);wireSash(s,'left')}
  if(!ce('cew-right-sash')){const s=document.createElement('div');s.id='cew-right-sash';s.className='cew-sash';s.tabIndex=0;s.setAttribute('role','separator');s.setAttribute('aria-label','Ridimensiona ispettore');right.insertAdjacentElement('beforebegin',s);wireSash(s,'right')}
}
function wireSash(sash,side){
  const defaults=side==='left'?292:336,min=side==='left'?220:260,max=side==='left'?500:560;
  sash.addEventListener('pointerdown',e=>{if(e.button!==0)return;e.preventDefault();const startX=e.clientX,start=side==='left'?wbState.leftWidth:wbState.rightWidth;sash.classList.add('dragging');sash.setPointerCapture?.(e.pointerId);
    const move=ev=>{const delta=ev.clientX-startX,val=clamp(start+(side==='left'?delta:-delta),min,max);if(side==='left')wbState.leftWidth=val;else wbState.rightWidth=val;applyWorkbenchLayout(false)};
    const end=ev=>{sash.releasePointerCapture?.(ev.pointerId);sash.classList.remove('dragging');sash.removeEventListener('pointermove',move);sash.removeEventListener('pointerup',end);sash.removeEventListener('pointercancel',end);saveWorkbenchState();requestViewerRelayout()};
    sash.addEventListener('pointermove',move);sash.addEventListener('pointerup',end);sash.addEventListener('pointercancel',end);
  });
  sash.addEventListener('dblclick',()=>{if(side==='left')wbState.leftWidth=defaults;else wbState.rightWidth=defaults;applyWorkbenchLayout()});
  sash.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const delta=e.key==='ArrowRight'?12:-12;if(side==='left')wbState.leftWidth=clamp(wbState.leftWidth+delta,min,max);else wbState.rightWidth=clamp(wbState.rightWidth-delta,min,max);applyWorkbenchLayout()});
}

function applyWorkbenchLayout(persist=true){
  document.documentElement.style.setProperty('--cew-left',`${clamp(wbState.leftWidth,220,500)}px`);
  document.documentElement.style.setProperty('--cew-right',`${clamp(wbState.rightWidth,260,560)}px`);
  document.body.classList.toggle('cew-primary-collapsed',!wbState.leftVisible);
  document.body.classList.toggle('cew-aux-collapsed',!wbState.rightVisible);
  if(persist)saveWorkbenchState();requestViewerRelayout();
}

function makeStatusBar(){
  if(ce('cew-statusbar'))return;
  const layout=document.querySelector('.layout');if(!layout)return;
  const bar=document.createElement('div');bar.id='cew-statusbar';bar.className='cew-statusbar';layout.insertAdjacentElement('afterend',bar);
  const shell=makeCanvasShell();if(shell&&!ce('cew-viewport-note')){const n=document.createElement('div');n.id='cew-viewport-note';n.className='cew-viewport-note';n.textContent='Trascina: pan · rotella: zoom';shell.appendChild(n)}
}
function updateEditorBar(){
  const label=ce('cew-editor-label'),evidence=ce('cew-editor-evidence');if(label)label.textContent=documentLabel();
  const pc=Number(state?.primitive_candidate_count||0),cc=Number(state?.graphic_cluster_count||0),reg=state?.source_registration_state||'NESSUNA_SESSIONE';
  if(evidence)evidence.textContent=state?(pc>0||cc>0?`${pc} PR · ${cc} CL`:(state.page_count?'VERIFICA NECESSARIA':reg)):reg;
}
function updateStatusBar(){
  const bar=ce('cew-statusbar');if(!bar)return;
  const budget=state?.preview_budget||{},renderer=budget.render_boundary||budget.worker_mode||(state?'STRUCTURED':'—'),pc=Number(state?.primitive_candidate_count||0),cc=Number(state?.graphic_cluster_count||0);
  bar.innerHTML=`<span>Pagina <strong>${state?.page_count?Number(currentPreviewPageIndex||0)+1:0}/${Number(state?.page_count||0)}</strong></span><span>Zoom <strong>${Math.round(Number(previewZoom||1)*100)}%</strong></span><span>Rot <strong>${Number(previewRotation||0)}°</strong></span><span class="optional">Renderer <strong>${h(renderer)}</strong></span><span>Primitive <strong>${pc}</strong></span><span>Cluster <strong>${cc}</strong></span><span class="optional">Fonte <strong>${h(state?.source_registration_state||'—')}</strong></span><span>Training <strong>${state?.teaching_enabled?'ON':'BLOCCATO'}</strong></span>`;
  updateEditorBar();
}

const baseProfessionalIntakeMessage=intakeMessage;
intakeMessage=function(text,kind=''){
  const pc=Number(state?.primitive_candidate_count||0),cc=Number(state?.graphic_cluster_count||0);
  if(kind==='ok'&&state&&pc===0&&cc===0){
    return baseProfessionalIntakeMessage(`Analisi completata · ${state.page_count} pagina${state.page_count===1?'':'e'} · nessuna regione grafica acquisita · verifica necessaria. Training ${state.teaching_enabled?'consentito':'bloccato'}.`,'warn');
  }
  return baseProfessionalIntakeMessage(text,kind);
};

function professionalRender(){composeTopbar();makeCanvasShell();makeEditorBar();makePrimarySidebar();makeInspector();makeSashes();makeStatusBar();ensurePreviewControls();compactViewportControls();renderNavigation();renderInspector();updateStatusBar();applyWorkbenchLayout(false)}

const baseProfessionalRender=render;
render=function(){baseProfessionalRender();professionalRender()};
const baseSelected=selected;
selected=function(){baseSelected();professionalRender()};
const baseSetPreviewZoom=setPreviewZoom;
setPreviewZoom=function(value){baseSetPreviewZoom(value);requestAnimationFrame(()=>{compactViewportControls();updateStatusBar()})};
const baseRotatePreview=rotatePreview;
rotatePreview=function(delta){baseRotatePreview(delta);requestAnimationFrame(updateStatusBar)};
const baseSetPreviewView=setPreviewView;
setPreviewView=function(mode){baseSetPreviewView(mode);requestAnimationFrame(updateStatusBar)};

function enableWheelZoom(){
  const viewer=ce('viewer');if(!viewer||viewer.dataset.wheelZoom==='1')return;viewer.dataset.wheelZoom='1';
  viewer.addEventListener('wheel',e=>{
    if(!session||ce('page').hidden)return;e.preventDefault();
    const rect=viewer.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;
    const old=Math.max(.01,Number(previewZoom||1)),next=Math.min(8,Math.max(.25,old*(e.deltaY<0?1.12:1/1.12)));
    const oldLeft=viewer.scrollLeft,oldTop=viewer.scrollTop;setPreviewZoom(next);
    requestAnimationFrame(()=>{const ratio=next/old;viewer.scrollLeft=(oldLeft+x)*ratio-x;viewer.scrollTop=(oldTop+y)*ratio-y;updateStatusBar()});
  },{passive:false});
}

function installWorkbenchShortcuts(){
  if(document.body.dataset.workbenchKeys==='1')return;document.body.dataset.workbenchKeys='1';
  document.addEventListener('keydown',e=>{
    if((e.ctrlKey||e.metaKey)&&!e.shiftKey&&e.key.toLowerCase()==='b'){e.preventDefault();togglePrimary()}
    if((e.ctrlKey||e.metaKey)&&e.altKey&&e.key.toLowerCase()==='i'){e.preventDefault();toggleAuxiliary()}
  });
}

document.body.classList.add('cew-professional-document');
composeTopbar();makeCanvasShell();makeEditorBar();makePrimarySidebar();makeInspector();makeSashes();makeStatusBar();ensurePreviewControls();compactViewportControls();enableWheelZoom();installWorkbenchShortcuts();applyWorkbenchLayout(false);professionalRender();
})();
</script>'''


def _patched_page() -> str:
    html = async_preview._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_PROFESSIONAL_DOCUMENT_HTML_MARKER_MISSING")
    html = html.replace("</head>", _PROFESSIONAL_STYLE + "</head>", 1)
    html = html.replace("</body>", _PROFESSIONAL_SCRIPT + "</body>", 1)
    return html


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def professional_document_page():
        return HTMLResponse(
            _patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Document-Workbench": "PROFESSIONAL_V2",
                "X-CEW-Panel-Architecture": "ACTIVITY_PRIMARY_EDITOR_AUXILIARY_STATUS",
            },
        )

    return router
