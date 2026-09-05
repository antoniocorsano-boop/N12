#!/usr/bin/env python3
"""Deterministic tiled raster evidence fallback for CEW Document Discovery.

The engine observes page pixels without semantic object prior. It creates a
resource-bounded RasterPlan, captures overlapping grayscale evidence tiles,
derives connected non-semantic graphic regions, reconciles regions across tile
boundaries, and reports measurable page coverage and an explicit quality gate.

It never creates project truth, learning receipts, canonical writes, structural
identity or engineering authority.
"""
from __future__ import annotations

from collections import deque
from hashlib import sha256
import json
import math
from typing import Any

import pymupdf

import cew_new_project_preacquisition as base

RASTER_SAFE_EXTRACTOR_VERSION = "CEW_DOCUMENT_DISCOVERY_RASTER_EVIDENCE_ENGINE_v2"
RASTER_CONTRACT_SCHEMA = "CEW_RASTER_EVIDENCE_ENGINE_CONTRACT_v2"
MAX_PREVIEW_PAGES_ANALYZED = 6
TARGET_SCALE_PX_PER_PT = 1.5
MIN_TRUSTED_SCALE_PX_PER_PT = 0.85
MIN_SCALE_PX_PER_PT = 0.30
TILE_RENDER_MAX_PX = 1024
TILE_OVERLAP_PX = 24
TILE_CORE_PX = TILE_RENDER_MAX_PX - (2 * TILE_OVERLAP_PX)
MAX_TILES_PER_PAGE = 96
SIGNAL_CELL_PX = 3
BACKGROUND_SAMPLE_STEP_PX = 8
BACKGROUND_PERCENTILE = 0.90
INK_THRESHOLD_DELTA = 12
MIN_COMPONENT_RAW_CELLS = 2
MIN_COMPONENT_SPAN_CELLS = 4
MAX_REGIONS_PER_TILE = 512
MAX_TOTAL_CANDIDATES = 6000
BOUNDARY_MERGE_GAP_PT = 2.0


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, payload: Any, length: int = 20) -> str:
    return f"{prefix}{sha256(_canonical(payload).encode('utf-8')).hexdigest()[:length]}"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _bbox_dict(rect: pymupdf.Rect, page_rect: pymupdf.Rect) -> dict[str, float]:
    clipped = pymupdf.Rect(rect) & page_rect
    if clipped.is_empty or clipped.width <= 0 or clipped.height <= 0:
        raise ValueError("EMPTY_GRAPHIC_BBOX")
    return {
        "x": round(float(clipped.x0 / page_rect.width), 10),
        "y": round(float(clipped.y0 / page_rect.height), 10),
        "w": round(float(clipped.width / page_rect.width), 10),
        "h": round(float(clipped.height / page_rect.height), 10),
    }


def _page_rect_tuple(rect: pymupdf.Rect) -> tuple[float, float, float, float]:
    return tuple(round(float(value), 6) for value in (rect.x0, rect.y0, rect.x1, rect.y1))


