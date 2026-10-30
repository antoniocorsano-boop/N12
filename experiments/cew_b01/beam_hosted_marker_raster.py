from __future__ import annotations

import math
from typing import Any, Sequence


def _runs(values: list[int]) -> list[tuple[int, int]]:
    if not values:
        return []
    result: list[tuple[int, int]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        result.append((start, previous))
        start = previous = value
    result.append((start, previous))
    return result


def _stroke_records(
    active_coordinates: list[int],
    *,
    long_span: float,
    max_stroke_width_fraction: float,
) -> list[dict[str, float | int]]:
    max_width = max(2.0, long_span * max_stroke_width_fraction)
    records: list[dict[str, float | int]] = []
    for start, end in _runs(active_coordinates):
        width = end - start + 1
        if width > max_width:
            continue
        records.append({
            "start": start,
            "end": end,
            "center": round((start + end) / 2.0, 6),
            "width": width,
        })
    return records


def _first_valid_pair(
    strokes: list[dict[str, float | int]],
    *,
    long_span: float,
    min_pair_separation_fraction: float,
    max_pair_separation_fraction: float,
) -> list[dict[str, float | int]]:
    min_separation = max(2.0, long_span * min_pair_separation_fraction)
    max_separation = max(min_separation, long_span * max_pair_separation_fraction)
    for index, first in enumerate(strokes):
        first_center = float(first["center"])
        for second in strokes[index + 1 :]:
            separation = abs(float(second["center"]) - first_center)
            if min_separation <= separation <= max_separation:
                return [first, second]
    return []


def detect_local_transverse_pair_from_binary(
    binary_ink: Sequence[Sequence[Any]],
    *,
    marker_geometry: dict[str, float | int],
    carrier_orientation: str,
    carrier_track_centerlines: Sequence[float | int],
    search_depth_factor: float = 2.5,
    minimum_axis_coverage: float = 0.55,
    longitudinal_margin_fraction: float = 0.10,
    max_stroke_width_fraction: float = 0.20,
    min_pair_separation_fraction: float = 0.03,
    max_pair_separation_fraction: float = 0.60,
) -> dict[str, Any]:
    """Detect two persistent strokes transverse to a carrier near one marker.

    `binary_ink` is a two-dimensional truthy/falsey raster in the same pixel
    coordinate frame as the marker/carrier geometry. The detector is neutral:
    it reports only local stroke geometry and never assigns technical meaning.
    """

    height = len(binary_ink)
    if height <= 0:
        raise ValueError("HOSTED_MARKER_RASTER_EMPTY")
    width = len(binary_ink[0])
    if width <= 0 or any(len(row) != width for row in binary_ink):
        raise ValueError("HOSTED_MARKER_RASTER_INVALID_SHAPE")
    if carrier_orientation not in {"HORIZONTAL", "VERTICAL"}:
        raise ValueError("HOSTED_MARKER_RASTER_INVALID_ORIENTATION")
    if len(carrier_track_centerlines) != 2:
        raise ValueError("HOSTED_MARKER_RASTER_REQUIRES_TWO_CARRIER_TRACKS")

    x = float(marker_geometry["x"])
    y = float(marker_geometry["y"])
    marker_width = float(marker_geometry["width"])
    marker_height = float(marker_geometry["height"])
    band_lo, band_hi = sorted(float(value) for value in carrier_track_centerlines)

    if carrier_orientation == "HORIZONTAL":
        long_start, long_end = x, x + marker_width
        long_limit = width
        cross_limit = height
    else:
        long_start, long_end = y, y + marker_height
        long_limit = height
        cross_limit = width

    long_span = max(1.0, long_end - long_start)
    longitudinal_margin = max(2.0, long_span * longitudinal_margin_fraction)
    long_a = max(0, int(math.floor(long_start - longitudinal_margin)))
    long_b = min(long_limit - 1, int(math.ceil(long_end + longitudinal_margin)))
    search_depth = max(12, int(round(long_span * search_depth_factor)))

    side_windows = [
        (
            "BEFORE_CROSS_AXIS",
            max(0, int(math.floor(band_lo)) - search_depth),
            max(0, int(math.floor(band_lo)) - 1),
        ),
        (
            "AFTER_CROSS_AXIS",
            min(cross_limit - 1, int(math.ceil(band_hi)) + 1),
            min(cross_limit - 1, int(math.ceil(band_hi)) + search_depth),
        ),
    ]

    side_results: list[dict[str, Any]] = []
    for side, cross_a, cross_b in side_windows:
        if cross_b < cross_a:
            continue
        cross_count = cross_b - cross_a + 1
        active: list[int] = []
        for long_coordinate in range(long_a, long_b + 1):
            ink_count = 0
            for cross_coordinate in range(cross_a, cross_b + 1):
                if carrier_orientation == "HORIZONTAL":
                    pixel = binary_ink[cross_coordinate][long_coordinate]
                else:
                    pixel = binary_ink[long_coordinate][cross_coordinate]
                ink_count += int(bool(pixel))
            coverage = ink_count / cross_count
            if coverage >= minimum_axis_coverage:
                active.append(long_coordinate)

        strokes = _stroke_records(
            active,
            long_span=long_span,
            max_stroke_width_fraction=max_stroke_width_fraction,
        )
        pair = _first_valid_pair(
            strokes,
            long_span=long_span,
            min_pair_separation_fraction=min_pair_separation_fraction,
            max_pair_separation_fraction=max_pair_separation_fraction,
        )
        side_results.append({
            "side": side,
            "cross_start": cross_a,
            "cross_end": cross_b,
            "stroke_runs": strokes,
            "pair_strokes": pair,
        })

    if not side_results:
        return {
            "pair_detected": False,
            "side": None,
            "stroke_runs": [],
            "pair_strokes": [],
            "longitudinal_search_start": long_a,
            "longitudinal_search_end": long_b,
        }

    selected = sorted(
        side_results,
        key=lambda result: (
            0 if result["pair_strokes"] else 1,
            -len(result["stroke_runs"]),
            result["side"],
        ),
    )[0]
    return {
        "pair_detected": len(selected["pair_strokes"]) == 2,
        "side": selected["side"],
        "stroke_runs": selected["stroke_runs"],
        "pair_strokes": selected["pair_strokes"],
        "longitudinal_search_start": long_a,
        "longitudinal_search_end": long_b,
        "cross_search_start": selected["cross_start"],
        "cross_search_end": selected["cross_end"],
    }
