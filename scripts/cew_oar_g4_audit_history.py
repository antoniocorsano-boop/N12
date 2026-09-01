#!/usr/bin/env python3
"""Stable-snapshot governed audit-history reader for the G4/TAV-05S OAR pilot.

The append-only backend remains the complete audit authority. Filesystem freezes
an in-memory list, Neon uses one REPEATABLE READ transaction, and Supabase/
Netlify materialize the complete OAR receipt set in one server-side MVCC query.
The client may chunk that frozen result locally for reduction, but it never pages
across changing remote database states.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Iterator
from urllib import error, request

import cew_oar_g4_region_binding as binding
import cew_runtime_audit_store as audit_store

DEFAULT_PAGE_SIZE = 200
MAX_PAGE_SIZE = audit_store.MAX_GOVERNED_READ_RECEIPTS
SUPABASE_SNAPSHOT_RPC = "cew_oar_read_region_receipts_v1"


def _json_object(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("OAR_AUDIT_RECEIPT_JSON_INVALID") from exc
        if isinstance(value, dict):
            return value
    raise ValueError("OAR_AUDIT_RECEIPT_JSON_OBJECT_REQUIRED")


def _chunks(receipts: list[dict], page_size: int) -> Iterator[list[dict]]:
    for offset in range(0, len(receipts), page_size):
        yield receipts[offset : offset + page_size]


def _file_pages(store: Path, receipt_type: str, page_size: int) -> Iterator[list[dict]]:
    root = store.resolve()
    if not root.exists():
        return
    if not root.is_dir():
        raise ValueError("runtime audit store is not a directory")
    receipts: list[dict] = []
    for path in root.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("runtime audit receipt file is invalid") from exc
        if not isinstance(payload, dict):
            raise ValueError("runtime audit receipt file must contain an object")
        if payload.get("receipt_type") == receipt_type:
            receipts.append(payload)
    yield from _chunks(binding._ordered_receipts(receipts), page_size)


def _neon_pages(receipt_type: str, page_size: int) -> Iterator[list[dict]]:
    try:
        import psycopg
    except Exception as exc:
        raise ValueError("Neon audit driver unavailable") from exc
    try:
        with psycopg.connect(os.environ["CEW_AUDIT_NEON_DATABASE_URL"], connect_timeout=10) as conn:
            conn.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
            offset = 0
            while True:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT receipt_json
                        FROM public.cew_human_receipt_audit
                        WHERE receipt_json->>'receipt_type' = %s
                        ORDER BY submitted_at ASC NULLS LAST, decision_id ASC
                        LIMIT %s OFFSET %s
                        """,
                        (receipt_type, page_size, offset),
                    )
                    rows = cur.fetchall()
                page = [_json_object(row[0]) for row in rows]
                if page:
                    yield page
                if len(page) < page_size:
                    break
                offset += len(page)
            conn.rollback()
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("Neon OAR governed receipt read failed") from exc


