#!/usr/bin/env python3
"""Interaction hardening for CEW reference-first visual selection.

When the operator is drawing a visual reference, the floating viewport toolbar
must yield pointer ownership to the drawing surface. This is an interaction-only
layer: it changes neither visual similarity logic nor semantic/canonical authority.
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
function mode(){return window.CEWVisualReferenceSearch?.state?.().mode||'IDLE'}
function setCapture(active){
  document.body.dataset.cewVisualReferenceCapture=active?'active':'idle';
  const controls=ce('preview-view-controls');
  if(controls){
    controls.setAttribute('aria-disabled',active?'true':'false');
    controls.title=active?'Comandi vista sospesi mentre disegni il riferimento. Usa Nuovo riferimento per annullare.':'';
  }
}
function sync(){setCapture(mode()==='SELECTING')}

document.addEventListener('click',e=>{
  const id=e.target?.id;
  if(id==='cew-reference-start'||id==='cew-reference-reset'||id==='cew-reference-search')queueMicrotask(sync);
},true);

document.addEventListener('pointerup',e=>{
  if(e.target?.id==='cew-visual-select-layer'||e.target?.closest?.('#cew-visual-select-layer'))queueMicrotask(sync);
},true);
document.addEventListener('pointercancel',()=>queueMicrotask(sync),true);
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&mode()==='SELECTING'){
    e.preventDefault();
    window.CEWVisualReferenceSearch?.reset?.();
    queueMicrotask(sync);
  }
},true);

const observer=new MutationObserver(()=>sync());
observer.observe(document.body,{attributes:true,attributeFilter:['data-cew-layout-phase']});
setCapture(false);
})();
</script>'''


def _patched_page() -> str:
    html = visual_reference_search._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_VISUAL_REFERENCE_CAPTURE_HTML_MARKER_MISSING")
    html = html.replace("</head>", _STYLE + "</head>", 1)
    html = html.replace("</body>", _SCRIPT + "</body>", 1)
    return html
