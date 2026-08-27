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
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_f7_native_review_service as review_service
import cew_project_control_room as control_room
import cew_runtime_audit_store as audit_store

# Production and local runtime use the same F7 pipeline; only the audit backend changes.
review_service.persist_runtime_receipt = audit_store.persist_runtime_receipt

app = FastAPI(title="CEW Project Control Room", docs_url=None, redoc_url=None)
SESSION_COOKIE = "cew_session"
SESSION_PURPOSE = b"CEW_SINGLE_OPERATOR_PILOT_V1"
PRODUCTION_AUDIT_BACKENDS = {"SUPABASE_APPEND_ONLY", "NETLIFY_AUDIT_HTTPS"}


def _auth_disabled_for_test() -> bool:
    return os.getenv("CEW_AUTH_DISABLED_FOR_TEST") == "1" and not os.getenv("VERCEL")


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
<style>body{{font-family:system-ui;background:#f4f6f8;margin:0;color:#17202a}}main{{max-width:440px;margin:10vh auto;background:white;padding:28px;border:1px solid #d8dde3;border-radius:12px}}input,button{{width:100%;box-sizing:border-box;padding:11px;margin-top:8px}}button{{background:#17202a;color:white;border:0;border-radius:7px;font-weight:700}}.error{{color:#a12622}}</style></head><body><main><h1>CEW</h1><p>Project Control Room — accesso tecnico</p>{config_note}{note}<form method="post" action="/login"><label>Password operatore<input type="password" name="password" autocomplete="current-password" autofocus></label><button type="submit">Accedi</button></form></main></body></html>'''


@app.middleware("http")
async def access_guard(request: Request, call_next):
    path = request.url.path
    if path in {"/healthz", "/login"}:
        return await call_next(request)
    if not _authorized(request):
        return RedirectResponse(url="/login", status_code=303)
    return await call_next(request)


@app.get("/healthz")
def healthz():
    backend = audit_store.backend_status()
    return {
        "service": "CEW_USER_WEB_PILOT",
        "status": "OK" if (_auth_configured() or _auth_disabled_for_test()) else "CONFIG_REQUIRED",
        "auth_configured": _auth_configured(),
        "audit_backend": backend,
        "production_receipt_submit_ready": backend in PRODUCTION_AUDIT_BACKENDS,
        "canonical_write_authorized": False,
    }


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
        secure=bool(os.getenv("VERCEL")) or request.url.scheme == "https",
        samesite="lax",
        max_age=12 * 60 * 60,
    )
    return response


@app.post("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/", response_class=HTMLResponse)
def control_room_home():
    state = review_service.load_json(review_service.STATE)
    issues = review_service.load_json(review_service.ISSUES)
    tasks = review_service.rows(review_service.TASKS)
    body = control_room.build(state, issues, tasks)
    marker = "</header>"
    toolbar = "<div style='max-width:1400px;margin:auto;padding:0 32px 12px'><form method='post' action='/logout'><button style='padding:7px 10px'>Esci</button></form></div>"
    return HTMLResponse(body.replace(marker, marker + toolbar, 1))


@app.get("/review/f7", response_class=HTMLResponse)
def review_f7(task: str = ""):
    return HTMLResponse(review_service.render_review(task))


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
