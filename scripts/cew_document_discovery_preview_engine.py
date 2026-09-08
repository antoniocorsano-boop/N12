#!/usr/bin/env python3
"""Resource-bounded zero-prior extraction for the interactive Document Discovery preview.

This is deliberately a PREVIEW engine, not the canonical full-document extractor.
It uses PyMuPDF ``get_cdrawings()`` for lower overhead and caps how much derived
candidate state is materialized in the web worker. Any cap hit is explicit in the
report. No semantic authority is created by truncation or by the preview itself.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

import pymupdf

import cew_new_project_preacquisition as base

PREVIEW_EXTRACTOR_VERSION = "CEW_DOCUMENT_DISCOVERY_BOUNDED_PREVIEW_CDRAWINGS_v1"
MAX_PREVIEW_PAGES_ANALYZED = 6
MAX_VECTOR_PATHS_PER_PAGE = 3000
MAX_TEXT_BLOCKS_PER_PAGE = 750
MAX_IMAGE_REGIONS_PER_PAGE = 250
MAX_TOTAL_CANDIDATES = 6000


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, payload: Any, length: int = 20) -> str:
    return f"{prefix}{sha256(_canonical(payload).encode('utf-8')).hexdigest()[:length]}"


def _candidate(*, source_version_id: str, source_sha256: str, page_index: int,
               bbox: dict[str, float], primitive_family: str, detector: str,
               stats: dict[str, Any]) -> dict[str, Any]:
    signature = {
        "primitive_family": primitive_family,
        "aspect_bucket": base._aspect_bucket(bbox),
        "area_bucket": base._area_bucket(bbox),
        "complexity_bucket": base._complexity_bucket(int(stats.get("item_count", 1))),
        "filled": bool(stats.get("filled", False)),
        "stroke_width_bucket": stats.get("stroke_width_bucket", "NA"),
    }
    identity = {
        "source_sha256": source_sha256,
        "page_index": page_index,
        "bbox": bbox,
        "detector": detector,
        "extractor_version": PREVIEW_EXTRACTOR_VERSION,
        "signature": signature,
    }
    return {
        "candidate_id": _stable_id("GPC-", identity),
        "source_version_id": source_version_id,
        "source_sha256": source_sha256,
        "page_index": page_index,
        "coordinate_system": "NORMALIZED_0_1",
        "bbox": bbox,
        "primitive_family": primitive_family,
        "detector": detector,
        "extractor_version": PREVIEW_EXTRACTOR_VERSION,
        "feature_signature": signature,
        "statistics": stats,
        "semantic_meaning": None,
        "semantic_authority": "NONE",
    }


def _append_candidate(candidates: list[dict[str, Any]], row: dict[str, Any]) -> bool:
    if len(candidates) >= MAX_TOTAL_CANDIDATES:
        return False
    candidates.append(row)
    return True


def _extract_page(page: pymupdf.Page, *, source_version_id: str, source_sha256: str,
                  page_index: int, total_candidates_before: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    page_rect = page.rect
    candidates: list[dict[str, Any]] = []
    budget_left = max(0, MAX_TOTAL_CANDIDATES - total_candidates_before)
    if budget_left <= 0:
        return [], {
            "page_index": page_index,
            "width_pt": round(float(page_rect.width), 6),
            "height_pt": round(float(page_rect.height), 6),
            "rotation": int(page.rotation),
            "modality": "NOT_ANALYZED_BUDGET_EXHAUSTED",
            "vector_drawing_count": None,
            "text_block_count": None,
            "raster_image_region_count": None,
            "primitive_candidate_count": 0,
            "semantic_object_prior_used": False,
            "bounded_preview": True,
            "budget_exhausted": True,
        }

    drawings = page.get_cdrawings()
    vector_count = len(drawings)
    vector_limit = min(vector_count, MAX_VECTOR_PATHS_PER_PAGE, budget_left)
    for drawing_index, drawing in enumerate(drawings[:vector_limit]):
        rect = drawing.get("rect")
        if rect is None:
            continue
        try:
            bbox = base._normalized_bbox(pymupdf.Rect(rect), page_rect)
        except ValueError:
            continue
        items = drawing.get("items") or []
        family = base._drawing_family(drawing)
        if not _append_candidate(candidates, _candidate(
            source_version_id=source_version_id,
            source_sha256=source_sha256,
            page_index=page_index,
            bbox=bbox,
            primitive_family=family,
            detector="PYMUPDF_GET_CDRAWINGS_BOUNDED",
            stats={
                "drawing_index": drawing_index,
                "item_count": len(items),
                "filled": drawing.get("fill") is not None,
                "stroke_width_bucket": base._stroke_width_bucket(drawing.get("width")),
            },
        )):
            break
    del drawings

    text_blocks = page.get_text("blocks")
    text_count = len(text_blocks)
    text_limit = min(text_count, MAX_TEXT_BLOCKS_PER_PAGE, max(0, budget_left - len(candidates)))
    for block_index, block in enumerate(text_blocks[:text_limit]):
        if len(block) < 4:
            continue
        try:
            bbox = base._normalized_bbox(
                pymupdf.Rect(float(block[0]), float(block[1]), float(block[2]), float(block[3])),
                page_rect,
            )
        except ValueError:
            continue
        text = str(block[4]) if len(block) > 4 else ""
        if not _append_candidate(candidates, _candidate(
            source_version_id=source_version_id,
            source_sha256=source_sha256,
            page_index=page_index,
            bbox=bbox,
            primitive_family="TEXT_BLOCK",
            detector="PYMUPDF_TEXT_BLOCK_BOUNDED",
            stats={
                "block_index": block_index,
                "item_count": 1,
                "text_length_bucket": "EMPTY" if not text.strip() else ("SHORT" if len(text) < 40 else "LONG"),
            },
        )):
            break
    del text_blocks

    image_regions = 0
    image_refs = page.get_images(full=True)
    seen_boxes: set[tuple[float, float, float, float]] = set()
    for image in image_refs:
        if image_regions >= MAX_IMAGE_REGIONS_PER_PAGE or len(candidates) >= budget_left:
            break
        if not image:
            continue
        xref = int(image[0])
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            rects = []
        for rect in rects:
            if image_regions >= MAX_IMAGE_REGIONS_PER_PAGE or len(candidates) >= budget_left:
                break
            try:
                bbox = base._normalized_bbox(pymupdf.Rect(rect), page_rect)
            except ValueError:
                continue
            key = (bbox["x"], bbox["y"], bbox["w"], bbox["h"])
            if key in seen_boxes:
                continue
            seen_boxes.add(key)
            image_regions += 1
            _append_candidate(candidates, _candidate(
                source_version_id=source_version_id,
                source_sha256=source_sha256,
                page_index=page_index,
                bbox=bbox,
                primitive_family="RASTER_IMAGE_REGION",
                detector="PYMUPDF_IMAGE_RECT_BOUNDED",
                stats={"xref": xref, "item_count": 1},
            ))

    if vector_count >= 8 and image_regions == 0:
        modality = "NATIVE_VECTOR"
    elif image_regions > 0 and vector_count < 5:
        modality = "RASTER_OR_SCANNED"
    elif image_regions > 0 and vector_count >= 5:
        modality = "MIXED"
    else:
        modality = "TEXT_OR_SPARSE"

    vector_truncated = vector_count > vector_limit
    text_truncated = text_count > text_limit
    budget_exhausted = len(candidates) >= budget_left
    return candidates, {
        "page_index": page_index,
        "width_pt": round(float(page_rect.width), 6),
        "height_pt": round(float(page_rect.height), 6),
        "rotation": int(page.rotation),
        "modality": modality,
        "vector_drawing_count": vector_count,
        "vector_paths_materialized": min(vector_count, vector_limit),
        "vector_paths_truncated": vector_truncated,
        "text_block_count": text_count,
        "text_blocks_materialized": min(text_count, text_limit),
        "text_blocks_truncated": text_truncated,
        "raster_image_region_count": image_regions,
        "primitive_candidate_count": len(candidates),
        "semantic_object_prior_used": False,
        "bounded_preview": True,
        "budget_exhausted": budget_exhausted,
    }


def preacquire_preview_pdf(payload: bytes, *, source_version_id: str,
                           expected_sha256: str | None = None) -> dict[str, Any]:
    if not payload.startswith(b"%PDF"):
        raise ValueError("PREACQUISITION_INPUT_NOT_PDF")
    source_version_id = str(source_version_id or "").strip()
    if not source_version_id:
        raise ValueError("SOURCE_VERSION_ID_REQUIRED")
    digest = sha256(payload).hexdigest()
    if expected_sha256 and digest.lower() != str(expected_sha256).strip().lower():
        raise ValueError("SOURCE_SHA256_MISMATCH")

    all_candidates: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    with pymupdf.open(stream=payload, filetype="pdf") as doc:
        source_page_count = int(doc.page_count)
        analyzed_count = min(source_page_count, MAX_PREVIEW_PAGES_ANALYZED)
        for page_index in range(analyzed_count):
            page = doc.load_page(page_index)
            candidates, preflight = _extract_page(
                page,
                source_version_id=source_version_id,
                source_sha256=digest,
                page_index=page_index,
                total_candidates_before=len(all_candidates),
            )
            all_candidates.extend(candidates)
            pages.append(preflight)
            if len(all_candidates) >= MAX_TOTAL_CANDIDATES:
                break

    clusters = base.cluster_primitives(all_candidates, digest)
    library_state, proposals, library_generation = base.match_clusters_to_library(clusters, None)
    triage = base.build_human_triage_queue(clusters, proposals)
    truncated = (
        source_page_count > len(pages)
        or any(bool(page.get("vector_paths_truncated") or page.get("text_blocks_truncated") or page.get("budget_exhausted")) for page in pages)
    )
    report_identity = {
        "source_sha256": digest,
        "extractor_version": PREVIEW_EXTRACTOR_VERSION,
        "candidate_ids": [row["candidate_id"] for row in all_candidates],
        "cluster_ids": [row["cluster_id"] for row in clusters],
        "bounded_preview": True,
    }
    return {
        "schema": base.SCHEMA,
        "contract_schema": base.CONTRACT_SCHEMA,
        "mode": "NEW_PROJECT_ZERO_SEMANTIC_PRIOR",
        "analysis_scope": "BOUNDED_INTERACTIVE_PREVIEW",
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "extractor_version": PREVIEW_EXTRACTOR_VERSION,
        "report_fingerprint": "sha256:" + sha256(_canonical(report_identity).encode("utf-8")).hexdigest(),
        "source_page_count": source_page_count,
        "page_count": len(pages),
        "pages_omitted_count": max(0, source_page_count - len(pages)),
        "pages": pages,
        "primitive_candidate_count": len(all_candidates),
        "primitive_candidates": all_candidates,
        "graphic_cluster_count": len(clusters),
        "graphic_clusters": clusters,
        "library_state": library_state,
        "library_generation": library_generation,
        "knowledge_match_proposals": proposals,
        "human_triage_queue": triage,
        "preview_budget": {
            "max_pages_analyzed": MAX_PREVIEW_PAGES_ANALYZED,
            "max_vector_paths_per_page": MAX_VECTOR_PATHS_PER_PAGE,
            "max_text_blocks_per_page": MAX_TEXT_BLOCKS_PER_PAGE,
            "max_image_regions_per_page": MAX_IMAGE_REGIONS_PER_PAGE,
            "max_total_candidates": MAX_TOTAL_CANDIDATES,
            "truncated": truncated,
        },
        "known_object_types_required": False,
        "semantic_labels_assigned_automatically": False,
        "authority": dict(base.AUTHORITY),
        "next_gate": "HUMAN_DOCUMENT_AND_GRAPHIC_TRIAGE_REQUIRED",
    }
