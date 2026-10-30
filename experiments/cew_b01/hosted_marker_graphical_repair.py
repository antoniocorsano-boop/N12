from __future__ import annotations

import copy
from typing import Any, Sequence

from .beam_hosted_marker_raster import detect_bilateral_transverse_section_from_binary


def _marker_long_interval(candidate: dict[str, Any]) -> tuple[float, float, float]:
    geometry = candidate["marker_geometry"]
    orientation = str(candidate["carrier_orientation"])
    if orientation == "HORIZONTAL":
        start = float(geometry["x"])
        span = max(float(geometry["width"]), 1.0)
    elif orientation == "VERTICAL":
        start = float(geometry["y"])
        span = max(float(geometry["height"]), 1.0)
    else:
        raise ValueError("HOSTED_MARKER_REPAIR_INVALID_CARRIER_ORIENTATION")
    return start, start + span, span


def _marker_cross_interval(candidate: dict[str, Any]) -> tuple[float, float, float]:
    geometry = candidate["marker_geometry"]
    orientation = str(candidate["carrier_orientation"])
    if orientation == "HORIZONTAL":
        start = float(geometry["y"])
        span = max(float(geometry["height"]), 1.0)
    elif orientation == "VERTICAL":
        start = float(geometry["x"])
        span = max(float(geometry["width"]), 1.0)
    else:
        raise ValueError("HOSTED_MARKER_REPAIR_INVALID_CARRIER_ORIENTATION")
    return start, start + span, span


def carrier_topology_evidence(
    candidate: dict[str, Any],
    carrier: dict[str, Any],
    *,
    end_run_ratio_threshold: float = 0.5,
    minimum_through_overlap_ratio: float = 4.0,
) -> dict[str, Any]:
    """Describe neutral longitudinal carrier topology around one frozen marker."""

    orientation = str(candidate["carrier_orientation"])
    carrier_orientation = str(carrier.get("orientation", orientation))
    marker_start, marker_end, marker_long_span = _marker_long_interval(candidate)
    overlap_start = float(carrier["overlap_start"])
    overlap_end = float(carrier["overlap_end"])
    if overlap_end < overlap_start:
        overlap_start, overlap_end = overlap_end, overlap_start

    before_run = max(0.0, marker_start - overlap_start)
    after_run = max(0.0, overlap_end - marker_end)
    before_ratio = before_run / marker_long_span
    after_ratio = after_run / marker_long_span
    overlap_length = max(0.0, overlap_end - overlap_start)
    overlap_ratio = overlap_length / marker_long_span
    minimum_side_ratio = min(before_ratio, after_ratio)

    if carrier_orientation != orientation:
        topology_state = "AMBIGUOUS_CARRIER_TOPOLOGY"
    elif minimum_side_ratio < end_run_ratio_threshold:
        topology_state = "END_OR_TERMINATED_CARRIER"
    elif overlap_ratio < minimum_through_overlap_ratio:
        topology_state = "AMBIGUOUS_CARRIER_TOPOLOGY"
    else:
        topology_state = "THROUGH_LINEAR_CARRIER"

    return {
        "topology_state": topology_state,
        "carrier_orientation": orientation,
        "marker_long_start": round(marker_start, 6),
        "marker_long_end": round(marker_end, 6),
        "marker_long_span": round(marker_long_span, 6),
        "carrier_overlap_start": round(overlap_start, 6),
        "carrier_overlap_end": round(overlap_end, 6),
        "carrier_overlap_length": round(overlap_length, 6),
        "before_run": round(before_run, 6),
        "after_run": round(after_run, 6),
        "before_run_ratio": round(before_ratio, 12),
        "after_run_ratio": round(after_ratio, 12),
        "minimum_side_run_ratio": round(minimum_side_ratio, 12),
        "carrier_overlap_to_marker_long_span": round(overlap_ratio, 12),
        "end_run_ratio_threshold": round(float(end_run_ratio_threshold), 12),
        "minimum_through_overlap_ratio": round(float(minimum_through_overlap_ratio), 12),
    }


