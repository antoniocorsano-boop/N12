from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any


_ORIENTATIONS = {"HORIZONTAL", "VERTICAL"}


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _source_sha(item: dict[str, Any]) -> str:
    source = item.get("source", {})
    return str(source.get("sha256", ""))


def _segment_projection(item: dict[str, Any]) -> tuple[str, float, float, float]:
    geometry = item["geometry"]
    orientation = str(item.get("feature_signature", {}).get("orientation", ""))
    if orientation == "HORIZONTAL":
        centerline = float(geometry["y"]) + float(geometry["height"]) / 2.0
        start = float(geometry["x"])
        end = float(geometry["x"]) + float(geometry["width"])
    elif orientation == "VERTICAL":
        centerline = float(geometry["x"]) + float(geometry["width"]) / 2.0
        start = float(geometry["y"])
        end = float(geometry["y"]) + float(geometry["height"])
    else:
        raise ValueError("HOSTED_MARKER_TRACK_REQUIRES_AXIS_ORIENTATION")
    return orientation, centerline, min(start, end), max(start, end)


def _interval_gap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(b_start - a_end, a_start - b_end, 0.0)


def build_line_tracks(
    primitives: list[dict[str, Any]],
    *,
    centerline_tolerance_px: float = 4.0,
    interval_gap_tolerance_px: float = 15.0,
) -> list[dict[str, Any]]:
    """Coalesce duplicate/fragmentary axis-aligned Hough observations.

    The function intentionally scans the complete supplied census. It has no
    positional member cap. Tracks are neutral geometric observations and retain
    every contributing G1 primitive ID.
    """

    eligible: list[dict[str, Any]] = []
    for primitive in primitives:
        if primitive.get("family") != "LINE_SEGMENT":
            continue
        orientation = primitive.get("feature_signature", {}).get("orientation")
        if orientation not in _ORIENTATIONS:
            continue
        projected = _segment_projection(primitive)
        eligible.append({
            "primitive": primitive,
            "orientation": projected[0],
            "centerline": projected[1],
            "start": projected[2],
            "end": projected[3],
        })

    grouped: dict[tuple[str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in eligible:
        primitive = item["primitive"]
        grouped[(
            _source_sha(primitive),
            int(primitive.get("page_index", 0)),
            str(primitive.get("frame", "")),
            item["orientation"],
        )].append(item)

    tracks: list[dict[str, Any]] = []
    for group_key in sorted(grouped):
        items = sorted(
            grouped[group_key],
            key=lambda item: (
                item["centerline"],
                item["start"],
                item["end"],
                str(item["primitive"]["primitive_id"]),
            ),
        )
        parent = list(range(len(items)))

        def find(index: int) -> int:
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                if ra < rb:
                    parent[rb] = ra
                else:
                    parent[ra] = rb

        for index, first in enumerate(items):
            for other_index in range(index + 1, len(items)):
                second = items[other_index]
                if second["centerline"] - first["centerline"] > centerline_tolerance_px:
                    break
                if abs(second["centerline"] - first["centerline"]) > centerline_tolerance_px:
                    continue
                if _interval_gap(first["start"], first["end"], second["start"], second["end"]) <= interval_gap_tolerance_px:
                    union(index, other_index)

        components: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for index, item in enumerate(items):
            components[find(index)].append(item)

        source_sha, page_index, frame, orientation = group_key
        for root in sorted(components):
            members = components[root]
            primitive_ids = sorted(str(member["primitive"]["primitive_id"]) for member in members)
            start = min(member["start"] for member in members)
            end = max(member["end"] for member in members)
            centerline = sum(member["centerline"] for member in members) / len(members)
            identity = {
                "source_sha256": source_sha,
                "page_index": page_index,
                "frame": frame,
                "orientation": orientation,
                "member_primitive_ids": primitive_ids,
            }
            tracks.append({
                "track_id": "CEW-B01-LT-" + _canonical_hash(identity)[:24],
                "source_sha256": source_sha,
                "page_index": page_index,
                "frame": frame,
                "orientation": orientation,
                "centerline": round(centerline, 6),
                "start": round(start, 6),
                "end": round(end, 6),
                "length": round(end - start, 6),
                "member_primitive_ids": primitive_ids,
            })

    return sorted(
        tracks,
        key=lambda track: (
            track["source_sha256"],
            track["page_index"],
            track["frame"],
            track["orientation"],
            track["centerline"],
            track["start"],
            track["end"],
            track["track_id"],
        ),
    )


def build_linear_carriers(
    tracks: list[dict[str, Any]],
    *,
    min_track_length_px: float = 200.0,
    min_separation_px: float = 8.0,
    min_overlap_fraction: float = 0.55,
    max_separation_to_overlap: float = 0.25,
) -> list[dict[str, Any]]:
    """Pair neutral, distinct parallel tracks into carrier candidates."""

    grouped: dict[tuple[str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for track in tracks:
        orientation = str(track.get("orientation", ""))
        if orientation not in _ORIENTATIONS:
            continue
        if float(track.get("length", 0.0)) < min_track_length_px:
            continue
        grouped[(
            str(track.get("source_sha256", "")),
            int(track.get("page_index", 0)),
            str(track.get("frame", "")),
            orientation,
        )].append(track)

    carriers: list[dict[str, Any]] = []
    for group_key in sorted(grouped):
        source_sha, page_index, frame, orientation = group_key
        items = sorted(
            grouped[group_key],
            key=lambda track: (
                float(track["centerline"]),
                float(track["start"]),
                float(track["end"]),
                str(track["track_id"]),
            ),
        )
        for index, first in enumerate(items):
            for second in items[index + 1 :]:
                separation = abs(float(second["centerline"]) - float(first["centerline"]))
                if separation < min_separation_px:
                    continue
                overlap_start = max(float(first["start"]), float(second["start"]))
                overlap_end = min(float(first["end"]), float(second["end"]))
                overlap_length = max(0.0, overlap_end - overlap_start)
                shorter = min(float(first["length"]), float(second["length"]))
                if shorter <= 0.0 or overlap_length <= 0.0:
                    continue
                if overlap_length / shorter < min_overlap_fraction:
                    continue
                if separation / overlap_length > max_separation_to_overlap:
                    continue

                track_ids = sorted([str(first["track_id"]), str(second["track_id"])])
                primitive_ids = sorted(set(first.get("member_primitive_ids", [])) | set(second.get("member_primitive_ids", [])))
                identity = {
                    "source_sha256": source_sha,
                    "page_index": page_index,
                    "frame": frame,
                    "orientation": orientation,
                    "track_ids": track_ids,
                }
                carriers.append({
                    "carrier_id": "CEW-B01-LC-" + _canonical_hash(identity)[:24],
                    "source_sha256": source_sha,
                    "page_index": page_index,
                    "frame": frame,
                    "orientation": orientation,
                    "track_ids": track_ids,
                    "member_primitive_ids": primitive_ids,
                    "separation": round(separation, 6),
                    "overlap_start": round(overlap_start, 6),
                    "overlap_end": round(overlap_end, 6),
                    "overlap_length": round(overlap_length, 6),
                    "track_centerlines": sorted([round(float(first["centerline"]), 6), round(float(second["centerline"]), 6)]),
                })

    return sorted(
        carriers,
        key=lambda carrier: (
            carrier["source_sha256"],
            carrier["page_index"],
            carrier["frame"],
            carrier["orientation"],
            carrier["overlap_start"],
            carrier["track_centerlines"],
            carrier["carrier_id"],
        ),
    )


def _marker_axes(marker: dict[str, Any], carrier_orientation: str) -> tuple[float, float, float, float]:
    geometry = marker["geometry"]
    x = float(geometry["x"])
    y = float(geometry["y"])
    width = float(geometry["width"])
    height = float(geometry["height"])
    if carrier_orientation == "HORIZONTAL":
        return x, x + width, y, y + height
    if carrier_orientation == "VERTICAL":
        return y, y + height, x, x + width
    raise ValueError("HOSTED_MARKER_INVALID_CARRIER_ORIENTATION")


def _same_scope(marker: dict[str, Any], carrier_or_track: dict[str, Any]) -> bool:
    return (
        _source_sha(marker) == str(carrier_or_track.get("source_sha256", ""))
        and int(marker.get("page_index", 0)) == int(carrier_or_track.get("page_index", 0))
        and str(marker.get("frame", "")) == str(carrier_or_track.get("frame", ""))
    )


def _distance_to_interval(value: float, start: float, end: float) -> float:
    if start <= value <= end:
        return 0.0
    return min(abs(value - start), abs(value - end))


def build_hosted_marker_candidates(
    primitives: list[dict[str, Any]],
    marker_seed_ids: list[str],
    *,
    carrier_cross_tolerance_px: float = 4.0,
    max_marker_to_carrier_overlap_fraction: float = 0.35,
    transverse_window_factor: float = 2.5,
    local_pair_edge_tolerance_px: float = 15.0,
    local_pair_edge_fraction: float = 0.25,
) -> list[dict[str, Any]]:
    """Bind frozen rectilinear markers to neutral carriers and describe local crossing tracks.

    The broad transverse window preserves contextual crossing tracks. Pair
    promotion is stricter: both tracks must lie locally at or near the marker
    footprint. This function emits graphical states only and deliberately does
    not encode beam identity, slab support, or any other technical meaning.
    """

    primitive_by_id = {str(item.get("primitive_id")): item for item in primitives}
    missing = sorted(set(marker_seed_ids) - set(primitive_by_id))
    if missing:
        raise ValueError("HOSTED_MARKER_SEED_MISSING:" + ",".join(missing))

    tracks = build_line_tracks(primitives)
    carriers = build_linear_carriers(tracks)
    results: list[dict[str, Any]] = []

    for marker_id in marker_seed_ids:
        marker = primitive_by_id[marker_id]
        if marker.get("family") != "RECTILINEAR_CLOSED_SHAPE":
            raise ValueError("HOSTED_MARKER_SEED_NOT_RECTILINEAR")

        bindings: list[tuple[tuple[float, float, float, str], dict[str, Any], tuple[float, float, float, float]]] = []
        for carrier in carriers:
            if not _same_scope(marker, carrier):
                continue
            long_start, long_end, cross_start, cross_end = _marker_axes(marker, str(carrier["orientation"]))
            long_span = max(0.0, long_end - long_start)
            long_center = (long_start + long_end) / 2.0
            band_lo, band_hi = sorted(float(value) for value in carrier["track_centerlines"])
            if cross_start < band_lo - carrier_cross_tolerance_px:
                continue
            if cross_end > band_hi + carrier_cross_tolerance_px:
                continue
            if long_center < float(carrier["overlap_start"]) or long_center > float(carrier["overlap_end"]):
                continue
            overlap_length = float(carrier["overlap_length"])
            if overlap_length <= 0.0 or long_span > max_marker_to_carrier_overlap_fraction * overlap_length:
                continue

            edge_fit_residual = abs(cross_start - band_lo) + abs(cross_end - band_hi)
            center_fit_residual = abs(((cross_start + cross_end) / 2.0) - ((band_lo + band_hi) / 2.0))
            score = (
                round(edge_fit_residual, 6),
                round(center_fit_residual, 6),
                -round(overlap_length, 6),
                str(carrier["carrier_id"]),
            )
            bindings.append((score, carrier, (long_start, long_end, cross_start, cross_end)))

        if not bindings:
            continue

        bindings.sort(key=lambda item: item[0])
        _score, carrier, marker_axes = bindings[0]
        long_start, long_end, _cross_start, _cross_end = marker_axes
        long_span = max(1.0, long_end - long_start)
        long_center = (long_start + long_end) / 2.0
        band_lo, band_hi = sorted(float(value) for value in carrier["track_centerlines"])
        orthogonal = "VERTICAL" if carrier["orientation"] == "HORIZONTAL" else "HORIZONTAL"
        window = transverse_window_factor * long_span

        qualifying_tracks: list[dict[str, Any]] = []
        for track in tracks:
            if str(track.get("orientation")) != orthogonal:
                continue
            if not _same_scope(marker, track):
                continue
            if float(track["start"]) > band_lo + carrier_cross_tolerance_px:
                continue
            if float(track["end"]) < band_hi - carrier_cross_tolerance_px:
                continue
            if abs(float(track["centerline"]) - long_center) > window:
                continue
            qualifying_tracks.append(track)

        qualifying_tracks = sorted(
            qualifying_tracks,
            key=lambda track: (
                abs(float(track["centerline"]) - long_center),
                str(track["track_id"]),
            ),
        )
        transverse_track_ids = [str(track["track_id"]) for track in qualifying_tracks]
        local_pair_tolerance = max(local_pair_edge_tolerance_px, local_pair_edge_fraction * long_span)
        local_pair_tracks = [
            track
            for track in qualifying_tracks
            if _distance_to_interval(float(track["centerline"]), long_start, long_end) <= local_pair_tolerance
        ]
        transverse_pair_track_ids = (
            [str(track["track_id"]) for track in local_pair_tracks[:2]]
            if len(local_pair_tracks) >= 2
            else []
        )
        transverse_primitive_ids = sorted({
            primitive_id
            for track in qualifying_tracks
            for primitive_id in track.get("member_primitive_ids", [])
        })
        graphical_state = (
            "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE"
            if len(transverse_pair_track_ids) == 2
            else "RECT_ALONE_ON_CARRIER"
        )
        identity = {
            "marker_primitive_id": marker_id,
            "carrier_id": carrier["carrier_id"],
            "transverse_track_ids": transverse_track_ids,
        }
        results.append({
            "hosted_marker_id": "CEW-B01-HM-" + _canonical_hash(identity)[:24],
            "marker_primitive_id": marker_id,
            "marker_geometry": dict(marker["geometry"]),
            "carrier_id": carrier["carrier_id"],
            "carrier_orientation": carrier["orientation"],
            "carrier_track_ids": list(carrier["track_ids"]),
            "carrier_primitive_ids": list(carrier["member_primitive_ids"]),
            "carrier_separation": carrier["separation"],
            "carrier_overlap_start": carrier["overlap_start"],
            "carrier_overlap_end": carrier["overlap_end"],
            "transverse_track_ids": transverse_track_ids,
            "transverse_pair_track_ids": transverse_pair_track_ids,
            "transverse_primitive_ids": transverse_primitive_ids,
            "graphical_state": graphical_state,
            "semantic_meaning": None,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "g3_authorized": False,
            "merge_authorized": False,
            "review_state": "UNREVIEWED",
        })

    return sorted(results, key=lambda item: (item["marker_primitive_id"], item["hosted_marker_id"]))
