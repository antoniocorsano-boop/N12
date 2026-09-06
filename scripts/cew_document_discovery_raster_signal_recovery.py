#!/usr/bin/env python3
"""Adaptive, source-bound raster signal recovery for CEW Document Discovery.

This is a second-stage detector used only after the governed tiled raster engine
has completed full coverage but independent corroboration proves that the page
contains information while zero graphic primitives were recovered.

The recovery remains non-semantic and process-isolated. It uses deterministic
background-relative thresholds and connected regions to recover faint technical
linework without assigning object meaning, structural identity, or canonical
truth.
"""
from __future__ import annotations

from collections import deque
from hashlib import sha256
import json
import math
from typing import Any

import pymupdf

import cew_new_project_preacquisition as base

RECOVERY_EXTRACTOR_VERSION = "CEW_DOCUMENT_DISCOVERY_RASTER_SIGNAL_RECOVERY_v1"
RECOVERY_SCHEMA = "CEW_RASTER_SIGNAL_RECOVERY_v1"
MAX_PREVIEW_PAGES_ANALYZED = 6
TARGET_SCALE_PX_PER_PT = 1.8
MIN_SCALE_PX_PER_PT = 0.55
TILE_RENDER_MAX_PX = 960
TILE_OVERLAP_PX = 32
TILE_CORE_PX = TILE_RENDER_MAX_PX - (2 * TILE_OVERLAP_PX)
MAX_TILES_PER_PAGE = 96
SIGNAL_CELL_PX = 3
BACKGROUND_SAMPLE_STEP_PX = 6
BACKGROUND_PERCENTILE = 0.94
MAX_REGIONS_PER_TILE = 640
MAX_TOTAL_CANDIDATES = 6000
BOUNDARY_MERGE_GAP_PT = 2.5


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, payload: Any, length: int = 20) -> str:
    return f"{prefix}{sha256(_canonical(payload).encode('utf-8')).hexdigest()[:length]}"


def _page_rect_tuple(rect: pymupdf.Rect) -> tuple[float, float, float, float]:
    return tuple(round(float(value), 6) for value in (rect.x0, rect.y0, rect.x1, rect.y1))


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


def _plan_page(page_rect: pymupdf.Rect, page_index: int, digest: str) -> dict[str, Any]:
    width_pt = max(1.0, float(page_rect.width))
    height_pt = max(1.0, float(page_rect.height))
    scale = TARGET_SCALE_PX_PER_PT

    def grid(candidate_scale: float) -> tuple[int, int, float]:
        core_span_pt = TILE_CORE_PX / candidate_scale
        cols = max(1, math.ceil(width_pt / core_span_pt))
        rows = max(1, math.ceil(height_pt / core_span_pt))
        return cols, rows, core_span_pt

    cols, rows, core_span_pt = grid(scale)
    while cols * rows > MAX_TILES_PER_PAGE and scale > MIN_SCALE_PX_PER_PT:
        scale = max(MIN_SCALE_PX_PER_PT, scale * 0.90)
        cols, rows, core_span_pt = grid(scale)
        if scale == MIN_SCALE_PX_PER_PT:
            break

    overlap_pt = TILE_OVERLAP_PX / scale
    tiles: list[dict[str, Any]] = []
    for row in range(rows):
        for col in range(cols):
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
                "digest": digest,
                "page_index": page_index,
                "row": row,
                "col": col,
                "core": _page_rect_tuple(core),
                "clip": _page_rect_tuple(clip),
                "scale": round(scale, 8),
            }
            tiles.append({
                "tile_id": _stable_id("RR-", identity, 18),
                "row": row,
                "col": col,
                "core_bbox_pt": _page_rect_tuple(core),
                "clip_bbox_pt": _page_rect_tuple(clip),
            })

    identity = {
        "engine": RECOVERY_EXTRACTOR_VERSION,
        "digest": digest,
        "page_index": page_index,
        "page_bbox": _page_rect_tuple(page_rect),
        "scale": round(scale, 8),
        "tile_ids": [row["tile_id"] for row in tiles],
    }
    return {
        "schema": "CEW_RASTER_SIGNAL_RECOVERY_PLAN_v1",
        "plan_id": _stable_id("RRP-", identity, 20),
        "strategy": "TILED_FULL_COVERAGE_ADAPTIVE_RECOVERY",
        "effective_scale_px_per_pt": round(scale, 8),
        "tile_columns": cols,
        "tile_rows": rows,
        "tiles_planned": len(tiles),
        "tile_overlap_px": TILE_OVERLAP_PX,
        "tiles": tiles,
    }


