from __future__ import annotations

import math
from typing import Any, Sequence

from .beam_hosted_marker_hybrid import build_hybrid_hosted_marker_candidates


def discover_hosted_marker_occurrences(
    primitives: list[dict[str, Any]],
    binary_ink: Sequence[Sequence[Any]],
) -> list[dict[str, Any]]:
    """Run the qualified hybrid hosted-marker pipeline on every rectilinear seed.

    Discovery adds no new carrier rules, semantics, or promotion authority. A
    rectilinear observation is emitted only when the existing hybrid pipeline
    can bind it to a local carrier.
    """

    marker_seed_ids = sorted(
        str(item["primitive_id"])
        for item in primitives
        if item.get("family") == "RECTILINEAR_CLOSED_SHAPE"
    )
    if not marker_seed_ids:
        return []

    occurrences = build_hybrid_hosted_marker_candidates(
        primitives,
        marker_seed_ids,
        binary_ink,
    )
    return sorted(
        occurrences,
        key=lambda item: (str(item["marker_primitive_id"]), str(item["hosted_marker_id"])),
    )


def hosted_marker_signature(candidate: dict[str, Any]) -> dict[str, float]:
    """Return scale-normalized neutral geometry used only for review ordering."""

    geometry = candidate["marker_geometry"]
    width = float(geometry["width"])
    height = float(geometry["height"])
    orientation = str(candidate["carrier_orientation"])
    if orientation == "HORIZONTAL":
        long_span, cross_span = width, height
    elif orientation == "VERTICAL":
        long_span, cross_span = height, width
    else:
        raise ValueError("HOSTED_MARKER_SIGNATURE_INVALID_ORIENTATION")

    long_span = max(long_span, 1e-9)
    cross_span = max(cross_span, 1e-9)
    overlap_length = max(
        float(candidate["carrier_overlap_end"]) - float(candidate["carrier_overlap_start"]),
        1e-9,
    )
    signature = {
        "marker_long_to_cross": long_span / cross_span,
        "carrier_separation_to_marker_cross_span": float(candidate["carrier_separation"]) / cross_span,
        "marker_long_span_to_carrier_overlap": long_span / overlap_length,
    }

    raster = candidate.get("raster_transverse_evidence") or {}
    pair_strokes = list(raster.get("pair_strokes") or [])
    if bool(raster.get("pair_detected")) and len(pair_strokes) >= 2:
        centers = sorted(float(stroke["center"]) for stroke in pair_strokes[:2])
        separation = abs(centers[1] - centers[0])
        if separation > 0.0:
            signature["raster_pair_separation_to_marker_long_span"] = separation / long_span

    return {key: round(float(value), 12) for key, value in sorted(signature.items())}


def prototype_distance(
    candidate_signature: dict[str, float],
    prototype_signature: dict[str, float],
) -> float:
    """Compare only shared positive signature components using log-ratio distance."""

    shared = sorted(set(candidate_signature) & set(prototype_signature))
    if not shared:
        raise ValueError("HOSTED_MARKER_PROTOTYPE_NO_SHARED_SIGNATURE")

    distance = 0.0
    compared = 0
    for key in shared:
        candidate_value = float(candidate_signature[key])
        prototype_value = float(prototype_signature[key])
        if candidate_value <= 0.0 or prototype_value <= 0.0:
            continue
        distance += abs(math.log(candidate_value / prototype_value))
        compared += 1
    if compared == 0:
        raise ValueError("HOSTED_MARKER_PROTOTYPE_NO_POSITIVE_SIGNATURE")
    return round(distance, 12)


def _geometry_sort_key(candidate: dict[str, Any]) -> tuple[float, float, float, float]:
    geometry = candidate["marker_geometry"]
    return (
        float(geometry["y"]),
        float(geometry["x"]),
        float(geometry["height"]),
        float(geometry["width"]),
    )


def rank_occurrences_for_review(
    occurrences: list[dict[str, Any]],
    prototype_by_state: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rank additional same-state occurrences by neutral prototype resemblance.

    Frozen prototypes are excluded from the returned review list. Ranking is for
    human-review ordering only and never changes the candidate graphical state.
    """

    prototype_signatures = {
        state: hosted_marker_signature(prototype)
        for state, prototype in prototype_by_state.items()
    }
    prototype_ids = {
        state: str(prototype["marker_primitive_id"])
        for state, prototype in prototype_by_state.items()
    }

    ranked: list[dict[str, Any]] = []
    for occurrence in occurrences:
        state = str(occurrence.get("graphical_state", ""))
        if state not in prototype_by_state:
            continue
        if str(occurrence["marker_primitive_id"]) == prototype_ids[state]:
            continue

        item = dict(occurrence)
        item["prototype_marker_primitive_id"] = prototype_ids[state]
        item["prototype_distance"] = prototype_distance(
            hosted_marker_signature(occurrence),
            prototype_signatures[state],
        )
        item["review_state"] = "UNREVIEWED"
        ranked.append(item)

    return sorted(
        ranked,
        key=lambda item: (
            str(item["graphical_state"]),
            float(item["prototype_distance"]),
            _geometry_sort_key(item),
            str(item["marker_primitive_id"]),
            str(item["hosted_marker_id"]),
        ),
    )
