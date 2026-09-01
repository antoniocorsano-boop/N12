#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_auth_context as auth_context

CONTRACT = ROOT / "automation/CEW_EWS5_AUTH_CONTEXT_RESTORATION_CONTRACT_v1.json"
APP = ROOT / "app.py"
PILOT = "/workbench?task=OA-N12-G4-COLUMN-PILOT"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["contract"] == "CEW_EWS5_AUTH_CONTEXT_RESTORATION", "contract id drift")
    require(contract["status"] in {"IMPLEMENTED_PENDING_VALIDATION", "EWS5_COMPLETE_PASS"}, "invalid EWS-5 state")
    require(contract["authority_effect"] == "NONE", "auth return-to cannot create authority")
    require(contract["canonical_write_authorized"] is False, "canonical write drift")
    require(contract["project_material_ready"] is False, "project material release drift")

    require(auth_context.safe_return_to(PILOT) == PILOT, "pilot deep link not preserved")
    require(auth_context.safe_return_to("/evidence/review?task=ERW-N12-001") == "/evidence/review?task=ERW-N12-001", "internal query string not preserved")
    require(auth_context.safe_return_to("/") == "/", "home target drift")
    for bad in [
        "https://evil.example/workbench",
        "http://evil.example/",
        "//evil.example/workbench",
        "javascript:alert(1)",
        "workbench?task=x",
        "/login",
        "/logout",
    ]:
        require(auth_context.safe_return_to(bad) == "/", f"unsafe return-to accepted: {bad}")
    login_url = auth_context.login_url_for(PILOT)
    require(login_url.startswith("/login?next="), "login return-to URL missing next")
    require("https%3A" not in login_url and "%2F%2Fevil" not in login_url, "external redirect material leaked")

    source = APP.read_text(encoding="utf-8")
    compile(source, str(APP), "exec")
    for marker in [
        "import cew_auth_context as auth_context",
        "auth_context.login_url_for(_request_return_to(request))",
        "<input type=\"hidden\" name=\"next\"",
        "def login_get(request: Request, next: str = \"/\")",
        "target = auth_context.safe_return_to(next)",
        "target = auth_context.safe_return_to(fields.get(\"next\", [\"/\"])[0])",
        "RedirectResponse(url=target, status_code=303)",
        "_login_page(\"Password non valida.\", target)",
    ]:
        require(marker in source, f"app boundary marker missing: {marker}")
    require('RedirectResponse(url="/", status_code=303)' not in source[source.find('@app.get("/login"'):source.find('@app.post("/logout")')], "login flow still hard-redirects to home")

    security = contract["security_boundary"]
    require(security["same_origin_absolute_path_only"] is True, "same-origin rule weakened")
    require(security["external_absolute_url_rejected"] is True, "external URL rejection weakened")
    require(security["protocol_relative_url_rejected"] is True, "protocol-relative rejection weakened")
    require(security["return_to_is_governed_state"] is False, "return-to must remain UI navigation state")
    require(security["return_to_contains_auth_secret"] is False, "auth secret leakage rule lost")

    forbidden = set(contract["forbidden_shortcuts"])
    for item in {"OPEN_REDIRECT", "EXTERNAL_RETURN_TO", "PROTOCOL_RELATIVE_RETURN_TO", "PASSWORD_IN_RETURN_TO", "SESSION_SECRET_IN_RETURN_TO", "RETURN_TO_CREATES_AUTHORITY", "RETURN_TO_CREATES_CANONICAL_WRITE", "OA6_RELEASE"}:
        require(item in forbidden, f"forbidden shortcut missing: {item}")

    print("CEW_EWS5_AUTH_CONTEXT_RESTORATION = PASS")
    print(f"PILOT_RETURN_TO = {PILOT}")
    print("EXTERNAL_RETURN_TO = REJECTED")
    print("PROTOCOL_RELATIVE_RETURN_TO = REJECTED")
    print("RETURN_TO_AUTHORITY = NONE")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
