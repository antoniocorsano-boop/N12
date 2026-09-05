#!/usr/bin/env python3
"""Human-first acquisition Workbench for CEW.

Primary interaction:
source -> teach one example -> find similar -> review grouped candidates.
R2HR/R2GI/R2GM remain separate governed engineering/document-geometry layers and
are not bypassed or silently satisfied by this Workbench.
"""
from __future__ import annotations

import html
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

import cew_acquisition_group_review as group_review
import cew_document_discovery as discovery


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    body = dict(payload)
    body.setdefault("authority", dict(group_review.AUTHORITY))
    return JSONResponse(body, status_code=status_code, headers={"Cache-Control": "no-store"})


def _page() -> str:
    return r'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Acquisizione assistita</title><style>
:root{--bg:#edf1f4;--panel:#fff;--ink:#17222b;--muted:#67747d;--line:#ccd5dc;--accent:#17415f;--ok:#1f6d4b;--bad:#9e3434;--warn:#906100}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,sans-serif}header{background:#fff;border-bottom:1px solid var(--line);padding:12px 15px}h1{font-size:20px;margin:0 0 3px}.sub,.meta{color:var(--muted);font-size:12px}.toolbar{display:flex;gap:7px;flex-wrap:wrap;padding:10px;background:#fff;border-bottom:1px solid var(--line)}input,select,textarea,button{font:inherit}input,select,textarea{border:1px solid var(--line);border-radius:7px;padding:8px;background:#fff}button{border:0;border-radius:7px;padding:9px 11px;font-weight:700;cursor:pointer}.primary{background:var(--accent);color:#fff}.secondary{background:#e3e9ed}.positive{background:var(--ok);color:#fff}.negative{background:var(--bad);color:#fff}.uncertain{background:var(--warn);color:#fff}.layout{display:grid;grid-template-columns:285px minmax(0,1fr) 390px;height:calc(100vh - 126px)}aside{background:#fff;padding:10px;overflow:auto}.left{border-right:1px solid var(--line)}.right{border-left:1px solid var(--line)}#viewer{overflow:auto;background:#d8e0e5;display:flex;align-items:flex-start;justify-content:center;padding:12px}.pagewrap{position:relative;display:inline-block}.pagewrap img{display:block;max-width:100%;height:auto;background:#fff;box-shadow:0 2px 12px #0003}.box{position:absolute;border:3px solid #0877ba;background:#0877ba20;pointer-events:none}.card{width:100%;display:block;text-align:left;border:1px solid var(--line);background:#fff;border-radius:8px;padding:8px;margin:0 0 6px}.card.active{outline:2px solid var(--accent)}.candidate{display:grid;grid-template-columns:auto 1fr auto;gap:7px;align-items:start}.candidate.reviewed{opacity:.55}.pill{display:inline-block;border-radius:999px;padding:3px 7px;font-size:11px;background:#e7edf1}.likely{background:#e6f5ec;color:#1e6547}.review{background:#fff2d6;color:#7f5a00}.outlier{background:#f1e8e8;color:#8c3333}.section{border-top:1px solid var(--line);margin-top:10px;padding-top:10px}.gate{padding:8px;border-radius:7px;background:#fff3d8;border:1px solid #dfc175;margin:7px 0;font-size:12px}.gate.ready{background:#e9f6ef;border-color:#97c8ac}.grid{display:grid;gap:6px}.grid label{font-size:12px}.grid input,.grid textarea{width:100%}textarea{min-height:55px}.actions{display:grid;grid-template-columns:1fr 1fr;gap:6px}.actions .wide{grid-column:1/-1}.status{white-space:pre-wrap;background:#f3f5f7;border-radius:7px;padding:8px;min-height:40px}.summary{display:flex;gap:6px;flex-wrap:wrap;margin:7px 0}.mutedbtn{background:#f1f3f5;color:#53616b}@media(max-width:900px){.layout{display:flex;flex-direction:column;height:auto}.left{order:1;border:0}#viewer{order:2;min-height:44vh}.right{order:3;border:0}aside{overflow:visible}}
</style></head><body><header><h1>Acquisizione assistita</h1><div class="sub">Documento → un esempio umano → trova simili → revisione del gruppo. Le eccezioni restano visibili; nessuna identità strutturale viene creata automaticamente.</div></header><div class="toolbar"><input id="project" value="N12" placeholder="Progetto"><select id="source"><option value="">Fonte governata…</option></select><button id="open" class="primary">Apri fonte</button><button id="reset" class="secondary">Azzera vista</button></div><div class="layout"><aside class="left"><b>Famiglie grafiche</b><div id="sourceStatus" class="meta">Seleziona una fonte governata.</div><div id="clusters" class="section"></div></aside><main id="viewer"><div class="pagewrap"><img id="page" alt="Pagina documento" hidden><div id="box" class="box" hidden></div></div></main><aside class="right"><div id="gate" class="gate">Training disponibile solo su SourceVersion e Page governate.</div><div class="grid"><label>Tipo / concetto<input id="concept" placeholder="es. COLUMN"></label><label>Significato<input id="meaning" placeholder="es. pilastro rettangolare"></label><label>Revisore<input id="reviewer" placeholder="nome o sigla"></label><label>Motivazione<textarea id="rationale" placeholder="Criterio osservato nella fonte"></textarea></label></div><div class="actions"><button id="teach" class="positive wide" disabled>Questo è un…</button><button id="similar" class="primary wide" disabled>Trova simili</button></div><div id="memory" class="section meta"></div><div id="group" class="section" hidden><b>Revisione del gruppo</b><div id="summary" class="summary"></div><div class="actions"><button id="selectLikely" class="mutedbtn">Seleziona probabili</button><button id="clearSel" class="mutedbtn">Deseleziona</button><button id="confirm" class="positive">Conferma selezionati</button><button id="reject" class="negative">Rifiuta selezionati</button><button id="ambiguous" class="uncertain wide">Segna come ambigui</button></div><div id="results" class="section"></div></div><div id="message" class="status section meta"></div></aside></div><script>
let session=null,state=null,clusterId=null,candidateId=null,proposal=null;const q=id=>document.getElementById(id);const h=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));async function api(url,opt){const r=await fetch(url,opt);const text=await r.text();let b={};try{b=text?JSON.parse(text):{}}catch(_){b={reason:`HTTP ${r.status}`}}if(!r.ok)throw Error(b.reason||b.state||`HTTP ${r.status}`);return b}function currentCluster(){return state?.clusters.find(x=>x.cluster_id===clusterId)}function showBox(c){if(!c||!session)return;candidateId=c.candidate_id;const b=c.bbox,p=q('box'),img=q('page');p.hidden=false;p.style.left=b.x*100+'%';p.style.top=b.y*100+'%';p.style.width=b.w*100+'%';p.style.height=b.h*100+'%';img.hidden=false;img.src=`/api/workbench/acquisition/session/${encodeURIComponent(session)}/page/${c.page_index}.jpg`;buttons()}function buttons(){q('teach').disabled=!(state?.teaching_enabled&&candidateId&&q('concept').value.trim()&&q('meaning').value.trim()&&q('reviewer').value.trim()&&q('rationale').value.trim());const mem=(state?.concepts||[]).find(x=>x.concept_id===q('concept').value.trim()&&x.meaning===q('meaning').value.trim());q('similar').disabled=!(mem?.search_ready)}function renderClusters(){q('clusters').innerHTML='';for(const c of state?.clusters||[]){const b=document.createElement('button');b.className='card'+(c.cluster_id===clusterId?' active':'');b.innerHTML=`<b>${h(c.feature_signature.primitive_family)} · ${c.occurrence_count}</b><span class="meta">${h(c.feature_signature.aspect_bucket)} · ${h(c.feature_signature.area_bucket)}</span>`;b.onclick=()=>{clusterId=c.cluster_id;renderClusters();showBox(c.representative)};q('clusters').appendChild(b)}}function renderMemory(){const rows=state?.concepts||[];q('memory').innerHTML='<b>Memoria del progetto</b><br>'+(rows.length?rows.map(x=>`<button class="card memory" data-id="${h(x.concept_id)}" data-m="${h(x.meaning)}"><b>${h(x.meaning)}</b><span class="meta">${h(x.concept_id)} · +${x.example_counts.POSITIVE} / −${x.example_counts.NEGATIVE} / ?${x.example_counts.AMBIGUOUS}</span></button>`).join(''):'Nessun prototipo ancora insegnato.');for(const el of document.querySelectorAll('.memory'))el.onclick=()=>{q('concept').value=el.dataset.id;q('meaning').value=el.dataset.m;buttons()}}function renderState(){q('sourceStatus').innerHTML=`<br><b>${h(state.source_id)}</b><br>${state.page_count} pagine · ${state.primitive_candidate_count} primitive · ${state.graphic_cluster_count} cluster`;q('gate').className='gate '+(state.teaching_enabled?'ready':'');q('gate').textContent=state.teaching_enabled?'Fonte governata: puoi insegnare e revisionare gruppi.':'Fonte non governata: revisione bloccata.';renderClusters();renderMemory();if(!clusterId&&state.clusters?.length){clusterId=state.clusters[0].cluster_id;renderClusters();showBox(state.clusters[0].representative)}buttons()}async function load(){state=await api(`/api/workbench/acquisition/session/${encodeURIComponent(session)}`);renderState()}function bucketLabel(v){return v==='LIKELY_MATCH'?'probabile':v==='REVIEW'?'da verificare':'anomalo'}function renderProposal(){q('group').hidden=false;q('summary').innerHTML=`<span class="pill likely">${proposal.bucket_counts.LIKELY_MATCH} probabili</span><span class="pill review">${proposal.bucket_counts.REVIEW} da verificare</span><span class="pill outlier">${proposal.bucket_counts.OUTLIER} anomali</span>`;q('results').innerHTML='';for(const c of proposal.candidates){const label=document.createElement('label');label.className='card candidate'+(c.already_reviewed?' reviewed':'');const cls=c.triage_bucket==='LIKELY_MATCH'?'likely':c.triage_bucket==='REVIEW'?'review':'outlier';label.innerHTML=`<input type="checkbox" class="pick" value="${h(c.candidate_id)}" ${c.recommended_selection?'checked':''} ${c.already_reviewed?'disabled':''}><span><b>${h(c.candidate_id)}</b><span class="meta">pag. ${c.page_index+1} · ${h(c.primitive_family)}${c.already_reviewed?' · già revisionato':''}</span></span><span class="pill ${cls}">${bucketLabel(c.triage_bucket)} · ${Number(c.fused_score).toFixed(3)}</span>`;label.onclick=e=>{if(e.target.tagName!=='INPUT')showBox(c)};q('results').appendChild(label)}}function selected(){return [...document.querySelectorAll('.pick:checked')].map(x=>x.value)}async function groupAction(action){try{const ids=selected();if(!ids.length)throw Error('Seleziona almeno un candidato.');const body={concept_id:q('concept').value.trim(),meaning:q('meaning').value.trim(),reviewer:q('reviewer').value.trim(),rationale:q('rationale').value.trim(),action,candidate_ids:ids,proposal_fingerprint:proposal.proposal_fingerprint};const b=await api(`/api/workbench/acquisition/session/${encodeURIComponent(session)}/group-review`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});q('message').textContent=`${b.state}\n${b.candidate_count} candidati registrati con un'unica decisione di gruppo.\nProssimo confine: ${b.next_gate}`;await load();await findSimilar()}catch(e){q('message').textContent=e.message}}async function findSimilar(){try{const body={concept_id:q('concept').value.trim(),meaning:q('meaning').value.trim(),limit:100};proposal=await api(`/api/workbench/acquisition/session/${encodeURIComponent(session)}/similar`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});renderProposal();q('message').textContent='I raggruppamenti sono triage, non classificazione automatica. Controlla soprattutto eccezioni e casi dubbi.'}catch(e){q('message').textContent=e.message}}q('open').onclick=async()=>{try{const project=q('project').value.trim(),source=q('source').value;if(!project||!source)throw Error('Indica progetto e fonte governata.');const b=await api('/api/workbench/acquisition/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:project,source_id:source})});session=b.session_id;state=null;clusterId=null;candidateId=null;proposal=null;q('group').hidden=true;await load();q('message').textContent='Fonte pronta. Seleziona un esempio rappresentativo e insegna il concetto.'}catch(e){q('message').textContent=e.message}};q('teach').onclick=async()=>{try{const body={candidate_id:candidateId,role:'POSITIVE',concept_id:q('concept').value.trim(),meaning:q('meaning').value.trim(),reviewer:q('reviewer').value.trim(),rationale:q('rationale').value.trim()};const b=await api(`/api/workbench/acquisition/session/${encodeURIComponent(session)}/learn`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});q('message').textContent=`Prototipo registrato · +${b.example_counts.POSITIVE}. Ora usa Trova simili.`;await load()}catch(e){q('message').textContent=e.message}};q('similar').onclick=findSimilar;q('selectLikely').onclick=()=>{for(const x of document.querySelectorAll('.pick'))x.checked=!x.disabled&&proposal.candidates.find(c=>c.candidate_id===x.value)?.triage_bucket==='LIKELY_MATCH'};q('clearSel').onclick=()=>{for(const x of document.querySelectorAll('.pick'))x.checked=false};q('confirm').onclick=()=>groupAction('CONFIRM_GROUP');q('reject').onclick=()=>groupAction('REJECT_GROUP');q('ambiguous').onclick=()=>groupAction('MARK_AMBIGUOUS');q('reset').onclick=()=>location.reload();for(const id of ['concept','meaning','reviewer','rationale'])q(id).oninput=buttons;(async()=>{try{const b=await api('/api/workbench/acquisition/status');for(const s of b.governed_sources){const o=document.createElement('option');o.value=s.source_id;o.textContent=`${s.source_id} · ${s.ready_page_count} pagine READY`;q('source').appendChild(o)}q('message').textContent='Seleziona una fonte governata. Questo Workbench riduce la manualità ma non promuove automaticamente oggetti canonici.'}catch(e){q('message').textContent=e.message}})();</script></body></html>'''


def build_router(source_workspace) -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/acquisition", response_class=HTMLResponse)
    def acquisition_workbench():
        return HTMLResponse(
            _page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Structural-Identity": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
            },
        )

    @router.get("/api/workbench/acquisition/status")
    def acquisition_status():
        return _json(
            {
                "state": "OA1_ACQUISITION_HUMAN_WORKBENCH_READY",
                "governed_sources": discovery.governed_sources(source_workspace),
                "primary_interaction": [
                    "TEACH_ONE_EXAMPLE",
                    "FIND_SIMILAR",
                    "REVIEW_GROUP",
                    "FOCUS_EXCEPTIONS",
                ],
                "r2hr_r2gi_r2gm_bypassed": False,
                "canonical_write_authorized": False,
                "structural_identity_authorized": False,
            }
        )

    @router.post("/api/workbench/acquisition/start")
    async def acquisition_start(request: Request):
        try:
            body = await request.json()
            session = discovery.create_governed(
                source_workspace,
                str(body.get("source_id") or ""),
                str(body.get("project_id") or ""),
            )
            return _json(
                {
                    "state": "OA1_GOVERNED_SOURCE_SESSION_READY",
                    "session_id": session["session_id"],
                    "source_id": session["source_id"],
                    "source_version_id": session["source_version_id"],
                    "teaching_enabled": session["teaching_enabled"],
                }
            )
        except (ValueError, KeyError) as exc:
            return _json({"state": "OA1_SOURCE_SESSION_REJECTED", "reason": str(exc)}, 422)

    @router.get("/api/workbench/acquisition/session/{session_id}")
    def acquisition_session(session_id: str):
        try:
            return _json(discovery.status(session_id))
        except ValueError as exc:
            return _json({"state": "OA1_SESSION_NOT_AVAILABLE", "reason": str(exc)}, 404)

    @router.get("/api/workbench/acquisition/session/{session_id}/page/{page_index}.jpg")
    def acquisition_page(session_id: str, page_index: int):
        try:
            payload = discovery.render_page(session_id, page_index)
            return Response(payload, media_type="image/jpeg", headers={"Cache-Control": "no-store"})
        except ValueError as exc:
            return _json({"state": "OA1_PAGE_NOT_AVAILABLE", "reason": str(exc)}, 404)

    @router.post("/api/workbench/acquisition/session/{session_id}/learn")
    async def acquisition_learn(session_id: str, request: Request):
        try:
            return _json(discovery.teach(session_id, await request.json()))
        except ValueError as exc:
            return _json({"state": "OA1_LEARNING_REJECTED", "reason": str(exc)}, 409)

    @router.post("/api/workbench/acquisition/session/{session_id}/similar")
    async def acquisition_similar(session_id: str, request: Request):
        try:
            body = await request.json()
            return _json(
                group_review.proposal(
                    session_id,
                    str(body.get("concept_id") or ""),
                    str(body.get("meaning") or ""),
                    int(body.get("limit", 80)),
                )
            )
        except (ValueError, TypeError) as exc:
            return _json({"state": "OA1_SIMILARITY_REJECTED", "reason": str(exc)}, 409)

    @router.post("/api/workbench/acquisition/session/{session_id}/group-review")
    async def acquisition_group_review(session_id: str, request: Request):
        try:
            return _json(group_review.record_group_review(session_id, await request.json()))
        except ValueError as exc:
            return _json({"state": "OA1_GROUP_REVIEW_REJECTED", "reason": str(exc)}, 409)

    return router
