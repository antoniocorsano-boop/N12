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
