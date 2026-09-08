#!/usr/bin/env python3
"""Authenticated Workbench surface for G4/TAV-05S evidence localization.

The router is included by the existing Professional Workbench router, therefore
it inherits the application's global authentication middleware. Geometry
receipts are append-only runtime audit evidence; this module never writes the
canonical EvidenceRegion registry and never grants OAR classification authority.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import cew_oar_g4_region_binding as binding
import cew_runtime_audit_store as audit_store

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT / "archive" / "documentazione_originaria" / "tavola 5.pdf"
RUNTIME_STORE = Path("/tmp/cew-runtime/oar-g4-region-receipts")
RUNTIME_RASTER = Path("/tmp/cew-runtime/oar-g4-region-assets/TAV05S_150dpi.png")
EXPECTED_SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
EXPECTED_PAGE_WIDTH_PT = 1683.72
EXPECTED_PAGE_HEIGHT_PT = 3007.08
RUNTIME_DPI = 150
SAFE_SUPPORT_FOR_ID = re.compile(r"[^A-Za-z0-9._-]+")


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    body = dict(payload)
    body.setdefault("canonical_write_authorized", False)
    body.setdefault("engineering_authority_effect", "NONE")
    return JSONResponse(body, status_code=status_code, headers={"Cache-Control": "no-store"})


def _error(state: str, reason: str, status_code: int) -> JSONResponse:
    return _json({"state": state, "reason": reason}, status_code)


def _source_sha256() -> str:
    digest = hashlib.sha256()
    with SOURCE_PDF.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source() -> dict[str, Any]:
    if not SOURCE_PDF.is_file():
        raise ValueError("OAR_G4_SOURCE_PDF_NOT_FOUND")
    digest = _source_sha256()
    if digest != EXPECTED_SOURCE_SHA256:
        raise ValueError("OAR_G4_SOURCE_SHA256_MISMATCH")
    try:
        import fitz
    except Exception as exc:
        raise ValueError("OAR_G4_PYMUPDF_UNAVAILABLE") from exc
    document = fitz.open(SOURCE_PDF)
    try:
        if document.page_count != 1:
            raise ValueError("OAR_G4_SOURCE_PAGE_COUNT_MISMATCH")
        page = document[0]
        width = float(page.rect.width)
        height = float(page.rect.height)
        if abs(width - EXPECTED_PAGE_WIDTH_PT) > 0.01 or abs(height - EXPECTED_PAGE_HEIGHT_PT) > 0.01:
            raise ValueError("OAR_G4_SOURCE_PAGE_DIMENSIONS_MISMATCH")
    finally:
        document.close()
    return {
        "state": "READY",
        "source_sha256": digest,
        "page_width_pt": EXPECTED_PAGE_WIDTH_PT,
        "page_height_pt": EXPECTED_PAGE_HEIGHT_PT,
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "canonical_write_authorized": False,
    }


def ensure_runtime_raster() -> Path:
    verification = verify_source()
    RUNTIME_RASTER.parent.mkdir(parents=True, exist_ok=True)
    if RUNTIME_RASTER.is_file():
        return RUNTIME_RASTER
    import fitz
    document = fitz.open(SOURCE_PDF)
    try:
        page = document[0]
        pixmap = page.get_pixmap(dpi=RUNTIME_DPI, alpha=False)
        pixmap.save(RUNTIME_RASTER)
    finally:
        document.close()
    # The runtime image is a derived interaction aid only. Re-check the source
    # identity after generation so a race/replacement cannot silently pass.
    if _source_sha256() != verification["source_sha256"]:
        RUNTIME_RASTER.unlink(missing_ok=True)
        raise ValueError("OAR_G4_SOURCE_CHANGED_DURING_RENDER")
    return RUNTIME_RASTER


def load_report() -> dict[str, Any]:
    loaded = audit_store.load_runtime_receipts(binding.RECEIPT_TYPE, RUNTIME_STORE)
    report = binding.aggregate(loaded["receipts"])
    report["audit_backend"] = loaded["audit_backend"]
    report["receipt_count"] = loaded["receipt_count"]
    report["source_verification"] = verify_source()
    report["runtime_raster"] = {
        "dpi": RUNTIME_DPI,
        "authority": "DERIVED_INTERACTION_AID_ONLY",
        "canonical_asset": False,
    }
    return report


def _latest_proposal_bbox(report: dict[str, Any], support_id: str) -> dict[str, float]:
    row = next((item for item in report["objects"] if str(item["support_id"]) == str(support_id)), None)
    if row is None:
        raise ValueError("OAR_REGION_SUPPORT_NOT_IN_PILOT")
    if row["state"] != "PROPOSED" or not isinstance(row.get("bbox"), dict):
        raise ValueError("OAR_REGION_CONFIRMATION_REQUIRES_CURRENT_PROPOSAL")
    return row["bbox"]


def persist_action(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("OAR_REGION_REQUEST_OBJECT_REQUIRED")
    allowed = {"decision_id", "support_id", "action", "bbox"}
    if not set(payload).issubset(allowed) or not {"decision_id", "support_id", "action"}.issubset(payload):
        raise ValueError("OAR_REGION_REQUEST_FIELD_SET_INVALID")
    action = str(payload["action"])
    support_id = str(payload["support_id"])
    current = load_report()
    if action == binding.PROPOSAL_ACTION:
        bbox = payload.get("bbox")
    elif action == binding.CONFIRM_ACTION:
        # Confirmation is server-bound to the current proposal. A client cannot
        # alter coordinates while confirming.
        bbox = _latest_proposal_bbox(current, support_id)
        if "bbox" in payload and payload["bbox"] is not None and binding.normalize_bbox(payload["bbox"]) != bbox:
            raise ValueError("OAR_REGION_CONFIRMATION_BBOX_MISMATCH")
    else:
        raise ValueError("OAR_REGION_ACTION_INVALID")

    receipt = binding.build_receipt(
        decision_id=str(payload["decision_id"]),
        support_id=support_id,
        bbox=bbox,
        action=action,
    )
    # Validate the complete governed sequence before append-only persistence.
    loaded = audit_store.load_runtime_receipts(binding.RECEIPT_TYPE, RUNTIME_STORE)
    binding.aggregate([*loaded["receipts"], receipt])
    persisted = audit_store.persist_runtime_receipt(receipt, RUNTIME_STORE)
    report = load_report()
    row = next(item for item in report["objects"] if str(item["support_id"]) == support_id)
    return {
        "state": "OAR_REGION_RECEIPT_PERSISTED_AUDIT_ONLY",
        "runtime_receipt_id": persisted["runtime_receipt_id"],
        "sha256": persisted["sha256"],
        "audit_backend": persisted["audit_backend"],
        "support_id": support_id,
        "object_state": row["state"],
        "bbox": row["bbox"],
        "summary": report["summary"],
        "next_gate": report["next_gate"],
        "oar_human_confirmation": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def build_page() -> str:
    contract = binding.load_contract()
    buttons = "".join(
        f'<button class="support" data-support="{html.escape(str(row["support_id"]), quote=True)}">'
        f'{html.escape(str(row["support_id"]))}<span>{html.escape(str(row["family_id"]))}</span></button>'
        for row in contract["objects"]
    )
    return f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CEW — Localizzazione pilastri G4</title>
<style>
:root{{--bg:#eef1f4;--panel:#fff;--ink:#17202a;--muted:#5d6875;--line:#cfd6dd;--accent:#173f5f;--ok:#1e6b45;--warn:#8a5a00}}
*{{box-sizing:border-box}} body{{margin:0;font-family:system-ui;background:var(--bg);color:var(--ink)}}
header{{display:flex;gap:14px;align-items:center;padding:12px 16px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}}
header h1{{font-size:17px;margin:0}} header .meta{{font-size:12px;color:var(--muted)}} header a{{margin-left:auto;color:var(--accent)}}
main{{display:grid;grid-template-columns:270px minmax(0,1fr) 300px;min-height:calc(100vh - 55px)}}
aside{{background:var(--panel);padding:14px;border-right:1px solid var(--line);overflow:auto;max-height:calc(100vh - 55px);position:sticky;top:55px}}
aside.right{{border-left:1px solid var(--line);border-right:0}} h2{{font-size:14px;margin:0 0 10px}}
.supports{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}} .support{{padding:7px 4px;border:1px solid var(--line);background:#fff;border-radius:6px;cursor:pointer;font-weight:700}}
.support span{{display:block;font-size:8px;font-weight:400;color:var(--muted);overflow:hidden}} .support.active{{outline:2px solid var(--accent)}} .support.confirmed{{border-color:var(--ok)}} .support.proposed{{border-color:var(--warn)}}
.stage-scroll{{overflow:auto;padding:16px;max-height:calc(100vh - 55px)}} .stage{{position:relative;width:min(100%,900px);margin:0 auto;background:white;box-shadow:0 2px 12px #0002}}
.stage img{{width:100%;height:auto;display:block;user-select:none;-webkit-user-drag:none}} #overlay{{position:absolute;inset:0;width:100%;height:100%;touch-action:none;cursor:crosshair}}
#box{{fill:#173f5f22;stroke:#173f5f;stroke-width:2;vector-effect:non-scaling-stroke}} .field{{font-size:13px;margin:8px 0}} .field b{{display:block}}
button.action{{width:100%;padding:10px;margin-top:8px;border:0;border-radius:7px;font-weight:700;cursor:pointer}} #propose{{background:var(--accent);color:#fff}} #confirm{{background:var(--ok);color:#fff}} #confirm:disabled,#propose:disabled{{opacity:.4;cursor:not-allowed}}
.notice{{font-size:12px;color:var(--muted);line-height:1.4}} #message{{font-size:12px;min-height:42px;padding:8px;background:#f5f7f8;border-radius:6px;white-space:pre-wrap}} code{{font-size:11px}}
@media(max-width:900px){{main{{grid-template-columns:1fr}} aside{{position:static;max-height:none;border:0;border-bottom:1px solid var(--line)}} aside.right{{border:0;border-top:1px solid var(--line)}} .stage-scroll{{max-height:none}}}}
</style></head><body>
<header><div><h1>Localizzazione documentale — Pilastri G4</h1><div class="meta">TAV-05S · pagina verificata · coordinate normalizzate 0–1</div></div><a href="/">Progetto</a></header>
<main>
<aside><h2>Supporti</h2><div class="supports">{buttons}</div><p class="notice">Seleziona un supporto, traccia il rettangolo sulla tavola intera e registra la proposta. La conferma successiva riguarda solo la localizzazione documentale.</p></aside>
<section class="stage-scroll"><div class="stage" id="stage"><img id="source" src="/workbench/oar/g4-regions/source.png" alt="TAV-05S verificata"><svg id="overlay" viewBox="0 0 1 1" preserveAspectRatio="none"><rect id="box" x="0" y="0" width="0" height="0" visibility="hidden"/></svg></div></section>
<aside class="right"><h2>Decisione geometrica</h2><div class="field"><b>Supporto</b><span id="selected">—</span></div><div class="field"><b>Stato</b><span id="state">UNBOUND</span></div><div class="field"><b>Rettangolo normalizzato</b><code id="bbox">—</code></div><button class="action" id="propose" disabled>Registra proposta geometrica</button><button class="action" id="confirm" disabled>Conferma localizzazione</button><p class="notice"><b>Non conferma:</b> famiglia OAR, identità strutturale o scrittura canonica.</p><div id="message"></div></aside>
</main>
<script>
const overlay=document.getElementById('overlay'), box=document.getElementById('box');
const selectedEl=document.getElementById('selected'), stateEl=document.getElementById('state'), bboxEl=document.getElementById('bbox');
const propose=document.getElementById('propose'), confirmBtn=document.getElementById('confirm'), message=document.getElementById('message');
let report=null, selected=null, draft=null, dragStart=null;
function sanitize(v){{return String(v).replace(/[^A-Za-z0-9._-]+/g,'_')}}
function decision(action){{return `oar-g4-${{sanitize(selected)}}-${{action.toLowerCase()}}-${{Date.now()}}`}}
function point(ev){{const r=overlay.getBoundingClientRect();return {{x:Math.max(0,Math.min(1,(ev.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(ev.clientY-r.top)/r.height))}}}}
function setBox(b){{draft=b;if(!b){{box.setAttribute('visibility','hidden');bboxEl.textContent='—';return}};box.setAttribute('x',b.x);box.setAttribute('y',b.y);box.setAttribute('width',b.w);box.setAttribute('height',b.h);box.setAttribute('visibility','visible');bboxEl.textContent=JSON.stringify(b)}}
function row(){{return report?.objects.find(o=>String(o.support_id)===String(selected))}}
function refreshSelection(){{const r=row();selectedEl.textContent=selected??'—';stateEl.textContent=r?.state??'UNBOUND';setBox(r?.bbox??null);propose.disabled=!selected;confirmBtn.disabled=!(r&&r.state==='PROPOSED');document.querySelectorAll('.support').forEach(b=>{{b.classList.toggle('active',b.dataset.support===String(selected));const rr=report?.objects.find(o=>String(o.support_id)===b.dataset.support);b.classList.toggle('confirmed',rr?.state==='GEOMETRY_CONFIRMED');b.classList.toggle('proposed',rr?.state==='PROPOSED')}})}}
async function load(){{const res=await fetch('/api/workbench/oar/g4-regions/status',{{cache:'no-store'}});report=await res.json();if(!res.ok)throw new Error(report.reason||report.state);refreshSelection()}}
document.querySelectorAll('.support').forEach(b=>b.addEventListener('click',()=>{{selected=b.dataset.support;refreshSelection()}}));
overlay.addEventListener('pointerdown',ev=>{{if(!selected)return;dragStart=point(ev);overlay.setPointerCapture(ev.pointerId)}});
overlay.addEventListener('pointermove',ev=>{{if(!dragStart)return;const p=point(ev),x=Math.min(dragStart.x,p.x),y=Math.min(dragStart.y,p.y);setBox({{x,y,w:Math.abs(p.x-dragStart.x),h:Math.abs(p.y-dragStart.y)}});propose.disabled=!(draft&&draft.w>0&&draft.h>0)}});
overlay.addEventListener('pointerup',ev=>{{if(!dragStart)return;dragStart=null;try{{overlay.releasePointerCapture(ev.pointerId)}}catch(e){{}}}});
async function send(action){{if(!selected)return;const payload={{decision_id:decision(action),support_id:selected,action}};if(action==='PROPOSE_GEOMETRY')payload.bbox=draft;message.textContent='Registrazione…';const res=await fetch('/api/workbench/oar/g4-regions/receipt',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});const body=await res.json();if(!res.ok){{message.textContent=`${{body.state}}\n${{body.reason}}`;return}};message.textContent=`${{body.state}}\nSupporto ${{body.support_id}} → ${{body.object_state}}`;await load()}}
propose.addEventListener('click',()=>send('PROPOSE_GEOMETRY'));confirmBtn.addEventListener('click',()=>send('CONFIRM_GEOMETRY'));
load().catch(e=>{{message.textContent=String(e)}});
</script></body></html>'''


def build_router() -> APIRouter:
    router = APIRouter()

    @router.get("/workbench/oar/g4-regions", response_class=HTMLResponse)
    def region_workbench():
        try:
            verify_source()
        except ValueError as exc:
            return HTMLResponse(
                f"<h1>Localizzazione non disponibile</h1><p>{html.escape(str(exc))}</p><a href='/'>Torna al progetto</a>",
                status_code=503,
            )
        return HTMLResponse(
            build_page(),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Review-Authority": "HUMAN_EVIDENCE_LOCALIZATION_ONLY",
                "X-CEW-OAR-Human-Confirmation": "false",
                "X-CEW-Canonical-Write": "false",
            },
        )

    @router.get("/workbench/oar/g4-regions/source.png")
    def region_source_image():
        try:
            target = ensure_runtime_raster()
        except ValueError as exc:
            return _error("OAR_G4_SOURCE_RENDER_UNAVAILABLE", str(exc), 503)
        return FileResponse(
            target,
            media_type="image/png",
            headers={
                "Cache-Control": "private, max-age=3600",
                "X-CEW-Derived-Authority": "DERIVED_INTERACTION_AID_ONLY",
                "X-CEW-Source-SHA256": EXPECTED_SOURCE_SHA256,
                "X-CEW-Canonical-Write": "false",
            },
        )

    @router.get("/api/workbench/oar/g4-regions/status")
    def region_status():
        try:
            return _json(load_report())
        except ValueError as exc:
            return _error("OAR_G4_REGION_STATUS_UNAVAILABLE", str(exc), 503)

    @router.post("/api/workbench/oar/g4-regions/receipt")
    async def region_receipt(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return _error("OAR_G4_REGION_RECEIPT_REJECTED", "INVALID_JSON", 400)
        try:
            result = persist_action(payload)
        except ValueError as exc:
            marker = str(exc)
            status = 409 if "duplicate decision_id" in marker.lower() else 422
            return _error("OAR_G4_REGION_RECEIPT_REJECTED", marker, status)
        return _json(result)

    return router
