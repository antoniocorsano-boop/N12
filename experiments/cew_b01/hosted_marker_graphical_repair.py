from __future__ import annotations

from typing import Any


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
