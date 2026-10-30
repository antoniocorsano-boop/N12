from __future__ import annotations

from typing import Any, Sequence

from experiments.cew_b01.marker_topology_repair import _cluster_positions, _geometry_float


def _binary_dimensions(binary_ink: Sequence[Sequence[Any]]) -> tuple[int, int]:
    height = len(binary_ink)
    width = len(binary_ink[0]) if height else 0
    return width, height


def _vertical_support(
    binary_ink: Sequence[Sequence[Any]], *, x: int, y0: int, y1: int
) -> float:
    width, height = _binary_dimensions(binary_ink)
    if x < 0 or x >= width:
        return 0.0
    lo = max(0, min(y0, y1))
    hi = min(height - 1, max(y0, y1))
    if hi < lo:
        return 0.0
    return sum(1 for y in range(lo, hi + 1) if bool(binary_ink[y][x])) / max(
        1, hi - lo + 1
    )


def _horizontal_support(
    binary_ink: Sequence[Sequence[Any]], *, y: int, x0: int, x1: int
) -> float:
    width, height = _binary_dimensions(binary_ink)
    if y < 0 or y >= height:
        return 0.0
    lo = max(0, min(x0, x1))
    hi = min(width - 1, max(x0, x1))
    if hi < lo:
        return 0.0
    return sum(1 for x in range(lo, hi + 1) if bool(binary_ink[y][x])) / max(
        1, hi - lo + 1
    )


def _group_contiguous_positions(
    positions: list[tuple[int, float]], *, source: str
) -> list[dict[str, Any]]:
    if not positions:
        return []
    ordered = sorted(positions)
    groups: list[list[tuple[int, float]]] = [[ordered[0]]]
    for item in ordered[1:]:
        if item[0] <= groups[-1][-1][0] + 1:
            groups[-1].append(item)
        else:
            groups.append([item])
    result: list[dict[str, Any]] = []
    for group in groups:
        coords = [position for position, _support in group]
        support = max(value for _position, value in group)
        result.append(
            {
                "centerline": round(sum(coords) / len(coords), 6),
                "profile_start": float(min(coords)),
                "profile_end": float(max(coords)),
                "support": round(float(support), 6),
                "source": source,
            }
        )
    return result


def _match_cross_side_centers(
    negative: list[float], positive: list[float], tolerance_px: float
) -> list[dict[str, float]]:
    remaining = list(sorted(positive))
    pairs: list[dict[str, float]] = []
    for negative_center in sorted(negative):
        if not remaining:
            break
        ranked = sorted(
            (
                abs(positive_center - negative_center),
                positive_center,
            )
            for positive_center in remaining
        )
        distance, positive_center = ranked[0]
        if distance <= tolerance_px:
            remaining.remove(positive_center)
            pairs.append(
                {
                    "negative_center": round(float(negative_center), 6),
                    "positive_center": round(float(positive_center), 6),
                    "delta_px": round(float(distance), 6),
                }
            )
    return pairs


