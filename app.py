#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import hmac
import html
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_b1_acceptance_lab as acceptance_lab
import cew_document_drawing_workspace as document_workspace
import cew_document_intake as document_intake
import cew_document_map_page as document_map_page
import cew_drawing_viewer as drawing_viewer
import cew_f7_native_review_service as review_service
import cew_project_control_room as control_room
import cew_project_home as project_home
import cew_runtime_audit_store as audit_store
import cew_source_evidence_workspace as source_workspace

review_service.persist_runtime_receipt = audit_store.persist_runtime_receipt

app = FastAPI(title="CEW — Structural Existing Workflow", docs_url=None, redoc_url=None)
SESSION_COOKIE = "cew_session"
SESSION_PURPOSE = b"CEW_SINGLE_OPERATOR_PILOT_V1"
PRODUCTION_AUDIT_BACKENDS = {"SUPABASE_APPEND_ONLY", "NETLIFY_AUDIT_HTTPS", "NEON_APPEND_ONLY"}
TERMINOLOGY = ROOT / "automation/CEW_TERMINOLOGY_LAYER_v1.json"
LIFECYCLE = ROOT / "automation/CEW_PROJECT_LIFECYCLE_MODEL_v1.json"


def _managed_runtime() -> bool:
    return bool(os.getenv("VERCEL") or os.getenv("RENDER"))


def _runtime_provider() -> str:
    if os.getenv("RENDER"):
        return "RENDER"
    if os.getenv("VERCEL"):
        return "VERCEL"
    return "LOCAL"


def _runtime_revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("CEW_RUNTIME_REVISION")
        or "LOCAL"
    )


def _auth_disabled_for_test() -> bool:
    return os.getenv("CEW_AUTH_DISABLED_FOR_TEST") == "1" and not _managed_runtime()


def _auth_configured() -> bool:
    return bool(os.getenv("CEW_ACCESS_PASSWORD")) and bool(os.getenv("CEW_SESSION_SECRET"))


def _session_value() -> str:
    secret = os.getenv("CEW_SESSION_SECRET", "").encode("utf-8")
    return hmac.new(secret, SESSION_PURPOSE, hashlib.sha256).hexdigest()


def _authorized(request: Request) -> bool:
    if _auth_disabled_for_test():
        return True
    if not _auth_configured():
        return False
    value = request.cookies.get(SESSION_COOKIE, "")
    return hmac.compare_digest(value, _session_value())


def _login_page(message: str = "") -> str:
    note = f"<p class='error'>{html.escape(message)}</p>" if message else ""
    config_note = "" if _auth_configured() else "<p class='error'>CEW non è ancora configurato per l'accesso utente.</p>"
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Accesso</title>
<style>body{{font-family:system-ui;background:#f4f6f8;margin:0;color:#17202a}}main{{max-width:440px;margin:10vh auto;background:white;padding:28px;border:1px solid #d8dde3;border-radius:12px}}input,button{{width:100%;box-sizing:border-box;padding:11px;margin-top:8px}}button{{background:#173f5f;color:white;border:0;border-radius:7px;font-weight:700}}.error{{color:#a12622}}.muted{{color:#5d6875}}</style></head><body><main><h1>CEW</h1><p>Ambiente di lavoro per la valutazione strutturale dell’esistente</p><p class="muted">Accesso operatore</p>{config_note}{note}<form method="post" action="/login"><label>Password<input type="password" name="password" autocomplete="current-password" autofocus></label><button type="submit">Accedi al progetto</button></form></main></body></html>'''


@app.middleware("http")
async def access_guard(request: Request, call_next):
    if request.url.path in {"/healthz", "/readyz", "/login"}:
        return await call_next(request)
    if not _authorized(request):
        return RedirectResponse(url="/login", status_code=303)
    return await call_next(request)


@app.get("/healthz")
def healthz():
    backend = audit_store.backend_status()
    return {
        "service": "CEW_USER_RUNTIME",
        "status": "OK" if (_auth_configured() or _auth_disabled_for_test()) else "CONFIG_REQUIRED",
        "runtime_provider": _runtime_provider(),
        "runtime_revision": _runtime_revision(),
        "runtime_role": os.getenv("CEW_RUNTIME_ROLE", "UNSPECIFIED"),
        "auth_configured": _auth_configured(),
        "audit_backend": backend,
        "production_receipt_submit_ready": backend in PRODUCTION_AUDIT_BACKENDS,
        "document_workspace": "B11_AVAILABLE",
        "drawing_register": "B11_AVAILABLE",
        "drawing_viewer": "B12_PREP_AVAILABLE_NOT_PROMOTED",
        "document_map": "B13_PREP_AVAILABLE_NOT_PROMOTED",
        "document_intake": "B14_METADATA_ONLY_PREP_AVAILABLE_NOT_PROMOTED",
        "document_byte_storage": "NOT_CONFIGURED",
        "b1_acceptance_lab": "B17_PREP_AVAILABLE_NOT_PROMOTED",
        "source_workspace": "B1_AVAILABLE",
        "source_integrity_policy": "IMMUTABLE_COMMIT_PLUS_SHA256_FAIL_CLOSED",
        "canonical_write_authorized": False,
    }


@app.get("/readyz")
def readyz():
    backend = audit_store.backend_status()
    ready = _auth_configured() and backend in PRODUCTION_AUDIT_BACKENDS
    payload = {
        "service": "CEW_USER_RUNTIME",
        "status": "READY" if ready else "CONFIG_REQUIRED",
        "runtime_provider": _runtime_provider(),
        "runtime_revision": _runtime_revision(),
        "runtime_role": os.getenv("CEW_RUNTIME_ROLE", "UNSPECIFIED"),
        "auth_configured": _auth_configured(),
        "audit_backend": backend,
        "persistent_audit_ready": backend in PRODUCTION_AUDIT_BACKENDS,
        "canonical_write_authorized": False,
    }
    return JSONResponse(payload, status_code=200 if ready else 503, headers={"Cache-Control": "no-store"})


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    if _authorized(request):
        return RedirectResponse(url="/", status_code=303)
    return HTMLResponse(_login_page())


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request):
    if not _auth_configured():
        return HTMLResponse(_login_page("Configurazione accesso mancante."), status_code=503)
    raw = (await request.body()).decode("utf-8", errors="replace")
    supplied = parse_qs(raw).get("password", [""])[0]
    expected = os.getenv("CEW_ACCESS_PASSWORD", "")
    if not hmac.compare_digest(supplied, expected):
        return HTMLResponse(_login_page("Password non valida."), status_code=401)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        _session_value(),
        httponly=True,
        secure=_managed_runtime() or request.url.scheme == "https",
        samesite="lax",
        max_age=12 * 60 * 60,
    )
    return response