def _supabase_snapshot(receipt_type: str) -> list[dict]:
    if receipt_type != binding.RECEIPT_TYPE:
        raise ValueError("OAR_SUPABASE_SNAPSHOT_RECEIPT_TYPE_INVALID")
    base = os.environ["CEW_AUDIT_SUPABASE_URL"].rstrip("/")
    key = os.environ["CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY"]
    req = request.Request(
        f"{base}/rest/v1/rpc/{SUPABASE_SNAPSHOT_RPC}",
        data=b"{}",
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                raise ValueError(f"unexpected Supabase OAR snapshot status: {resp.status}")
            rows = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise ValueError(f"Supabase OAR MVCC snapshot read failed: HTTP {exc.code}") from exc
    except (error.URLError, json.JSONDecodeError) as exc:
        raise ValueError("Supabase OAR MVCC snapshot read unavailable") from exc
    if not isinstance(rows, list):
        raise ValueError("Supabase OAR MVCC snapshot must return a list")
    receipts: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or "receipt_json" not in row:
            raise ValueError("Supabase OAR MVCC snapshot row is invalid")
        receipts.append(_json_object(row["receipt_json"]))
    return receipts


def _supabase_pages(receipt_type: str, page_size: int) -> Iterator[list[dict]]:
    # One RPC call = one PostgreSQL statement/MVCC snapshot. Local chunking does
    # not re-query the remote database and therefore cannot be shifted by a late commit.
    yield from _chunks(_supabase_snapshot(receipt_type), page_size)


def _https_snapshot(receipt_type: str) -> list[dict]:
    endpoint = os.environ["CEW_AUDIT_HTTPS_URL"].strip()
    secret = os.environ["CEW_AUDIT_SHARED_SECRET"]
    separator = "&" if "?" in endpoint else "?"
    req = request.Request(
        f"{endpoint}{separator}receipt_type={receipt_type}&snapshot=oar_mvcc",
        method="GET",
        headers={"Authorization": f"Bearer {secret}", "Accept": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                raise ValueError(f"unexpected Netlify OAR snapshot status: {resp.status}")
            payload = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        raise ValueError(f"Netlify OAR MVCC snapshot read failed: HTTP {exc.code}") from exc
    except (error.URLError, json.JSONDecodeError) as exc:
        raise ValueError("Netlify OAR MVCC snapshot read unavailable") from exc
    if not isinstance(payload, dict) or payload.get("snapshot") != "SERVER_MVCC_SINGLE_QUERY":
        raise ValueError("Netlify OAR MVCC snapshot contract missing")
    rows = payload.get("receipts")
    if not isinstance(rows, list):
        raise ValueError("Netlify OAR MVCC snapshot must return receipts")
    return [_json_object(row.get("receipt_json") if isinstance(row, dict) and "receipt_json" in row else row) for row in rows]


def _https_pages(receipt_type: str, page_size: int) -> Iterator[list[dict]]:
    # Netlify materializes the complete OAR set with one database SELECT and one
    # HTTP response; page_size applies only after that immutable response exists.
    yield from _chunks(_https_snapshot(receipt_type), page_size)


def _pages(receipt_type: str, store: Path, page_size: int) -> tuple[str, Iterable[list[dict]]]:
    backend = audit_store.backend_status()
    if backend == "FILESYSTEM_APPEND_ONLY":
        return backend, _file_pages(store, receipt_type, page_size)
    if backend == "NEON_APPEND_ONLY":
        return backend, _neon_pages(receipt_type, page_size)
    if backend == "SUPABASE_APPEND_ONLY":
        return backend, _supabase_pages(receipt_type, page_size)
    if backend == "NETLIFY_AUDIT_HTTPS":
        return backend, _https_pages(receipt_type, page_size)
    if backend == "UNCONFIGURED_PRODUCTION":
        raise ValueError("production audit backend is not configured")
    raise ValueError(f"unsupported OAR audit backend: {backend}")


def _anchor_closed_compact(receipts: list[dict], contract: dict, *, report: dict | None = None) -> list[dict]:
    report = report or binding.aggregate(receipts, contract)
    by_decision = {str(row.get("decision_id", "")): row for row in receipts}
    keep: set[str] = set()
    pending: list[str] = []
    for obj in report["objects"]:
        for key in ("geometry_proposal_receipt_id", "geometry_confirmation_receipt_id"):
            decision_id = obj.get(key)
            if decision_id:
                pending.append(str(decision_id))
    while pending:
        decision_id = pending.pop()
        if decision_id in keep:
            continue
        receipt = by_decision.get(decision_id)
        if receipt is None:
            raise ValueError("OAR_REGION_COMPACT_ACTIVE_RECEIPT_NOT_FOUND")
        keep.add(decision_id)
        anchor = receipt.get("base_proposal_decision_id")
        if anchor is not None:
            anchor_id = str(anchor)
            if anchor_id.startswith(binding.UNBOUND_REVISION_PREFIX):
                expected = binding.unbound_revision_anchor(str(receipt.get("support_id", "")))
                if anchor_id != expected:
                    raise ValueError("OAR_REGION_UNBOUND_REVISION_ANCHOR_MISMATCH")
                continue
            if anchor_id not in by_decision:
                raise ValueError("OAR_REGION_BASE_PROPOSAL_NOT_FOUND")
            pending.append(anchor_id)
    compact = [row for row in receipts if str(row.get("decision_id", "")) in keep]
    compact = binding._ordered_receipts(compact)
    binding.aggregate(compact, contract)
    return compact


def _reduce_history(pages: Iterable[list[dict]], contract: dict | None = None) -> tuple[list[dict], int]:
    contract = contract or binding.load_contract()
    receipts: list[dict] = []
    seen_decisions: set[str] = set()
    for page in pages:
        for receipt in page:
            decision_id = str(receipt.get("decision_id", ""))
            if not decision_id or decision_id in seen_decisions:
                raise ValueError("OAR_REGION_DUPLICATE_DECISION_ID")
            seen_decisions.add(decision_id)
            receipts.append(receipt)
    report = binding.aggregate(receipts, contract)
    compact = _anchor_closed_compact(receipts, contract, report=report)
    return compact, len(receipts)


def load_runtime_receipts(receipt_type: str, store: Path, *, max_receipts: int = MAX_PAGE_SIZE) -> dict:
    if receipt_type != binding.RECEIPT_TYPE:
        return audit_store.load_runtime_receipts(receipt_type, store, max_receipts=max_receipts)
    if not isinstance(max_receipts, int) or max_receipts < 1 or max_receipts > MAX_PAGE_SIZE:
        raise ValueError("runtime audit max_receipts is invalid")
    backend, pages = _pages(receipt_type, store, max_receipts)
    receipts, total = _reduce_history(pages)
    return {
        "audit_backend": backend,
        "receipt_type": receipt_type,
        "receipt_count": total,
        "reduced_receipt_count": len(receipts),
        "receipts": receipts,
        "history_policy": "SERVER_MVCC_SNAPSHOT_APPEND_ONLY_ANCHOR_CLOSED_SINGLE_PASS_REDUCED_FOR_STATE_RECONSTRUCTION",
        "authority": "RUNTIME_AUDIT_READ_ONLY",
        "canonical_write": False,
        "engineering_authority_effect": "NONE",
    }
