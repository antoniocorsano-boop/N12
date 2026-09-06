#!/usr/bin/env python3
"""Independent PDFium raster recovery for CEW Document Discovery.

Second-stage, process-isolated recovery used only after the governed MuPDF
baseline completed but yielded no graphic regions. PDFium provides an
independent rendering implementation so recovery does not keep re-processing the
same MuPDF pixel stream. All outputs remain preview-only and non-semantic.
"""
from __future__ import annotations

import base64
from collections import deque
from hashlib import sha256
import json
import math
from typing import Any

import pypdfium2 as pdfium
import pymupdf  # JPEG encoder only; never used here to parse/render the PDF.

import cew_new_project_preacquisition as base

RECOVERY_EXTRACTOR_VERSION = "CEW_DOCUMENT_DISCOVERY_PDFIUM_SIGNAL_RECOVERY_v1"
RECOVERY_SCHEMA = "CEW_PDFIUM_SIGNAL_RECOVERY_v1"
MAX_PREVIEW_PAGES_ANALYZED = 6
MAX_RENDER_PIXELS = 6_000_000
TARGET_SCALE_PX_PER_PT = 1.6
MIN_SCALE_PX_PER_PT = 0.10
SIGNAL_CELL_PX = 3
BACKGROUND_SAMPLE_STEP_PX = 6
BACKGROUND_PERCENTILE = 0.94
MAX_COMPONENTS_PER_PAGE = 1200
MAX_TOTAL_CANDIDATES = 6000
MAX_PREVIEW_PAGE_ARTIFACT_BYTES = 6 * 1024 * 1024
JPEG_QUALITY = 86
MEDIA_BOX_AREA_RATIO_TRIGGER = 1.20


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, payload: Any, length: int = 20) -> str:
    return f"{prefix}{sha256(_canonical(payload).encode('utf-8')).hexdigest()[:length]}"


def _bbox_area(box: tuple[float, float, float, float] | None) -> float:
    if not box:
        return 0.0
    left, bottom, right, top = [float(value) for value in box]
    return max(0.0, right - left) * max(0.0, top - bottom)


def _page_dimensions(page: Any) -> tuple[float, float]:
    width, height = page.get_size()
    return max(1.0, float(width)), max(1.0, float(height))


def _render_scale(width_pt: float, height_pt: float) -> float:
    area = max(1.0, width_pt * height_pt)
    scale = min(TARGET_SCALE_PX_PER_PT, math.sqrt(MAX_RENDER_PIXELS / area))
    return max(MIN_SCALE_PX_PER_PT, scale)


def _pack_gray(bitmap: Any) -> tuple[bytes, int, int, int]:
    width = int(bitmap.width)
    height = int(bitmap.height)
    stride = int(bitmap.stride)
    raw = bytes(bitmap.buffer)
    if stride == width:
        return raw[: width * height], width, height, stride
    packed = bytearray(width * height)
    for y in range(height):
        src = y * stride
        dst = y * width
        packed[dst : dst + width] = raw[src : src + width]
    return bytes(packed), width, height, stride


def _render_gray(page: Any) -> tuple[bytes, int, int, float]:
    width_pt, height_pt = _page_dimensions(page)
    scale = _render_scale(width_pt, height_pt)
    bitmap = page.render(
        scale=scale,
        rotation=0,
        grayscale=True,
        draw_annots=False,
        may_draw_forms=False,
        fill_color=(255, 255, 255, 255),
        optimize_mode="print",
        limit_image_cache=True,
    )
    try:
        packed, width, height, _stride = _pack_gray(bitmap)
    finally:
        bitmap.close()
    return packed, width, height, scale


def _histogram(samples: bytes, width: int, height: int) -> tuple[list[int], int, int]:
    hist = [0] * 256
    total = 0
    minimum = 255
    step = BACKGROUND_SAMPLE_STEP_PX
    view = memoryview(samples)
    for y in range(0, height, step):
        row = y * width
        for x in range(0, width, step):
            value = int(view[row + x])
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
    if contrast <= 4:
        delta = 1
    elif contrast <= 12:
        delta = 2
    elif contrast <= 32:
        delta = 3
    elif contrast <= 64:
        delta = 4
    else:
        delta = 6
    return max(0, min(254, background - delta)), delta


