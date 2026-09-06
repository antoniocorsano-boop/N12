#!/usr/bin/env python3
"""Regression gate for independent PDFium recovery and reading-aid fidelity."""
from __future__ import annotations

from pathlib import Path

import pymupdf

import cew_document_discovery_preview_jobs as jobs
import cew_document_discovery_preview_trust as trust
import cew_document_discovery_pdfium_signal_recovery as recovery


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


def _cropbox_exclusion_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=600, height=800)
    page.draw_rect(pymupdf.Rect(350, 100, 550, 700), color=(0, 0, 0), width=2.0)
    page.draw_line(pymupdf.Point(350, 100), pymupdf.Point(550, 700), color=(0, 0, 0), width=1.0)
    page.set_cropbox(pymupdf.Rect(0, 0, 200, 800))
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


def _insufficient_witness_report() -> dict:
    report = _zero_report()
    report["quality_gate"]["status"] = "INCONCLUSIVE"
    report["quality_gate"]["reasons"] = ["BLANK_CORROBORATION_INSUFFICIENT"]
    report["pages"][0]["blank_corroboration"] = {
        "state": "INSUFFICIENT",
        "blank_confirmed": False,
    }
    return report


def _contradicted_witness_report() -> dict:
    report = _zero_report()
    report["quality_gate"]["status"] = "INCONCLUSIVE"
    report["quality_gate"]["reasons"] = ["BLANK_CORROBORATION_CONTRADICTED"]
    report["pages"][0]["blank_corroboration"] = {
        "state": "CONTENT_PRESENT",
        "blank_confirmed": False,
    }
    return report


def main() -> None:
    assert jobs._signal_recovery_trigger(_insufficient_witness_report()) == "BLANK_CORROBORATION_INSUFFICIENT"
    assert jobs._needs_signal_recovery(_insufficient_witness_report()) is True
    assert jobs._signal_recovery_trigger(_contradicted_witness_report()) == "BLANK_CORROBORATION_CONTRADICTED"
    confirmed_blank = _zero_report()
    confirmed_blank["quality_gate"]["blank_pages_observed"] = [0]
    confirmed_blank["pages"][0]["blank_corroboration"] = {"state": "CONFIRMED_BLANK", "blank_confirmed": True}
    assert jobs._needs_signal_recovery(confirmed_blank) is False

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
    assert first["preview_fallback_mode"] == "PDFIUM_INDEPENDENT_RASTER_SIGNAL_RECOVERY_V1"
    assert first["quality_gate"]["minimum_page_coverage_ratio"] == 1.0
    assert first["primitive_candidate_count"] > 0, first["quality_gate"]
    assert first["graphic_cluster_count"] > 0
    assert all(page["coverage_ratio"] == 1.0 for page in first["pages"])
    assert all(
        row["detector"] == "PDFIUM_RASTER_ADAPTIVE_SIGNAL_RECOVERY_V1"
        for row in first["primitive_candidates"]
    )
    assert all(row["render_engine"] == "PDFIUM" for row in first["primitive_candidates"])
    assert first["semantic_labels_assigned_automatically"] is False
    assert first["authority"]["canonical_write_authorized"] is False
    assert first["signal_recovery"]["independent_from_baseline_renderer"] is True
    assert first["report_fingerprint"] == second["report_fingerprint"]
    assert [row["candidate_id"] for row in first["primitive_candidates"]] == [
        row["candidate_id"] for row in second["primitive_candidates"]
    ]

    artifact = first["preview_page_images"][0]
    assert artifact["render_boundary"] == "PROCESS_ISOLATED_WORKER"
    assert artifact["render_engine"] == "PDFIUM"
    assert artifact["render_policy"] == "INDEPENDENT_PDFIUM_BOUNDED_READING_AID"
    assert artifact["media_type"] == "image/jpeg"
    assert artifact["byte_count"] > 0

    blank = recovery.preacquire_preview_pdf(
        _blank_pdf(),
        source_version_id="RECOVERY-BLANK-CONTROL",
    )
    assert blank["primitive_candidate_count"] == 0
    assert blank["quality_gate"]["status"] == "INCONCLUSIVE"
    assert "PDFIUM_RECOVERY_NO_GRAPHIC_REGIONS" in blank["quality_gate"]["reasons"]

    crop = recovery.preacquire_preview_pdf(
        _cropbox_exclusion_pdf(),
        source_version_id="RECOVERY-CROPBOX-EXCLUSION",
    )
    assert crop["primitive_candidate_count"] > 0, crop["quality_gate"]
    assert crop["pages"][0]["render_scope"] == "MEDIA_BOX_RECOVERY"
    assert crop["pages"][0]["media_box_probe_used"] is True
    assert crop["quality_gate"]["status"] == "INCONCLUSIVE"
    assert "VISIBLE_CROPBOX_EXCLUDES_RECOVERED_SIGNAL" in crop["quality_gate"]["reasons"]
    assert crop["preview_page_images"][0]["render_scope"] == "MEDIA_BOX_RECOVERY"

    reading_aid = trust.attach_trust_evidence(faint, _zero_report())
    baseline_artifact = reading_aid["preview_page_images"][0]
    assert baseline_artifact["render_boundary"] == "PROCESS_ISOLATED_WORKER"
    assert baseline_artifact["render_policy"] == "BOUNDED_CONTRAST_PRESERVING_READING_AID"
    assert baseline_artifact["display_enhancement"] in {"GRAYSCALE_GAMMA", "NONE"}
    assert reading_aid["preview_page_reading_aid_policy"] == "CONTRAST_PRESERVING_DECLARED_TRANSFORM"

    worker = Path("cew_document_discovery_preview_worker.py").read_text(encoding="utf-8")
    jobs_source = Path("cew_document_discovery_preview_jobs.py").read_text(encoding="utf-8")
    trust_source = Path("cew_document_discovery_preview_trust.py").read_text(encoding="utf-8")
    assert 'RASTER_SIGNAL_RECOVERY_MODE = "RASTER_SIGNAL_RECOVERY"' in worker
    assert "cew_document_discovery_pdfium_signal_recovery" in worker
    assert "PRIOR_REPORT_FILENAME" in worker
    assert "_inherit_trust_evidence" in worker
    assert 'if key not in report and key in prior' in worker
    assert "preview_trust.attach_trust_evidence" in worker
    assert 'RASTER_SIGNAL_RECOVERY_MODE = "RASTER_SIGNAL_RECOVERY"' in jobs_source
    assert "_signal_recovery_trigger" in jobs_source
    assert "BLANK_CORROBORATION_CONTRADICTED" in jobs_source
    assert "BLANK_CORROBORATION_INSUFFICIENT" in jobs_source
    assert "PREVIEW_SIGNAL_RECOVERY_TIMEOUT_SECONDS" in jobs_source
    assert "DOCUMENT_DISCOVERY_SIGNAL_RECOVERY_DEGRADED" in jobs_source
    assert "get_image_info()" in trust_source
    assert "get_images(full=True)" not in trust_source

    print("CEW_PDFIUM_SIGNAL_RECOVERY_PASS")
    print("independent_renderer=PDFIUM faint_line_recovery=PASS deterministic_replay=PASS")
    print("insufficient_blank_witness_trigger=PASS confirmed_blank_excluded=PASS")
    print("cropbox_media_probe=PASS recovery_artifact=PDFIUM_JPEG")
    print("displayed_image_witness=PASS baseline_evidence_preservation=GOVERNED")
    print("semantic_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