def _plan_page(page_rect: pymupdf.Rect, page_index: int, source_sha256: str) -> dict[str, Any]:
    width_pt = max(float(page_rect.width), 1.0)
    height_pt = max(float(page_rect.height), 1.0)
    scale = TARGET_SCALE_PX_PER_PT

    def grid_for(candidate_scale: float) -> tuple[int, int, int, float]:
        core_span_pt = TILE_CORE_PX / candidate_scale
        columns = max(1, math.ceil(width_pt / core_span_pt))
        rows = max(1, math.ceil(height_pt / core_span_pt))
        return columns, rows, columns * rows, core_span_pt

    columns, rows, tile_count, core_span_pt = grid_for(scale)
    while tile_count > MAX_TILES_PER_PAGE and scale > MIN_SCALE_PX_PER_PT:
        scale = max(MIN_SCALE_PX_PER_PT, scale * 0.90)
        columns, rows, tile_count, core_span_pt = grid_for(scale)
        if scale == MIN_SCALE_PX_PER_PT:
            break

    overlap_pt = TILE_OVERLAP_PX / scale
    tiles: list[dict[str, Any]] = []
    for row in range(rows):
        for col in range(columns):
            core = pymupdf.Rect(
                col * core_span_pt,
                row * core_span_pt,
                min(width_pt, (col + 1) * core_span_pt),
                min(height_pt, (row + 1) * core_span_pt),
            )
            clip = pymupdf.Rect(
                max(0.0, core.x0 - overlap_pt),
                max(0.0, core.y0 - overlap_pt),
                min(width_pt, core.x1 + overlap_pt),
                min(height_pt, core.y1 + overlap_pt),
            )
            identity = {
                "source_sha256": source_sha256,
                "page_index": page_index,
                "row": row,
                "col": col,
                "core_bbox_pt": _page_rect_tuple(core),
                "clip_bbox_pt": _page_rect_tuple(clip),
                "scale": round(scale, 8),
            }
            tiles.append({
                "tile_id": _stable_id("RT-", identity, 18),
                "row": row,
                "col": col,
                "core_bbox_pt": _page_rect_tuple(core),
                "clip_bbox_pt": _page_rect_tuple(clip),
            })

    plan_identity = {
        "engine": RASTER_SAFE_EXTRACTOR_VERSION,
        "source_sha256": source_sha256,
        "page_index": page_index,
        "page_bbox_pt": _page_rect_tuple(page_rect),
        "scale": round(scale, 8),
        "overlap_px": TILE_OVERLAP_PX,
        "tile_ids": [tile["tile_id"] for tile in tiles],
    }
    return {
        "schema": "CEW_RASTER_PLAN_v2",
        "plan_id": _stable_id("RP-", plan_identity, 20),
        "strategy": "TILED_FULL_COVERAGE",
        "page_index": page_index,
        "page_width_pt": round(width_pt, 6),
        "page_height_pt": round(height_pt, 6),
        "target_scale_px_per_pt": TARGET_SCALE_PX_PER_PT,
        "effective_scale_px_per_pt": round(scale, 8),
        "trusted_scale_min_px_per_pt": MIN_TRUSTED_SCALE_PX_PER_PT,
        "scale_degraded": scale < TARGET_SCALE_PX_PER_PT,
        "scale_below_trusted_minimum": scale < MIN_TRUSTED_SCALE_PX_PER_PT,
        "tile_overlap_px": TILE_OVERLAP_PX,
        "tile_core_px": TILE_CORE_PX,
        "tile_columns": columns,
        "tile_rows": rows,
        "tiles_planned": len(tiles),
        "tile_budget_exceeded": len(tiles) > MAX_TILES_PER_PAGE,
        "tiles": tiles,
    }


def _percentile_background(samples: memoryview, width: int, height: int, stride: int) -> int:
    histogram = [0] * 256
    total = 0
    step = BACKGROUND_SAMPLE_STEP_PX
    for y in range(0, height, step):
        offset = y * stride
        for x in range(0, width, step):
            histogram[int(samples[offset + x])] += 1
            total += 1
    if total == 0:
        return 255
    target = max(1, math.ceil(total * BACKGROUND_PERCENTILE))
    cumulative = 0
    for value, count in enumerate(histogram):
        cumulative += count
        if cumulative >= target:
            return value
    return 255


def _raw_signal_mask(
    samples: memoryview,
    width: int,
    height: int,
    stride: int,
    threshold: int,
) -> tuple[bytearray, int, int, int]:
    grid_w = max(1, math.ceil(width / SIGNAL_CELL_PX))
    grid_h = max(1, math.ceil(height / SIGNAL_CELL_PX))
    raw = bytearray(grid_w * grid_h)
    raw_count = 0
    for gy in range(grid_h):
        y0 = gy * SIGNAL_CELL_PX
        y1 = min(height, y0 + SIGNAL_CELL_PX)
        for gx in range(grid_w):
            x0 = gx * SIGNAL_CELL_PX
            x1 = min(width, x0 + SIGNAL_CELL_PX)
            active = False
            for y in range(y0, y1):
                offset = y * stride
                for x in range(x0, x1):
                    if int(samples[offset + x]) < threshold:
                        active = True
                        break
                if active:
                    break
            if active:
                idx = gy * grid_w + gx
                raw[idx] = 1
                raw_count += 1
    return raw, grid_w, grid_h, raw_count


