from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Iterable, Sequence

import cv2
import numpy as np

from .document_zoning import validate_zone_partition
from .evidence_schema import Task3RasterBinding
from .grammar_schema import (
    DocumentRegionKind,
    DocumentRegionMask,
    GraphicPrimitiveObservation,
    PrimitiveFamily,
    RecurringMotif,
)


_EXCLUSION_KINDS = {
    DocumentRegionKind.TITLE_BLOCK,
    DocumentRegionKind.LOCATION_DIAGRAM,
    DocumentRegionKind.APPROVAL_STAMP_SIGNATURE,
    DocumentRegionKind.NOTE_OR_LEGEND_REGION,
    DocumentRegionKind.MARGIN_VOID,
    DocumentRegionKind.SCAN_ARTIFACT,
}


def _read_image(binding: Task3RasterBinding, raster_path: Path) -> np.ndarray:
    image = cv2.imread(str(raster_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("GRAMMAR_REVIEW_RASTER_READ_FAILED")
    height, width = image.shape[:2]
    if width != binding.raster_width_px or height != binding.raster_height_px:
        raise ValueError("GRAMMAR_REVIEW_RASTER_BINDING_DIMENSION_MISMATCH")
    return image


def _confirmed_workarea_mask(
    binding: Task3RasterBinding,
    zones: Sequence[DocumentRegionMask],
) -> np.ndarray:
    if not zones or any(not zone.human_confirmed for zone in zones):
        raise ValueError("GRAMMAR_REVIEW_REQUIRES_CONFIRMED_G0_ZONES")
    validate_zone_partition(binding, zones)
    mask = np.zeros((binding.raster_height_px, binding.raster_width_px), dtype=np.uint8)
    workareas = [zone for zone in zones if zone.kind == DocumentRegionKind.STRUCTURAL_WORKAREA]
    if not workareas:
        raise ValueError("GRAMMAR_REVIEW_STRUCTURAL_WORKAREA_REQUIRED")
    for zone in workareas:
        x0 = int(round(zone.x))
        y0 = int(round(zone.y))
        x1 = int(round(zone.x + zone.width))
        y1 = int(round(zone.y + zone.height))
        mask[y0:y1, x0:x1] = 255
    for zone in zones:
        if zone.kind not in _EXCLUSION_KINDS:
            continue
        x0 = int(round(zone.x))
        y0 = int(round(zone.y))
        x1 = int(round(zone.x + zone.width))
        y1 = int(round(zone.y + zone.height))
        mask[y0:y1, x0:x1] = 0
    return mask


def _primitive_box(item: GraphicPrimitiveObservation) -> tuple[int, int, int, int]:
    x0 = int(np.floor(item.x))
    y0 = int(np.floor(item.y))
    x1 = int(np.ceil(item.x + item.width))
    y1 = int(np.ceil(item.y + item.height))
    return x0, y0, x1, y1


def _validate_primitives(
    binding: Task3RasterBinding,
    workarea_mask: np.ndarray,
    primitives: Sequence[GraphicPrimitiveObservation],
) -> dict[str, GraphicPrimitiveObservation]:
    by_id: dict[str, GraphicPrimitiveObservation] = {}
    height, width = workarea_mask.shape[:2]
    for item in primitives:
        if not isinstance(item, GraphicPrimitiveObservation):
            raise ValueError("GRAMMAR_REVIEW_REQUIRES_TYPED_PRIMITIVES")
        if item.source != binding.source or item.page_index != binding.source.page_index:
            raise ValueError("GRAMMAR_REVIEW_PRIMITIVE_SOURCE_MISMATCH")
        x0, y0, x1, y1 = _primitive_box(item)
        x0 = max(0, min(width, x0))
        x1 = max(0, min(width, x1))
        y0 = max(0, min(height, y0))
        y1 = max(0, min(height, y1))
        if x1 <= x0 or y1 <= y0:
            raise ValueError("GRAMMAR_REVIEW_PRIMITIVE_GEOMETRY_INVALID")
        if not bool(np.all(workarea_mask[y0:y1, x0:x1] > 0)):
            raise ValueError("GRAMMAR_REVIEW_PRIMITIVE_OUTSIDE_WORKAREA")
        if item.semantic_meaning is not None or item.structural_identity_authorized or item.canonical_write_authorized:
            raise ValueError("GRAMMAR_REVIEW_PRIMITIVE_AUTHORITY_VIOLATION")
        by_id[item.primitive_id] = item
    return by_id


def _validate_motifs(
    binding: Task3RasterBinding,
    primitive_by_id: dict[str, GraphicPrimitiveObservation],
    motifs: Sequence[RecurringMotif],
) -> None:
    for motif in motifs:
        if not isinstance(motif, RecurringMotif):
            raise ValueError("GRAMMAR_REVIEW_REQUIRES_TYPED_MOTIFS")
        if motif.source != binding.source or motif.page_index != binding.source.page_index:
            raise ValueError("GRAMMAR_REVIEW_MOTIF_SOURCE_MISMATCH")
        if motif.representative_primitive_id not in primitive_by_id:
            raise ValueError("GRAMMAR_REVIEW_MOTIF_REPRESENTATIVE_MISSING")
        if any(member_id not in primitive_by_id for member_id in motif.member_primitive_ids):
            raise ValueError("GRAMMAR_REVIEW_MOTIF_MEMBER_MISSING")
        if motif.semantic_meaning is not None or motif.structural_identity_authorized or motif.canonical_write_authorized:
            raise ValueError("GRAMMAR_REVIEW_MOTIF_AUTHORITY_VIOLATION")


def _fit_inside(image: np.ndarray, width: int, height: int) -> np.ndarray:
    source_height, source_width = image.shape[:2]
    if source_width <= 0 or source_height <= 0:
        raise ValueError("GRAMMAR_REVIEW_INVALID_IMAGE_DIMENSIONS")
    scale = min(width / source_width, height / source_height)
    target_width = max(1, int(round(source_width * scale)))
    target_height = max(1, int(round(source_height * scale)))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    return cv2.resize(image, (target_width, target_height), interpolation=interpolation)


def _render_zone_overview(
    image: np.ndarray,
    zones: Sequence[DocumentRegionMask],
    destination: Path,
) -> None:
    canvas = image.copy()
    for zone in zones:
        x0 = int(round(zone.x))
        y0 = int(round(zone.y))
        x1 = int(round(zone.x + zone.width))
        y1 = int(round(zone.y + zone.height))
        if zone.kind == DocumentRegionKind.STRUCTURAL_WORKAREA:
            colour = (0, 180, 0)
        elif zone.kind in _EXCLUSION_KINDS:
            colour = (0, 0, 220)
        else:
            colour = (220, 120, 0)
        cv2.rectangle(canvas, (x0, y0), (x1, y1), colour, max(1, round(max(canvas.shape[:2]) / 1600)))
        cv2.putText(
            canvas,
            zone.kind.value,
            (max(0, x0 + 4), max(18, y0 + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            max(0.35, min(0.9, max(canvas.shape[:2]) / 5000)),
            colour,
            1,
            cv2.LINE_AA,
        )
    preview = _fit_inside(canvas, 1800, 2200)
    if not cv2.imwrite(str(destination), preview):
        raise ValueError("GRAMMAR_REVIEW_ZONE_OVERVIEW_WRITE_FAILED")


def _coverage_masks(
    image: np.ndarray,
    workarea_mask: np.ndarray,
    primitives: Sequence[GraphicPrimitiveObservation],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    ink[workarea_mask == 0] = 0
    accounted = np.zeros_like(ink)
    for item in primitives:
        x0, y0, x1, y1 = _primitive_box(item)
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(ink.shape[1], x1)
        y1 = min(ink.shape[0], y1)
        accounted[y0:y1, x0:x1] = 255
    accounted_ink = cv2.bitwise_and(ink, accounted)
    unaccounted = cv2.bitwise_and(ink, cv2.bitwise_not(accounted))
    return ink, accounted_ink, unaccounted


def _render_coverage_overlay(
    image: np.ndarray,
    workarea_mask: np.ndarray,
    unaccounted: np.ndarray,
    destination: Path,
) -> None:
    canvas = image.copy()
    canvas[workarea_mask == 0] = (245, 245, 245)
    canvas[unaccounted > 0] = (0, 0, 255)
    preview = _fit_inside(canvas, 1800, 2200)
    if not cv2.imwrite(str(destination), preview):
        raise ValueError("GRAMMAR_REVIEW_COVERAGE_WRITE_FAILED")


def _context_crop(image: np.ndarray, item: GraphicPrimitiveObservation) -> np.ndarray:
    x0, y0, x1, y1 = _primitive_box(item)
    margin = max(20, int(round(max(item.width, item.height) * 2.5)))
    left = max(0, x0 - margin)
    top = max(0, y0 - margin)
    right = min(image.shape[1], x1 + margin)
    bottom = min(image.shape[0], y1 + margin)
    crop = image[top:bottom, left:right].copy()
    cv2.rectangle(
        crop,
        (x0 - left, y0 - top),
        (x1 - left, y1 - top),
        (0, 0, 255),
        max(1, round(max(crop.shape[:2]) / 250)),
    )
    return crop


def _render_motif_atlas(
    image: np.ndarray,
    primitive_by_id: dict[str, GraphicPrimitiveObservation],
    motifs: Sequence[RecurringMotif],
    destination: Path,
) -> list[str]:
    if not motifs:
        return []
    destination.mkdir(parents=True, exist_ok=True)
    columns = 3
    rows = 4
    tile_width = 520
    tile_height = 380
    per_sheet = columns * rows
    paths: list[str] = []
    ordered = sorted(
        motifs,
        key=lambda motif: (
            -motif.occurrence_count,
            str(motif.neutral_descriptor.get("family", "")),
            motif.motif_id,
        ),
    )
    for start in range(0, len(ordered), per_sheet):
        items = ordered[start : start + per_sheet]
        sheet = np.full((rows * tile_height, columns * tile_width, 3), 255, dtype=np.uint8)
        for offset, motif in enumerate(items):
            representative = primitive_by_id[motif.representative_primitive_id]
            crop = _context_crop(image, representative)
            header_height = 58
            fitted = _fit_inside(crop, tile_width - 16, tile_height - header_height - 16)
            row = offset // columns
            col = offset % columns
            x0 = col * tile_width
            y0 = row * tile_height
            paste_x = x0 + (tile_width - fitted.shape[1]) // 2
            paste_y = y0 + header_height + (tile_height - header_height - fitted.shape[0]) // 2
            sheet[paste_y : paste_y + fitted.shape[0], paste_x : paste_x + fitted.shape[1]] = fitted
            family = str(motif.neutral_descriptor.get("family", "UNKNOWN"))
            label = f"{family}  n={motif.occurrence_count}"
            cv2.putText(sheet, label, (x0 + 8, y0 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(sheet, motif.motif_id, (x0 + 8, y0 + 46), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (0, 0, 0), 1, cv2.LINE_AA)
        path = destination / f"motif-atlas-{start // per_sheet + 1:02d}.png"
        if not cv2.imwrite(str(path), sheet):
            raise ValueError("GRAMMAR_REVIEW_MOTIF_ATLAS_WRITE_FAILED")
        paths.append(str(path))
    return paths


def render_grammar_foundation_review_package(
    binding: Task3RasterBinding,
    raster_path: Path | str,
    zones: Sequence[DocumentRegionMask],
    primitives: Iterable[GraphicPrimitiveObservation],
    motifs: Iterable[RecurringMotif],
    output_dir: Path | str,
) -> dict[str, object]:
    if not isinstance(binding, Task3RasterBinding):
        raise ValueError("GRAMMAR_REVIEW_REQUIRES_TASK3_RASTER_BINDING")
    image = _read_image(binding, Path(raster_path))
    workarea_mask = _confirmed_workarea_mask(binding, zones)
    primitive_items = tuple(primitives)
    motif_items = tuple(motifs)
    primitive_by_id = _validate_primitives(binding, workarea_mask, primitive_items)
    _validate_motifs(binding, primitive_by_id, motif_items)

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    zone_overview_path = destination / "zone-overview.png"
    coverage_overlay_path = destination / "coverage-overlay.png"
    _render_zone_overview(image, zones, zone_overview_path)

    ink, accounted_ink, unaccounted = _coverage_masks(image, workarea_mask, primitive_items)
    _render_coverage_overlay(image, workarea_mask, unaccounted, coverage_overlay_path)
    motif_atlas_paths = _render_motif_atlas(image, primitive_by_id, motif_items, destination / "atlas")

    total_ink = int(np.count_nonzero(ink))
    accounted_ink_pixels = int(np.count_nonzero(accounted_ink))
    unaccounted_ink_pixels = int(np.count_nonzero(unaccounted))
    coverage_ratio = (accounted_ink_pixels / total_ink) if total_ink else 1.0
    family_counts = Counter(item.family.value for item in primitive_items)
    unknown_motifs = [
        motif
        for motif in motif_items
        if motif.neutral_descriptor.get("family") == PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP.value
    ]

    manifest = {
        "schema_id": "CEW_B01_GRAMMAR_FOUNDATION_REVIEW_PACKAGE",
        "schema_version": 1,
        "review_state": "PENDING_HUMAN_MOTIF_REVIEW",
        "g0_g2_engineering_pass": True,
        "source": binding.source.to_mapping(),
        "raster": {
            "width_px": binding.raster_width_px,
            "height_px": binding.raster_height_px,
            "raster_sha256": binding.raster_sha256,
            "png_sha256": binding.png_sha256,
            "renderer_tool_id": binding.renderer_tool_id,
            "renderer_tool_version": binding.renderer_tool_version,
        },
        "zones": {
            "count": len(zones),
            "items": [zone.to_mapping() for zone in zones],
        },
        "primitives": {
            "count": len(primitive_items),
            "family_counts": dict(sorted(family_counts.items())),
            "items": [item.to_mapping() for item in sorted(primitive_items, key=lambda primitive: primitive.primitive_id)],
        },
        "motifs": {
            "count": len(motif_items),
            "unknown_motif_count": len(unknown_motifs),
            "items": [motif.to_mapping() for motif in sorted(motif_items, key=lambda motif: motif.motif_id)],
        },
        "coverage": {
            "workarea_ink_pixels": total_ink,
            "accounted_ink_pixels": accounted_ink_pixels,
            "unaccounted_ink_pixels": unaccounted_ink_pixels,
            "accounted_ink_ratio": round(coverage_ratio, 6),
            "unaccounted_is_review_item": True,
        },
        "authority": {
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }
    manifest_path = destination / "grammar-foundation-review.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "manifest_path": str(manifest_path),
        "zone_overview_path": str(zone_overview_path),
        "coverage_overlay_path": str(coverage_overlay_path),
        "motif_atlas_paths": motif_atlas_paths,
    }