def marker_carrier_alignment_evidence(
    candidate: dict[str, Any],
    carrier: dict[str, Any],
    *,
    max_center_offset_ratio: float = 0.25,
) -> dict[str, Any]:
    """Measure marker centering relative to the selected carrier band.

    This is a neutral relationship check. It never moves the marker or rewrites
    the carrier; it only records whether the frozen G1 marker is centered on the
    two-track carrier band within a scale-normalized tolerance.
    """

    marker_cross_start, marker_cross_end, marker_cross_span = _marker_cross_interval(candidate)
    marker_cross_center = (marker_cross_start + marker_cross_end) / 2.0
    centerlines = sorted(float(value) for value in carrier.get("track_centerlines", []))
    if len(centerlines) != 2:
        raise ValueError("HOSTED_MARKER_REPAIR_REQUIRES_TWO_CARRIER_TRACKS")

    carrier_band_start, carrier_band_end = centerlines
    carrier_band_center = (carrier_band_start + carrier_band_end) / 2.0
    carrier_separation = abs(carrier_band_end - carrier_band_start)
    center_offset_px = abs(marker_cross_center - carrier_band_center)
    center_offset_ratio = center_offset_px / marker_cross_span
    separation_ratio = carrier_separation / marker_cross_span

    carrier_alignment_state = (
        "CARRIER_ALIGNED"
        if center_offset_ratio <= max_center_offset_ratio
        else "CARRIER_MISALIGNED"
    )

    return {
        "carrier_alignment_state": carrier_alignment_state,
        "marker_cross_start": round(marker_cross_start, 6),
        "marker_cross_end": round(marker_cross_end, 6),
        "marker_cross_span": round(marker_cross_span, 6),
        "marker_cross_center": round(marker_cross_center, 6),
        "carrier_band_start": round(carrier_band_start, 6),
        "carrier_band_end": round(carrier_band_end, 6),
        "carrier_band_center": round(carrier_band_center, 6),
        "carrier_separation": round(carrier_separation, 6),
        "center_offset_px": round(center_offset_px, 6),
        "center_offset_to_marker_cross_span": round(center_offset_ratio, 12),
        "carrier_separation_to_marker_cross_span": round(separation_ratio, 12),
        "max_center_offset_ratio": round(float(max_center_offset_ratio), 12),
    }


def _binary_shape(binary_ink: Sequence[Sequence[Any]]) -> tuple[int, int]:
    height = len(binary_ink)
    if height <= 0:
        raise ValueError("HOSTED_MARKER_ALIGNMENT_EMPTY_RASTER")
    width = len(binary_ink[0])
    if width <= 0 or any(len(row) != width for row in binary_ink):
        raise ValueError("HOSTED_MARKER_ALIGNMENT_INVALID_RASTER")
    return width, height


def _horizontal_edge_support(
    binary_ink: Sequence[Sequence[Any]],
    *,
    x0: int,
    x1: int,
    y: int,
    tolerance_px: int,
    width: int,
    height: int,
) -> float:
    start = max(0, min(x0, x1))
    end = min(width - 1, max(x0, x1))
    if end < start:
        return 0.0
    supported = 0
    total = end - start + 1
    for x in range(start, end + 1):
        found = False
        for yy in range(max(0, y - tolerance_px), min(height - 1, y + tolerance_px) + 1):
            if bool(binary_ink[yy][x]):
                found = True
                break
        supported += int(found)
    return supported / total if total else 0.0


def _vertical_edge_support(
    binary_ink: Sequence[Sequence[Any]],
    *,
    y0: int,
    y1: int,
    x: int,
    tolerance_px: int,
    width: int,
    height: int,
) -> float:
    start = max(0, min(y0, y1))
    end = min(height - 1, max(y0, y1))
    if end < start:
        return 0.0
    supported = 0
    total = end - start + 1
    for y in range(start, end + 1):
        found = False
        for xx in range(max(0, x - tolerance_px), min(width - 1, x + tolerance_px) + 1):
            if bool(binary_ink[y][xx]):
                found = True
                break
        supported += int(found)
    return supported / total if total else 0.0


