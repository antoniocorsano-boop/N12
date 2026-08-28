#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os

import cew_drawing_viewer as drawing_viewer
import cew_source_evidence_workspace as source_workspace

# Raster budget used while generating deterministic reading aids. This does
# not alter SourceVersion, Page, PageTransform, EvidenceRegion, or any
# engineering/canonical authority.
MAX_RUNTIME_RENDER_PIXELS = 6_000_000
MIN_RUNTIME_DPI = 36


def bounded_dpi(width_pt: float, height_pt: float, requested_dpi: int) -> tuple[int, int]:
    if width_pt <= 0 or height_pt <= 0:
        raise ValueError("INVALID_RENDER_GEOMETRY")
    if requested_dpi <= 0:
        raise ValueError("INVALID_RENDER_DPI")

    max_dpi = int(math.floor(72.0 * math.sqrt(MAX_RUNTIME_RENDER_PIXELS / (width_pt * height_pt))))
    effective_dpi = min(requested_dpi, max(MIN_RUNTIME_DPI, max_dpi))
    width_px = max(1, int(math.ceil(width_pt * effective_dpi / 72.0)))
    height_px = max(1, int(math.ceil(height_pt * effective_dpi / 72.0)))
    pixels = width_px * height_px

    while pixels > MAX_RUNTIME_RENDER_PIXELS and effective_dpi > MIN_RUNTIME_DPI:
        effective_dpi -= 1
        width_px = max(1, int(math.ceil(width_pt * effective_dpi / 72.0)))
        height_px = max(1, int(math.ceil(height_pt * effective_dpi / 72.0)))
        pixels = width_px * height_px

    if pixels > MAX_RUNTIME_RENDER_PIXELS:
        raise ValueError("RENDER_GEOMETRY_EXCEEDS_RUNTIME_PIXEL_BUDGET")
    return effective_dpi, pixels


def _emit_budget_receipt(kind: str, source_id: str, requested_dpi: int, effective_dpi: int, pixels: int) -> None:
    print(
        "CEW_RUNTIME_RENDER_BUDGET "
        + json.dumps(
            {
                "kind": kind,
                "source_id": source_id,
                "requested_dpi": requested_dpi,
                "effective_dpi": effective_dpi,
                "pixel_count": pixels,
                "pixel_budget": MAX_RUNTIME_RENDER_PIXELS,
                "authority": "READING_AID_ONLY",
                "canonical_write_authorized": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )


def render_task_source_bounded(task_id: str, scale: str) -> tuple[bytes, dict]:
    import pymupdf

    ctx = source_workspace.task_context(task_id)
    source_id = ctx["task"]["source_id"]
    payload, source = source_workspace.fetch_verified_source(source_id)
    page_index = int(ctx["page"]["page_index"])

    with pymupdf.open(stream=payload, filetype="pdf") as doc:
        if page_index < 0 or page_index >= doc.page_count:
            raise ValueError("PAGE_INDEX_OUT_OF_RANGE")
        page = doc.load_page(page_index)
        clip, requested_dpi = source_workspace._clip_for_scale(ctx["region"], page.rect, scale)
        effective_dpi, pixels = bounded_dpi(clip.width, clip.height, requested_dpi)
        _emit_budget_receipt("EVIDENCE_SOURCE", source_id, requested_dpi, effective_dpi, pixels)
        pix = page.get_pixmap(dpi=effective_dpi, clip=clip, alpha=False)
        print(f"CEW_RUNTIME_RENDER_STAGE PIXMAP_READY task={task_id} scale={scale.upper()}", flush=True)
        png = pix.tobytes("png")
        print(f"CEW_RUNTIME_RENDER_STAGE PNG_READY task={task_id} scale={scale.upper()} bytes={len(png)}", flush=True)

    return png, {
        **ctx,
        "verified_sha256": source["sha256"],
        "scale": scale.upper(),
        "requested_dpi": requested_dpi,
        "effective_dpi": effective_dpi,
        "render_pixels": pixels,
        "render_pixel_budget": MAX_RUNTIME_RENDER_PIXELS,
    }


def render_full_page_bounded(source_id: str, dpi: int = drawing_viewer.DEFAULT_DPI) -> tuple[bytes, dict]:
    import pymupdf

    if dpi not in drawing_viewer.ALLOWED_DPI:
        raise ValueError("UNSUPPORTED_DRAWING_DPI")

    ctx = drawing_viewer.drawing_context(source_id)
    if not ctx["viewer_ready"]:
        raise ValueError(ctx["viewer_reason"])

    page_record = ctx["page"]
    payload, source = source_workspace.fetch_verified_source(source_id)
    page_index = int(page_record["page_index"])

    with pymupdf.open(stream=payload, filetype="pdf") as doc:
        if page_index < 0 or page_index >= doc.page_count:
            raise ValueError("PAGE_INDEX_OUT_OF_RANGE")
        page = doc.load_page(page_index)
        expected_w = float(page_record["source_width"])
        expected_h = float(page_record["source_height"])
        if (
            abs(page.rect.width - expected_w) > drawing_viewer.DIMENSION_TOLERANCE_PT
            or abs(page.rect.height - expected_h) > drawing_viewer.DIMENSION_TOLERANCE_PT
        ):
            raise ValueError("PAGE_DIMENSION_MISMATCH")

        effective_dpi, pixels = bounded_dpi(page.rect.width, page.rect.height, dpi)
        _emit_budget_receipt("DRAWING_FULL_PAGE", source_id, dpi, effective_dpi, pixels)
        pix = page.get_pixmap(dpi=effective_dpi, alpha=False)
        print(f"CEW_RUNTIME_RENDER_STAGE PIXMAP_READY source={source_id} dpi={effective_dpi}", flush=True)
        png = pix.tobytes("png")
        print(f"CEW_RUNTIME_RENDER_STAGE PNG_READY source={source_id} bytes={len(png)}", flush=True)

    return png, {
        **ctx,
        "dpi": effective_dpi,
        "requested_dpi": dpi,
        "effective_dpi": effective_dpi,
        "render_pixels": pixels,
        "render_pixel_budget": MAX_RUNTIME_RENDER_PIXELS,
        "verified_sha256": source["sha256"],
        "derived_authority": "READING_AID_ONLY",
        "canonical_write_authorized": False,
    }


def install() -> None:
    # Managed web runtimes must never perform CPU-heavy PDF rasterization on
    # request. Render/Vercel serve immutable reading aids generated during the
    # build and verified against the exact runtime revision.
    if os.getenv("RENDER") or os.getenv("VERCEL"):
        import cew_runtime_render_cache as runtime_cache

        runtime_cache.install()
        return

    source_workspace.render_task_source = render_task_source_bounded
    drawing_viewer.render_full_page = render_full_page_bounded