def _signal_mask(samples: bytes, width: int, height: int, background: int, threshold: int) -> tuple[bytearray, int, int, int]:
    grid_w = max(1, math.ceil(width / SIGNAL_CELL_PX))
    grid_h = max(1, math.ceil(height / SIGNAL_CELL_PX))
    raw = bytearray(grid_w * grid_h)
    active_count = 0
    view = memoryview(samples)
    edge_floor = max(0, background - 1)
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
                row = y * width
                for x in range(x0, x1):
                    value = int(view[row + x])
                    cell_min = min(cell_min, value)
                    cell_max = max(cell_max, value)
                    if value <= threshold:
                        below += 1
            local_range = cell_max - cell_min
            active = below > 0 or (cell_min <= edge_floor and local_range >= 2)
            if active:
                idx = gy * grid_w + gx
                raw[idx] = 1
                active_count += 1
    return raw, grid_w, grid_h, active_count


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
    result.sort(key=lambda row: (-row["raw_cells"], row["min_y"], row["min_x"]))
    return result[:MAX_COMPONENTS_PER_PAGE]


def _family(component: dict[str, int]) -> str:
    span_x = max(1, component["span_x"])
    span_y = max(1, component["span_y"])
    ratio = span_x / span_y
    density = component["raw_cells"] / max(1, span_x * span_y)
    if ratio >= 4.0 or ratio <= 0.25:
        return "LINEAR_STROKE_GROUP"
    if density >= 0.50:
        return "FILLED_OR_HATCHED_REGION"
    if component["raw_cells"] >= 20:
        return "COMPLEX_VECTOR_GROUP"
    return "UNKNOWN_GRAPHIC_GROUP"


def _artifact(samples: bytes, width: int, height: int, *, page_index: int, scale: float, scope: str, background: int, minimum: int) -> dict[str, Any]:
    contrast = max(0, background - minimum)
    transformed = False
    display = samples
    if 1 <= contrast <= 80:
        low = max(0, minimum)
        high = max(low + 1, background)
        lut = bytes(max(0, min(255, round((value - low) * 255 / (high - low)))) for value in range(256))
        display = samples.translate(lut)
        transformed = True
    pix = pymupdf.Pixmap(pymupdf.csGRAY, width, height, display, False)
    payload = pix.tobytes("jpeg", jpg_quality=JPEG_QUALITY)
    if not payload.startswith(b"\xff\xd8") or len(payload) > MAX_PREVIEW_PAGE_ARTIFACT_BYTES:
        raise ValueError("DOCUMENT_DISCOVERY_PDFIUM_PAGE_ARTIFACT_INVALID")
    return {
        "page_index": page_index,
        "media_type": "image/jpeg",
        "render_boundary": "PROCESS_ISOLATED_WORKER",
        "render_engine": "PDFIUM",
        "render_policy": "INDEPENDENT_PDFIUM_BOUNDED_READING_AID",
        "render_scope": scope,
        "source_pixels_transformed": transformed,
        "display_enhancement": "LINEAR_CONTRAST_STRETCH" if transformed else "NONE",
        "pre_enhancement_background_estimate": int(background),
        "pre_enhancement_minimum_sample": int(minimum),
        "pre_enhancement_contrast_span": int(contrast),
        "scale_px_per_pt": round(scale, 8),
        "width_px": width,
        "height_px": height,
        "byte_count": len(payload),
        "sha256": sha256(payload).hexdigest(),
        "data_base64": base64.b64encode(payload).decode("ascii"),
    }


def _analyze_render(samples: bytes, width: int, height: int) -> tuple[list[dict[str, int]], dict[str, Any]]:
    hist, total, minimum = _histogram(samples, width, height)
    background = _percentile(hist, total, BACKGROUND_PERCENTILE)
    threshold, delta = _adaptive_threshold(background, minimum)
    raw, grid_w, grid_h, raw_count = _signal_mask(samples, width, height, background, threshold)
    components = _components(raw, _dilate(raw, grid_w, grid_h), grid_w, grid_h)
    return components, {
        "background_estimate": int(background),
        "minimum_sample": int(minimum),
        "contrast_span": int(max(0, background - minimum)),
        "threshold_used": int(threshold),
        "threshold_delta": int(delta),
        "raw_signal_cells": int(raw_count),
        "grid_width": grid_w,
        "grid_height": grid_h,
        "component_count": len(components),
    }


def _component_bbox(component: dict[str, int], width: int, height: int) -> dict[str, float]:
    x0 = component["min_x"] * SIGNAL_CELL_PX
    y0 = component["min_y"] * SIGNAL_CELL_PX
    x1 = min(width, (component["max_x"] + 1) * SIGNAL_CELL_PX)
    y1 = min(height, (component["max_y"] + 1) * SIGNAL_CELL_PX)
    return {
        "x": round(x0 / max(1, width), 10),
        "y": round(y0 / max(1, height), 10),
        "w": round(max(1, x1 - x0) / max(1, width), 10),
        "h": round(max(1, y1 - y0) / max(1, height), 10),
    }