def marker_alignment_evidence(
    binary_ink: Sequence[Sequence[Any]],
    marker_geometry: dict[str, Any],
    *,
    tolerance_px: int = 2,
    aligned_minimum_side_support: float = 0.55,
    mismatch_minimum_side_support: float = 0.15,
) -> dict[str, Any]:
    """Measure raster support for the four edges of the frozen marker geometry.

    The function is diagnostic only. It never returns replacement or snapped
    geometry; the supplied G1 rectangle remains the provenance anchor.
    """

    width, height = _binary_shape(binary_ink)
    x0 = int(round(float(marker_geometry["x"])))
    y0 = int(round(float(marker_geometry["y"])))
    marker_width = max(1, int(round(float(marker_geometry["width"]))))
    marker_height = max(1, int(round(float(marker_geometry["height"]))))
    x1 = x0 + marker_width - 1
    y1 = y0 + marker_height - 1

    side_support = {
        "top": _horizontal_edge_support(
            binary_ink,
            x0=x0,
            x1=x1,
            y=y0,
            tolerance_px=tolerance_px,
            width=width,
            height=height,
        ),
        "bottom": _horizontal_edge_support(
            binary_ink,
            x0=x0,
            x1=x1,
            y=y1,
            tolerance_px=tolerance_px,
            width=width,
            height=height,
        ),
        "left": _vertical_edge_support(
            binary_ink,
            y0=y0,
            y1=y1,
            x=x0,
            tolerance_px=tolerance_px,
            width=width,
            height=height,
        ),
        "right": _vertical_edge_support(
            binary_ink,
            y0=y0,
            y1=y1,
            x=x1,
            tolerance_px=tolerance_px,
            width=width,
            height=height,
        ),
    }
    side_support = {key: round(value, 12) for key, value in sorted(side_support.items())}
    minimum_side_support = min(side_support.values())
    mean_side_support = sum(side_support.values()) / len(side_support)

    if minimum_side_support >= aligned_minimum_side_support:
        alignment_state = "ALIGNED"
    elif minimum_side_support < mismatch_minimum_side_support:
        alignment_state = "GEOMETRY_MISMATCH"
    else:
        alignment_state = "WEAK_EDGE_SUPPORT"

    return {
        "alignment_state": alignment_state,
        "side_support": side_support,
        "minimum_side_support": round(minimum_side_support, 12),
        "mean_side_support": round(mean_side_support, 12),
        "tolerance_px": int(tolerance_px),
        "aligned_minimum_side_support": round(float(aligned_minimum_side_support), 12),
        "mismatch_minimum_side_support": round(float(mismatch_minimum_side_support), 12),
    }


def refine_graphical_candidate(
    candidate: dict[str, Any],
    carrier: dict[str, Any],
    binary_ink: Sequence[Sequence[Any]],
) -> dict[str, Any]:
    """Add neutral repair evidence without mutating or semantically promoting input."""

    item = copy.deepcopy(candidate)
    topology = carrier_topology_evidence(candidate, carrier)
    alignment = marker_alignment_evidence(binary_ink, candidate["marker_geometry"])
    carrier_alignment = marker_carrier_alignment_evidence(candidate, carrier)
    transverse = detect_bilateral_transverse_section_from_binary(
        binary_ink,
        marker_geometry=candidate["marker_geometry"],
        carrier_orientation=str(candidate["carrier_orientation"]),
        carrier_track_centerlines=list(carrier["track_centerlines"]),
    )

    if (
        alignment["alignment_state"] != "ALIGNED"
        or carrier_alignment["carrier_alignment_state"] != "CARRIER_ALIGNED"
    ):
        role = "MARKER_ALIGNMENT_REVIEW"
    elif topology["topology_state"] != "THROUGH_LINEAR_CARRIER":
        role = "CARRIER_TOPOLOGY_REVIEW"
    elif transverse["section_state"] == "UNILATERAL_PAIR_OR_PARTIAL":
        role = "PARTIAL_TRANSVERSE_REVIEW"
    elif transverse["section_state"] == "BILATERAL_DOUBLE_PAIR":
        role = "REVIEW_ELIGIBLE_BILATERAL_DOUBLE_PAIR"
    else:
        role = "REVIEW_ELIGIBLE_ALONE"

    item["carrier_topology_evidence"] = topology
    item["marker_alignment_evidence"] = alignment
    item["marker_carrier_alignment_evidence"] = carrier_alignment
    item["transverse_section_evidence"] = transverse
    item["graphical_repair_role"] = role
    item["semantic_meaning"] = None
    item["structural_identity_authorized"] = False
    item["canonical_write_authorized"] = False
    item["g3_authorized"] = False
    item["merge_authorized"] = False
    return item
