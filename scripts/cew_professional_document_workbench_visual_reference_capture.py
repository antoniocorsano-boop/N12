#!/usr/bin/env python3
"""Interaction hardening for CEW reference-first visual selection.

When the operator is drawing a visual reference, the floating viewport toolbar
and the capture-phase pan controller must yield pointer ownership to the drawing
surface. During selection the transparent selector is temporarily portaled above
the viewer, so mature pan handlers cannot intercept the gesture. This layer
changes neither similarity logic nor semantic/canonical authority.
"""
from __future__ import annotations

import cew_professional_document_workbench_visual_reference_search as visual_reference_search


_STYLE = r'''<style id="cew-visual-reference-capture-style">
body[data-cew-visual-reference-capture="active"] #preview-view-controls{
  pointer-events:none!important;
  opacity:.42;
}
body[data-cew-visual-reference-capture="active"] #cew-visual-select-layer{
  cursor:crosshair;
}
</style>'''


_SCRIPT = r'''<script id="cew-visual-reference-capture-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
let watchedSelector=null;
let selectorObserver=null;
let domSyncPending=false;
let portaled=false;
function mode(){return window.CEWVisualReferenceSearch?.state?.().mode||'IDLE'}
function selectorActive(){return !!ce('cew-visual-select-layer')?.classList.contains('active')}
function setCapture(active){
  document.body.dataset.cewVisualReferenceCapture=active?'active':'idle';
  const controls=ce('preview-view-controls');
  if(controls){
    controls.setAttribute('aria-disabled',active?'true':'false');
    controls.title=active?'Comandi vista e Pan sospesi mentre disegni il riferimento. Premi Esc o usa Nuovo riferimento per annullare.':'';
  }
}
function portalSelector(active){
  const selector=ce('cew-visual-select-layer'),img=ce('page'),stage=ce('page-stage');
  if(!selector)return;
  if(active){
    const r=img?.getBoundingClientRect();
    if(!r||r.width<2||r.height<2)return;
    if(selector.parentElement!==document.body)document.body.appendChild(selector);
    selector.style.position='fixed';
    selector.style.inset='auto';
    selector.style.left=`${r.left}px`;
    selector.style.top=`${r.top}px`;
    selector.style.width=`${r.width}px`;
    selector.style.height=`${r.height}px`;
    selector.style.zIndex='2147483000';
    portaled=true;
    return;
  }
  if(portaled&&stage&&selector.parentElement!==stage)stage.appendChild(selector);
  for(const prop of ['position','inset','left','top','width','height','zIndex'])selector.style[prop]='';
  portaled=false;
}
function sync(){
  const active=selectorActive()||mode()==='SELECTING';
  portalSelector(active);
  setCapture(active);
}
function watchSelector(){
  const selector=ce('cew-visual-select-layer');
  if(!selector||selector===watchedSelector)return;
  selectorObserver?.disconnect();
  watchedSelector=selector;
  selectorObserver=new MutationObserver(()=>sync());
  selectorObserver.observe(selector,{attributes:true,attributeFilter:['class']});
  sync();
}
function scheduleDomSync(){
  if(domSyncPending)return;
  domSyncPending=true;
  requestAnimationFrame(()=>{domSyncPending=false;watchSelector();sync()});
}

document.addEventListener('click',e=>{
  const id=e.target?.id;
  if(id==='cew-reference-start'||id==='cew-reference-reset'||id==='cew-reference-search'){
    setTimeout(()=>{watchSelector();sync()},0);
  }
},true);

document.addEventListener('pointerup',()=>setTimeout(sync,0),true);
document.addEventListener('pointercancel',()=>setTimeout(sync,0),true);
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&(selectorActive()||mode()==='SELECTING')){
    e.preventDefault();
    window.CEWVisualReferenceSearch?.reset?.();
    setTimeout(sync,0);
  }
},true);
window.addEventListener('resize',()=>{if(selectorActive()||mode()==='SELECTING')portalSelector(true)});
window.addEventListener('scroll',()=>{if(selectorActive()||mode()==='SELECTING')portalSelector(true)},true);

const domObserver=new MutationObserver(()=>scheduleDomSync());
domObserver.observe(document.body,{childList:true,subtree:true});
const phaseObserver=new MutationObserver(()=>scheduleDomSync());
phaseObserver.observe(document.body,{attributes:true,attributeFilter:['data-cew-layout-phase']});
watchSelector();
sync();
})();
</script>'''


def _patched_page() -> str:
    html = visual_reference_search._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_VISUAL_REFERENCE_CAPTURE_HTML_MARKER_MISSING")
    html = html.replace("</head>", _STYLE + "</head>", 1)
    html = html.replace("</body>", _SCRIPT + "</body>", 1)
    return html