def _candidate(*, source_version_id: str, digest: str, page_index: int, component: dict[str, int], width: int, height: int, scale: float, render_scope: str) -> dict[str, Any]:
    bbox = _component_bbox(component, width, height)
    family = _family(component)
    signature = {
        "primitive_family": family,
        "aspect_bucket": base._aspect_bucket(bbox),
        "area_bucket": base._area_bucket(bbox),
        "complexity_bucket": base._complexity_bucket(1),
        "filled": family == "FILLED_OR_HATCHED_REGION",
        "stroke_width_bucket": "PDFIUM_RASTER_RECOVERY",
    }
    identity = {
        "digest": digest,
        "page_index": page_index,
        "bbox": bbox,
        "extractor": RECOVERY_EXTRACTOR_VERSION,
        "scope": render_scope,
        "signature": signature,
    }
    x0 = component["min_x"] * SIGNAL_CELL_PX / scale
    y0 = component["min_y"] * SIGNAL_CELL_PX / scale
    x1 = min(width, (component["max_x"] + 1) * SIGNAL_CELL_PX) / scale
    y1 = min(height, (component["max_y"] + 1) * SIGNAL_CELL_PX) / scale
    return {
        "candidate_id": _stable_id("GPC-", identity),
        "source_version_id": source_version_id,
        "source_sha256": digest,
        "page_index": page_index,
        "coordinate_system": "NORMALIZED_0_1",
        "bbox": bbox,
        "page_bbox_pt": [round(x0, 6), round(y0, 6), round(x1, 6), round(y1, 6)],
        "primitive_family": family,
        "detector": "PDFIUM_RASTER_ADAPTIVE_SIGNAL_RECOVERY_V1",
        "extractor_version": RECOVERY_EXTRACTOR_VERSION,
        "render_engine": "PDFIUM",
        "render_scope": render_scope,
        "feature_signature": signature,
        "statistics": {"raw_signal_cells": int(component["raw_cells"])},
        "semantic_meaning": None,
        "semantic_authority": "NONE",
    }


def _materially_larger_media(page: Any) -> tuple[bool, tuple[float, float, float, float] | None, tuple[float, float, float, float] | None]:
    try:
        media = page.get_mediabox()
        visible = page.get_bbox()
    except Exception:
        return False, None, None
    media_area = _bbox_area(media)
    visible_area = _bbox_area(visible)
    return bool(media_area > 0 and visible_area > 0 and media_area / visible_area >= MEDIA_BOX_AREA_RATIO_TRIGGER), media, visible


def _extract_page(page: Any, *, source_version_id: str, digest: str, page_index: int, total_before: int) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    original_rotation = int(page.get_rotation())
    media_larger, media_box, visible_box = _materially_larger_media(page)

    samples, width, height, scale = _render_gray(page)
    components, metrics = _analyze_render(samples, width, height)
    render_scope = "VISIBLE_PAGE_BBOX"
    media_probe_used = False

    if not components and media_larger and media_box is not None:
        original_crop = None
        try:
            original_crop = page.get_cropbox()
            page.set_cropbox(*media_box)
            media_samples, media_width, media_height, media_scale = _render_gray(page)
            media_components, media_metrics = _analyze_render(media_samples, media_width, media_height)
            media_probe_used = True
            if media_components:
                samples, width, height, scale = media_samples, media_width, media_height, media_scale
                components, metrics = media_components, media_metrics
                render_scope = "MEDIA_BOX_RECOVERY"
        finally:
            try:
                if original_crop is not None:
                    page.set_cropbox(*original_crop)
            except Exception:
                pass

    budget_left = max(0, MAX_TOTAL_CANDIDATES - total_before)
    truncated = len(components) > budget_left
    components = components[:budget_left]
    candidates = [
        _candidate(
            source_version_id=source_version_id,
            digest=digest,
            page_index=page_index,
            component=component,
            width=width,
            height=height,
            scale=scale,
            render_scope=render_scope,
        )
        for component in components
    ]
    reasons: list[str] = []
    if truncated:
        reasons.append("PDFIUM_RECOVERY_REGION_BUDGET_TRUNCATED")
    if not candidates:
        reasons.append("PDFIUM_RECOVERY_NO_GRAPHIC_REGIONS")
    if render_scope == "MEDIA_BOX_RECOVERY":
        reasons.append("VISIBLE_CROPBOX_EXCLUDES_RECOVERED_SIGNAL")
    quality = "INCONCLUSIVE" if reasons and not candidates else "READY"
    if render_scope == "MEDIA_BOX_RECOVERY":
        quality = "INCONCLUSIVE"

    artifact = _artifact(
        samples,
        width,
        height,
        page_index=page_index,
        scale=scale,
        scope=render_scope,
        background=int(metrics["background_estimate"]),
        minimum=int(metrics["minimum_sample"]),
    )
    page_report = {
        "page_index": page_index,
        "width_pt": round(width / scale, 6),
        "height_pt": round(height / scale, 6),
        "rotation": original_rotation,
        "modality": "PDFIUM_INDEPENDENT_RASTER_RECOVERY",
        "render_engine": "PDFIUM",
        "render_scope": render_scope,
        "pdfium_page_bbox": list(visible_box) if visible_box else None,
        "pdfium_media_box": list(media_box) if media_box else None,
        "media_box_probe_used": media_probe_used,
        "effective_scale_px_per_pt": round(scale, 8),
        "raster_width_px": width,
        "raster_height_px": height,
        "coverage_ratio": 1.0,
        "required_coverage_ratio": 1.0,
        "raw_signal_cells": int(metrics["raw_signal_cells"]),
        "signal_state": "PRESENT" if metrics["raw_signal_cells"] else "ABSENT",
        "page_observation_state": "RASTER_SIGNAL_PRESENT" if metrics["raw_signal_cells"] else "RASTER_SIGNAL_ABSENT",
        "raw_region_count": int(metrics["component_count"]),
        "reconciled_region_count": len(candidates),
        "primitive_candidate_count": len(candidates),
        "quality_status": quality,
        "quality_reasons": reasons,
        "detector_metrics": metrics,
        "semantic_object_prior_used": False,
        "bounded_preview": True,
    }
    return candidates, page_report, artifact


