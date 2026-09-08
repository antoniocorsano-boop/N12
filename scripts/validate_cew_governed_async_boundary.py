#!/usr/bin/env python3
"""Deterministic gate for governed Document Discovery process isolation."""
from __future__ import annotations

import base64
from hashlib import sha256
import json
from pathlib import Path

import cew_document_discovery as discovery
import cew_document_discovery_governed_async as governed_async
import cew_document_discovery_governed_jobs as governed_jobs


class InlineExecutor:
    def submit(self, fn, *args, **kwargs):
        fn(*args, **kwargs)
        return None


class FakeSourceWorkspace:
    def __init__(self, payload: bytes, digest: str):
        self.payload = payload
        self.digest = digest
        self.fetch_count = 0

    def fetch_verified_source(self, source_id: str):
        assert source_id == "TAV-06A"
        self.fetch_count += 1
        return self.payload, {"sha256": self.digest}

    def maps(self):
        return {
            "pages": {
                "P1": {
                    "logical_source_code": "TAV-06A",
                    "readiness_state": "READY",
                    "page_index": 0,
                    "page_id": "CEW-N12-PAGE-TAV06A-P001",
                    "source_version_id": "CEW-N12-SV-TAV06A",
                }
            }
        }


def main() -> None:
    payload = b"%PDF-1.4\n% governed test envelope\n%%EOF\n"
    digest = sha256(payload).hexdigest()
    jpeg = b"\xff\xd8CEW-GOVERNED-CACHED\xff\xd9"
    report = {
        "analysis_scope": "BOUNDED_INTERACTIVE_PREVIEW",
        "source_sha256": digest,
        "source_version_id": "CEW-N12-SV-TAV06A",
        "page_count": 1,
        "pages": [{"page_index": 0, "source_version_id": "CEW-N12-SV-TAV06A"}],
        "primitive_candidate_count": 1,
        "primitive_candidates": [{
            "candidate_id": "CAND-1",
            "page_index": 0,
            "source_version_id": "CEW-N12-SV-TAV06A",
            "coordinate_system": "NORMALIZED_0_1",
            "bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.2},
            "primitive_family": "RECT",
            "feature_signature": {"primitive_family": "RECT", "aspect_bucket": "TALL", "area_bucket": "SMALL"},
        }],
        "graphic_cluster_count": 1,
        "graphic_clusters": [{
            "cluster_id": "CL-1",
            "occurrence_count": 1,
            "page_indices": [0],
            "feature_signature": {"primitive_family": "RECT", "aspect_bucket": "TALL", "area_bucket": "SMALL"},
            "member_candidate_ids": ["CAND-1"],
        }],
        "library_state": "NONE",
        "quality_gate": {"status": "PASS", "reasons": [], "minimum_page_coverage_ratio": 1.0},
        "preview_worker_mode": "VECTOR_BOUNDED",
        "preview_page_images": [{
            "page_index": 0,
            "render_boundary": "PROCESS_ISOLATED_WORKER",
            "data_base64": base64.b64encode(jpeg).decode("ascii"),
            "sha256": sha256(jpeg).hexdigest(),
        }],
    }

    original_executor = governed_jobs.EXECUTOR
    original_invoke = governed_jobs.preview_jobs._invoke_worker
    original_validate = discovery._validate_pdf

    def forbidden_in_process_pdf_validation(_payload: bytes) -> None:
        raise AssertionError("GOVERNED_WEB_PROCESS_MUST_NOT_PARSE_PDF")

    def fake_invoke_worker(*, work_dir: Path, **_kwargs):
        (work_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return None, None

    try:
        discovery.clear_sessions()
        governed_jobs.clear_jobs()
        governed_jobs.EXECUTOR = InlineExecutor()
        governed_jobs.preview_jobs._invoke_worker = fake_invoke_worker
        discovery._validate_pdf = forbidden_in_process_pdf_validation

        workspace = FakeSourceWorkspace(payload, digest)
        queued = governed_jobs.start_governed_job(workspace, "TAV-06A", "N12")
        assert queued["state"] == "QUEUED"
        assert queued["analysis_scope"] == "BOUNDED_GOVERNED_DOCUMENT_DISCOVERY"
        assert queued["execution_boundary"] == "PROCESS_ISOLATED_SUBPROCESS"
        assert workspace.fetch_count == 1

        done = governed_jobs.governed_job_status(queued["job_id"])
        assert done["state"] == "READY", done
        assert done["teaching_enabled"] is True
        assert done["source_version_id"] == "CEW-N12-SV-TAV06A"
        assert done["authority"]["canonical_write_authorized"] is False

        session = discovery.get_session(done["session_id"])
        assert session["source_registration_state"] == "GOVERNED_IMMUTABLE_SOURCE"
        assert session["source_version_id"] == "CEW-N12-SV-TAV06A"
        assert session["page_registry"][0]["readiness_state"] == "READY"
        assert session["teaching_enabled"] is True
        candidate = session["report"]["primitive_candidates"][0]
        assert candidate["source_version_id"] == session["page_registry"][0]["source_version_id"]
        assert governed_async._cached_page_artifact(done["session_id"], 0) == jpeg
    finally:
        governed_jobs.EXECUTOR = original_executor
        governed_jobs.preview_jobs._invoke_worker = original_invoke
        discovery._validate_pdf = original_validate
        discovery.clear_sessions()
        governed_jobs.clear_jobs()

    print("CEW_GOVERNED_ASYNC_BOUNDARY_PASS")
    print("web_pdf_parse=BLOCKED extraction=PROCESS_ISOLATED_SUBPROCESS")
    print("source_version=CANONICAL ready_page_registry=PRESERVED teaching=GOVERNED_ONLY")
    print("page_artifact=PROCESS_ISOLATED_CACHED canonical_write_authorized=false")


if __name__ == "__main__":
    main()
