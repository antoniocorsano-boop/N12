#!/usr/bin/env python3
"""Async governed-source boundary for CEW Document Discovery.

This adapter avoids parsing or rendering large governed PDFs inside the Uvicorn
process. Analysis is queued to a bounded subprocess worker and page inspection
is served from the worker-produced cached JPEG evidence whenever available.
"""
from __future__ import annotations

import base64
import binascii
from hashlib import sha256
import logging

from fastapi import APIRouter, Request
from fastapi.responses import Response

import cew_document_discovery as discovery
import cew_document_discovery_governed_jobs as governed_jobs
import cew_document_discovery_workbench as base_workbench


LOGGER = logging.getLogger(__name__)
MAX_PAGE_ARTIFACT_BYTES = 6 * 1024 * 1024


def _cached_page_artifact(session_id: str, page_index: int) -> bytes:
    session = discovery.get_session(session_id)
    rows = session.get("report", {}).get("preview_page_images") or []
    selected = None
    for row in rows:
        if isinstance(row, dict) and int(row.get("page_index", -1)) == page_index:
            selected = row
            break
    if selected is None:
        if session.get("source_registration_state") == "GOVERNED_IMMUTABLE_SOURCE":
            raise ValueError("DOCUMENT_DISCOVERY_GOVERNED_PAGE_ARTIFACT_MISSING")
        return discovery.render_page(session_id, page_index)
    if selected.get("render_boundary") != "PROCESS_ISOLATED_WORKER":
        raise ValueError("DOCUMENT_DISCOVERY_PAGE_BOUNDARY_INVALID")
    encoded = str(selected.get("data_base64") or "")
    payload = base64.b64decode(encoded, validate=True)
    if not payload.startswith(b"\xff\xd8") or len(payload) > MAX_PAGE_ARTIFACT_BYTES:
        raise ValueError("DOCUMENT_DISCOVERY_PAGE_ARTIFACT_INVALID")
    if sha256(payload).hexdigest() != str(selected.get("sha256") or "").lower():
        raise ValueError("DOCUMENT_DISCOVERY_PAGE_ARTIFACT_SHA_INVALID")
    return payload


def build_router(source_workspace) -> APIRouter:
    router = APIRouter()

    @router.post("/api/workbench/document-discovery/analyze-governed-async")
    async def analyze_governed_async(request: Request):
        try:
            body = await request.json()
            job = governed_jobs.start_governed_job(
                source_workspace,
                body.get("source_id"),
                body.get("project_id"),
            )
            return base_workbench._json(job, 202)
        except (KeyError, ValueError, TypeError):
            return base_workbench._json({
                "state": "DOCUMENT_DISCOVERY_GOVERNED_ANALYSIS_REJECTED",
                "reason": "DOCUMENT_DISCOVERY_REQUEST_REJECTED",
            }, 409)
        except Exception:
            LOGGER.exception("DOCUMENT_DISCOVERY_GOVERNED_ENQUEUE_BLOCKED")
            return base_workbench._json({
                "state": "DOCUMENT_DISCOVERY_GOVERNED_ENQUEUE_BLOCKED",
                "reason": "DOCUMENT_DISCOVERY_INTERNAL_ERROR",
            }, 503)

    @router.get("/api/workbench/document-discovery/governed-job/{job_id}")
    def governed_job(job_id: str):
        try:
            return base_workbench._json(governed_jobs.governed_job_status(job_id))
        except ValueError:
            return base_workbench._json({
                "state": "DOCUMENT_DISCOVERY_GOVERNED_JOB_NOT_FOUND",
                "reason": "DOCUMENT_DISCOVERY_GOVERNED_JOB_NOT_FOUND",
            }, 404)

    @router.get("/api/workbench/document-discovery/session/{session_id}/page/{page_index}.jpg")
    def cached_page_image(session_id: str, page_index: int):
        try:
            payload = _cached_page_artifact(session_id, page_index)
            return Response(
                payload,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "no-store",
                    "X-CEW-Authority": "READING_AID_ONLY",
                    "X-CEW-Page-Render": "PROCESS_ISOLATED_CACHED",
                },
            )
        except (ValueError, TypeError, binascii.Error):
            return base_workbench._json({
                "state": "DOCUMENT_DISCOVERY_PAGE_REJECTED",
                "reason": "DOCUMENT_DISCOVERY_REQUEST_REJECTED",
            }, 404)

    return router
