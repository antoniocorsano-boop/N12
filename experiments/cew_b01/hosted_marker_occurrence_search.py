from __future__ import annotations

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
