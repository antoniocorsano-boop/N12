#!/usr/bin/env python3
"""Deterministic regression corpus for CEW Raster Evidence Engine v2."""
from __future__ import annotations

import pymupdf

import cew_document_discovery_raster_preview_engine as raster


def _make_pdf(width: float, height: float, draw) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=width, height=height)
    if draw is not None:
        draw(page)
    payload = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return payload


def _assert_ready_graphic(payload: bytes, source_version_id: str) -> dict:
    report = raster.preacquire_preview_pdf(payload, source_version_id=source_version_id)
    assert report["raster_contract_schema"] == raster.RASTER_CONTRACT_SCHEMA
    assert report["quality_gate"]["status"] == "READY", report["quality_gate"]
    assert report["quality_gate"]["minimum_page_coverage_ratio"] == 1.0
    assert report["primitive_candidate_count"] > 0
    assert report["graphic_cluster_count"] > 0
    assert report["semantic_labels_assigned_automatically"] is False
    assert report["authority"]["canonical_write_authorized"] is False
    assert report["authority"]["structural_identity_authorized"] is False
    for page in report["pages"]:
        assert page["coverage_ratio"] == 1.0
        assert page["tiles_failed"] == 0
        assert page["signal_state"] == "PRESENT"
        assert page["quality_status"] == "READY"
        assert page["raster_plan"]["strategy"] == "TILED_FULL_COVERAGE"
    for candidate in report["primitive_candidates"]:
        assert candidate["detector"] == "PYMUPDF_RASTER_CONNECTED_REGION_TILED_V2"
        assert candidate["semantic_authority"] == "NONE"
        assert candidate["raster_plan_id"]
        assert candidate["supporting_tile_ids"]
        assert candidate["signal_metrics"]["raw_signal_cells"] > 0
        assert candidate["aggregation_method"] == "DILATED_CONNECTIVITY_RAW_GEOMETRY_WITH_CROSS_TILE_RECONCILIATION"
    return report


def main() -> None:
    blank = _make_pdf(842, 595, None)
    blank_report = raster.preacquire_preview_pdf(blank, source_version_id="RASTER-V2-BLANK")
    assert blank_report["quality_gate"]["status"] == "READY"
    assert blank_report["primitive_candidate_count"] == 0
    assert blank_report["pages"][0]["page_observation_state"] == "PAGE_BLANK_OBSERVED"
    assert blank_report["pages"][0]["coverage_ratio"] == 1.0
    assert blank_report["pages"][0]["tiles_failed"] == 0

    thin_horizontal = _make_pdf(
        2400,
        360,
        lambda page: page.draw_line(
            pymupdf.Point(20, 180), pymupdf.Point(2380, 180), color=(0, 0, 0), width=0.2
        ),
    )
    horizontal_report = _assert_ready_graphic(thin_horizontal, "RASTER-V2-THIN-H")
    assert horizontal_report["pages"][0]["tiles_planned"] > 1
    assert any(row["primitive_family"] == "LINEAR_STROKE_GROUP" for row in horizontal_report["primitive_candidates"])

    thin_vertical = _make_pdf(
        360,
        4000,
        lambda page: page.draw_line(
            pymupdf.Point(180, 20), pymupdf.Point(180, 3980), color=(0, 0, 0), width=0.2
        ),
    )
    vertical_report = _assert_ready_graphic(thin_vertical, "RASTER-V2-THIN-V")
    assert vertical_report["pages"][0]["tiles_planned"] > 1
    assert any(row["primitive_family"] == "LINEAR_STROKE_GROUP" for row in vertical_report["primitive_candidates"])

    def draw_grid(page: pymupdf.Page) -> None:
        for x in range(60, 1200, 90):
            page.draw_line(pymupdf.Point(x, 40), pymupdf.Point(x, 760), color=(0, 0, 0), width=0.25)
        for y in range(70, 760, 80):
            page.draw_line(pymupdf.Point(40, y), pymupdf.Point(1260, y), color=(0, 0, 0), width=0.25)
        page.draw_rect(pymupdf.Rect(420, 260, 780, 500), color=(0, 0, 0), width=0.5)

    grid = _make_pdf(1300, 800, draw_grid)
    grid_report = _assert_ready_graphic(grid, "RASTER-V2-GRID")
    assert grid_report["pages"][0]["raw_region_count"] >= grid_report["pages"][0]["reconciled_region_count"]

    replay_a = raster.preacquire_preview_pdf(grid, source_version_id="RASTER-V2-REPLAY")
    replay_b = raster.preacquire_preview_pdf(grid, source_version_id="RASTER-V2-REPLAY")
    assert replay_a["report_fingerprint"] == replay_b["report_fingerprint"]
    assert [row["candidate_id"] for row in replay_a["primitive_candidates"]] == [
        row["candidate_id"] for row in replay_b["primitive_candidates"]
    ]
    assert [page["raster_plan_id"] for page in replay_a["pages"]] == [
        page["raster_plan_id"] for page in replay_b["pages"]
    ]

    contract_fields = {
        "source_sha256",
        "source_version_id",
        "page_index",
        "coordinate_system",
        "bbox",
        "raster_plan_id",
        "supporting_tile_ids",
        "detector",
        "extractor_version",
        "signal_metrics",
        "aggregation_method",
    }
    assert contract_fields.issubset(grid_report["primitive_candidates"][0])

    print("CEW_RASTER_EVIDENCE_ENGINE_V2_PASS")
    print("blank=DEMONSTRATED thin_horizontal=DETECTED thin_vertical=DETECTED")
    print("elongated_page=TILED_FULL_COVERAGE cross_tile_reconciliation=ENABLED")
    print("deterministic_replay=PASS semantic_authority=NONE canonical_write_authorized=false")


if __name__ == "__main__":
    main()
