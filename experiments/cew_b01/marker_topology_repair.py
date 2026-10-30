from __future__ import annotations

import math
from typing import Any, Sequence


def _binary_dimensions(binary_ink: Sequence[Sequence[Any]]) -> tuple[int, int]:
    height = len(binary_ink)
    width = len(binary_ink[0]) if height else 0
    return width, height


def _geometry_float(geometry: dict[str, Any]) -> dict[str, float]:
    return {
        "x": float(geometry["x"]),
        "y": float(geometry["y"]),
        "width": float(geometry["width"]),
        "height": float(geometry["height"]),
    }


def _horizontal_support(
    binary_ink: Sequence[Sequence[Any]],
    *,
    y: int,
    x0: int,
    x1: int,
) -> float:
    image_width, image_height = _binary_dimensions(binary_ink)
    if y < 0 or y >= image_height:
        return 0.0
    lo = max(0, min(x0, x1))
    hi = min(image_width - 1, max(x0, x1))
    if hi < lo:
        return 0.0
    count = sum(1 for x in range(lo, hi + 1) if bool(binary_ink[y][x]))
    return count / max(1, hi - lo + 1)


def _vertical_support(
    binary_ink: Sequence[Sequence[Any]],
    *,
    x: int,
    y0: int,
    y1: int,
) -> float:
    image_width, image_height = _binary_dimensions(binary_ink)
    if x < 0 or x >= image_width:
        return 0.0
    lo = max(0, min(y0, y1))
    hi = min(image_height - 1, max(y0, y1))
    if hi < lo:
        return 0.0
    count = sum(1 for y in range(lo, hi + 1) if bool(binary_ink[y][x]))
    return count / max(1, hi - lo + 1)


def _best_axis_position(
    *,
    center: float,
    radius: int,
    support_at: Any,
) -> tuple[int, float]:
    anchor = int(round(center))
    candidates: list[tuple[float, int, int]] = []
    for position in range(anchor - radius, anchor + radius + 1):
        support = float(support_at(position))
        candidates.append((-support, abs(position - anchor), position))
    _neg_support, _distance, position = min(candidates)
    return position, -_neg_support


def _edge_supports(
    binary_ink: Sequence[Sequence[Any]],
    geometry: dict[str, float],
) -> dict[str, float]:
    x0 = int(round(geometry["x"]))
    y0 = int(round(geometry["y"]))
    x1 = int(round(geometry["x"] + geometry["width"]))
    y1 = int(round(geometry["y"] + geometry["height"]))
    return {
        "top": _horizontal_support(binary_ink, y=y0, x0=x0, x1=x1),
        "bottom": _horizontal_support(binary_ink, y=y1, x0=x0, x1=x1),
        "left": _vertical_support(binary_ink, x=x0, y0=y0, y1=y1),
        "right": _vertical_support(binary_ink, x=x1, y0=y0, y1=y1),
    }


def _edge_residual(supports: dict[str, float]) -> float:
    return round(sum(1.0 - max(0.0, min(1.0, float(value))) for value in supports.values()), 12)


def _iou(first: dict[str, float], second: dict[str, float]) -> float:
    ax0, ay0 = first["x"], first["y"]
    ax1, ay1 = ax0 + first["width"], ay0 + first["height"]
    bx0, by0 = second["x"], second["y"]
    bx1, by1 = bx0 + second["width"], by0 + second["height"]
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    intersection = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
    union = first["width"] * first["height"] + second["width"] * second["height"] - intersection
    return 0.0 if union <= 0.0 else intersection / union


