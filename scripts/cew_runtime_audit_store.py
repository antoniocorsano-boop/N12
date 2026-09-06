#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from urllib import error, parse, request

SAFE_DECISION_ID = re.compile(r"^[A-Za-z0-9._-]+$")
MAX_GOVERNED_READ_RECEIPTS = 500


def _raw(receipt: dict) -> str:
    return json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def backend_status() -> str:
    neon_url = os.getenv("CEW_AUDIT_NEON_DATABASE_URL", "").strip()
    if neon_url:
        return "NEON_APPEND_ONLY"
    https_url = os.getenv("CEW_AUDIT_HTTPS_URL", "").strip()
    https_secret = os.getenv("CEW_AUDIT_SHARED_SECRET", "").strip()
    if https_url and https_secret:
        return "NETLIFY_AUDIT_HTTPS"
    url = os.getenv("CEW_AUDIT_SUPABASE_URL", "").strip()
    key = os.getenv("CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if url and key:
        return "SUPABASE_APPEND_ONLY"
    if os.getenv("VERCEL") or os.getenv("RENDER"):
        return "UNCONFIGURED_PRODUCTION"
    return "FILESYSTEM_APPEND_ONLY"


def _persist_file(receipt: dict, store: Path, digest: str) -> dict:
    decision_id = str(receipt["decision_id"])
    store = store.resolve()
    store.mkdir(parents=True, exist_ok=True)
    target = store / ("receipt-" + hashlib.sha256(decision_id.encode("utf-8")).hexdigest() + ".json")
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


def _persist_neon(receipt: dict, digest: str) -> dict:
    try:
        import psycopg
        from psycopg.errors import UniqueViolation
    except Exception as e:
        raise ValueError("Neon audit driver unavailable") from e

    payload = {
        "decision_id": receipt["decision_id"],
        "task_id": receipt.get("task_id"),
        "residual_id": receipt.get("residual_id"),
        "receipt_sha256": digest,
        "receipt_json": json.dumps(receipt, ensure_ascii=False, separators=(",", ":")),
        "authority": "RUNTIME_AUDIT_ONLY",
        "canonical_write": False,
        "submitted_at": receipt.get("timestamp"),
    }
    sql = """
        INSERT INTO public.cew_human_receipt_audit
          (decision_id, task_id, residual_id, receipt_sha256, receipt_json,
           authority, canonical_write, submitted_at)
        VALUES
          (%(decision_id)s, %(task_id)s, %(residual_id)s, %(receipt_sha256)s,
           %(receipt_json)s::jsonb, %(authority)s, %(canonical_write)s, %(submitted_at)s)
    """
    try:
        with psycopg.connect(os.environ["CEW_AUDIT_NEON_DATABASE_URL"], connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, payload)
            conn.commit()
    except UniqueViolation as e:
        raise ValueError("duplicate decision_id: runtime receipt already exists") from e
    except Exception as e:
        raise ValueError("Neon audit persistence failed") from e

    return {
        "runtime_receipt_id": str(receipt["decision_id"]),
        "sha256": digest,
        "authority": "RUNTIME_AUDIT_ONLY",
        "audit_backend": "NEON_APPEND_ONLY",
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
    if backend == "NEON_APPEND_ONLY":
        return _persist_neon(receipt, digest)
    if backend == "NETLIFY_AUDIT_HTTPS":
        return _persist_https(receipt, digest)
    if backend == "SUPABASE_APPEND_ONLY":
        return _persist_supabase(receipt, digest)
    if backend == "UNCONFIGURED_PRODUCTION":
        raise ValueError("production audit backend is not configured")
    return _persist_file(receipt, store, digest)


def _receipt_json_object(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("runtime audit receipt_json is invalid") from exc
        if isinstance(payload, dict):
            return payload
    raise ValueError("runtime audit receipt_json must be an object")


def _load_file_receipts(store: Path, receipt_type: str, max_receipts: int) -> list[dict]:
    root = store.resolve()
    if not root.exists():
        return []
    if not root.is_dir():
        raise ValueError("runtime audit store is not a directory")
    receipts: list[dict] = []
    for path in sorted(root.glob("*.json")):
        if len(receipts) >= max_receipts:
            raise ValueError("runtime audit governed receipt read limit exceeded")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("runtime audit receipt file is invalid") from exc
        if not isinstance(payload, dict):
            raise ValueError("runtime audit receipt file must contain an object")
        if payload.get("receipt_type") == receipt_type:
            receipts.append(payload)
    return receipts


def _load_neon_receipts(receipt_type: str, max_receipts: int) -> list[dict]:
    try:
        import psycopg
    except Exception as exc:
        raise ValueError("Neon audit driver unavailable") from exc
    sql = """
        SELECT receipt_json
        FROM public.cew_human_receipt_audit
        WHERE receipt_json->>'receipt_type' = %s
        ORDER BY submitted_at ASC NULLS LAST, decision_id ASC
        LIMIT %s
    """
    try:
        with psycopg.connect(os.environ["CEW_AUDIT_NEON_DATABASE_URL"], connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (receipt_type, max_receipts + 1))
                rows = cur.fetchall()
    except Exception as exc:
        raise ValueError("Neon audit governed receipt read failed") from exc
    if len(rows) > max_receipts:
        raise ValueError("runtime audit governed receipt read limit exceeded")
    return [_receipt_json_object(row[0]) for row in rows]


def _load_supabase_receipts(receipt_type: str, max_receipts: int) -> list[dict]:
    base = os.environ["CEW_AUDIT_SUPABASE_URL"].rstrip("/")
    key = os.environ["CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY"]
    table = os.getenv("CEW_AUDIT_TABLE", "cew_human_receipt_audit")
    query = parse.urlencode(
        {
            "select": "receipt_json",
            "receipt_json->>receipt_type": f"eq.{receipt_type}",
            "order": "submitted_at.asc.nullslast,decision_id.asc",
            "limit": str(max_receipts + 1),
        }
    )
    req = request.Request(
        f"{base}/rest/v1/{table}?{query}",
        method="GET",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=12) as resp:
            if resp.status != 200:
                raise ValueError(f"unexpected Supabase audit read status: {resp.status}")
            rows = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise ValueError(f"Supabase audit governed receipt read failed: HTTP {exc.code}") from exc
    except (error.URLError, json.JSONDecodeError) as exc:
        raise ValueError("Supabase audit governed receipt read unavailable") from exc
    if not isinstance(rows, list):
        raise ValueError("Supabase audit governed receipt read must return a list")
    if len(rows) > max_receipts:
        raise ValueError("runtime audit governed receipt read limit exceeded")
    receipts: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or "receipt_json" not in row:
            raise ValueError("Supabase audit governed receipt row is invalid")
        receipts.append(_receipt_json_object(row["receipt_json"]))
    return receipts


def _load_https_receipts(receipt_type: str, max_receipts: int) -> list[dict]:
    endpoint = os.environ["CEW_AUDIT_HTTPS_URL"].strip()
    secret = os.environ["CEW_AUDIT_SHARED_SECRET"]
    separator = "&" if "?" in endpoint else "?"
    query = parse.urlencode({"receipt_type": receipt_type, "limit": str(max_receipts + 1)})
    req = request.Request(
        f"{endpoint}{separator}{query}",
        method="GET",
        headers={
            "Authorization": f"Bearer {secret}",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=12) as resp:
            if resp.status != 200:
                raise ValueError(f"unexpected Netlify audit read status: {resp.status}")
            payload = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise ValueError(f"Netlify audit governed receipt read failed: HTTP {exc.code}") from exc
    except (error.URLError, json.JSONDecodeError) as exc:
        raise ValueError("Netlify audit governed receipt read unavailable") from exc
    rows = payload.get("receipts") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("Netlify audit governed receipt read must return receipts")
    if len(rows) > max_receipts:
        raise ValueError("runtime audit governed receipt read limit exceeded")
    receipts: list[dict] = []
    for row in rows:
        if isinstance(row, dict) and "receipt_json" in row:
            row = row["receipt_json"]
        receipts.append(_receipt_json_object(row))
    return receipts


def load_runtime_receipts(receipt_type: str, store: Path, *, max_receipts: int = MAX_GOVERNED_READ_RECEIPTS) -> dict:
    """Read append-only runtime receipts for a governed downstream gate.

    This is deliberately read-only. It does not grant canonical-write, geometry,
    structural, promotion, or engineering authority. Every backend advertised as
    production-ready by app.py has an explicit governed read-back path here;
    transport/schema failures remain fail-closed.
    """
    if not isinstance(receipt_type, str) or not receipt_type.strip() or len(receipt_type) > 200:
        raise ValueError("runtime audit receipt_type is invalid")
    if not isinstance(max_receipts, int) or max_receipts < 1 or max_receipts > MAX_GOVERNED_READ_RECEIPTS:
        raise ValueError("runtime audit max_receipts is invalid")
    receipt_type = receipt_type.strip()
    backend = backend_status()
    if backend == "FILESYSTEM_APPEND_ONLY":
        receipts = _load_file_receipts(store, receipt_type, max_receipts)
    elif backend == "NEON_APPEND_ONLY":
        receipts = _load_neon_receipts(receipt_type, max_receipts)
    elif backend == "SUPABASE_APPEND_ONLY":
        receipts = _load_supabase_receipts(receipt_type, max_receipts)
    elif backend == "NETLIFY_AUDIT_HTTPS":
        receipts = _load_https_receipts(receipt_type, max_receipts)
    elif backend == "UNCONFIGURED_PRODUCTION":
        raise ValueError("production audit backend is not configured")
    else:
        raise ValueError(f"governed receipt read unsupported for audit backend: {backend}")
    return {
        "audit_backend": backend,
        "receipt_type": receipt_type,
        "receipt_count": len(receipts),
        "receipts": receipts,
        "authority": "RUNTIME_AUDIT_READ_ONLY",
        "canonical_write": False,
        "engineering_authority_effect": "NONE",
    }