def _histogram(samples: memoryview, width: int, height: int, stride: int) -> tuple[list[int], int, int]:
    hist = [0] * 256
    total = 0
    minimum = 255
    step = BACKGROUND_SAMPLE_STEP_PX
    for y in range(0, height, step):
        offset = y * stride
        for x in range(0, width, step):
            value = int(samples[offset + x])
            hist[value] += 1
            total += 1
            minimum = min(minimum, value)
    return hist, total, minimum


def _percentile(hist: list[int], total: int, fraction: float) -> int:
    if total <= 0:
        return 255
    target = max(1, math.ceil(total * fraction))
    cumulative = 0
    for value, count in enumerate(hist):
        cumulative += count
        if cumulative >= target:
            return value
    return 255


def _adaptive_threshold(background: int, minimum: int) -> tuple[int, int]:
    contrast = max(0, background - minimum)
    if contrast <= 2:
        delta = 2
    elif contrast <= 12:
        delta = 3
    elif contrast <= 40:
        delta = 4
    elif contrast <= 96:
        delta = 5
    else:
        delta = 7
    threshold = max(0, min(253, background - delta))
    return threshold, delta


def _signal_mask(
    samples: memoryview,
    width: int,
    height: int,
    stride: int,
    background: int,
    threshold: int,
) -> tuple[bytearray, int, int, int]:
    grid_w = max(1, math.ceil(width / SIGNAL_CELL_PX))
    grid_h = max(1, math.ceil(height / SIGNAL_CELL_PX))
    raw = bytearray(grid_w * grid_h)
    count = 0
    edge_floor = max(0, background - 2)
    for gy in range(grid_h):
        y0 = gy * SIGNAL_CELL_PX
        y1 = min(height, y0 + SIGNAL_CELL_PX)
        for gx in range(grid_w):
            x0 = gx * SIGNAL_CELL_PX
            x1 = min(width, x0 + SIGNAL_CELL_PX)
            cell_min = 255
            cell_max = 0
            below = 0
            for y in range(y0, y1):
                offset = y * stride
                for x in range(x0, x1):
                    value = int(samples[offset + x])
                    cell_min = min(cell_min, value)
                    cell_max = max(cell_max, value)
                    if value <= threshold:
                        below += 1
            local_range = cell_max - cell_min
            active = below > 0 or (cell_min <= edge_floor and local_range >= 3)
            if active:
                idx = gy * grid_w + gx
                raw[idx] = 1
                count += 1
    return raw, grid_w, grid_h, count


def _dilate(raw: bytearray, grid_w: int, grid_h: int) -> bytearray:
    out = bytearray(raw)
    for idx, active in enumerate(raw):
        if not active:
            continue
        y, x = divmod(idx, grid_w)
        for dy in (-1, 0, 1):
            ny = y + dy
            if ny < 0 or ny >= grid_h:
                continue
            row = ny * grid_w
            for dx in (-1, 0, 1):
                nx = x + dx
                if 0 <= nx < grid_w:
                    out[row + nx] = 1
    return out


