from __future__ import annotations

from typing import Any, Sequence

from .beam_hosted_marker_raster import detect_local_transverse_pair_from_binary
from .beam_hosted_markers import (
    build_hosted_marker_candidates,
    build_line_tracks,
    build_linear_carriers,
)


def build_hybrid_hosted_marker_candidates(
    primitives: list[dict[str, Any]],
    marker_seed_ids: list[str],
    binary_ink: Sequence[Sequence[Any]],
) -> list[dict[str, Any]]:
    """Combine neutral primitive and local-raster evidence without hiding either.

    Primitive evidence determines carrier binding and its own local-track state.
    Raster evidence may independently establish a local transverse pair missed by
    Hough segmentation. The result remains nonsemantic and nonpromoting.
    """

    primitive_candidates = build_hosted_marker_candidates(primitives, marker_seed_ids)
    carriers = {
        carrier["carrier_id"]: carrier
        for carrier in build_linear_carriers(build_line_tracks(primitives))
    }

    results: list[dict[str, Any]] = []
    for candidate in primitive_candidates:
        carrier = carriers.get(candidate["carrier_id"])
        if carrier is None:
            raise ValueError("HOSTED_MARKER_HYBRID_CARRIER_MISSING")

        raster_evidence = detect_local_transverse_pair_from_binary(
            binary_ink,
            marker_geometry=candidate["marker_geometry"],
            carrier_orientation=candidate["carrier_orientation"],
            carrier_track_centerlines=carrier["track_centerlines"],
        )
        primitive_pair = len(candidate.get("transverse_pair_track_ids", [])) == 2
        evidence_sources: list[str] = []
        if primitive_pair:
            evidence_sources.append("PRIMITIVE_LOCAL_TRACK_PAIR")
        if bool(raster_evidence.get("pair_detected")):
            evidence_sources.append("RASTER_LOCAL_PROFILE")

        result = dict(candidate)
        result["primitive_graphical_state"] = candidate["graphical_state"]
        result["raster_transverse_evidence"] = raster_evidence
        result["pair_evidence_sources"] = evidence_sources
        result["graphical_state"] = (
            "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE"
            if evidence_sources
            else "RECT_ALONE_ON_CARRIER"
        )

        # Reassert the experimental authority boundary explicitly so this layer
        # cannot accidentally inherit or manufacture semantic authority.
        result["semantic_meaning"] = None
        result["structural_identity_authorized"] = False
        result["canonical_write_authorized"] = False
        result["g3_authorized"] = False
        result["merge_authorized"] = False
        result["review_state"] = "UNREVIEWED"
        results.append(result)

    return sorted(
        results,
        key=lambda item: (item["marker_primitive_id"], item["hosted_marker_id"]),
    )
