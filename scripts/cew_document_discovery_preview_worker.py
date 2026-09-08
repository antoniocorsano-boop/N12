#!/usr/bin/env python3
"""Isolated extraction worker for CEW Document Discovery preview.

This module is executed in a separate Python process. It performs only bounded
preview extraction inside a supervisor-created private temporary directory. The
worker never accepts filesystem paths from its command line: it reads fixed
files in its current working directory and atomically writes ``report.json``.

MuPDF stages use a strict RLIMIT_AS ceiling. PDFium recovery uses a larger
virtual-address ceiling because Chromium/PDFium PartitionAlloc reserves large
virtual regions independently from resident raster memory. Actual recovery work
remains bounded by the engine pixel/page limits, subprocess timeout, single-worker
supervision and the hosting cgroup. This avoids treating virtual address-space
reservation as if it were resident memory consumption.

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
RASTER_SIGNAL_RECOVERY_MODE = "RASTER_SIGNAL_RECOVERY"
DEFAULT_MEMORY_LIMIT_MB = 192
PDFIUM_ADDRESS_SPACE_LIMIT_MB = 8192
INPUT_FILENAME = "source.pdf"
OUTPUT_FILENAME = "report.json"
TEMP_OUTPUT_FILENAME = "report.json.tmp"
PRIOR_REPORT_FILENAME = "prior_report.json"


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


def _pdfium_address_space_limit_mb() -> int:
    raw = str(
        os.environ.get(
            "CEW_PREVIEW_PDFIUM_ADDRESS_SPACE_MB",
            PDFIUM_ADDRESS_SPACE_LIMIT_MB,
        )
    ).strip()
    try:
        value = int(raw)
    except ValueError:
        value = PDFIUM_ADDRESS_SPACE_LIMIT_MB
    # Chromium PartitionAlloc exercises address-space-limited POSIX builds with
    # multi-gigabyte limits. Keep a governed floor while avoiding infinity.
    return max(6144, min(value, 16384))


def _address_space_limit_mb(mode: str) -> int:
    if mode == RASTER_SIGNAL_RECOVERY_MODE:
        return _pdfium_address_space_limit_mb()
    return _memory_limit_mb()


def _apply_resource_limits(mode: str) -> None:
    """Bound child virtual address space using a renderer-compatible policy."""
    try:
        import resource

        limit_bytes = _address_space_limit_mb(mode) * 1024 * 1024
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
    if mode == RASTER_SIGNAL_RECOVERY_MODE:
        import cew_document_discovery_pdfium_signal_recovery as engine
        return engine
    raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_WORKER_MODE_INVALID")


def _read_prior_report() -> dict:
    path = Path(PRIOR_REPORT_FILENAME)
    if not path.is_file():
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_PRIOR_REPORT_MISSING")
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_PRIOR_REPORT_INVALID")
    return report


def _inherit_trust_evidence(prior: dict, report: dict) -> dict:
    """Reuse trust evidence without overwriting a stronger recovery artifact."""
    for key in (
        "preview_page_image_mode",
        "preview_page_artifact_count",
        "preview_page_images",
    ):
        if key not in report and key in prior:
            report[key] = prior[key]

    prior_pages = {
        int(row.get("page_index", -1)): row
        for row in (prior.get("pages") or [])
        if isinstance(row, dict)
    }
    for page in report.get("pages") or []:
        if not isinstance(page, dict):
            continue
        prior_page = prior_pages.get(int(page.get("page_index", -1)))
        if not isinstance(prior_page, dict):
            continue
        if "blank_corroboration" in prior_page:
            page["blank_corroboration"] = prior_page["blank_corroboration"]

    report["preview_signal_recovery_used"] = True
    report["preview_signal_recovery_trigger"] = (
        prior.get("preview_signal_recovery_trigger")
        or "ZERO_CANDIDATES_INDEPENDENT_RECOVERY"
    )
    report["preview_signal_recovery_prior_fingerprint"] = prior.get("report_fingerprint")
    return report


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
    _apply_resource_limits(mode)

    try:
        engine = _engine(mode)
        payload = input_path.read_bytes()

        if mode == RASTER_SIGNAL_RECOVERY_MODE:
            prior_report = _read_prior_report()
            report = engine.preacquire_preview_pdf(
                payload,
                source_version_id=source_version_id,
                expected_sha256=expected_sha256,
                prior_report=prior_report,
            )
            report = _inherit_trust_evidence(prior_report, report)
        else:
            report = engine.preacquire_preview_pdf(
                payload,
                source_version_id=source_version_id,
                expected_sha256=expected_sha256,
            )
            # Imported only after the renderer-compatible RLIMIT_AS policy has
            # been applied. Trust evidence is attached once to the baseline
            # result and reused by recovery.
            import cew_document_discovery_preview_trust as preview_trust

            report = preview_trust.attach_trust_evidence(payload, report)
            report["preview_signal_recovery_used"] = False

        report["preview_worker_mode"] = mode
        report["preview_worker_memory_limit_mb"] = _memory_limit_mb()
        report["preview_worker_address_space_limit_mb"] = _address_space_limit_mb(mode)
        report["preview_worker_resource_policy"] = (
            "PDFIUM_MULTI_GB_VIRTUAL_ADDRESS_WITH_BOUNDED_RASTER"
            if mode == RASTER_SIGNAL_RECOVERY_MODE
            else "STRICT_RLIMIT_AS"
        )
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
