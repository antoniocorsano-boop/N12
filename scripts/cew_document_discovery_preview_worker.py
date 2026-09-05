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
also produces bounded page inspection artifacts and independent blank-page
corroboration inside this same isolated boundary. If the normal raster evidence
pass returns zero primitives while independent evidence proves that content is
present, a deterministic adaptive signal-recovery pass is allowed inside the
same bounded worker before the result is exposed to the web process.

The worker never creates project truth, learning receipts, canonical writes,
structural identity or engineering effects.
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
    """Bound child memory before importing PyMuPDF or any PDF parser."""
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


def _corroborated_content_without_candidates(report: dict) -> bool:
    if int(report.get("primitive_candidate_count") or 0) != 0:
        return False
    for page in report.get("pages") or []:
        if not isinstance(page, dict):
            continue
        witness = page.get("blank_corroboration")
        if isinstance(witness, dict) and witness.get("state") == "CONTENT_PRESENT":
            return True
    return False


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
        # Imported only after RLIMIT_AS has been applied. This module uses
        # PyMuPDF for bounded inspection JPEGs and blank corroboration.
        import cew_document_discovery_preview_trust as preview_trust

        payload = input_path.read_bytes()
        report = engine.preacquire_preview_pdf(
            payload,
            source_version_id=source_version_id,
            expected_sha256=expected_sha256,
        )
        report = preview_trust.attach_trust_evidence(payload, report)

        if mode == RASTER_SAFE_MODE and _corroborated_content_without_candidates(report):
            import cew_document_discovery_raster_signal_recovery as signal_recovery

            prior_report = report
            report = signal_recovery.preacquire_preview_pdf(
                payload,
                source_version_id=source_version_id,
                expected_sha256=expected_sha256,
                prior_report=prior_report,
            )
            report = preview_trust.attach_trust_evidence(payload, report)
            report["preview_signal_recovery_used"] = True
            report["preview_signal_recovery_trigger"] = "BLANK_CORROBORATION_CONTRADICTED"
        else:
            report["preview_signal_recovery_used"] = False

        report["preview_worker_mode"] = mode
        report["preview_worker_memory_limit_mb"] = _memory_limit_mb()
        report["preview_page_render_boundary"] = "PROCESS_ISOLATED_WORKER"
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
