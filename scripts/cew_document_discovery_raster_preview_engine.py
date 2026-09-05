#!/usr/bin/env python3
"""Memory-bounded raster fallback for CEW Document Discovery preview.

This engine is used only when the preferred bounded vector preview cannot run
within the runtime resource envelope. It rasterizes pages at low resolution,
finds ink-bearing tiles, and emits non-semantic graphic primitive candidates.
It never creates semantic truth, learning receipts, canonical writes or
structural identity.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

import pymupdf

import cew_new_project_preacquisition as base

RASTER_SAFE_EXTRACTOR_VERSION = "CEW_DOCUMENT_DISCOVERY_RASTER_SAFE_PREVIEW_v1"
MAX_PREVIEW_PAGES_ANALYZED = 6
MAX_RASTER_DIMENSION_PX = 900
RASTER_GRID_COLUMNS = 24
RASTER_GRID_ROWS = 18
RASTER_DARK_THRESHOLD = 245
RASTER_MIN_DARK_RATIO = 0.012
MAX_TEXT_BLOCKS_PER_PAGE = 500
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
        "extractor_version": RASTER_SAFE_EXTRACTOR_VERSION,
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
        "extractor_version": RASTER_SAFE_EXTRACTOR_VERSION,
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


def _tile_bbox(col: int, row: int) -> dict[str, float]:
    x0 = col / RASTER_GRID_COLUMNS
    y0 = row / RASTER_GRID_ROWS
    x1 = (col + 1) / RASTER_GRID_COLUMNS
    y1 = (row + 1) / RASTER_GRID_ROWS
    return {
        "x": round(x0, 10),
        "y": round(y0, 10),
        "w": round(x1 - x0, 10),
        "h": round(y1 - y0, 10),
    }


def _ink_tiles(page: pymupdf.Page) -> tuple[list[tuple[int, int, float]], dict[str, int]]:
    page_rect = page.rect
    longest = max(float(page_rect.width), float(page_rect.height), 1.0)
    scale = min(1.0, MAX_RASTER_DIMENSION_PX / longest)
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(scale, scale),
        colorspace=pymupdf.csGRAY,
        alpha=False,
        annots=False,
    )
    width = int(pix.width)
    height = int(pix.height)
    stride = int(pix.stride)
    samples = pix.samples_mv if hasattr(pix, "samples_mv") else memoryview(pix.samples)
    active: list[tuple[int, int, float]] = []

    for row in range(RASTER_GRID_ROWS):
        y0 = (row * height) // RASTER_GRID_ROWS
        y1 = max(y0 + 1, ((row + 1) * height) // RASTER_GRID_ROWS)
        for col in range(RASTER_GRID_COLUMNS):
            x0 = (col * width) // RASTER_GRID_COLUMNS
            x1 = max(x0 + 1, ((col + 1) * width) // RASTER_GRID_COLUMNS)
            tile_w = max(1, x1 - x0)
            tile_h = max(1, y1 - y0)
            step = max(1, min(tile_w, tile_h) // 12)
            dark = 0
            total = 0
            for y in range(y0, y1, step):
                base_offset = y * stride
                for x in range(x0, x1, step):
                    total += 1
                    if samples[base_offset + x] < RASTER_DARK_THRESHOLD:
                        dark += 1
            ratio = (dark / total) if total else 0.0
            if ratio >= RASTER_MIN_DARK_RATIO:
                active.append((col, row, ratio))

    return active, {"raster_width_px": width, "raster_height_px": height}


def _extract_page(page: pymupdf.Page, *, source_version_id: str, source_sha256: str,
                  page_index: int, total_candidates_before: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    page_rect = page.rect
    budget_left = max(0, MAX_TOTAL_CANDIDATES - total_candidates_before)
    candidates: list[dict[str, Any]] = []
    if budget_left <= 0:
        return [], {
            "page_index": page_index,
            "width_pt": round(float(page_rect.width), 6),
            "height_pt": round(float(page_rect.height), 6),
            "rotation": int(page.rotation),
            "modality": "NOT_ANALYZED_BUDGET_EXHAUSTED",
            "primitive_candidate_count": 0,
            "bounded_preview": True,
            "budget_exhausted": True,
            "vector_extraction_state": "NOT_ATTEMPTED_RASTER_SAFE_MODE",
        }

    tiles, raster_meta = _ink_tiles(page)
    for col, row, dark_ratio in tiles:
        if len(candidates) >= budget_left:
            break
        _append_candidate(candidates, _candidate(
            source_version_id=source_version_id,
            source_sha256=source_sha256,
            page_index=page_index,
            bbox=_tile_bbox(col, row),
            primitive_family="UNKNOWN_GRAPHIC_GROUP",
            detector="PYMUPDF_RASTER_INK_TILE_BOUNDED",
            stats={
                "grid_col": col,
                "grid_row": row,
                "item_count": 1,
                "dark_ratio": round(float(dark_ratio), 6),
                "filled": False,
            },
        ))

    text_blocks = page.get_text("blocks")
    text_limit = min(len(text_blocks), MAX_TEXT_BLOCKS_PER_PAGE, max(0, budget_left - len(candidates)))
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
            detector="PYMUPDF_TEXT_BLOCK_RASTER_SAFE",
            stats={
                "block_index": block_index,
                "item_count": 1,
                "text_length_bucket": "EMPTY" if not text.strip() else ("SHORT" if len(text) < 40 else "LONG"),
            },
        )):
            break

    budget_exhausted = len(candidates) >= budget_left
    return candidates, {
        "page_index": page_index,
        "width_pt": round(float(page_rect.width), 6),
        "height_pt": round(float(page_rect.height), 6),
        "rotation": int(page.rotation),
        "modality": "RASTERIZED_BOUNDED_PREVIEW",
        "vector_drawing_count": None,
        "vector_paths_materialized": 0,
        "vector_paths_truncated": True,
        "vector_extraction_state": "NOT_ATTEMPTED_RASTER_SAFE_MODE",
        "text_block_count": len(text_blocks),
        "text_blocks_materialized": min(len(text_blocks), text_limit),
        "text_blocks_truncated": len(text_blocks) > text_limit,
        "raster_ink_tile_count": len(tiles),
        "primitive_candidate_count": len(candidates),
        "semantic_object_prior_used": False,
        "bounded_preview": True,
        "budget_exhausted": budget_exhausted,
        **raster_meta,
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
    truncated = source_page_count > len(pages) or any(bool(page.get("budget_exhausted")) for page in pages)
    report_identity = {
        "source_sha256": digest,
        "extractor_version": RASTER_SAFE_EXTRACTOR_VERSION,
        "candidate_ids": [row["candidate_id"] for row in all_candidates],
        "cluster_ids": [row["cluster_id"] for row in clusters],
        "bounded_preview": True,
        "raster_safe": True,
    }
    return {
        "schema": base.SCHEMA,
        "contract_schema": base.CONTRACT_SCHEMA,
        "mode": "NEW_PROJECT_ZERO_SEMANTIC_PRIOR",
        "analysis_scope": "BOUNDED_INTERACTIVE_PREVIEW",
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "extractor_version": RASTER_SAFE_EXTRACTOR_VERSION,
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
            "max_raster_dimension_px": MAX_RASTER_DIMENSION_PX,
            "raster_grid_columns": RASTER_GRID_COLUMNS,
            "raster_grid_rows": RASTER_GRID_ROWS,
            "max_text_blocks_per_page": MAX_TEXT_BLOCKS_PER_PAGE,
            "max_total_candidates": MAX_TOTAL_CANDIDATES,
            "truncated": truncated,
        },
        "preview_fallback_mode": "RASTER_SAFE_RESOURCE_BOUNDED",
        "known_object_types_required": False,
        "semantic_labels_assigned_automatically": False,
        "authority": dict(base.AUTHORITY),
        "next_gate": "HUMAN_DOCUMENT_AND_GRAPHIC_TRIAGE_REQUIRED",
    }
