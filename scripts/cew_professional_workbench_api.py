#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import html
from pathlib import Path, PurePosixPath
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import cew_managed_f3_assets as managed_f3_assets
import cew_professional_gap_review as gap_review
import cew_professional_workbench_client as client
import cew_professional_workbench_core as core
import cew_professional_workbench_document_geometry as document_geometry
import cew_professional_workbench_projection as projection
import cew_r2hr_governed_ingest as r2gi
import cew_runtime_audit_store as audit_store

R2HR_RUNTIME_STORE = Path("/tmp/cew-runtime/r2hr-receipts")


def _error(state: str, reason: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        {
            "state": state,
            "reason": reason,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    body = dict(payload)
    body.setdefault("canonical_write_authorized", False)
    body.setdefault("engineering_authority_effect", "NONE")
    return JSONResponse(body, status_code=status_code, headers={"Cache-Control": "no-store"})


def _task(payload: dict[str, Any]) -> str:
    task = payload.get("task")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("WORKBENCH_TASK_REQUIRED")
    return task.strip()


def _runtime_scene(task: str, source_workspace) -> dict[str, Any]:
    scene = deepcopy(projection.build_scene(task, source_workspace))
    assets = managed_f3_assets.status()
    geometry = document_geometry.status()
    scene["capabilities"]["managed_f3_assets"] = assets["state"]
    scene["capabilities"]["managed_document_geometry"] = geometry["state"]
    scene["capabilities"]["managed_runtime_dynamic_pdf_rasterization"] = False
    scene["capabilities"]["runtime_docling_required"] = False
    scene["source"]["managed_f3_asset_state"] = assets["state"]
    scene["source"]["managed_document_geometry_state"] = geometry["state"]
    scene["source"]["managed_f3_dzi_url"] = None
    if assets["state"] == "READY":
        scene["source"]["managed_f3_dzi_url"] = (
            "/workbench/assets/" + scene["source"]["f3_dzi_reference"]
        )
        scene["capabilities"]["source_multiresolution_assets"] = "READY_EXACT_REVISION"
    else:
        scene["capabilities"]["source_multiresolution_assets"] = "UNAVAILABLE_FAIL_CLOSED"
        scene["source"]["managed_f3_asset_reason"] = assets.get("reason", "UNAVAILABLE")
    if geometry["state"] != "READY":
        scene["source"]["managed_document_geometry_reason"] = geometry.get("reason", "UNAVAILABLE")
    core.validate_scene(scene)
    return scene


def _safe_asset_path(asset_path: str) -> Path:
    posix = PurePosixPath(asset_path)
    if not asset_path or posix.is_absolute() or any(part in {"", ".", ".."} for part in posix.parts):
        raise ValueError("MANAGED_F3_ASSET_PATH_REJECTED")
    root = managed_f3_assets.ASSET_ROOT.resolve()
    target = (root / Path(*posix.parts)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("MANAGED_F3_ASSET_PATH_REJECTED") from exc
    return target


def _task_context(task: str, source_workspace) -> tuple[dict[str, Any], str]:
    ctx = source_workspace.task_context(task)
    region_id = str(ctx["region"]["evidence_region_id"]).strip()
    if not region_id:
        raise ValueError("WORKBENCH_EVIDENCE_REGION_REQUIRED")
    return ctx, region_id


def _runtime_r2gi_report() -> dict[str, Any]:
    review_state = gap_review.status()
    if review_state.get("state") != "READY":
        raise ValueError(review_state.get("reason", "R2HR_PACKAGE_NOT_READY"))
    loaded = audit_store.load_runtime_receipts(
        r2gi.ALLOWED_AUDIT_RECEIPT_TYPE,
        R2HR_RUNTIME_STORE,
    )
    candidate_head_sha = str(review_state["candidate_head_sha"])
    candidate_receipts = [
        envelope
        for envelope in loaded["receipts"]
        if isinstance(envelope.get("r2hr_receipt"), dict)
        and envelope["r2hr_receipt"].get("candidate_head_sha") == candidate_head_sha
    ]
    report = r2gi.ingest_envelopes(candidate_receipts)
    report["runtime_ingest"] = True
    report["audit_backend"] = loaded["audit_backend"]
    report["audit_receipt_total"] = loaded["receipt_count"]
    report["candidate_receipt_count"] = len(candidate_receipts)
    report["canonical_write_authorized"] = False
    report["engineering_authority_effect"] = "NONE"
    return report


def _public_workbench_html(task: str) -> str:
    """Keep internal task ids out of the primary visible Workbench chrome."""
    rendered = client.build_client(task)
    escaped = html.escape(task, quote=True)
    rendered = rendered.replace(
        f"<title>CEW — Ambiente grafico professionale · {escaped}</title>",
        "<title>CEW — Ambiente grafico professionale</title>",
    )
    rendered = rendered.replace(
        f'<div class="crumb">Progetto N12 › Evidenza › {escaped}</div>',
        '<div class="crumb">Progetto N12 › Evidenza › Revisione tecnica</div>',
    )
    marker = '<a id="pdfLink" class="button desktop-only" href="#" target="_blank" rel="noopener">PDF verificato</a>'
    review_link = (
        f'<a id="gapReviewLink" class="button desktop-only" '
        f'href="/workbench/gap-review?task={escaped}">Verifica continuità raster</a>'
    )
    if marker in rendered:
        rendered = rendered.replace(marker, marker + review_link, 1)
    return rendered


def build_router(source_workspace) -> APIRouter:
    router = APIRouter()

    @router.get("/workbench", response_class=HTMLResponse)
    def professional_workbench(task: str = ""):
        if not task.strip():
            return HTMLResponse(
                "<h1>Ambiente grafico non disponibile</h1><p>Seleziona una revisione dal progetto.</p><a href='/'>Torna al progetto</a>",
                status_code=400,
            )
        try:
            source_workspace.task_context(task.strip())
        except (KeyError, ValueError):
            return HTMLResponse(
                "<h1>Ambiente grafico non disponibile</h1><p>Attività o provenienza non valida. Nessuna geometria è stata ricostruita.</p><a href='/'>Torna al progetto</a>",
                status_code=404,
            )
        return HTMLResponse(
            _public_workbench_html(task.strip()),
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Engineering-Authority-Effect": "NONE",
            },
        )

    @router.get("/api/workbench/assets/status")
    def workbench_asset_status():
        return _json(managed_f3_assets.status())

    @router.get("/api/workbench/document-geometry/status")
    def workbench_document_geometry_status():
        return _json(document_geometry.status())

    @router.get("/api/workbench/gap-review/status")
    def workbench_gap_review_status(task: str = ""):
        if not task.strip():
            return _error("R2HR_STATUS_REJECTED", "WORKBENCH_TASK_REQUIRED", 400)
        try:
            _, region_id = _task_context(task.strip(), source_workspace)
            state = gap_review.status()
        except (KeyError, ValueError) as exc:
            return _error("R2HR_STATUS_REJECTED", str(exc), 422)
        if state["state"] != "READY":
            return _json(state, 503)
        row = next((row for row in state["regions"] if row["evidence_region_id"] == region_id), None)
        if row is None:
            return _error("R2HR_STATUS_REJECTED", "R2HR_REGION_NOT_FOUND", 404)
        return _json(
            {
                "state": "READY",
                "evidence_region_id": region_id,
                "gap_count": row["gap_count"],
                "candidate_head_sha": state["candidate_head_sha"],
                "human_review_required": row["gap_count"] > 0,
                "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
                "geometry_materialization_authorized": False,
            }
        )

    @router.get("/api/workbench/gap-review/ingest-status")
    def workbench_gap_review_ingest_status(task: str = ""):
        if not task.strip():
            return _error("R2GI_RUNTIME_STATUS_REJECTED", "WORKBENCH_TASK_REQUIRED", 400)
        try:
            _, region_id = _task_context(task.strip(), source_workspace)
            report = _runtime_r2gi_report()
        except KeyError:
            return _error("R2GI_RUNTIME_STATUS_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            marker = str(exc)
            if "R2GI_DUPLICATE_REGION_RECEIPT" in marker:
                return _error("R2GI_RUNTIME_RECEIPT_CONFLICT", marker, 409)
            return _error("R2GI_RUNTIME_STATUS_UNAVAILABLE", marker, 503)
        row = next((item for item in report["regions"] if item["evidence_region_id"] == region_id), None)
        if row is None:
            return _error("R2GI_RUNTIME_STATUS_REJECTED", "R2GI_REGION_NOT_FOUND", 404)
        return _json(
            {
                "state": report["state"],
                "next_gate": report["next_gate"],
                "candidate_head_sha": report["candidate_head_sha"],
                "region_coverage": report["region_coverage"],
                "evidence_region_id": region_id,
                "region_state": row["state"],
                "receipt_ingested": row["receipt_ingested"],
                "candidate_receipt_count": report["candidate_receipt_count"],
                "audit_backend": report["audit_backend"],
                "review_findings_are_geometry": False,
                "geometry_materialization_authorized": False,
            }
        )

    @router.get("/workbench/gap-review", response_class=HTMLResponse)
    def workbench_gap_review(task: str = ""):
        if not task.strip():
            return HTMLResponse("<h1>Revisione non disponibile</h1><a href='/'>Torna al progetto</a>", status_code=400)
        try:
            _, region_id = _task_context(task.strip(), source_workspace)
            page = gap_review.build_review_page(task.strip(), region_id)
        except (KeyError, ValueError) as exc:
            return HTMLResponse(
                f"<h1>Revisione non disponibile</h1><p>{html.escape(str(exc))}</p><a href='/workbench?task={html.escape(task.strip(), quote=True)}'>Torna all'ambiente grafico</a>",
                status_code=503,
            )
        return HTMLResponse(
            page,
            headers={
                "Cache-Control": "no-store",
                "X-CEW-Review-Authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
                "X-CEW-Geometry-Materialization": "false",
                "X-CEW-Canonical-Write": "false",
            },
        )

    @router.get("/workbench/gap-review/assets/{region_id}/source_crop_300.png")
    def workbench_gap_review_source_crop(region_id: str):
        try:
            target = gap_review.source_crop_path(region_id)
        except ValueError as exc:
            return _error("R2HR_ASSET_REJECTED", str(exc), 422)
        return FileResponse(
            target,
            media_type="image/png",
            headers={
                "Cache-Control": "private, max-age=31536000, immutable",
                "X-CEW-Derived-Authority": "READING_AID_ONLY",
                "X-CEW-Canonical-Write": "false",
            },
        )

    @router.post("/api/workbench/gap-review/receipt")
    async def workbench_gap_review_receipt(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return _error("R2HR_RECEIPT_REJECTED", "INVALID_JSON", 400)
        if not isinstance(payload, dict) or set(payload) != {"task", "receipt"}:
            return _error("R2HR_RECEIPT_REJECTED", "R2HR_WRAPPER_FIELD_SET_MISMATCH", 400)
        try:
            task_id = _task(payload)
            _, region_id = _task_context(task_id, source_workspace)
            receipt = payload.get("receipt")
            if not isinstance(receipt, dict):
                raise ValueError("R2HR_RECEIPT_OBJECT_REQUIRED")
            if receipt.get("evidence_region_id") != region_id:
                raise ValueError("R2HR_TASK_REGION_MISMATCH")
            expected = gap_review.template(region_id)
            validated = gap_review.validate_receipt(receipt, expected)
            envelope = gap_review.audit_envelope(task_id, validated)
            persisted = audit_store.persist_runtime_receipt(envelope, R2HR_RUNTIME_STORE)
        except (KeyError, ValueError) as exc:
            return _error("R2HR_RECEIPT_REJECTED", str(exc), 422)

        ingest_state = "UNAVAILABLE_FAIL_CLOSED"
        ingest_coverage = None
        ingest_next_gate = "R2HR_GOVERNED_REVIEW_INGEST_REQUIRED"
        ingest_reason = None
        try:
            report = _runtime_r2gi_report()
            ingest_state = report["state"]
            ingest_coverage = report["region_coverage"]
            ingest_next_gate = report["next_gate"]
        except ValueError as exc:
            ingest_reason = str(exc)
            if "R2GI_DUPLICATE_REGION_RECEIPT" in ingest_reason:
                ingest_state = "BLOCKED_RECEIPT_CONFLICT"
                ingest_next_gate = "R2GI_RECEIPT_CONFLICT_RESOLUTION_REQUIRED"

        return _json(
            {
                "state": "R2HR_RECEIPT_PERSISTED_AUDIT_ONLY",
                "runtime_receipt_id": persisted["runtime_receipt_id"],
                "sha256": persisted["sha256"],
                "audit_backend": persisted["audit_backend"],
                "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
                "governed_ingest_state": ingest_state,
                "governed_ingest_region_coverage": ingest_coverage,
                "governed_ingest_reason": ingest_reason,
                "geometry_materialization_authorized": False,
                "bridge_candidate_authorized": False,
                "next_gate": ingest_next_gate,
            }
        )

    @router.get("/workbench/assets/{asset_path:path}")
    def workbench_asset(asset_path: str):
        try:
            managed_f3_assets.validate_manifest()
            target = _safe_asset_path(asset_path)
        except ValueError as exc:
            return _error("MANAGED_F3_ASSET_REJECTED", str(exc), 422)
        if not target.is_file():
            return _error("MANAGED_F3_ASSET_NOT_FOUND", "ASSET_NOT_FOUND", 404)
        return FileResponse(
            target,
            headers={
                "Cache-Control": "private, max-age=31536000, immutable",
                "X-CEW-Derived-Authority": "READING_AID_ONLY",
                "X-CEW-Canonical-Write": "false",
                "X-CEW-Runtime-Revision": managed_f3_assets.runtime_revision(),
            },
        )

    @router.get("/api/workbench/scene")
    def workbench_scene(task: str = ""):
        if not task.strip():
            return _error("WORKBENCH_SCENE_REJECTED", "WORKBENCH_TASK_REQUIRED", 400)
        try:
            scene = _runtime_scene(task.strip(), source_workspace)
        except KeyError:
            return _error("WORKBENCH_SCENE_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            return _error("WORKBENCH_SCENE_REJECTED", str(exc), 422)
        except Exception:
            return _error("WORKBENCH_SCENE_UNAVAILABLE", "SCENE_PROJECTION_FAILED", 503)
        return _json(scene)

    @router.post("/api/workbench/view/resolve")
    async def workbench_view_resolve(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return _error("WORKBENCH_VIEW_REJECTED", "INVALID_JSON", 400)
        if not isinstance(payload, dict):
            return _error("WORKBENCH_VIEW_REJECTED", "JSON_OBJECT_REQUIRED", 400)
        try:
            scene = _runtime_scene(_task(payload), source_workspace)
            result = core.resolve_view_state(
                scene,
                requested_mode=str(payload.get("requested_mode", "SOURCE")),
                requested_sync_mode=str(payload.get("requested_sync_mode", "OFF")),
                registration_id=payload.get("registration_id"),
            )
        except KeyError:
            return _error("WORKBENCH_VIEW_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            return _error("WORKBENCH_VIEW_REJECTED", str(exc), 422)
        except Exception:
            return _error("WORKBENCH_VIEW_UNAVAILABLE", "VIEW_RESOLUTION_FAILED", 503)
        return _json(result)

    @router.post("/api/workbench/view/snapshot")
    async def workbench_view_snapshot(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return _error("WORKBENCH_VIEW_REJECTED", "INVALID_JSON", 400)
        if not isinstance(payload, dict):
            return _error("WORKBENCH_VIEW_REJECTED", "JSON_OBJECT_REQUIRED", 400)
        try:
            scene = _runtime_scene(_task(payload), source_workspace)
            view = core.create_view_snapshot(
                scene,
                requested_mode=str(payload.get("requested_mode", "SOURCE")),
                requested_sync_mode=str(payload.get("requested_sync_mode", "OFF")),
                registration_id=payload.get("registration_id"),
                active_layers=list(payload.get("active_layers") or ["ORIGINAL_SOURCE"]),
                source_viewport=dict(payload.get("source_viewport") or {}),
                technical_viewport=dict(payload.get("technical_viewport") or {}),
                selected_object_id=payload.get("selected_object_id"),
                selected_evidence_region_id=payload.get("selected_evidence_region_id"),
            )
        except KeyError:
            return _error("WORKBENCH_VIEW_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except (TypeError, ValueError) as exc:
            return _error("WORKBENCH_VIEW_REJECTED", str(exc), 422)
        except Exception:
            return _error("WORKBENCH_VIEW_UNAVAILABLE", "VIEW_SNAPSHOT_FAILED", 503)
        return _json(view)

    @router.post("/api/workbench/working-edit/preview")
    async def workbench_working_edit_preview(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return _error("WORKING_EDIT_REJECTED", "INVALID_JSON", 400)
        if not isinstance(payload, dict):
            return _error("WORKING_EDIT_REJECTED", "JSON_OBJECT_REQUIRED", 400)
        try:
            scene = _runtime_scene(_task(payload), source_workspace)
            edit = core.create_working_edit(
                scene,
                target_object_id=str(payload.get("target_object_id", "")),
                property_name=str(payload.get("property_name", "")),
                proposed_value=payload.get("proposed_value"),
                author_session=str(payload.get("author_session", "")),
                state=str(payload.get("state", "DRAFT")),
            )
        except KeyError:
            return _error("WORKING_EDIT_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except ValueError as exc:
            return _error("WORKING_EDIT_REJECTED", str(exc), 422)
        except Exception:
            return _error("WORKING_EDIT_UNAVAILABLE", "WORKING_EDIT_PREVIEW_FAILED", 503)
        return _json(edit)

    @router.post("/api/workbench/reading-issue/preview")
    async def workbench_reading_issue_preview(request: Request):
        try:
            payload = await request.json()
        except Exception:
            return _error("READING_ISSUE_REJECTED", "INVALID_JSON", 400)
        if not isinstance(payload, dict):
            return _error("READING_ISSUE_REJECTED", "JSON_OBJECT_REQUIRED", 400)
        try:
            scene = _runtime_scene(_task(payload), source_workspace)
            issue = core.create_reading_issue(
                scene,
                question=str(payload.get("question", "")),
                state=str(payload.get("state", "OPEN")),
                anchor_object_id=payload.get("anchor_object_id"),
                anchor_geometry=payload.get("anchor_geometry"),
                evidence_link_ids=list(payload.get("evidence_link_ids") or []),
            )
        except KeyError:
            return _error("READING_ISSUE_NOT_FOUND", "TASK_OR_SOURCE_NOT_FOUND", 404)
        except (TypeError, ValueError) as exc:
            return _error("READING_ISSUE_REJECTED", str(exc), 422)
        except Exception:
            return _error("READING_ISSUE_UNAVAILABLE", "READING_ISSUE_PREVIEW_FAILED", 503)
        return _json(issue)

    return router
