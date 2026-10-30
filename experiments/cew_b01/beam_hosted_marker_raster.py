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


def _side_transverse_results(
    binary_ink: Sequence[Sequence[Any]],
    *,
    marker_geometry: dict[str, float | int],
    carrier_orientation: str,
    carrier_track_centerlines: Sequence[float | int],
    search_depth_factor: float,
    minimum_axis_coverage: float,
    longitudinal_margin_fraction: float,
    max_stroke_width_fraction: float,
    min_pair_separation_fraction: float,
    max_pair_separation_fraction: float,
) -> tuple[list[dict[str, Any]], int, int]:
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
            "pair_detected": len(pair) == 2,
        })

    return side_results, long_a, long_b


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
    """Detect one local transverse pair while preserving the legacy selection rule."""

    side_results, long_a, long_b = _side_transverse_results(
        binary_ink,
        marker_geometry=marker_geometry,
        carrier_orientation=carrier_orientation,
        carrier_track_centerlines=carrier_track_centerlines,
        search_depth_factor=search_depth_factor,
        minimum_axis_coverage=minimum_axis_coverage,
        longitudinal_margin_fraction=longitudinal_margin_fraction,
        max_stroke_width_fraction=max_stroke_width_fraction,
        min_pair_separation_fraction=min_pair_separation_fraction,
        max_pair_separation_fraction=max_pair_separation_fraction,
    )

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


def detect_bilateral_transverse_section_from_binary(
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
    """Evaluate the two cross-axis sides independently for a neutral double-pair section."""

    side_results, long_a, long_b = _side_transverse_results(
        binary_ink,
        marker_geometry=marker_geometry,
        carrier_orientation=carrier_orientation,
        carrier_track_centerlines=carrier_track_centerlines,
        search_depth_factor=search_depth_factor,
        minimum_axis_coverage=minimum_axis_coverage,
        longitudinal_margin_fraction=longitudinal_margin_fraction,
        max_stroke_width_fraction=max_stroke_width_fraction,
        min_pair_separation_fraction=min_pair_separation_fraction,
        max_pair_separation_fraction=max_pair_separation_fraction,
    )
    by_side = {item["side"]: item for item in side_results}
    empty_side = {
        "cross_start": None,
        "cross_end": None,
        "stroke_runs": [],
        "pair_strokes": [],
        "pair_detected": False,
    }
    before = dict(by_side.get("BEFORE_CROSS_AXIS", empty_side))
    after = dict(by_side.get("AFTER_CROSS_AXIS", empty_side))
    before.pop("side", None)
    after.pop("side", None)
    pair_side_count = int(bool(before.get("pair_detected"))) + int(bool(after.get("pair_detected")))
    if pair_side_count == 2:
        section_state = "BILATERAL_DOUBLE_PAIR"
    elif pair_side_count == 1 or before.get("stroke_runs") or after.get("stroke_runs"):
        section_state = "UNILATERAL_PAIR_OR_PARTIAL"
    else:
        section_state = "NO_TRANSVERSE_SECTION"

    return {
        "bilateral_double_pair_detected": pair_side_count == 2,
        "pair_side_count": pair_side_count,
        "section_state": section_state,
        "before": before,
        "after": after,
        "longitudinal_search_start": long_a,
        "longitudinal_search_end": long_b,
    }
