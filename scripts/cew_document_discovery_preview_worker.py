#!/usr/bin/env python3
"""Isolated extraction worker for CEW Document Discovery preview.

This module is executed in a separate Python process. It performs only bounded
preview extraction and writes the derived report to an isolated temporary file.
It never creates project truth, learning receipts, canonical writes or session
state. The web process remains authoritative for transient job/session state.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import cew_document_discovery_preview_engine as preview_engine


def _lower_priority() -> None:
    """Prefer the web process under CPU contention on constrained runtimes."""
    try:
        os.nice(10)
    except (AttributeError, OSError):
        pass


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print("DOCUMENT_DISCOVERY_PREVIEW_WORKER_ARGUMENTS_INVALID", file=sys.stderr)
        return 64

    _, input_path_raw, output_path_raw, source_version_id, expected_sha256 = argv
    input_path = Path(input_path_raw)
    output_path = Path(output_path_raw)
    temp_output = output_path.with_suffix(output_path.suffix + ".tmp")

    _lower_priority()

    try:
        payload = input_path.read_bytes()
        report = preview_engine.preacquire_preview_pdf(
            payload,
            source_version_id=source_version_id,
            expected_sha256=expected_sha256,
        )
        temp_output.write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temp_output, output_path)
        return 0
    except Exception as exc:
        try:
            temp_output.unlink(missing_ok=True)
        except OSError:
            pass
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
