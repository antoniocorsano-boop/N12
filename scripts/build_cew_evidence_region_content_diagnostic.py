#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pymupdf

import build_cew_document_geometry_artifacts as geometry_builder
import build_cew_managed_f3_assets as managed_f3_builder

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_evidence_region_content_diagnostic"
MANIFEST = ASSET_ROOT / "manifest.json"
PAGE_REGISTRY = ROOT / "data/canonical/CEW_PAGE_REGISTRY_v1.csv"
CLASSIFICATIONS = (
    "VECTOR",
    "RASTER",
    "TEXT",
    "MIXED",
    "REGION_MAPPING_ERROR",
    "EMPTY",
)
DIAGNOSTIC_DPI = 150
PAGE_DIMENSION_TOLERANCE_PT = 0.5
INK_LUMA_THRESHOLD = 245
MIN_MEANINGFUL_INK_RATIO = 0.001
MIN_EMBEDDED_IMAGE_COVERAGE = 0.001
MAX_TEXT_PREVIEW_CHARS = 240


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _build_revision() -> str:
    env = os.getenv("RENDER_GIT_COMMIT") or os.getenv("VERCEL_GIT_COMMIT_SHA") or os.getenv("GITHUB_SHA")
    if env:
        return env.strip()
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _page_registry_row(page_id: str, source_version_id: str) -> dict[str, str] | None:
    matches = [
        row for row in _rows(PAGE_REGISTRY)
        if row.get("page_id", "").strip() == page_id
        and row.get("source_version_id", "").strip() == source_version_id
        and row.get("readiness_state", "").strip() == "READY"
    ]
    if len(matches) > 1:
        raise AssertionError(f"duplicate READY Page rows for {page_id}")
    return matches[0] if matches else None


def _rect_area(rect: pymupdf.Rect) -> float:
    if rect.is_empty or rect.is_infinite:
        return 0.0
    return max(0.0, float(rect.width)) * max(0.0, float(rect.height))


def _intersection_area(a: pymupdf.Rect, b: pymupdf.Rect) -> float:
    inter = a & b
    return _rect_area(inter)


def _drawing_metrics(page: pymupdf.Page, clip: pymupdf.Rect) -> dict[str, int]:
    path_count = 0
    item_count = 0
    for drawing in page.get_drawings():
        rect = drawing.get("rect")
        if rect is None:
            continue
        rect = pymupdf.Rect(rect)
        if _intersection_area(rect, clip) <= 0:
            continue
        path_count += 1
        item_count += len(drawing.get("items") or [])
    return {"path_count": path_count, "item_count": item_count}


def _text_metrics(page: pymupdf.Page, clip: pymupdf.Rect) -> dict[str, Any]:
    data = page.get_text("dict", clip=clip)
    spans: list[str] = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                value = str(span.get("text", "")).strip()
                if value:
                    spans.append(value)
    joined = " ".join(spans)
    preview = joined[:MAX_TEXT_PREVIEW_CHARS]
    return {
        "span_count": len(spans),
        "character_count": len(joined),
        "preview": preview,
        "preview_truncated": len(joined) > MAX_TEXT_PREVIEW_CHARS,
    }


def _image_metrics(page: pymupdf.Page, clip: pymupdf.Rect) -> dict[str, Any]:
    region_area = _rect_area(clip)
    intersecting: list[dict[str, Any]] = []
    covered_area = 0.0
    for info in page.get_image_info(xrefs=True):
        bbox_value = info.get("bbox")
        if not bbox_value:
            continue
        bbox = pymupdf.Rect(bbox_value)
        area = _intersection_area(bbox, clip)
        if area <= 0:
            continue
        covered_area += area
        intersecting.append(
            {
                "xref": int(info.get("xref") or 0),
                "intersection_area_pt2": round(area, 6),
            }
        )
    coverage = min(1.0, covered_area / region_area) if region_area > 0 else 0.0
    return {
        "embedded_image_count": len(intersecting),
        "approx_region_coverage": round(coverage, 8),
        "images": intersecting,
    }


