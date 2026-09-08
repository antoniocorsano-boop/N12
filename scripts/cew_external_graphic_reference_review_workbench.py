#!/usr/bin/env python3
"""Human review workspace for acquired external graphic-reference evidence.

This surface is deliberately upstream of the Graphic Reference Library. It can:
- render only queue-listed pages from exact-byte verified acquired sources;
- persist explicit human ACCEPT / REJECT / DEFER review receipts;
- keep DEFER non-terminal while preserving append-only review history;
- materialize a non-promoting EXTERNAL_REFERENCE pack candidate only after the
  complete review queue has terminal ACCEPT/REJECT decisions.

It cannot write the repository library index, grant project semantic authority,
create CAD objects, assign structural identity, or affect engineering authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import pymupdf
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, Response

import cew_external_graphic_reference_acquisition as acquisition_tools
import cew_external_graphic_reference_pack as pack_builder
import cew_new_project_preacquisition as preacquisition
import cew_runtime_audit_store as audit_store

ROOT = Path(__file__).resolve().parents[1]
ACQUISITION_PATH = ROOT / "knowledge" / "graphic_reference" / "CEW_EXTERNAL_REFERENCE_ACQUISITION_RECEIPT_v1.json"
QUEUE_PATH = ROOT / "knowledge" / "graphic_reference" / "CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1.json"
REVIEW_STORE = ROOT / "artifacts" / "cew_external_reference_review_receipts"
RECEIPT_TYPE = "CEW_EXTERNAL_REFERENCE_REVIEW_DECISION_v1"
DECISIONS_SCHEMA = "CEW_EXTERNAL_REFERENCE_REVIEW_DECISIONS_v1"
ACQUISITION_SCHEMA = "CEW_EXTERNAL_REFERENCE_ACQUISITION_RECEIPT_v1"
QUEUE_SCHEMA = "CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1"
ALLOWED_REVIEW_STATES = {"ACCEPT_REFERENCE_EVIDENCE", "REJECT_REFERENCE_EVIDENCE", "DEFER"}
TERMINAL_REVIEW_STATES = {"ACCEPT_REFERENCE_EVIDENCE", "REJECT_REFERENCE_EVIDENCE"}
NONTERMINAL_REVIEW_STATES = {"DEFER"}
SOURCE_CACHE: dict[str, bytes] = {}

AUTHORITY = {
    "library_entries_created": False,
    "project_semantic_authority": "NONE",
    "canonical_write_authorized": False,
    "structural_identity_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    body = dict(payload)
    body.setdefault("authority", dict(AUTHORITY))
    return JSONResponse(body, status_code=status_code, headers={"Cache-Control": "no-store"})


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("REFERENCE_REVIEW_GOVERNED_JSON_INVALID")
    return data


def _governed() -> tuple[dict[str, Any], dict[str, Any]]:
    acquisition = _load_json(ACQUISITION_PATH)
    queue = _load_json(QUEUE_PATH)
    if acquisition.get("schema") != ACQUISITION_SCHEMA:
        raise ValueError("REFERENCE_REVIEW_ACQUISITION_SCHEMA_INVALID")
    if queue.get("schema") != QUEUE_SCHEMA:
        raise ValueError("REFERENCE_REVIEW_QUEUE_SCHEMA_INVALID")
    if acquisition.get("library_promotion_authorized") is not False:
        raise ValueError("REFERENCE_REVIEW_ACQUISITION_AUTHORITY_DRIFT")
    if queue.get("automatic_library_pack_build_authorized") is not False:
        raise ValueError("REFERENCE_REVIEW_QUEUE_AUTHORITY_DRIFT")
    if acquisition.get("authority", {}).get("project_semantic_authority") != "NONE":
        raise ValueError("REFERENCE_REVIEW_ACQUISITION_SEMANTIC_AUTHORITY_DRIFT")
    if queue.get("authority", {}).get("project_semantic_authority") != "NONE":
        raise ValueError("REFERENCE_REVIEW_QUEUE_SEMANTIC_AUTHORITY_DRIFT")
    expected_fingerprint = acquisition.get("artifact", {}).get("receipt_fingerprint")
    if queue.get("acquisition_receipt_fingerprint") != expected_fingerprint:
        raise ValueError("REFERENCE_REVIEW_ACQUISITION_FINGERPRINT_MISMATCH")
    return acquisition, queue


def _source_index(acquisition: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for source in acquisition.get("acquired_sources") or []:
        source_id = str(source.get("source_id") or "")
        if not source_id or source_id in rows:
            raise ValueError("REFERENCE_REVIEW_SOURCE_ID_INVALID_OR_DUPLICATE")
        if source.get("acquisition_status") != "ACQUIRED_EXACT_BYTES":
            raise ValueError("REFERENCE_REVIEW_SOURCE_NOT_EXACT_BYTES")
        rows[source_id] = source
    return rows


def _queue_index(queue: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for item in queue.get("review_items") or []:
        item_id = str(item.get("review_item_id") or "")
        if not item_id or item_id in rows:
            raise ValueError("REFERENCE_REVIEW_ITEM_ID_INVALID_OR_DUPLICATE")
        if item.get("meaning") is not None or item.get("review_state") != "UNREVIEWED":
            raise ValueError("REFERENCE_REVIEW_QUEUE_MUST_BEGIN_UNREVIEWED")
        rows[item_id] = item
    return rows


def _acquired_page(source: dict[str, Any], page_index: int) -> dict[str, Any]:
    matches = [
        row
        for row in source.get("selected_reference_evidence") or []
        if int(row.get("page_index", -1)) == int(page_index)
    ]
    if not matches:
        raise ValueError("REFERENCE_REVIEW_PAGE_NOT_IN_ACQUISITION_RECEIPT")
    first = matches[0]
    for row in matches[1:]:
        for field in ("page_text_sha256", "page_feature_sha256"):
            if row.get(field) != first.get(field):
                raise ValueError("REFERENCE_REVIEW_ACQUIRED_PAGE_FINGERPRINT_CONFLICT")
    return first


def _fetch_verified_source(source: dict[str, Any]) -> bytes:
    source_id = str(source["source_id"])
    cached = SOURCE_CACHE.get(source_id)
    if cached is not None:
        if hashlib.sha256(cached).hexdigest() != str(source["source_sha256"]):
            SOURCE_CACHE.pop(source_id, None)
            raise ValueError("REFERENCE_REVIEW_SOURCE_CACHE_SHA_MISMATCH")
        return cached
    payload, _transport = acquisition_tools._fetch_exact_bytes(str(source["source_url"]))
    digest = hashlib.sha256(payload).hexdigest()
    if digest != str(source["source_sha256"]):
        raise ValueError("REFERENCE_REVIEW_SOURCE_SHA_MISMATCH")
    SOURCE_CACHE[source_id] = payload
    return payload


def _verify_review_page(item: dict[str, Any], source: dict[str, Any], payload: bytes) -> pymupdf.Document:
    if hashlib.sha256(payload).hexdigest() != str(item["source_sha256"]):
        raise ValueError("REFERENCE_REVIEW_ITEM_SOURCE_SHA_MISMATCH")
    doc = pymupdf.open(stream=payload, filetype="pdf")
    page_index = int(item["page_index"])
    if page_index < 0 or page_index >= doc.page_count:
        doc.close()
        raise ValueError("REFERENCE_REVIEW_PAGE_INDEX_OUT_OF_RANGE")
    acquired = _acquired_page(source, page_index)
    page = doc.load_page(page_index)
    page_text = acquisition_tools._normalize_text(page.get_text("text"))
    text_sha = hashlib.sha256(page_text.encode("utf-8")).hexdigest()
    feature_sha, _counts = acquisition_tools._page_feature_fingerprint(page)
    expected_text = str(item["page_text_sha256"])
    expected_feature = str(item["page_feature_sha256"])
    if str(acquired["page_text_sha256"]) != expected_text or text_sha != expected_text:
        doc.close()
        raise ValueError("REFERENCE_REVIEW_PAGE_TEXT_FINGERPRINT_MISMATCH")
    if str(acquired["page_feature_sha256"]) != expected_feature or feature_sha != expected_feature:
        doc.close()
        raise ValueError("REFERENCE_REVIEW_PAGE_FEATURE_FINGERPRINT_MISMATCH")
    return doc


def render_review_page(review_item_id: str, *, scale: float = 1.5) -> bytes:
    acquisition, queue = _governed()
    item = _queue_index(queue).get(str(review_item_id))
    if item is None:
        raise ValueError("REFERENCE_REVIEW_ITEM_UNKNOWN")
    source = _source_index(acquisition).get(str(item["source_id"]))
    if source is None:
        raise ValueError("REFERENCE_REVIEW_SOURCE_NOT_ACQUIRED")
    payload = _fetch_verified_source(source)
    doc = _verify_review_page(item, source, payload)
    try:
        page = doc.load_page(int(item["page_index"]))
        scale = max(0.75, min(2.5, float(scale)))
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        return pix.tobytes("jpeg", jpg_quality=88)
    finally:
        doc.close()


def _require_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"REFERENCE_REVIEW_{field.upper()}_REQUIRED")
    return text


def _decision_order_key(row: dict[str, Any]) -> tuple[datetime, str]:
    value = _require_text(row.get("reviewed_at"), "reviewed_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("REFERENCE_REVIEW_REVIEWED_AT_INVALID") from exc
    if parsed.tzinfo is None:
        raise ValueError("REFERENCE_REVIEW_REVIEWED_AT_TIMEZONE_REQUIRED")
    return parsed.astimezone(timezone.utc), _require_text(row.get("decision_id"), "decision_id")


def build_review_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    acquisition, queue = _governed()
    item_id = _require_text(payload.get("review_item_id"), "review_item_id")
    item = _queue_index(queue).get(item_id)
    if item is None:
        raise ValueError("REFERENCE_REVIEW_ITEM_UNKNOWN")
    source = _source_index(acquisition).get(str(item["source_id"]))
    if source is None:
        raise ValueError("REFERENCE_REVIEW_SOURCE_NOT_ACQUIRED")
    acquired = _acquired_page(source, int(item["page_index"]))
    state = str(payload.get("state") or "")
    if state not in ALLOWED_REVIEW_STATES:
        raise ValueError("REFERENCE_REVIEW_DECISION_STATE_INVALID")
    decision_id = _require_text(payload.get("decision_id"), "decision_id")
    reviewer = _require_text(payload.get("reviewer"), "reviewer")
    rationale = _require_text(payload.get("rationale"), "rationale")
    now = datetime.now(timezone.utc).isoformat()
    receipt: dict[str, Any] = {
        "receipt_type": RECEIPT_TYPE,
        "schema": DECISIONS_SCHEMA,
        "decision_id": decision_id,
        "task_id": item_id,
        "review_item_id": item_id,
        "state": state,
        "source_id": str(item["source_id"]),
        "source_sha256": str(item["source_sha256"]),
        "page_index": int(item["page_index"]),
        "page_number_1_based": int(item["page_number_1_based"]),
        "page_text_sha256": str(item["page_text_sha256"]),
        "page_feature_sha256": str(item["page_feature_sha256"]),
        "discovery_query": item.get("discovery_query"),
        "discovery_queries": item.get("discovery_queries"),
        "meaning": None,
        "scope": None,
        "primitive_families": [],
        "reviewer": reviewer,
        "rationale": rationale,
        "reviewed_at": now,
        "timestamp": now,
        "acquisition_receipt_fingerprint": str(queue["acquisition_receipt_fingerprint"]),
        "automatic_acceptance": False,
        "discovery_query_supplied_meaning": False,
        "terminal_decision": state in TERMINAL_REVIEW_STATES,
        "authority": dict(AUTHORITY),
    }
    if str(receipt["source_sha256"]) != str(source["source_sha256"]):
        raise ValueError("REFERENCE_REVIEW_SOURCE_SHA256_MISMATCH")
    for field in ("page_text_sha256", "page_feature_sha256"):
        if str(receipt[field]) != str(acquired[field]):
            raise ValueError(f"REFERENCE_REVIEW_{field.upper()}_MISMATCH")
    if state == "ACCEPT_REFERENCE_EVIDENCE":
        meaning = _require_text(payload.get("meaning"), "meaning")
        scope_description = _require_text(payload.get("scope_description"), "scope_description")
        primitive_families = payload.get("primitive_families")
        if not isinstance(primitive_families, list) or not primitive_families:
            raise ValueError("REFERENCE_REVIEW_PRIMITIVE_FAMILIES_REQUIRED")
        normalized = sorted({str(value).strip() for value in primitive_families if str(value).strip()})
        if not normalized or any(value not in preacquisition.PRIMITIVE_FAMILIES for value in normalized):
            raise ValueError("REFERENCE_REVIEW_PRIMITIVE_FAMILY_INVALID")
        receipt["meaning"] = meaning
        receipt["scope"] = {"description": scope_description}
        receipt["primitive_families"] = normalized
        aspect_buckets = payload.get("aspect_buckets") or []
        area_buckets = payload.get("area_buckets") or []
        if not isinstance(aspect_buckets, list) or not isinstance(area_buckets, list):
            raise ValueError("REFERENCE_REVIEW_PATTERN_BUCKETS_INVALID")
        receipt["aspect_buckets"] = sorted({str(x).strip() for x in aspect_buckets if str(x).strip()})
        receipt["area_buckets"] = sorted({str(x).strip() for x in area_buckets if str(x).strip()})
        filled = payload.get("filled")
        if filled not in (None, True, False):
            raise ValueError("REFERENCE_REVIEW_FILLED_INVALID")
        receipt["filled"] = filled
        counterexample_refs = payload.get("counterexample_refs") or []
        if not isinstance(counterexample_refs, list):
            raise ValueError("REFERENCE_REVIEW_COUNTEREXAMPLE_REFS_INVALID")
        receipt["counterexample_refs"] = [str(x) for x in counterexample_refs]
    return receipt


def _validated_runtime_history() -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    acquisition, queue = _governed()
    governed = audit_store.load_runtime_receipts(RECEIPT_TYPE, REVIEW_STORE)
    queued = _queue_index(queue)
    raw = list(governed["receipts"])
    raw.sort(key=_decision_order_key)
    seen_decision_ids: set[str] = set()
    by_item: dict[str, list[dict[str, Any]]] = {}

    for row in raw:
        decision_id = _require_text(row.get("decision_id"), "decision_id")
        item_id = _require_text(row.get("review_item_id"), "review_item_id")
        if decision_id in seen_decision_ids:
            raise ValueError("REFERENCE_REVIEW_DECISION_ID_DUPLICATE")
        seen_decision_ids.add(decision_id)
        item = queued.get(item_id)
        if item is None:
            raise ValueError("REFERENCE_REVIEW_RUNTIME_ITEM_UNKNOWN")
        state = str(row.get("state") or "")
        if state not in ALLOWED_REVIEW_STATES:
            raise ValueError("REFERENCE_REVIEW_DECISION_STATE_INVALID")
        for field in ("source_id", "source_sha256", "page_index", "page_text_sha256", "page_feature_sha256"):
            expected: Any = item[field]
            actual: Any = row.get(field)
            if field == "page_index":
                actual = int(actual)
                expected = int(expected)
            if actual != expected:
                raise ValueError(f"REFERENCE_REVIEW_RUNTIME_{field.upper()}_MISMATCH")
        if row.get("authority", {}).get("project_semantic_authority") != "NONE":
            raise ValueError("REFERENCE_REVIEW_RUNTIME_AUTHORITY_DRIFT")
        _decision_order_key(row)
        by_item.setdefault(item_id, []).append(row)

    active_by_item: dict[str, dict[str, Any]] = {}
    terminal_by_item: dict[str, dict[str, Any]] = {}
    history: list[dict[str, Any]] = []
    for item_id in sorted(by_item):
        terminal_seen = False
        for row in sorted(by_item[item_id], key=_decision_order_key):
            state = str(row["state"])
            if terminal_seen:
                raise ValueError("REFERENCE_REVIEW_DECISION_AFTER_TERMINAL")
            history.append(row)
            active_by_item[item_id] = row
            if state in TERMINAL_REVIEW_STATES:
                terminal_seen = True
                terminal_by_item[item_id] = row
    history.sort(key=_decision_order_key)
    return acquisition, queue, history, active_by_item, terminal_by_item


def decisions_document() -> dict[str, Any]:
    _acquisition, queue, history, active, terminal = _validated_runtime_history()
    total = len(queue.get("review_items") or [])
    complete = len(terminal) == total
    return {
        "schema": DECISIONS_SCHEMA,
        "status": "HUMAN_REVIEW_COMPLETE" if complete else "HUMAN_REVIEW_IN_PROGRESS",
        "acquisition_receipt_fingerprint": queue["acquisition_receipt_fingerprint"],
        "review_queue_ref": "knowledge/graphic_reference/CEW_EXTERNAL_REFERENCE_REVIEW_QUEUE_v1.json",
        "decision_history": history,
        "decision_history_count": len(history),
        "active_decisions": [active[item_id] for item_id in sorted(active)],
        "decisions": [terminal[item_id] for item_id in sorted(terminal)],
        "terminal_decision_count": len(terminal),
        "required_terminal_decision_count": total,
        "defer_is_terminal": False,
        "authority": dict(AUTHORITY),
    }


def build_pack_candidate() -> dict[str, Any]:
    acquisition, queue, _history, _active, terminal = _validated_runtime_history()
    total = len(queue.get("review_items") or [])
    if len(terminal) != total:
        raise ValueError("REFERENCE_REVIEW_INCOMPLETE")
    wrapper = {
        "schema": DECISIONS_SCHEMA,
        "status": "HUMAN_REVIEW_COMPLETE",
        "acquisition_receipt_fingerprint": queue["acquisition_receipt_fingerprint"],
        "decisions": [terminal[item_id] for item_id in sorted(terminal)],
        "authority": dict(AUTHORITY),
    }
    candidate = pack_builder.build_pack(acquisition, queue, wrapper)
    candidate["runtime_candidate_only"] = True
    candidate["repository_library_index_written"] = False
    candidate["authority"] = dict(AUTHORITY)
    return candidate


def review_status() -> dict[str, Any]:
    _acquisition, queue, history, active, terminal = _validated_runtime_history()
    items: list[dict[str, Any]] = []
    summary = {"UNREVIEWED": 0, "ACCEPT_REFERENCE_EVIDENCE": 0, "REJECT_REFERENCE_EVIDENCE": 0, "DEFER": 0}
    for item in queue.get("review_items") or []:
        item_id = str(item["review_item_id"])
        decision = active.get(item_id)
        state = str(decision["state"]) if decision else "UNREVIEWED"
        summary[state] += 1
        item_history_count = sum(1 for row in history if str(row["review_item_id"]) == item_id)
        items.append(
            {
                **item,
                "review_state": state,
                "terminal": item_id in terminal,
                "decision_history_count": item_history_count,
                "decision_id": decision.get("decision_id") if decision else None,
                "meaning": decision.get("meaning") if decision else None,
                "scope": decision.get("scope") if decision else None,
                "reviewer": decision.get("reviewer") if decision else None,
                "rationale": decision.get("rationale") if decision else None,
            }
        )
    total = len(items)
    complete = len(terminal) == total
    return {
        "state": "HUMAN_REFERENCE_REVIEW_COMPLETE" if complete else "HUMAN_REFERENCE_REVIEW_REQUIRED",
        "review_item_count": total,
        "summary": summary,
        "terminal_decision_count": len(terminal),
        "decision_history_count": len(history),
        "defer_is_terminal": False,
        "items": items,
        "pack_candidate_available": complete and summary["ACCEPT_REFERENCE_EVIDENCE"] > 0,
        "repository_library_index_written": False,
        "authority": dict(AUTHORITY),
    }


def persist_review_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    receipt = build_review_receipt(payload)
    _acquisition, _queue, history, active, terminal = _validated_runtime_history()
    item_id = str(receipt["review_item_id"])
    decision_id = str(receipt["decision_id"])
    if any(str(row["decision_id"]) == decision_id for row in history):
        raise ValueError("REFERENCE_REVIEW_DECISION_ID_DUPLICATE")
    if item_id in terminal:
        raise ValueError("REFERENCE_REVIEW_ITEM_ALREADY_TERMINAL")
    current = active.get(item_id)
    if current is not None and str(current["state"]) == "DEFER" and receipt["state"] == "DEFER":
        raise ValueError("REFERENCE_REVIEW_ITEM_ALREADY_DEFERRED")
    persisted = audit_store.persist_runtime_receipt(receipt, REVIEW_STORE)
    return {
        "state": "REFERENCE_REVIEW_DECISION_PERSISTED",
        "review_item_id": item_id,
        "decision_state": receipt["state"],
        "terminal_decision": bool(receipt["terminal_decision"]),
        "runtime_receipt_id": persisted["runtime_receipt_id"],
        "sha256": persisted["sha256"],
        "audit_backend": persisted["audit_backend"],
        "repository_library_index_written": False,
        "authority": dict(AUTHORITY),
    }


def _page() -> str:
    primitive_options = "".join(
        f'<label><input type="checkbox" name="primitive" value="{name}"> {name}</label>'
        for name in sorted(preacquisition.PRIMITIVE_FAMILIES)
    )
    return f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CEW — Reference Review</title>
<style>
:root{{--bg:#eef2f5;--panel:#fff;--ink:#17202a;--muted:#63717d;--line:#ccd5dd;--accent:#173f5f;--ok:#1e6b45;--bad:#9b2c2c;--defer:#8a5a00}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,sans-serif}}header{{display:flex;gap:12px;align-items:center;padding:12px 14px;background:#fff;border-bottom:1px solid var(--line)}}header h1{{font-size:17px;margin:0}}header small{{color:var(--muted)}}main{{display:grid;grid-template-columns:290px minmax(0,1fr) 350px;height:calc(100vh - 58px)}}aside{{background:#fff;padding:12px;overflow:auto}}.left{{border-right:1px solid var(--line)}}.right{{border-left:1px solid var(--line)}}#canvas{{overflow:auto;display:flex;align-items:flex-start;justify-content:center;padding:16px;background:#dce2e7}}#pageimg{{max-width:100%;height:auto;box-shadow:0 2px 12px #0003;background:#fff}}.item{{width:100%;text-align:left;border:1px solid var(--line);background:#fff;border-radius:7px;padding:8px;margin:0 0 6px}}.item.active{{outline:2px solid var(--accent)}}.item.accept{{border-color:var(--ok)}}.item.reject{{border-color:var(--bad)}}.item.defer{{border-color:var(--defer)}}.item b{{display:block}}.item small{{color:var(--muted)}}label{{display:block;font-size:12px;margin:7px 0}}input[type=text],textarea{{width:100%;padding:8px;border:1px solid var(--line);border-radius:6px}}textarea{{min-height:74px}}.primitives{{max-height:150px;overflow:auto;border:1px solid var(--line);padding:7px;border-radius:6px}}button.action{{width:100%;border:0;border-radius:7px;padding:10px;margin-top:7px;font-weight:700}}.acceptb{{background:var(--ok);color:#fff}}.rejectb{{background:var(--bad);color:#fff}}.deferb{{background:var(--defer);color:#fff}}.secondary{{background:#e8edf1}}button:disabled{{opacity:.45}}#message{{white-space:pre-wrap;font-size:12px;background:#f4f6f8;padding:8px;border-radius:6px;min-height:54px}}.meta{{font-size:12px;color:var(--muted);line-height:1.5}}@media(max-width:900px){{main{{display:flex;flex-direction:column;height:auto}}.left{{order:1;border:0}}#canvas{{order:2;min-height:55vh}}.right{{order:3;border:0}}aside{{overflow:visible}}}}
</style></head><body>
<header><div><h1>Reference Review Workspace</h1><small>Fonti esterne acquisite · decisione umana prima della libreria</small></div></header>
<main><aside class="left"><div id="summary" class="meta">Caricamento…</div><div id="items"></div></aside><section id="canvas"><img id="pageimg" alt="Pagina di riferimento verificata"></section><aside class="right"><h3 id="itemtitle">Seleziona una pagina</h3><div id="itemmeta" class="meta"></div><label>Revisore<input id="reviewer" type="text" placeholder="Nome o identificativo revisore"></label><label>Rationale<textarea id="rationale" placeholder="Perché questa pagina è utile, non utile o da rinviare"></textarea></label><div id="acceptfields"><label>Significato di riferimento<input id="meaning" type="text" placeholder="Es. convenzione grafica per ..."></label><label>Scope<input id="scope" type="text" placeholder="Ambito preciso; non verità di progetto"></label><div class="primitives">{primitive_options}</div></div><button id="accept" class="action acceptb" disabled>Accetta come riferimento</button><button id="reject" class="action rejectb" disabled>Rifiuta come riferimento</button><button id="defer" class="action deferb" disabled>Rinvia</button><button id="pack" class="action secondary" disabled>Calcola pack candidate</button><p class="meta">DEFER è non terminale: un item rinviato resta aperto e deve poi essere accettato o rifiutato. Il pack resta <b>EXTERNAL_REFERENCE</b> e richiede esiti terminali su tutte le pagine. Nessuna classificazione del progetto, scrittura CAD o identità strutturale viene autorizzata.</p><div id="message"></div></aside></main>
<script>
let report=null,selected=null;const el=id=>document.getElementById(id);const clean=v=>String(v).replace(/[^A-Za-z0-9._-]+/g,'_');
function current(){{return report?.items.find(x=>x.review_item_id===selected)}}
function decisionId(state){{return `gref-review-${{clean(selected)}}-${{state.toLowerCase()}}-${{Date.now()}}`}}
function render(){{const host=el('items');host.innerHTML='';for(const item of report.items){{const b=document.createElement('button');b.className='item';if(item.review_item_id===selected)b.classList.add('active');if(item.review_state==='ACCEPT_REFERENCE_EVIDENCE')b.classList.add('accept');if(item.review_state==='REJECT_REFERENCE_EVIDENCE')b.classList.add('reject');if(item.review_state==='DEFER')b.classList.add('defer');b.innerHTML=`<b>${{item.review_item_id}}</b><small>${{item.source_id}} · pag. ${{item.page_number_1_based}} · ${{item.review_state}} · history ${{item.decision_history_count}}</small>`;b.onclick=()=>selectItem(item.review_item_id);host.appendChild(b)}}const s=report.summary;el('summary').textContent=`Terminali ${{report.terminal_decision_count}}/${{report.review_item_count}} · ${{s.ACCEPT_REFERENCE_EVIDENCE}} accettati · ${{s.REJECT_REFERENCE_EVIDENCE}} rifiutati · ${{s.DEFER}} rinviati · ${{s.UNREVIEWED}} mai rivisti`;el('pack').disabled=!report.pack_candidate_available}}
function selectItem(id){{selected=id;const item=current();render();el('itemtitle').textContent=`${{item.review_item_id}} · pag. ${{item.page_number_1_based}}`;const q=item.discovery_queries?item.discovery_queries.join(', '):item.discovery_query;el('itemmeta').textContent=`Fonte: ${{item.source_id}} · query discovery: ${{q||'—'}} · drawing ${{item.drawing_count}} · text blocks ${{item.text_block_count}} · images ${{item.image_count}}`;el('pageimg').src=`/api/workbench/reference-review/page/${{encodeURIComponent(id)}}.jpg`;const terminal=item.terminal===true;const deferred=item.review_state==='DEFER';el('accept').disabled=terminal;el('reject').disabled=terminal;el('defer').disabled=terminal||deferred;if(terminal)el('message').textContent=`Decisione terminale già registrata: ${{item.review_state}} · ${{item.decision_id}}`;else if(deferred)el('message').textContent=`Item rinviato · ${{item.decision_id}}. DEFER non chiude la review: ispeziona e registra ACCEPT oppure REJECT.`;else el('message').textContent='Ispeziona visivamente la pagina. La query di discovery non assegna il significato.'}}
function primitives(){{return [...document.querySelectorAll('input[name=primitive]:checked')].map(x=>x.value)}}
async function decide(state){{const item=current();if(!item)return;const payload={{decision_id:decisionId(state),review_item_id:item.review_item_id,state,reviewer:el('reviewer').value,rationale:el('rationale').value}};if(state==='ACCEPT_REFERENCE_EVIDENCE'){{payload.meaning=el('meaning').value;payload.scope_description=el('scope').value;payload.primitive_families=primitives()}}el('message').textContent='Registrazione decisione…';const res=await fetch('/api/workbench/reference-review/decision',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});const body=await res.json();if(!res.ok){{el('message').textContent=body.state||'REFERENCE_REVIEW_DECISION_REJECTED';return}}el('message').textContent=`${{body.decision_state}} · terminal=${{body.terminal_decision}} · receipt ${{body.runtime_receipt_id}}`;await load()}}
async function load(){{const res=await fetch('/api/workbench/reference-review/status',{{cache:'no-store'}});const body=await res.json();if(!res.ok)throw new Error(body.state||'REFERENCE_REVIEW_STATUS_BLOCKED');report=body;render();if(selected&&current())selectItem(selected)}}
el('accept').onclick=()=>decide('ACCEPT_REFERENCE_EVIDENCE');el('reject').onclick=()=>decide('REJECT_REFERENCE_EVIDENCE');el('defer').onclick=()=>decide('DEFER');el('pack').onclick=async()=>{{const res=await fetch('/api/workbench/reference-review/pack-candidate',{{cache:'no-store'}});const body=await res.json();el('message').textContent=res.ok?`Pack candidate ${{body.generation_id||'EMPTY'}} · entries ${{body.entry_count}} · repository write=false`:body.state||'REFERENCE_PACK_CANDIDATE_BLOCKED'}};
load().catch(e=>el('message').textContent=e.message);
</script></body></html>'''


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/reference-review", response_class=HTMLResponse)
    def reference_review_page():
        try:
            _governed()
        except (ValueError, OSError, json.JSONDecodeError):
            return HTMLResponse("CEW reference review unavailable", status_code=503)
        return HTMLResponse(
            _page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Reference-Review": "HUMAN_REQUIRED",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Structural-Identity": "false",
            },
        )

    @router.get("/api/workbench/reference-review/status")
    def status():
        try:
            return _json(review_status())
        except (ValueError, OSError, json.JSONDecodeError, TypeError):
            return _json({"state": "REFERENCE_REVIEW_STATUS_BLOCKED"}, 503)

    @router.get("/api/workbench/reference-review/page/{review_item_id}.jpg")
    def page_image(review_item_id: str, scale: float = 1.5):
        try:
            image = render_review_page(review_item_id, scale=scale)
        except (ValueError, OSError, json.JSONDecodeError):
            return _json({"state": "REFERENCE_REVIEW_PAGE_BLOCKED"}, 503)
        return Response(
            content=image,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Source-Verification": "SHA_AND_PAGE_FINGERPRINT_PASS",
                "X-CEW-Reference-Only": "true",
            },
        )

    @router.post("/api/workbench/reference-review/decision")
    def decision(payload: dict[str, Any]):
        try:
            return _json(persist_review_receipt(payload), 201)
        except (ValueError, OSError, json.JSONDecodeError, TypeError):
            return _json({"state": "REFERENCE_REVIEW_DECISION_REJECTED"}, 422)

    @router.get("/api/workbench/reference-review/decisions")
    def decisions():
        try:
            return _json(decisions_document())
        except (ValueError, OSError, json.JSONDecodeError, TypeError):
            return _json({"state": "REFERENCE_REVIEW_DECISIONS_BLOCKED"}, 503)

    @router.get("/api/workbench/reference-review/pack-candidate")
    def pack_candidate():
        try:
            return _json(build_pack_candidate())
        except ValueError as exc:
            if str(exc) == "REFERENCE_REVIEW_INCOMPLETE":
                return _json({"state": "REFERENCE_REVIEW_INCOMPLETE"}, 409)
            return _json({"state": "REFERENCE_PACK_CANDIDATE_BLOCKED"}, 422)
        except (OSError, json.JSONDecodeError, TypeError):
            return _json({"state": "REFERENCE_PACK_CANDIDATE_BLOCKED"}, 503)

    return router
