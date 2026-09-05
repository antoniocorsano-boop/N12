#!/usr/bin/env python3
"""Async/bounded preview adapter for the CEW Document Discovery Workbench.

Mounted before the original Document Discovery router. It shadows only the HTML
workspace route so the Preview button uses enqueue + polling, while all existing
session/learning endpoints remain provided by the preserved workbench router.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

import cew_document_discovery as discovery
import cew_document_discovery_preview_engine as preview_engine
import cew_document_discovery_preview_jobs as preview_jobs
import cew_document_discovery_workbench as base_workbench


LOGGER = logging.getLogger(__name__)

_ASYNC_SCRIPT = r'''<script>
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function showPreviewPage(pageIndex=0){
  if(!session)return;
  candidateId=null;
  q('box').hidden=true;
  q('viewer-placeholder').hidden=true;
  const img=q('page');
  img.hidden=false;
  img.src=`/api/workbench/document-discovery/session/${encodeURIComponent(session)}/page/${pageIndex}.jpg`;
}
const baseRender=render;
render=function(){
  baseRender();
  if(state?.page_count>0&&(!state.clusters||state.clusters.length===0)&&session)showPreviewPage(0);
};
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
      if(state?.page_count>0)showPreviewPage(0);
      intakeMessage(`Preview inconcludente${mode}${coverage} · ${done.reason||'evidenza insufficiente'}. Pagina osservabile; training bloccato.`,'error');
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

    return router
