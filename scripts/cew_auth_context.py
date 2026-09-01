#!/usr/bin/env python3
from __future__ import annotations

from urllib.parse import quote, urlsplit

HOME = "/"
FORBIDDEN_RETURN_PATHS = {"/login", "/logout"}


def safe_return_to(value: str | None) -> str:
    """Return a same-origin absolute-path target or fail closed to project home."""
    raw = (value or HOME).strip()
    if not raw.startswith("/") or raw.startswith("//"):
        return HOME
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc:
        return HOME
    path = parsed.path or HOME
    if path in FORBIDDEN_RETURN_PATHS:
        return HOME
    query = f"?{parsed.query}" if parsed.query else ""
    return path + query


def login_url_for(return_to: str | None) -> str:
    target = safe_return_to(return_to)
    return "/login?next=" + quote(target, safe="")
