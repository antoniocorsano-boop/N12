#!/usr/bin/env python3
"""Atomic/idempotent hardening for the external-reference review workspace.

The review receipt log is append-only. This layer addresses two distinct cases:

1. future concurrent taps/POSTs are serialized per review item on Neon with a
   PostgreSQL advisory transaction lock, so only one terminal transition can be
   appended;
2. a legacy race that already appended two materially identical terminal
   receipts is reconciled as a redundant replay while retaining both audit rows.

A materially different receipt after a terminal decision remains fail-closed.
No library, CAD, structural, semantic-project, or engineering authority is
created here.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator

_EFFECT_FIELDS = (
    "review_item_id",
    "state",
    "source_id",
    "source_sha256",
    "page_index",
    "page_text_sha256",
    "page_feature_sha256",
    "meaning",
    "scope",
    "primitive_families",
    "aspect_buckets",
    "area_buckets",
    "filled",
    "counterexample_refs",
    "reviewer",
    "rationale",
)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _receipt_sha(receipt: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()


def _effect(receipt: dict[str, Any]) -> dict[str, Any]:
    return {field: receipt.get(field) for field in _EFFECT_FIELDS}


def _same_effect(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return _canonical(_effect(left)) == _canonical(_effect(right))


def _validated_history_from_rows(review, rows: list[dict[str, Any]]):
    acquisition, queue = review._governed()
    queued = review._queue_index(queue)
    raw = list(rows)
    raw.sort(key=review._decision_order_key)
    seen_decision_ids: set[str] = set()
    by_item: dict[str, list[dict[str, Any]]] = {}

    for row in raw:
        decision_id = review._require_text(row.get("decision_id"), "decision_id")
        item_id = review._require_text(row.get("review_item_id"), "review_item_id")
        if decision_id in seen_decision_ids:
            raise ValueError("REFERENCE_REVIEW_DECISION_ID_DUPLICATE")
        seen_decision_ids.add(decision_id)
        item = queued.get(item_id)
        if item is None:
            raise ValueError("REFERENCE_REVIEW_RUNTIME_ITEM_UNKNOWN")
        state = str(row.get("state") or "")
        if state not in review.ALLOWED_REVIEW_STATES:
            raise ValueError("REFERENCE_REVIEW_DECISION_STATE_INVALID")
        for field in ("source_id", "source_sha256", "page_index", "page_text_sha256", "page_feature_sha256"):
            expected: Any = item[field]
            actual: Any = row.get(field)
            if field == "page_index":
                actual = int(actual)
                expected = int(expected)
            if actual != expected:
                raise ValueError(f"REFERENCE_REVIEW_RUNTIME_{field.upper()}_MISMATCH")
        if row.get("authority", {}).get("project_semantic_authority") != "NONE":
            raise ValueError("REFERENCE_REVIEW_RUNTIME_AUTHORITY_DRIFT")
        review._decision_order_key(row)
        by_item.setdefault(item_id, []).append(row)

    active_by_item: dict[str, dict[str, Any]] = {}
    terminal_by_item: dict[str, dict[str, Any]] = {}
    history: list[dict[str, Any]] = []
    for item_id in sorted(by_item):
        terminal_row: dict[str, Any] | None = None
        for row in sorted(by_item[item_id], key=review._decision_order_key):
            state = str(row["state"])
            if terminal_row is not None:
                # Preserve the audit row but reconcile only an equivalent replay.
                # Any conflicting post-terminal effect remains a hard failure.
                if not _same_effect(terminal_row, row):
                    raise ValueError("REFERENCE_REVIEW_DECISION_AFTER_TERMINAL")
                history.append(row)
                continue
            history.append(row)
            active_by_item[item_id] = row
            if state in review.TERMINAL_REVIEW_STATES:
                terminal_row = row
                terminal_by_item[item_id] = row

    history.sort(key=review._decision_order_key)
    return acquisition, queue, history, active_by_item, terminal_by_item


def _validated_runtime_history(review):
    governed = review.audit_store.load_runtime_receipts(review.RECEIPT_TYPE, review.REVIEW_STORE)
    return _validated_history_from_rows(review, list(governed["receipts"]))


def _idempotent_result(review, receipt: dict[str, Any], existing: dict[str, Any], backend: str) -> dict[str, Any]:
    return {
        "state": "REFERENCE_REVIEW_DECISION_PERSISTED",
        "review_item_id": str(existing["review_item_id"]),
        "decision_state": str(existing["state"]),
        "terminal_decision": str(existing["state"]) in review.TERMINAL_REVIEW_STATES,
        "runtime_receipt_id": str(existing["decision_id"]),
        "sha256": _receipt_sha(existing),
        "audit_backend": backend,
        "idempotent_replay": True,
        "repository_library_index_written": False,
        "authority": dict(review.AUTHORITY),
    }


def _transition_guard(review, receipt: dict[str, Any], rows: list[dict[str, Any]]):
    _acquisition, _queue, _history, active, terminal = _validated_history_from_rows(review, rows)
    item_id = str(receipt["review_item_id"])
    existing_terminal = terminal.get(item_id)
    if existing_terminal is not None:
        if _same_effect(existing_terminal, receipt):
            return existing_terminal
        raise ValueError("REFERENCE_REVIEW_ITEM_ALREADY_TERMINAL")
    current = active.get(item_id)
    if current is not None and str(current.get("state")) == "DEFER" and str(receipt.get("state")) == "DEFER":
        if _same_effect(current, receipt):
            return current
        raise ValueError("REFERENCE_REVIEW_ITEM_ALREADY_DEFERRED")
    return None


@contextmanager
def _file_lock(store: Path) -> Iterator[None]:
    store.mkdir(parents=True, exist_ok=True)
    handle = (store / ".reference-review.lock").open("a+b")
    try:
        try:
            import fcntl
        except ImportError as exc:
            raise ValueError("REFERENCE_REVIEW_ATOMIC_FILE_LOCK_UNAVAILABLE") from exc
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def _persist_file_atomic(review, receipt: dict[str, Any]) -> dict[str, Any]:
    with _file_lock(review.REVIEW_STORE):
        governed = review.audit_store.load_runtime_receipts(review.RECEIPT_TYPE, review.REVIEW_STORE)
        existing = list(governed["receipts"])
        replay = _transition_guard(review, receipt, existing)
        if replay is not None:
            return _idempotent_result(review, receipt, replay, "FILESYSTEM_APPEND_ONLY")
        persisted = review.audit_store.persist_runtime_receipt(receipt, review.REVIEW_STORE)
    return {
        "state": "REFERENCE_REVIEW_DECISION_PERSISTED",
        "review_item_id": str(receipt["review_item_id"]),
        "decision_state": str(receipt["state"]),
        "terminal_decision": bool(receipt["terminal_decision"]),
        "runtime_receipt_id": persisted["runtime_receipt_id"],
        "sha256": persisted["sha256"],
        "audit_backend": persisted["audit_backend"],
        "idempotent_replay": False,
        "repository_library_index_written": False,
        "authority": dict(review.AUTHORITY),
    }


def _persist_neon_atomic(review, receipt: dict[str, Any]) -> dict[str, Any]:
    try:
        import psycopg
        from psycopg.errors import UniqueViolation
    except Exception as exc:
        raise ValueError("REFERENCE_REVIEW_NEON_DRIVER_UNAVAILABLE") from exc

    item_id = str(receipt["review_item_id"])
    decision_id = str(receipt["decision_id"])
    digest = _receipt_sha(receipt)
    try:
        with psycopg.connect(os.environ["CEW_AUDIT_NEON_DATABASE_URL"], connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                    (f"{review.RECEIPT_TYPE}:{item_id}",),
                )
                cur.execute(
                    "SELECT receipt_json FROM public.cew_human_receipt_audit "
                    "WHERE receipt_json->>'receipt_type'=%s "
                    "ORDER BY submitted_at ASC NULLS LAST, decision_id ASC",
                    (review.RECEIPT_TYPE,),
                )
                rows = [row[0] if isinstance(row[0], dict) else json.loads(row[0]) for row in cur.fetchall()]
                replay = _transition_guard(review, receipt, rows)
                if replay is not None:
                    conn.rollback()
                    return _idempotent_result(review, receipt, replay, "NEON_APPEND_ONLY")
                cur.execute(
                    """
                    INSERT INTO public.cew_human_receipt_audit
                      (decision_id, task_id, residual_id, receipt_sha256, receipt_json,
                       authority, canonical_write, submitted_at)
                    VALUES (%s,%s,%s,%s,%s::jsonb,'RUNTIME_AUDIT_ONLY',false,%s::timestamptz)
                    """,
                    (
                        decision_id,
                        receipt.get("task_id"),
                        receipt.get("residual_id"),
                        digest,
                        json.dumps(receipt, ensure_ascii=False, separators=(",", ":")),
                        receipt["timestamp"],
                    ),
                )
            conn.commit()
    except UniqueViolation as exc:
        raise ValueError("REFERENCE_REVIEW_DECISION_ID_DUPLICATE") from exc
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("REFERENCE_REVIEW_NEON_ATOMIC_PERSISTENCE_FAILED") from exc

    return {
        "state": "REFERENCE_REVIEW_DECISION_PERSISTED",
        "review_item_id": item_id,
        "decision_state": str(receipt["state"]),
        "terminal_decision": bool(receipt["terminal_decision"]),
        "runtime_receipt_id": decision_id,
        "sha256": digest,
        "audit_backend": "NEON_APPEND_ONLY",
        "idempotent_replay": False,
        "repository_library_index_written": False,
        "authority": dict(review.AUTHORITY),
    }


def persist_review_receipt(review, payload: dict[str, Any]) -> dict[str, Any]:
    receipt = review.build_review_receipt(payload)
    backend = review.audit_store.backend_status()
    if backend == "NEON_APPEND_ONLY":
        return _persist_neon_atomic(review, receipt)
    if backend == "FILESYSTEM_APPEND_ONLY":
        return _persist_file_atomic(review, receipt)
    if backend == "UNCONFIGURED_PRODUCTION":
        raise ValueError("REFERENCE_REVIEW_AUDIT_BACKEND_UNCONFIGURED")
    # This human decision route requires a backend with an atomic per-item
    # transition primitive. Do not silently regress to check-then-insert.
    raise ValueError("REFERENCE_REVIEW_ATOMIC_BACKEND_UNSUPPORTED")


def install(review):
    """Install hardened read/write boundaries into the existing review module."""
    review._validated_runtime_history = lambda: _validated_runtime_history(review)
    review.persist_review_receipt = lambda payload: persist_review_receipt(review, payload)
    return review