def _dilate(raw: bytearray, grid_w: int, grid_h: int) -> bytearray:
    detected = bytearray(raw)
    for idx, value in enumerate(raw):
        if not value:
            continue
        y, x = divmod(idx, grid_w)
        for dy in (-1, 0, 1):
            ny = y + dy
            if ny < 0 or ny >= grid_h:
                continue
            start = ny * grid_w
            for dx in (-1, 0, 1):
                nx = x + dx
                if 0 <= nx < grid_w:
                    detected[start + nx] = 1
    return detected


def _components(raw: bytearray, detected: bytearray, grid_w: int, grid_h: int) -> list[dict[str, int]]:
    seen = bytearray(len(detected))
    components: list[dict[str, int]] = []
    for start_idx, active in enumerate(detected):
        if not active or seen[start_idx]:
            continue
        queue: deque[int] = deque([start_idx])
        seen[start_idx] = 1
        raw_cells = 0
        min_x = grid_w
        min_y = grid_h
        max_x = -1
        max_y = -1
        detection_cells = 0
        while queue:
            idx = queue.popleft()
            y, x = divmod(idx, grid_w)
            detection_cells += 1
            if raw[idx]:
                raw_cells += 1
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
            for dy in (-1, 0, 1):
                ny = y + dy
                if ny < 0 or ny >= grid_h:
                    continue
                base_idx = ny * grid_w
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx = x + dx
                    if nx < 0 or nx >= grid_w:
                        continue
                    nidx = base_idx + nx
                    if detected[nidx] and not seen[nidx]:
                        seen[nidx] = 1
                        queue.append(nidx)
        if raw_cells == 0:
            continue
        span_x = max_x - min_x + 1
        span_y = max_y - min_y + 1
        if raw_cells < MIN_COMPONENT_RAW_CELLS and max(span_x, span_y) < MIN_COMPONENT_SPAN_CELLS:
            continue
        components.append({
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "raw_cells": raw_cells,
            "detection_cells": detection_cells,
            "span_x": span_x,
            "span_y": span_y,
        })
    components.sort(key=lambda row: (row["min_y"], row["min_x"], row["max_y"], row["max_x"]))
    return components


def _family(component: dict[str, int]) -> str:
    span_x = max(1, component["span_x"])
    span_y = max(1, component["span_y"])
    ratio = span_x / span_y
    raw_density = component["raw_cells"] / max(1, span_x * span_y)
    if ratio >= 4.0 or ratio <= 0.25:
        return "LINEAR_STROKE_GROUP"
    if raw_density >= 0.55:
        return "FILLED_OR_HATCHED_REGION"
    if component["raw_cells"] >= 24:
        return "COMPLEX_VECTOR_GROUP"
    return "UNKNOWN_GRAPHIC_GROUP"


def _component_page_rect(
    component: dict[str, int],
    clip: pymupdf.Rect,
    scale: float,
    page_rect: pymupdf.Rect,
) -> pymupdf.Rect:
    x0 = clip.x0 + (component["min_x"] * SIGNAL_CELL_PX) / scale
    y0 = clip.y0 + (component["min_y"] * SIGNAL_CELL_PX) / scale
    x1 = clip.x0 + ((component["max_x"] + 1) * SIGNAL_CELL_PX) / scale
    y1 = clip.y0 + ((component["max_y"] + 1) * SIGNAL_CELL_PX) / scale
    rect = pymupdf.Rect(x0, y0, x1, y1) & page_rect
    if rect.is_empty or rect.width <= 0 or rect.height <= 0:
        raise ValueError("EMPTY_GRAPHIC_BBOX")
    return rect


