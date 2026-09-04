#!/usr/bin/env python3
"""FastAPI surface for CEW document-first discovery and project-local teaching."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from starlette.concurrency import run_in_threadpool

import cew_document_discovery as discovery


LOGGER = logging.getLogger(__name__)


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    body = dict(payload)
    body.setdefault("authority", dict(discovery.AUTHORITY))
    return JSONResponse(body, status_code=status_code, headers={"Cache-Control": "no-store"})


def _page() -> str:
    return r'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Document Discovery</title><style>
:root{--bg:#edf1f4;--panel:#fff;--ink:#18222b;--muted:#67747e;--line:#ccd5dc;--accent:#17415f;--ok:#1d704b;--bad:#a13232;--warn:#916000}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,sans-serif}header{padding:12px 15px;background:#fff;border-bottom:1px solid var(--line)}h1{font-size:19px;margin:0}header small,.meta{color:var(--muted);font-size:12px}.provider{padding:7px 10px;background:#f8fafb;border-bottom:1px solid var(--line)}.intake{display:flex;gap:7px;flex-wrap:wrap;padding:10px;background:#fff;border-bottom:1px solid var(--line)}.intake-status{flex-basis:100%;padding:7px 9px;border-radius:7px;background:#f3f5f7;border:1px solid #d9e0e5}.intake-status.busy{background:#e8f1f7;border-color:#9dbed2;color:#17415f}.intake-status.error{background:#fdecec;border-color:#dfa6a6;color:#842b2b}.intake-status.ok{background:#e9f6ef;border-color:#97c8ac;color:#205d40}input,select,textarea,button{font:inherit}input[type=text],select,textarea{border:1px solid var(--line);border-radius:7px;padding:8px;background:#fff}button{border:0;border-radius:7px;padding:9px 11px;font-weight:700}.primary{background:var(--accent);color:#fff}.secondary{background:#e3e9ed}.positive{background:var(--ok);color:#fff}.negative{background:var(--bad);color:#fff}.uncertain{background:var(--warn);color:#fff}.layout{display:grid;grid-template-columns:300px minmax(0,1fr) 340px;height:calc(100vh - 196px)}aside{background:#fff;padding:10px;overflow:auto}.left{border-right:1px solid var(--line)}.right{border-left:1px solid var(--line)}#viewer{overflow:auto;background:#d8e0e5;display:flex;align-items:flex-start;justify-content:center;padding:12px;position:relative}.pagewrap{position:relative;display:inline-block}.pagewrap img{display:block;max-width:100%;height:auto;background:#fff;box-shadow:0 2px 12px #0003}.pagewrap img[hidden]{display:none}.viewer-placeholder{align-self:center;max-width:360px;padding:18px;text-align:center;color:#5f6d77;background:#edf2f5;border:1px dashed #aebbc4;border-radius:9px}.box{position:absolute;border:3px solid #0877ba;background:#0877ba20;pointer-events:none}.card{width:100%;display:block;text-align:left;border:1px solid var(--line);background:#fff;border-radius:7px;padding:8px;margin:0 0 6px}.card.active{outline:2px solid var(--accent)}.card b{display:block}.pill{display:inline-block;background:#e7edf1;border-radius:999px;padding:3px 7px;margin:2px;font-size:11px}.gate{padding:8px;border-radius:7px;font-size:12px;margin:7px 0}.ready{background:#e9f6ef;border:1px solid #97c8ac}.blocked{background:#fff3d8;border:1px solid #dfc175}label{display:block;font-size:12px;margin:7px 0}label input,textarea{width:100%}textarea{min-height:65px}.buttons{display:grid;gap:6px;margin-top:8px}.buttons button:disabled,.intake button:disabled{opacity:.45}.section{border-top:1px solid var(--line);margin-top:10px;padding-top:10px}#message{white-space:pre-wrap;background:#f3f5f7;padding:8px;border-radius:7px;min-height:42px}@media(max-width:900px){.layout{display:flex;flex-direction:column;height:auto}.left{order:1;border:0}#viewer{order:2;min-height:44vh}.right{order:3;border:0}aside{overflow:visible}.viewer-placeholder{margin:auto}}
</style></head><body><header><h1>Document Discovery Workspace</h1><small>Prima il documento: primitive → cluster → esempi umani → simili. Nessun oggetto è noto in partenza.</small></header><div id="provider" class="provider meta">Provider: caricamento stato…</div><div class="intake"><input id="project" type="text" placeholder="ID progetto"><select id="source"><option value="">Fonte governata…</option></select><button id="analyze" class="primary">Analizza fonte</button><input id="file" type="file" accept="application/pdf"><button id="preview" class="secondary">Preview PDF</button><div id="intake-message" class="intake-status meta">Seleziona un PDF. Il limite preview verrà verificato prima dell'upload.</div></div><div class="layout"><aside class="left"><div id="status" class="meta">Seleziona una fonte o un PDF.</div><div id="clusters" class="section"></div></aside><section id="viewer"><div id="viewer-placeholder" class="viewer-placeholder">Seleziona una fonte governata oppure un PDF per avviare la scoperta grafica. Nessuna pagina è ancora caricata.</div><div class="pagewrap"><img id="page" alt="Pagina documento" hidden><div id="box" class="box" hidden></div></div></section><aside class="right"><h3 id="title">Nessun cluster selezionato</h3><div id="detail" class="meta"></div><div id="gate" class="gate blocked">Training bloccato finché SourceVersion e Page non sono governate.</div><label>Concetto / ID<input id="concept" type="text" placeholder="es. ELEMENTO-TIPO-A"></label><label>Significato insegnato<input id="meaning" type="text" placeholder="Es. elemento verticale rettangolare"></label><label>Revisore<input id="reviewer" type="text"></label><label>Rationale<textarea id="rationale"></textarea></label><div class="buttons"><button id="pos" class="positive" disabled>Insegna: questo è un…</button><button id="neg" class="negative" disabled>Non è questo</button><button id="amb" class="uncertain" disabled>Incerto</button><button id="similar" class="primary" disabled>Trova simili</button></div><div id="concepts" class="section meta"></div><div id="results" class="section"></div><div id="message" class="section meta"></div></aside></div><script>
let state=null,session=null,clusterId=null,candidateId=null,maxPreviewBytes=12*1024*1024,busy=false;const q=id=>document.getElementById(id);const h=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const mb=n=>(Number(n||0)/1048576).toFixed(1)+' MB';async function responseJson(r){const text=await r.text();let b={};try{b=text?JSON.parse(text):{}}catch(_){b={reason:`Risposta runtime non JSON · HTTP ${r.status}`}}if(!r.ok)throw Error(b.reason||b.state||`Errore CEW · HTTP ${r.status}`);return b}async function api(url,opt){return responseJson(await fetch(url,opt))}function cluster(){return state?.clusters.find(x=>x.cluster_id===clusterId)}
function intakeMessage(text,kind=''){const el=q('intake-message');el.textContent=text;el.className='intake-status meta'+(kind?' '+kind:'')}
function setBusy(value,text=''){busy=!!value;q('preview').disabled=busy;q('analyze').disabled=busy;if(text)intakeMessage(text,busy?'busy':'')}
function resetViewer(){candidateId=null;q('box').hidden=true;q('page').hidden=true;q('page').removeAttribute('src');q('viewer-placeholder').hidden=false}
function box(c){if(!c)return;candidateId=c.candidate_id;const b=c.bbox,p=q('box'),img=q('page');p.hidden=false;p.style.left=b.x*100+'%';p.style.top=b.y*100+'%';p.style.width=b.w*100+'%';p.style.height=b.h*100+'%';q('viewer-placeholder').hidden=true;img.hidden=false;img.src=`/api/workbench/document-discovery/session/${encodeURIComponent(session)}/page/${c.page_index}.jpg`}
function buttons(){const enabled=!!state?.teaching_enabled&&!!candidateId;q('pos').disabled=!enabled;q('neg').disabled=!enabled;q('amb').disabled=!enabled;const cid=q('concept').value.trim(),m=q('meaning').value.trim(),mem=state?.concepts.find(x=>x.concept_id===cid&&x.meaning===m);q('similar').disabled=!(mem?.search_ready)}
function clusters(){q('clusters').innerHTML='';for(const c of state.clusters){const b=document.createElement('button');b.className='card'+(c.cluster_id===clusterId?' active':'');b.innerHTML=`<b>${h(c.feature_signature.primitive_family)} · ${c.occurrence_count}</b><span class="meta">${h(c.feature_signature.aspect_bucket)} · ${h(c.feature_signature.area_bucket)}<br>${h(c.cluster_id)}</span>`;b.onclick=()=>{clusterId=c.cluster_id;clusters();selected()};q('clusters').appendChild(b)}}
function selected(){const c=cluster();if(!c)return;q('title').textContent=`Famiglia grafica · ${c.occurrence_count} occorrenze`;q('detail').innerHTML=`<span class="pill">${h(c.feature_signature.primitive_family)}</span><span class="pill">${h(c.feature_signature.aspect_bucket)}</span><span class="pill">${h(c.feature_signature.area_bucket)}</span><br>Significato automatico: <b>nessuno</b>`;box(c.representative);buttons()}
function concepts(){const rows=state.concepts||[];q('concepts').innerHTML='<b>Memoria del progetto</b><br>'+(rows.length?rows.map(x=>`<button class="card memory" data-id="${h(x.concept_id)}" data-m="${h(x.meaning)}"><b>${h(x.meaning)}</b><span class="meta">${h(x.concept_id)} · +${x.example_counts.POSITIVE} / −${x.example_counts.NEGATIVE} / ?${x.example_counts.AMBIGUOUS}</span></button>`).join(''):'Nessun concetto insegnato.');for(const b of document.querySelectorAll('.memory'))b.onclick=()=>{q('concept').value=b.dataset.id;q('meaning').value=b.dataset.m;buttons()}}
function render(){q('status').innerHTML=`<b>${h(state.source_registration_state)}</b><br>${state.page_count} pagine · ${state.primitive_candidate_count} primitive · ${state.graphic_cluster_count} cluster<br>Structured: ${h(state.provider_states.structured_graphic.state)} · DINOv3: ${h(state.provider_states.visual_foundation.state)}<br>Etichette automatiche: no`;q('provider').innerHTML=`Structured: <b>${h(state.provider_states.structured_graphic.state)}</b> · DINOv3: <b>${h(state.provider_states.visual_foundation.state)}</b> · nessuna classificazione automatica`;q('gate').className='gate '+(state.teaching_enabled?'ready':'blocked');q('gate').textContent=state.teaching_enabled?'SourceVersion + Page READY: training project-local consentito.':'Preview analizzabile, ma training bloccato fino alla registrazione SourceVersion/Page.';clusters();concepts();if(!clusterId&&state.clusters.length){clusterId=state.clusters[0].cluster_id;clusters();selected()}else if(!state.clusters.length){resetViewer()}buttons()}
async function load(){state=await api(`/api/workbench/document-discovery/session/${encodeURIComponent(session)}`);render()}
async function boot(){const b=await api('/api/workbench/document-discovery/status');maxPreviewBytes=Number(b.max_preview_pdf_bytes||maxPreviewBytes);q('provider').innerHTML=`Structured: <b>${h(b.provider_states.structured_graphic.state)}</b> · DINOv3: <b>${h(b.provider_states.visual_foundation.state)}</b> · nessuna classificazione automatica`;for(const s of b.governed_sources){const o=document.createElement('option');o.value=s.source_id;o.textContent=`${s.source_id} · ${s.ready_page_count} Page READY`;q('source').appendChild(o)}intakeMessage(`Preview PDF: massimo ${mb(maxPreviewBytes)}. Il training resta bloccato per file non governati.`)}
q('file').onchange=()=>{const f=q('file').files[0];if(!f){intakeMessage(`Preview PDF: massimo ${mb(maxPreviewBytes)}.`);return}if(f.size>maxPreviewBytes){intakeMessage(`${f.name} · ${mb(f.size)} supera il limite preview di ${mb(maxPreviewBytes)}.`, 'error');return}intakeMessage(`${f.name} · ${mb(f.size)} · pronto per la preview.`,'ok')}
q('analyze').onclick=async()=>{if(busy)return;try{const project=q('project').value.trim(),source=q('source').value;if(!project||!source)throw Error('Indica progetto e fonte.');setBusy(true,'Fonte governata: acquisizione e analisi in corso…');resetViewer();const b=await api('/api/workbench/document-discovery/analyze-governed',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:project,source_id:source})});session=b.session_id;clusterId=null;await load();intakeMessage(`Analisi completata · ${state.page_count} pagine · ${state.primitive_candidate_count} primitive · ${state.graphic_cluster_count} cluster.`,'ok')}catch(e){intakeMessage(e.message,'error');q('message').textContent=e.message}finally{setBusy(false)}}
q('preview').onclick=async()=>{if(busy)return;try{const project=q('project').value.trim(),f=q('file').files[0];if(!project||!f)throw Error('Indica progetto e PDF.');if(f.size>maxPreviewBytes)throw Error(`${f.name} · ${mb(f.size)} supera il limite preview di ${mb(maxPreviewBytes)}.`);setBusy(true,`Upload ${f.name} · ${mb(f.size)}. Analisi grafica in corso…`);resetViewer();const r=await fetch(`/api/workbench/document-discovery/analyze-preview?project_id=${encodeURIComponent(project)}`,{method:'POST',headers:{'Content-Type':'application/pdf'},body:f});const b=await responseJson(r);session=b.session_id;clusterId=null;await load();intakeMessage(`Preview completata · ${state.page_count} pagine · ${state.primitive_candidate_count} primitive · ${state.graphic_cluster_count} cluster. Training bloccato.`,'ok')}catch(e){intakeMessage(e.message,'error');q('message').textContent=e.message}finally{setBusy(false)}}
async function learn(role){try{const p={candidate_id:candidateId,role,concept_id:q('concept').value.trim(),meaning:q('meaning').value.trim(),reviewer:q('reviewer').value.trim(),rationale:q('rationale').value.trim()};const b=await api(`/api/workbench/document-discovery/session/${encodeURIComponent(session)}/learn`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});q('message').textContent=`${b.role} registrato · +${b.example_counts.POSITIVE} / −${b.example_counts.NEGATIVE} / ?${b.example_counts.AMBIGUOUS}`;await load()}catch(e){q('message').textContent=e.message}}q('pos').onclick=()=>learn('POSITIVE');q('neg').onclick=()=>learn('NEGATIVE');q('amb').onclick=()=>learn('AMBIGUOUS');q('concept').oninput=buttons;q('meaning').oninput=buttons;
q('similar').onclick=async()=>{try{const b=await api(`/api/workbench/document-discovery/session/${encodeURIComponent(session)}/similar`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({concept_id:q('concept').value.trim(),meaning:q('meaning').value.trim(),limit:40})});q('results').innerHTML='<b>Proposte simili</b><br>'+b.candidates.map(x=>`<button class="card result" data-id="${h(x.candidate_id)}"><b>${h(x.primitive_family)} · ${(x.fused_score*100).toFixed(1)}%</b><span class="meta">${h(x.candidate_id)}${x.is_training_example?' · training':''}</span></button>`).join('');for(const btn of document.querySelectorAll('.result'))btn.onclick=()=>{const x=b.candidates.find(v=>v.candidate_id===btn.dataset.id);if(x)box(x)};q('message').textContent=`${b.candidate_count} proposte · ${b.search_channel_state}. Nessuna classificazione automatica.`}catch(e){q('message').textContent=e.message}};boot().catch(e=>{intakeMessage(e.message,'error');q('message').textContent=e.message});
</script></body></html>'''


def build_router(source_workspace) -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def page():
        return HTMLResponse(_page(), headers={"Cache-Control":"no-store","X-CEW-Canonical-Write":"false","X-CEW-Engineering-Authority-Effect":"NONE"})

    @router.get("/api/workbench/document-discovery/status")
    def status():
        try:
            return _json({
                "state":"DOCUMENT_DISCOVERY_AVAILABLE",
                "governed_sources":discovery.governed_sources(source_workspace),
                "preview_allowed":True,
                "preview_teaching_allowed":False,
                "max_preview_pdf_bytes":discovery.MAX_PDF_BYTES,
                "max_preview_pages":discovery.MAX_PAGES,
                "provider_states":discovery.provider_states(),
            })
        except Exception:
            LOGGER.exception("DOCUMENT_DISCOVERY_STATUS_BLOCKED")
            return _json({"state":"DOCUMENT_DISCOVERY_STATUS_BLOCKED","reason":"DOCUMENT_DISCOVERY_INTERNAL_ERROR"},409)

    @router.post("/api/workbench/document-discovery/analyze-governed")
    async def analyze_governed(request: Request):
        try:
            body=await request.json()
            session=await run_in_threadpool(discovery.create_governed,source_workspace,body.get("source_id"),body.get("project_id"))
            return _json(discovery.status(session["session_id"]))
        except (KeyError,ValueError) as exc:
            return _json({"state":"DOCUMENT_DISCOVERY_GOVERNED_ANALYSIS_REJECTED","reason":str(exc)},409)
        except Exception:
            LOGGER.exception("DOCUMENT_DISCOVERY_GOVERNED_ANALYSIS_BLOCKED")
            return _json({"state":"DOCUMENT_DISCOVERY_GOVERNED_ANALYSIS_BLOCKED","reason":"DOCUMENT_DISCOVERY_INTERNAL_ERROR"},503)

    @router.post("/api/workbench/document-discovery/analyze-preview")
    async def analyze_preview(request: Request, project_id: str=""):
        try:
            if str(request.headers.get("content-type") or "").split(";",1)[0].lower()!="application/pdf":
                raise ValueError("DOCUMENT_DISCOVERY_APPLICATION_PDF_REQUIRED")
            content_length=str(request.headers.get("content-length") or "").strip()
            if content_length and int(content_length)>discovery.MAX_PDF_BYTES:
                return _json({"state":"DOCUMENT_DISCOVERY_PREVIEW_TOO_LARGE","reason":f"PDF exceeds preview limit of {discovery.MAX_PDF_BYTES} bytes"},413)
            payload=await request.body()
            session=await run_in_threadpool(discovery.create_preview,payload,project_id)
            return _json(discovery.status(session["session_id"]))
        except ValueError as exc:
            return _json({"state":"DOCUMENT_DISCOVERY_PREVIEW_REJECTED","reason":str(exc)},400)
        except Exception:
            LOGGER.exception("DOCUMENT_DISCOVERY_PREVIEW_BLOCKED")
            return _json({"state":"DOCUMENT_DISCOVERY_PREVIEW_BLOCKED","reason":"DOCUMENT_DISCOVERY_INTERNAL_ERROR"},503)

    @router.get("/api/workbench/document-discovery/session/{session_id}")
    def session_status(session_id: str):
        try:
            return _json(discovery.status(session_id))
        except ValueError as exc:
            return _json({"state":"DOCUMENT_DISCOVERY_SESSION_REJECTED","reason":str(exc)},404)

    @router.get("/api/workbench/document-discovery/session/{session_id}/page/{page_index}.jpg")
    def page_image(session_id: str,page_index: int):
        try:
            return Response(discovery.render_page(session_id,page_index),media_type="image/jpeg",headers={"Cache-Control":"no-store","X-CEW-Authority":"READING_AID_ONLY"})
        except ValueError as exc:
            return _json({"state":"DOCUMENT_DISCOVERY_PAGE_REJECTED","reason":str(exc)},404)

    @router.post("/api/workbench/document-discovery/session/{session_id}/learn")
    async def learn(session_id: str,request: Request):
        try:
            return _json(discovery.teach(session_id,await request.json()))
        except ValueError as exc:
            return _json({"state":"DOCUMENT_DISCOVERY_LEARNING_REJECTED","reason":str(exc)},409)
        except Exception:
            LOGGER.exception("DOCUMENT_DISCOVERY_LEARNING_BLOCKED")
            return _json({"state":"DOCUMENT_DISCOVERY_LEARNING_BLOCKED","reason":"DOCUMENT_DISCOVERY_INTERNAL_ERROR"},503)

    @router.post("/api/workbench/document-discovery/session/{session_id}/similar")
    async def similar(session_id: str,request: Request):
        try:
            body=await request.json()
            return _json(discovery.find_similar(session_id,body.get("concept_id"),body.get("meaning"),int(body.get("limit",40))))
        except ValueError as exc:
            return _json({"state":"DOCUMENT_DISCOVERY_SIMILARITY_REJECTED","reason":str(exc)},409)

    return router
