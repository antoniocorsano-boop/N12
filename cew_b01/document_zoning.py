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
    # Otsu keeps the proposer source-local and deterministic while avoiding
    # dependence on any structural detector or historical object oracle.
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def _propose_title_block_bbox(ink: np.ndarray) -> tuple[int, int, int, int] | None:
    height, width = ink.shape[:2]
    rows = 8
    cols = 8
    cell_h = max(1, height // rows)
    cell_w = max(1, width // cols)
    global_density = float((ink > 0).mean())
    threshold = max(0.08, global_density * 2.0)

    dense_cells: list[tuple[int, int]] = []
    for row in range(rows):
        y0 = row * cell_h
        y1 = height if row == rows - 1 else min(height, (row + 1) * cell_h)
        for col in range(cols):
            x0 = col * cell_w
            x1 = width if col == cols - 1 else min(width, (col + 1) * cell_w)
            region = ink[y0:y1, x0:x1]
            if not region.size:
                continue
            density = float((region > 0).mean())
            # Document title blocks on the pilot are expected toward the right
            # and/or lower part of the sheet, but this remains only a proposal.
            in_candidate_sector = col >= cols // 2 and row >= rows // 2
            if in_candidate_sector and density >= threshold:
                dense_cells.append((row, col))

    if not dense_cells:
        return None

    min_row = min(row for row, _ in dense_cells)
    max_row = max(row for row, _ in dense_cells)
    min_col = min(col for _, col in dense_cells)
    max_col = max(col for _, col in dense_cells)

    x0 = min_col * cell_w
    y0 = min_row * cell_h
    x1 = width if max_col == cols - 1 else min(width, (max_col + 1) * cell_w)
    y1 = height if max_row == rows - 1 else min(height, (max_row + 1) * cell_h)
    if x1 <= x0 or y1 <= y0:
        return None
    return (x0, y0, x1 - x0, y1 - y0)


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
                method="G0_DENSE_ORTHOGONAL_GRID_PROPOSAL_V1",
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
