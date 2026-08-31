#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import cew_oa_governed_audit as governed
import cew_runtime_audit_store as audit_store

OA_RUNTIME_STORE = Path("/tmp/cew-runtime/oa-governed-receipts")


def _error(state: str, reason: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        {
            "state": state,
            "reason": reason,
            "canonical_write_authorized": False,
            "project_material_ready": False,
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def _task_context(source_workspace, task: str) -> tuple[dict[str, Any], dict[str, str]]:
    task = task.strip()
    if not task:
        raise ValueError("OA_GOVERNED_TASK_REQUIRED")
    ctx = source_workspace.task_context(task)
    return ctx, governed.source_evidence_from_context(ctx)


def _load_task_receipts(task: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    loaded = audit_store.load_runtime_receipts(governed.RECEIPT_TYPE, OA_RUNTIME_STORE)
    receipts = [r for r in loaded["receipts"] if r.get("task_id") == task]
    return loaded, receipts


def _same_semantic_decision(existing: dict[str, Any], candidate: dict[str, Any]) -> bool:
    fields = (
        "decision_id",
        "task_id",
        "stage",
        "revision",
        "reviewer",
        "payload_fingerprint",
        "parent_decision_id",
        "parent_receipt_fingerprint",
    )
    return all(existing.get(field) == candidate.get(field) for field in fields)


def _receipt_resume_payload(receipt: dict[str, Any], audit_backend: str) -> dict[str, Any]:
    return {
        "state": "OA_GOVERNED_RECEIPT_RESUMED_READ_ONLY",
        "audit_backend": audit_backend,
        "runtime_receipt_id": receipt["decision_id"],
        "receipt_fingerprint": receipt["receipt_fingerprint"],
        "stage": receipt["stage"],
        "revision": receipt["revision"],
        "reviewer": receipt["reviewer"],
        "parent_decision_id": receipt.get("parent_decision_id"),
        "source_evidence": receipt["source_evidence"],
        "payload": receipt["payload"],
        "authority": "RUNTIME_AUDIT_READ_ONLY",
        "engineering_authority_effect": "NONE",
        "canonical_write_authorized": False,
        "project_material_ready": False,
    }


def build_router(source_workspace) -> APIRouter:
    router = APIRouter()

    @router.get("/api/workbench/object-acquisition/status")
    def oa_governed_status(task: str = ""):
        try:
            _, expected_source = _task_context(source_workspace, task)
            loaded, receipts = _load_task_receipts(task.strip())
        except KeyError:
            return _error("OA_GOVERNED_STATUS_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            return _error("OA_GOVERNED_STATUS_UNAVAILABLE", str(exc), 503)

        stage_latest = {
            stage: governed.latest_stage_receipt(receipts, task.strip(), stage)
            for stage in governed.STAGE_ORDER
        }
        source_mismatch = False
        for row in receipts:
            source = row.get("source_evidence") or {}
            if any(str(source.get(f, "")).strip().lower() != expected_source[f].lower() for f in governed.SOURCE_FIELDS):
                source_mismatch = True
                break
        if source_mismatch:
            return _error("OA_GOVERNED_STATUS_BLOCKED", "OA_GOVERNED_STALE_SOURCE_RECEIPT_PRESENT", 409)

        return JSONResponse(
            {
                "state": "OA_GOVERNED_AUDIT_READY",
                "audit_backend": loaded["audit_backend"],
                "receipt_type": governed.RECEIPT_TYPE,
                "task": task.strip(),
                "source_evidence": expected_source,
                "receipt_count": len(receipts),
                "latest_by_stage": {
                    stage: None if row is None else {
                        "decision_id": row["decision_id"],
                        "receipt_fingerprint": row["receipt_fingerprint"],
                        "revision": row["revision"],
                        "reviewer": row["reviewer"],
                        "timestamp": row["timestamp"],
                    }
                    for stage, row in stage_latest.items()
                },
                "session_storage_role": "UI_CACHE_ONLY",
                "canonical_write_authorized": False,
                "project_material_ready": False,
            },
            headers={"Cache-Control": "no-store"},
        )

    @router.get("/api/workbench/object-acquisition/resume")
    def oa_governed_resume(task: str = "", stage: str = "OA2_PROTOTYPE"):
        task = task.strip()
        stage = stage.strip()
        if stage not in governed.STAGE_ORDER:
            return _error("OA_GOVERNED_RESUME_REJECTED", "OA_GOVERNED_STAGE_INVALID", 400)
        try:
            _, expected_source = _task_context(source_workspace, task)
            loaded, receipts = _load_task_receipts(task)
            row = governed.latest_stage_receipt(receipts, task, stage)
        except KeyError:
            return _error("OA_GOVERNED_RESUME_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            return _error("OA_GOVERNED_RESUME_UNAVAILABLE", str(exc), 503)
        if row is None:
            return _error("OA_GOVERNED_RESUME_EMPTY", "OA_GOVERNED_STAGE_RECEIPT_NOT_FOUND", 404)
        source = row.get("source_evidence") or {}
        if any(str(source.get(f, "")).strip().lower() != expected_source[f].lower() for f in governed.SOURCE_FIELDS):
            return _error("OA_GOVERNED_RESUME_BLOCKED", "OA_GOVERNED_STALE_SOURCE_RECEIPT_PRESENT", 409)
        return JSONResponse(_receipt_resume_payload(row, loaded["audit_backend"]), headers={"Cache-Control": "no-store"})

    @router.post("/api/workbench/object-acquisition/receipt")
    async def oa_governed_receipt(request: Request):
        try:
            wrapper = await request.json()
        except Exception:
            return _error("OA_GOVERNED_RECEIPT_REJECTED", "INVALID_JSON", 400)
        if not isinstance(wrapper, dict):
            return _error("OA_GOVERNED_RECEIPT_REJECTED", "JSON_OBJECT_REQUIRED", 400)
        allowed = {"task", "stage", "revision", "reviewer", "payload", "parent_decision_id"}
        if set(wrapper) - allowed:
            return _error("OA_GOVERNED_RECEIPT_REJECTED", "OA_GOVERNED_WRAPPER_FIELD_SET_MISMATCH", 400)
        try:
            task = str(wrapper.get("task", "")).strip()
            stage = str(wrapper.get("stage", "")).strip()
            revision = str(wrapper.get("revision", "")).strip()
            reviewer = str(wrapper.get("reviewer", "")).strip()
            payload = wrapper.get("payload")
            if not isinstance(payload, dict):
                raise ValueError("OA_GOVERNED_PAYLOAD_OBJECT_REQUIRED")
            _, expected_source = _task_context(source_workspace, task)
            loaded, receipts = _load_task_receipts(task)
            parent_id = wrapper.get("parent_decision_id")
            parent = None
            if parent_id is not None:
                parent = governed.index_receipts(receipts, task).get(str(parent_id))
                if parent is None:
                    raise ValueError("OA_GOVERNED_PARENT_RECEIPT_NOT_FOUND")
            receipt = governed.build_receipt(
                task_id=task,
                stage=stage,
                payload=payload,
                expected_source=expected_source,
                revision=revision,
                reviewer=reviewer,
                parent=parent,
            )
            existing = governed.index_receipts(receipts, task).get(receipt["decision_id"])
            if existing is not None:
                if not _same_semantic_decision(existing, receipt):
                    raise ValueError("OA_GOVERNED_DECISION_ID_COLLISION")
                body = _receipt_resume_payload(existing, loaded["audit_backend"])
                body["state"] = "OA_GOVERNED_RECEIPT_ALREADY_PERSISTED"
                body["idempotent_replay"] = True
                body["next_gate"] = {
                    "OA2_PROTOTYPE": "OA3_DETERMINISTIC_SIMILARITY",
                    "OA4_CLUSTER_REVIEW": "OA5_STRUCTURAL_RESOLVER",
                    "OA5_IDENTITY_CANDIDATE": "OA_G5_EXPLICIT_STRUCTURAL_IDENTITY_REVIEW",
                    "OA_G5_IDENTITY_DECISION": "OA6_PROJECT_MATERIAL_GATE_REMAINS_SEPARATE",
                }[existing["stage"]]
                return JSONResponse(body, status_code=200, headers={"Cache-Control": "no-store"})
            persisted = audit_store.persist_runtime_receipt(receipt, OA_RUNTIME_STORE)
        except KeyError:
            return _error("OA_GOVERNED_RECEIPT_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            reason = str(exc)
            status = 409 if "duplicate decision_id" in reason or "PARENT" in reason or "MISMATCH" in reason or "COLLISION" in reason else 422
            return _error("OA_GOVERNED_RECEIPT_REJECTED", reason, status)

        return JSONResponse(
            {
                "state": "OA_GOVERNED_RECEIPT_PERSISTED_APPEND_ONLY",
                "runtime_receipt_id": persisted["runtime_receipt_id"],
                "sha256": persisted["sha256"],
                "audit_backend": persisted["audit_backend"],
                "stage": receipt["stage"],
                "receipt_fingerprint": receipt["receipt_fingerprint"],
                "parent_decision_id": receipt["parent_decision_id"],
                "authority": receipt["authority"],
                "engineering_authority_effect": receipt["engineering_authority_effect"],
                "canonical_write_authorized": False,
                "project_material_ready": False,
                "next_gate": {
                    "OA2_PROTOTYPE": "OA3_DETERMINISTIC_SIMILARITY",
                    "OA4_CLUSTER_REVIEW": "OA5_STRUCTURAL_RESOLVER",
                    "OA5_IDENTITY_CANDIDATE": "OA_G5_EXPLICIT_STRUCTURAL_IDENTITY_REVIEW",
                    "OA_G5_IDENTITY_DECISION": "OA6_PROJECT_MATERIAL_GATE_REMAINS_SEPARATE",
                }[receipt["stage"]],
            },
            status_code=201,
            headers={"Cache-Control": "no-store"},
        )

    return router
