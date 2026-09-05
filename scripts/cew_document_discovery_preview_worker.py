#!/usr/bin/env python3
"""Isolated extraction worker for CEW Document Discovery preview.

This module is executed in a separate Python process. It performs only bounded
preview extraction inside a supervisor-created private temporary directory. The
worker never accepts filesystem paths from its command line: it reads the fixed
``source.pdf`` input and atomically writes the fixed ``report.json`` output in
its current working directory. This keeps the process boundary both resource-
bounded and path-confined.

The worker applies a hard address-space ceiling before importing PyMuPDF so a
pathological vector page cannot exhaust the whole Render service container. It
never creates project truth, learning receipts, canonical writes or session
state. The web process remains authoritative for transient job/session state.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

VECTOR_MODE = "VECTOR_BOUNDED"
RASTER_SAFE_MODE = "RASTER_SAFE"
DEFAULT_MEMORY_LIMIT_MB = 192
INPUT_FILENAME = "source.pdf"
OUTPUT_FILENAME = "report.json"
TEMP_OUTPUT_FILENAME = "report.json.tmp"


def _lower_priority() -> None:
    """Prefer the web process under CPU contention on constrained runtimes."""
    try:
        os.nice(10)
    except (AttributeError, OSError):
        pass


def _memory_limit_mb() -> int:
    raw = str(os.environ.get("CEW_PREVIEW_WORKER_MEMORY_MB", DEFAULT_MEMORY_LIMIT_MB)).strip()
    try:
        value = int(raw)
    except ValueError:
        value = DEFAULT_MEMORY_LIMIT_MB
    return max(96, min(value, 384))


def _apply_resource_limits() -> None:
    """Bound child memory before importing PyMuPDF.

    RLIMIT_AS is Linux/POSIX-specific. If unavailable, process isolation and the
    supervisor timeout remain active; the worker does not escalate authority.
    """
    try:
        import resource

        limit_bytes = _memory_limit_mb() * 1024 * 1024
        _current_soft, current_hard = resource.getrlimit(resource.RLIMIT_AS)
        infinity = resource.RLIM_INFINITY
        hard = limit_bytes if current_hard == infinity else min(current_hard, limit_bytes)
        soft = min(limit_bytes, hard)
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
    except (ImportError, OSError, ValueError):
        pass


def _engine(mode: str):
    if mode == VECTOR_MODE:
        import cew_document_discovery_preview_engine as engine
        return engine
    if mode == RASTER_SAFE_MODE:
        import cew_document_discovery_raster_preview_engine as engine
        return engine
    raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_WORKER_MODE_INVALID")


def main(argv: list[str]) -> int:
    if len(argv) not in {3, 4}:
        print("DOCUMENT_DISCOVERY_PREVIEW_WORKER_ARGUMENTS_INVALID", file=sys.stderr)
        return 64

    _, source_version_id, expected_sha256, *rest = argv
    mode = rest[0] if rest else VECTOR_MODE
    input_path = Path(INPUT_FILENAME)
    output_path = Path(OUTPUT_FILENAME)
    temp_output = Path(TEMP_OUTPUT_FILENAME)

    _lower_priority()
    _apply_resource_limits()

    try:
        engine = _engine(mode)
        payload = input_path.read_bytes()
        report = engine.preacquire_preview_pdf(
            payload,
            source_version_id=source_version_id,
            expected_sha256=expected_sha256,
        )
        report["preview_worker_mode"] = mode
        report["preview_worker_memory_limit_mb"] = _memory_limit_mb()
        temp_output.write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temp_output, output_path)
        return 0
    except MemoryError:
        try:
            temp_output.unlink(missing_ok=True)
        except OSError:
            pass
        print("DOCUMENT_DISCOVERY_PREVIEW_WORKER_MEMORY_LIMIT", file=sys.stderr)
        return 75
    except Exception:
        try:
            temp_output.unlink(missing_ok=True)
        except OSError:
            pass
        # Do not expose exception types/messages from parsing untrusted PDFs.
        print("DOCUMENT_DISCOVERY_PREVIEW_WORKER_INTERNAL_ERROR", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
