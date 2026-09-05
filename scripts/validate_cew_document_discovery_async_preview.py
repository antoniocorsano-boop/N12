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
        if current["state"] in {"READY", "INCONCLUSIVE", "FAILED"}:
            return current
        time.sleep(0.05)
    raise AssertionError(f"preview job did not terminate: {current}")


def _fake_empty_then_raster_worker(path: Path) -> None:
    path.write_text(
        "import json, sys\n"
        "_, source_version_id, digest, mode = sys.argv\n"
        "primitive_count = 0 if mode == 'VECTOR_BOUNDED' else 1\n"
        "cluster_count = 0 if primitive_count == 0 else 1\n"
        "report = {\n"
        "    'analysis_scope': 'BOUNDED_INTERACTIVE_PREVIEW',\n"
        "    'source_sha256': digest,\n"
        "    'source_version_id': source_version_id,\n"
        "    'page_count': 1,\n"
        "    'primitive_candidate_count': primitive_count,\n"
        "    'graphic_cluster_count': cluster_count,\n"
        "    'preview_worker_mode': mode,\n"
        "    'quality_gate': {'status': 'READY', 'reasons': [], 'minimum_page_coverage_ratio': 1.0, 'blank_pages_observed': []} if mode == 'RASTER_SAFE' else None,\n"
        "}\n"
        "open('report.json', 'w', encoding='utf-8').write(json.dumps(report))\n",
        encoding="utf-8",
    )


def _fake_inconclusive_worker(path: Path) -> None:
    path.write_text(
        "import json, sys\n"
        "_, source_version_id, digest, mode = sys.argv\n"
        "report = {\n"
        "    'analysis_scope': 'BOUNDED_INTERACTIVE_PREVIEW',\n"
        "    'source_sha256': digest,\n"
        "    'source_version_id': source_version_id,\n"
        "    'page_count': 1,\n"
        "    'pages': [{'page_index': 0}],\n"
        "    'primitive_candidate_count': 0,\n"
        "    'primitive_candidates': [],\n"
        "    'graphic_cluster_count': 0,\n"
        "    'graphic_clusters': [],\n"
        "    'library_state': 'LIBRARY_NOT_CONFIGURED',\n"
        "    'preview_worker_mode': mode,\n"
        "}\n"
        "if mode == 'RASTER_SAFE': report['quality_gate'] = {'status':'INCONCLUSIVE','reasons':['INCONCLUSIVE_RASTER_DETECTION'],'minimum_page_coverage_ratio':1.0,'blank_pages_observed':[]}\n"
        "open('report.json', 'w', encoding='utf-8').write(json.dumps(report))\n",
        encoding="utf-8",
    )