def refine_marker_grounding(
    candidate: dict[str, Any],
    binary_ink: Sequence[Sequence[Any]],
    *,
    minimum_edge_support: float = 0.60,
    minimum_residual_improvement: float = 0.05,
    max_dimension_ratio_change: float = 0.25,
) -> dict[str, Any]:
    """Refine a review overlay locally without rewriting the G1 marker geometry."""

    result = dict(candidate)
    source = _geometry_float(candidate["marker_geometry"])
    width = max(source["width"], 1.0)
    height = max(source["height"], 1.0)
    search_radius = max(6, int(round(min(width, height) * 0.15)))

    source_supports = _edge_supports(binary_ink, source)
    source_residual = _edge_residual(source_supports)

    source_x0 = source["x"]
    source_y0 = source["y"]
    source_x1 = source["x"] + source["width"]
    source_y1 = source["y"] + source["height"]

    left, left_support = _best_axis_position(
        center=source_x0,
        radius=search_radius,
        support_at=lambda x: _vertical_support(
            binary_ink,
            x=x,
            y0=int(round(source_y0 - search_radius)),
            y1=int(round(source_y1 + search_radius)),
        ),
    )
    right, right_support = _best_axis_position(
        center=source_x1,
        radius=search_radius,
        support_at=lambda x: _vertical_support(
            binary_ink,
            x=x,
            y0=int(round(source_y0 - search_radius)),
            y1=int(round(source_y1 + search_radius)),
        ),
    )
    top, top_support = _best_axis_position(
        center=source_y0,
        radius=search_radius,
        support_at=lambda y: _horizontal_support(
            binary_ink,
            y=y,
            x0=int(round(source_x0 - search_radius)),
            x1=int(round(source_x1 + search_radius)),
        ),
    )
    bottom, bottom_support = _best_axis_position(
        center=source_y1,
        radius=search_radius,
        support_at=lambda y: _horizontal_support(
            binary_ink,
            y=y,
            x0=int(round(source_x0 - search_radius)),
            x1=int(round(source_x1 + search_radius)),
        ),
    )

    refined = {
        "x": float(left),
        "y": float(top),
        "width": float(right - left),
        "height": float(bottom - top),
    }
    refined_supports = {
        "top": top_support,
        "bottom": bottom_support,
        "left": left_support,
        "right": right_support,
    }
    refined_residual = _edge_residual(refined_supports)

    valid_shape = refined["width"] > 0.0 and refined["height"] > 0.0
    width_ratio = refined["width"] / width if width > 0.0 else 0.0
    height_ratio = refined["height"] / height if height > 0.0 else 0.0
    dimensions_local = (
        1.0 - max_dimension_ratio_change <= width_ratio <= 1.0 + max_dimension_ratio_change
        and 1.0 - max_dimension_ratio_change <= height_ratio <= 1.0 + max_dimension_ratio_change
    )
    all_edges_supported = min(refined_supports.values()) >= minimum_edge_support

    source_center = (source["x"] + source["width"] / 2.0, source["y"] + source["height"] / 2.0)
    refined_center = (
        refined["x"] + refined["width"] / 2.0,
        refined["y"] + refined["height"] / 2.0,
    )
    center_shift = math.hypot(refined_center[0] - source_center[0], refined_center[1] - source_center[1])
    local_shift = center_shift <= math.sqrt(2.0) * search_radius
    improvement = source_residual - refined_residual

    use_refined = (
        valid_shape
        and dimensions_local
        and all_edges_supported
        and local_shift
        and improvement >= minimum_residual_improvement
    )

    review = refined if use_refined else source
    review_supports = refined_supports if use_refined else source_supports
    review_residual = refined_residual if use_refined else source_residual

    result["source_marker_geometry"] = dict(source)
    result["review_marker_geometry"] = dict(review)
    result["marker_grounding"] = {
        "method": "RASTER_REFINED_LOCAL_RECT" if use_refined else "G1_EXACT",
        "qualified": bool(min(review_supports.values()) >= minimum_edge_support),
        "search_radius_px": float(search_radius),
        "source_edge_support": {key: round(value, 12) for key, value in sorted(source_supports.items())},
        "review_edge_support": {key: round(value, 12) for key, value in sorted(review_supports.items())},
        "source_edge_residual": round(source_residual, 12),
        "review_edge_residual": round(review_residual, 12),
        "center_shift_px": round(center_shift if use_refined else 0.0, 12),
        "iou_with_source": round(_iou(source, review), 12),
    }
    result["semantic_meaning"] = None
    result["structural_identity_authorized"] = False
    result["canonical_write_authorized"] = False
    result["g3_authorized"] = False
    result["merge_authorized"] = False
    return result