def _components(raw: bytearray, detected: bytearray, grid_w: int, grid_h: int) -> list[dict[str, int]]:
    seen = bytearray(len(detected))
    result: list[dict[str, int]] = []
    for start, active in enumerate(detected):
        if not active or seen[start]:
            continue
        queue: deque[int] = deque([start])
        seen[start] = 1
        raw_cells = 0
        min_x = grid_w
        min_y = grid_h
        max_x = -1
        max_y = -1
        while queue:
            idx = queue.popleft()
            y, x = divmod(idx, grid_w)
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
                row = ny * grid_w
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx = x + dx
                    if nx < 0 or nx >= grid_w:
                        continue
                    nidx = row + nx
                    if detected[nidx] and not seen[nidx]:
                        seen[nidx] = 1
                        queue.append(nidx)
        if raw_cells <= 0:
            continue
        span_x = max_x - min_x + 1
        span_y = max_y - min_y + 1
        if raw_cells == 1 and max(span_x, span_y) < 3:
            continue
        result.append({
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
            "raw_cells": raw_cells,
            "span_x": span_x,
            "span_y": span_y,
        })
    result.sort(key=lambda row: (row["min_y"], row["min_x"], row["max_y"], row["max_x"]))
    return result


def _family(component: dict[str, int]) -> str:
    sx = max(1, component["span_x"])
    sy = max(1, component["span_y"])
    ratio = sx / sy
    density = component["raw_cells"] / max(1, sx * sy)
    if ratio >= 4.0 or ratio <= 0.25:
        return "LINEAR_STROKE_GROUP"
    if density >= 0.50:
        return "FILLED_OR_HATCHED_REGION"
    if component["raw_cells"] >= 20:
        return "COMPLEX_VECTOR_GROUP"
    return "UNKNOWN_GRAPHIC_GROUP"


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
    hist, total, minimum = _histogram(samples, width, height, stride)
    background = _percentile(hist, total, BACKGROUND_PERCENTILE)
    threshold, threshold_delta = _adaptive_threshold(background, minimum)
    raw, grid_w, grid_h, raw_count = _signal_mask(samples, width, height, stride, background, threshold)
    detected = _dilate(raw, grid_w, grid_h)
    components = _components(raw, detected, grid_w, grid_h)
    truncated = len(components) > MAX_REGIONS_PER_TILE
    if truncated:
        components = sorted(
            components,
            key=lambda row: (-row["raw_cells"], -max(row["span_x"], row["span_y"]), row["min_y"], row["min_x"]),
        )[:MAX_REGIONS_PER_TILE]
        components.sort(key=lambda row: (row["min_y"], row["min_x"]))

    regions: list[dict[str, Any]] = []
    for component in components:
        x0 = clip.x0 + (component["min_x"] * SIGNAL_CELL_PX) / scale
        y0 = clip.y0 + (component["min_y"] * SIGNAL_CELL_PX) / scale
        x1 = clip.x0 + ((component["max_x"] + 1) * SIGNAL_CELL_PX) / scale
        y1 = clip.y0 + ((component["max_y"] + 1) * SIGNAL_CELL_PX) / scale
        rect = pymupdf.Rect(x0, y0, x1, y1) & page_rect
        if rect.is_empty or rect.width <= 0 or rect.height <= 0:
            continue
        regions.append({
            "page_bbox_pt": _page_rect_tuple(rect),
            "primitive_family": _family(component),
            "supporting_tile_ids": [tile["tile_id"]],
            "tile_row": int(tile["row"]),
            "tile_col": int(tile["col"]),
            "raw_signal_cells": int(component["raw_cells"]),
            "background_estimate": int(background),
            "minimum_sample": int(minimum),
            "threshold_used": int(threshold),
            "threshold_delta": int(threshold_delta),
        })

    return regions, {
        "tile_id": tile["tile_id"],
        "row": tile["row"],
        "col": tile["col"],
        "status": "COMPLETE",
        "background_estimate": int(background),
        "minimum_sample": int(minimum),
        "threshold_used": int(threshold),
        "threshold_delta": int(threshold_delta),
        "raw_signal_cells": int(raw_count),
        "derived_region_count": len(regions),
        "region_budget_truncated": truncated,
    }


