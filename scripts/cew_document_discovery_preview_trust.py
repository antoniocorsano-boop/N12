#!/usr/bin/env python3
"""Independent trust hardening for CEW Document Discovery preview workers.

This module runs only inside the process-isolated preview worker, after the
worker memory ceiling has been applied. It adds two evidence products that the
web process must never compute from an unregistered user PDF:

1. bounded JPEG page inspection artifacts;
2. an independent blank-page corroboration witness.

The witness does not classify structural objects. It can only confirm that a
normal-aspect page is demonstrably blank, contradict a blank claim when
independent content evidence exists, or remain inconclusive. All outputs remain
preview-only and carry zero semantic / engineering authority.
"""
from __future__ import annotations

import base64
from hashlib import sha256
import math
from typing import Any

import pymupdf

PREVIEW_TRUST_VERSION = "CEW_DOCUMENT_DISCOVERY_PREVIEW_TRUST_v1"
PREVIEW_PAGE_MAX_PIXELS = 1_800_000
PREVIEW_PAGE_MAX_SCALE = 1.25
PREVIEW_PAGE_MIN_SCALE = 0.05
PREVIEW_PAGE_JPEG_QUALITY = 82
OVERVIEW_MAX_DIMENSION_PX = 768
OVERVIEW_MIN_SCALE = 0.03
BLANK_MAX_ASPECT_RATIO = 4.0
BLANK_MIN_ASPECT_RATIO = 0.25
OVERVIEW_BACKGROUND_PERCENTILE = 0.90
OVERVIEW_INK_DELTA = 4
OVERVIEW_MIN_DARK_PIXELS = 8
MAX_PREVIEW_PAGE_ARTIFACT_BYTES = 6 * 1024 * 1024


def _histogram(samples: memoryview, width: int, height: int, stride: int) -> tuple[list[int], int, int]:
    histogram = [0] * 256
    total = 0
    minimum = 255
    for y in range(height):
        offset = y * stride
        for x in range(width):
            value = int(samples[offset + x])
            histogram[value] += 1
            total += 1
            minimum = min(minimum, value)
    return histogram, total, minimum


def _percentile(histogram: list[int], total: int, fraction: float) -> int:
    if total <= 0:
        return 255
    target = max(1, math.ceil(total * fraction))
    cumulative = 0
    for value, count in enumerate(histogram):
        cumulative += count
        if cumulative >= target:
            return value
    return 255


def _render_inspection_artifact(page: pymupdf.Page, page_index: int) -> dict[str, Any]:
    area = max(1.0, float(page.rect.width) * float(page.rect.height))
    scale = min(PREVIEW_PAGE_MAX_SCALE, math.sqrt(PREVIEW_PAGE_MAX_PIXELS / area))
    scale = max(PREVIEW_PAGE_MIN_SCALE, scale)
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(scale, scale),
        colorspace=pymupdf.csRGB,
        alpha=False,
        annots=False,
    )
    payload = pix.tobytes("jpeg", jpg_quality=PREVIEW_PAGE_JPEG_QUALITY)
    if not payload.startswith(b"\xff\xd8") or len(payload) > MAX_PREVIEW_PAGE_ARTIFACT_BYTES:
        raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_PAGE_ARTIFACT_INVALID")
    return {
        "page_index": page_index,
        "media_type": "image/jpeg",
        "render_boundary": "PROCESS_ISOLATED_WORKER",
        "render_policy": "BOUNDED_INSPECTION_ARTIFACT",
        "scale_px_per_pt": round(scale, 8),
        "width_px": int(pix.width),
        "height_px": int(pix.height),
        "byte_count": len(payload),
        "sha256": sha256(payload).hexdigest(),
        "data_base64": base64.b64encode(payload).decode("ascii"),
    }


def _overview_witness(page: pymupdf.Page) -> dict[str, Any]:
    width_pt = max(1.0, float(page.rect.width))
    height_pt = max(1.0, float(page.rect.height))
    longest = max(width_pt, height_pt)
    scale = max(OVERVIEW_MIN_SCALE, min(1.0, OVERVIEW_MAX_DIMENSION_PX / longest))
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(scale, scale),
        colorspace=pymupdf.csGRAY,
        alpha=False,
        annots=False,
    )
    samples = pix.samples_mv if hasattr(pix, "samples_mv") else memoryview(pix.samples)
    histogram, total, minimum = _histogram(samples, int(pix.width), int(pix.height), int(pix.stride))
    background = _percentile(histogram, total, OVERVIEW_BACKGROUND_PERCENTILE)
    threshold = max(0, background - OVERVIEW_INK_DELTA)
    dark_pixels = sum(histogram[: threshold + 1]) if threshold >= 0 else 0
    contrast = max(0, background - minimum)
    raster_content_present = contrast >= OVERVIEW_INK_DELTA and dark_pixels >= OVERVIEW_MIN_DARK_PIXELS
    return {
        "scale_px_per_pt": round(scale, 8),
        "width_px": int(pix.width),
        "height_px": int(pix.height),
        "background_estimate": int(background),
        "minimum_sample": int(minimum),
        "contrast_span": int(contrast),
        "dark_pixel_count": int(dark_pixels),
        "raster_content_present": bool(raster_content_present),
    }


