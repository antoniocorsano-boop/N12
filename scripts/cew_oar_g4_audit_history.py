#!/usr/bin/env python3
"""Paginated, governed audit-history reader for the G4/TAV-05S OAR pilot.

The append-only backend remains the complete audit authority. This reader pages
through that history and reduces it to the minimal receipt sequence required to
reconstruct the current OAR localization state. Every receipt is still checked
against the domain aggregate while streaming; invalid or authority-divergent
history remains fail-closed instead of being hidden by compaction.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Iterator
from urllib import error, parse, request

import cew_oar_g4_region_binding as binding
import cew_runtime_audit_store as audit_store

DEFAULT_PAGE_SIZE = 200
MAX_PAGE_SIZE = audit_store.MAX_GOVERNED_READ_RECEIPTS


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
    ordered = binding._ordered_receipts(receipts)
    for offset in range(0, len(ordered), page_size):
        yield ordered[offset : offset + page_size]


def _neon_pages(receipt_type: str, page_size: int) -> Iterator[list[dict]]:
    try:
        import psycopg
    except Exception as exc:
        raise ValueError("Neon audit driver unavailable") from exc
    sql = """
        SELECT receipt_json
        FROM public.cew_human_receipt_audit
        WHERE receipt_json->>'receipt_type' = %s
        ORDER BY submitted_at ASC NULLS LAST, decision_id ASC
        LIMIT %s OFFSET %s
    """
    offset = 0
    while True:
        try:
            with psycopg.connect(os.environ["CEW_AUDIT_NEON_DATABASE_URL"], connect_timeout=10) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (receipt_type, page_size, offset))
                    rows = cur.fetchall()
        except Exception as exc:
            raise ValueError("Neon OAR governed receipt read failed") from exc
        page = [_json_object(row[0]) for row in rows]
        if page:
            yield page
        if len(page) < page_size:
            break
        offset += len(page)


def _supabase_pages(receipt_type: str, page_size: int) -> Iterator[list[dict]]:
    base = os.environ["CEW_AUDIT_SUPABASE_URL"].rstrip("/")
    key = os.environ["CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY"]
    table = os.getenv("CEW_AUDIT_TABLE", "cew_human_receipt_audit")
    offset = 0
    while True:
        query = parse.urlencode(
            {
                "select": "receipt_json",
                "receipt_json->>receipt_type": f"eq.{receipt_type}",
                "order": "submitted_at.asc.nullslast,decision_id.asc",
                "limit": str(page_size),
                "offset": str(offset),
            }
        )
        req = request.Request(
            f"{base}/rest/v1/{table}?{query}",
            method="GET",
            headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=12) as resp:
                if resp.status != 200:
                    raise ValueError(f"unexpected Supabase OAR audit read status: {resp.status}")
                rows = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise ValueError(f"Supabase OAR governed receipt read failed: HTTP {exc.code}") from exc
        except (error.URLError, json.JSONDecodeError) as exc:
            raise ValueError("Supabase OAR governed receipt read unavailable") from exc
        if not isinstance(rows, list):
            raise ValueError("Supabase OAR governed receipt read must return a list")
        page = []
        for row in rows:
            if not isinstance(row, dict) or "receipt_json" not in row:
                raise ValueError("Supabase OAR governed receipt row is invalid")
            page.append(_json_object(row["receipt_json"]))
        if page:
            yield page
        if len(page) < page_size:
            break
        offset += len(page)


def _https_pages(receipt_type: str, page_size: int) -> Iterator[list[dict]]:
    endpoint = os.environ["CEW_AUDIT_HTTPS_URL"].strip()
    secret = os.environ["CEW_AUDIT_SHARED_SECRET"]
    offset = 0
    while True:
        separator = "&" if "?" in endpoint else "?"
        query = parse.urlencode({"receipt_type": receipt_type, "limit": str(page_size), "offset": str(offset)})
        req = request.Request(
            f"{endpoint}{separator}{query}",
            method="GET",
            headers={"Authorization": f"Bearer {secret}", "Accept": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=12) as resp:
                if resp.status != 200:
                    raise ValueError(f"unexpected Netlify OAR audit read status: {resp.status}")
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise ValueError(f"Netlify OAR governed receipt read failed: HTTP {exc.code}") from exc
        except (error.URLError, json.JSONDecodeError) as exc:
            raise ValueError("Netlify OAR governed receipt read unavailable") from exc
        rows = payload.get("receipts") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("Netlify OAR governed receipt read must return receipts")
        page = []
        for row in rows:
            if isinstance(row, dict) and "receipt_json" in row:
                row = row["receipt_json"]
            page.append(_json_object(row))
        if page:
            yield page
        if len(page) < page_size:
            break
        offset += len(page)


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


def _reduce_history(pages: Iterable[list[dict]], contract: dict | None = None) -> tuple[list[dict], int]:
    contract = contract or binding.load_contract()
    compact: list[dict] = []
    seen_decisions: set[str] = set()
    total = 0

    for page in pages:
        for receipt in page:
            total += 1
            decision_id = str(receipt.get("decision_id", ""))
            if not decision_id or decision_id in seen_decisions:
                raise ValueError("OAR_REGION_DUPLICATE_DECISION_ID")
            seen_decisions.add(decision_id)

            # Validate every historical receipt before reducing it. The domain
            # aggregate is the single authority for equivalence and fail-closed
            # state transitions.
            binding.aggregate([*compact, receipt], contract)

            support_id = str(receipt.get("support_id", ""))
            action = receipt.get("action")
            if action == binding.PROPOSAL_ACTION:
                compact = [
                    row
                    for row in compact
                    if not (str(row.get("support_id", "")) == support_id and row.get("action") == binding.PROPOSAL_ACTION)
                ]
                compact.append(receipt)
            elif action == binding.CONFIRM_ACTION:
                existing = next(
                    (
                        row
                        for row in compact
                        if str(row.get("support_id", "")) == support_id and row.get("action") == binding.CONFIRM_ACTION
                    ),
                    None,
                )
                if existing is None:
                    compact.append(receipt)
                else:
                    # The aggregate call above already proved this replay is
                    # equivalent under the full governed domain predicate.
                    continue
            else:
                raise ValueError("OAR_REGION_ACTION_INVALID")

    binding.aggregate(compact, contract)
    return compact, total


def load_runtime_receipts(
    receipt_type: str,
    store: Path,
    *,
    max_receipts: int = MAX_PAGE_SIZE,
) -> dict:
    """Paginate and reduce OAR audit history without truncating the backend."""
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
        "history_policy": "PAGINATED_APPEND_ONLY_REDUCED_FOR_STATE_RECONSTRUCTION",
        "authority": "RUNTIME_AUDIT_READ_ONLY",
        "canonical_write": False,
        "engineering_authority_effect": "NONE",
    }
