#!/usr/bin/env python3
"""Readable local-focus interaction for CEW technical drawing review.

A confirmed ReadingUnit is a working viewport, not just a page-scale overlay.
Tall reading columns are fit by width and scrolled vertically; row-like units are
fit by height. Raw/global overlays are suppressed while working locally. Visual
search results can be inspected one by one without changing semantic authority or
the source ReadingUnit used by the search.
"""
from __future__ import annotations

import cew_professional_document_workbench_visual_reference_capture as visual_reference_capture


_STYLE = r'''<style id="cew-local-focus-style">
body.cew-professional-document[data-cew-local-focus="active"] #cluster-overlay,
body.cew-professional-document[data-cew-local-focus="active"] #box,
body.cew-professional-document[data-cew-local-focus="active"] #cew-region-overlay,
body.cew-professional-document[data-cew-local-focus="active"] #cew-local-overlay{
  display:none!important;
}
body.cew-professional-document[data-cew-local-focus="active"] #cew-layout-overlay .cew-layout-unit{
  display:none!important;
}
body.cew-professional-document[data-cew-local-focus="active"] #cew-layout-overlay .cew-layout-unit.active{
  display:block!important;
  background:transparent!important;
  border:2px solid #6f5aa6!important;
}
body.cew-professional-document[data-cew-local-focus="active"][data-cew-match-review="true"] #cew-layout-overlay .cew-layout-unit.active{
  display:none!important;
}
body.cew-professional-document[data-cew-local-focus="active"][data-cew-match-review="true"] #cew-layout-overlay .cew-layout-unit.cew-review-target{
  display:block!important;
  background:transparent!important;
  border:2px solid #17738f!important;
}
body.cew-professional-document[data-cew-visual-reference-capture="active"] #cew-layout-overlay .cew-layout-unit.active{
  border-color:transparent!important;
}
body.cew-professional-document[data-cew-local-focus="active"] #cew-layout-alternative,
body.cew-professional-document[data-cew-local-focus="active"] #cew-layout-teach{
  display:none!important;
}
body.cew-professional-document[data-cew-local-focus="active"] #cew-layout-phase-panel dl{
  display:none!important;
}
body.cew-professional-document[data-cew-local-focus="active"] #cew-layout-reset{
  margin-top:0;padding:6px 8px;font-size:10px;
}
#cew-reference-return{background:#e3e9ed!important;color:#25353f!important}
#cew-local-focus-mode{display:inline-flex;align-items:center;height:20px;padding:0 7px;border-radius:10px;background:#e7f0f5;color:#28556b;font-size:9px;font-weight:800;white-space:nowrap}
</style>'''


