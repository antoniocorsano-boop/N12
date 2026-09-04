#!/usr/bin/env python3
"""Regression gate for async/resource-bounded CEW Document Discovery preview."""
from __future__ import annotations

from pathlib import Path
import tempfile
import time

import pymupdf

import cew_document_discovery as discovery
import cew_document_discovery_async_preview as async_preview
import cew_document_discovery_preview_engine as preview_engine
import cew_document_discovery_raster_preview_engine as raster_preview_engine
import cew_document_discovery_preview_jobs as preview_jobs


def _pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=842, height=595)
    for i in range(24):
        x = 30 + (i % 8) * 95
        y = 45 + (i // 8) * 150
        page.draw_rect(pymupdf.Rect(x, y, x + 35, y + 35), color=(0, 0, 0), width=0.7)
        page.draw_line(pymupdf.Point(x - 10, y + 17), pymupdf.Point(x + 45, y + 17), color=(0, 0, 0), width=0.4)
    page.insert_text((50, 560), "ASYNC BOUNDED PREVIEW TEST", fontsize=10)
    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


def _wait(job_id: str, timeout_seconds: float = 30.0) -> dict:
    deadline = time.time() + timeout_seconds
    current = preview_jobs.preview_job_status(job_id)
    while time.time() < deadline:
        current = preview_jobs.preview_job_status(job_id)
        if current["state"] in {"READY", "FAILED"}:
            return current
        time.sleep(0.05)
    raise AssertionError(f"preview job did not terminate: {current}")


def main() -> None:
    payload = _pdf()
    discovery.clear_sessions()
    preview_jobs.clear_jobs()

    report = preview_engine.preacquire_preview_pdf(
        payload,
        source_version_id="PREVIEW-ASYNC-TEST",
    )
    assert report["analysis_scope"] == "BOUNDED_INTERACTIVE_PREVIEW"
    assert report["preview_budget"]["max_pages_analyzed"] == preview_engine.MAX_PREVIEW_PAGES_ANALYZED
    assert report["preview_budget"]["max_total_candidates"] == preview_engine.MAX_TOTAL_CANDIDATES
    assert report["semantic_labels_assigned_automatically"] is False
    assert report["authority"]["canonical_write_authorized"] is False
    assert report["primitive_candidate_count"] > 0
    assert all(
        row["detector"] != "PYMUPDF_GET_DRAWINGS"
        for row in report["primitive_candidates"]
        if row["primitive_family"] != "TEXT_BLOCK"
    )

    raster_report = raster_preview_engine.preacquire_preview_pdf(
        payload,
        source_version_id="PREVIEW-RASTER-SAFE-TEST",
    )
    assert raster_report["analysis_scope"] == "BOUNDED_INTERACTIVE_PREVIEW"
    assert raster_report["preview_fallback_mode"] == "RASTER_SAFE_RESOURCE_BOUNDED"
    assert raster_report["semantic_labels_assigned_automatically"] is False
    assert raster_report["authority"]["canonical_write_authorized"] is False
    assert raster_report["primitive_candidate_count"] > 0
    assert any(
        row["detector"] == "PYMUPDF_RASTER_INK_TILE_BOUNDED"
        for row in raster_report["primitive_candidates"]
    )

    job = preview_jobs.start_preview_job(payload, "HVA-DISCOVERY-ASYNC-TEST")
    assert job["state"] == "QUEUED"
    assert job["session_id"] is None
    assert job["execution_boundary"] == "PROCESS_ISOLATED_SUBPROCESS"
    assert job["teaching_enabled"] is False

    current = _wait(job["job_id"])
    assert current["state"] == "READY", current
    assert current["session_id"]
    assert current["execution_boundary"] == "PROCESS_ISOLATED_SUBPROCESS"
    assert current["preview_worker_mode"] in {preview_jobs.VECTOR_MODE, preview_jobs.RASTER_SAFE_MODE}

    status = discovery.status(current["session_id"])
    assert status["source_registration_state"] == "UNREGISTERED_PREVIEW"
    assert status["teaching_enabled"] is False
    assert status["teaching_blocker"] == "IMMUTABLE_SOURCE_AND_READY_PAGE_REGISTRATION_REQUIRED"
    assert status["semantic_labels_assigned_automatically"] is False
    assert status["authority"]["canonical_write_authorized"] is False
    assert status["authority"]["structural_identity_authorized"] is False

    # If both vector and raster-safe child executions fail, only the preview job
    # fails. The validator remains alive and authority remains fail-closed.
    original_worker = preview_jobs.WORKER_SCRIPT
    with tempfile.TemporaryDirectory(prefix="cew-preview-worker-failure-test-") as tmp:
        failing_worker = Path(tmp) / "fail_worker.py"
        failing_worker.write_text("raise SystemExit(7)\n", encoding="utf-8")
        preview_jobs.WORKER_SCRIPT = failing_worker
        preview_jobs.clear_jobs()
        failed_job = preview_jobs.start_preview_job(payload, "HVA-DISCOVERY-WORKER-FAILURE-TEST")
        preview_jobs.WORKER_SCRIPT = original_worker
        failed = _wait(failed_job["job_id"])
        assert failed["state"] == "FAILED", failed
        assert failed["reason"] == (
            "DOCUMENT_DISCOVERY_PREVIEW_RASTER_FALLBACK_FAILED:"
            "DOCUMENT_DISCOVERY_PREVIEW_WORKER_EXIT_7"
        ), failed
        assert failed["preview_fallback_used"] is True
        assert failed["session_id"] is None
        assert discovery.provider_states()["structured_graphic"]["state"] == "READY"

    html = async_preview._patched_page()
    assert "/api/workbench/document-discovery/analyze-preview-async" in html
    assert "/api/workbench/document-discovery/preview-job/" in html
    assert "waitPreviewJob" in html
    assert "Accodamento analisi" in html
    assert "body:f" in html
    assert "arrayBuffer()" not in html

    router = async_preview.build_router()
    paths = [route.path for route in router.routes]
    assert paths[0] == "/workbench/document-discovery"
    assert "/api/workbench/document-discovery/analyze-preview-async" in paths
    assert "/api/workbench/document-discovery/preview-job/{job_id}" in paths

    composition = Path("cew_professional_workbench_api.py").read_text(encoding="utf-8")
    async_mount = "router.include_router(_document_discovery_async_preview.build_router())"
    legacy_mount = "router.include_router(_document_discovery.build_router(source_workspace))"
    assert async_mount in composition
    assert legacy_mount in composition
    assert composition.index(async_mount) < composition.index(legacy_mount)

    engine_source = Path("cew_document_discovery_preview_engine.py").read_text(encoding="utf-8")
    raster_source = Path("cew_document_discovery_raster_preview_engine.py").read_text(encoding="utf-8")
    assert "page.get_cdrawings()" in engine_source
    assert "MAX_VECTOR_PATHS_PER_PAGE" in engine_source
    assert "MAX_TOTAL_CANDIDATES" in engine_source
    assert "page.get_pixmap(" in raster_source
    assert "PYMUPDF_RASTER_INK_TILE_BOUNDED" in raster_source
    assert "RASTER_SAFE_RESOURCE_BOUNDED" in raster_source

    jobs_source = Path("cew_document_discovery_preview_jobs.py").read_text(encoding="utf-8")
    worker_source = Path("cew_document_discovery_preview_worker.py").read_text(encoding="utf-8")
    assert "subprocess.run(" in jobs_source
    assert "PROCESS_ISOLATED_SUBPROCESS" in jobs_source
    assert "PREVIEW_VECTOR_TIMEOUT_SECONDS" in jobs_source
    assert "PREVIEW_RASTER_TIMEOUT_SECONDS" in jobs_source
    assert "RASTER_SAFE_MODE" in jobs_source
    assert "DOCUMENT_DISCOVERY_PREVIEW_RASTER_FALLBACK_FAILED" in jobs_source
    assert "preview_engine.preacquire_preview_pdf" not in jobs_source
    assert "resource.RLIMIT_AS" in worker_source
    assert "CEW_PREVIEW_WORKER_MEMORY_MB" in worker_source
    assert "cew_document_discovery_preview_engine" in worker_source
    assert "cew_document_discovery_raster_preview_engine" in worker_source
    assert "os.nice(10)" in worker_source

    print("CEW_DOCUMENT_DISCOVERY_ASYNC_PREVIEW_PASS")
    print("http_boundary=ENQUEUE_THEN_POLL gateway_wait=DECOUPLED")
    print("worker_boundary=PROCESS_ISOLATED_SUBPROCESS memory_ceiling=ENFORCED")
    print("vector_failure=RASTER_SAFE_RESOURCE_BOUNDED_FALLBACK")
    print("preview_training=BLOCKED semantic_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
