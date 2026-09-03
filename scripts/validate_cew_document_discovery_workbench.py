#!/usr/bin/env python3
"""Deterministic gate for the CEW Document Discovery Workspace."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import tempfile

import pymupdf

import cew_document_discovery as discovery
import cew_document_discovery_workbench as workbench
import cew_runtime_audit_store as audit_store
import cew_visual_learning as learning


PROJECT_ID = "PROJECT-DISCOVERY-TEST-001"
SOURCE_ID = "DISCOVERY-TEST-DRAWING"
SOURCE_VERSION_ID = "CEW-TEST-SRC-DISCOVERY-V1"
PAGE_ID = "CEW-TEST-PAGE-DISCOVERY-P001"


def _pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=842, height=595)
    for i in range(8):
        x = 70 + (i % 4) * 175
        y = 90 + (i // 4) * 220
        page.draw_rect(pymupdf.Rect(x, y, x + 44, y + 44), color=(0, 0, 0), width=1)
        page.draw_line(pymupdf.Point(x - 20, y + 22), pymupdf.Point(x + 64, y + 22), color=(0, 0, 0), width=0.5)
        page.draw_line(pymupdf.Point(x + 22, y - 20), pymupdf.Point(x + 22, y + 64), color=(0, 0, 0), width=0.5)
    page.draw_rect(pymupdf.Rect(690, 420, 770, 445), color=(0, 0, 0), width=1)
    page.insert_text((70, 545), "DOCUMENT DISCOVERY ZERO PRIOR TEST", fontsize=11)
    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


class FakeSourceWorkspace:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.digest = sha256(payload).hexdigest()

    def maps(self):
        return {
            "sources": {
                SOURCE_ID: {
                    "id": SOURCE_ID,
                    "status": "DOC_PRIMARY_IMMUTABLE",
                    "sha256": self.digest,
                }
            },
            "pages": {
                PAGE_ID: {
                    "page_id": PAGE_ID,
                    "logical_source_code": SOURCE_ID,
                    "source_version_id": SOURCE_VERSION_ID,
                    "page_index": "0",
                    "readiness_state": "READY",
                }
            },
        }

    def fetch_verified_source(self, source_id: str):
        if source_id != SOURCE_ID:
            raise KeyError("SOURCE_NOT_FOUND")
        return self.payload, {
            "id": SOURCE_ID,
            "status": "DOC_PRIMARY_IMMUTABLE",
            "sha256": self.digest,
        }


def _candidate(session: dict) -> dict:
    rows = session["report"]["primitive_candidates"]
    assert rows
    preferred = [row for row in rows if row["primitive_family"] == "RECTILINEAR_CLOSED_SHAPE"]
    return preferred[0] if preferred else rows[0]


def main() -> None:
    payload = _pdf()
    workspace = FakeSourceWorkspace(payload)
    discovery.clear_sessions()

    provider = discovery.provider_states()
    assert provider["structured_graphic"]["state"] == "READY"
    assert provider["structured_graphic"]["used_now"] is True
    assert provider["visual_foundation"]["provider_id"] == "DINOV3_FROZEN_FEATURES"
    assert provider["visual_foundation"]["used_now"] is False
    assert provider["visual_foundation"]["simulated"] is False

    sources = discovery.governed_sources(workspace)
    assert sources == [{
        "source_id": SOURCE_ID,
        "sha256": sha256(payload).hexdigest(),
        "ready_page_count": 1,
        "teaching_possible": True,
    }]

    preview = discovery.create_preview(payload, PROJECT_ID)
    preview_status = discovery.status(preview["session_id"])
    assert preview_status["source_registration_state"] == "UNREGISTERED_PREVIEW"
    assert preview_status["teaching_enabled"] is False
    assert preview_status["teaching_blocker"] == "IMMUTABLE_SOURCE_AND_READY_PAGE_REGISTRATION_REQUIRED"
    assert preview_status["primitive_candidate_count"] > 0
    assert preview_status["graphic_cluster_count"] > 0
    assert preview_status["semantic_labels_assigned_automatically"] is False
    assert preview_status["authority"]["canonical_write_authorized"] is False

    candidate = _candidate(preview)
    try:
        discovery.teach(preview["session_id"], {
            "candidate_id": candidate["candidate_id"],
            "role": "POSITIVE",
            "concept_id": "CONCEPT-A",
            "meaning": "HUMAN TAUGHT CONCEPT A",
            "reviewer": "TEST-REVIEWER",
            "rationale": "preview must never train",
        })
        raise AssertionError("preview training should be rejected")
    except ValueError as exc:
        assert "TEACHING_REQUIRES_GOVERNED_SOURCE" in str(exc)

    original_store = learning.RUNTIME_STORE
    original_backend = audit_store.backend_status
    with tempfile.TemporaryDirectory(prefix="cew-document-discovery-") as tmp:
        learning.RUNTIME_STORE = Path(tmp)
        audit_store.backend_status = lambda: "FILESYSTEM_APPEND_ONLY"
        try:
            governed = discovery.create_governed(workspace, SOURCE_ID, PROJECT_ID)
            governed_status = discovery.status(governed["session_id"])
            assert governed_status["source_registration_state"] == "GOVERNED_IMMUTABLE_SOURCE"
            assert governed_status["source_version_id"] == SOURCE_VERSION_ID
            assert governed_status["teaching_enabled"] is True
            assert governed_status["teaching_blocker"] is None
            assert governed_status["authority"]["project_semantic_authority"] == "NONE"
            assert governed_status["authority"]["f2_registry_written"] is False

            candidate = _candidate(governed)
            result = discovery.teach(governed["session_id"], {
                "candidate_id": candidate["candidate_id"],
                "role": "POSITIVE",
                "concept_id": "CONCEPT-A",
                "meaning": "HUMAN TAUGHT CONCEPT A",
                "reviewer": "TEST-REVIEWER",
                "rationale": "explicit human positive example",
            })
            assert result["state"] == "PROJECT_LOCAL_LEARNING_RECEIPT_PERSISTED"
            assert result["role"] == "POSITIVE"
            assert result["example_counts"]["POSITIVE"] == 1
            assert result["authority"]["canonical_write_authorized"] is False
            assert result["authority"]["structural_identity_authorized"] is False

            loaded = learning.load_learning_receipts()
            assert loaded["receipt_count"] == 1
            receipt = loaded["receipts"][0]
            assert receipt["source_version_id"] == SOURCE_VERSION_ID
            assert receipt["page_id"] == PAGE_ID
            assert receipt["project_id"] == PROJECT_ID
            assert receipt["learning_effect"] == "DERIVED_PROTOTYPE_MEMORY_ONLY"
            assert receipt["authority"]["project_semantic_authority"] == "NONE"

            similar = discovery.find_similar(
                governed["session_id"], "CONCEPT-A", "HUMAN TAUGHT CONCEPT A", limit=20
            )
            assert similar["candidate_count"] > 0
            assert similar["automatic_classification"] is False
            assert similar["visual_foundation_used"] is False
            assert similar["authority"]["canonical_write_authorized"] is False
            assert all(row["proposal_state"] == "SIMILARITY_PROPOSAL" for row in similar["candidates"])
            assert all(row["semantic_assignment"] is None for row in similar["candidates"])

            jpeg = discovery.render_page(governed["session_id"], 0)
            assert jpeg.startswith(b"\xff\xd8")
        finally:
            learning.RUNTIME_STORE = original_store
            audit_store.backend_status = original_backend

    html = workbench._page()
    assert "Document Discovery Workspace" in html
    assert "Insegna: questo è un" in html
    assert "Non è questo" in html
    assert "Incerto" in html
    assert "Trova simili" in html
    assert "Significato automatico: <b>nessuno</b>" in html
    assert "Preview analizzabile, ma training bloccato" in html

    # Mobile HVA regression: a tap must provide immediate, local feedback and must
    # stream the browser File directly instead of duplicating it with arrayBuffer().
    assert 'id="intake-message"' in html
    assert "Analisi grafica in corso" in html
    assert "Preview completata" in html
    assert "body:f" in html
    assert "arrayBuffer()" not in html
    assert "maxPreviewBytes" in html
    assert "supera il limite preview" in html
    assert "responseJson" in html

    router = workbench.build_router(workspace)
    paths = {route.path for route in router.routes}
    required = {
        "/workbench/document-discovery",
        "/api/workbench/document-discovery/status",
        "/api/workbench/document-discovery/analyze-governed",
        "/api/workbench/document-discovery/analyze-preview",
        "/api/workbench/document-discovery/session/{session_id}",
        "/api/workbench/document-discovery/session/{session_id}/page/{page_index}.jpg",
        "/api/workbench/document-discovery/session/{session_id}/learn",
        "/api/workbench/document-discovery/session/{session_id}/similar",
    }
    assert required.issubset(paths)

    workbench_source = Path(workbench.__file__).read_text(encoding="utf-8")
    assert '"max_preview_pdf_bytes":discovery.MAX_PDF_BYTES' in workbench_source
    assert "run_in_threadpool(discovery.create_preview" in workbench_source
    assert "DOCUMENT_DISCOVERY_PREVIEW_BLOCKED" in workbench_source

    composition = (Path(__file__).with_name("cew_professional_workbench_api.py")).read_text(encoding="utf-8")
    assert "import cew_document_discovery_workbench as _document_discovery" in composition
    assert "router.include_router(_document_discovery.build_router(source_workspace))" in composition

    print("CEW_DOCUMENT_DISCOVERY_WORKBENCH_PASS")
    print("preview_analysis=PASS preview_training=BLOCKED")
    print("mobile_preview_feedback=PASS direct_file_upload=PASS")
    print("governed_source_page_binding=PASS learning_receipt=APPEND_ONLY")
    print("find_similar=PROPOSAL_ONLY automatic_classification=false")
    print("document_discovery_router=MOUNTED_IN_PROFESSIONAL_WORKBENCH")
    print("canonical_write_authorized=false structural_identity_authorized=false engineering_authority_effect=NONE")


if __name__ == "__main__":
    main()