def _capture_tile(page: pymupdf.Page, page_rect: pymupdf.Rect, plan: dict[str, Any], tile: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scale = float(plan["effective_scale_px_per_pt"])
    clip = pymupdf.Rect(tile["clip_bbox_pt"])
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(scale, scale),
        clip=clip,
        colorspace=pymupdf.csGRAY,
        alpha=False,
        annots=False,
    )
    width = int(pix.width)
    height = int(pix.height)
    stride = int(pix.stride)
    samples = pix.samples_mv if hasattr(pix, "samples_mv") else memoryview(pix.samples)
    background = _percentile_background(samples, width, height, stride)
    threshold = int(_clamp(background - INK_THRESHOLD_DELTA, 80, 248))
    raw, grid_w, grid_h, raw_count = _raw_signal_mask(samples, width, height, stride, threshold)
    detected = _dilate(raw, grid_w, grid_h)
    components = _components(raw, detected, grid_w, grid_h)
    truncated = len(components) > MAX_REGIONS_PER_TILE
    if truncated:
        components = sorted(
            components,
            key=lambda row: (-row["raw_cells"], -max(row["span_x"], row["span_y"]), row["min_y"], row["min_x"]),
        )[:MAX_REGIONS_PER_TILE]
        components.sort(key=lambda row: (row["min_y"], row["min_x"], row["max_y"], row["max_x"]))

    regions: list[dict[str, Any]] = []
    for component in components:
        try:
            page_region = _component_page_rect(component, clip, scale, page_rect)
        except ValueError:
            continue
        regions.append({
            "page_bbox_pt": _page_rect_tuple(page_region),
            "primitive_family": _family(component),
            "supporting_tile_ids": [tile["tile_id"]],
            "tile_row": int(tile["row"]),
            "tile_col": int(tile["col"]),
            "raw_signal_cells": int(component["raw_cells"]),
            "detection_cells": int(component["detection_cells"]),
            "component_span_x_cells": int(component["span_x"]),
            "component_span_y_cells": int(component["span_y"]),
            "background_estimate": background,
            "threshold_used": threshold,
        })

    total_cells = max(1, grid_w * grid_h)
    return regions, {
        "tile_id": tile["tile_id"],
        "row": tile["row"],
        "col": tile["col"],
        "core_bbox_pt": tile["core_bbox_pt"],
        "clip_bbox_pt": tile["clip_bbox_pt"],
        "raster_width_px": width,
        "raster_height_px": height,
        "background_estimate": background,
        "threshold_used": threshold,
        "raw_signal_cells": raw_count,
        "signal_cell_count": total_cells,
        "signal_cell_ratio": round(raw_count / total_cells, 10),
        "derived_region_count": len(regions),
        "region_budget_truncated": truncated,
        "status": "COMPLETE",
    }


def _rect_distance_or_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    x_overlap = min(ax1, bx1) - max(ax0, bx0)
    y_overlap = min(ay1, by1) - max(ay0, by0)
    x_gap = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    y_gap = max(0.0, max(ay0, by0) - min(ay1, by1))
    return x_overlap, y_overlap, x_gap, y_gap


