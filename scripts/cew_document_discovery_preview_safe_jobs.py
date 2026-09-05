#!/usr/bin/env python3
"""Web-safe enqueue facade for CEW Document Discovery preview jobs.

The web process performs only byte-envelope validation before enqueueing an
unregistered PDF. It deliberately does not open or parse the user PDF with
PyMuPDF. Full PDF validation, extraction and page rendering occur in the
process-isolated worker owned by ``cew_document_discovery_preview_jobs``.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import secrets
from typing import Any

import cew_document_discovery as discovery
import cew_document_discovery_preview_jobs as base


def _validate_upload_envelope(payload: bytes) -> None:
    if not payload or len(payload) > discovery.MAX_PDF_BYTES or not payload.startswith(b"%PDF"):
        raise ValueError("DOCUMENT_DISCOVERY_PDF_INVALID_OR_TOO_LARGE")


def start_preview_job(payload: bytes, project_id: str) -> dict[str, Any]:
    """Enqueue without opening/parsing the PDF in the Uvicorn process."""
    _validate_upload_envelope(payload)
    project_id = discovery._text(project_id, "project_id")
    digest = sha256(payload).hexdigest()
    job_id = "DPJ-" + secrets.token_hex(12)
    job = {
        "state": "QUEUED",
        "job_id": job_id,
        "project_id": project_id,
        "created_at": base._now(),
        "updated_at": base._now(),
        "source_sha256": digest,
        "source_bytes": len(payload),
        "session_id": None,
        "reason": None,
        "preview_worker_mode": None,
        "preview_fallback_used": False,
        "quality_status": None,
        "minimum_page_coverage_ratio": None,
    }
    queued_public = base._public(dict(job))
    with base.JOB_LOCK:
        while len(base.JOBS) >= base.MAX_JOBS:
            terminal = [
                key for key, row in base.JOBS.items()
                if row["state"] in {"READY", "INCONCLUSIVE", "FAILED"}
            ]
            if terminal:
                oldest = min(terminal, key=lambda key: base.JOBS[key]["updated_at"])
            else:
                oldest = min(base.JOBS, key=lambda key: base.JOBS[key]["created_at"])
            base.JOBS.pop(oldest, None)
        base.JOBS[job_id] = job

    worker_script = Path(base.WORKER_SCRIPT)
    base.EXECUTOR.submit(
        base._run,
        job_id,
        payload,
        project_id,
        worker_script,
        float(base.PREVIEW_VECTOR_TIMEOUT_SECONDS),
        float(base.PREVIEW_RASTER_TIMEOUT_SECONDS),
    )
    return queued_public


def preview_job_status(job_id: str) -> dict[str, Any]:
    return base.preview_job_status(job_id)


def clear_jobs() -> None:
    base.clear_jobs()


def __getattr__(name: str):
    return getattr(base, name)
