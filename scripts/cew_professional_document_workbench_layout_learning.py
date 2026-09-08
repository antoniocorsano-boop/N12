#!/usr/bin/env python3
"""Teach-one-relation layout learning for CEW Document Discovery.

This layer sits above non-semantic region guidance. It does not classify beams,
reinforcement, sections or any other engineering object. Instead it proposes
alternative page-layout hypotheses and lets the operator teach one spatial
relationship by drawing two boxes that belong to the same reading unit. CEW
then infers a transient LayoutPrototype and propagates that relationship across
the page using whitespace/ink geometry only.

The original governed document remains the evidentiary authority. Learned
layout prototypes are local workflow aids, never canonical structural data.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_region_guidance as region_guidance


_LAYOUT_STYLE = r'''<style id="cew-layout-learning-style">
body.cew-professional-document[data-cew-layout-view="units"] #cew-region-overlay{display:none}
body.cew-professional-document[data-cew-layout-learning="v1"] #preview-layout[aria-pressed="true"],
body.cew-professional-document[data-cew-layout-learning="v1"] #preview-teach-layout[aria-pressed="true"]{
  background:#44515b!important;box-shadow:inset 0 0 0 1px #8bc4e8!important;
}
#cew-layout-overlay{position:absolute;inset:0;z-index:6;pointer-events:none}
#cew-layout-overlay .cew-layout-unit{
  position:absolute;pointer-events:auto;border:2px dashed #6b5fa8;background:#6b5fa810;
  padding:0;border-radius:3px;cursor:pointer;
}
#cew-layout-overlay .cew-layout-unit:hover,#cew-layout-overlay .cew-layout-unit:focus-visible{
  border-style:solid;background:#6b5fa820;outline:2px solid #b3a9df;outline-offset:1px;
}
#cew-layout-overlay .cew-layout-unit.active{border-style:solid;border-width:3px;background:#6b5fa828}
#cew-layout-overlay .cew-layout-example{position:absolute;border:3px solid #b66a00;background:#e79a2516;pointer-events:none}
#cew-layout-overlay .cew-layout-example::before{
  content:attr(data-label);position:absolute;left:2px;top:2px;background:#fff8ec;color:#7b4a00;
  border:1px solid #d9aa68;border-radius:2px;padding:1px 4px;font-size:9px;font-weight:800;
}
#cew-layout-overlay .cew-layout-draft{position:absolute;border:2px solid #b66a00;background:#e79a2518;pointer-events:none}
.cew-layout-pill{display:inline-flex;align-items:center;height:20px;padding:0 7px;border-radius:10px;background:#eeeaf8;color:#5c527f;font-size:9px;font-weight:750;white-space:nowrap;cursor:pointer}
</style>'''


_LAYOUT_SCRIPT = r'''<script id="cew-layout-learning-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
const layoutState={
  hypotheses:[],activeHypothesis:0,units:[],visible:true,activeUnit:null,
  teach:false,teachBoxes:[],drag:null,restorePan:false,prototype:null,lastImageKey:''
};
document.body.dataset.cewLayoutLearning='v1';
document.body.dataset.cewLayoutView='units';

function clamp(n,min,max){return Math.min(max,Math.max(min,Number(n)||0))}
function overlap1d(a0,a1,b0,b1){return Math.max(0,Math.min(a1,b1)-Math.max(a0,b0))}
function unionBox(a,b){
  const x=Math.min(a.x,b.x),y=Math.min(a.y,b.y),r=Math.max(a.x+a.w,b.x+b.w),d=Math.max(a.y+a.h,b.y+b.h);
  return {x,y,w:r-x,h:d-y};
}
function inkArea(matrix,r){
  const x0=clamp(Math.floor(r.x*matrix.w),0,matrix.w-1),x1=clamp(Math.ceil((r.x+r.w)*matrix.w),1,matrix.w);
  const y0=clamp(Math.floor(r.y*matrix.h),0,matrix.h-1),y1=clamp(Math.ceil((r.y+r.h)*matrix.h),1,matrix.h);
  let hits=0,total=0;
  for(let y=y0;y<y1;y+=2)for(let x=x0;x<x1;x+=2){hits+=matrix.ink[y*matrix.w+x];total++}
  return hits/Math.max(1,total);
}
function matrix(){
  const img=ce('page');if(!img||img.hidden||!img.naturalWidth||!img.naturalHeight)return null;
  const maxSide=420,scale=Math.min(1,maxSide/Math.max(img.naturalWidth,img.naturalHeight));
  const w=Math.max(60,Math.round(img.naturalWidth*scale)),h=Math.max(60,Math.round(img.naturalHeight*scale));
  const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
  const ctx=canvas.getContext('2d',{willReadFrequently:true});if(!ctx)return null;
  ctx.drawImage(img,0,0,w,h);const data=ctx.getImageData(0,0,w,h).data;
  const lum=new Uint8Array(w*h);let sum=0;
  for(let i=0,p=0;i<data.length;i+=4,p++){
    const v=Math.round(.2126*data[i]+.7152*data[i+1]+.0722*data[i+2]);lum[p]=v;sum+=v;
  }
  const mean=sum/Math.max(1,lum.length),threshold=clamp(mean-22,120,228),ink=new Uint8Array(w*h);
  for(let i=0;i<lum.length;i++)ink[i]=lum[i]<threshold?1:0;
  return {w,h,ink,threshold};
}
function projection(m,axis,band){
  const dim=axis==='x'?m.w:m.h,out=new Float32Array(dim);
  if(axis==='x'){
    const y0=clamp(Math.floor((band?.y??0)*m.h),0,m.h-1),y1=clamp(Math.ceil(((band?.y??0)+(band?.h??1))*m.h),1,m.h);
    for(let x=0;x<m.w;x++){let hits=0,total=0;for(let y=y0;y<y1;y++){hits+=m.ink[y*m.w+x];total++}out[x]=hits/Math.max(1,total)}
  }else{
    const x0=clamp(Math.floor((band?.x??0)*m.w),0,m.w-1),x1=clamp(Math.ceil(((band?.x??0)+(band?.w??1))*m.w),1,m.w);
    for(let y=0;y<m.h;y++){let hits=0,total=0;for(let x=x0;x<x1;x++){hits+=m.ink[y*m.w+x];total++}out[y]=hits/Math.max(1,total)}
  }
  return Array.from(out);
}
function quantile(values,q){
  if(!values.length)return 0;const v=[...values].sort((a,b)=>a-b);const p=clamp(q,0,1)*(v.length-1),lo=Math.floor(p),hi=Math.ceil(p),t=p-lo;
  return v[lo]*(1-t)+v[hi]*t;
}
function axisSegments(m,axis,band=null){
  const p=projection(m,axis,band),dim=p.length,q20=quantile(p,.20),q50=quantile(p,.50);
  const blankLimit=clamp(Math.min(q50*.58,q20*1.8+.0025),.0015,.035);
  const minRun=Math.max(2,Math.floor(dim*.009));let runs=[],start=null;
  for(let i=0;i<=dim;i++){
    const blank=i<dim&&p[i]<=blankLimit;
    if(blank&&start===null)start=i;
    if((!blank||i===dim)&&start!==null){const end=i-1;if(end-start+1>=minRun)runs.push({start,end,center:(start+end)/2,len:end-start+1});start=null}
  }
  const cuts=runs.filter(r=>r.center>dim*.03&&r.center<dim*.97).map(r=>r.center/dim);
  const bounds=[0,...cuts,1].sort((a,b)=>a-b),raw=[];
  for(let i=0;i<bounds.length-1;i++){
    const s=bounds[i],e=bounds[i+1],size=e-s;if(size<.045)continue;
    const rect=axis==='x'?{x:s,y:band?.y??0,w:size,h:band?.h??1}:{x:band?.x??0,y:s,w:band?.w??1,h:size};
    if(inkArea(m,rect)<.0015)continue;raw.push(rect);
  }
  if(raw.length<2||raw.length>16)return {segments:[],score:0,blankLimit};
  const sizes=raw.map(r=>axis==='x'?r.w:r.h),median=quantile(sizes,.5),mad=quantile(sizes.map(v=>Math.abs(v-median)),.5);
  const regularity=clamp(1-mad/Math.max(.02,median),0,1),countScore=clamp(raw.length/6,0,1);
  const gutterScore=clamp(runs.reduce((s,r)=>s+r.len,0)/Math.max(1,dim)*4,0,1);
  return {segments:raw,score:.45*countScore+.35*regularity+.20*gutterScore,blankLimit};
}
function automaticHypotheses(){
  const m=matrix();if(!m)return [];
  const x=axisSegments(m,'x'),y=axisSegments(m,'y'),out=[];
  if(x.segments.length>=3)out.push({id:'LH-V',orientation:'VERTICAL_STACK',repeatAxis:'x',score:x.score,units:x.segments});
  if(y.segments.length>=3)out.push({id:'LH-H',orientation:'HORIZONTAL_SEQUENCE',repeatAxis:'y',score:y.score,units:y.segments});
  return out.sort((a,b)=>b.score-a.score);
}
function humanOrientation(o){return o==='VERTICAL_STACK'?'verticale':'orizzontale'}
function layoutOverlay(){
  const stage=ce('page-stage');if(!stage)return null;let el=ce('cew-layout-overlay');
  if(!el){el=document.createElement('div');el.id='cew-layout-overlay';stage.appendChild(el)}return el;
}
function setLayoutNote(text,title='Ipotesi geometrica di impaginazione · nessuna classificazione automatica'){
  const meta=document.querySelector('.cew-editor-meta');if(!meta)return;let pill=ce('cew-layout-pill');
  if(!pill){pill=document.createElement('span');pill.id='cew-layout-pill';pill.className='cew-layout-pill optional';meta.insertBefore(pill,meta.firstChild);pill.onclick=()=>cycleHypothesis()}
  pill.textContent=text;pill.title=title;
}
function syncControls(){
  const layout=ce('preview-layout'),teach=ce('preview-teach-layout'),viewer=ce('viewer');
  if(layout){layout.setAttribute('aria-pressed',layoutState.visible?'true':'false');layout.title=layoutState.visible?'Nascondi unità di layout':'Mostra unità di layout'}
  if(teach){teach.setAttribute('aria-pressed',layoutState.teach?'true':'false');teach.title=layoutState.teach?'Annulla insegnamento layout':'Insegna una relazione con due riquadri'}
  if(viewer&&layoutState.teach)viewer.style.cursor='crosshair';
  document.body.dataset.cewLayoutView=layoutState.visible?'units':'regions';
}
function ensureControls(){
  const bar=ce('preview-view-controls');if(!bar)return;
  let layout=ce('preview-layout');
  if(!layout){layout=document.createElement('button');layout.id='preview-layout';layout.type='button';layout.className='secondary';layout.textContent='▥';layout.setAttribute('aria-label','Unità di layout');const regions=ce('preview-regions');if(regions?.nextSibling)bar.insertBefore(layout,regions.nextSibling);else bar.appendChild(layout);layout.onclick=e=>{e.preventDefault();e.stopPropagation();layoutState.visible=!layoutState.visible;render();syncControls()}}
  let teach=ce('preview-teach-layout');
  if(!teach){teach=document.createElement('button');teach.id='preview-teach-layout';teach.type='button';teach.className='secondary';teach.textContent='⛓';teach.setAttribute('aria-label','Insegna relazione di layout');if(layout.nextSibling)bar.insertBefore(teach,layout.nextSibling);else bar.appendChild(teach);teach.onclick=e=>{e.preventDefault();e.stopPropagation();setTeach(!layoutState.teach)}}
  syncControls();wireTeach();
}
function render(){
  const el=layoutOverlay();if(!el)return;el.innerHTML='';
  if(layoutState.visible){
    for(const u of layoutState.units){
      const b=document.createElement('button');b.type='button';b.className='cew-layout-unit'+(layoutState.activeUnit===u.id?' active':'');b.dataset.layoutUnit=u.id;
      b.style.left=`${u.x*100}%`;b.style.top=`${u.y*100}%`;b.style.width=`${u.w*100}%`;b.style.height=`${u.h*100}%`;
      b.title=`Unità ${u.id} · layout ${humanOrientation(layoutState.prototype?.orientation||layoutState.hypotheses[layoutState.activeHypothesis]?.orientation)}`;
      b.setAttribute('aria-label',`Apri unità di layout ${u.id}`);b.onclick=e=>{e.preventDefault();e.stopPropagation();focusUnit(u)};el.appendChild(b);
    }
  }
  layoutState.teachBoxes.forEach((r,i)=>{const box=document.createElement('div');box.className='cew-layout-example';box.dataset.label=i===0?'A':'B';box.style.left=`${r.x*100}%`;box.style.top=`${r.y*100}%`;box.style.width=`${r.w*100}%`;box.style.height=`${r.h*100}%`;el.appendChild(box)});
}
function focusUnit(u){
  layoutState.activeUnit=u.id;render();ce('preview-overview')?.click();
  const target=Math.min(8,Math.max(1.15,Math.min(.86/Math.max(.04,u.w),.78/Math.max(.04,u.h))));
  requestAnimationFrame(()=>{setPreviewZoom(target);requestAnimationFrame(()=>ce('cew-layout-overlay')?.querySelector(`[data-layout-unit="${u.id}"]`)?.scrollIntoView({block:'center',inline:'center'}))});
  setLayoutNote(`Unità ${u.id} · layout ${humanOrientation(layoutState.prototype?.orientation||layoutState.hypotheses[layoutState.activeHypothesis]?.orientation)}`);
}
function setAutomatic(hypotheses){
  layoutState.prototype=null;layoutState.hypotheses=hypotheses;layoutState.activeHypothesis=0;layoutState.activeUnit=null;
  if(!hypotheses.length){layoutState.units=[];layoutState.visible=false;setLayoutNote('Layout da insegnare','Nessuna ipotesi di layout sufficientemente stabile. Usa Insegna relazione.');render();syncControls();return}
  const h=hypotheses[0];layoutState.units=h.units.map((r,i)=>({...r,id:`LU-${i+1}`}));layoutState.visible=true;
  const ambiguous=hypotheses.length>1&&Math.abs(h.score-hypotheses[1].score)<.14;
  setLayoutNote(`${ambiguous?'Ipotesi':'Layout proposto'} ${humanOrientation(h.orientation)} · ${layoutState.units.length} unità`,ambiguous?'Clicca per confrontare l’altra ipotesi; oppure insegna una relazione con ⛓.':'Ipotesi geometrica non semantica; clicca per confrontare eventuali alternative.');render();syncControls();
}
function cycleHypothesis(){
  if(layoutState.prototype||layoutState.hypotheses.length<2)return;
  layoutState.activeHypothesis=(layoutState.activeHypothesis+1)%layoutState.hypotheses.length;const h=layoutState.hypotheses[layoutState.activeHypothesis];layoutState.units=h.units.map((r,i)=>({...r,id:`LU-${i+1}`}));layoutState.activeUnit=null;layoutState.visible=true;setLayoutNote(`Ipotesi ${humanOrientation(h.orientation)} · ${layoutState.units.length} unità`,'Clicca di nuovo per confrontare l’altra ipotesi.');render();syncControls();
}
function pointOnImage(e){
  const img=ce('page');if(!img||img.hidden)return null;const r=img.getBoundingClientRect();if(r.width<2||r.height<2)return null;
  return {x:clamp((e.clientX-r.left)/r.width,0,1),y:clamp((e.clientY-r.top)/r.height,0,1)};
}
function setTeach(active){
  layoutState.teach=!!active;layoutState.drag=null;
  if(active){
    layoutState.teachBoxes=[];layoutState.visible=false;layoutState.restorePan=ce('preview-pan')?.getAttribute('aria-pressed')==='true';
    if(layoutState.restorePan)ce('preview-pan')?.click();
    const roi=ce('preview-roi');if(roi?.getAttribute('aria-pressed')==='true')roi.click();
    setLayoutNote('Insegna layout · seleziona il blocco ancora','Disegna un riquadro sul primo blocco della relazione. Nessun significato strutturale viene assegnato.');
  }else{
    if(layoutState.restorePan&&ce('preview-pan')?.getAttribute('aria-pressed')!=='true')ce('preview-pan')?.click();layoutState.restorePan=false;
  }
  render();syncControls();
}
function wireTeach(){
  const viewer=ce('viewer');if(!viewer||viewer.dataset.cewLayoutTeachReady==='1')return;viewer.dataset.cewLayoutTeachReady='1';
  viewer.addEventListener('pointerdown',e=>{
    if(!layoutState.teach||e.button!==0||e.target.closest('#preview-view-controls'))return;const p=pointOnImage(e);if(!p)return;
    e.preventDefault();e.stopImmediatePropagation();layoutState.drag={id:e.pointerId,start:p,current:p};try{viewer.setPointerCapture?.(e.pointerId)}catch(_){}drawDraft();
  },true);
  viewer.addEventListener('pointermove',e=>{const d=layoutState.drag;if(!d||d.id!==e.pointerId)return;const p=pointOnImage(e);if(!p)return;e.preventDefault();e.stopImmediatePropagation();d.current=p;drawDraft()},true);
  const end=e=>{
    const d=layoutState.drag;if(!d||d.id!==e.pointerId)return;e.preventDefault();e.stopImmediatePropagation();layoutState.drag=null;
    const a=d.start,b=d.current,r={x:Math.min(a.x,b.x),y:Math.min(a.y,b.y),w:Math.abs(a.x-b.x),h:Math.abs(a.y-b.y)};
    if(r.w<.015||r.h<.015){render();return}layoutState.teachBoxes.push(r);
    if(layoutState.teachBoxes.length===1){setLayoutNote('Ancora acquisita · ora seleziona i dettagli associati','Disegna il secondo riquadro che appartiene alla stessa unità di lettura.');render();return}
    teach(layoutState.teachBoxes[0],layoutState.teachBoxes[1]);setTeach(false);
  };
  viewer.addEventListener('pointerup',end,true);viewer.addEventListener('pointercancel',end,true);
}
function drawDraft(){
  render();const d=layoutState.drag,el=layoutOverlay();if(!d||!el)return;const a=d.start,b=d.current,r={x:Math.min(a.x,b.x),y:Math.min(a.y,b.y),w:Math.abs(a.x-b.x),h:Math.abs(a.y-b.y)};
  const box=document.createElement('div');box.className='cew-layout-draft';box.style.left=`${r.x*100}%`;box.style.top=`${r.y*100}%`;box.style.width=`${r.w*100}%`;box.style.height=`${r.h*100}%`;el.appendChild(box);
}
function inferPrototype(anchor,details){
  const ax0=anchor.x,ax1=anchor.x+anchor.w,ay0=anchor.y,ay1=anchor.y+anchor.h,dx0=details.x,dx1=details.x+details.w,dy0=details.y,dy1=details.y+details.h;
  const xov=overlap1d(ax0,ax1,dx0,dx1)/Math.max(.001,Math.min(anchor.w,details.w));
  const yov=overlap1d(ay0,ay1,dy0,dy1)/Math.max(.001,Math.min(anchor.h,details.h));
  const ac={x:anchor.x+anchor.w/2,y:anchor.y+anchor.h/2},dc={x:details.x+details.w/2,y:details.y+details.h/2};
  let orientation;
  if(dc.y>ac.y&&xov>=.20)orientation='VERTICAL_STACK';
  else if(dc.x>ac.x&&yov>=.20)orientation='HORIZONTAL_SEQUENCE';
  else orientation=Math.abs(dc.y-ac.y)>=Math.abs(dc.x-ac.x)?'VERTICAL_STACK':'HORIZONTAL_SEQUENCE';
  const union=unionBox(anchor,details);
  return {
    version:'LAYOUT_PROTOTYPE_V1',orientation,repeatAxis:orientation==='VERTICAL_STACK'?'x':'y',
    anchor:{...anchor},details:{...details},union,
    relation:{x_overlap:Number(xov.toFixed(4)),y_overlap:Number(yov.toFixed(4)),below:dc.y>ac.y,right_of:dc.x>ac.x},
    semantic_authority:'NONE',canonical_write_authorized:false,origin:'HUMAN_DEMONSTRATION'
  };
}
function propagate(proto){
  const m=matrix();if(!m)return [];
  const u=proto.union,pad=.015,band={x:clamp(u.x-pad,0,1),y:clamp(u.y-pad,0,1),w:clamp(u.w+2*pad,0,1),h:clamp(u.h+2*pad,0,1)};
  if(band.x+band.w>1)band.w=1-band.x;if(band.y+band.h>1)band.h=1-band.y;
  const result=axisSegments(m,proto.repeatAxis,band);const taughtSize=proto.repeatAxis==='x'?u.w:u.h;
  let segs=result.segments.filter(r=>{const s=proto.repeatAxis==='x'?r.w:r.h;return s>=taughtSize*.42&&s<=taughtSize*2.35});
  if(segs.length<2)segs=result.segments;
  if(proto.repeatAxis==='x')segs=segs.map(r=>({x:r.x,y:band.y,w:r.w,h:band.h}));
  else segs=segs.map(r=>({x:band.x,y:r.y,w:band.w,h:r.h}));
  if(segs.length<2)segs=[band];
  return segs.slice(0,16).map((r,i)=>({...r,id:`LP-${i+1}`}));
}
function storageKey(){const project=ce('project')?.value?.trim()||'NO_PROJECT',source=ce('source')?.value||'NO_SOURCE';return `cew.layoutPrototype.v1:${project}:${source}`}
function persistPrototype(){
  if(!layoutState.prototype)return;try{localStorage.setItem(storageKey(),JSON.stringify({prototype:layoutState.prototype,units:layoutState.units}))}catch(_){}
}
function restorePrototype(){
  try{const raw=localStorage.getItem(storageKey());if(!raw)return false;const saved=JSON.parse(raw);if(!saved?.prototype||!Array.isArray(saved?.units))return false;layoutState.prototype=saved.prototype;layoutState.units=saved.units;layoutState.hypotheses=[];layoutState.visible=true;layoutState.activeUnit=null;setLayoutNote(`Prototipo locale ${humanOrientation(saved.prototype.orientation)} · ${saved.units.length} unità`,'Appreso da una dimostrazione umana in questo browser; non è dato canonico. Usa ⛓ per sostituirlo.');render();syncControls();return true}catch(_){return false}
}
function teach(anchor,details){
  const proto=inferPrototype(anchor,details);layoutState.prototype=proto;layoutState.hypotheses=[];layoutState.units=propagate(proto);layoutState.visible=true;layoutState.activeUnit=null;persistPrototype();
  setLayoutNote(`Prototipo ${humanOrientation(proto.orientation)} · ${layoutState.units.length} unità`,'Relazione dedotta da un esempio umano. Nessuna identità strutturale assegnata.');render();syncControls();return {...proto};
}
function refresh(force=false){
  const img=ce('page');if(!img||img.hidden||!img.naturalWidth)return;const key=`${session||''}:${currentPreviewPageIndex||0}:${img.naturalWidth}x${img.naturalHeight}:${ce('source')?.value||''}`;
  if(!force&&layoutState.lastImageKey===key)return;layoutState.lastImageKey=key;layoutState.teachBoxes=[];layoutState.activeUnit=null;
  if(restorePrototype())return;setAutomatic(automaticHypotheses());
}
function install(){
  ensureControls();const img=ce('page');if(img&&img.dataset.cewLayoutLoad!=='1'){img.dataset.cewLayoutLoad='1';img.addEventListener('load',()=>setTimeout(()=>refresh(true),120))}
  if(img?.complete&&img.naturalWidth)refresh(false);
}
const observer=new MutationObserver(()=>requestAnimationFrame(install));observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class']});
install();
window.CEWLayoutLearning={
  refresh:()=>refresh(true),
  hypotheses:()=>layoutState.hypotheses.map(h=>({...h,units:h.units.map(u=>({...u}))})),
  prototype:()=>layoutState.prototype?JSON.parse(JSON.stringify(layoutState.prototype)):null,
  units:()=>layoutState.units.map(u=>({...u})),
  teach:(anchor,details)=>teach(anchor,details),
  cycle:()=>cycleHypothesis()
};
})();
</script>'''


def _patched_page() -> str:
    html = region_guidance._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_LAYOUT_LEARNING_HTML_MARKER_MISSING")
    html = html.replace("</head>", _LAYOUT_STYLE + "</head>", 1)
    html = html.replace("</body>", _LAYOUT_SCRIPT + "</body>", 1)
    return html


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def layout_learning_page():
        return HTMLResponse(
            _patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Document-Workbench": "PROFESSIONAL_V2",
                "X-CEW-Panel-Quality": "MATURE_V1",
                "X-CEW-Region-Guidance": "LAYOUT_PRIMITIVES_V1",
                "X-CEW-Layout-Learning": "HYPOTHESIS_PLUS_TEACH_ONE_RELATION_V1",
                "X-CEW-Layout-Semantic-Authority": "NONE",
                "X-CEW-Layout-Prototype-Persistence": "LOCAL_NON_CANONICAL_V1",
            },
        )

    return router
