#!/usr/bin/env python3
"""Deterministic gate for CEW new-project zero-prior pre-acquisition."""
from __future__ import annotations

import json
from pathlib import Path

import pymupdf

import cew_new_project_preacquisition as pre

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_NEW_PROJECT_PREACQUISITION_CONTRACT_v1.json"
ANALYSIS = ROOT / "analysis/cew/CEW_NEW_PROJECT_PREACQUISITION_ANALYSIS_v1.md"
LIBRARY_INDEX = ROOT / "knowledge/graphic_reference/CEW_GRAPHIC_REFERENCE_LIBRARY_INDEX_v1.json"


def _synthetic_unknown_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=842, height=595)
    # Repeated rectangles deliberately have no semantic label. They only form a
    # recurring graphic family for the clustering gate.
    for i in range(6):
        x = 80 + (i % 3) * 180
        y = 90 + (i // 3) * 180
        page.draw_rect(pymupdf.Rect(x, y, x + 44, y + 44), color=(0, 0, 0), width=1)
        page.draw_line(pymupdf.Point(x - 25, y + 22), pymupdf.Point(x + 70, y + 22), color=(0, 0, 0), width=0.5)
        page.draw_line(pymupdf.Point(x + 22, y - 25), pymupdf.Point(x + 22, y + 70), color=(0, 0, 0), width=0.5)
    page.draw_circle(pymupdf.Point(690, 110), 22, color=(0, 0, 0), width=1)
    page.insert_text((70, 520), "UNKNOWN PROJECT DRAWING 001", fontsize=12)
    page2 = doc.new_page(width=842, height=595)
    for i in range(4):
        x = 110 + i * 150
        page2.draw_rect(pymupdf.Rect(x, 150, x + 44, 194), color=(0, 0, 0), width=1)
    page2.insert_text((70, 520), "SECOND UNKNOWN PAGE", fontsize=12)
    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schema"] == pre.CONTRACT_SCHEMA
    assert contract["input_assumption"] == "ZERO_SEMANTIC_OBJECT_PRIOR"
    assert contract["default_interaction"] == "DOCUMENT_DISCOVERY_WORKSPACE"
    assert contract["mature_object_interaction"] == "TEACH_THIS_IS->FIND_SIMILAR->REVIEW_SIMILAR_GROUP"
    assert contract["snap_role"] == "GEOMETRY_EDITING_AID_ONLY"
    assert contract["authority"] == pre.AUTHORITY
    assert contract["first_implementation_slice"]["requires_known_object_types"] is False
    assert contract["first_implementation_slice"]["library_optional"] is True
    assert ANALYSIS.is_file()
    analysis_text = ANALYSIS.read_text(encoding="utf-8")
    assert "DOCUMENT INTAKE" in analysis_text
    assert "NON-SEMANTIC GRAPHIC CLUSTERING" in analysis_text
    assert "TEACH_THIS_IS" in analysis_text
    assert "Internet acquisition rule" in analysis_text

    library_index = json.loads(LIBRARY_INDEX.read_text(encoding="utf-8"))
    assert library_index["schema"] == pre.LIBRARY_SCHEMA
    assert library_index["status"] == "LIBRARY_NOT_CONFIGURED"
    assert library_index["entry_count"] == 0
    assert library_index["policy"]["direct_web_result_may_be_project_truth"] is False
    assert library_index["authority"]["semantic_authority"] == "NONE"

    payload = _synthetic_unknown_pdf()
    report1 = pre.preacquire_pdf(payload, source_version_id="SRC-NEW-PROJECT-TEST-V1")
    report2 = pre.preacquire_pdf(payload, source_version_id="SRC-NEW-PROJECT-TEST-V1")

    assert report1["schema"] == pre.SCHEMA
    assert report1["mode"] == "NEW_PROJECT_ZERO_SEMANTIC_PRIOR"
    assert report1["known_object_types_required"] is False
    assert report1["semantic_labels_assigned_automatically"] is False
    assert report1["page_count"] == 2
    assert report1["primitive_candidate_count"] > 0
    assert report1["graphic_cluster_count"] > 0
    assert report1["library_state"] == "LIBRARY_NOT_CONFIGURED"
    assert report1["knowledge_match_proposals"] == []
    assert report1["human_triage_queue"]
    assert report1["authority"] == pre.AUTHORITY
    assert report1["next_gate"] == "HUMAN_DOCUMENT_AND_GRAPHIC_TRIAGE_REQUIRED"

    assert report1["report_fingerprint"] == report2["report_fingerprint"]
    assert [x["candidate_id"] for x in report1["primitive_candidates"]] == [
        x["candidate_id"] for x in report2["primitive_candidates"]
    ]
    assert [x["cluster_id"] for x in report1["graphic_clusters"]] == [
        x["cluster_id"] for x in report2["graphic_clusters"]
    ]

    families = {x["primitive_family"] for x in report1["primitive_candidates"]}
    assert "RECTILINEAR_CLOSED_SHAPE" in families
    assert "LINEAR_STROKE_GROUP" in families
    assert "CURVED_OR_ARC_SHAPE" in families
    assert "TEXT_BLOCK" in families
    assert any(page["modality"] == "NATIVE_VECTOR" for page in report1["pages"])

    for candidate in report1["primitive_candidates"]:
        assert candidate["source_version_id"] == "SRC-NEW-PROJECT-TEST-V1"
        assert candidate["source_sha256"] == report1["source_sha256"]
        assert candidate["semantic_meaning"] is None
        assert candidate["semantic_authority"] == "NONE"
        bbox = candidate["bbox"]
        assert 0.0 <= bbox["x"] <= 1.0
        assert 0.0 <= bbox["y"] <= 1.0
        assert bbox["w"] > 0 and bbox["h"] > 0
        assert bbox["x"] + bbox["w"] <= 1.0000001
        assert bbox["y"] + bbox["h"] <= 1.0000001

    for cluster in report1["graphic_clusters"]:
        assert cluster["cluster_id"].startswith("GC-")
        assert cluster["cluster_kind"] == "NON_SEMANTIC_GRAPHIC_CLUSTER"
        assert cluster["semantic_meaning"] is None
        assert cluster["automatic_structural_label"] is False
        assert cluster["human_review_required"] is True
        assert cluster["member_candidate_ids"]

    for triage in report1["human_triage_queue"]:
        assert "TEACH_THIS_IS" in triage["allowed_actions"]
        assert "UNCERTAIN" in triage["allowed_actions"]
        assert triage["semantic_authority_before_action"] == "NONE"

    entries = [
        {
            "entry_id": "GREF-TEST-RECT-001",
            "meaning": "RECTANGULAR_SYMBOL_CANDIDATE",
            "tier": "EXTERNAL_REFERENCE",
            "primitive_families": ["RECTILINEAR_CLOSED_SHAPE"],
            "aspect_buckets": ["SQUAREISH"],
            "area_buckets": ["TINY", "SMALL"],
            "filled": False,
            "source_refs": ["REF-SYNTHETIC-001"],
            "counterexample_refs": ["REF-SYNTHETIC-COUNTER-001"],
        }
    ]
    pack = {
        "schema": pre.LIBRARY_SCHEMA,
        "status": "LIBRARY_AVAILABLE_UNVERIFIED_FOR_CONTEXT",
        "generation_id": "GREF-GEN-TEST-001",
        "content_sha256": pre._library_entries_fingerprint(entries),
        "entry_count": len(entries),
        "entries": entries,
    }
    with_library = pre.preacquire_pdf(
        payload,
        source_version_id="SRC-NEW-PROJECT-TEST-V1",
        library_pack=pack,
    )
    assert with_library["library_state"] == "LIBRARY_MATCHES_AVAILABLE"
    assert with_library["knowledge_match_proposals"]
    for proposal in with_library["knowledge_match_proposals"]:
        assert proposal["library_generation_id"] == "GREF-GEN-TEST-001"
        assert proposal["project_semantic_authority"] == "NONE"
        assert proposal["human_project_validation_required"] is True
        for match in proposal["matches"]:
            assert match["meaning"] == "RECTANGULAR_SYMBOL_CANDIDATE"
            assert match["support_refs"]
            assert match["counterexample_refs"]

    assert with_library["authority"] == pre.AUTHORITY
    assert with_library["semantic_labels_assigned_automatically"] is False

    print("CEW_NEW_PROJECT_PREACQUISITION_PASS")
    print(f"pages={report1['page_count']} primitives={report1['primitive_candidate_count']} clusters={report1['graphic_cluster_count']}")
    print("zero_semantic_prior=true stable_candidate_identity=true stable_cluster_identity=true")
    print("library_absence_nonfatal=true library_matches_proposal_only=true")
    print("human_triage_queue=READY automatic_structural_labels=false")
    print("canonical_write_authorized=false structural_identity_authorized=false engineering_authority_effect=NONE")


if __name__ == "__main__":
    main()
