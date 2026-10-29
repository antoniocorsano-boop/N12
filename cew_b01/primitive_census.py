from __future__ import annotations

from math import atan2, degrees, hypot
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np

from .document_zoning import validate_zone_partition
from .evidence_schema import Task3RasterBinding
from .grammar_schema import (
    DocumentRegionKind,
    DocumentRegionMask,
    GraphicPrimitiveObservation,
    PrimitiveFamily,
)
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
        raise ValueError("G1_RASTER_READ_FAILED")
    height, width = image.shape[:2]
    if width != binding.raster_width_px or height != binding.raster_height_px:
        raise ValueError("G1_RASTER_BINDING_DIMENSION_MISMATCH")
    return image


def _confirmed_analysis_mask(
    binding: Task3RasterBinding,
    zones: Sequence[DocumentRegionMask],
) -> np.ndarray:
    if not zones or any(not zone.human_confirmed for zone in zones):
        raise ValueError("G1_REQUIRES_CONFIRMED_G0_ZONES")
    validate_zone_partition(binding, zones)
    mask = np.zeros((binding.raster_height_px, binding.raster_width_px), dtype=np.uint8)
    workareas = [zone for zone in zones if zone.kind == DocumentRegionKind.STRUCTURAL_WORKAREA]
    if not workareas:
        raise ValueError("G1_REQUIRES_CONFIRMED_G0_ZONES")
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