_SCRIPT = r'''<script id="cew-local-focus-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
const focusState={unitId:null,reviewUnitId:null,internalViewChange:false,token:0};
document.body.dataset.cewLocalFocus='none';
document.body.dataset.cewMatchReview='false';
document.body.dataset.cewLocalFocusPolicy='reading-unit-working-view-v1';

function clamp(n,min,max){return Math.min(max,Math.max(min,Number(n)||0))}
function units(){return window.CEWLayoutLearning?.units?.()||[]}
function phase(){return window.CEWLayoutPhaseGate?.state?.()||{confirmed:false,activeUnit:null}}
function unitById(id){return units().find(u=>u.id===id)||null}
function unitButton(id){return [...document.querySelectorAll('#cew-layout-overlay .cew-layout-unit')].find(b=>b.dataset.layoutUnit===id)||null}
function label(id){const n=(String(id||'').match(/(\d+)$/)||[])[1]||'?';return `U${n}`}
function raf2(fn){requestAnimationFrame(()=>requestAnimationFrame(fn))}
function clearTitles(){for(const b of document.querySelectorAll('#cew-layout-overlay .cew-layout-unit'))b.removeAttribute('title')}
function clearReviewTarget(){for(const b of document.querySelectorAll('#cew-layout-overlay .cew-layout-unit.cew-review-target'))b.classList.remove('cew-review-target');focusState.reviewUnitId=null;document.body.dataset.cewMatchReview='false'}
function setModePill(text=''){let pill=ce('cew-local-focus-mode');const meta=document.querySelector('.cew-editor-meta');if(!pill&&meta){pill=document.createElement('span');pill.id='cew-local-focus-mode';meta.insertBefore(pill,meta.firstChild)}if(pill){pill.hidden=!text;pill.textContent=text}}
function maxScroll(el,axis){return axis==='x'?Math.max(0,el.scrollWidth-el.clientWidth):Math.max(0,el.scrollHeight-el.clientHeight)}

function leaveLocalFocus(){
  focusState.token++;
  focusState.unitId=null;clearReviewTarget();
  document.body.dataset.cewLocalFocus='none';
  setModePill('');
}

function resetViewToOverview(){
  const overview=ce('preview-overview');
  if(overview){focusState.internalViewChange=true;overview.click();focusState.internalViewChange=false;return}
  try{setPreviewView('overview')}catch(_){}
}

function focusUnit(id,opts={}){
  const u=unitById(id),viewer=ce('viewer'),img=ce('page');if(!u||!viewer||!img||img.hidden)return false;
  const token=++focusState.token;
  focusState.unitId=id;
  clearReviewTarget();
  if(opts.review){const b=unitButton(id);if(b)b.classList.add('cew-review-target');focusState.reviewUnitId=id;document.body.dataset.cewMatchReview='true'}
  document.body.dataset.cewShowLocalDiagnostics='false';
  document.body.dataset.cewLocalFocus='pending';
  clearTitles();
  resetViewToOverview();
  raf2(()=>{
    if(token!==focusState.token)return;
    document.body.dataset.cewLocalFocus='active';
    clearTitles();
    const b=unitButton(id),vr=viewer.getBoundingClientRect(),br=b?.getBoundingClientRect();if(!b||!br||br.width<2||br.height<2)return;
    const column=Number(u.h)>=Number(u.w)*1.45;
    const targetPixels=column?vr.width*.72:vr.height*.68;
    const currentPixels=column?br.width:br.height;
    const factor=clamp(targetPixels/Math.max(1,currentPixels),1.15,5.0);
    try{setPreviewZoom(factor)}catch(_){return}
    raf2(()=>{
      if(token!==focusState.token)return;
      const vr2=viewer.getBoundingClientRect(),br2=b.getBoundingClientRect(),ir=img.getBoundingClientRect();
      const desiredX=vr2.left+vr2.width*.49;
      viewer.scrollLeft=clamp(viewer.scrollLeft+(br2.left+br2.width/2-desiredX),0,maxScroll(viewer,'x'));
      if(opts.targetY!=null){
        const targetScreenY=ir.top+clamp(opts.targetY,0,1)*ir.height;
        viewer.scrollTop=clamp(viewer.scrollTop+(targetScreenY-(vr2.top+vr2.height*.46)),0,maxScroll(viewer,'y'));
      }else if(column){
        viewer.scrollTop=clamp(viewer.scrollTop+(br2.top-(vr2.top+14)),0,maxScroll(viewer,'y'));
      }else{
        viewer.scrollTop=clamp(viewer.scrollTop+(br2.top+br2.height/2-(vr2.top+vr2.height*.48)),0,maxScroll(viewer,'y'));
      }
      document.body.dataset.cewLocalFocus='active';
      setModePill(`${label(id)} · vista di lavoro`);
      const summary=ce('cew-local-summary');if(summary&&!opts.review)summary.textContent=`Unità ${label(id)} in vista di lavoro. Scorri nella tavola e scegli il dettaglio da verificare; i segnali diagnostici restano nascosti.`;
      if(opts.review&&summary)summary.textContent=`Risultato ${label(id)} in vista di lavoro. Questa è solo una corrispondenza grafica da verificare.`;
    });
  });
  return true;
}

function focusActive(){const p=phase();return !!(p.confirmed&&p.activeUnit&&focusUnit(p.activeUnit))}

function ensureReturnButton(){
  const host=ce('cew-visual-search');if(!host||ce('cew-reference-return'))return;
  const b=document.createElement('button');b.id='cew-reference-return';b.type='button';b.hidden=true;b.textContent='Torna al riferimento';
  b.addEventListener('click',()=>{const s=window.CEWVisualReferenceSearch?.state?.();if(s?.activeUnit){focusUnit(s.activeUnit);b.hidden=true}});
  const list=ce('cew-visual-results-list');if(list?.nextSibling)host.insertBefore(b,list.nextSibling);else host.appendChild(b);
}

function wireResultRows(){
  const api=window.CEWVisualReferenceSearch;if(!api?.state)return;const s=api.state();
  const rows=[...document.querySelectorAll('#cew-visual-results-list label')];
  for(const row of rows){
    if(row.dataset.cewFocusWired==='1')continue;row.dataset.cewFocusWired='1';row.style.cursor='pointer';row.title='Apri questa corrispondenza nella vista di lavoro';
    row.addEventListener('click',e=>{
      if(e.target?.matches?.('input'))return;
      e.preventDefault();
      const m=(row.textContent||'').match(/U(\d+)/),id=m?`LU-${m[1]}`:null,match=id?s.matches.find(x=>x.unitId===id):null;if(!id||!match)return;
      focusUnit(id,{review:true,targetY:Number(match.rect?.y||0)+Number(match.rect?.h||0)/2});
      const back=ce('cew-reference-return');if(back)back.hidden=false;
    });
  }
  const back=ce('cew-reference-return');if(back&&s.mode!=='RESULTS')back.hidden=true;
}

function wrapPhaseGate(){
  const api=window.CEWLayoutPhaseGate;if(!api||api.__cewLocalFocusWrapped)return;api.__cewLocalFocusWrapped=true;
  if(typeof api.selectUnit==='function'){
    const original=api.selectUnit.bind(api);
    api.selectUnit=id=>{const result=original(id);queueMicrotask(()=>focusUnit(id));return result};
  }
}

function install(){wrapPhaseGate();ensureReturnButton();clearTitles();wireResultRows()}

// If the operator returned to an overview and immediately asks for a reference,
// restore a readable working view first, then enter rectangle selection.
document.addEventListener('click',e=>{
  const id=e.target?.id;
  if((id==='preview-overview'||id==='preview-width')&&!focusState.internalViewChange){leaveLocalFocus();return}
  if(id==='cew-layout-reset'||id==='cew-layout-alternative'){leaveLocalFocus();return}
  if(id==='cew-reference-start'&&document.body.dataset.cewLocalFocus!=='active'){
    const p=phase();if(!p.confirmed||!p.activeUnit)return;
    e.preventDefault();e.stopImmediatePropagation();
    focusUnit(p.activeUnit);
    setTimeout(()=>window.CEWVisualReferenceSearch?.start?.(),120);
  }
},true);

const observer=new MutationObserver(()=>requestAnimationFrame(()=>{install();wireResultRows()}));
observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['data-cew-layout-phase','data-cew-visual-reference-capture']});
install();
window.CEWLocalFocus={focus:focusUnit,active:focusActive,leave:leaveLocalFocus,state:()=>({...focusState,mode:document.body.dataset.cewLocalFocus||'none',matchReview:document.body.dataset.cewMatchReview==='true'})};
})();
</script>'''


def _patched_page() -> str:
    html = visual_reference_capture._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_LOCAL_FOCUS_HTML_MARKER_MISSING")
    html = html.replace("</head>", _STYLE + "</head>", 1)
    html = html.replace("</body>", _SCRIPT + "</body>", 1)
    return html
