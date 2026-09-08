#!/usr/bin/env python3
"""Async/bounded preview adapter for the CEW Document Discovery Workbench.

Mounted before the original Document Discovery router. It shadows the HTML
workspace, unregistered-preview enqueue/poll endpoints, and the preview page
image route. User PDFs are never opened or rasterized in the web process: page
inspection bytes are produced inside the isolated worker and served from the
transient session report.
"""
from __future__ import annotations

import base64
from hashlib import sha256
import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

import cew_document_discovery as discovery
import cew_document_discovery_preview_engine as preview_engine
import cew_document_discovery_preview_safe_jobs as preview_jobs
import cew_document_discovery_workbench as base_workbench


LOGGER = logging.getLogger(__name__)
MAX_PREVIEW_PAGE_ARTIFACT_BYTES = 6 * 1024 * 1024

_ASYNC_SCRIPT = r'''<script>
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let previewViewMode='overview';
let previewRotation=0;
let previewZoom=1;
let currentPreviewPageIndex=0;
let panDrag=null;

function ensureInspectionStage(){
  const img=q('page');
  const wrap=img.closest('.pagewrap');
  let stage=q('page-stage');
  if(!stage){
    stage=document.createElement('div');
    stage.id='page-stage';
    stage.style.cssText='position:absolute;left:0;top:0;transform-origin:0 0';
    const boxEl=q('box');
    wrap.insertBefore(stage,img);
    stage.appendChild(img);
    stage.appendChild(boxEl);
    const overlay=document.createElement('div');
    overlay.id='cluster-overlay';
    overlay.style.cssText='position:absolute;inset:0;z-index:3;pointer-events:none';
    stage.appendChild(overlay);
  }
  wrap.style.position='relative';
  return stage;
}

function ensurePreviewControls(){
  let bar=q('preview-view-controls');
  if(bar)return bar;
  const viewer=q('viewer');
  bar=document.createElement('div');
  bar.id='preview-view-controls';
  bar.style.cssText='position:absolute;z-index:6;top:8px;right:8px;display:flex;flex-wrap:wrap;justify-content:flex-end;gap:6px;max-width:min(96%,640px);padding:5px;background:#ffffffee;border:1px solid #bcc8d0;border-radius:8px;box-shadow:0 1px 5px #0002';
  const add=(id,label,handler,title='')=>{const b=document.createElement('button');b.id=id;b.className='secondary';b.textContent=label;b.title=title;b.style.padding='6px 8px';b.onclick=handler;bar.appendChild(b);return b};
  add('preview-overview','Panoramica',()=>setPreviewView('overview'),'Adatta l’intera tavola allo spazio disponibile');
  add('preview-width','Larghezza',()=>setPreviewView('width'),'Adatta la tavola alla larghezza disponibile');
  add('preview-zoom-out','Zoom −',()=>setPreviewZoom(previewZoom/1.25),'Riduci');
  add('preview-zoom-reset','100%',()=>setPreviewZoom(1),'Ripristina lo zoom della modalità corrente');
  add('preview-zoom-in','Zoom +',()=>setPreviewZoom(previewZoom*1.25),'Ingrandisci');
  add('preview-rotate-left','Ruota ↶',()=>rotatePreview(-90),'Ruota la tavola di 90° in senso antiorario');
  add('preview-rotate-right','Ruota ↷',()=>rotatePreview(90),'Ruota la tavola di 90° in senso orario');
  viewer.appendChild(bar);
  return bar;
}

function updatePreviewControlState(){
  ensurePreviewControls();
  const overview=q('preview-overview'),width=q('preview-width'),reset=q('preview-zoom-reset');
  if(overview)overview.style.outline=previewViewMode==='overview'?'2px solid #17415f':'none';
  if(width)width.style.outline=previewViewMode==='width'?'2px solid #17415f':'none';
  if(reset)reset.textContent=`${Math.round(previewZoom*100)}%`;
}

function setPreviewView(mode='overview'){
  previewViewMode=mode==='width'?'width':'overview';
  previewZoom=1;
  renderPageGeometry(true);
}

function setPreviewZoom(value){
  previewZoom=Math.min(8,Math.max(0.25,Number(value)||1));
  renderPageGeometry(false);
}

function rotatePreview(delta){
  previewRotation=((previewRotation+delta)%360+360)%360;
  renderPageGeometry(true);
}

function stageTransform(angle,w,h){
  if(angle===90)return `translate(${h}px,0px) rotate(90deg)`;
  if(angle===180)return `translate(${w}px,${h}px) rotate(180deg)`;
  if(angle===270)return `translate(0px,${w}px) rotate(270deg)`;
  return 'translate(0px,0px) rotate(0deg)';
}

function renderClusterHotspots(){
  const overlay=q('cluster-overlay');
  if(!overlay)return;
  overlay.innerHTML='';
  if(!state?.clusters?.length)return;
  for(const c of state.clusters){
    const r=c.representative;
    if(!r||Number(r.page_index)!==Number(currentPreviewPageIndex)||!r.bbox)continue;
    const b=r.bbox;
    const hit=document.createElement('button');
    hit.className='cluster-hotspot';
    hit.type='button';
    hit.dataset.clusterId=c.cluster_id;
    hit.title=`Seleziona ${c.feature_signature?.primitive_family||'cluster'} · ${c.cluster_id}`;
    const active=c.cluster_id===clusterId;
    hit.style.cssText=`position:absolute;left:${b.x*100}%;top:${b.y*100}%;width:${Math.max(b.w*100,0.9)}%;height:${Math.max(b.h*100,0.9)}%;min-width:10px;min-height:10px;padding:0;border:${active?3:2}px solid ${active?'#17415f':'#0877ba'};background:${active?'#17415f26':'#0877ba14'};border-radius:3px;pointer-events:auto;cursor:pointer;z-index:4`;
    hit.onclick=e=>{e.preventDefault();e.stopPropagation();clusterId=c.cluster_id;clusters();selected();box(r);renderClusterHotspots()};
    overlay.appendChild(hit);
  }
}

function renderPageGeometry(resetScroll=false){
  ensurePreviewControls();
  const img=q('page');
  if(!img||img.hidden||!img.naturalWidth||!img.naturalHeight){updatePreviewControlState();return}
  const viewer=q('viewer');
  const wrap=img.closest('.pagewrap');
  const stage=ensureInspectionStage();
  const angle=((previewRotation%360)+360)%360;
  const odd=angle===90||angle===270;
  const availableWidth=Math.max(240,viewer.clientWidth-28);
  const availableHeight=Math.max(220,viewer.clientHeight-28);
  const rotatedNaturalWidth=odd?img.naturalHeight:img.naturalWidth;
  const rotatedNaturalHeight=odd?img.naturalWidth:img.naturalHeight;
  let fitScale=previewViewMode==='width'
    ? availableWidth/rotatedNaturalWidth
    : Math.min(availableWidth/rotatedNaturalWidth,availableHeight/rotatedNaturalHeight);
  fitScale=Math.max(0.02,fitScale);
  const scale=fitScale*previewZoom;
  const w=Math.max(1,img.naturalWidth*scale);
  const h=Math.max(1,img.naturalHeight*scale);
  img.style.width=w+'px';img.style.height=h+'px';img.style.maxWidth='none';img.style.maxHeight='none';img.style.objectFit='contain';
  stage.style.width=w+'px';stage.style.height=h+'px';stage.style.transform=stageTransform(angle,w,h);
  wrap.style.width=(odd?h:w)+'px';wrap.style.height=(odd?w:h)+'px';
  renderClusterHotspots();
  updatePreviewControlState();
  if(resetScroll){viewer.scrollTop=0;viewer.scrollLeft=0}
}

function enableDragPan(){
  const viewer=q('viewer');
  if(viewer.dataset.panReady==='1')return;
  viewer.dataset.panReady='1';
  viewer.addEventListener('pointerdown',e=>{
    if(e.button!==0||e.target.closest('#preview-view-controls')||e.target.closest('.cluster-hotspot'))return;
    panDrag={id:e.pointerId,x:e.clientX,y:e.clientY,left:viewer.scrollLeft,top:viewer.scrollTop};
    viewer.setPointerCapture?.(e.pointerId);
    viewer.style.cursor='grabbing';
  });
  viewer.addEventListener('pointermove',e=>{
    if(!panDrag||panDrag.id!==e.pointerId)return;
    viewer.scrollLeft=panDrag.left-(e.clientX-panDrag.x);
    viewer.scrollTop=panDrag.top-(e.clientY-panDrag.y);
  });
  const end=e=>{if(!panDrag||panDrag.id!==e.pointerId)return;panDrag=null;viewer.style.cursor='default'};
  viewer.addEventListener('pointerup',end);viewer.addEventListener('pointercancel',end);
}

const baseResetViewer=resetViewer;
resetViewer=function(){
  baseResetViewer();
  previewRotation=0;previewZoom=1;previewViewMode='overview';currentPreviewPageIndex=0;
  const overlay=q('cluster-overlay');if(overlay)overlay.innerHTML='';
  const wrap=q('page').closest('.pagewrap');if(wrap){wrap.style.width='';wrap.style.height=''}
};

box=function(c){
  if(!c)return;
  candidateId=c.candidate_id;
  currentPreviewPageIndex=Number(c.page_index||0);
  const b=c.bbox,p=q('box'),img=q('page');
  ensureInspectionStage();
  p.hidden=false;p.style.left=b.x*100+'%';p.style.top=b.y*100+'%';p.style.width=b.w*100+'%';p.style.height=b.h*100+'%';
  q('viewer-placeholder').hidden=true;img.hidden=false;
  const src=`/api/workbench/document-discovery/session/${encodeURIComponent(session)}/page/${c.page_index}.jpg`;
  img.onload=()=>renderPageGeometry(false);
  if(img.getAttribute('src')!==src)img.src=src;else if(img.complete)renderPageGeometry(false);
};

function showPreviewPage(pageIndex=0,viewMode='overview'){
  if(!session)return;
  candidateId=null;currentPreviewPageIndex=Number(pageIndex||0);
  q('box').hidden=true;q('viewer-placeholder').hidden=true;
  const img=q('page');img.hidden=false;
  previewViewMode=viewMode==='width'?'width':'overview';previewZoom=1;
  ensureInspectionStage();ensurePreviewControls();enableDragPan();
  img.onload=()=>renderPageGeometry(true);
  img.src=`/api/workbench/document-discovery/session/${encodeURIComponent(session)}/page/${pageIndex}.jpg`;
  if(img.complete&&img.naturalWidth)renderPageGeometry(true);
}

const baseRender=render;
render=function(){
  baseRender();
  ensureInspectionStage();ensurePreviewControls();enableDragPan();
  if(state?.page_count>0&&(!state.clusters||state.clusters.length===0)&&session)showPreviewPage(0,'overview');
  else renderPageGeometry(false);
};
window.addEventListener('resize',()=>renderPageGeometry(false));

async function waitPreviewJob(jobId){
  for(let attempt=0;attempt<240;attempt++){
    await sleep(750);
    const j=await api(`/api/workbench/document-discovery/preview-job/${encodeURIComponent(jobId)}`);
    if(j.state==='READY'||j.state==='INCONCLUSIVE')return j;
    if(j.state==='FAILED')throw Error(j.reason||'Analisi preview fallita.');
    intakeMessage(`Analisi grafica ${j.state==='QUEUED'?'in coda':'in corso'}… Il browser può restare su questa pagina.`,'busy');
  }
  throw Error('Analisi preview ancora in corso oltre il tempo di attesa dell’interfaccia. Riprova lo stato senza reinviare il PDF.');
}
q('preview').onclick=async()=>{
  if(busy)return;
  try{
    const project=q('project').value.trim(),f=q('file').files[0];
    if(!project||!f)throw Error('Indica progetto e PDF.');
    if(f.size>maxPreviewBytes)throw Error(`${f.name} · ${mb(f.size)} supera il limite preview di ${mb(maxPreviewBytes)}.`);
    setBusy(true,`Upload ${f.name} · ${mb(f.size)}. Accodamento analisi…`);
    resetViewer();
    const r=await fetch(`/api/workbench/document-discovery/analyze-preview-async?project_id=${encodeURIComponent(project)}`,{
      method:'POST',headers:{'Content-Type':'application/pdf'},body:f
    });
    const queued=await responseJson(r);
    intakeMessage(`PDF ricevuto · job ${queued.job_id}. Analisi grafica in corso…`,'busy');
    const done=await waitPreviewJob(queued.job_id);
    session=done.session_id;clusterId=null;await load();
    const budget=state.preview_budget||{};
    const bounded=budget.truncated?' · preview limitata dal budget grafico':'';
    const mode=done.preview_fallback_used?' · raster tiled evidence':' · vettoriale';
    const coverage=done.minimum_page_coverage_ratio==null?'':` · copertura ${(100*done.minimum_page_coverage_ratio).toFixed(1)}%`;
    if(done.state==='INCONCLUSIVE'){
      if(state?.page_count>0)showPreviewPage(0,'overview');
      intakeMessage(`Preview inconcludente${mode}${coverage} · ${done.reason||'evidenza insufficiente'}. Pagina mostrata in panoramica; training bloccato.`,'error');
      q('message').textContent=`INCONCLUSIVE · ${done.reason||'evidenza raster insufficiente'} · nessuna classificazione automatica`;
      return;
    }
    intakeMessage(`Preview completata · ${state.page_count} pagine analizzate · ${state.primitive_candidate_count} primitive · ${state.graphic_cluster_count} cluster${mode}${coverage}${bounded}. Training bloccato.`,'ok');
  }catch(e){
    intakeMessage(e.message,'error');q('message').textContent=e.message;
  }finally{setBusy(false)}
};
</script>'''