def main() -> None:
    payload = _pdf()
    discovery.clear_sessions()
    preview_jobs.clear_jobs()

    report = preview_engine.preacquire_preview_pdf(payload, source_version_id="PREVIEW-ASYNC-TEST")
    assert report["analysis_scope"] == "BOUNDED_INTERACTIVE_PREVIEW"
    assert report["preview_budget"]["max_pages_analyzed"] == preview_engine.MAX_PREVIEW_PAGES_ANALYZED
    assert report["preview_budget"]["max_total_candidates"] == preview_engine.MAX_TOTAL_CANDIDATES
    assert report["semantic_labels_assigned_automatically"] is False
    assert report["authority"]["canonical_write_authorized"] is False
    assert report["primitive_candidate_count"] > 0
    assert all(row["detector"] != "PYMUPDF_GET_DRAWINGS" for row in report["primitive_candidates"] if row["primitive_family"] != "TEXT_BLOCK")

    raster_report = raster_preview_engine.preacquire_preview_pdf(payload, source_version_id="PREVIEW-RASTER-EVIDENCE-V2-TEST")
    assert raster_report["analysis_scope"] == "BOUNDED_INTERACTIVE_PREVIEW"
    assert raster_report["raster_contract_schema"] == raster_preview_engine.RASTER_CONTRACT_SCHEMA
    assert raster_report["preview_fallback_mode"] == "RASTER_TILED_EVIDENCE_V2"
    assert raster_report["quality_gate"]["status"] == "READY"
    assert raster_report["quality_gate"]["minimum_page_coverage_ratio"] == 1.0
    assert raster_report["semantic_labels_assigned_automatically"] is False
    assert raster_report["authority"]["canonical_write_authorized"] is False
    assert raster_report["primitive_candidate_count"] > 0
    assert any(row["detector"] == "PYMUPDF_RASTER_CONNECTED_REGION_TILED_V2" for row in raster_report["primitive_candidates"])
    assert all(page["tiles_failed"] == 0 for page in raster_report["pages"])
    assert all(page["coverage_ratio"] == 1.0 for page in raster_report["pages"])

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

    original_worker = preview_jobs.WORKER_SCRIPT
    with tempfile.TemporaryDirectory(prefix="cew-preview-empty-vector-test-") as tmp:
        fake_worker = Path(tmp) / "empty_then_raster_worker.py"
        _fake_empty_then_raster_worker(fake_worker)
        preview_jobs.WORKER_SCRIPT = fake_worker
        preview_jobs.clear_jobs()
        fallback_job = preview_jobs.start_preview_job(payload, "HVA-DISCOVERY-EMPTY-VECTOR-TEST")
        preview_jobs.WORKER_SCRIPT = original_worker
        fallback = _wait(fallback_job["job_id"])
        assert fallback["state"] == "READY", fallback
        assert fallback["preview_fallback_used"] is True, fallback
        assert fallback["preview_worker_mode"] == preview_jobs.RASTER_SAFE_MODE, fallback
        assert fallback["session_id"], fallback
        assert fallback["quality_status"] == "READY"
        assert fallback["minimum_page_coverage_ratio"] == 1.0

    with tempfile.TemporaryDirectory(prefix="cew-preview-inconclusive-test-") as tmp:
        fake_worker = Path(tmp) / "inconclusive_worker.py"
        _fake_inconclusive_worker(fake_worker)
        preview_jobs.WORKER_SCRIPT = fake_worker
        preview_jobs.clear_jobs()
        inconclusive_job = preview_jobs.start_preview_job(payload, "HVA-DISCOVERY-INCONCLUSIVE-TEST")
        preview_jobs.WORKER_SCRIPT = original_worker
        inconclusive = _wait(inconclusive_job["job_id"])
        assert inconclusive["state"] == "INCONCLUSIVE", inconclusive
        assert inconclusive["session_id"], inconclusive
        assert inconclusive["reason"] == "INCONCLUSIVE_RASTER_DETECTION"
        assert inconclusive["preview_fallback_used"] is True
        assert inconclusive["quality_status"] == "INCONCLUSIVE"
        assert inconclusive["minimum_page_coverage_ratio"] == 1.0
        inconclusive_status = discovery.status(inconclusive["session_id"])
        assert inconclusive_status["teaching_enabled"] is False
        assert inconclusive_status["authority"]["canonical_write_authorized"] is False

    with tempfile.TemporaryDirectory(prefix="cew-preview-worker-failure-test-") as tmp:
        failing_worker = Path(tmp) / "fail_worker.py"
        failing_worker.write_text("raise SystemExit(7)\n", encoding="utf-8")
        preview_jobs.WORKER_SCRIPT = failing_worker
        preview_jobs.clear_jobs()
        failed_job = preview_jobs.start_preview_job(payload, "HVA-DISCOVERY-WORKER-FAILURE-TEST")
        preview_jobs.WORKER_SCRIPT = original_worker
        failed = _wait(failed_job["job_id"])
        assert failed["state"] == "FAILED", failed
        assert failed["reason"] == "DOCUMENT_DISCOVERY_PREVIEW_RASTER_FALLBACK_FAILED:DOCUMENT_DISCOVERY_PREVIEW_WORKER_EXIT_7", failed
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
    assert "showPreviewPage" in html
    assert "state?.page_count>0" in html
    assert "INCONCLUSIVE" in html
    assert "raster tiled evidence" in html
    assert "copertura" in html

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
    assert "TILED_FULL_COVERAGE" in raster_source
    assert "PYMUPDF_RASTER_CONNECTED_REGION_TILED_V2" in raster_source
    assert "PAGE_BLANK_OBSERVED" in raster_source
    assert "INCONCLUSIVE_RASTER_DETECTION" in raster_source
    assert "RASTER_TILED_EVIDENCE_V2" in raster_source

    jobs_source = Path("cew_document_discovery_preview_jobs.py").read_text(encoding="utf-8")
    worker_source = Path("cew_document_discovery_preview_worker.py").read_text(encoding="utf-8")
    assert "subprocess.run(" in jobs_source
    assert "PROCESS_ISOLATED_SUBPROCESS" in jobs_source
    assert "PREVIEW_VECTOR_TIMEOUT_SECONDS" in jobs_source
    assert "PREVIEW_RASTER_TIMEOUT_SECONDS" in jobs_source
    assert "RASTER_SAFE_MODE" in jobs_source
    assert "DOCUMENT_DISCOVERY_PREVIEW_VECTOR_EMPTY" in jobs_source
    assert 'state="INCONCLUSIVE"' in jobs_source
    assert "preview_engine.preacquire_preview_pdf" not in jobs_source
    assert "resource.RLIMIT_AS" in worker_source
    assert "CEW_PREVIEW_WORKER_MEMORY_MB" in worker_source
    assert "cew_document_discovery_preview_engine" in worker_source
    assert "cew_document_discovery_raster_preview_engine" in worker_source
    assert "os.nice(10)" in worker_source

    print("CEW_DOCUMENT_DISCOVERY_ASYNC_PREVIEW_PASS")
    print("http_boundary=ENQUEUE_THEN_POLL gateway_wait=DECOUPLED")
    print("worker_boundary=PROCESS_ISOLATED_SUBPROCESS memory_ceiling=ENFORCED")
    print("vector_empty=RASTER_TILED_EVIDENCE_V2_FALLBACK")
    print("raster_inconclusive=EVIDENCE_SESSION_VISIBLE training=BLOCKED")
    print("preview_training=BLOCKED semantic_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
