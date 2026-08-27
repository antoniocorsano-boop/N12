#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from urllib import error, request

SAFE_DECISION_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def _raw(receipt: dict) -> str:
    return json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def backend_status() -> str:
    https_url = os.getenv("CEW_AUDIT_HTTPS_URL", "").strip()
    https_secret = os.getenv("CEW_AUDIT_SHARED_SECRET", "").strip()
    if https_url and https_secret:
        return "NETLIFY_AUDIT_HTTPS"
    url = os.getenv("CEW_AUDIT_SUPABASE_URL", "").strip()
    key = os.getenv("CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if url and key:
        return "SUPABASE_APPEND_ONLY"
    if os.getenv("VERCEL"):
        return "UNCONFIGURED_PRODUCTION"
    return "FILESYSTEM_APPEND_ONLY"


def _persist_file(receipt: dict, store: Path, digest: str) -> dict:
    decision_id = str(receipt["decision_id"])
    store = store.resolve()
    store.mkdir(parents=True, exist_ok=True)
    target = store / f"{decision_id}.json"
    pretty = json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    try:
        with target.open("x", encoding="utf-8") as f:
            f.write(pretty)
    except FileExistsError as e:
        raise ValueError("duplicate decision_id: runtime receipt already exists") from e
    return {
        "runtime_receipt_id": decision_id,
        "sha256": digest,
        "authority": "RUNTIME_AUDIT_ONLY",
        "audit_backend": "FILESYSTEM_APPEND_ONLY",
        "canonical_write": False,
    }


def _persist_https(receipt: dict, digest: str) -> dict:
    endpoint = os.environ["CEW_AUDIT_HTTPS_URL"].strip()
    secret = os.environ["CEW_AUDIT_SHARED_SECRET"]
    payload = {
        "decision_id": receipt["decision_id"],
        "task_id": receipt.get("task_id"),
        "residual_id": receipt.get("residual_id"),
        "receipt_sha256": digest,
        "receipt_json": receipt,
        "authority": "RUNTIME_AUDIT_ONLY",
        "canonical_write": False,
        "submitted_at": receipt.get("timestamp"),
    }
    req = request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=12) as resp:
            if resp.status not in (200, 201, 204):
                raise ValueError(f"unexpected audit storage status: {resp.status}")
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 409 or "duplicate" in body.lower():
            raise ValueError("duplicate decision_id: runtime receipt already exists") from e
        raise ValueError(f"Netlify audit persistence failed: HTTP {e.code}") from e
    except error.URLError as e:
        raise ValueError("Netlify audit persistence unavailable") from e
    return {
        "runtime_receipt_id": str(receipt["decision_id"]),
        "sha256": digest,
        "authority": "RUNTIME_AUDIT_ONLY",
        "audit_backend": "NETLIFY_AUDIT_HTTPS",
        "canonical_write": False,
    }


def _persist_supabase(receipt: dict, digest: str) -> dict:
    base = os.environ["CEW_AUDIT_SUPABASE_URL"].rstrip("/")
    key = os.environ["CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY"]
    table = os.getenv("CEW_AUDIT_TABLE", "cew_human_receipt_audit")
    payload = {
        "decision_id": receipt["decision_id"],
        "task_id": receipt.get("task_id"),
        "residual_id": receipt.get("residual_id"),
        "receipt_sha256": digest,
        "receipt_json": receipt,
        "authority": "RUNTIME_AUDIT_ONLY",
        "canonical_write": False,
        "submitted_at": receipt.get("timestamp"),
    }
    req = request.Request(
        f"{base}/rest/v1/{table}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    try:
        with request.urlopen(req, timeout=12) as resp:
            if resp.status not in (200, 201, 204):
                raise ValueError(f"unexpected audit storage status: {resp.status}")
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 409 or "23505" in body:
            raise ValueError("duplicate decision_id: runtime receipt already exists") from e
        raise ValueError(f"Supabase audit persistence failed: HTTP {e.code}") from e
    except error.URLError as e:
        raise ValueError("Supabase audit persistence unavailable") from e
    return {
        "runtime_receipt_id": str(receipt["decision_id"]),
        "sha256": digest,
        "authority": "RUNTIME_AUDIT_ONLY",
        "audit_backend": "SUPABASE_APPEND_ONLY",
        "canonical_write": False,
    }


def persist_runtime_receipt(receipt: dict, store: Path) -> dict:
    decision_id = str(receipt.get("decision_id", ""))
    if not SAFE_DECISION_ID.fullmatch(decision_id):
        raise ValueError("decision_id contains unsafe characters")
    digest = hashlib.sha256(_raw(receipt).encode("utf-8")).hexdigest()
    backend = backend_status()
    if backend == "NETLIFY_AUDIT_HTTPS":
        return _persist_https(receipt, digest)
    if backend == "SUPABASE_APPEND_ONLY":
        return _persist_supabase(receipt, digest)
    if backend == "UNCONFIGURED_PRODUCTION":
        raise ValueError("production audit backend is not configured")
    return _persist_file(receipt, store, digest)