def _blank_corroboration(page: pymupdf.Page) -> dict[str, Any]:
    try:
        text_blocks = [
            block for block in page.get_text("blocks")
            if len(block) > 4 and str(block[4] or "").strip()
        ]
    except Exception:
        text_blocks = []
        text_witness_available = False
    else:
        text_witness_available = True

    try:
        image_count = len(page.get_images(full=True))
    except Exception:
        image_count = 0
        image_witness_available = False
    else:
        image_witness_available = True

    try:
        overview = _overview_witness(page)
    except Exception:
        overview = None

    width = max(1.0, float(page.rect.width))
    height = max(1.0, float(page.rect.height))
    aspect = width / height
    text_present = bool(text_blocks)
    image_present = image_count > 0
    raster_present = bool(overview and overview.get("raster_content_present"))
    content_present = text_present or image_present or raster_present

    if content_present:
        state = "CONTENT_PRESENT"
        blank_confirmed = False
    elif overview is None or not text_witness_available or not image_witness_available:
        state = "INCONCLUSIVE_WITNESS_UNAVAILABLE"
        blank_confirmed = False
    elif not (BLANK_MIN_ASPECT_RATIO <= aspect <= BLANK_MAX_ASPECT_RATIO):
        # Extreme technical sheets are never declared blank solely because a
        # globally reduced witness did not observe sparse linework.
        state = "INCONCLUSIVE_EXTREME_ASPECT_RATIO"
        blank_confirmed = False
    else:
        state = "CONFIRMED_BLANK"
        blank_confirmed = True

    return {
        "schema": "CEW_BLANK_CORROBORATION_v1",
        "version": PREVIEW_TRUST_VERSION,
        "state": state,
        "blank_confirmed": blank_confirmed,
        "page_aspect_ratio": round(aspect, 8),
        "text_witness_available": text_witness_available,
        "text_block_count": len(text_blocks),
        "image_witness_available": image_witness_available,
        "image_count": image_count,
        "overview": overview,
    }


def _append_reason(page: dict[str, Any], reason: str) -> None:
    reasons = [str(value) for value in (page.get("quality_reasons") or []) if str(value).strip()]
    if reason not in reasons:
        reasons.append(reason)
    page["quality_reasons"] = reasons
    page["quality_status"] = "INCONCLUSIVE"


def attach_trust_evidence(payload: bytes, report: dict[str, Any]) -> dict[str, Any]:
    """Attach process-isolated page artifacts and conservative blank evidence."""
    pages = report.get("pages") if isinstance(report.get("pages"), list) else []
    page_by_index = {
        int(row.get("page_index")): row
        for row in pages
        if isinstance(row, dict) and isinstance(row.get("page_index"), int)
    }
    artifacts: list[dict[str, Any]] = []

    with pymupdf.open(stream=payload, filetype="pdf") as doc:
        for page_index in sorted(page_by_index):
            if page_index < 0 or page_index >= doc.page_count:
                raise ValueError("DOCUMENT_DISCOVERY_PREVIEW_PAGE_INDEX_INVALID")
            page = doc.load_page(page_index)
            artifacts.append(_render_inspection_artifact(page, page_index))
            page_report = page_by_index[page_index]
            if int(page_report.get("primitive_candidate_count") or 0) != 0:
                continue
            witness = _blank_corroboration(page)
            page_report["blank_corroboration"] = witness
            if witness["state"] == "CONTENT_PRESENT":
                page_report["page_observation_state"] = "RASTER_SIGNAL_ABSENT_CONTENT_CORROBORATED"
                _append_reason(page_report, "BLANK_CORROBORATION_CONTRADICTED")
            elif witness["state"] == "CONFIRMED_BLANK":
                page_report["page_observation_state"] = "PAGE_BLANK_OBSERVED"
            else:
                page_report["page_observation_state"] = "BLANK_NOT_PROVEN"
                _append_reason(page_report, "BLANK_CORROBORATION_INSUFFICIENT")

    report["preview_trust_version"] = PREVIEW_TRUST_VERSION
    report["preview_page_image_mode"] = "PROCESS_ISOLATED_BOUNDED_JPEG"
    report["preview_page_images"] = artifacts
    report["preview_page_artifact_count"] = len(artifacts)

    gate = report.get("quality_gate")
    if isinstance(gate, dict):
        reasons = sorted({
            str(reason)
            for page in pages
            for reason in (page.get("quality_reasons") or [])
            if str(reason).strip()
        })
        any_inconclusive = any(str(page.get("quality_status") or "").upper() == "INCONCLUSIVE" for page in pages)
        gate["status"] = "INCONCLUSIVE" if any_inconclusive else str(gate.get("status") or "READY").upper()
        gate["reasons"] = reasons
        gate["blank_pages_observed"] = [
            int(page["page_index"])
            for page in pages
            if page.get("page_observation_state") == "PAGE_BLANK_OBSERVED"
            and (page.get("blank_corroboration") or {}).get("blank_confirmed") is True
        ]
        report["analysis_completeness"] = (
            "INCONCLUSIVE_REQUIRED_COVERAGE_OR_DETECTION"
            if gate["status"] == "INCONCLUSIVE"
            else report.get("analysis_completeness")
        )
    return report
