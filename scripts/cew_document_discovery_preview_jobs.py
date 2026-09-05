#!/usr/bin/env python3
"""Process-isolated async job boundary for CEW interactive PDF preview.

The HTTP request validates and enqueues only. Expensive PyMuPDF extraction runs
in a separate Python process so vector parsing cannot monopolize or terminate the
Uvicorn web process. The preferred vector worker is memory-capped; if it cannot
complete inside that envelope, the supervisor retries once with the governed
raster evidence engine. Jobs and preview sessions remain transient state and
create no project truth.
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
PREVIEW_VECTOR_TIMEOUT_SECONDS = 45.0
PREVIEW_RASTER_TIMEOUT_SECONDS = 90.0
PREVIEW_WORKER_MEMORY_MB = 192
WORKER_SCRIPT = Path(__file__).with_name("cew_document_discovery_preview_worker.py")
VECTOR_MODE = "VECTOR_BOUNDED"
RASTER_SAFE_MODE = "RASTER_SAFE"
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
        "preview_worker_mode": job.get("preview_worker_mode"),
        "preview_fallback_used": bool(job.get("preview_fallback_used", False)),
        "quality_status": job.get("quality_status"),
        "minimum_page_coverage_ratio": job.get("minimum_page_coverage_ratio"),
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


def _report_is_empty(report: dict[str, Any]) -> bool:
    return (
        int(report.get("page_count") or 0) > 0
        and int(report.get("primitive_candidate_count") or 0) == 0
    )


def _quality(report: dict[str, Any]) -> tuple[str | None, list[str], float | None]:
    gate = report.get("quality_gate")
    if not isinstance(gate, dict):
        return None, [], None
    status = str(gate.get("status") or "").strip().upper() or None
    reasons = [str(value) for value in (gate.get("reasons") or []) if str(value).strip()]
    try:
        coverage = float(gate.get("minimum_page_coverage_ratio"))
    except (TypeError, ValueError):
        coverage = None
    return status, reasons, coverage


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


def _invoke_worker(
    *,
    worker_script: Path,
    work_dir: Path,
    source_version_id: str,
    digest: str,
    mode: str,
    timeout_seconds: float,
    env: dict[str, str],
) -> tuple[subprocess.CompletedProcess[str] | None, str | None]:
    try:
        completed = subprocess.run(
            [
                sys.executable,
                str(worker_script),
                source_version_id,
                digest,
                mode,
            ],
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return None, f"DOCUMENT_DISCOVERY_PREVIEW_WORKER_TIMEOUT_{mode}"

    if completed.returncode != 0:
        LOGGER.warning(
            "DOCUMENT_DISCOVERY_PREVIEW_WORKER_NONZERO mode=%s returncode=%s",
            mode,
            completed.returncode,
        )
        return completed, _worker_exit_reason(completed.returncode)
    return completed, None


def _run(
    job_id: str,
    payload: bytes,
    project_id: str,
    worker_script: Path,
    vector_timeout_seconds: float,
    raster_timeout_seconds: float,
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
            env.setdefault("CEW_PREVIEW_WORKER_MEMORY_MB", str(PREVIEW_WORKER_MEMORY_MB))

            _, primary_failure = _invoke_worker(
                worker_script=worker_script,
                work_dir=root,
                source_version_id=source_version_id,
                digest=digest,
                mode=VECTOR_MODE,
                timeout_seconds=vector_timeout_seconds,
                env=env,
            )

            primary_report: dict[str, Any] | None = None
            if primary_failure is None:
                try:
                    primary_report = _load_worker_report(
                        output_path,
                        digest=digest,
                        source_version_id=source_version_id,
                    )
                except Exception:
                    LOGGER.exception(
                        "DOCUMENT_DISCOVERY_PREVIEW_VECTOR_REPORT_INVALID job_id=%s",
                        job_id,
                    )
                    primary_failure = "DOCUMENT_DISCOVERY_PREVIEW_VECTOR_REPORT_INVALID"
                else:
                    if _report_is_empty(primary_report):
                        primary_failure = "DOCUMENT_DISCOVERY_PREVIEW_VECTOR_EMPTY"
                        LOGGER.warning(
                            "DOCUMENT_DISCOVERY_PREVIEW_VECTOR_EMPTY job_id=%s page_count=%s",
                            job_id,
                            primary_report.get("page_count"),
                        )

            fallback_used = primary_failure is not None
            if fallback_used:
                output_path.unlink(missing_ok=True)
                LOGGER.warning(
                    "DOCUMENT_DISCOVERY_PREVIEW_VECTOR_FALLBACK job_id=%s reason=%s",
                    job_id,
                    primary_failure,
                )
                _, fallback_failure = _invoke_worker(
                    worker_script=worker_script,
                    work_dir=root,
                    source_version_id=source_version_id,
                    digest=digest,
                    mode=RASTER_SAFE_MODE,
                    timeout_seconds=raster_timeout_seconds,
                    env=env,
                )
                if fallback_failure is not None:
                    _set(
                        job_id,
                        state="FAILED",
                        reason=f"DOCUMENT_DISCOVERY_PREVIEW_RASTER_FALLBACK_FAILED:{fallback_failure}",
                        preview_worker_mode=RASTER_SAFE_MODE,
                        preview_fallback_used=True,
                    )
                    return
                report = _load_worker_report(
                    output_path,
                    digest=digest,
                    source_version_id=source_version_id,
                )
                quality_status, quality_reasons, coverage = _quality(report)
                blank_observed = bool((report.get("quality_gate") or {}).get("blank_pages_observed"))
                inconclusive = quality_status == "INCONCLUSIVE" or (
                    _report_is_empty(report) and not blank_observed
                )
                if inconclusive:
                    report["preview_fallback"] = {
                        "used": True,
                        "primary_failure": primary_failure,
                        "fallback_mode": RASTER_SAFE_MODE,
                    }
                    session = _save_preview_session(
                        payload,
                        project_id,
                        digest=digest,
                        source_version_id=source_version_id,
                        report=report,
                    )
                    reason = quality_reasons[0] if quality_reasons else "INCONCLUSIVE_RASTER_DETECTION"
                    _set(
                        job_id,
                        state="INCONCLUSIVE",
                        session_id=session["session_id"],
                        reason=reason,
                        preview_worker_mode=report.get("preview_worker_mode", RASTER_SAFE_MODE),
                        preview_fallback_used=True,
                        quality_status="INCONCLUSIVE",
                        minimum_page_coverage_ratio=coverage,
                    )
                    return
            else:
                if primary_report is None:
                    raise RuntimeError("DOCUMENT_DISCOVERY_PREVIEW_PRIMARY_REPORT_MISSING")
                report = primary_report

            report["preview_fallback"] = {
                "used": fallback_used,
                "primary_failure": primary_failure,
                "fallback_mode": RASTER_SAFE_MODE if fallback_used else None,
            }
            quality_status, _quality_reasons, coverage = _quality(report)
            session = _save_preview_session(
                payload,
                project_id,
                digest=digest,
                source_version_id=source_version_id,
                report=report,
            )
            _set(
                job_id,
                state="READY",
                session_id=session["session_id"],
                reason=None,
                preview_worker_mode=report.get("preview_worker_mode", VECTOR_MODE),
                preview_fallback_used=fallback_used,
                quality_status=quality_status or "READY",
                minimum_page_coverage_ratio=coverage,
            )
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
        "preview_worker_mode": None,
        "preview_fallback_used": False,
        "quality_status": None,
        "minimum_page_coverage_ratio": None,
    }
    queued_public = _public(dict(job))
    with JOB_LOCK:
        while len(JOBS) >= MAX_JOBS:
            terminal = [key for key, row in JOBS.items() if row["state"] in {"READY", "INCONCLUSIVE", "FAILED"}]
            if terminal:
                oldest = min(terminal, key=lambda key: JOBS[key]["updated_at"])
            else:
                oldest = min(JOBS, key=lambda key: JOBS[key]["created_at"])
            JOBS.pop(oldest, None)
        JOBS[job_id] = job

    worker_script = Path(WORKER_SCRIPT)
    vector_timeout_seconds = float(PREVIEW_VECTOR_TIMEOUT_SECONDS)
    raster_timeout_seconds = float(PREVIEW_RASTER_TIMEOUT_SECONDS)
    EXECUTOR.submit(
        _run,
        job_id,
        payload,
        project_id,
        worker_script,
        vector_timeout_seconds,
        raster_timeout_seconds,
    )
    return queued_public


def preview_job_status(job_id: str) -> dict[str, Any]:
    job_id = discovery._text(job_id, "job_id")
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_JOB_NOT_FOUND")
        return _public(dict(job))
