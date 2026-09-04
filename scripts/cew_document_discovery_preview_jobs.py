#!/usr/bin/env python3
"""Process-isolated async job boundary for CEW interactive PDF preview.

The HTTP request validates and enqueues only. Expensive PyMuPDF extraction runs
in a separate Python process so vector parsing cannot monopolize or terminate the
Uvicorn web process. Jobs and preview sessions remain transient process-local
state and create no project truth.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from threading import RLock
from typing import Any

import cew_document_discovery as discovery

MAX_JOBS = 6
PREVIEW_WORKER_TIMEOUT_SECONDS = 150.0
WORKER_SCRIPT = Path(__file__).with_name("cew_document_discovery_preview_worker.py")
JOB_LOCK = RLock()
JOBS: dict[str, dict[str, Any]] = {}
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cew-preview-supervisor")
LOGGER = logging.getLogger(__name__)


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
        "execution_boundary": "PROCESS_ISOLATED_SUBPROCESS",
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


def _worker_exit_reason(returncode: int) -> str:
    if returncode < 0:
        return f"DOCUMENT_DISCOVERY_PREVIEW_WORKER_SIGNAL_{-returncode}"
    return f"DOCUMENT_DISCOVERY_PREVIEW_WORKER_EXIT_{returncode}"


def _load_worker_report(output_path: Path, *, digest: str, source_version_id: str) -> dict[str, Any]:
    if not output_path.is_file():
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_WORKER_RESULT_MISSING")
    report = json.loads(output_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_WORKER_RESULT_INVALID")
    if report.get("analysis_scope") != "BOUNDED_INTERACTIVE_PREVIEW":
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_WORKER_SCOPE_INVALID")
    if str(report.get("source_sha256") or "").lower() != digest.lower():
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_WORKER_SHA_INVALID")
    if report.get("source_version_id") != source_version_id:
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_WORKER_SOURCE_VERSION_INVALID")
    return report


def _save_preview_session(
    payload: bytes,
    project_id: str,
    *,
    digest: str,
    source_version_id: str,
    report: dict[str, Any],
) -> dict[str, Any]:
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


def _run(
    job_id: str,
    payload: bytes,
    project_id: str,
    worker_script: Path,
    timeout_seconds: float,
) -> None:
    _set(job_id, state="RUNNING")
    digest = sha256(payload).hexdigest()
    source_version_id = "PREVIEW-" + digest[:24]

    try:
        with tempfile.TemporaryDirectory(prefix="cew-preview-worker-") as tmp:
            root = Path(tmp)
            input_path = root / "source.pdf"
            output_path = root / "report.json"
            input_path.write_bytes(payload)

            env = dict(os.environ)
            env.setdefault("OMP_NUM_THREADS", "1")
            env.setdefault("OPENBLAS_NUM_THREADS", "1")
            env.setdefault("MKL_NUM_THREADS", "1")
            env.setdefault("NUMEXPR_NUM_THREADS", "1")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(worker_script),
                    str(input_path),
                    str(output_path),
                    source_version_id,
                    digest,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=timeout_seconds,
                env=env,
            )

            if completed.returncode != 0:
                LOGGER.error(
                    "DOCUMENT_DISCOVERY_PREVIEW_WORKER_NONZERO job_id=%s returncode=%s stderr=%s",
                    job_id,
                    completed.returncode,
                    (completed.stderr or "").strip()[:2000],
                )
                _set(job_id, state="FAILED", reason=_worker_exit_reason(completed.returncode))
                return

            report = _load_worker_report(
                output_path,
                digest=digest,
                source_version_id=source_version_id,
            )
            session = _save_preview_session(
                payload,
                project_id,
                digest=digest,
                source_version_id=source_version_id,
                report=report,
            )
            _set(job_id, state="READY", session_id=session["session_id"], reason=None)
    except subprocess.TimeoutExpired:
        LOGGER.warning(
            "DOCUMENT_DISCOVERY_PREVIEW_WORKER_TIMEOUT job_id=%s timeout_seconds=%s",
            job_id,
            timeout_seconds,
        )
        _set(job_id, state="FAILED", reason="DOCUMENT_DISCOVERY_PREVIEW_WORKER_TIMEOUT")
    except Exception:
        LOGGER.exception("DOCUMENT_DISCOVERY_PREVIEW_WORKER_SUPERVISOR_FAILED job_id=%s", job_id)
        _set(job_id, state="FAILED", reason="DOCUMENT_DISCOVERY_PREVIEW_WORKER_INTERNAL_ERROR")


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
    # Capture the enqueue acknowledgement before the supervisor can mutate the
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

    # Snapshot mutable test/runtime knobs before queueing. The supervisor thread
    # waits for the child process only; PyMuPDF extraction never runs in Uvicorn.
    worker_script = Path(WORKER_SCRIPT)
    timeout_seconds = float(PREVIEW_WORKER_TIMEOUT_SECONDS)
    EXECUTOR.submit(_run, job_id, payload, project_id, worker_script, timeout_seconds)
    return queued_public


def preview_job_status(job_id: str) -> dict[str, Any]:
    job_id = discovery._text(job_id, "job_id")
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_JOB_NOT_FOUND")
        return _public(dict(job))
