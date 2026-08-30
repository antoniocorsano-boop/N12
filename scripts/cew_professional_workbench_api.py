#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

import cew_managed_f3_assets as managed_f3_assets
import cew_professional_workbench_client as client
import cew_professional_workbench_core as core
import cew_professional_workbench_document_geometry as document_geometry
import cew_professional_workbench_projection as projection


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
    # Runtime delivery metadata is not part of the scene-revision projection digest.
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
            client.build_client(task.strip()),
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