def _mergeable(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a["primitive_family"] != b["primitive_family"]:
        return False
    if abs(int(a["tile_row"]) - int(b["tile_row"])) > 1 or abs(int(a["tile_col"]) - int(b["tile_col"])) > 1:
        return False
    if int(a["tile_row"]) == int(b["tile_row"]) and int(a["tile_col"]) == int(b["tile_col"]):
        return False
    x_overlap, y_overlap, x_gap, y_gap = _rect_distance_or_overlap(a["page_bbox_pt"], b["page_bbox_pt"])
    if x_overlap > 0 and y_overlap > 0:
        return True
    if x_gap <= BOUNDARY_MERGE_GAP_PT and y_overlap > 0:
        return True
    if y_gap <= BOUNDARY_MERGE_GAP_PT and x_overlap > 0:
        return True
    return False


def _reconcile_regions(regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not regions:
        return []
    parent = list(range(len(regions)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            if root_left < root_right:
                parent[root_right] = root_left
            else:
                parent[root_left] = root_right

    ordered = sorted(range(len(regions)), key=lambda idx: (regions[idx]["page_bbox_pt"][0], regions[idx]["page_bbox_pt"][1]))
    for position, left_idx in enumerate(ordered):
        left = regions[left_idx]
        left_x1 = float(left["page_bbox_pt"][2])
        for right_idx in ordered[position + 1:]:
            right = regions[right_idx]
            if float(right["page_bbox_pt"][0]) > left_x1 + BOUNDARY_MERGE_GAP_PT:
                break
            if _mergeable(left, right):
                union(left_idx, right_idx)

    grouped: dict[int, list[dict[str, Any]]] = {}
    for idx, region in enumerate(regions):
        grouped.setdefault(find(idx), []).append(region)

    merged: list[dict[str, Any]] = []
    for members in grouped.values():
        members.sort(key=lambda row: (row["page_bbox_pt"], row["supporting_tile_ids"]))
        x0 = min(row["page_bbox_pt"][0] for row in members)
        y0 = min(row["page_bbox_pt"][1] for row in members)
        x1 = max(row["page_bbox_pt"][2] for row in members)
        y1 = max(row["page_bbox_pt"][3] for row in members)
        supporting = sorted({tile_id for row in members for tile_id in row["supporting_tile_ids"]})
        merged.append({
            "page_bbox_pt": (round(x0, 6), round(y0, 6), round(x1, 6), round(y1, 6)),
            "primitive_family": members[0]["primitive_family"],
            "supporting_tile_ids": supporting,
            "raw_signal_cells": sum(int(row["raw_signal_cells"]) for row in members),
            "detection_cells": sum(int(row["detection_cells"]) for row in members),
            "component_count": len(members),
            "background_estimate_min": min(int(row["background_estimate"]) for row in members),
            "background_estimate_max": max(int(row["background_estimate"]) for row in members),
            "threshold_used_min": min(int(row["threshold_used"]) for row in members),
            "threshold_used_max": max(int(row["threshold_used"]) for row in members),
        })
    merged.sort(key=lambda row: (row["page_bbox_pt"], row["primitive_family"], row["supporting_tile_ids"]))
    return merged


def _candidate(
    *,
    source_version_id: str,
    source_sha256: str,
    page_index: int,
    page_rect: pymupdf.Rect,
    raster_plan_id: str,
    region: dict[str, Any],
) -> dict[str, Any]:
    rect = pymupdf.Rect(region["page_bbox_pt"])
    bbox = _bbox_dict(rect, page_rect)
    primitive_family = str(region["primitive_family"])
    signature = {
        "primitive_family": primitive_family,
        "aspect_bucket": base._aspect_bucket(bbox),
        "area_bucket": base._area_bucket(bbox),
        "complexity_bucket": base._complexity_bucket(int(region.get("component_count", 1))),
        "filled": primitive_family == "FILLED_OR_HATCHED_REGION",
        "stroke_width_bucket": "RASTER_DERIVED",
    }
    identity = {
        "source_sha256": source_sha256,
        "page_index": page_index,
        "bbox": bbox,
        "raster_plan_id": raster_plan_id,
        "extractor_version": RASTER_SAFE_EXTRACTOR_VERSION,
        "signature": signature,
    }
    signal_metrics = {
        "raw_signal_cells": int(region["raw_signal_cells"]),
        "detection_cells": int(region["detection_cells"]),
        "component_count": int(region["component_count"]),
        "background_estimate_min": int(region["background_estimate_min"]),
        "background_estimate_max": int(region["background_estimate_max"]),
        "threshold_used_min": int(region["threshold_used_min"]),
        "threshold_used_max": int(region["threshold_used_max"]),
    }
    return {
        "candidate_id": _stable_id("GPC-", identity),
        "source_version_id": source_version_id,
        "source_sha256": source_sha256,
        "page_index": page_index,
        "coordinate_system": "NORMALIZED_0_1",
        "bbox": bbox,
        "page_bbox_pt": list(region["page_bbox_pt"]),
        "primitive_family": primitive_family,
        "detector": "PYMUPDF_RASTER_CONNECTED_REGION_TILED_V2",
        "extractor_version": RASTER_SAFE_EXTRACTOR_VERSION,
        "raster_plan_id": raster_plan_id,
        "supporting_tile_ids": list(region["supporting_tile_ids"]),
        "signal_metrics": signal_metrics,
        "aggregation_method": "DILATED_CONNECTIVITY_RAW_GEOMETRY_WITH_CROSS_TILE_RECONCILIATION",
        "feature_signature": signature,
        "statistics": {
            "item_count": int(region["component_count"]),
            "filled": primitive_family == "FILLED_OR_HATCHED_REGION",
            "stroke_width_bucket": "RASTER_DERIVED",
            **signal_metrics,
        },
        "semantic_meaning": None,
        "semantic_authority": "NONE",
    }


def _extract_page(
    page: pymupdf.Page,
    *,
    source_version_id: str,
    source_sha256: str,
    page_index: int,
    total_candidates_before: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    page_rect = page.rect
    plan = _plan_page(page_rect, page_index, source_sha256)
    raw_regions: list[dict[str, Any]] = []
    tile_reports: list[dict[str, Any]] = []
    failed_tiles = 0
    for tile in plan["tiles"]:
        try:
            regions, tile_report = _capture_tile(page, page_rect, plan, tile)
        except Exception:
            failed_tiles += 1
            tile_reports.append({
                "tile_id": tile["tile_id"],
                "row": tile["row"],
                "col": tile["col"],
                "core_bbox_pt": tile["core_bbox_pt"],
                "clip_bbox_pt": tile["clip_bbox_pt"],
                "status": "FAILED",
                "failure_reason": "RASTER_TILE_CAPTURE_FAILED",
            })
            continue
        raw_regions.extend(regions)
        tile_reports.append(tile_report)

    completed_tiles = len(plan["tiles"]) - failed_tiles
    coverage_ratio = completed_tiles / max(1, len(plan["tiles"]))
    reconciled = _reconcile_regions(raw_regions)
    budget_left = max(0, MAX_TOTAL_CANDIDATES - total_candidates_before)
    candidate_budget_truncated = len(reconciled) > budget_left
    if candidate_budget_truncated:
        reconciled = reconciled[:budget_left]
    candidates = [
        _candidate(
            source_version_id=source_version_id,
            source_sha256=source_sha256,
            page_index=page_index,
            page_rect=page_rect,
            raster_plan_id=plan["plan_id"],
            region=region,
        )
        for region in reconciled
    ]

    raw_signal_cells = sum(int(tile.get("raw_signal_cells", 0)) for tile in tile_reports if tile.get("status") == "COMPLETE")
    signal_cells = sum(int(tile.get("signal_cell_count", 0)) for tile in tile_reports if tile.get("status") == "COMPLETE")
    signal_present = raw_signal_cells > 0
    region_budget_truncated = any(bool(tile.get("region_budget_truncated")) for tile in tile_reports)
    full_coverage = coverage_ratio == 1.0 and failed_tiles == 0
    blank_observed = full_coverage and not signal_present

    reasons: list[str] = []
    if not full_coverage:
        reasons.append("RASTER_COVERAGE_INCOMPLETE")
    if plan["scale_below_trusted_minimum"]:
        reasons.append("RASTER_SCALE_BELOW_TRUSTED_MINIMUM")
    if region_budget_truncated or candidate_budget_truncated:
        reasons.append("RASTER_REGION_BUDGET_TRUNCATED")
    if signal_present and not candidates:
        reasons.append("INCONCLUSIVE_RASTER_DETECTION")

    quality_status = "INCONCLUSIVE" if reasons else "READY"
    page_state = "PAGE_BLANK_OBSERVED" if blank_observed and quality_status == "READY" else (
        "RASTER_SIGNAL_PRESENT" if signal_present else "RASTER_SIGNAL_ABSENT"
    )

    return candidates, {
        "page_index": page_index,
        "width_pt": round(float(page_rect.width), 6),
        "height_pt": round(float(page_rect.height), 6),
        "rotation": int(page.rotation),
        "modality": "RASTER_TILED_EVIDENCE_PREVIEW",
        "raster_plan": plan,
        "raster_plan_id": plan["plan_id"],
        "tiles_planned": len(plan["tiles"]),
        "tiles_completed": completed_tiles,
        "tiles_failed": failed_tiles,
        "coverage_ratio": round(coverage_ratio, 10),
        "required_coverage_ratio": 1.0,
        "effective_scale_px_per_pt": plan["effective_scale_px_per_pt"],
        "raw_signal_cells": raw_signal_cells,
        "signal_cell_count": signal_cells,
        "signal_cell_ratio": round(raw_signal_cells / max(1, signal_cells), 10),
        "signal_state": "PRESENT" if signal_present else "ABSENT",
        "page_observation_state": page_state,
        "raw_region_count": len(raw_regions),
        "reconciled_region_count": len(reconciled),
        "primitive_candidate_count": len(candidates),
        "region_budget_truncated": region_budget_truncated,
        "candidate_budget_truncated": candidate_budget_truncated,
        "quality_status": quality_status,
        "quality_reasons": reasons,
        "tile_reports": tile_reports,
        "vector_extraction_state": "NOT_ATTEMPTED_RASTER_EVIDENCE_MODE",
        "semantic_object_prior_used": False,
        "bounded_preview": True,
    }


def preacquire_preview_pdf(
    payload: bytes,
    *,
    source_version_id: str,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
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
    quality_reasons = sorted({reason for page in pages for reason in page.get("quality_reasons", [])})
    quality_status = "INCONCLUSIVE" if any(page.get("quality_status") == "INCONCLUSIVE" for page in pages) else "READY"
    blank_pages = [page["page_index"] for page in pages if page.get("page_observation_state") == "PAGE_BLANK_OBSERVED"]
    minimum_coverage = min((float(page.get("coverage_ratio", 0.0)) for page in pages), default=0.0)
    analysis_completeness = "FULL_REQUIRED_COVERAGE" if quality_status == "READY" else "INCONCLUSIVE_REQUIRED_COVERAGE_OR_DETECTION"
    bounded_scope = source_page_count > len(pages)

    report_identity = {
        "source_sha256": digest,
        "extractor_version": RASTER_SAFE_EXTRACTOR_VERSION,
        "raster_plan_ids": [page["raster_plan_id"] for page in pages],
        "candidate_ids": [row["candidate_id"] for row in all_candidates],
        "cluster_ids": [row["cluster_id"] for row in clusters],
        "quality_status": quality_status,
        "quality_reasons": quality_reasons,
    }
    return {
        "schema": base.SCHEMA,
        "contract_schema": base.CONTRACT_SCHEMA,
        "raster_contract_schema": RASTER_CONTRACT_SCHEMA,
        "mode": "NEW_PROJECT_ZERO_SEMANTIC_PRIOR",
        "analysis_scope": "BOUNDED_INTERACTIVE_PREVIEW",
        "analysis_completeness": analysis_completeness,
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
        "quality_gate": {
            "status": quality_status,
            "reasons": quality_reasons,
            "minimum_page_coverage_ratio": round(minimum_coverage, 10),
            "required_page_coverage_ratio": 1.0,
            "blank_pages_observed": blank_pages,
            "signal_present": any(page.get("signal_state") == "PRESENT" for page in pages),
            "candidate_count": len(all_candidates),
        },
        "preview_budget": {
            "max_pages_analyzed": MAX_PREVIEW_PAGES_ANALYZED,
            "target_scale_px_per_pt": TARGET_SCALE_PX_PER_PT,
            "minimum_trusted_scale_px_per_pt": MIN_TRUSTED_SCALE_PX_PER_PT,
            "tile_render_max_px": TILE_RENDER_MAX_PX,
            "tile_overlap_px": TILE_OVERLAP_PX,
            "max_tiles_per_page": MAX_TILES_PER_PAGE,
            "max_regions_per_tile": MAX_REGIONS_PER_TILE,
            "max_total_candidates": MAX_TOTAL_CANDIDATES,
            "truncated": bounded_scope,
        },
        "preview_fallback_mode": "RASTER_TILED_EVIDENCE_V2",
        "known_object_types_required": False,
        "semantic_labels_assigned_automatically": False,
        "authority": dict(base.AUTHORITY),
        "next_gate": "HUMAN_DOCUMENT_AND_GRAPHIC_TRIAGE_REQUIRED",
    }