def _render_crop(page: pymupdf.Page, clip: pymupdf.Rect, target: Path) -> dict[str, Any]:
    matrix = pymupdf.Matrix(DIAGNOSTIC_DPI / 72.0, DIAGNOSTIC_DPI / 72.0)
    pix = page.get_pixmap(matrix=matrix, clip=clip, colorspace=pymupdf.csGRAY, alpha=False)
    if pix.width <= 0 or pix.height <= 0:
        raise AssertionError("diagnostic crop produced zero dimensions")
    samples = bytes(pix.samples)
    ink = sum(1 for value in samples if value < INK_LUMA_THRESHOLD)
    ratio = ink / len(samples) if samples else 0.0
    target.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(target))
    return {
        "dpi": DIAGNOSTIC_DPI,
        "width_px": int(pix.width),
        "height_px": int(pix.height),
        "ink_luma_threshold": INK_LUMA_THRESHOLD,
        "ink_ratio": round(ratio, 8),
        "sha256": _sha256(target),
        "filename": target.name,
    }


def _classification(*, mapping_error: bool, drawing: dict[str, int], text: dict[str, Any], images: dict[str, Any], crop: dict[str, Any]) -> tuple[str, dict[str, bool]]:
    if mapping_error:
        return "REGION_MAPPING_ERROR", {
            "vector": False,
            "raster": False,
            "text": False,
            "rendered_ink": bool(crop.get("ink_ratio", 0.0) >= MIN_MEANINGFUL_INK_RATIO),
        }

    vector_signal = drawing["path_count"] > 0 or drawing["item_count"] > 0
    text_signal = text["span_count"] > 0
    raster_signal = (
        images["embedded_image_count"] > 0
        and images["approx_region_coverage"] >= MIN_EMBEDDED_IMAGE_COVERAGE
    )
    rendered_ink_signal = crop["ink_ratio"] >= MIN_MEANINGFUL_INK_RATIO

    signal_count = sum((vector_signal, raster_signal, text_signal))
    if signal_count >= 2:
        classification = "MIXED"
    elif vector_signal:
        classification = "VECTOR"
    elif raster_signal:
        classification = "RASTER"
    elif text_signal:
        classification = "TEXT"
    elif rendered_ink_signal:
        # Non-empty pixels without PDF vector/text objects are conservatively
        # treated as raster/form-like document content. This does not OCR or
        # authorize technical interpretation.
        classification = "RASTER"
    else:
        classification = "EMPTY"

    return classification, {
        "vector": vector_signal,
        "raster": raster_signal,
        "text": text_signal,
        "rendered_ink": rendered_ink_signal,
    }


def build_plan() -> dict[str, Any]:
    geometry_plan = geometry_builder.build_plan()
    region_ids = [
        region["evidence_region_id"]
        for source in geometry_plan["sources"]
        for region in source.get("evidence_regions", [])
    ]
    if len(region_ids) != 4 or len(set(region_ids)) != 4:
        raise AssertionError(f"PWB-005-R1 expects exactly four governed regions, got {region_ids}")
    return {
        "schema_version": "1.0",
        "diagnostic_contract": "CEW_PWB005_R1_EVIDENCE_REGION_CONTENT_DIAGNOSTIC_v1",
        "build_revision": _build_revision(),
        "archive_commit": geometry_plan["archive_commit"],
        "source_coverage": "4/4",
        "governed_region_count": 4,
        "classification_vocabulary": list(CLASSIFICATIONS),
        "diagnostic_dpi": DIAGNOSTIC_DPI,
        "page_dimension_tolerance_pt": PAGE_DIMENSION_TOLERANCE_PT,
        "minimum_meaningful_ink_ratio": MIN_MEANINGFUL_INK_RATIO,
        "sources": geometry_plan["sources"],
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "hva_execution_authorized": False,
    }


