#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import cew_precision_gcp_audit as precision
import cew_runtime_audit_store as audit_store

GCP_RUNTIME_STORE = Path("/tmp/cew-runtime/precision-gcp-receipts")


def _error(state: str, reason: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        {
            "state": state,
            "reason": reason,
            "canonical_write_authorized": False,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def _task_context(source_workspace, task: str) -> tuple[dict[str, Any], dict[str, str]]:
    task = task.strip()
    if not task:
        raise ValueError("PRECISION_GCP_TASK_REQUIRED")
    ctx = source_workspace.task_context(task)
    return ctx, precision.source_evidence_from_context(ctx)


def _load_task_receipts(task: str):
    loaded = audit_store.load_runtime_receipts(precision.RECEIPT_TYPE, GCP_RUNTIME_STORE)
    receipts = [r for r in loaded["receipts"] if r.get("task_id") == task]
    return loaded, receipts


def _same_semantic_decision(existing: dict[str, Any], candidate: dict[str, Any]) -> bool:
    fields = ("decision_id", "task_id", "revision", "reviewer", "payload_fingerprint")
    return all(existing.get(field) == candidate.get(field) for field in fields)


def build_router(source_workspace) -> APIRouter:
    router = APIRouter()

    @router.get("/api/workbench/precision/gcp")
    def gcp_list(task: str = ""):
        try:
            _, expected_source = _task_context(source_workspace, task)
            loaded, receipts = _load_task_receipts(task.strip())
        except KeyError:
            return _error("PRECISION_GCP_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            return _error("PRECISION_GCP_UNAVAILABLE", str(exc), 503)

        rows = []
        for row in receipts:
            source = row.get("source_evidence") or {}
            if any(str(source.get(f, "")).strip().lower() != expected_source[f].lower() for f in precision.SOURCE_FIELDS):
                return _error("PRECISION_GCP_BLOCKED", "STALE_SOURCE_RECEIPT_PRESENT", 409)
            rows.append({
                "decision_id": row["decision_id"],
                "receipt_fingerprint": row["receipt_fingerprint"],
                "revision": row["revision"],
                "reviewer": row["reviewer"],
                "timestamp": row["timestamp"],
                "payload": row["payload"],
            })
        return JSONResponse(
            {
                "state": "PRECISION_GCP_AUDIT_READY",
                "audit_backend": loaded["audit_backend"],
                "receipt_type": precision.RECEIPT_TYPE,
                "task": task.strip(),
                "source_evidence": expected_source,
                "gcp_count": len(rows),
                "gcps": rows,
                "locator_promotion_authorized": False,
                "canonical_write_authorized": False,
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
            },
            headers={"Cache-Control": "no-store"},
        )

    @router.post("/api/workbench/precision/gcp")
    async def gcp_capture(request: Request):
        try:
            wrapper = await request.json()
        except Exception:
            return _error("PRECISION_GCP_REJECTED", "INVALID_JSON", 400)
        if not isinstance(wrapper, dict):
            return _error("PRECISION_GCP_REJECTED", "JSON_OBJECT_REQUIRED", 400)
        allowed = {"task", "revision", "reviewer", "payload"}
        if set(wrapper) - allowed:
            return _error("PRECISION_GCP_REJECTED", "WRAPPER_FIELD_SET_MISMATCH", 400)
        try:
            task = str(wrapper.get("task", "")).strip()
            revision = str(wrapper.get("revision", "")).strip()
            reviewer = str(wrapper.get("reviewer", "")).strip()
            payload = wrapper.get("payload")
            _, expected_source = _task_context(source_workspace, task)
            loaded, receipts = _load_task_receipts(task)
            receipt = precision.build_receipt(
                task_id=task,
                revision=revision,
                reviewer=reviewer,
                payload=payload,
                expected_source=expected_source,
            )
            existing = precision.index_receipts(receipts, task).get(receipt["decision_id"])
            if existing is not None:
                if not _same_semantic_decision(existing, receipt):
                    raise ValueError("PRECISION_GCP_DECISION_ID_COLLISION")
                return JSONResponse(
                    {
                        "state": "PRECISION_GCP_ALREADY_PERSISTED",
                        "idempotent_replay": True,
                        "runtime_receipt_id": existing["decision_id"],
                        "receipt_fingerprint": existing["receipt_fingerprint"],
                        "payload": existing["payload"],
                        "audit_backend": loaded["audit_backend"],
                        "locator_promotion_authorized": False,
                        "canonical_write_authorized": False,
                    },
                    status_code=200,
                    headers={"Cache-Control": "no-store"},
                )
            persisted = audit_store.persist_runtime_receipt(receipt, GCP_RUNTIME_STORE)
        except KeyError:
            return _error("PRECISION_GCP_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            reason = str(exc)
            status = 409 if "COLLISION" in reason or "MISMATCH" in reason else 422
            return _error("PRECISION_GCP_REJECTED", reason, status)

        return JSONResponse(
            {
                "state": "PRECISION_GCP_PERSISTED_APPEND_ONLY",
                "runtime_receipt_id": persisted["runtime_receipt_id"],
                "sha256": persisted["sha256"],
                "audit_backend": persisted["audit_backend"],
                "receipt_fingerprint": receipt["receipt_fingerprint"],
                "payload": receipt["payload"],
                "locator_promotion_authorized": False,
                "canonical_write_authorized": False,
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "next_gate": "PR3_RESIDUAL_FIELD_ANALYSIS",
            },
            status_code=201,
            headers={"Cache-Control": "no-store"},
        )

    return router
