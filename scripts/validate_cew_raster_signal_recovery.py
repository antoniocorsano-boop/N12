#!/usr/bin/env python3
"""Regression gate for adaptive faint-line raster recovery and reading-aid fidelity."""
from __future__ import annotations

from pathlib import Path

import pymupdf

import cew_document_discovery_preview_trust as trust
import cew_document_discovery_raster_signal_recovery as recovery


def _faint_technical_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=3600)
    faint = (0.96, 0.96, 0.96)
    for y in range(80, 3520, 120):
        page.draw_line(
            pymupdf.Point(24, y),
            pymupdf.Point(276, y),
            color=faint,
            width=0.30,
        )
    for x in range(30, 280, 35):
        page.draw_line(
            pymupdf.Point(x, 60),
            pymupdf.Point(x, 3540),
            color=faint,
            width=0.25,
        )
    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


def _blank_pdf() -> bytes:
    doc = pymupdf.open()
    doc.new_page(width=300, height=3600)
    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


def _zero_report() -> dict:
    return {
        "page_count": 1,
        "pages": [{
            "page_index": 0,
            "coverage_ratio": 1.0,
            "tiles_failed": 0,
            "primitive_candidate_count": 0,
            "quality_status": "READY",
            "quality_reasons": [],
            "page_observation_state": "RASTER_SIGNAL_ABSENT",
        }],
        "primitive_candidate_count": 0,
        "primitive_candidates": [],
        "graphic_cluster_count": 0,
        "graphic_clusters": [],
        "quality_gate": {
            "status": "READY",
            "reasons": [],
            "minimum_page_coverage_ratio": 1.0,
            "blank_pages_observed": [],
        },
        "analysis_completeness": "FULL_REQUIRED_COVERAGE",
    }


def main() -> None:
    faint = _faint_technical_pdf()
    first = recovery.preacquire_preview_pdf(
        faint,
        source_version_id="RECOVERY-FAINT-TECHNICAL",
    )
    second = recovery.preacquire_preview_pdf(
        faint,
        source_version_id="RECOVERY-FAINT-TECHNICAL",
    )
    assert first["recovery_schema"] == recovery.RECOVERY_SCHEMA
    assert first["preview_fallback_mode"] == "RASTER_TILED_ADAPTIVE_SIGNAL_RECOVERY_V1"
    assert first["quality_gate"]["minimum_page_coverage_ratio"] == 1.0
    assert first["primitive_candidate_count"] > 0, first["quality_gate"]
    assert first["graphic_cluster_count"] > 0
    assert all(page["tiles_failed"] == 0 for page in first["pages"])
    assert all(page["coverage_ratio"] == 1.0 for page in first["pages"])
    assert all(
        row["detector"] == "PYMUPDF_RASTER_ADAPTIVE_SIGNAL_RECOVERY_V1"
        for row in first["primitive_candidates"]
    )
    assert first["semantic_labels_assigned_automatically"] is False
    assert first["authority"]["canonical_write_authorized"] is False
    assert first["report_fingerprint"] == second["report_fingerprint"]
    assert [row["candidate_id"] for row in first["primitive_candidates"]] == [
        row["candidate_id"] for row in second["primitive_candidates"]
    ]

    blank = recovery.preacquire_preview_pdf(
        _blank_pdf(),
        source_version_id="RECOVERY-BLANK-CONTROL",
    )
    assert blank["primitive_candidate_count"] == 0
    assert blank["quality_gate"]["status"] == "INCONCLUSIVE"
    assert "RASTER_RECOVERY_NO_GRAPHIC_REGIONS" in blank["quality_gate"]["reasons"]

    reading_aid = trust.attach_trust_evidence(faint, _zero_report())
    artifact = reading_aid["preview_page_images"][0]
    assert artifact["render_boundary"] == "PROCESS_ISOLATED_WORKER"
    assert artifact["render_policy"] == "BOUNDED_CONTRAST_PRESERVING_READING_AID"
    assert artifact["display_enhancement"] in {"GRAYSCALE_GAMMA", "NONE"}
    assert reading_aid["preview_page_reading_aid_policy"] == "CONTRAST_PRESERVING_DECLARED_TRANSFORM"

    worker = Path("cew_document_discovery_preview_worker.py").read_text(encoding="utf-8")
    assert "_corroborated_content_without_candidates" in worker
    assert "cew_document_discovery_raster_signal_recovery" in worker
    assert "BLANK_CORROBORATION_CONTRADICTED" in worker
    assert worker.index("preview_trust.attach_trust_evidence") < worker.index("cew_document_discovery_raster_signal_recovery")

    print("CEW_RASTER_SIGNAL_RECOVERY_PASS")
    print("faint_line_recovery=PASS full_coverage=PASS deterministic_replay=PASS")
    print("blank_control=INCONCLUSIVE reading_aid_transform=DECLARED")
    print("semantic_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
