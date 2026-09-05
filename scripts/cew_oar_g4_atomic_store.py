#!/usr/bin/env python3
"""Arena-style atomic persistence boundary for OAR G4 geometry receipts.

A receipt is admitted to the governed append-only log only if its
``base_proposal_decision_id`` still matches the current support revision inside
the persistence critical section. The commit timestamp is assigned inside that
critical section; worker-created timestamps never define transition order.

For Neon, the append-only receipt history itself is the revision source of truth.
A per-support PostgreSQL advisory transaction lock serializes competing writes,
then the current revision is derived from the history inside the same transaction.
No runtime DDL or mutable revision-head table is required.

This module does not grant canonical, structural, classification or engineering
authority. It only serializes the runtime-audit revision transition.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Iterator
from urllib import error, request

import cew_oar_g4_region_binding as binding
import cew_runtime_audit_store as audit_store

ATOMIC_RPC = "cew_oar_append_region_receipt_v1"


def _raw(receipt: dict) -> str:
    return json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _commit_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _committed(receipt: dict) -> dict:
    value = dict(receipt)
    value["timestamp"] = _commit_timestamp()
    return value


def _expected_anchor(receipt: dict) -> str:
    anchor = receipt.get("base_proposal_decision_id")
    if not isinstance(anchor, str) or not anchor.strip():
        raise ValueError("OAR_REGION_ATOMIC_BASE_REVISION_REQUIRED")
    return anchor.strip()


def _current_row(report: dict, support_id: str) -> dict:
    row = next((item for item in report["objects"] if str(item["support_id"]) == str(support_id)), None)
    if row is None:
        raise ValueError("OAR_REGION_SUPPORT_NOT_IN_PILOT")
    return row


def _assert_current_revision(receipt: dict, existing: list[dict]) -> None:
    """CAS guard evaluated while the persistence lock is held."""
    report = binding.aggregate(existing)
    row = _current_row(report, str(receipt["support_id"]))
    expected = _expected_anchor(receipt)
    action = receipt.get("action")

    if action == binding.PROPOSAL_ACTION:
        if row["state"] == "UNBOUND":
            current = binding.unbound_revision_anchor(str(receipt["support_id"]))
        elif row["state"] == "PROPOSED":
            current = row.get("geometry_proposal_receipt_id")
        else:
            raise ValueError("OAR_REGION_GEOMETRY_ALREADY_CONFIRMED")
    elif action == binding.CONFIRM_ACTION:
        if row["state"] != "PROPOSED":
            raise ValueError("OAR_REGION_CONFIRMATION_REQUIRES_CURRENT_PROPOSAL")
        current = row.get("geometry_proposal_receipt_id")
    else:
        raise ValueError("OAR_REGION_ACTION_INVALID")

    if not current or expected != current:
        raise ValueError("OAR_REGION_REVISION_CONFLICT")


@contextmanager
def _file_lock(store: Path) -> Iterator[None]:
    store.mkdir(parents=True, exist_ok=True)
    lock_path = store / ".oar-g4-revision.lock"
    handle = lock_path.open("a+b")
    try:
        try:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except ImportError:
            raise ValueError("OAR_REGION_ATOMIC_FILE_LOCK_UNAVAILABLE")
    finally:
        handle.close()


def _file_receipts(store: Path) -> list[dict]:
    receipts: list[dict] = []
    if not store.exists():
        return receipts
    for path in store.glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("receipt_type") == binding.RECEIPT_TYPE:
            receipts.append(payload)
    return receipts


def _persist_file_atomic(receipt: dict, store: Path) -> dict:
    with _file_lock(store):
        existing = _file_receipts(store)
        _assert_current_revision(receipt, existing)
        committed = _committed(receipt)
        binding.aggregate([*existing, committed])
        persisted = audit_store.persist_runtime_receipt(committed, store)
    return {**persisted, "committed_receipt": committed, "atomic_revision": True}


def _persist_neon_atomic(receipt: dict) -> dict:
    """Append atomically to Neon without runtime schema mutation.

    The advisory xact lock is scoped to binding+support, so concurrent transitions
    for the same support are serialized. Once locked, the current revision is
    reconstructed from the append-only audit history and checked against the
    receipt anchor before insertion. This keeps the history as the sole durable
    state and avoids CREATE/UPDATE DDL-DML on a secondary head table.
    """
    try:
        import psycopg
        from psycopg.errors import UniqueViolation
    except Exception as exc:
        raise ValueError("OAR_REGION_NEON_DRIVER_UNAVAILABLE") from exc

    support_id = str(receipt["support_id"])
    binding_id = str(receipt["binding_id"])
    decision_id = str(receipt["decision_id"])
    _expected_anchor(receipt)

    try:
        with psycopg.connect(os.environ["CEW_AUDIT_NEON_DATABASE_URL"], connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                    (f"{binding_id}:{support_id}",),
                )
                cur.execute(
                    "SELECT receipt_json FROM public.cew_human_receipt_audit "
                    "WHERE receipt_json->>'receipt_type'=%s "
                    "AND receipt_json->>'support_id'=%s "
                    "ORDER BY submitted_at ASC NULLS LAST, decision_id ASC",
                    (binding.RECEIPT_TYPE, support_id),
                )
                existing = [row[0] if isinstance(row[0], dict) else json.loads(row[0]) for row in cur.fetchall()]

                _assert_current_revision(receipt, existing)
                committed = _committed(receipt)
                binding.aggregate([*existing, committed])
                digest = hashlib.sha256(_raw(committed).encode("utf-8")).hexdigest()
                cur.execute(
                    """
                    INSERT INTO public.cew_human_receipt_audit
                      (decision_id, task_id, residual_id, receipt_sha256, receipt_json,
                       authority, canonical_write, submitted_at)
                    VALUES (%s,%s,%s,%s,%s::jsonb,'RUNTIME_AUDIT_ONLY',false,%s::timestamptz)
                    """,
                    (
                        decision_id,
                        committed.get("task_id"),
                        committed.get("residual_id"),
                        digest,
                        json.dumps(committed, ensure_ascii=False, separators=(",", ":")),
                        committed["timestamp"],
                    ),
                )
            conn.commit()
    except UniqueViolation as exc:
        raise ValueError("OAR_REGION_DUPLICATE_DECISION_ID") from exc
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("OAR_REGION_NEON_ATOMIC_PERSISTENCE_FAILED") from exc

    return {
        "runtime_receipt_id": decision_id,
        "sha256": digest,
        "authority": "RUNTIME_AUDIT_ONLY",
        "audit_backend": "NEON_APPEND_ONLY",
        "canonical_write": False,
        "committed_receipt": committed,
        "atomic_revision": True,
    }


def _persist_supabase_atomic(receipt: dict) -> dict:
    base = os.environ["CEW_AUDIT_SUPABASE_URL"].rstrip("/")
    key = os.environ["CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY"]
    req = request.Request(
        f"{base}/rest/v1/rpc/{ATOMIC_RPC}",
        data=json.dumps({"p_receipt": receipt}, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if "OAR_REGION_REVISION_CONFLICT" in body:
            raise ValueError("OAR_REGION_REVISION_CONFLICT") from exc
        raise ValueError("OAR_REGION_SUPABASE_ATOMIC_PERSISTENCE_FAILED") from exc
    except (error.URLError, json.JSONDecodeError) as exc:
        raise ValueError("OAR_REGION_SUPABASE_ATOMIC_PERSISTENCE_UNAVAILABLE") from exc
    row = payload[0] if isinstance(payload, list) and payload else payload
    if not isinstance(row, dict) or not isinstance(row.get("receipt_json"), dict):
        raise ValueError("OAR_REGION_SUPABASE_ATOMIC_RESPONSE_INVALID")
    return {
        "runtime_receipt_id": str(row["receipt_json"]["decision_id"]),
        "sha256": str(row["receipt_sha256"]),
        "authority": "RUNTIME_AUDIT_ONLY",
        "audit_backend": "SUPABASE_APPEND_ONLY",
        "canonical_write": False,
        "committed_receipt": row["receipt_json"],
        "atomic_revision": True,
    }


def _persist_https_atomic(receipt: dict) -> dict:
    endpoint = os.environ["CEW_AUDIT_HTTPS_URL"].strip()
    secret = os.environ["CEW_AUDIT_SHARED_SECRET"]
    req = request.Request(
        endpoint,
        data=json.dumps({"oar_atomic_transition": True, "receipt_json": receipt}, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 409 and "OAR_REGION_REVISION_CONFLICT" in body:
            raise ValueError("OAR_REGION_REVISION_CONFLICT") from exc
        raise ValueError("OAR_REGION_NETLIFY_ATOMIC_PERSISTENCE_FAILED") from exc
    except (error.URLError, json.JSONDecodeError) as exc:
        raise ValueError("OAR_REGION_NETLIFY_ATOMIC_PERSISTENCE_UNAVAILABLE") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("receipt_json"), dict):
        raise ValueError("OAR_REGION_NETLIFY_ATOMIC_RESPONSE_INVALID")
    return {
        "runtime_receipt_id": str(payload["receipt_json"]["decision_id"]),
        "sha256": str(payload["sha256"]),
        "authority": "RUNTIME_AUDIT_ONLY",
        "audit_backend": "NETLIFY_AUDIT_HTTPS",
        "canonical_write": False,
        "committed_receipt": payload["receipt_json"],
        "atomic_revision": True,
    }


def persist_region_receipt(receipt: dict, store: Path) -> dict:
    if receipt.get("receipt_type") != binding.RECEIPT_TYPE:
        raise ValueError("OAR_REGION_ATOMIC_RECEIPT_TYPE_REQUIRED")
    _expected_anchor(receipt)
    backend = audit_store.backend_status()
    if backend == "NEON_APPEND_ONLY":
        return _persist_neon_atomic(receipt)
    if backend == "SUPABASE_APPEND_ONLY":
        return _persist_supabase_atomic(receipt)
    if backend == "NETLIFY_AUDIT_HTTPS":
        return _persist_https_atomic(receipt)
    if backend == "UNCONFIGURED_PRODUCTION":
        raise ValueError("OAR_REGION_AUDIT_BACKEND_UNCONFIGURED")
    return _persist_file_atomic(receipt, store)