def _rect_relation(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return (
        min(ax1, bx1) - max(ax0, bx0),
        min(ay1, by1) - max(ay0, by0),
        max(0.0, max(ax0, bx0) - min(ax1, bx1)),
        max(0.0, max(ay0, by0) - min(ay1, by1)),
    )


def _mergeable(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a["primitive_family"] != b["primitive_family"]:
        return False
    if abs(a["tile_row"] - b["tile_row"]) > 1 or abs(a["tile_col"] - b["tile_col"]) > 1:
        return False
    if a["tile_row"] == b["tile_row"] and a["tile_col"] == b["tile_col"]:
        return False
    xo, yo, xg, yg = _rect_relation(a["page_bbox_pt"], b["page_bbox_pt"])
    return (xo > 0 and yo > 0) or (xg <= BOUNDARY_MERGE_GAP_PT and yo > 0) or (yg <= BOUNDARY_MERGE_GAP_PT and xo > 0)


def _reconcile(regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not regions:
        return []
    parent = list(range(len(regions)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if ra < rb:
            parent[rb] = ra
        else:
            parent[ra] = rb

    order = sorted(range(len(regions)), key=lambda i: (regions[i]["page_bbox_pt"][0], regions[i]["page_bbox_pt"][1]))
    for pos, left_idx in enumerate(order):
        left = regions[left_idx]
        limit = float(left["page_bbox_pt"][2]) + BOUNDARY_MERGE_GAP_PT
        for right_idx in order[pos + 1:]:
            right = regions[right_idx]
            if float(right["page_bbox_pt"][0]) > limit:
                break
            if _mergeable(left, right):
                union(left_idx, right_idx)

    grouped: dict[int, list[dict[str, Any]]] = {}
    for idx, region in enumerate(regions):
        grouped.setdefault(find(idx), []).append(region)

    merged: list[dict[str, Any]] = []
    for members in grouped.values():
        x0 = min(row["page_bbox_pt"][0] for row in members)
        y0 = min(row["page_bbox_pt"][1] for row in members)
        x1 = max(row["page_bbox_pt"][2] for row in members)
        y1 = max(row["page_bbox_pt"][3] for row in members)
        merged.append({
            "page_bbox_pt": (round(x0, 6), round(y0, 6), round(x1, 6), round(y1, 6)),
            "primitive_family": members[0]["primitive_family"],
            "supporting_tile_ids": sorted({tid for row in members for tid in row["supporting_tile_ids"]}),
            "raw_signal_cells": sum(int(row["raw_signal_cells"]) for row in members),
            "component_count": len(members),
            "background_estimate_min": min(int(row["background_estimate"]) for row in members),
            "background_estimate_max": max(int(row["background_estimate"]) for row in members),
            "minimum_sample_min": min(int(row["minimum_sample"]) for row in members),
            "threshold_used_min": min(int(row["threshold_used"]) for row in members),
            "threshold_used_max": max(int(row["threshold_used"]) for row in members),
        })
    merged.sort(key=lambda row: (row["page_bbox_pt"], row["primitive_family"]))
    return merged


def _candidate(*, source_version_id: str, digest: str, page_index: int, page_rect: pymupdf.Rect, plan_id: str, region: dict[str, Any]) -> dict[str, Any]:
    bbox = _bbox_dict(pymupdf.Rect(region["page_bbox_pt"]), page_rect)
    family = str(region["primitive_family"])
    signature = {
        "primitive_family": family,
        "aspect_bucket": base._aspect_bucket(bbox),
        "area_bucket": base._area_bucket(bbox),
        "complexity_bucket": base._complexity_bucket(int(region.get("component_count", 1))),
        "filled": family == "FILLED_OR_HATCHED_REGION",
        "stroke_width_bucket": "RASTER_RECOVERY",
    }
    identity = {
        "digest": digest,
        "page_index": page_index,
        "bbox": bbox,
        "plan_id": plan_id,
        "extractor": RECOVERY_EXTRACTOR_VERSION,
        "signature": signature,
    }
    stats = {
        "item_count": int(region.get("component_count", 1)),
        "filled": family == "FILLED_OR_HATCHED_REGION",
        "stroke_width_bucket": "RASTER_RECOVERY",
        "raw_signal_cells": int(region["raw_signal_cells"]),
        "background_estimate_min": int(region["background_estimate_min"]),
        "background_estimate_max": int(region["background_estimate_max"]),
        "minimum_sample_min": int(region["minimum_sample_min"]),
        "threshold_used_min": int(region["threshold_used_min"]),
        "threshold_used_max": int(region["threshold_used_max"]),
    }
    return {
        "candidate_id": _stable_id("GPC-", identity),
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "page_index": page_index,
        "coordinate_system": "NORMALIZED_0_1",
        "bbox": bbox,
        "page_bbox_pt": list(region["page_bbox_pt"]),
        "primitive_family": family,
        "detector": "PYMUPDF_RASTER_ADAPTIVE_SIGNAL_RECOVERY_V1",
        "extractor_version": RECOVERY_EXTRACTOR_VERSION,
        "raster_plan_id": plan_id,
        "supporting_tile_ids": list(region["supporting_tile_ids"]),
        "feature_signature": signature,
        "statistics": stats,
        "semantic_meaning": None,
        "semantic_authority": "NONE",
    }


def _extract_page(page: pymupdf.Page, *, source_version_id: str, digest: str, page_index: int, total_before: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    page_rect = page.rect
    plan = _plan_page(page_rect, page_index, digest)
    raw_regions: list[dict[str, Any]] = []
    tile_reports: list[dict[str, Any]] = []
    failed = 0
    for tile in plan["tiles"]:
        try:
            regions, tile_report = _capture_tile(page, page_rect, plan, tile)
        except Exception:
            failed += 1
            tile_reports.append({"tile_id": tile["tile_id"], "row": tile["row"], "col": tile["col"], "status": "FAILED"})
            continue
        raw_regions.extend(regions)
        tile_reports.append(tile_report)

    completed = len(plan["tiles"]) - failed
    coverage = completed / max(1, len(plan["tiles"]))
    reconciled = _reconcile(raw_regions)
    budget_left = max(0, MAX_TOTAL_CANDIDATES - total_before)
    truncated = len(reconciled) > budget_left
    reconciled = reconciled[:budget_left]
    candidates = [
        _candidate(
            source_version_id=source_version_id,
            digest=digest,
            page_index=page_index,
            page_rect=page_rect,
            plan_id=plan["plan_id"],
            region=region,
        )
        for region in reconciled
    ]
    raw_signal_cells = sum(int(row.get("raw_signal_cells", 0)) for row in tile_reports if row.get("status") == "COMPLETE")
    reasons: list[str] = []
    if coverage != 1.0 or failed:
        reasons.append("RASTER_RECOVERY_COVERAGE_INCOMPLETE")
    if truncated or any(bool(row.get("region_budget_truncated")) for row in tile_reports):
        reasons.append("RASTER_RECOVERY_REGION_BUDGET_TRUNCATED")
    if not candidates:
        reasons.append("RASTER_RECOVERY_NO_GRAPHIC_REGIONS")
    quality = "INCONCLUSIVE" if reasons else "READY"
    return candidates, {
        "page_index": page_index,
        "width_pt": round(float(page_rect.width), 6),
        "height_pt": round(float(page_rect.height), 6),
        "rotation": int(page.rotation),
        "modality": "RASTER_ADAPTIVE_SIGNAL_RECOVERY",
        "raster_plan": plan,
        "raster_plan_id": plan["plan_id"],
        "tiles_planned": len(plan["tiles"]),
        "tiles_completed": completed,
        "tiles_failed": failed,
        "coverage_ratio": round(coverage, 10),
        "required_coverage_ratio": 1.0,
        "raw_signal_cells": raw_signal_cells,
        "signal_state": "PRESENT" if raw_signal_cells else "ABSENT",
        "page_observation_state": "RASTER_SIGNAL_PRESENT" if raw_signal_cells else "RASTER_SIGNAL_ABSENT",
        "raw_region_count": len(raw_regions),
        "reconciled_region_count": len(reconciled),
        "primitive_candidate_count": len(candidates),
        "quality_status": quality,
        "quality_reasons": reasons,
        "tile_reports": tile_reports,
        "semantic_object_prior_used": False,
        "bounded_preview": True,
    }


def preacquire_preview_pdf(
    payload: bytes,
    *,
    source_version_id: str,
    expected_sha256: str | None = None,
    prior_report: dict[str, Any] | None = None,
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
            candidates, page_report = _extract_page(
                page,
                source_version_id=source_version_id,
                digest=digest,
                page_index=page_index,
                total_before=len(all_candidates),
            )
            all_candidates.extend(candidates)
            pages.append(page_report)
            if len(all_candidates) >= MAX_TOTAL_CANDIDATES:
                break

    clusters = base.cluster_primitives(all_candidates, digest)
    library_state, proposals, library_generation = base.match_clusters_to_library(clusters, None)
    triage = base.build_human_triage_queue(clusters, proposals)
    quality_reasons = sorted({reason for page in pages for reason in page.get("quality_reasons", [])})
    quality_status = "INCONCLUSIVE" if any(page.get("quality_status") == "INCONCLUSIVE" for page in pages) else "READY"
    minimum_coverage = min((float(page.get("coverage_ratio", 0.0)) for page in pages), default=0.0)
    report_identity = {
        "digest": digest,
        "extractor": RECOVERY_EXTRACTOR_VERSION,
        "plan_ids": [page["raster_plan_id"] for page in pages],
        "candidate_ids": [row["candidate_id"] for row in all_candidates],
        "cluster_ids": [row["cluster_id"] for row in clusters],
        "quality": quality_status,
    }
    prior_gate = (prior_report or {}).get("quality_gate") if isinstance(prior_report, dict) else None
    return {
        "schema": base.SCHEMA,
        "contract_schema": base.CONTRACT_SCHEMA,
        "raster_contract_schema": "CEW_RASTER_EVIDENCE_ENGINE_CONTRACT_v2",
        "recovery_schema": RECOVERY_SCHEMA,
        "mode": "NEW_PROJECT_ZERO_SEMANTIC_PRIOR",
        "analysis_scope": "BOUNDED_INTERACTIVE_PREVIEW",
        "analysis_completeness": "FULL_REQUIRED_COVERAGE" if quality_status == "READY" else "INCONCLUSIVE_REQUIRED_COVERAGE_OR_DETECTION",
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "extractor_version": RECOVERY_EXTRACTOR_VERSION,
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
            "blank_pages_observed": [],
            "signal_present": any(page.get("signal_state") == "PRESENT" for page in pages),
            "candidate_count": len(all_candidates),
        },
        "preview_budget": {
            "max_pages_analyzed": MAX_PREVIEW_PAGES_ANALYZED,
            "target_scale_px_per_pt": TARGET_SCALE_PX_PER_PT,
            "tile_render_max_px": TILE_RENDER_MAX_PX,
            "tile_overlap_px": TILE_OVERLAP_PX,
            "max_tiles_per_page": MAX_TILES_PER_PAGE,
            "max_regions_per_tile": MAX_REGIONS_PER_TILE,
            "max_total_candidates": MAX_TOTAL_CANDIDATES,
            "truncated": source_page_count > len(pages),
        },
        "preview_fallback_mode": "RASTER_TILED_ADAPTIVE_SIGNAL_RECOVERY_V1",
        "signal_recovery": {
            "used": True,
            "trigger": "BLANK_CORROBORATION_CONTRADICTED",
            "prior_extractor_version": (prior_report or {}).get("extractor_version") if isinstance(prior_report, dict) else None,
            "prior_quality_status": prior_gate.get("status") if isinstance(prior_gate, dict) else None,
            "prior_quality_reasons": prior_gate.get("reasons") if isinstance(prior_gate, dict) else [],
        },
        "known_object_types_required": False,
        "semantic_labels_assigned_automatically": False,
        "authority": dict(base.AUTHORITY),
        "next_gate": "HUMAN_DOCUMENT_AND_GRAPHIC_TRIAGE_REQUIRED",
    }
