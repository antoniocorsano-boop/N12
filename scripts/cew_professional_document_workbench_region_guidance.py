#!/usr/bin/env python3
"""Non-semantic region guidance for CEW Document Discovery.

This layer does not try to decide what a drawing means. It proposes spatial
working regions from whitespace/content density on the already rendered page,
lets the operator accept one proposal or draw one corrective ROI, and focuses
the existing viewer on that region. The original document remains the evidence
authority; region proposals are transient reading/workflow aids only.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_governed_async as governed_async


_REGION_STYLE = r'''<style id="cew-region-guidance-style">
body.cew-professional-document[data-cew-region-guidance="v1"] #preview-regions[aria-pressed="true"],
body.cew-professional-document[data-cew-region-guidance="v1"] #preview-roi[aria-pressed="true"]{
  background:#44515b!important;box-shadow:inset 0 0 0 1px #8bc4e8!important;
}
#cew-region-overlay{position:absolute;inset:0;z-index:5;pointer-events:none}
#cew-region-overlay .cew-region-proposal{
  position:absolute;pointer-events:auto;border:2px dashed #1b83b8;background:#1b83b812;
  padding:0;border-radius:3px;cursor:pointer;
}
#cew-region-overlay .cew-region-proposal:hover,#cew-region-overlay .cew-region-proposal:focus-visible{
  border-style:solid;background:#1b83b824;outline:2px solid #8bc4e8;outline-offset:1px;
}
#cew-region-overlay .cew-region-proposal.active{border-style:solid;border-width:3px;background:#17415f20}
#cew-region-overlay .cew-roi-draft{position:absolute;border:2px solid #b66a00;background:#e79a2518;pointer-events:none}
.cew-region-pill{display:inline-flex;align-items:center;height:20px;padding:0 7px;border-radius:10px;background:#e7ecef;color:#53616c;font-size:9px;font-weight:750;white-space:nowrap}
</style>'''


_REGION_SCRIPT = r'''<script id="cew-region-guidance-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
const regionState={regions:[],visible:true,roi:false,drag:null,active:null,lastImageKey:''};
document.body.dataset.cewRegionGuidance='v1';

function clamp(n,min,max){return Math.min(max,Math.max(min,Number(n)||0))}
function overlay(){
  const stage=ce('page-stage');if(!stage)return null;
  let el=ce('cew-region-overlay');
  if(!el){el=document.createElement('div');el.id='cew-region-overlay';stage.appendChild(el)}
  return el;
}
function bboxArea(b){return Math.max(0,Number(b?.w||0))*Math.max(0,Number(b?.h||0))}
function underSegmented(){
  const groups=Number(state?.graphic_cluster_count||0);
  const maxArea=Math.max(0,...(state?.clusters||[]).map(c=>bboxArea(c?.representative?.bbox)));
  return groups<=4||maxArea>=0.22;
}
function setRegionNote(text){
  let pill=ce('cew-region-pill');const meta=document.querySelector('.cew-editor-meta');if(!meta)return;
  if(!pill){pill=document.createElement('span');pill.id='cew-region-pill';pill.className='cew-region-pill optional';meta.insertBefore(pill,meta.firstChild)}
  pill.textContent=text;pill.title='Suddivisione spaziale non semantica: nessuna classificazione automatica';
}
function syncButtons(){
  const regions=ce('preview-regions'),roi=ce('preview-roi');
  if(regions){regions.setAttribute('aria-pressed',regionState.visible?'true':'false');regions.title='Mostra/nascondi aree proposte automaticamente'}
  if(roi){roi.setAttribute('aria-pressed',regionState.roi?'true':'false');roi.title=regionState.roi?'Disegna un’area sulla tavola':'Seleziona manualmente un’area di lavoro'}
  const viewer=ce('viewer');if(viewer&&regionState.roi)viewer.style.cursor='crosshair';
}
function ensureControls(){
  const bar=ce('preview-view-controls');if(!bar)return;
  let regions=ce('preview-regions');
  if(!regions){
    regions=document.createElement('button');regions.id='preview-regions';regions.type='button';regions.textContent='▦';regions.className='secondary';
    regions.setAttribute('aria-label','Aree proposte');
    const pan=ce('preview-pan');if(pan?.nextSibling)bar.insertBefore(regions,pan.nextSibling);else bar.appendChild(regions);
    regions.onclick=e=>{e.preventDefault();e.stopPropagation();regionState.visible=!regionState.visible;renderRegions();syncButtons()};
  }
  let roi=ce('preview-roi');
  if(!roi){
    roi=document.createElement('button');roi.id='preview-roi';roi.type='button';roi.textContent='▱';roi.className='secondary';roi.setAttribute('aria-label','Seleziona area di lavoro');
    if(regions.nextSibling)bar.insertBefore(roi,regions.nextSibling);else bar.appendChild(roi);
    roi.onclick=e=>{e.preventDefault();e.stopPropagation();regionState.roi=!regionState.roi;if(regionState.roi){ce('preview-pan')?.click()}syncButtons()};
  }
  syncButtons();wireRoi();
}

function imageMatrix(){
  const img=ce('page');if(!img||img.hidden||!img.naturalWidth||!img.naturalHeight)return null;
  const maxSide=360,scale=Math.min(1,maxSide/Math.max(img.naturalWidth,img.naturalHeight));
  const w=Math.max(40,Math.round(img.naturalWidth*scale)),h=Math.max(40,Math.round(img.naturalHeight*scale));
  const canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
  const ctx=canvas.getContext('2d',{willReadFrequently:true});if(!ctx)return null;
  ctx.drawImage(img,0,0,w,h);const data=ctx.getImageData(0,0,w,h).data;
  let sum=0,count=0;const lum=new Uint8Array(w*h);
  for(let i=0,p=0;i<data.length;i+=4,p++){
    const v=Math.round(.2126*data[i]+.7152*data[i+1]+.0722*data[i+2]);lum[p]=v;sum+=v;count++;
  }
  const mean=sum/Math.max(1,count),threshold=clamp(mean-20,125,230),ink=new Uint8Array(w*h);
  for(let i=0;i<lum.length;i++)ink[i]=lum[i]<threshold?1:0;
  return {w,h,ink,threshold};
}
function density(matrix,rect,axis,index){
  const {w,h,ink}=matrix;let hits=0,total=0;
  if(axis==='x'){
    const x=clamp(Math.round(index),0,w-1),y0=clamp(Math.floor(rect.y*h),0,h-1),y1=clamp(Math.ceil((rect.y+rect.h)*h),1,h);
    for(let y=y0;y<y1;y++){hits+=ink[y*w+x];total++}
  }else{
    const y=clamp(Math.round(index),0,h-1),x0=clamp(Math.floor(rect.x*w),0,w-1),x1=clamp(Math.ceil((rect.x+rect.w)*w),1,w);
    for(let x=x0;x<x1;x++){hits+=ink[y*w+x];total++}
  }
  return hits/Math.max(1,total);
}
function bestGutter(matrix,rect,axis){
  const dim=axis==='x'?matrix.w:matrix.h,start=Math.floor((axis==='x'?rect.x:rect.y)*dim),end=Math.ceil(((axis==='x'?rect.x+rect.w:rect.y+rect.h))*dim);
  const margin=Math.max(2,Math.floor((end-start)*.16)),lo=start+margin,hi=end-margin;if(hi-lo<8)return null;
  const limit=.018;let best=null,runStart=null;
  for(let i=lo;i<=hi;i++){
    const blank=i<hi&&density(matrix,rect,axis,i)<=limit;
    if(blank&&runStart===null)runStart=i;
    if((!blank||i===hi)&&runStart!==null){
      const runEnd=i-1,len=runEnd-runStart+1,center=(runStart+runEnd)/2;
      if(len>=Math.max(2,(end-start)*.018)&&(!best||len>best.len))best={center,len};
      runStart=null;
    }
  }
  return best;
}
function regionInk(matrix,rect){
  const x0=Math.floor(rect.x*matrix.w),x1=Math.ceil((rect.x+rect.w)*matrix.w),y0=Math.floor(rect.y*matrix.h),y1=Math.ceil((rect.y+rect.h)*matrix.h);let hits=0,total=0;
  for(let y=y0;y<y1;y+=2)for(let x=x0;x<x1;x+=2){hits+=matrix.ink[y*matrix.w+x];total++}
  return hits/Math.max(1,total);
}
function splitRegion(matrix,rect,depth,out){
  if(depth>=5||rect.w<.12||rect.h<.08){out.push(rect);return}
  const gx=bestGutter(matrix,rect,'x'),gy=bestGutter(matrix,rect,'y');
  let use=null,axis=null;
  if(gx&&gy){const nx=gx.len/(rect.w*matrix.w),ny=gy.len/(rect.h*matrix.h);if(nx>=ny){use=gx;axis='x'}else{use=gy;axis='y'}}else if(gx){use=gx;axis='x'}else if(gy){use=gy;axis='y'}
  if(!use){out.push(rect);return}
  if(axis==='x'){
    const cut=use.center/matrix.w,a={x:rect.x,y:rect.y,w:cut-rect.x,h:rect.h},b={x:cut,y:rect.y,w:rect.x+rect.w-cut,h:rect.h};
    if(a.w<.07||b.w<.07){out.push(rect);return}splitRegion(matrix,a,depth+1,out);splitRegion(matrix,b,depth+1,out);
  }else{
    const cut=use.center/matrix.h,a={x:rect.x,y:rect.y,w:rect.w,h:cut-rect.y},b={x:rect.x,y:cut,w:rect.w,h:rect.y+rect.h-cut};
    if(a.h<.05||b.h<.05){out.push(rect);return}splitRegion(matrix,a,depth+1,out);splitRegion(matrix,b,depth+1,out);
  }
}
function proposeRegions(){
  const matrix=imageMatrix();if(!matrix)return [];
  const out=[];splitRegion(matrix,{x:0,y:0,w:1,h:1},0,out);
  return out.filter(r=>r.w*r.h>=.012&&r.w*r.h<=.72&&regionInk(matrix,r)>=.0025).slice(0,24).map((r,i)=>({...r,id:`AR-${i+1}`}));
}
function renderRegions(){
  const el=overlay();if(!el)return;el.innerHTML='';
  if(!regionState.visible)return;
  for(const r of regionState.regions){
    const b=document.createElement('button');b.type='button';b.className='cew-region-proposal'+(regionState.active===r.id?' active':'');b.dataset.regionId=r.id;
    b.style.left=`${r.x*100}%`;b.style.top=`${r.y*100}%`;b.style.width=`${r.w*100}%`;b.style.height=`${r.h*100}%`;
    b.title=`Area proposta ${r.id} · suddivisione spaziale non semantica`;b.setAttribute('aria-label',`Apri area proposta ${r.id}`);
    b.onclick=e=>{e.preventDefault();e.stopPropagation();focusRegion(r)};el.appendChild(b);
  }
}
function focusRegion(r){
  regionState.active=r.id;renderRegions();
  ce('preview-overview')?.click();
  const target=Math.min(8,Math.max(1.15,Math.min(.86/Math.max(.04,r.w),.78/Math.max(.04,r.h))));
  requestAnimationFrame(()=>{setPreviewZoom(target);requestAnimationFrame(()=>{const button=ce('cew-region-overlay')?.querySelector(`[data-region-id="${r.id}"]`);button?.scrollIntoView({block:'center',inline:'center'});setRegionNote(`Area di lavoro ${r.id}`)})});
}
function refreshProposals(force=false){
  const img=ce('page');if(!img||img.hidden||!img.naturalWidth)return;
  const key=`${session||''}:${currentPreviewPageIndex||0}:${img.naturalWidth}x${img.naturalHeight}`;
  if(!force&&regionState.lastImageKey===key)return;regionState.lastImageKey=key;
  regionState.active=null;regionState.regions=proposeRegions();regionState.visible=underSegmented();renderRegions();
  setRegionNote(regionState.regions.length?`${regionState.regions.length} aree proposte`:'Nessuna area proposta');syncButtons();
}

function pointOnImage(e){
  const img=ce('page');if(!img||img.hidden)return null;const r=img.getBoundingClientRect();if(r.width<2||r.height<2)return null;
  return {x:clamp((e.clientX-r.left)/r.width,0,1),y:clamp((e.clientY-r.top)/r.height,0,1)};
}
function wireRoi(){
  const viewer=ce('viewer');if(!viewer||viewer.dataset.cewRoiReady==='1')return;viewer.dataset.cewRoiReady='1';
  viewer.addEventListener('pointerdown',e=>{
    if(!regionState.roi||e.button!==0||e.target.closest('#preview-view-controls'))return;
    const p=pointOnImage(e);if(!p)return;e.preventDefault();e.stopImmediatePropagation();regionState.drag={id:e.pointerId,start:p,current:p};try{viewer.setPointerCapture?.(e.pointerId)}catch(_){}drawDraft();
  },true);
  viewer.addEventListener('pointermove',e=>{if(!regionState.drag||regionState.drag.id!==e.pointerId)return;const p=pointOnImage(e);if(!p)return;regionState.drag.current=p;drawDraft()},true);
  const end=e=>{
    const d=regionState.drag;if(!d||d.id!==e.pointerId)return;const a=d.start,b=d.current;regionState.drag=null;const x=Math.min(a.x,b.x),y=Math.min(a.y,b.y),w=Math.abs(a.x-b.x),h=Math.abs(a.y-b.y);
    if(w>=.015&&h>=.015){const r={id:'ROI-1',x,y,w,h,manual:true};regionState.regions=[r];regionState.visible=true;regionState.roi=false;focusRegion(r)}else renderRegions();syncButtons();
  };
  viewer.addEventListener('pointerup',end,true);viewer.addEventListener('pointercancel',end,true);
}
function drawDraft(){
  const el=overlay();if(!el)return;renderRegions();const d=regionState.drag;if(!d)return;const a=d.start,b=d.current,x=Math.min(a.x,b.x),y=Math.min(a.y,b.y),w=Math.abs(a.x-b.x),h=Math.abs(a.y-b.y);
  const box=document.createElement('div');box.className='cew-roi-draft';box.style.left=`${x*100}%`;box.style.top=`${y*100}%`;box.style.width=`${w*100}%`;box.style.height=`${h*100}%`;el.appendChild(box);
}

function install(){ensureControls();const img=ce('page');if(img&&img.dataset.cewRegionLoad!=='1'){img.dataset.cewRegionLoad='1';img.addEventListener('load',()=>setTimeout(()=>refreshProposals(true),80))}if(img?.complete&&img.naturalWidth)refreshProposals(false)}
const observer=new MutationObserver(()=>requestAnimationFrame(install));observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['hidden','class']});
install();
window.CEWRegionGuidance={refresh:()=>refreshProposals(true),regions:()=>regionState.regions.map(r=>({...r})),focus:id=>{const r=regionState.regions.find(x=>x.id===id);if(r)focusRegion(r)}};
})();
</script>'''


def _patched_page() -> str:
    html = governed_async._patched_page()
    if "</head>" not in html or "</body>" not in html:
        raise RuntimeError("CEW_REGION_GUIDANCE_HTML_MARKER_MISSING")
    html = html.replace("</head>", _REGION_STYLE + "</head>", 1)
    html = html.replace("</body>", _REGION_SCRIPT + "</body>", 1)
    return html


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def region_guided_page():
        return HTMLResponse(
            _patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Document-Workbench": "PROFESSIONAL_V2",
                "X-CEW-Panel-Quality": "MATURE_V1",
                "X-CEW-Region-Guidance": "AUTO_LAYOUT_PLUS_HUMAN_ROI_V1",
                "X-CEW-Region-Semantic-Authority": "NONE",
            },
        )

    return router