def preacquire_preview_pdf(payload: bytes, *, source_version_id: str, expected_sha256: str | None = None, prior_report: dict[str, Any] | None = None) -> dict[str, Any]:
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
    artifacts: list[dict[str, Any]] = []
    pdf = pdfium.PdfDocument(payload)
    try:
        source_page_count = len(pdf)
        analyzed_count = min(source_page_count, MAX_PREVIEW_PAGES_ANALYZED)
        for page_index in range(analyzed_count):
            page = pdf[page_index]
            try:
                candidates, page_report, artifact = _extract_page(
                    page,
                    source_version_id=source_version_id,
                    digest=digest,
                    page_index=page_index,
                    total_before=len(all_candidates),
                )
            finally:
                page.close()
            all_candidates.extend(candidates)
            pages.append(page_report)
            artifacts.append(artifact)
            if len(all_candidates) >= MAX_TOTAL_CANDIDATES:
                break
    finally:
        pdf.close()

    clusters = base.cluster_primitives(all_candidates, digest)
    library_state, proposals, library_generation = base.match_clusters_to_library(clusters, None)
    triage = base.build_human_triage_queue(clusters, proposals)
    quality_reasons = sorted({reason for page in pages for reason in page.get("quality_reasons", [])})
    quality_status = "INCONCLUSIVE" if any(page.get("quality_status") == "INCONCLUSIVE" for page in pages) else "READY"
    minimum_coverage = min((float(page.get("coverage_ratio", 0.0)) for page in pages), default=0.0)
    prior_gate = (prior_report or {}).get("quality_gate") if isinstance(prior_report, dict) else None
    report_identity = {
        "digest": digest,
        "extractor": RECOVERY_EXTRACTOR_VERSION,
        "candidate_ids": [row["candidate_id"] for row in all_candidates],
        "cluster_ids": [row["cluster_id"] for row in clusters],
        "quality": quality_status,
        "artifacts": [row["sha256"] for row in artifacts],
    }
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
            "max_render_pixels_per_page": MAX_RENDER_PIXELS,
            "target_scale_px_per_pt": TARGET_SCALE_PX_PER_PT,
            "max_components_per_page": MAX_COMPONENTS_PER_PAGE,
            "max_total_candidates": MAX_TOTAL_CANDIDATES,
            "truncated": source_page_count > len(pages),
        },
        "preview_fallback_mode": "PDFIUM_INDEPENDENT_RASTER_SIGNAL_RECOVERY_V1",
        "preview_page_image_mode": "PROCESS_ISOLATED_PDFIUM_JPEG",
        "preview_page_reading_aid_policy": "INDEPENDENT_PDFIUM_DECLARED_TRANSFORM",
        "preview_page_images": artifacts,
        "preview_page_artifact_count": len(artifacts),
        "signal_recovery": {
            "used": True,
            "trigger": "BLANK_CORROBORATION_CONTRADICTED",
            "renderer": "PDFIUM",
            "independent_from_baseline_renderer": True,
            "prior_extractor_version": (prior_report or {}).get("extractor_version") if isinstance(prior_report, dict) else None,
            "prior_quality_status": prior_gate.get("status") if isinstance(prior_gate, dict) else None,
            "prior_quality_reasons": prior_gate.get("reasons") if isinstance(prior_gate, dict) else [],
        },
        "known_object_types_required": False,
        "semantic_labels_assigned_automatically": False,
        "authority": dict(base.AUTHORITY),
        "next_gate": "HUMAN_DOCUMENT_AND_GRAPHIC_TRIAGE_REQUIRED",
    }
