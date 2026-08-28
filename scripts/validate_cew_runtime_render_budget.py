#!/usr/bin/env python3
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_runtime_render_budget as budget
import cew_source_evidence_workspace as source_workspace


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> int:
    if budget.MAX_RUNTIME_RENDER_PIXELS != 6_000_000:
        fail("unexpected runtime pixel budget")

    # Canonical TAV-05A dimensions from CEW_PAGE_REGISTRY_v1.csv.
    page_w = 1031.760010
    page_h = 8343.360352
    drawing_dpi, drawing_pixels = budget.bounded_dpi(page_w, page_h, 90)
    if drawing_dpi >= 90:
        fail("TAV-05A full-page renderer must be bounded below requested 90 dpi")
    if drawing_pixels > budget.MAX_RUNTIME_RENDER_PIXELS:
        fail("bounded full-page render exceeds pixel budget")

    ctx = source_workspace.task_context("ERW-N12-001")
    region = ctx["region"]
    # Reproduce the MICRO clip size algebra without rasterizing the PDF.
    w = float(region["width"])
    h = float(region["height"])
    pad_x = max(0.01, w * 0.03)
    pad_y = max(0.008, h * 0.10)
    clip_w = (min(1.0, float(region["x"]) + w + pad_x) - max(0.0, float(region["x"]) - pad_x)) * page_w
    clip_h = (min(1.0, float(region["y"]) + h + pad_y) - max(0.0, float(region["y"]) - pad_y)) * page_h
    micro_dpi, micro_pixels = budget.bounded_dpi(clip_w, clip_h, 220)
    if micro_dpi >= 220:
        fail("ERW-N12-001 MICRO renderer must be bounded below requested 220 dpi")
    if micro_pixels > budget.MAX_RUNTIME_RENDER_PIXELS:
        fail("bounded MICRO render exceeds pixel budget")
    if micro_dpi <= 42:
        fail("MICRO effective dpi must remain above MACRO 42 dpi")

    # Small render requests must not be degraded when they are already safe.
    safe_dpi, safe_pixels = budget.bounded_dpi(400.0, 300.0, 145)
    if safe_dpi != 145:
        fail("safe raster request was unnecessarily degraded")
    if safe_pixels > budget.MAX_RUNTIME_RENDER_PIXELS:
        fail("safe raster request exceeds budget")

    print("CEW_RUNTIME_RENDER_BUDGET = PASS")
    print(f"PIXEL_BUDGET = {budget.MAX_RUNTIME_RENDER_PIXELS}")
    print(f"TAV05A_DRAWING_REQUESTED_DPI = 90")
    print(f"TAV05A_DRAWING_EFFECTIVE_DPI = {drawing_dpi}")
    print(f"TAV05A_DRAWING_PIXELS = {drawing_pixels}")
    print("ERW_N12_001_MICRO_REQUESTED_DPI = 220")
    print(f"ERW_N12_001_MICRO_EFFECTIVE_DPI = {micro_dpi}")
    print(f"ERW_N12_001_MICRO_PIXELS = {micro_pixels}")
    print("SOURCE_GEOMETRY_MUTATED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
