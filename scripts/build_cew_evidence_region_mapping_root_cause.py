#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pymupdf

import build_cew_evidence_region_content_diagnostic as r1
import build_cew_managed_f3_assets as managed_f3_builder

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_evidence_region_mapping_root_cause"
MANIFEST = ASSET_ROOT / "manifest.json"
PAGE_REGISTRY = ROOT / "data/canonical/CEW_PAGE_REGISTRY_v1.csv"
TARGET_IDS = {"CEW-N12-REG-G01-R06", "CEW-N12-REG-G07-R07"}
EDGE_TOLERANCE_PT = 0.01
PAGE_DIMENSION_TOLERANCE_PT = 0.5
ROOT_CAUSES = {
    "PAGE_REGISTRY_ROW_MISSING",
    "SOURCE_VERSION_MISMATCH",
    "PAGE_INDEX_OUT_OF_RANGE",
    "PAGE_DIMENSION_MISMATCH",
    "NORMALIZED_REGION_OUT_OF_BOUNDS",
    "FLOATING_POINT_CONTAINMENT_TOLERANCE",
    "SOURCE_REGION_OUTSIDE_PAGE",
    "NO_MAPPING_ERROR_REPRODUCED",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _revision() -> str:
    value = os.getenv("RENDER_GIT_COMMIT") or os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("GITHUB_SHA")
    if value:
        return value.strip()
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _page_row(page_id: str) -> dict[str, str] | None:
    matches = [row for row in _rows(PAGE_REGISTRY) if row.get("page_id", "").strip() == page_id]
    if len(matches) > 1:
        raise AssertionError(f"duplicate Page rows for {page_id}")
    return matches[0] if matches else None


def _area(rect: pymupdf.Rect) -> float:
    if rect.is_empty or rect.is_infinite:
        return 0.0
    return max(0.0, float(rect.width)) * max(0.0, float(rect.height))


def _root_cause(pred: dict[str, bool], overhang: dict[str, float]) -> str:
    if not pred["page_registry_present"]:
        return "PAGE_REGISTRY_ROW_MISSING"
    if not pred["source_version_match"]:
        return "SOURCE_VERSION_MISMATCH"
    if not pred["page_index_in_range"]:
        return "PAGE_INDEX_OUT_OF_RANGE"
    if not pred["page_dimensions_match"]:
        return "PAGE_DIMENSION_MISMATCH"
    if not pred["normalized_bbox_valid"]:
        return "NORMALIZED_REGION_OUT_OF_BOUNDS"
    if pred["strict_r1_containment"]:
        return "NO_MAPPING_ERROR_REPRODUCED"
    if pred["edge_tolerant_containment"] and max(overhang.values()) <= EDGE_TOLERANCE_PT:
        return "FLOATING_POINT_CONTAINMENT_TOLERANCE"
    return "SOURCE_REGION_OUTSIDE_PAGE"


def _diagnose(source: dict[str, Any], region: dict[str, Any], pdf: Path) -> dict[str, Any]:
    page_row = _page_row(region["page_id"])
    source_version_match = bool(page_row) and page_row.get("source_version_id", "").strip() == source["source_version_id"]
    page_index = int(page_row["page_index"]) if page_row and page_row.get("page_index", "") else -1

    doc = pymupdf.open(pdf)
    try:
        page_index_in_range = 0 <= page_index < doc.page_count
        if page_index_in_range:
            page = doc[page_index]
            page_rect = pymupdf.Rect(page.rect)
            actual_w = float(page_rect.width)
            actual_h = float(page_rect.height)
        else:
            page_rect = pymupdf.Rect(0, 0, 0, 0)
            actual_w = actual_h = 0.0

        expected_w = float(page_row["source_width"]) if page_row and page_row.get("source_width") else None
        expected_h = float(page_row["source_height"]) if page_row and page_row.get("source_height") else None
        width_delta = abs(actual_w - expected_w) if expected_w is not None else None
        height_delta = abs(actual_h - expected_h) if expected_h is not None else None
        dimensions_match = (
            page_index_in_range
            and expected_w is not None
            and expected_h is not None
            and width_delta <= PAGE_DIMENSION_TOLERANCE_PT
            and height_delta <= PAGE_DIMENSION_TOLERANCE_PT
        )

        bbox = region["bbox_normalized"]
        x = float(bbox["x"])
        y = float(bbox["y"])
        w = float(bbox["width"])
        h = float(bbox["height"])
        normalized_valid = (
            x >= 0.0 and y >= 0.0 and w > 0.0 and h > 0.0
            and x + w <= 1.000001 and y + h <= 1.000001
        )
        source_rect = pymupdf.Rect(
            page_rect.x0 + x * actual_w,
            page_rect.y0 + y * actual_h,
            page_rect.x0 + (x + w) * actual_w,
            page_rect.y0 + (y + h) * actual_h,
        ) if page_index_in_range else pymupdf.Rect(0, 0, 0, 0)
        intersection = source_rect & page_rect if page_index_in_range else pymupdf.Rect(0, 0, 0, 0)
        source_area = _area(source_rect)
        intersection_area = _area(intersection)
        deficit = max(0.0, source_area - intersection_area)

        overhang = {
            "left": max(0.0, float(page_rect.x0 - source_rect.x0)),
            "top": max(0.0, float(page_rect.y0 - source_rect.y0)),
            "right": max(0.0, float(source_rect.x1 - page_rect.x1)),
            "bottom": max(0.0, float(source_rect.y1 - page_rect.y1)),
        }
        strict = bool(
            page_index_in_range
            and normalized_valid
            and source_area > 0.0
            and intersection_area >= source_area - 1e-6
        )
        edge_tolerant = bool(
            page_index_in_range
            and normalized_valid
            and source_area > 0.0
            and source_rect.x0 >= page_rect.x0 - EDGE_TOLERANCE_PT
            and source_rect.y0 >= page_rect.y0 - EDGE_TOLERANCE_PT
            and source_rect.x1 <= page_rect.x1 + EDGE_TOLERANCE_PT
            and source_rect.y1 <= page_rect.y1 + EDGE_TOLERANCE_PT
        )
        predicates = {
            "page_registry_present": page_row is not None,
            "source_version_match": source_version_match,
            "page_index_in_range": page_index_in_range,
            "page_dimensions_match": dimensions_match,
            "normalized_bbox_valid": normalized_valid,
            "source_rect_nonempty": source_area > 0.0,
            "strict_r1_containment": strict,
            "edge_tolerant_containment": edge_tolerant,
        }
        cause = _root_cause(predicates, overhang)
        return {
            "evidence_region_id": region["evidence_region_id"],
            "source_code": source["source_code"],
            "source_version_id": source["source_version_id"],
            "page_id": region["page_id"],
            "transform_id": region["transform_id"],
            "predicates": predicates,
            "page": {
                "registry_source_version_id": page_row.get("source_version_id", "").strip() if page_row else None,
                "page_index": page_index,
                "pdf_page_count": doc.page_count,
                "expected_width_pt": expected_w,
                "expected_height_pt": expected_h,
                "actual_rect_pt": [round(float(page_rect.x0), 9), round(float(page_rect.y0), 9), round(float(page_rect.x1), 9), round(float(page_rect.y1), 9)],
                "actual_width_pt": round(actual_w, 9),
                "actual_height_pt": round(actual_h, 9),
                "width_delta_pt": round(width_delta, 9) if width_delta is not None else None,
                "height_delta_pt": round(height_delta, 9) if height_delta is not None else None,
            },
            "region": {
                "bbox_normalized": bbox,
                "source_rect_pt": [round(float(source_rect.x0), 9), round(float(source_rect.y0), 9), round(float(source_rect.x1), 9), round(float(source_rect.y1), 9)],
                "source_area_pt2": round(source_area, 9),
                "intersection_area_pt2": round(intersection_area, 9),
                "intersection_area_deficit_pt2": round(deficit, 12),
                "edge_overhang_pt": {key: round(value, 12) for key, value in overhang.items()},
            },
            "root_cause": cause,
            "edge_tolerance_pt": EDGE_TOLERANCE_PT,
            "r1_strict_area_tolerance_pt2": 1e-6,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    finally:
        doc.close()


def build() -> dict[str, Any]:
    plan = r1.build_plan()
    managed_f3_builder._ensure_archive_commit(plan["archive_commit"])
    if ASSET_ROOT.exists():
        shutil.rmtree(ASSET_ROOT)
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="cew-pwb005-r1a-") as temp_name:
        temp_root = Path(temp_name)
        for source in plan["sources"]:
            target_regions = [r for r in source.get("evidence_regions", []) if r["evidence_region_id"] in TARGET_IDS]
            if not target_regions:
                continue
            pdf = temp_root / f"{source['source_code']}.pdf"
            managed_f3_builder._materialize_source(source, pdf)
            for region in target_regions:
                results.append(_diagnose(source, region, pdf))

    if {row["evidence_region_id"] for row in results} != TARGET_IDS:
        raise AssertionError(f"R1A target coverage mismatch: {[row['evidence_region_id'] for row in results]}")

    manifest = {
        "schema_version": "1.0",
        "diagnostic_contract": "CEW_PWB005_R1A_REGION_MAPPING_ROOT_CAUSE_v1",
        "build_revision": _revision(),
        "archive_commit": plan["archive_commit"],
        "target_region_ids": sorted(TARGET_IDS),
        "edge_tolerance_pt": EDGE_TOLERANCE_PT,
        "page_dimension_tolerance_pt": PAGE_DIMENSION_TOLERANCE_PT,
        "allowed_root_causes": sorted(ROOT_CAUSES),
        "results": sorted(results, key=lambda row: row["evidence_region_id"]),
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "hva_execution_authorized": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R1A_MAPPING_ROOT_CAUSE_BUILD = PASS")
    print("TARGET_REGION_COVERAGE = 2/2")
    for row in manifest["results"]:
        print(
            "MAPPING_ROOT_CAUSE",
            row["evidence_region_id"],
            row["root_cause"],
            "strict=" + str(row["predicates"]["strict_r1_containment"]),
            "tolerant=" + str(row["predicates"]["edge_tolerant_containment"]),
            "area_deficit=" + str(row["region"]["intersection_area_deficit_pt2"]),
            "overhang=" + json.dumps(row["region"]["edge_overhang_pt"], sort_keys=True),
        )
    print("PROVENANCE_REPAIR_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


def main() -> int:
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