def _diagnose_region(source: dict[str, Any], region: dict[str, Any], pdf: Path, region_dir: Path) -> dict[str, Any]:
    doc = pymupdf.open(pdf)
    try:
        page_row = _page_registry_row(region["page_id"], source["source_version_id"])
        page_index = int(page_row["page_index"]) if page_row else 0
        if page_index < 0 or page_index >= doc.page_count:
            return {
                "evidence_region_id": region["evidence_region_id"],
                "source_code": source["source_code"],
                "source_version_id": source["source_version_id"],
                "page_id": region["page_id"],
                "classification": "REGION_MAPPING_ERROR",
                "mapping_error_reason": "PAGE_INDEX_OUT_OF_RANGE",
                "canonical_write_authorized": False,
                "engineering_authority_effect": "NONE",
            }

        page = doc[page_index]
        actual_width = float(page.rect.width)
        actual_height = float(page.rect.height)
        expected_width = float(page_row["source_width"]) if page_row else None
        expected_height = float(page_row["source_height"]) if page_row else None
        delta_width = abs(actual_width - expected_width) if expected_width is not None else None
        delta_height = abs(actual_height - expected_height) if expected_height is not None else None

        normalized = region["bbox_normalized"]
        x = float(normalized["x"])
        y = float(normalized["y"])
        width = float(normalized["width"])
        height = float(normalized["height"])
        normalized_valid = (
            0.0 <= x <= 1.0
            and 0.0 <= y <= 1.0
            and width > 0.0
            and height > 0.0
            and x + width <= 1.000001
            and y + height <= 1.000001
        )
        clip = pymupdf.Rect(
            x * actual_width,
            y * actual_height,
            (x + width) * actual_width,
            (y + height) * actual_height,
        )
        clip_inside_page = normalized_valid and _rect_area(clip) > 0 and _intersection_area(clip, page.rect) >= _rect_area(clip) - 1e-6
        dimension_match = (
            page_row is not None
            and delta_width is not None
            and delta_height is not None
            and delta_width <= PAGE_DIMENSION_TOLERANCE_PT
            and delta_height <= PAGE_DIMENSION_TOLERANCE_PT
        )
        mapping_error = not (page_row is not None and dimension_match and clip_inside_page)

        # Even on a mapping error, render only a safe clipped intersection when possible
        # so the diagnostic can explain the failure without interpreting it.
        safe_clip = clip & page.rect
        if safe_clip.is_empty:
            safe_clip = pymupdf.Rect(0, 0, min(1.0, actual_width), min(1.0, actual_height))

        drawing = _drawing_metrics(page, safe_clip) if not mapping_error else {"path_count": 0, "item_count": 0}
        text = _text_metrics(page, safe_clip) if not mapping_error else {"span_count": 0, "character_count": 0, "preview": "", "preview_truncated": False}
        images = _image_metrics(page, safe_clip) if not mapping_error else {"embedded_image_count": 0, "approx_region_coverage": 0.0, "images": []}
        crop_path = region_dir / f"{region['evidence_region_id']}.png"
        crop = _render_crop(page, safe_clip, crop_path)
        classification, signals = _classification(
            mapping_error=mapping_error,
            drawing=drawing,
            text=text,
            images=images,
            crop=crop,
        )

        mapping_reason = None
        if mapping_error:
            if page_row is None:
                mapping_reason = "PAGE_REGISTRY_ROW_MISSING"
            elif not dimension_match:
                mapping_reason = "PAGE_DIMENSION_MISMATCH"
            elif not normalized_valid:
                mapping_reason = "NORMALIZED_REGION_OUT_OF_BOUNDS"
            else:
                mapping_reason = "SOURCE_PAGE_CLIP_INVALID"

        return {
            "schema_version": "1.0",
            "evidence_region_id": region["evidence_region_id"],
            "reference_item": region["reference_item"],
            "source_code": source["source_code"],
            "source_id": source["source_id"],
            "source_version_id": source["source_version_id"],
            "source_sha256": source["sha256"],
            "page_id": region["page_id"],
            "transform_id": region["transform_id"],
            "page_index": page_index,
            "page_registry": {
                "present": page_row is not None,
                "expected_width_pt": expected_width,
                "expected_height_pt": expected_height,
                "actual_width_pt": round(actual_width, 6),
                "actual_height_pt": round(actual_height, 6),
                "width_delta_pt": round(delta_width, 6) if delta_width is not None else None,
                "height_delta_pt": round(delta_height, 6) if delta_height is not None else None,
                "dimension_match": dimension_match,
            },
            "region": {
                "coordinate_space": "NORMALIZED_0_1",
                "bbox_normalized": normalized,
                "bbox_source_pt": {
                    "x0": round(float(clip.x0), 6),
                    "y0": round(float(clip.y0), 6),
                    "x1": round(float(clip.x1), 6),
                    "y1": round(float(clip.y1), 6),
                },
                "normalized_valid": normalized_valid,
                "clip_inside_page": clip_inside_page,
            },
            "drawing": drawing,
            "text": text,
            "embedded_images": images,
            "crop": crop,
            "classification": classification,
            "classification_signals": signals,
            "mapping_error_reason": mapping_reason,
            "diagnostic_role": "DERIVED_NON_AUTHORITATIVE_CONTENT_CLASSIFICATION",
            "ocr_used": False,
            "technical_identity_authorized": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    finally:
        doc.close()


def build_diagnostic() -> dict[str, Any]:
    plan = build_plan()
    managed_f3_builder._ensure_archive_commit(plan["archive_commit"])
    if ASSET_ROOT.exists():
        shutil.rmtree(ASSET_ROOT)
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    region_dir = ASSET_ROOT / "regions"
    region_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="cew-pwb005-r1-") as temp_name:
        temp_root = Path(temp_name)
        for source in plan["sources"]:
            regions = source.get("evidence_regions", [])
            if not regions:
                continue
            pdf = temp_root / f"{source['source_code']}.pdf"
            managed_f3_builder._materialize_source(source, pdf)
            for region in regions:
                result = _diagnose_region(source, region, pdf, region_dir)
                result_path = region_dir / f"{region['evidence_region_id']}.json"
                result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                result["result_filename"] = result_path.name
                result["result_sha256"] = _sha256(result_path)
                results.append(result)

    counts = {name: 0 for name in CLASSIFICATIONS}
    for result in results:
        counts[result["classification"]] += 1

    manifest = {
        **{key: value for key, value in plan.items() if key != "sources"},
        "sources": [
            {
                "source_code": source["source_code"],
                "source_id": source["source_id"],
                "source_version_id": source["source_version_id"],
                "sha256": source["sha256"],
                "archive_commit": source["archive_commit"],
                "region_ids": [region["evidence_region_id"] for region in source.get("evidence_regions", [])],
            }
            for source in plan["sources"]
        ],
        "region_results": results,
        "classification_counts": counts,
        "diagnostic_state": "COMPLETE_WITH_FINDINGS",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "hva_execution_authorized": False,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R1_CONTENT_DIAGNOSTIC_BUILD = PASS")
    print(f"BUILD_REVISION = {manifest['build_revision']}")
    print("SOURCE_COVERAGE = 4/4")
    print("GOVERNED_REGION_COVERAGE = 4/4")
    for result in sorted(results, key=lambda item: item["evidence_region_id"]):
        print(
            "REGION_CONTENT",
            result["evidence_region_id"],
            "classification=" + result["classification"],
            "drawings=" + str(result["drawing"]["path_count"]),
            "text_spans=" + str(result["text"]["span_count"]),
            "images=" + str(result["embedded_images"]["embedded_image_count"]),
            "image_coverage=" + str(result["embedded_images"]["approx_region_coverage"]),
            "ink_ratio=" + str(result["crop"]["ink_ratio"]),
        )
    print("OCR_USED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("HVA_EXECUTION_AUTHORIZED = false")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-plan-only", action="store_true")
    args = parser.parse_args()
    plan = build_plan()
    if args.validate_plan_only:
        print("CEW_PWB005_R1_CONTENT_DIAGNOSTIC_PLAN = PASS")
        print(f"BUILD_REVISION = {plan['build_revision']}")
        print("SOURCE_COVERAGE = 4/4")
        print("GOVERNED_REGION_COVERAGE = 4/4")
        print("CLASSIFICATIONS = " + ",".join(CLASSIFICATIONS))
        print("CANONICAL_WRITE_AUTHORIZED = false")
        return 0
    build_diagnostic()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