def _marker_long_interval(candidate: dict[str, Any]) -> tuple[float, float, float]:
    geometry = _geometry_float(candidate.get("review_marker_geometry") or candidate["marker_geometry"])
    orientation = str(candidate["carrier_orientation"])
    if orientation == "HORIZONTAL":
        start = geometry["x"]
        end = geometry["x"] + geometry["width"]
    elif orientation == "VERTICAL":
        start = geometry["y"]
        end = geometry["y"] + geometry["height"]
    else:
        raise ValueError("MARKER_TOPOLOGY_INVALID_CARRIER_ORIENTATION")
    return start, end, max(1.0, end - start)


def describe_carrier_topology(
    candidate: dict[str, Any],
    tracks: list[dict[str, Any]],
    *,
    carrier_cross_tolerance_px: float = 4.0,
    through_fraction: float = 0.75,
    terminal_fraction: float = 0.25,
    junction_edge_fraction: float = 0.25,
    junction_edge_min_px: float = 8.0,
) -> dict[str, Any]:
    """Describe local carrier continuity and junction geometry without technical semantics."""

    orientation = str(candidate["carrier_orientation"])
    if orientation not in {"HORIZONTAL", "VERTICAL"}:
        raise ValueError("MARKER_TOPOLOGY_INVALID_CARRIER_ORIENTATION")

    long_start, long_end, long_span = _marker_long_interval(candidate)
    overlap_start = float(candidate["carrier_overlap_start"])
    overlap_end = float(candidate["carrier_overlap_end"])
    continuation_before = max(0.0, long_start - overlap_start)
    continuation_after = max(0.0, overlap_end - long_end)

    track_by_id = {str(track["track_id"]): track for track in tracks}
    carrier_track_ids = sorted(str(track_id) for track_id in candidate.get("carrier_track_ids", []))
    carrier_tracks = [track_by_id[track_id] for track_id in carrier_track_ids if track_id in track_by_id]
    centerlines = sorted(float(track["centerline"]) for track in carrier_tracks)
    band_lo = centerlines[0] if centerlines else float("nan")
    band_hi = centerlines[-1] if centerlines else float("nan")

    orthogonal = "VERTICAL" if orientation == "HORIZONTAL" else "HORIZONTAL"
    junction_window = max(junction_edge_min_px, junction_edge_fraction * long_span)
    end_junction_tracks: list[dict[str, Any]] = []
    if centerlines:
        for track in tracks:
            track_id = str(track.get("track_id", ""))
            if track_id in carrier_track_ids or str(track.get("orientation")) != orthogonal:
                continue
            if float(track["start"]) > band_lo + carrier_cross_tolerance_px:
                continue
            if float(track["end"]) < band_hi - carrier_cross_tolerance_px:
                continue
            long_position = float(track["centerline"])
            edge_distance = min(abs(long_position - long_start), abs(long_position - long_end))
            if edge_distance <= junction_window:
                end_junction_tracks.append(track)

    end_junction_track_ids = sorted(str(track["track_id"]) for track in end_junction_tracks)
    through_threshold = through_fraction * long_span
    terminal_threshold = terminal_fraction * long_span
    through = continuation_before >= through_threshold and continuation_after >= through_threshold
    terminal_asymmetry = (
        continuation_before <= terminal_threshold and continuation_after >= through_threshold
    ) or (
        continuation_after <= terminal_threshold and continuation_before >= through_threshold
    )

    if len(end_junction_track_ids) >= 2:
        topology_state = "JUNCTION_COMPLEX"
    elif terminal_asymmetry:
        topology_state = "TERMINAL_OR_STEM"
    elif through:
        topology_state = "THROUGH_CONTINUOUS"
    else:
        topology_state = "AMBIGUOUS"

    return {
        "topology_state": topology_state,
        "carrier_orientation": orientation,
        "carrier_track_ids": carrier_track_ids,
        "continuation_before_px": round(continuation_before, 6),
        "continuation_after_px": round(continuation_after, 6),
        "through_threshold_px": round(through_threshold, 6),
        "terminal_threshold_px": round(terminal_threshold, 6),
        "junction_edge_window_px": round(junction_window, 6),
        "end_junction_track_ids": end_junction_track_ids,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }
