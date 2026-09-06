#!/usr/bin/env python3
"""Regression gate for preview render isolation and blank corroboration."""
from __future__ import annotations

import base64
from pathlib import Path

import pymupdf

import cew_document_discovery_preview_safe_jobs as safe_jobs
import cew_document_discovery_preview_trust as trust


def _pdf(width: float, height: float, *, text: str | None = None) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=width, height=height)
    if text:
        page.insert_text((20, 30), text, fontsize=9)
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
            "page_observation_state": "PAGE_BLANK_OBSERVED",
        }],
        "primitive_candidate_count": 0,
        "primitive_candidates": [],
        "graphic_cluster_count": 0,
        "graphic_clusters": [],
        "quality_gate": {
            "status": "READY",
            "reasons": [],
            "minimum_page_coverage_ratio": 1.0,
            "blank_pages_observed": [0],
        },
        "analysis_completeness": "FULL_REQUIRED_COVERAGE",
    }


def _assert_artifact(report: dict) -> None:
    assert report["preview_page_image_mode"] == "PROCESS_ISOLATED_BOUNDED_JPEG"
    assert report["preview_page_artifact_count"] == 1
    artifact = report["preview_page_images"][0]
    assert artifact["render_boundary"] == "PROCESS_ISOLATED_WORKER"
    payload = base64.b64decode(artifact["data_base64"], validate=True)
    assert payload.startswith(b"\xff\xd8")
    assert len(payload) == artifact["byte_count"]


def main() -> None:
    blank = trust.attach_trust_evidence(_pdf(842, 595), _zero_report())
    _assert_artifact(blank)
    assert blank["quality_gate"]["status"] == "READY"
    assert blank["quality_gate"]["blank_pages_observed"] == [0]
    witness = blank["pages"][0]["blank_corroboration"]
    assert witness["state"] == "CONFIRMED_BLANK", witness
    assert witness["blank_confirmed"] is True

    elongated_blank = trust.attach_trust_evidence(_pdf(300, 3600), _zero_report())
    _assert_artifact(elongated_blank)
    assert elongated_blank["quality_gate"]["status"] == "INCONCLUSIVE"
    assert "BLANK_CORROBORATION_INSUFFICIENT" in elongated_blank["quality_gate"]["reasons"]
    assert elongated_blank["quality_gate"]["blank_pages_observed"] == []
    assert elongated_blank["pages"][0]["page_observation_state"] == "BLANK_NOT_PROVEN"

    elongated_content = trust.attach_trust_evidence(
        _pdf(300, 3600, text="TECHNICAL DRAWING CONTENT"),
        _zero_report(),
    )
    _assert_artifact(elongated_content)
    assert elongated_content["quality_gate"]["status"] == "INCONCLUSIVE"
    assert "BLANK_CORROBORATION_CONTRADICTED" in elongated_content["quality_gate"]["reasons"]
    witness = elongated_content["pages"][0]["blank_corroboration"]
    assert witness["state"] == "CONTENT_PRESENT", witness
    assert witness["text_block_count"] > 0
    assert elongated_content["quality_gate"]["blank_pages_observed"] == []

    safe_source = Path("cew_document_discovery_preview_safe_jobs.py").read_text(encoding="utf-8")
    worker_source = Path("cew_document_discovery_preview_worker.py").read_text(encoding="utf-8")
    async_source = Path("cew_document_discovery_async_preview.py").read_text(encoding="utf-8")
    assert "discovery._validate_pdf(payload)" not in safe_source
    assert "_validate_upload_envelope(payload)" in safe_source
    assert "preview_trust.attach_trust_evidence" in worker_source
    assert worker_source.index("_apply_resource_limits(mode)") < worker_source.index("import cew_document_discovery_preview_trust")
    assert "cew_document_discovery_preview_safe_jobs as preview_jobs" in async_source
    assert "X-CEW-Preview-Page-Render" in async_source
    assert "PROCESS_ISOLATED_CACHED" in async_source
    assert "preview_page_images" in async_source

    # Byte-envelope validation must reject malformed user uploads without
    # invoking a PDF parser in the web process.
    try:
        safe_jobs._validate_upload_envelope(b"not-a-pdf")
    except ValueError:
        pass
    else:
        raise AssertionError("malformed preview upload was not rejected")

    print("CEW_PREVIEW_TRUST_BOUNDARY_PASS")
    print("web_user_pdf_parse=FORBIDDEN page_render=PROCESS_ISOLATED_CACHED")
    print("blank=CORROBORATED extreme_aspect_blank=INCONCLUSIVE contradictory_content=INCONCLUSIVE")
    print("renderer_compatible_resource_limits=PASS")
    print("semantic_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
