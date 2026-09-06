#!/usr/bin/env python3
"""Browser/runtime recovery overlay for governed CEW document analysis.

The existing MATURE_V1/HVA-refined workbench remains the visual authority. This
layer only redirects the governed-source action to the bounded async job API and
reconstructs the analysis once if the Render process restarts and loses its
transient job/session state.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

import cew_professional_document_workbench_mature_content as mature_content


_GOVERNED_ASYNC_SCRIPT = r'''<script id="cew-governed-async-script">
(function(){
'use strict';
const ce=id=>document.getElementById(id);
const TRANSIENT_HTTP=new Set([502,503,504]);
const MAX_TRANSIENT_RETRIES=12;
const MAX_REBUILD_ATTEMPTS=1;
let governedContext=null;
let governedPageRetry=0;
let governedArtifactRecovery=false;
document.body.dataset.cewGovernedAnalysis='async-bounded-reconstruct-v1';

const sleepGoverned=ms=>new Promise(resolve=>setTimeout(resolve,ms));

async function governedFetch(url,options={},allowNotFound=false){
  let delay=500;
  for(let attempt=0;attempt<=MAX_TRANSIENT_RETRIES;attempt++){
    let response=null;
    try{
      response=await fetch(url,options);
    }catch(_){
      if(attempt>=MAX_TRANSIENT_RETRIES)throw Error('Runtime CEW non raggiungibile dopo i tentativi di recupero.');
      intakeMessage('Servizio temporaneamente non disponibile. Recupero automatico in corso…','busy');
      await sleepGoverned(delay);delay=Math.min(2500,Math.round(delay*1.35));continue;
    }
    if(TRANSIENT_HTTP.has(response.status)){
      if(attempt>=MAX_TRANSIENT_RETRIES)throw Error(`Runtime CEW ancora indisponibile · HTTP ${response.status}.`);
      intakeMessage(`Servizio temporaneamente non disponibile · HTTP ${response.status}. Recupero automatico in corso…`,'busy');
      await sleepGoverned(delay);delay=Math.min(2500,Math.round(delay*1.35));continue;
    }
    if(allowNotFound&&response.status===404)return {response,notFound:true};
    return {response,notFound:false};
  }
  throw Error('Runtime CEW non raggiungibile.');
}

async function enqueueGoverned(project,source){
  const {response}=await governedFetch('/api/workbench/document-discovery/analyze-governed-async',{
    method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:project,source_id:source})
  });
  return responseJson(response);
}

async function pollGoverned(jobId){
  for(let attempt=0;attempt<240;attempt++){
    await sleepGoverned(750);
    const result=await governedFetch(`/api/workbench/document-discovery/governed-job/${encodeURIComponent(jobId)}`,{},true);
    if(result.notFound)return {state:'RUNTIME_JOB_LOST',job_id:jobId};
    const job=await responseJson(result.response);
    if(job.state==='READY'||job.state==='INCONCLUSIVE')return job;
    if(job.state==='FAILED')throw Error(job.reason||'Analisi della fonte governata fallita.');
    intakeMessage(`Analisi della fonte ${job.state==='QUEUED'?'in coda':'in corso'}…`,'busy');
  }
  throw Error('Analisi ancora in corso oltre il tempo di attesa dell’interfaccia.');
}

async function loadGovernedSession(sessionId){
  const result=await governedFetch(`/api/workbench/document-discovery/session/${encodeURIComponent(sessionId)}`,{},true);
  if(result.notFound)return false;
  state=await responseJson(result.response);
  render();
  return true;
}

async function executeGoverned(project,source,rebuildAttempt=0){
  const queued=await enqueueGoverned(project,source);
  intakeMessage(`Fonte acquisita · analisi grafica avviata.`,'busy');
  const done=await pollGoverned(queued.job_id);
  if(done.state==='RUNTIME_JOB_LOST'){
    if(rebuildAttempt>=MAX_REBUILD_ATTEMPTS)throw Error('Il runtime CEW si è riavviato più volte durante la stessa analisi. Ripeti Analizza fonte.');
    intakeMessage('Il runtime CEW è stato riavviato. Ricostruzione automatica dalla fonte governata…','busy');
    return executeGoverned(project,source,rebuildAttempt+1);
  }
  session=done.session_id;clusterId=null;
  const loaded=await loadGovernedSession(session);
  if(!loaded){
    if(rebuildAttempt>=MAX_REBUILD_ATTEMPTS)throw Error('La sessione è stata persa dopo un nuovo riavvio del runtime. Ripeti Analizza fonte.');
    intakeMessage('La sessione non è più presente nel runtime. Ricostruzione automatica dalla fonte governata…','busy');
    session=null;state=null;resetViewer();
    return executeGoverned(project,source,rebuildAttempt+1);
  }
  governedContext={project,source,rebuildAttempt};
  governedPageRetry=0;
  const pages=Number(state?.page_count||0),elements=Number(state?.primitive_candidate_count||0),groups=Number(state?.graphic_cluster_count||0);
  if(done.state==='INCONCLUSIVE'){
    intakeMessage(`Analisi completata · ${pages} ${pages===1?'pagina':'pagine'} · evidenza grafica da verificare.`,'warn');
  }else{
    intakeMessage(`Analisi completata · ${pages} ${pages===1?'pagina':'pagine'} · ${elements} elementi · ${groups} gruppi candidati.`,'ok');
  }
  return done;
}

const analyze=ce('analyze');
if(analyze){
  analyze.onclick=async()=>{
    if(busy)return;
    const project=ce('project').value.trim(),source=ce('source').value;
    if(!project||!source){intakeMessage('Indica progetto e fonte governata.','error');return}
    governedContext={project,source,rebuildAttempt:0};
    setBusy(true,'Fonte governata: analisi grafica in corso…');
    resetViewer();
    try{await executeGoverned(project,source,0)}
    catch(error){
      const text=String(error?.message||error||'Errore analisi CEW.');
      intakeMessage(text,'error');
      if(ce('message'))ce('message').textContent=text;
    }finally{setBusy(false)}
  };
}

const pageImage=ce('page');
if(pageImage){
  pageImage.addEventListener('load',()=>{governedPageRetry=0});
  pageImage.addEventListener('error',()=>{
    if(!session||!governedContext||pageImage.hidden||governedArtifactRecovery)return;
    if(governedPageRetry<2){
      governedPageRetry+=1;
      const current=pageImage.getAttribute('src')||'';
      if(current){
        intakeMessage('Recupero della pagina in corso…','busy');
        setTimeout(()=>{pageImage.src=current.split('?')[0]+`?governed_retry=${Date.now()}`},650*governedPageRetry);
        return;
      }
    }
    const {project,source,rebuildAttempt}=governedContext;
    if(rebuildAttempt>=MAX_REBUILD_ATTEMPTS){
      intakeMessage('La pagina non è più disponibile dopo un ulteriore riavvio del runtime. Ripeti Analizza fonte.','error');
      return;
    }
    governedArtifactRecovery=true;
    session=null;state=null;clusterId=null;resetViewer();
    intakeMessage('La sessione è stata persa. Ricostruzione automatica dalla fonte governata…','busy');
    setBusy(true);
    executeGoverned(project,source,rebuildAttempt+1)
      .catch(error=>intakeMessage(String(error?.message||error),'error'))
      .finally(()=>{governedArtifactRecovery=false;setBusy(false)});
  });
}
})();
</script>'''


def _patched_page() -> str:
    html = mature_content._patched_page()
    if "</body>" not in html:
        raise RuntimeError("CEW_GOVERNED_ASYNC_HTML_MARKER_MISSING")
    return html.replace("</body>", _GOVERNED_ASYNC_SCRIPT + "</body>", 1)


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def governed_async_page():
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
                "X-CEW-Governed-Analysis": "ASYNC_BOUNDED_RECONSTRUCT_V1",
                "X-CEW-Preview-Runtime-Recovery": "BROWSER_RECONSTRUCT_V1",
            },
        )

    return router
