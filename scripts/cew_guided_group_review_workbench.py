#!/usr/bin/env python3
"""Human-centred CEW surface for guided batch similarity review.

This additive layer shadows only the Document Discovery HTML route so that the
existing `Trova simili` gesture enters group review. Existing discovery APIs,
async bounded preview, source provenance, and authority boundaries are preserved.
"""
from __future__ import annotations

import html
import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

import cew_document_discovery as discovery
import cew_document_discovery_async_preview as async_preview
import cew_guided_group_review as group
import cew_visual_learning as learning


_MEMORY_PATCH_MARKER = "_cew_guided_group_review_memory_v1_installed"


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    body = dict(payload)
    body.setdefault("authority", dict(discovery.AUTHORITY))
    return JSONResponse(body, status_code=status_code, headers={"Cache-Control": "no-store"})


def install() -> None:
    """Replay group receipts into project-local memory without mutating discovery core."""
    if getattr(discovery, _MEMORY_PATCH_MARKER, False):
        return
    original_memory = discovery.memory

    def integrated_memory(project_id: str, concept_id: str, meaning: str) -> dict[str, Any]:
        memory = original_memory(project_id, concept_id, meaning)
        applied = set(memory.get("applied_receipt_ids") or [])
        children = sorted(
            group.learning_receipts_for_memory(project_id, concept_id, meaning),
            key=lambda row: (str(row.get("timestamp") or ""), str(row.get("decision_id") or "")),
        )
        for child in children:
            decision_id = str(child.get("decision_id") or "")
            if not decision_id:
                raise ValueError("GUIDED_GROUP_REVIEW_CHILD_DECISION_ID_REQUIRED")
            if decision_id in applied:
                raise ValueError("GUIDED_GROUP_REVIEW_MEMORY_RECEIPT_CONFLICT")
            memory = learning.apply_learning_receipt(memory, child)
            applied.add(decision_id)
        return memory

    discovery.memory = integrated_memory
    setattr(discovery, _MEMORY_PATCH_MARKER, True)


def _review_group(session_id: str, concept_id: str, meaning: str, limit: int = 80) -> dict[str, Any]:
    session = discovery.get_session(session_id)
    concept_id = discovery._text(concept_id, "concept_id")
    meaning = discovery._text(meaning, "meaning")
    current = discovery.memory(session["project_id"], concept_id, meaning)
    if current["example_counts"]["POSITIVE"] < 1:
        raise ValueError("DOCUMENT_DISCOVERY_POSITIVE_PROTOTYPE_REQUIRED")

    ranked = discovery.find_similar(session_id, concept_id, meaning, limit=max(1, min(100, int(limit))))
    candidates = discovery.candidate_map(session)
    members = []
    for row in ranked["candidates"]:
        candidate = candidates.get(row["candidate_id"])
        if candidate is None:
            raise ValueError("DOCUMENT_DISCOVERY_GROUP_CANDIDATE_NOT_FOUND")
        page = session["page_registry"].get(int(candidate["page_index"]))
        if page is None or page.get("readiness_state") != "READY":
            raise ValueError("DOCUMENT_DISCOVERY_GROUP_READY_PAGE_REQUIRED")
        if candidate["source_version_id"] != page["source_version_id"]:
            raise ValueError("DOCUMENT_DISCOVERY_GROUP_SOURCE_VERSION_DRIFT")
        members.append({
            **row,
            "source_version_id": page["source_version_id"],
            "page_id": page["page_id"],
            "page_index": int(candidate["page_index"]),
            "bbox": candidate["bbox"],
            "primitive_family": candidate["primitive_family"],
            "evidence_fingerprint": discovery._evidence_fingerprint(session, candidate, page),
            "embedding": learning.structured_embedding_from_candidate(candidate),
        })

    return group.build_snapshot(
        project_id=session["project_id"],
        concept_id=concept_id,
        meaning=meaning,
        memory_fingerprint=current["memory_fingerprint"],
        candidates=members,
    )