def _analysis_binary(image: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    analysis = np.full_like(image, 255)
    analysis[mask > 0] = image[mask > 0]
    _, binary = cv2.threshold(analysis, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    binary[mask == 0] = 0
    return analysis, binary


def _bbox_from_points(points: Sequence[tuple[float, float]], *, pad: int = 1) -> tuple[float, float, float, float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x0 = max(0.0, min(xs) - pad)
    y0 = max(0.0, min(ys) - pad)
    x1 = max(xs) + pad
    y1 = max(ys) + pad
    return x0, y0, max(1.0, x1 - x0), max(1.0, y1 - y0)


def _segment_signature(segment: tuple[int, int, int, int]) -> dict[str, float | str]:
    x1, y1, x2, y2 = segment
    dx = x2 - x1
    dy = y2 - y1
    angle = degrees(atan2(dy, dx))
    if abs(dx) >= 2 * abs(dy):
        orientation = "HORIZONTAL"
    elif abs(dy) >= 2 * abs(dx):
        orientation = "VERTICAL"
    else:
        orientation = "DIAGONAL"
    return {
        "length_px": round(hypot(dx, dy), 3),
        "angle_deg": round(angle, 3),
        "orientation": orientation,
    }


def _normalise_segment(raw: np.ndarray) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = (int(value) for value in raw.reshape(4))
    if (x2, y2) < (x1, y1):
        x1, y1, x2, y2 = x2, y2, x1, y1
    return x1, y1, x2, y2


def _line_segments(binary: np.ndarray) -> list[tuple[int, int, int, int]]:
    height, width = binary.shape[:2]
    min_length = max(12, int(round(min(height, width) * 0.055)))
    max_gap = max(3, int(round(min(height, width) * 0.012)))
    lines = cv2.HoughLinesP(
        binary,
        rho=1,
        theta=np.pi / 180.0,
        threshold=max(12, min_length // 2),
        minLineLength=min_length,
        maxLineGap=max_gap,
    )
    if lines is None:
        return []
    unique = {_normalise_segment(line) for line in lines}
    return sorted(unique, key=lambda item: (item[1], item[0], item[3], item[2]))


def _axis_orientation(segment: tuple[int, int, int, int]) -> str:
    return str(_segment_signature(segment)["orientation"])


def _segment_centerline(segment: tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = segment
    orientation = _axis_orientation(segment)
    if orientation == "HORIZONTAL":
        return (y1 + y2) / 2.0
    if orientation == "VERTICAL":
        return (x1 + x2) / 2.0
    return 0.0


def _range_for_segment(segment: tuple[int, int, int, int]) -> tuple[float, float]:
    x1, y1, x2, y2 = segment
    orientation = _axis_orientation(segment)
    values = (x1, x2) if orientation == "HORIZONTAL" else (y1, y2)
    return float(min(values)), float(max(values))


def _overlap(a: tuple[float, float], b: tuple[float, float]) -> float:
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def _point_near_endpoint(point: tuple[float, float], segment: tuple[int, int, int, int], tolerance: float) -> bool:
    px, py = point
    x1, y1, x2, y2 = segment
    return min(hypot(px - x1, py - y1), hypot(px - x2, py - y2)) <= tolerance


def _make_observation(
    binding: Task3RasterBinding,
    *,
    family: PrimitiveFamily,
    detector: str,
    bbox: tuple[float, float, float, float],
    signature: dict[str, object],
) -> GraphicPrimitiveObservation:
    x, y, width, height = bbox
    return GraphicPrimitiveObservation.create(
        source=binding.source,
        frame=CoordinateFrame.RASTER_PIXEL,
        raster_width=binding.raster_width_px,
        raster_height=binding.raster_height_px,
        x=x,
        y=y,
        width=width,
        height=height,
        family=family,
        detector=detector,
        feature_signature=signature,
    )


def extract_neutral_primitives(
    binding: Task3RasterBinding,
    raster_path: Path | str,
    zones: Sequence[DocumentRegionMask],
) -> tuple[GraphicPrimitiveObservation, ...]:
    if not isinstance(binding, Task3RasterBinding):
        raise ValueError("G1_REQUIRES_TASK3_RASTER_BINDING")
    mask = _confirmed_analysis_mask(binding, zones)
    image = _read_grayscale(binding, Path(raster_path))
    _analysis, binary = _analysis_binary(image, mask)
    height, width = binary.shape[:2]

    observations: list[GraphicPrimitiveObservation] = []
    seen: set[tuple[object, ...]] = set()

    def add(family: PrimitiveFamily, detector: str, bbox: tuple[float, float, float, float], signature: dict[str, object]) -> None:
        x, y, w, h = bbox
        x = max(0.0, min(float(x), width - 1.0))
        y = max(0.0, min(float(y), height - 1.0))
        w = min(float(w), width - x)
        h = min(float(h), height - y)
        if w <= 0 or h <= 0:
            return
        # Fail closed at the confirmed G0 boundary: every pixel covered by the
        # emitted observation envelope must belong to STRUCTURAL_WORKAREA.
        x0 = max(0, min(width, int(np.floor(x))))
        y0 = max(0, min(height, int(np.floor(y))))
        x1 = max(0, min(width, int(np.ceil(x + w))))
        y1 = max(0, min(height, int(np.ceil(y + h))))
        if x1 <= x0 or y1 <= y0:
            return
        if not bool(np.all(mask[y0:y1, x0:x1] > 0)):
            return
        key = (family.value, round(x, 2), round(y, 2), round(w, 2), round(h, 2), detector)
        if key in seen:
            return
        seen.add(key)
        observations.append(_make_observation(binding, family=family, detector=detector, bbox=(x, y, w, h), signature=signature))

    segments = _line_segments(binary)
    for segment in segments:
        signature = _segment_signature(segment)
        x1, y1, x2, y2 = segment
        bbox = _bbox_from_points(((x1, y1), (x2, y2)), pad=1)
        family = PrimitiveFamily.LINE_SEGMENT
        add(family, "G1_HOUGH_LINE_V1", bbox, signature)
        if signature["orientation"] == "DIAGONAL" and float(signature["length_px"]) < max(width, height) * 0.25:
            add(PrimitiveFamily.LEADER_OR_CALLOUT_CANDIDATE, "G1_DIAGONAL_STROKE_V1", bbox, signature)
        elif float(signature["length_px"]) < min(width, height) * 0.13:
            add(PrimitiveFamily.DIMENSION_LINE_OR_TICK_CANDIDATE, "G1_SHORT_STROKE_V1", bbox, signature)

    axis_segments = [segment for segment in segments if _axis_orientation(segment) in {"HORIZONTAL", "VERTICAL"}]
    pair_cap = min(len(axis_segments), 220)
    axis_segments = axis_segments[:pair_cap]
    for index, first in enumerate(axis_segments):
        first_orientation = _axis_orientation(first)
        for second in axis_segments[index + 1 :]:
            second_orientation = _axis_orientation(second)
            if first_orientation == second_orientation:
                separation = abs(_segment_centerline(first) - _segment_centerline(second))
                overlap = _overlap(_range_for_segment(first), _range_for_segment(second))
                shorter = min(
                    float(_segment_signature(first)["length_px"]),
                    float(_segment_signature(second)["length_px"]),
                )
                if 3.0 <= separation <= max(24.0, min(width, height) * 0.08) and overlap >= max(8.0, shorter * 0.45):
                    bbox = _bbox_from_points(((first[0], first[1]), (first[2], first[3]), (second[0], second[1]), (second[2], second[3])), pad=2)
                    add(
                        PrimitiveFamily.PARALLEL_LINE_PAIR,
                        "G1_PARALLEL_PAIR_V1",
                        bbox,
                        {"orientation": first_orientation, "separation_px": round(separation, 3), "overlap_px": round(overlap, 3)},
                    )
                continue

            horizontal = first if first_orientation == "HORIZONTAL" else second
            vertical = first if first_orientation == "VERTICAL" else second
            hx1, hy1, hx2, hy2 = horizontal
            vx1, vy1, vx2, vy2 = vertical
            px = (vx1 + vx2) / 2.0
            py = (hy1 + hy2) / 2.0
            tolerance = 4.0
            if min(hx1, hx2) - tolerance <= px <= max(hx1, hx2) + tolerance and min(vy1, vy2) - tolerance <= py <= max(vy1, vy2) + tolerance:
                near_h = _point_near_endpoint((px, py), horizontal, tolerance * 1.5)
                near_v = _point_near_endpoint((px, py), vertical, tolerance * 1.5)
                family = PrimitiveFamily.T_JUNCTION if near_h ^ near_v else PrimitiveFamily.INTERSECTION
                add(
                    family,
                    "G1_AXIS_RELATION_V1",
                    (max(0.0, px - 4.0), max(0.0, py - 4.0), 8.0, 8.0),
                    {"near_horizontal_endpoint": near_h, "near_vertical_endpoint": near_v},
                )
                if not near_h and not near_v:
                    add(
                        PrimitiveFamily.CROSS_MOTIF,
                        "G1_AXIS_RELATION_V1",
                        (max(0.0, px - 7.0), max(0.0, py - 7.0), 14.0, 14.0),
                        {"relation": "CROSSING_AXIS_STROKES"},
                    )
                elif near_h ^ near_v:
                    add(
                        PrimitiveFamily.T_SHAPED_MOTIF,
                        "G1_AXIS_RELATION_V1",
                        (max(0.0, px - 7.0), max(0.0, py - 7.0), 14.0, 14.0),
                        {"relation": "T_AXIS_STROKES"},
                    )

    contours, _hierarchy = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < 16.0:
            continue
        perimeter = float(cv2.arcLength(contour, True))
        if perimeter <= 0:
            continue
        approx = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
        x, y, w, h = cv2.boundingRect(contour)
        if w < 5 or h < 5:
            continue
        bbox_area = float(w * h)
        rectangularity = area / bbox_area if bbox_area else 0.0
        if 4 <= len(approx) <= 6 and rectangularity >= 0.55:
            add(
                PrimitiveFamily.RECTILINEAR_CLOSED_SHAPE,
                "G1_CONTOUR_RECTILINEAR_V1",
                (float(x), float(y), float(w), float(h)),
                {"vertex_count": int(len(approx)), "rectangularity": round(rectangularity, 4), "contour_area": round(area, 3)},
            )

    component_count, labels, stats, _centroids = cv2.connectedComponentsWithStats((binary > 0).astype(np.uint8), connectivity=8)
    component_cap = min(component_count, 5000)
    for label in range(1, component_cap):
        x = int(stats[label, cv2.CC_STAT_LEFT])
        y = int(stats[label, cv2.CC_STAT_TOP])
        w = int(stats[label, cv2.CC_STAT_WIDTH])
        h = int(stats[label, cv2.CC_STAT_HEIGHT])
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < 4 or w <= 0 or h <= 0:
            continue
        bbox_area = max(1, w * h)
        ink_ratio = area / bbox_area
        if ink_ratio >= 0.42 and area >= 40 and w >= 6 and h >= 6:
            family = PrimitiveFamily.FILLED_OR_HATCHED_REGION
            detector = "G1_CONNECTED_DENSE_REGION_V1"
        elif w <= max(42, int(width * 0.18)) and h <= max(30, int(height * 0.18)) and area <= 900:
            family = PrimitiveFamily.TEXT_BLOCK
            detector = "G1_SMALL_CONNECTED_GROUP_V1"
        elif area >= 18:
            family = PrimitiveFamily.COMPLEX_GRAPHIC_GROUP
            detector = "G1_CONNECTED_COMPLEX_GROUP_V1"
        else:
            family = PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP
            detector = "G1_CONNECTED_UNKNOWN_V1"
        add(
            family,
            detector,
            (float(x), float(y), float(w), float(h)),
            {"component_area": area, "ink_ratio": round(float(ink_ratio), 4)},
        )

    if not observations and np.any(binary):
        ys, xs = np.where(binary > 0)
        add(
            PrimitiveFamily.UNKNOWN_GRAPHIC_GROUP,
            "G1_FALLBACK_UNKNOWN_V1",
            (float(xs.min()), float(ys.min()), float(xs.max() - xs.min() + 1), float(ys.max() - ys.min() + 1)),
            {"reason": "UNACCOUNTED_WORKAREA_INK"},
        )

    return tuple(
        sorted(
            observations,
            key=lambda item: (
                item.family.value,
                item.y,
                item.x,
                item.width,
                item.height,
                item.primitive_id,
            ),
        )
    )