@app.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


def _runtime_inputs():
    return (
        review_service.load_json(review_service.STATE),
        review_service.load_json(review_service.ISSUES),
        review_service.rows(review_service.TASKS),
    )


@app.get("/", response_class=HTMLResponse)
def project_home_route():
    state, issues, tasks = _runtime_inputs()
    terminology = review_service.load_json(TERMINOLOGY)
    lifecycle = review_service.load_json(LIFECYCLE)
    return HTMLResponse(project_home.build_project_home(state, issues, tasks, terminology, lifecycle))


@app.get("/acceptance/b1", response_class=HTMLResponse)
def b1_acceptance_lab():
    return HTMLResponse(acceptance_lab.build_lab())


@app.get("/documents", response_class=HTMLResponse)
def document_library():
    return HTMLResponse(document_workspace.build_document_library())


@app.get("/documents/intake", response_class=HTMLResponse)
def document_intake_page():
    return HTMLResponse(document_intake.build_intake_page())


@app.post("/api/intake/analyze")
async def document_intake_analyze(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"state": "FAILED", "reason_codes": ["INVALID_JSON"], "bytes_uploaded": False, "canonical_write_authorized": False}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"state": "FAILED", "reason_codes": ["JSON_OBJECT_REQUIRED"], "bytes_uploaded": False, "canonical_write_authorized": False}, status_code=400)
    try:
        result = document_intake.analyze_metadata(payload)
    except ValueError as exc:
        return JSONResponse({"state": "FAILED", "reason_codes": [str(exc)], "bytes_uploaded": False, "canonical_write_authorized": False}, status_code=422)
    return JSONResponse(result, headers={"Cache-Control": "no-store"})


@app.get("/drawings", response_class=HTMLResponse)
def drawing_register():
    return HTMLResponse(document_workspace.build_drawing_register())


@app.get("/drawings/{source_id}", response_class=HTMLResponse)
def drawing_card(source_id: str):
    if source_id not in source_workspace.maps()["sources"]:
        return HTMLResponse("<h1>Tavola non trovata</h1><a href='/drawings'>Torna alle tavole</a>", status_code=404)
    return HTMLResponse(drawing_viewer.build_viewer(source_id))


@app.get("/drawings/{source_id}/map", response_class=HTMLResponse)
def drawing_document_map(source_id: str):
    if source_id not in source_workspace.maps()["sources"]:
        return HTMLResponse("<h1>Tavola non trovata</h1><a href='/drawings'>Torna alle tavole</a>", status_code=404)
    return HTMLResponse(document_map_page.build_page(source_id))


@app.get("/sources", response_class=HTMLResponse)
def source_hub():
    return HTMLResponse(source_workspace.build_source_hub())


@app.get("/sources/{source_id}", response_class=HTMLResponse)
def source_detail(source_id: str):
    if source_id not in source_workspace.maps()["sources"]:
        return HTMLResponse("<h1>Fonte non trovata</h1><a href='/sources'>Torna alle fonti</a>", status_code=404)
    return HTMLResponse(source_workspace.build_source_detail(source_id))