def _review_group_decision(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    concept_id = discovery._text(payload.get("concept_id"), "concept_id")
    meaning = discovery._text(payload.get("meaning"), "meaning")
    limit = max(1, min(100, int(payload.get("limit", 80))))
    snapshot = _review_group(session_id, concept_id, meaning, limit)
    if discovery._text(payload.get("group_fingerprint"), "group_fingerprint") != snapshot["group_fingerprint"]:
        raise ValueError("DOCUMENT_DISCOVERY_GROUP_SNAPSHOT_STALE")
    selected = payload.get("selected_candidate_ids")
    if not isinstance(selected, list):
        raise ValueError("DOCUMENT_DISCOVERY_GROUP_SELECTION_REQUIRED")

    receipt = group.build_receipt(
        snapshot,
        action=payload.get("action"),
        selected_candidate_ids=selected,
        reviewer=payload.get("reviewer"),
        rationale=payload.get("rationale"),
    )
    persisted = group.persist_receipt(receipt)
    session = discovery.get_session(session_id)
    updated = discovery.memory(session["project_id"], concept_id, meaning)
    return {
        "state": "GUIDED_GROUP_REVIEW_RECEIPT_PERSISTED",
        "decision_id": receipt["decision_id"],
        "action": receipt["action"],
        "selected_count": receipt["selected_count"],
        "example_counts": updated["example_counts"],
        "memory_fingerprint": updated["memory_fingerprint"],
        "audit_backend": persisted["audit_backend"],
        "automatic_classification": False,
        "canonical_write_authorized": False,
        "structural_identity_authorized": False,
        "authority": dict(discovery.AUTHORITY),
    }


def _patched_document_discovery_page() -> str:
    """Preserve async preview while routing Find Similar into guided group review."""
    page = async_preview._patched_page()
    start = "q('similar').onclick=async()=>{"
    end = ";boot().catch"
    if page.count(start) != 1:
        raise RuntimeError("GUIDED_GROUP_REVIEW_FIND_SIMILAR_HANDLER_DRIFT")
    prefix, remainder = page.split(start, 1)
    if end not in remainder:
        raise RuntimeError("GUIDED_GROUP_REVIEW_BOOT_MARKER_MISSING")
    _, suffix = remainder.split(end, 1)
    replacement = r'''q('similar').onclick=()=>{try{const cid=q('concept').value.trim(),meaning=q('meaning').value.trim();if(!session||!cid||!meaning)throw Error('Seleziona un prototipo insegnato.');window.location.href=`/workbench/guided-group-review?session=${encodeURIComponent(session)}&concept=${encodeURIComponent(cid)}&meaning=${encodeURIComponent(meaning)}`}catch(e){q('message').textContent=e.message}}'''
    patched = prefix + replacement + end + suffix
    if "analyze-preview-async" not in patched:
        raise RuntimeError("GUIDED_GROUP_REVIEW_ASYNC_PREVIEW_REGRESSION")
    if "/workbench/guided-group-review?session=" not in patched:
        raise RuntimeError("GUIDED_GROUP_REVIEW_NAVIGATION_MISSING")
    return patched


def _page(session: str, concept: str, meaning: str) -> str:
    concept_h = html.escape(concept, quote=True)
    meaning_h = html.escape(meaning, quote=True)
    session_js = json.dumps(session, ensure_ascii=False)
    concept_js = json.dumps(concept, ensure_ascii=False)
    meaning_js = json.dumps(meaning, ensure_ascii=False)
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Revisione gruppo</title><style>
:root{{--bg:#edf1f4;--panel:#fff;--ink:#18222b;--muted:#67747e;--line:#ccd5dc;--accent:#17415f;--ok:#1d704b;--bad:#a13232;--warn:#916000}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,sans-serif}}header{{padding:12px 15px;background:#fff;border-bottom:1px solid var(--line)}}h1{{font-size:19px;margin:0}}small,.meta{{color:var(--muted);font-size:12px}}.layout{{display:grid;grid-template-columns:minmax(0,1fr) 390px;min-height:calc(100vh - 70px)}}main{{padding:12px;overflow:auto}}aside{{background:#fff;border-left:1px solid var(--line);padding:12px}}.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0 12px}}.metric{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px}}.metric b{{display:block;font-size:22px}}.card{{display:grid;grid-template-columns:auto 1fr auto;gap:9px;align-items:center;background:#fff;border:1px solid var(--line);border-radius:8px;padding:9px;margin:7px 0}}.card.training{{opacity:.55}}.score{{font-weight:700}}button{{border:0;border-radius:7px;padding:10px 11px;font-weight:700}}.primary{{background:var(--accent);color:white}}.positive{{background:var(--ok);color:white}}.negative{{background:var(--bad);color:white}}.uncertain{{background:var(--warn);color:white}}button:disabled{{opacity:.45}}label{{display:block;margin:8px 0;font-size:12px}}input,textarea{{width:100%;border:1px solid var(--line);border-radius:7px;padding:8px;font:inherit}}textarea{{min-height:82px}}#viewer{{position:relative;background:#d8e0e5;min-height:350px;display:flex;align-items:flex-start;justify-content:center;overflow:auto;padding:10px}}#page{{max-width:100%;height:auto;background:#fff}}#box{{position:absolute;border:3px solid #0877ba;background:#0877ba20;pointer-events:none}}.actions{{display:grid;gap:7px}}.note{{padding:8px;border:1px solid #dfc175;background:#fff3d8;border-radius:7px;font-size:12px}}@media(max-width:850px){{.layout{{display:block}}aside{{border:0;border-top:1px solid var(--line)}}.summary{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>Revisione del gruppo</h1><small>{concept_h} · {meaning_h} · conferma una volta, poi lavora sulle eccezioni.</small></header><div class="layout"><main><div class="summary"><div class="metric"><b id="high">–</b>alta similarità</div><div class="metric"><b id="review">–</b>da verificare</div><div class="metric"><b id="low">–</b>bassa similarità</div></div><div id="rows"></div></main><aside><div id="viewer"><img id="page" alt="Pagina documento" hidden><div id="box" hidden></div></div><div class="note">Le bande sono proposte di similarità, non classificazioni. La conferma alimenta solo la memoria locale del progetto.</div><label>Revisore<input id="reviewer" type="text"></label><label>Motivazione<textarea id="rationale" placeholder="Perché il gruppo è coerente o non coerente con il prototipo insegnato?"></textarea></label><div class="actions"><button id="confirm" class="positive">Conferma selezionati</button><button id="reject" class="negative">Non appartengono</button><button id="ambiguous" class="uncertain">Segna ambigui</button><button id="refresh" class="primary">Ricalcola gruppo</button></div><p id="message" class="meta"></p><p><a href="/workbench/document-discovery">← Torna a Document Discovery</a></p></aside></div><script>
const session={session_js},concept={concept_js},meaning={meaning_js};let snapshot=null;const q=id=>document.getElementById(id);const h=s=>String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));async function api(url,opt){{const r=await fetch(url,opt);const b=await r.json();if(!r.ok)throw Error(b.reason||b.state||`HTTP ${{r.status}}`);return b}}function selectedIds(){{return [...document.querySelectorAll('.pick:checked')].map(x=>x.value)}}function show(row){{const img=q('page'),box=q('box'),viewer=q('viewer');img.hidden=false;img.src=`/api/workbench/document-discovery/session/${{encodeURIComponent(session)}}/page/${{row.page_index}}.jpg`;img.onload=()=>{{const b=row.bbox;box.hidden=false;box.style.left=(img.offsetLeft+b.x*img.clientWidth)+'px';box.style.top=(img.offsetTop+b.y*img.clientHeight)+'px';box.style.width=(b.w*img.clientWidth)+'px';box.style.height=(b.h*img.clientHeight)+'px'}}}}function render(){{q('high').textContent=snapshot.band_counts.HIGH_SIMILARITY_PROPOSAL;q('review').textContent=snapshot.band_counts.REVIEW_PROPOSAL;q('low').textContent=snapshot.band_counts.LOW_SIMILARITY_PROPOSAL;const defaults=new Set(snapshot.default_selected_candidate_ids);q('rows').innerHTML=snapshot.members.map(row=>`<div class="card ${{row.is_training_example?'training':''}}"><input class="pick" type="checkbox" aria-label="Seleziona candidato ${{h(row.candidate_id)}}" value="${{h(row.candidate_id)}}" ${{defaults.has(row.candidate_id)?'checked':''}} ${{row.is_training_example?'disabled':''}}><span><b>${{h(row.primitive_family||'candidato')}}</b><span class="meta">${{h(row.candidate_id)}} · ${{h(row.similarity_band)}}${{row.is_training_example?' · già in memoria':''}}</span></span><button type="button" class="inspect" data-id="${{h(row.candidate_id)}}" aria-label="Ispeziona candidato ${{h(row.candidate_id)}}"><span class="score">${{(row.fused_score*100).toFixed(1)}}%</span></button></div>`).join('');for(const b of document.querySelectorAll('.inspect'))b.onclick=()=>{{const row=snapshot.members.find(x=>x.candidate_id===b.dataset.id);if(row)show(row)}};q('message').textContent=`${{snapshot.candidate_count}} proposte. Selezione predefinita: solo alta similarità non ancora usata come training.`}}async function load(){{snapshot=await api(`/api/workbench/document-discovery/session/${{encodeURIComponent(session)}}/group`,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{concept_id:concept,meaning,limit:80}})}});render()}}async function decide(action){{try{{const ids=selectedIds();if(!ids.length)throw Error('Seleziona almeno un candidato.');const reviewer=q('reviewer').value.trim(),rationale=q('rationale').value.trim();if(!reviewer||!rationale)throw Error('Indica revisore e motivazione.');const b=await api(`/api/workbench/document-discovery/session/${{encodeURIComponent(session)}}/group/decision`,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{concept_id:concept,meaning,limit:80,group_fingerprint:snapshot.group_fingerprint,action,selected_candidate_ids:ids,reviewer,rationale}})}});q('message').textContent=`Decisione di gruppo registrata · ${{b.selected_count}} candidati · memoria +${{b.example_counts.POSITIVE}} / −${{b.example_counts.NEGATIVE}} / ?${{b.example_counts.AMBIGUOUS}}`;await load()}}catch(e){{q('message').textContent=e.message}}}}q('confirm').onclick=()=>decide('CONFIRM_SELECTED');q('reject').onclick=()=>decide('REJECT_SELECTED');q('ambiguous').onclick=()=>decide('MARK_SELECTED_AMBIGUOUS');q('refresh').onclick=()=>load().catch(e=>q('message').textContent=e.message);load().catch(e=>q('message').textContent=e.message);
</script></body></html>'''


def build_router() -> APIRouter:
    install()
    router = APIRouter()

    # This route must be mounted before the async-preview and historical
    # Document Discovery HTML routes. It preserves the async page and changes
    # only the Find Similar destination.
    @router.get("/workbench/document-discovery", response_class=HTMLResponse)
    def document_discovery_page():
        return HTMLResponse(
            _patched_document_discovery_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
                "X-CEW-Preview-Execution": "ASYNC_BOUNDED",
                "X-CEW-Group-Review": "GUIDED_V1",
            },
        )

    @router.get("/workbench/guided-group-review", response_class=HTMLResponse)
    def page(session: str = "", concept: str = "", meaning: str = ""):
        if not session.strip() or not concept.strip() or not meaning.strip():
            return HTMLResponse("<h1>Revisione gruppo non disponibile</h1><p>Sessione, concetto e significato sono obbligatori.</p>", status_code=400)
        return HTMLResponse(
            _page(session.strip(), concept.strip(), meaning.strip()),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
            },
        )

    @router.post("/api/workbench/document-discovery/session/{session_id}/group")
    async def group_snapshot(session_id: str, request: Request):
        try:
            body = await request.json()
            return _json(_review_group(
                session_id,
                body.get("concept_id"),
                body.get("meaning"),
                int(body.get("limit", 80)),
            ))
        except ValueError as exc:
            return _json({"state": "GUIDED_GROUP_REVIEW_REJECTED", "reason": str(exc)}, 409)

    @router.post("/api/workbench/document-discovery/session/{session_id}/group/decision")
    async def group_decision(session_id: str, request: Request):
        try:
            return _json(_review_group_decision(session_id, await request.json()))
        except ValueError as exc:
            return _json({"state": "GUIDED_GROUP_DECISION_REJECTED", "reason": str(exc)}, 409)

    return router
