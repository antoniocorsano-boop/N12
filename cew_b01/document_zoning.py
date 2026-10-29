from __future__ import annotations

from pathlib import Path
from typing import Sequence

import cv2
import numpy as np

from .evidence_schema import Task3RasterBinding
from .grammar_schema import DocumentRegionKind, DocumentRegionMask
from .records import CoordinateFrame


_EXCLUSION_KINDS = {
    DocumentRegionKind.TITLE_BLOCK,
    DocumentRegionKind.LOCATION_DIAGRAM,
    DocumentRegionKind.APPROVAL_STAMP_SIGNATURE,
    DocumentRegionKind.NOTE_OR_LEGEND_REGION,
    DocumentRegionKind.MARGIN_VOID,
    DocumentRegionKind.SCAN_ARTIFACT,
}


def _read_grayscale(binding: Task3RasterBinding, raster_path: Path) -> np.ndarray:
    image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("G0_RASTER_READ_FAILED")
    height, width = image.shape[:2]
    if width != binding.raster_width_px or height != binding.raster_height_px:
        raise ValueError("G0_RASTER_BINDING_DIMENSION_MISMATCH")
    return image


def _ink_mask(image: np.ndarray) -> np.ndarray:
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def _first_sustained_support(
    projection: np.ndarray,
    *,
    support_floor: int,
    gap_tolerance: int,
) -> tuple[int, int] | None:
    if projection.size == 0:
        return None
    support = (projection >= max(1, support_floor)).astype(np.uint8).reshape(-1, 1)
    if not np.any(support):
        return None
    kernel_size = max(1, int(gap_tolerance) * 2 + 1)
    if kernel_size > 1:
        kernel = np.ones((kernel_size, 1), dtype=np.uint8)
        support = cv2.morphologyEx(support, cv2.MORPH_CLOSE, kernel).reshape(-1)
    else:
        support = support.reshape(-1)
    indices = np.flatnonzero(support)
    if indices.size == 0:
        return None
    return int(indices.min()), int(indices.max())