def _raster_cross_side_strokes(
    binary_ink: Sequence[Sequence[Any]],
    *,
    orientation: str,
    long_lo: float,
    long_hi: float,
    cross_lo: float,
    cross_hi: float,
    side_depth_px: float,
    minimum_profile_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    width, height = _binary_dimensions(binary_ink)
    if width <= 0 or height <= 0:
        return [], []

    negative_hits: list[tuple[int, float]] = []
    positive_hits: list[tuple[int, float]] = []
    if orientation == "HORIZONTAL":
        start = max(0, int(round(long_lo)))
        end = min(width - 1, int(round(long_hi)))
        neg_a = int(round(cross_lo - side_depth_px))
        neg_b = int(round(cross_lo - 1.0))
        pos_a = int(round(cross_hi + 1.0))
        pos_b = int(round(cross_hi + side_depth_px))
        for x in range(start, end + 1):
            negative_support = _vertical_support(binary_ink, x=x, y0=neg_a, y1=neg_b)
            positive_support = _vertical_support(binary_ink, x=x, y0=pos_a, y1=pos_b)
            if negative_support >= minimum_profile_fraction:
                negative_hits.append((x, negative_support))
            if positive_support >= minimum_profile_fraction:
                positive_hits.append((x, positive_support))
    else:
        start = max(0, int(round(long_lo)))
        end = min(height - 1, int(round(long_hi)))
        neg_a = int(round(cross_lo - side_depth_px))
        neg_b = int(round(cross_lo - 1.0))
        pos_a = int(round(cross_hi + 1.0))
        pos_b = int(round(cross_hi + side_depth_px))
        for y in range(start, end + 1):
            negative_support = _horizontal_support(binary_ink, y=y, x0=neg_a, x1=neg_b)
            positive_support = _horizontal_support(binary_ink, y=y, x0=pos_a, x1=pos_b)
            if negative_support >= minimum_profile_fraction:
                negative_hits.append((y, negative_support))
            if positive_support >= minimum_profile_fraction:
                positive_hits.append((y, positive_support))

    return (
        _group_contiguous_positions(negative_hits, source="RASTER_LOCAL_PROFILE"),
        _group_contiguous_positions(positive_hits, source="RASTER_LOCAL_PROFILE"),
    )


def describe_transverse_band(
    candidate: dict[str, Any],
    tracks: list[dict[str, Any]],
    binary_ink: Sequence[Sequence[Any]],
    *,
    carrier_cross_tolerance_px: float = 4.0,
    dedupe_tolerance_px: float = 3.0,
    raster_profile_fraction: float = 0.60,
    longitudinal_margin_fraction: float = 0.50,
    side_depth_cross_fraction: float = 2.50,
    minimum_side_depth_px: float = 24.0,
    pair_alignment_fraction: float = 0.12,
    minimum_pair_alignment_px: float = 6.0,
) -> dict[str, Any]:
    """Describe orthogonal traces on opposite sides of the carrier cross-axis.

    This is deliberately graphical and non-semantic.  For a horizontal carrier,
    the two sides are ABOVE/BELOW; for a vertical carrier they are LEFT/RIGHT.
    A complete double band requires two longitudinally matched cross-side pairs.
    """

    orientation = str(candidate["carrier_orientation"])
    if orientation not in {"HORIZONTAL", "VERTICAL"}:
        raise ValueError("MARKER_TOPOLOGY_INVALID_CARRIER_ORIENTATION")

    geometry = _geometry_float(
        candidate.get("review_marker_geometry") or candidate["marker_geometry"]
    )
    if orientation == "HORIZONTAL":
        long_start = geometry["x"]
        long_end = geometry["x"] + geometry["width"]
        marker_cross_lo = geometry["y"]
        marker_cross_hi = geometry["y"] + geometry["height"]
        orthogonal = "VERTICAL"
        negative_label, positive_label = "ABOVE", "BELOW"
    else:
        long_start = geometry["y"]
        long_end = geometry["y"] + geometry["height"]
        marker_cross_lo = geometry["x"]
        marker_cross_hi = geometry["x"] + geometry["width"]
        orthogonal = "HORIZONTAL"
        negative_label, positive_label = "LEFT", "RIGHT"

    long_span = max(1.0, long_end - long_start)
    long_margin = max(8.0, longitudinal_margin_fraction * long_span)
    long_lo = long_start - long_margin
    long_hi = long_end + long_margin

    track_by_id = {str(track["track_id"]): track for track in tracks}
    carrier_ids = sorted(str(value) for value in candidate.get("carrier_track_ids", []))
    carrier_tracks = [track_by_id[value] for value in carrier_ids if value in track_by_id]
    carrier_centers = sorted(float(track["centerline"]) for track in carrier_tracks)
    cross_lo = carrier_centers[0] if carrier_centers else marker_cross_lo
    cross_hi = carrier_centers[-1] if carrier_centers else marker_cross_hi
    cross_span = max(1.0, cross_hi - cross_lo)
    side_depth = max(minimum_side_depth_px, side_depth_cross_fraction * cross_span)

    primitive_negative: list[dict[str, Any]] = []
    primitive_positive: list[dict[str, Any]] = []
    for track in tracks:
        track_id = str(track.get("track_id", ""))
        if track_id in carrier_ids or str(track.get("orientation")) != orthogonal:
            continue
        long_position = float(track["centerline"])
        if not (long_lo <= long_position <= long_hi):
            continue
        cross_start = float(track["start"])
        cross_end = float(track["end"])
        reaches_negative = (
            cross_start <= cross_lo - 1.0
            and cross_end >= cross_lo - carrier_cross_tolerance_px
            and cross_end >= cross_lo - side_depth
        )
        reaches_positive = (
            cross_end >= cross_hi + 1.0
            and cross_start <= cross_hi + carrier_cross_tolerance_px
            and cross_start <= cross_hi + side_depth
        )
        if reaches_negative:
            primitive_negative.append(
                {"id": track_id, "centerline": long_position, "source": "G1_LINE_TRACKS"}
            )
        if reaches_positive:
            primitive_positive.append(
                {"id": track_id, "centerline": long_position, "source": "G1_LINE_TRACKS"}
            )

    negative_primitive_clusters = _cluster_positions(
        primitive_negative, dedupe_tolerance_px
    )
    positive_primitive_clusters = _cluster_positions(
        primitive_positive, dedupe_tolerance_px
    )
    primitive_negative_ids = sorted(
        cluster["members"][0]
        for cluster in negative_primitive_clusters
        if cluster["members"]
    )
    primitive_positive_ids = sorted(
        cluster["members"][0]
        for cluster in positive_primitive_clusters
        if cluster["members"]
    )

    raster_negative, raster_positive = _raster_cross_side_strokes(
        binary_ink,
        orientation=orientation,
        long_lo=long_lo,
        long_hi=long_hi,
        cross_lo=cross_lo,
        cross_hi=cross_hi,
        side_depth_px=side_depth,
        minimum_profile_fraction=raster_profile_fraction,
    )

    combined_negative = _cluster_positions(
        [
            {
                "id": cluster["members"][0] if cluster["members"] else None,
                "centerline": cluster["centerline"],
                "source": "G1_LINE_TRACKS",
            }
            for cluster in negative_primitive_clusters
        ]
        + [
            {"id": None, "centerline": stroke["centerline"], "source": "RASTER_LOCAL_PROFILE"}
            for stroke in raster_negative
        ],
        dedupe_tolerance_px,
    )
    combined_positive = _cluster_positions(
        [
            {
                "id": cluster["members"][0] if cluster["members"] else None,
                "centerline": cluster["centerline"],
                "source": "G1_LINE_TRACKS",
            }
            for cluster in positive_primitive_clusters
        ]
        + [
            {"id": None, "centerline": stroke["centerline"], "source": "RASTER_LOCAL_PROFILE"}
            for stroke in raster_positive
        ],
        dedupe_tolerance_px,
    )

    negative_centers = [float(cluster["centerline"]) for cluster in combined_negative]
    positive_centers = [float(cluster["centerline"]) for cluster in combined_positive]
    pair_tolerance = max(minimum_pair_alignment_px, pair_alignment_fraction * long_span)
    matched_pairs = _match_cross_side_centers(
        negative_centers, positive_centers, pair_tolerance
    )
    negative_count = len(negative_centers)
    positive_count = len(positive_centers)
    matched_count = len(matched_pairs)

    if negative_count >= 2 and positive_count >= 2 and matched_count >= 2:
        graphical_state = "RECT_PLUS_DOUBLE_TRANSVERSE_BAND"
    elif negative_count + positive_count > 0:
        graphical_state = "RECT_PLUS_PARTIAL_TRANSVERSE_TRACES"
    else:
        graphical_state = "RECT_ALONE_ON_CARRIER"

    evidence_sources: list[str] = []
    if negative_primitive_clusters or positive_primitive_clusters:
        evidence_sources.append("G1_LINE_TRACKS")
    if raster_negative or raster_positive:
        evidence_sources.append("RASTER_LOCAL_PROFILE")

    return {
        "graphical_state": graphical_state,
        "carrier_orientation": orientation,
        "side_reference": "CARRIER_CROSS_AXIS",
        "negative_side_label": negative_label,
        "positive_side_label": positive_label,
        "local_window_px": round(long_margin, 6),
        "cross_side_depth_px": round(side_depth, 6),
        "pair_alignment_tolerance_px": round(pair_tolerance, 6),
        "marker_edge_halo_px": 0.0,
        "negative_side_count": negative_count,
        "positive_side_count": positive_count,
        "negative_side_centers": [round(value, 6) for value in negative_centers],
        "positive_side_centers": [round(value, 6) for value in positive_centers],
        "matched_cross_side_pair_count": matched_count,
        "matched_cross_side_pairs": matched_pairs,
        "negative_pair_spacing_px": (
            None
            if len(negative_centers) < 2
            else round(abs(sorted(negative_centers)[1] - sorted(negative_centers)[0]), 6)
        ),
        "positive_pair_spacing_px": (
            None
            if len(positive_centers) < 2
            else round(abs(sorted(positive_centers)[1] - sorted(positive_centers)[0]), 6)
        ),
        "spacing_consistent": matched_count >= 2,
        "primitive_negative_track_ids": primitive_negative_ids,
        "primitive_positive_track_ids": primitive_positive_ids,
        "raster_negative_strokes": raster_negative,
        "raster_positive_strokes": raster_positive,
        "raster_marker_edge_bleed_strokes": [],
        "evidence_sources": evidence_sources,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }
