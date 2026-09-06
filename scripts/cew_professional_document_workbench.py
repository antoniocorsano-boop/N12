#!/usr/bin/env python3
"""Professional document inspection shell for CEW Document Discovery.

This module changes only the human inspection surface. It reuses the validated
async/bounded Document Discovery HTML and APIs, then applies a mature workbench
layout: primary navigation sidebar, dominant document canvas, contextual
inspector, viewport-anchored navigation tools, and a status bar.

No acquisition, semantic, learning, SourceVersion/Page, or canonical-write
boundary is changed here.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_document_discovery_async_preview as async_preview


_PROFESSIONAL_STYLE = r'''<style id="cew-professional-document-style">
:root{--cew-rail:44px;--cew-left:286px;--cew-right:326px;--cew-status:30px;--cew-ui:#f7f8fa;--cew-panel:#fff;--cew-border:#d6dce1;--cew-select:#17415f;--cew-canvas:#cfd7dd;--cew-warning:#8a5a00;--cew-warning-bg:#fff4d8}
body.cew-professional-document{overflow:hidden;background:#eef1f3}
body.cew-professional-document header{padding:9px 14px}
body.cew-professional-document .provider{padding:5px 10px}
body.cew-professional-document .intake{padding:7px 10px;gap:6px}
body.cew-professional-document .layout{grid-template-columns:var(--cew-left) minmax(360px,1fr) var(--cew-right);height:calc(100vh - 224px);min-height:420px;background:var(--cew-ui)}
body.cew-professional-document aside{padding:0;background:var(--cew-panel);min-width:0}
body.cew-professional-document .left{display:grid;grid-template-columns:var(--cew-rail) minmax(0,1fr);border-right:1px solid var(--cew-border)}
body.cew-professional-document .right{border-left:1px solid var(--cew-border);padding:12px;overflow:auto}
.cew-canvas-shell{position:relative;min-width:0;min-height:0;overflow:hidden;background:var(--cew-canvas)}
body.cew-professional-document #viewer{width:100%;height:100%;background:var(--cew-canvas);padding:14px 14px 36px;min-width:0;overflow:auto;justify-content:center;align-items:flex-start;cursor:grab}
body.cew-professional-document #viewer:active{cursor:grabbing}
body.cew-professional-document .pagewrap img{box-shadow:0 3px 18px #0004}
.cew-activity-rail{display:flex;flex-direction:column;align-items:center;gap:4px;padding:7px 5px;background:#20272d;border-right:1px solid #11181d}
.cew-activity-rail button{width:34px;height:34px;padding:0;border-radius:5px;background:transparent;color:#dbe3e9;font-weight:700;font-size:13px;border-left:2px solid transparent}
.cew-activity-rail button:hover{background:#323c44}.cew-activity-rail button.active{background:#3b4851;color:#fff;border-left-color:#68a8d1}
.cew-primary-content{min-width:0;overflow:auto;padding:10px}
.cew-sidebar-title{display:flex;align-items:center;justify-content:space-between;font-size:11px;font-weight:800;letter-spacing:.08em;color:#4e5b65;text-transform:uppercase;margin-bottom:9px}
.cew-nav-panel[hidden]{display:none!important}
.cew-page-row,.cew-summary-row{width:100%;display:flex;align-items:center;justify-content:space-between;gap:8px;padding:8px;border:1px solid var(--cew-border);border-radius:6px;background:#fff;margin-bottom:6px;text-align:left}
.cew-page-row.active{outline:2px solid var(--cew-select)}
.cew-kv{display:grid;grid-template-columns:minmax(90px,.9fr) minmax(0,1.3fr);gap:5px 10px;font-size:12px;line-height:1.35}.cew-kv dt{color:#66737d}.cew-kv dd{margin:0;font-weight:650;overflow-wrap:anywhere}
.cew-empty{padding:14px 8px;color:#6b7780;font-size:12px;text-align:center}
.cew-inspector-section{border-top:1px solid var(--cew-border);padding-top:10px;margin-top:10px}.cew-inspector-section:first-child{border-top:0;padding-top:0;margin-top:0}.cew-inspector-section h4{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#5e6b75;margin:0 0 8px}
#cew-decision-panel[hidden]{display:none!important}
#cew-decision-panel label{display:block}#cew-decision-panel .buttons{display:grid}
#preview-view-controls{position:absolute!important;z-index:8!important;left:8px!important;top:8px!important;right:auto!important;display:flex!important;flex-direction:column!important;flex-wrap:nowrap!important;justify-content:flex-start!important;gap:2px!important;width:38px!important;max-width:38px!important;padding:3px!important;background:#20272de8!important;border:1px solid #11181d!important;border-radius:7px!important;box-shadow:0 2px 8px #0004!important;transform:none!important}
#preview-view-controls button{width:30px!important;height:30px!important;min-width:30px!important;padding:0!important;border-radius:4px!important;background:transparent!important;color:#fff!important;font-size:16px!important;font-weight:700!important;line-height:30px!important;overflow:hidden!important;white-space:nowrap!important}
#preview-view-controls button:hover{background:#44525d!important}#preview-view-controls button:focus-visible{outline:2px solid #8bc4e8!important;outline-offset:1px}
#preview-zoom-reset{font-size:10px!important}
.cew-statusbar{height:var(--cew-status);display:flex;align-items:center;gap:0;background:#20272d;color:#e7edf1;border-top:1px solid #11181d;font-size:11px;white-space:nowrap;overflow:auto;padding:0 7px}
.cew-statusbar span{display:inline-flex;align-items:center;height:100%;padding:0 9px;border-right:1px solid #3b444b}.cew-statusbar strong{font-weight:700;color:#fff}
.intake-status.warn{background:var(--cew-warning-bg)!important;border-color:#dfbd67!important;color:var(--cew-warning)!important}
body.cew-professional-document .gate.blocked{margin:0;background:#fff4d8;border-color:#dfc175}
body.cew-professional-document .right>label,body.cew-professional-document .right>.buttons{display:none}
.cew-viewport-note{position:absolute;right:10px;bottom:8px;z-index:7;padding:4px 7px;border-radius:5px;background:#20272dcc;color:#eef3f6;font-size:10px;pointer-events:none}
@media(max-width:1050px){:root{--cew-left:245px;--cew-right:286px}}
@media(max-width:820px){body.cew-professional-document{overflow:auto}body.cew-professional-document .layout{display:flex;height:auto;min-height:0;flex-direction:column}.left{min-height:220px}.cew-canvas-shell{min-height:58vh}.cew-statusbar{position:sticky;bottom:0;z-index:20}body.cew-professional-document #viewer{min-height:58vh}body.cew-professional-document .right{min-height:260px}}
</style>'''


_PROFESSIONAL_SCRIPT = r'''<script id="cew-professional-document-script">
(function(){
'use strict';
const ce=q;
let activeNav='clusters';

function makeCanvasShell(){
  const viewer=ce('viewer');
  if(!viewer)return null;
  if(viewer.parentElement?.classList.contains('cew-canvas-shell'))return viewer.parentElement;
  const shell=document.createElement('section');
  shell.id='cew-canvas-shell';
  shell.className='cew-canvas-shell';
  shell.setAttribute('aria-label','Tavola tecnica');
  viewer.parentElement.insertBefore(shell,viewer);
  shell.appendChild(viewer);
  return shell;
}

function compactViewportControls(){
  const bar=ce('preview-view-controls');
  if(!bar)return;
  const spec={
    'preview-overview':['⛶','Adatta pagina'],
    'preview-width':['↔','Adatta larghezza'],
    'preview-zoom-out':['−','Riduci zoom'],
    'preview-zoom-reset':['100','Ripristina zoom'],
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
  const shell=makeCanvasShell();
  if(shell&&bar&&bar.parentElement!==shell)shell.appendChild(bar);
  compactViewportControls();
  return bar;
};

function makeSidebar(){
  const left=document.querySelector('aside.left');
  if(!left||ce('cew-activity-rail'))return;
  const existing=[...left.childNodes];
  const rail=document.createElement('nav');rail.id='cew-activity-rail';rail.className='cew-activity-rail';rail.setAttribute('aria-label','Navigazione documento');
  const content=document.createElement('div');content.id='cew-primary-content';content.className='cew-primary-content';
  for(const node of existing)content.appendChild(node);
  left.append(rail,content);
  const tabs=[['pages','Pg','Pagine'],['primitives','Pr','Primitive'],['clusters','Cl','Cluster'],['verify','!','Da verificare']];
  for(const [id,label,title] of tabs){const b=document.createElement('button');b.type='button';b.dataset.nav=id;b.textContent=label;b.title=title;b.setAttribute('aria-label',title);b.onclick=()=>showNav(id);rail.appendChild(b)}
  const status=ce('status'),clustersEl=ce('clusters');
  const pages=document.createElement('section');pages.id='cew-nav-pages';pages.className='cew-nav-panel';
  const primitives=document.createElement('section');primitives.id='cew-nav-primitives';primitives.className='cew-nav-panel';
  const clustersPanel=document.createElement('section');clustersPanel.id='cew-nav-clusters';clustersPanel.className='cew-nav-panel';
  const verify=document.createElement('section');verify.id='cew-nav-verify';verify.className='cew-nav-panel';
  if(status)status.hidden=true;if(clustersEl){clustersEl.classList.remove('section');clustersPanel.appendChild(clustersEl)}
  content.append(pages,primitives,clustersPanel,verify);
  showNav(activeNav);
}

function showNav(id){
  activeNav=id;
  for(const panel of document.querySelectorAll('.cew-nav-panel'))panel.hidden=panel.id!==`cew-nav-${id}`;
  for(const b of document.querySelectorAll('#cew-activity-rail button'))b.classList.toggle('active',b.dataset.nav===id);
}

function navTitle(text){return `<div class="cew-sidebar-title"><span>${h(text)}</span></div>`}
function renderNavigation(){
  const pages=ce('cew-nav-pages'),primitives=ce('cew-nav-primitives'),verify=ce('cew-nav-verify');if(!pages)return;
  const pageCount=Number(state?.page_count||0);
  pages.innerHTML=navTitle('Pagine')+(pageCount?[...Array(pageCount)].map((_,i)=>`<button class="cew-page-row ${i===Number(currentPreviewPageIndex||0)?'active':''}" data-page="${i}"><span>Pagina ${i+1}</span><span class="meta">${i===Number(currentPreviewPageIndex||0)?'attiva':''}</span></button>`).join(''):'<div class="cew-empty">Nessuna pagina caricata.</div>');
  for(const b of pages.querySelectorAll('[data-page]'))b.onclick=()=>showPreviewPage(Number(b.dataset.page),'overview');
  const pc=Number(state?.primitive_candidate_count||0);
  primitives.innerHTML=navTitle('Primitive')+(pc?`<div class="cew-summary-row"><span>Primitive grafiche</span><strong>${pc}</strong></div><div class="meta">Le primitive sono evidenza geometrica non semantica. La revisione operativa avviene tramite i cluster.</div>`:'<div class="cew-empty">Nessuna primitiva grafica acquisita.</div>');
  const cc=Number(state?.graphic_cluster_count||0),reg=state?.source_registration_state||'NESSUNA_SESSIONE';
  verify.innerHTML=navTitle('Da verificare')+`<dl class="cew-kv"><dt>Acquisizione</dt><dd>${pc>0||cc>0?'EVIDENZA_GRAFICA_RILEVATA':'NESSUNA_REGIONE_GRAFICA_ACQUISITA'}</dd><dt>Primitive</dt><dd>${pc}</dd><dt>Cluster</dt><dd>${cc}</dd><dt>Fonte</dt><dd>${h(reg)}</dd><dt>Training</dt><dd>${state?.teaching_enabled?'CONSENTITO':'BLOCCATO'}</dd></dl>`;
}

function makeInspector(){
  const right=document.querySelector('aside.right');if(!right||ce('cew-inspector-meta'))return;
  const meta=document.createElement('div');meta.id='cew-inspector-meta';meta.className='cew-inspector-section';
  const decision=document.createElement('section');decision.id='cew-decision-panel';decision.className='cew-inspector-section';decision.innerHTML='<h4>Decisione umana</h4>';
  const labels=[...right.querySelectorAll(':scope > label')],buttons=right.querySelector(':scope > .buttons');
  for(const el of labels)decision.appendChild(el);if(buttons)decision.appendChild(buttons);
  const gate=ce('gate');if(gate)right.insertBefore(meta,gate);right.appendChild(decision);
}

function inspectorRows(){
  const c=typeof cluster==='function'?cluster():null;
  const reg=state?.source_registration_state||'NESSUNA_SESSIONE';
  if(!state)return '<div class="cew-empty">Carica una fonte o un PDF.</div>';
  if(!c)return `<h4>Documento</h4><dl class="cew-kv"><dt>Pagine</dt><dd>${state.page_count}</dd><dt>Primitive</dt><dd>${state.primitive_candidate_count}</dd><dt>Cluster</dt><dd>${state.graphic_cluster_count}</dd><dt>Fonte</dt><dd>${h(reg)}</dd><dt>Significato</dt><dd>NON ASSEGNATO</dd></dl>`;
  const r=c.representative||{},b=r.bbox||{};
  return `<h4>Cluster selezionato</h4><dl class="cew-kv"><dt>ID</dt><dd>${h(c.cluster_id)}</dd><dt>Famiglia</dt><dd>${h(c.feature_signature?.primitive_family||'')}</dd><dt>Occorrenze</dt><dd>${Number(c.occurrence_count||0)}</dd><dt>Pagina</dt><dd>${Number(r.page_index||0)+1}</dd><dt>BBox</dt><dd>${[b.x,b.y,b.w,b.h].map(v=>Number(v||0).toFixed(4)).join(' · ')}</dd><dt>Significato</dt><dd>NON ASSEGNATO</dd><dt>Validazione</dt><dd>UMANA RICHIESTA</dd></dl>`;
}

function renderInspector(){
  const meta=ce('cew-inspector-meta'),decision=ce('cew-decision-panel');if(!meta)return;
  meta.innerHTML=inspectorRows();
  if(decision)decision.hidden=!state?.teaching_enabled;
}

function makeStatusBar(){
  if(ce('cew-statusbar'))return;
  const layout=document.querySelector('.layout');if(!layout)return;
  const bar=document.createElement('div');bar.id='cew-statusbar';bar.className='cew-statusbar';layout.insertAdjacentElement('afterend',bar);
  const shell=makeCanvasShell();if(shell&&!ce('cew-viewport-note')){const n=document.createElement('div');n.id='cew-viewport-note';n.className='cew-viewport-note';n.textContent='Trascina per spostare · rotella per zoom';shell.appendChild(n)}
}

function updateStatusBar(){
  const bar=ce('cew-statusbar');if(!bar)return;
  const pc=Number(state?.primitive_candidate_count||0),cc=Number(state?.graphic_cluster_count||0);
  const renderer=(state?.preview_worker_mode||state?.preview_fallback_mode||'AUTO');
  bar.innerHTML=`<span>Pagina <strong>${state?.page_count?Number(currentPreviewPageIndex||0)+1:0}/${Number(state?.page_count||0)}</strong></span><span>Zoom <strong>${Math.round(Number(previewZoom||1)*100)}%</strong></span><span>Rot <strong>${Number(previewRotation||0)}°</strong></span><span>Renderer <strong>${h(renderer)}</strong></span><span>Primitive <strong>${pc}</strong></span><span>Cluster <strong>${cc}</strong></span><span>Fonte <strong>${h(state?.source_registration_state||'—')}</strong></span><span>Training <strong>${state?.teaching_enabled?'ON':'BLOCCATO'}</strong></span>`;
}

const baseProfessionalIntakeMessage=intakeMessage;
intakeMessage=function(text,kind=''){
  const pc=Number(state?.primitive_candidate_count||0),cc=Number(state?.graphic_cluster_count||0);
  if(kind==='ok'&&state&&pc===0&&cc===0){
    return baseProfessionalIntakeMessage(`Analisi completata · ${state.page_count} pagina${state.page_count===1?'':'e'} · nessuna regione grafica acquisita · verifica necessaria. Training ${state.teaching_enabled?'consentito':'bloccato'}.`,'warn');
  }
  return baseProfessionalIntakeMessage(text,kind);
};

function professionalRender(){makeCanvasShell();makeSidebar();makeInspector();makeStatusBar();ensurePreviewControls();compactViewportControls();renderNavigation();renderInspector();updateStatusBar()}

const baseProfessionalRender=render;
render=function(){baseProfessionalRender();professionalRender()};
const baseSelected=selected;
selected=function(){baseSelected();professionalRender()};
const baseSetPreviewZoom=setPreviewZoom;
setPreviewZoom=function(value){baseSetPreviewZoom(value);requestAnimationFrame(updateStatusBar)};
const baseRotatePreview=rotatePreview;
rotatePreview=function(delta){baseRotatePreview(delta);requestAnimationFrame(updateStatusBar)};
const baseSetPreviewView=setPreviewView;
setPreviewView=function(mode){baseSetPreviewView(mode);requestAnimationFrame(updateStatusBar)};

function enableWheelZoom(){
  const viewer=ce('viewer');if(!viewer||viewer.dataset.wheelZoom==='1')return;viewer.dataset.wheelZoom='1';
  viewer.addEventListener('wheel',e=>{
    if(!session||ce('page').hidden)return;
    e.preventDefault();
    const rect=viewer.getBoundingClientRect(),x=e.clientX-rect.left,y=e.clientY-rect.top;
    const old=Math.max(.01,Number(previewZoom||1)),next=Math.min(8,Math.max(.25,old*(e.deltaY<0?1.12:1/1.12)));
    const oldLeft=viewer.scrollLeft,oldTop=viewer.scrollTop;setPreviewZoom(next);
    requestAnimationFrame(()=>{const ratio=next/old;viewer.scrollLeft=(oldLeft+x)*ratio-x;viewer.scrollTop=(oldTop+y)*ratio-y;updateStatusBar()});
  },{passive:false});
}

document.body.classList.add('cew-professional-document');makeCanvasShell();makeSidebar();makeInspector();makeStatusBar();ensurePreviewControls();compactViewportControls();enableWheelZoom();professionalRender();
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
                "X-CEW-Document-Workbench": "PROFESSIONAL_V1",
            },
        )

    return router
