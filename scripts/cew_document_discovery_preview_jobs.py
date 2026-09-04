#!/usr/bin/env python3
"""In-process async job boundary for CEW interactive PDF preview.

The HTTP request only validates and enqueues. Extraction happens after the
request has returned, so gateway request duration is not coupled to vector
complexity. Jobs are transient preview state only and create no project truth.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import secrets
from threading import RLock
from typing import Any

import cew_document_discovery as discovery
import cew_document_discovery_preview_engine as preview_engine

MAX_JOBS = 6
JOB_LOCK = RLock()
JOBS: dict[str, dict[str, Any]] = {}
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cew-preview")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clear_jobs() -> None:
    with JOB_LOCK:
        JOBS.clear()


def _public(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "state": job["state"],
        "job_id": job["job_id"],
        "project_id": job["project_id"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "source_sha256": job["source_sha256"],
        "source_bytes": job["source_bytes"],
        "session_id": job.get("session_id"),
        "reason": job.get("reason"),
        "analysis_scope": "BOUNDED_INTERACTIVE_PREVIEW",
        "teaching_enabled": False,
        "authority": dict(discovery.AUTHORITY),
    }


def _set(job_id: str, **changes: Any) -> None:
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return
        job.update(changes)
        job["updated_at"] = _now()


def _create_bounded_session(payload: bytes, project_id: str) -> dict[str, Any]:
    discovery._validate_pdf(payload)
    digest = sha256(payload).hexdigest()
    source_version_id = "PREVIEW-" + digest[:24]
    report = preview_engine.preacquire_preview_pdf(
        payload,
        source_version_id=source_version_id,
        expected_sha256=digest,
    )
    return discovery._save_session({
        "session_id": "DISC-" + secrets.token_hex(12),
        "created_at": _now(),
        "project_id": discovery._text(project_id, "project_id"),
        "source_id": None,
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "source_registration_state": "UNREGISTERED_PREVIEW",
        "page_registry": {},
        "teaching_enabled": False,
        "teaching_blocker": "IMMUTABLE_SOURCE_AND_READY_PAGE_REGISTRATION_REQUIRED",
        "payload": payload,
        "report": report,
        "authority": dict(discovery.AUTHORITY),
    })


def _run(job_id: str, payload: bytes, project_id: str) -> None:
    _set(job_id, state="RUNNING")
    try:
        session = _create_bounded_session(payload, project_id)
        _set(job_id, state="READY", session_id=session["session_id"], reason=None)
    except Exception as exc:
        _set(job_id, state="FAILED", reason=f"{type(exc).__name__}: {exc}")


def start_preview_job(payload: bytes, project_id: str) -> dict[str, Any]:
    discovery._validate_pdf(payload)
    project_id = discovery._text(project_id, "project_id")
    digest = sha256(payload).hexdigest()
    job_id = "DPJ-" + secrets.token_hex(12)
    job = {
        "state": "QUEUED",
        "job_id": job_id,
        "project_id": project_id,
        "created_at": _now(),
        "updated_at": _now(),
        "source_sha256": digest,
        "source_bytes": len(payload),
        "session_id": None,
        "reason": None,
    }
    # Capture the enqueue acknowledgement before the worker can mutate the
    # shared job object. The POST contract is always QUEUED; subsequent state
    # is observable only through preview_job_status().
    queued_public = _public(dict(job))
    with JOB_LOCK:
        while len(JOBS) >= MAX_JOBS:
            terminal = [key for key, row in JOBS.items() if row["state"] in {"READY", "FAILED"}]
            if terminal:
                oldest = min(terminal, key=lambda key: JOBS[key]["updated_at"])
            else:
                oldest = min(JOBS, key=lambda key: JOBS[key]["created_at"])
            JOBS.pop(oldest, None)
        JOBS[job_id] = job
    EXECUTOR.submit(_run, job_id, payload, project_id)
    return queued_public


def preview_job_status(job_id: str) -> dict[str, Any]:
    job_id = discovery._text(job_id, "job_id")
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_JOB_NOT_FOUND")
        return _public(dict(job))