def _refine_outward_title_block_bbox(
    ink: np.ndarray,
    coarse_bbox: tuple[int, int, int, int],
    *,
    cell_h: int,
    cell_w: int,
) -> tuple[int, int, int, int]:
    """Refine only page-facing title-block edges below the coarse-grid scale."""

    height, width = ink.shape[:2]
    x, y, w, h = coarse_bbox
    x2 = x + w
    y2 = y + h

    left_facing = x <= width - x2
    top_facing = y <= height - y2

    global_density = float((ink > 0).mean())
    # This pass intentionally has much higher recall than the coarse locator.
    # Its search is bounded to one coarse cell around a page-facing edge, so it
    # can retain sparse header text without granting permission to expand inward
    # into the structural workarea.
    low_density = max(0.00075, min(0.008, global_density * 0.10))

    if top_facing:
        sy0 = max(0, y - cell_h)
        sy1 = min(height, y + cell_h)
        strip = ink[sy0:sy1, x:x2] > 0
        if strip.size:
            support_floor = max(1, int(np.ceil(strip.shape[1] * low_density)))
            support = _first_sustained_support(
                strip.sum(axis=1),
                support_floor=support_floor,
                gap_tolerance=max(1, cell_h // 16),
            )
            if support is not None:
                first, _last = support
                refined_y = sy0 + first
                if refined_y < y2:
                    y = refined_y
                    h = y2 - y
    else:
        sy0 = max(0, y2 - cell_h)
        sy1 = min(height, y2 + cell_h)
        strip = ink[sy0:sy1, x:x2] > 0
        if strip.size:
            support_floor = max(1, int(np.ceil(strip.shape[1] * low_density)))
            support = _first_sustained_support(
                strip.sum(axis=1),
                support_floor=support_floor,
                gap_tolerance=max(1, cell_h // 16),
            )
            if support is not None:
                _first, last = support
                refined_y2 = sy0 + last + 1
                if refined_y2 > y:
                    h = refined_y2 - y
                    y2 = refined_y2

    y2 = y + h
    if left_facing:
        sx0 = max(0, x - cell_w)
        sx1 = min(width, x + cell_w)
        strip = ink[y:y2, sx0:sx1] > 0
        if strip.size:
            support_floor = max(1, int(np.ceil(strip.shape[0] * low_density)))
            support = _first_sustained_support(
                strip.sum(axis=0),
                support_floor=support_floor,
                gap_tolerance=max(1, cell_w // 16),
            )
            if support is not None:
                first, _last = support
                refined_x = sx0 + first
                if refined_x < x2:
                    x = refined_x
                    w = x2 - x
    else:
        sx0 = max(0, x2 - cell_w)
        sx1 = min(width, x2 + cell_w)
        strip = ink[y:y2, sx0:sx1] > 0
        if strip.size:
            support_floor = max(1, int(np.ceil(strip.shape[0] * low_density)))
            support = _first_sustained_support(
                strip.sum(axis=0),
                support_floor=support_floor,
                gap_tolerance=max(1, cell_w // 16),
            )
            if support is not None:
                _first, last = support
                refined_x2 = sx0 + last + 1
                if refined_x2 > x:
                    w = refined_x2 - x

    x = max(0, min(int(x), width - 1))
    y = max(0, min(int(y), height - 1))
    w = max(1, min(int(w), width - x))
    h = max(1, min(int(h), height - y))
    return x, y, w, h


def _propose_title_block_bbox(ink: np.ndarray) -> tuple[int, int, int, int] | None:
    """Propose one dense corner-region without assuming which corner it occupies."""

    height, width = ink.shape[:2]
    rows = 16
    cols = 16
    cell_h = max(1, height // rows)
    cell_w = max(1, width // cols)
    global_density = float((ink > 0).mean())
    threshold = max(0.08, global_density * 2.0)

    density_grid = np.zeros((rows, cols), dtype=np.float64)
    for row in range(rows):
        y0 = row * cell_h
        y1 = height if row == rows - 1 else min(height, (row + 1) * cell_h)
        for col in range(cols):
            x0 = col * cell_w
            x1 = width if col == cols - 1 else min(width, (col + 1) * cell_w)
            region = ink[y0:y1, x0:x1]
            if region.size:
                density_grid[row, col] = float((region > 0).mean())

    dense = (density_grid >= threshold).astype(np.uint8)
    half_row = rows // 2
    half_col = cols // 2
    corners = (
        (0, half_row, 0, half_col, 0, 0),
        (0, half_row, half_col, cols, 0, cols - 1),
        (half_row, rows, 0, half_col, rows - 1, 0),
        (half_row, rows, half_col, cols, rows - 1, cols - 1),
    )

    candidates: list[tuple[float, int, int, int, int]] = []
    for row0, row1, col0, col1, corner_row, corner_col in corners:
        sector = dense[row0:row1, col0:col1]
        if not np.any(sector):
            continue
        component_count, labels = cv2.connectedComponents(sector, connectivity=8)
        for label in range(1, component_count):
            local_rows, local_cols = np.where(labels == label)
            if len(local_rows) < 2:
                continue
            grid_rows = local_rows + row0
            grid_cols = local_cols + col0
            densities = density_grid[grid_rows, grid_cols]
            corner_distance = min(
                abs(int(row) - corner_row) + abs(int(col) - corner_col)
                for row, col in zip(grid_rows, grid_cols)
            )
            if corner_distance > 2:
                continue
            score = float(len(grid_rows)) * float(densities.mean()) / (1.0 + 0.25 * corner_distance)
            candidates.append(
                (
                    score,
                    int(grid_rows.min()),
                    int(grid_rows.max()),
                    int(grid_cols.min()),
                    int(grid_cols.max()),
                )
            )

    if not candidates:
        return None

    _, min_row, max_row, min_col, max_col = max(
        candidates,
        key=lambda item: (item[0], -item[1], -item[3], item[2] - item[1], item[4] - item[3]),
    )
    x0 = min_col * cell_w
    y0 = min_row * cell_h
    x1 = width if max_col == cols - 1 else min(width, (max_col + 1) * cell_w)
    y1 = height if max_row == rows - 1 else min(height, (max_row + 1) * cell_h)
    if x1 <= x0 or y1 <= y0:
        return None
    return _refine_outward_title_block_bbox(
        ink,
        (x0, y0, x1 - x0, y1 - y0),
        cell_h=cell_h,
        cell_w=cell_w,
    )


def _workareas_around_exclusion(
    *,
    width: int,
    height: int,
    exclusion: tuple[int, int, int, int] | None,
) -> list[tuple[int, int, int, int]]:
    if exclusion is None:
        return [(0, 0, width, height)]

    x, y, w, h = exclusion
    x2 = x + w
    y2 = y + h
    regions: list[tuple[int, int, int, int]] = []

    if x > 0:
        regions.append((0, 0, x, height))
    if x2 < width:
        regions.append((x2, 0, width - x2, height))
    if y > 0:
        regions.append((x, 0, w, y))
    if y2 < height:
        regions.append((x, y2, w, height - y2))

    return [region for region in regions if region[2] > 0 and region[3] > 0]


def propose_document_zones(
    binding: Task3RasterBinding,
    raster_path: Path,
) -> tuple[DocumentRegionMask, ...]:
    if not isinstance(binding, Task3RasterBinding):
        raise ValueError("G0_REQUIRES_TASK3_RASTER_BINDING")
    image = _read_grayscale(binding, Path(raster_path))
    ink = _ink_mask(image)
    height, width = image.shape[:2]
    title_bbox = _propose_title_block_bbox(ink)

    zones: list[DocumentRegionMask] = []
    if title_bbox is not None:
        tx, ty, tw, th = title_bbox
        zones.append(
            DocumentRegionMask.create(
                source=binding.source,
                frame=CoordinateFrame.RASTER_PIXEL,
                raster_width=width,
                raster_height=height,
                x=tx,
                y=ty,
                width=tw,
                height=th,
                kind=DocumentRegionKind.TITLE_BLOCK,
                method="G0_DENSE_CORNER_GRID_SUBCELL_PROPOSAL_V4",
                human_confirmed=False,
            )
        )

    for x, y, w, h in _workareas_around_exclusion(
        width=width,
        height=height,
        exclusion=title_bbox,
    ):
        zones.append(
            DocumentRegionMask.create(
                source=binding.source,
                frame=CoordinateFrame.RASTER_PIXEL,
                raster_width=width,
                raster_height=height,
                x=x,
                y=y,
                width=w,
                height=h,
                kind=DocumentRegionKind.STRUCTURAL_WORKAREA,
                method="G0_COMPLEMENTARY_WORKAREA_PROPOSAL_V1",
                human_confirmed=False,
            )
        )

    return tuple(
        sorted(
            zones,
            key=lambda item: (
                item.kind.value,
                item.y,
                item.x,
                item.width,
                item.height,
                item.region_id,
            ),
        )
    )


def _rectangles_overlap(a: DocumentRegionMask, b: DocumentRegionMask) -> bool:
    return not (
        a.x + a.width <= b.x
        or b.x + b.width <= a.x
        or a.y + a.height <= b.y
        or b.y + b.height <= a.y
    )


def validate_zone_partition(
    binding: Task3RasterBinding,
    zones: Sequence[DocumentRegionMask],
) -> None:
    if not isinstance(binding, Task3RasterBinding):
        raise ValueError("G0_REQUIRES_TASK3_RASTER_BINDING")
    if not zones:
        raise ValueError("G0_ZONE_PARTITION_EMPTY")

    workareas: list[DocumentRegionMask] = []
    exclusions: list[DocumentRegionMask] = []
    for zone in zones:
        if not isinstance(zone, DocumentRegionMask):
            raise ValueError("G0_ZONE_PARTITION_REQUIRES_TYPED_REGIONS")
        if zone.source != binding.source or zone.page_index != binding.source.page_index:
            raise ValueError("G0_ZONE_SOURCE_MISMATCH")
        if zone.frame != CoordinateFrame.RASTER_PIXEL:
            raise ValueError("G0_ZONE_FRAME_MISMATCH")
        if zone.raster_width != binding.raster_width_px or zone.raster_height != binding.raster_height_px:
            raise ValueError("G0_ZONE_RASTER_DIMENSION_MISMATCH")
        if zone.kind == DocumentRegionKind.STRUCTURAL_WORKAREA:
            workareas.append(zone)
        elif zone.kind in _EXCLUSION_KINDS:
            exclusions.append(zone)

    if not workareas:
        raise ValueError("G0_STRUCTURAL_WORKAREA_REQUIRED")

    for workarea in workareas:
        for exclusion in exclusions:
            if _rectangles_overlap(workarea, exclusion):
                raise ValueError("ZONE_PARTITION_REVIEW_REQUIRED")


def apply_structural_workarea_mask(
    image: np.ndarray,
    zones: Sequence[DocumentRegionMask],
) -> np.ndarray:
    if not isinstance(image, np.ndarray) or image.ndim not in (2, 3):
        raise ValueError("G0_MASK_REQUIRES_RASTER_ARRAY")
    if not zones:
        raise ValueError("G0_ZONE_PARTITION_EMPTY")

    height, width = image.shape[:2]
    workareas = [zone for zone in zones if zone.kind == DocumentRegionKind.STRUCTURAL_WORKAREA]
    if not workareas:
        raise ValueError("G0_STRUCTURAL_WORKAREA_REQUIRED")
    if any(not zone.human_confirmed for zone in workareas):
        raise ValueError("UNCONFIRMED_STRUCTURAL_WORKAREA")

    exclusions = [zone for zone in zones if zone.kind in _EXCLUSION_KINDS]
    if any(not zone.human_confirmed for zone in exclusions):
        raise ValueError("UNCONFIRMED_EXCLUSION_MASK")

    for zone in zones:
        if zone.raster_width != width or zone.raster_height != height:
            raise ValueError("G0_MASK_IMAGE_DIMENSION_MISMATCH")

    output = np.zeros_like(image)
    for zone in workareas:
        x0 = int(round(zone.x))
        y0 = int(round(zone.y))
        x1 = int(round(zone.x + zone.width))
        y1 = int(round(zone.y + zone.height))
        output[y0:y1, x0:x1] = image[y0:y1, x0:x1]

    for zone in exclusions:
        x0 = int(round(zone.x))
        y0 = int(round(zone.y))
        x1 = int(round(zone.x + zone.width))
        y1 = int(round(zone.y + zone.height))
        output[y0:y1, x0:x1] = 0

    return output
