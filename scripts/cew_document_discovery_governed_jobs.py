#!/usr/bin/env python3
"""Process-isolated jobs for governed CEW Document Discovery sources.

Governed source bytes are trusted by provenance, but their PDF parsing is still
resource-intensive. This module keeps fetch/hash/page-registry checks in the web
process and delegates extraction/render evidence to the same bounded subprocess
worker used by unregistered preview analysis.

The resulting session remains a governed immutable-source session: candidate
source_version_id values are produced by the worker against the canonical
SourceVersion, READY Page registrations are preserved, and teaching is enabled
only when every analysed page has a READY registry entry.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import tempfile
from threading import RLock
from typing import Any

import cew_document_discovery as discovery
import cew_document_discovery_preview_jobs as preview_jobs


MAX_JOBS = 6
JOB_LOCK = RLock()
JOBS: dict[str, dict[str, Any]] = {}
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cew-governed-supervisor")


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
        "source_id": job["source_id"],
        "source_version_id": job["source_version_id"],
        "source_sha256": job["source_sha256"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "session_id": job.get("session_id"),
        "reason": job.get("reason"),
        "analysis_scope": "BOUNDED_GOVERNED_DOCUMENT_DISCOVERY",
        "execution_boundary": "PROCESS_ISOLATED_SUBPROCESS",
        "worker_mode": job.get("worker_mode"),
        "fallback_used": bool(job.get("fallback_used", False)),
        "signal_recovery_used": bool(job.get("signal_recovery_used", False)),
        "quality_status": job.get("quality_status"),
        "minimum_page_coverage_ratio": job.get("minimum_page_coverage_ratio"),
        "teaching_enabled": bool(job.get("teaching_enabled", False)),
        "authority": dict(discovery.AUTHORITY),
    }


def _set(job_id: str, **changes: Any) -> None:
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            return
        job.update(changes)
        job["updated_at"] = _now()


def _save_governed_session(
    *,
    payload: bytes,
    project_id: str,
    source_id: str,
    source_version_id: str,
    digest: str,
    pages: dict[int, dict[str, Any]],
    report: dict[str, Any],
) -> dict[str, Any]:
    page_count = int(report.get("page_count") or 0)
    if page_count < 1:
        raise ValueError("DOCUMENT_DISCOVERY_GOVERNED_PAGE_COUNT_INVALID")
    all_pages_ready = all(index in pages for index in range(page_count))
    if not all_pages_ready:
        raise ValueError("DOCUMENT_DISCOVERY_READY_PAGE_REGISTRATION_REQUIRED")
    return discovery._save_session({
        "session_id": "DISC-" + secrets.token_hex(12),
        "created_at": _now(),
        "project_id": discovery._text(project_id, "project_id"),
        "source_id": source_id,
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "source_registration_state": "GOVERNED_IMMUTABLE_SOURCE",
        "page_registry": pages,
        "teaching_enabled": True,
        "teaching_blocker": None,
        "payload": payload,
        "report": report,
        "authority": dict(discovery.AUTHORITY),
    })


def _run(
    job_id: str,
    payload: bytes,
    project_id: str,
    source_id: str,
    source_version_id: str,
    digest: str,
    pages: dict[int, dict[str, Any]],
) -> None:
    _set(job_id, state="RUNNING")
    try:
        with tempfile.TemporaryDirectory(prefix="cew-governed-worker-") as tmp:
            root = Path(tmp)
            output_path = root / "report.json"
            prior_report_path = root / preview_jobs.PRIOR_REPORT_FILENAME
            (root / "source.pdf").write_bytes(payload)

            env = dict(os.environ)
            env.setdefault("OMP_NUM_THREADS", "1")
            env.setdefault("OPENBLAS_NUM_THREADS", "1")
            env.setdefault("MKL_NUM_THREADS", "1")
            env.setdefault("NUMEXPR_NUM_THREADS", "1")
            env.setdefault("CEW_PREVIEW_WORKER_MEMORY_MB", str(preview_jobs.PREVIEW_WORKER_MEMORY_MB))

            _, primary_failure = preview_jobs._invoke_worker(
                worker_script=Path(preview_jobs.WORKER_SCRIPT),
                work_dir=root,
                source_version_id=source_version_id,
                digest=digest,
                mode=preview_jobs.VECTOR_MODE,
                timeout_seconds=float(preview_jobs.PREVIEW_VECTOR_TIMEOUT_SECONDS),
                env=env,
            )
            report: dict[str, Any] | None = None
            if primary_failure is None:
                try:
                    report = preview_jobs._load_worker_report(
                        output_path,
                        digest=digest,
                        source_version_id=source_version_id,
                    )
                except Exception:
                    primary_failure = "DOCUMENT_DISCOVERY_GOVERNED_VECTOR_REPORT_INVALID"
                else:
                    if preview_jobs._report_is_empty(report):
                        primary_failure = "DOCUMENT_DISCOVERY_GOVERNED_VECTOR_EMPTY"

            fallback_used = primary_failure is not None
            signal_recovery_used = False
            recovery_outcome: str | None = None

            if fallback_used:
                output_path.unlink(missing_ok=True)
                _, fallback_failure = preview_jobs._invoke_worker(
                    worker_script=Path(preview_jobs.WORKER_SCRIPT),
                    work_dir=root,
                    source_version_id=source_version_id,
                    digest=digest,
                    mode=preview_jobs.RASTER_SAFE_MODE,
                    timeout_seconds=float(preview_jobs.PREVIEW_RASTER_TIMEOUT_SECONDS),
                    env=env,
                )
                if fallback_failure is not None:
                    _set(
                        job_id,
                        state="FAILED",
                        reason=f"DOCUMENT_DISCOVERY_GOVERNED_RASTER_FAILED:{fallback_failure}",
                        worker_mode=preview_jobs.RASTER_SAFE_MODE,
                        fallback_used=True,
                    )
                    return
                report = preview_jobs._load_worker_report(
                    output_path,
                    digest=digest,
                    source_version_id=source_version_id,
                )

                recovery_trigger = preview_jobs._signal_recovery_trigger(report)
                if recovery_trigger is not None:
                    signal_recovery_used = True
                    prior_report_path.write_text(
                        json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                        encoding="utf-8",
                    )
                    output_path.unlink(missing_ok=True)
                    _, recovery_failure = preview_jobs._invoke_worker(
                        worker_script=Path(preview_jobs.WORKER_SCRIPT),
                        work_dir=root,
                        source_version_id=source_version_id,
                        digest=digest,
                        mode=preview_jobs.RASTER_SIGNAL_RECOVERY_MODE,
                        timeout_seconds=float(preview_jobs.PREVIEW_SIGNAL_RECOVERY_TIMEOUT_SECONDS),
                        env=env,
                    )
                    if recovery_failure is None:
                        report = preview_jobs._load_worker_report(
                            output_path,
                            digest=digest,
                            source_version_id=source_version_id,
                        )
                        recovery_outcome = "COMPLETED"
                    else:
                        recovery_outcome = recovery_failure
                        gate = report.setdefault("quality_gate", {})
                        if isinstance(gate, dict):
                            gate["status"] = "INCONCLUSIVE"
                            reasons = [str(v) for v in (gate.get("reasons") or []) if str(v).strip()]
                            reason = f"DOCUMENT_DISCOVERY_SIGNAL_RECOVERY_DEGRADED:{recovery_failure}"
                            if reason not in reasons:
                                reasons.append(reason)
                            gate["reasons"] = reasons

            if report is None:
                raise RuntimeError("DOCUMENT_DISCOVERY_GOVERNED_REPORT_MISSING")

            report["preview_fallback"] = {
                "used": fallback_used,
                "primary_failure": primary_failure,
                "fallback_mode": preview_jobs.RASTER_SAFE_MODE if fallback_used else None,
                "signal_recovery_mode": preview_jobs.RASTER_SIGNAL_RECOVERY_MODE if signal_recovery_used else None,
                "signal_recovery_outcome": recovery_outcome,
            }
            quality_status, quality_reasons, coverage = preview_jobs._quality(report)
            session = _save_governed_session(
                payload=payload,
                project_id=project_id,
                source_id=source_id,
                source_version_id=source_version_id,
                digest=digest,
                pages=pages,
                report=report,
            )
            terminal = "INCONCLUSIVE" if quality_status == "INCONCLUSIVE" else "READY"
            _set(
                job_id,
                state=terminal,
                session_id=session["session_id"],
                reason=quality_reasons[0] if terminal == "INCONCLUSIVE" and quality_reasons else None,
                worker_mode=report.get("preview_worker_mode", preview_jobs.VECTOR_MODE),
                fallback_used=fallback_used,
                signal_recovery_used=signal_recovery_used,
                quality_status=quality_status or "READY",
                minimum_page_coverage_ratio=coverage,
                teaching_enabled=True,
            )
    except Exception:
        preview_jobs.LOGGER.exception("DOCUMENT_DISCOVERY_GOVERNED_WORKER_SUPERVISOR_FAILED job_id=%s", job_id)
        _set(job_id, state="FAILED", reason="DOCUMENT_DISCOVERY_GOVERNED_WORKER_INTERNAL_ERROR")


def start_governed_job(source_workspace, source_id: str, project_id: str) -> dict[str, Any]:
    source_id = discovery._text(source_id, "source_id")
    project_id = discovery._text(project_id, "project_id")
    if not hasattr(source_workspace, "fetch_verified_source"):
        raise ValueError("DOCUMENT_DISCOVERY_SOURCE_FETCH_UNAVAILABLE")

    payload, source = source_workspace.fetch_verified_source(source_id)
    if not payload or len(payload) > discovery.MAX_PDF_BYTES or not payload.startswith(b"%PDF"):
        raise ValueError("DOCUMENT_DISCOVERY_PDF_INVALID_OR_TOO_LARGE")
    digest = discovery._text(source.get("sha256"), "source_sha256").lower()
    if sha256(payload).hexdigest() != digest:
        raise ValueError("DOCUMENT_DISCOVERY_SOURCE_SHA256_MISMATCH")

    pages = discovery.page_registry(source_workspace, source_id)
    versions = sorted({row["source_version_id"] for row in pages.values()})
    if len(versions) != 1:
        raise ValueError("DOCUMENT_DISCOVERY_SOURCE_VERSION_REGISTRY_REQUIRED")
    source_version_id = versions[0]

    job_id = "DGJ-" + secrets.token_hex(12)
    job = {
        "state": "QUEUED",
        "job_id": job_id,
        "project_id": project_id,
        "source_id": source_id,
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "created_at": _now(),
        "updated_at": _now(),
        "session_id": None,
        "reason": None,
        "worker_mode": None,
        "fallback_used": False,
        "signal_recovery_used": False,
        "quality_status": None,
        "minimum_page_coverage_ratio": None,
        "teaching_enabled": False,
    }
    queued = _public(dict(job))
    with JOB_LOCK:
        while len(JOBS) >= MAX_JOBS:
            terminal = [key for key, row in JOBS.items() if row["state"] in {"READY", "INCONCLUSIVE", "FAILED"}]
            oldest = min(terminal or list(JOBS), key=lambda key: JOBS[key]["updated_at"])
            JOBS.pop(oldest, None)
        JOBS[job_id] = job

    EXECUTOR.submit(
        _run,
        job_id,
        payload,
        project_id,
        source_id,
        source_version_id,
        digest,
        pages,
    )
    return queued


def governed_job_status(job_id: str) -> dict[str, Any]:
    job_id = discovery._text(job_id, "job_id")
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            raise ValueError("DOCUMENT_DISCOVERY_GOVERNED_JOB_NOT_FOUND")
        return _public(dict(job))
