#!/usr/bin/env python3
"""Regression gate: adaptive recovery timeout must preserve baseline evidence."""
from __future__ import annotations

from pathlib import Path
import tempfile
import time

import pymupdf

import cew_document_discovery as discovery
import cew_document_discovery_preview_jobs as preview_jobs


def _pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=3600)
    page.insert_text((20, 40), "CORROBORATED TECHNICAL CONTENT", fontsize=9)
    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


def _fake_worker(path: Path) -> None:
    path.write_text(
        "import json, sys, time\n"
        "_, source_version_id, digest, mode = sys.argv\n"
        "if mode == 'RASTER_SIGNAL_RECOVERY':\n"
        "    time.sleep(1.0)\n"
        "    raise SystemExit(0)\n"
        "report = {\n"
        "  'analysis_scope':'BOUNDED_INTERACTIVE_PREVIEW',\n"
        "  'source_sha256':digest,\n"
        "  'source_version_id':source_version_id,\n"
        "  'page_count':1,\n"
        "  'pages':[{'page_index':0}],\n"
        "  'primitive_candidate_count':0,\n"
        "  'primitive_candidates':[],\n"
        "  'graphic_cluster_count':0,\n"
        "  'graphic_clusters':[],\n"
        "  'preview_worker_mode':mode,\n"
        "}\n"
        "if mode == 'RASTER_SAFE':\n"
        "    report['pages'][0]['blank_corroboration']={'state':'CONTENT_PRESENT'}\n"
        "    report['quality_gate']={'status':'INCONCLUSIVE','reasons':['BLANK_CORROBORATION_CONTRADICTED'],'minimum_page_coverage_ratio':1.0,'blank_pages_observed':[]}\n"
        "open('report.json','w',encoding='utf-8').write(json.dumps(report))\n",
        encoding="utf-8",
    )


def _wait(job_id: str) -> dict:
    deadline = time.time() + 5.0
    current = preview_jobs.preview_job_status(job_id)
    while time.time() < deadline:
        current = preview_jobs.preview_job_status(job_id)
        if current["state"] in {"READY", "INCONCLUSIVE", "FAILED"}:
            return current
        time.sleep(0.02)
    raise AssertionError(current)


def main() -> None:
    payload = _pdf()
    discovery.clear_sessions()
    preview_jobs.clear_jobs()

    original_worker = preview_jobs.WORKER_SCRIPT
    original_vector = preview_jobs.PREVIEW_VECTOR_TIMEOUT_SECONDS
    original_raster = preview_jobs.PREVIEW_RASTER_TIMEOUT_SECONDS
    original_recovery = preview_jobs.PREVIEW_SIGNAL_RECOVERY_TIMEOUT_SECONDS

    with tempfile.TemporaryDirectory(prefix="cew-recovery-timeout-test-") as tmp:
        fake = Path(tmp) / "fake_worker.py"
        _fake_worker(fake)
        preview_jobs.WORKER_SCRIPT = fake
        preview_jobs.PREVIEW_VECTOR_TIMEOUT_SECONDS = 2.0
        preview_jobs.PREVIEW_RASTER_TIMEOUT_SECONDS = 2.0
        preview_jobs.PREVIEW_SIGNAL_RECOVERY_TIMEOUT_SECONDS = 0.05
        job = preview_jobs.start_preview_job(payload, "HVA-RECOVERY-DEGRADATION-TEST")
        preview_jobs.WORKER_SCRIPT = original_worker
        preview_jobs.PREVIEW_VECTOR_TIMEOUT_SECONDS = original_vector
        preview_jobs.PREVIEW_RASTER_TIMEOUT_SECONDS = original_raster
        preview_jobs.PREVIEW_SIGNAL_RECOVERY_TIMEOUT_SECONDS = original_recovery
        result = _wait(job["job_id"])

    assert result["state"] == "INCONCLUSIVE", result
    assert result["session_id"], result
    assert result["preview_fallback_used"] is True
    assert result["preview_signal_recovery_used"] is True
    assert result["preview_worker_mode"] == preview_jobs.RASTER_SIGNAL_RECOVERY_MODE
    assert result["preview_signal_recovery_outcome"] == "DOCUMENT_DISCOVERY_PREVIEW_WORKER_TIMEOUT_RASTER_SIGNAL_RECOVERY"
    assert result["reason"].startswith("DOCUMENT_DISCOVERY_SIGNAL_RECOVERY_DEGRADED:"), result
    assert result["minimum_page_coverage_ratio"] == 1.0

    session = discovery.get_session(result["session_id"])
    assert session["teaching_enabled"] is False
    assert session["authority"]["canonical_write_authorized"] is False
    gate = session["report"]["quality_gate"]
    assert gate["status"] == "INCONCLUSIVE"
    assert any(str(reason).startswith("DOCUMENT_DISCOVERY_SIGNAL_RECOVERY_DEGRADED:") for reason in gate["reasons"])

    print("CEW_SIGNAL_RECOVERY_DEGRADATION_PASS")
    print("baseline_evidence=PRESERVED recovery_timeout=INCONCLUSIVE_NOT_FAILED")
    print("training=BLOCKED canonical_write_authorized=false")


if __name__ == "__main__":
    main()