def _patched_page() -> str:
    html = base_workbench._page()
    if "</body>" not in html:
        raise RuntimeError("DOCUMENT_DISCOVERY_HTML_BODY_MARKER_MISSING")
    return html.replace("</body>", _ASYNC_SCRIPT + "</body>", 1)


def _preview_artifact(session_id: str, page_index: int) -> bytes:
    session = discovery.get_session(session_id)
    if session.get("source_registration_state") != "UNREGISTERED_PREVIEW":
        # Governed-source analysis retains the existing route semantics. The
        # hard boundary here is specifically for unregistered user previews.
        return discovery.render_page(session_id, page_index)
    rows = session.get("report", {}).get("preview_page_images") or []
    selected = None
    for row in rows:
        if isinstance(row, dict) and int(row.get("page_index", -1)) == page_index:
            selected = row
            break
    if selected is None:
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_PAGE_ARTIFACT_MISSING")
    if selected.get("render_boundary") != "PROCESS_ISOLATED_WORKER":
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_PAGE_BOUNDARY_INVALID")
    encoded = str(selected.get("data_base64") or "")
    payload = base64.b64decode(encoded, validate=True)
    if not payload.startswith(b"\xff\xd8") or len(payload) > MAX_PREVIEW_PAGE_ARTIFACT_BYTES:
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_PAGE_ARTIFACT_INVALID")
    if sha256(payload).hexdigest() != str(selected.get("sha256") or "").lower():
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_PAGE_ARTIFACT_SHA_INVALID")
    return payload


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def page():
        return HTMLResponse(
            _patched_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Preview-Execution": "ASYNC_BOUNDED",
            },
        )

    @router.post("/api/workbench/document-discovery/analyze-preview-async")
    async def analyze_preview_async(request: Request, project_id: str = ""):
        try:
            if str(request.headers.get("content-type") or "").split(";", 1)[0].lower() != "application/pdf":
                raise ValueError("DOCUMENT_DISCOVERY_APPLICATION_PDF_REQUIRED")
            content_length = str(request.headers.get("content-length") or "").strip()
            if content_length and int(content_length) > discovery.MAX_PDF_BYTES:
                return base_workbench._json({
                    "state": "DOCUMENT_DISCOVERY_PREVIEW_TOO_LARGE",
                    "reason": "DOCUMENT_DISCOVERY_PREVIEW_TOO_LARGE",
                }, 413)
            payload = await request.body()
            job = preview_jobs.start_preview_job(payload, project_id)
            return base_workbench._json({
                **job,
                "preview_engine": preview_engine.PREVIEW_EXTRACTOR_VERSION,
                "preview_budget": {
                    "max_pages_analyzed": preview_engine.MAX_PREVIEW_PAGES_ANALYZED,
                    "max_vector_paths_per_page": preview_engine.MAX_VECTOR_PATHS_PER_PAGE,
                    "max_text_blocks_per_page": preview_engine.MAX_TEXT_BLOCKS_PER_PAGE,
                    "max_total_candidates": preview_engine.MAX_TOTAL_CANDIDATES,
                },
            }, 202)
        except ValueError:
            return base_workbench._json({
                "state": "DOCUMENT_DISCOVERY_PREVIEW_REJECTED",
                "reason": "DOCUMENT_DISCOVERY_PREVIEW_REJECTED",
            }, 400)
        except Exception:
            LOGGER.exception("DOCUMENT_DISCOVERY_PREVIEW_ENQUEUE_BLOCKED")
            return base_workbench._json({
                "state": "DOCUMENT_DISCOVERY_PREVIEW_ENQUEUE_BLOCKED",
                "reason": "DOCUMENT_DISCOVERY_INTERNAL_ERROR",
            }, 503)

    @router.get("/api/workbench/document-discovery/preview-job/{job_id}")
    def preview_job(job_id: str):
        try:
            return base_workbench._json(preview_jobs.preview_job_status(job_id))
        except ValueError:
            return base_workbench._json({
                "state": "DOCUMENT_DISCOVERY_PREVIEW_JOB_NOT_FOUND",
                "reason": "DOCUMENT_DISCOVERY_PREVIEW_JOB_NOT_FOUND",
            }, 404)

    @router.get("/api/workbench/document-discovery/session/{session_id}/page/{page_index}.jpg")
    def preview_page_image(session_id: str, page_index: int):
        try:
            payload = _preview_artifact(session_id, page_index)
            return Response(
                payload,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "no-store",
                    "X-CEW-Authority": "READING_AID_ONLY",
                    "X-CEW-Preview-Page-Render": "PROCESS_ISOLATED_CACHED",
                },
            )
        except (ValueError, TypeError, base64.binascii.Error):
            return base_workbench._json({
                "state": "DOCUMENT_DISCOVERY_PAGE_REJECTED",
                "reason": "DOCUMENT_DISCOVERY_REQUEST_REJECTED",
            }, 404)

    return router