@app.get("/evidence/review", response_class=HTMLResponse)
def evidence_workspace(task: str = ""):
    try:
        source_workspace.task_context(task)
    except (KeyError, ValueError):
        return HTMLResponse("<h1>Evidenza non disponibile</h1><a href='/sources'>Torna alle fonti</a>", status_code=404)
    return HTMLResponse(source_workspace.build_evidence_workspace(task))


@app.get("/api/source/pdf/{source_id}")
def source_pdf(source_id: str):
    try:
        payload, source = source_workspace.fetch_verified_source(source_id)
    except KeyError as exc:
        return JSONResponse({"state": "SOURCE_NOT_FOUND", "reason": str(exc)}, status_code=404)
    except ValueError as exc:
        return JSONResponse({"state": "SOURCE_INTEGRITY_REJECTED", "reason": str(exc)}, status_code=422)
    except Exception:
        return JSONResponse({"state": "SOURCE_ACCESS_UNAVAILABLE", "reason": "VERIFIED_SOURCE_RETRIEVAL_FAILED"}, status_code=503)
    filename = source.get("canonical_filename", f"{source_id}.pdf").replace('"', "")
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={
            "Cache-Control": "private, max-age=300",
            "Content-Disposition": f'inline; filename="{filename}"',
            "X-CEW-Primary-Source": "VERIFIED_IMMUTABLE_PDF",
            "X-CEW-Source-SHA256": source["sha256"],
        },
    )


@app.get("/api/drawing/render/{source_id}")
def drawing_render(source_id: str, dpi: int = drawing_viewer.DEFAULT_DPI):
    try:
        png, ctx = drawing_viewer.render_full_page(source_id, dpi)
    except KeyError as exc:
        return JSONResponse({"state": "DRAWING_SOURCE_NOT_FOUND", "reason": str(exc)}, status_code=404)
    except ValueError as exc:
        return JSONResponse({"state": "DRAWING_RENDER_REJECTED", "reason": str(exc)}, status_code=422)
    except Exception:
        return JSONResponse({"state": "DRAWING_RENDER_UNAVAILABLE", "reason": "VERIFIED_DRAWING_RENDER_FAILED"}, status_code=503)
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "private, max-age=300",
            "X-CEW-Source-SHA256": ctx["verified_sha256"],
            "X-CEW-Page-ID": ctx["page"]["page_id"],
            "X-CEW-Drawing-DPI": str(ctx["dpi"]),
            "X-CEW-Derived-Authority": "READING_AID_ONLY",
            "X-CEW-Canonical-Write": "false",
        },
    )


@app.get("/api/source/render")
def source_render(task: str = "", scale: str = "MICRO"):
    try:
        png, ctx = source_workspace.render_task_source(task, scale)
    except KeyError as exc:
        return JSONResponse({"state": "EVIDENCE_SOURCE_NOT_FOUND", "reason": str(exc)}, status_code=404)
    except ValueError as exc:
        return JSONResponse({"state": "EVIDENCE_RENDER_REJECTED", "reason": str(exc)}, status_code=422)
    except Exception:
        return JSONResponse({"state": "EVIDENCE_RENDER_UNAVAILABLE", "reason": "VERIFIED_RENDER_FAILED"}, status_code=503)
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "private, max-age=300",
            "X-CEW-Source-SHA256": ctx["verified_sha256"],
            "X-CEW-Source-Scale": ctx["scale"],
            "X-CEW-Derived-Authority": "READING_AID_ONLY",
            "X-CEW-Canonical-Write": "false",
        },
    )


@app.get("/technical/control-room", response_class=HTMLResponse)
def technical_control_room():
    state, issues, tasks = _runtime_inputs()
    body = control_room.build(state, issues, tasks)
    marker = "</header>"
    toolbar = "<div style='max-width:1400px;margin:auto;padding:0 32px 12px;display:flex;gap:12px;align-items:center'><a href='/' style='font-weight:700'>← Torna al progetto</a><form method='post' action='/logout'><button style='padding:7px 10px'>Esci</button></form></div>"
    return HTMLResponse(body.replace(marker, marker + toolbar, 1))


@app.get("/review/f7", response_class=HTMLResponse)
def review_f7(task: str = ""):
    return RedirectResponse(url=f"/evidence/review?task={task}", status_code=307)


@app.post("/api/f7/receipt")
async def submit_f7_receipt(request: Request):
    try:
        receipt = await request.json()
    except Exception:
        return JSONResponse({"state": "RECEIPT_REJECTED", "reason_codes": ["INVALID_JSON"], "canonical_write_performed": False}, status_code=400)
    if not isinstance(receipt, dict):
        return JSONResponse({"state": "RECEIPT_REJECTED", "reason_codes": ["JSON_OBJECT_REQUIRED"], "canonical_write_performed": False}, status_code=400)
    local_store = Path(os.getenv("CEW_LOCAL_AUDIT_DIR", "/tmp/cew-runtime/human-receipts"))
    result = review_service.process_receipt(receipt, local_store)
    status = 200 if result.get("state") not in {"RECEIPT_REJECTED"} else 422
    return JSONResponse(result, status_code=status, headers={"Cache-Control": "no-store"})
