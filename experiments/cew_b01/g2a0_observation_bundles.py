from __future__ import annotations

import hashlib
import json
import math
from typing import Any

_LOCAL_EVENT_FAMILIES = {
    "INTERSECTION",
    "T_JUNCTION",
    "LINE_ENDPOINT",
    "L_SHAPED_MOTIF",
    "T_SHAPED_MOTIF",
    "CROSS_MOTIF",
}
_SAME_FAMILY_COALESCE = {
    "PARALLEL_LINE_PAIR",
}


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _geometry(item: dict[str, Any]) -> dict[str, float]:
    return item["geometry"]


def _edges(item: dict[str, Any]) -> tuple[float, float, float, float]:
    g = _geometry(item)
    return g["x"], g["y"], g["x"] + g["width"], g["y"] + g["height"]


def _area(item: dict[str, Any]) -> float:
    g = _geometry(item)
    return max(0.0, g["width"] * g["height"])


def _intersection_area(a: dict[str, Any], b: dict[str, Any]) -> float:
    ax0, ay0, ax1, ay1 = _edges(a)
    bx0, by0, bx1, by1 = _edges(b)
    return max(0.0, min(ax1, bx1) - max(ax0, bx0)) * max(0.0, min(ay1, by1) - max(ay0, by0))


def _center(item: dict[str, Any]) -> tuple[float, float]:
    g = _geometry(item)
    return g["x"] + g["width"] / 2.0, g["y"] + g["height"] / 2.0


def _strongly_coincident(a: dict[str, Any], b: dict[str, Any]) -> bool:
    inter = _intersection_area(a, b)
    smaller = min(_area(a), _area(b))
    if smaller <= 0 or inter / smaller < 0.65:
        return False
    acx, acy = _center(a)
    bcx, bcy = _center(b)
    ga = _geometry(a)
    gb = _geometry(b)
    compact_scale = max(1.0, min(max(ga["width"], ga["height"]), max(gb["width"], gb["height"])))
    return math.hypot(acx - bcx, acy - bcy) <= max(3.0, 0.45 * compact_scale)


def _compatible(a: dict[str, Any], b: dict[str, Any]) -> bool:
    fa = a["family"]
    fb = b["family"]
    if fa in _LOCAL_EVENT_FAMILIES and fb in _LOCAL_EVENT_FAMILIES:
        return True
    if fa == fb and fa in _SAME_FAMILY_COALESCE:
        oa = a.get("feature_signature", {}).get("orientation")
        ob = b.get("feature_signature", {}).get("orientation")
        return oa == ob
    return False


def _can_union(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a["source"]["sha256"] != b["source"]["sha256"]:
        return False
    if a["page_index"] != b["page_index"] or a["frame"] != b["frame"]:
        return False
    return _compatible(a, b) and _strongly_coincident(a, b)


def _bundle_for(members: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(members, key=lambda item: item["primitive_id"])
    first = ordered[0]
    xs = [_geometry(item)["x"] for item in ordered]
    ys = [_geometry(item)["y"] for item in ordered]
    x1s = [_geometry(item)["x"] + _geometry(item)["width"] for item in ordered]
    y1s = [_geometry(item)["y"] + _geometry(item)["height"] for item in ordered]
    bbox = {
        "x": min(xs),
        "y": min(ys),
        "width": max(x1s) - min(xs),
        "height": max(y1s) - min(ys),
    }
    member_ids = [item["primitive_id"] for item in ordered]
    identity = {
        "source_sha256": first["source"]["sha256"],
        "page_index": first["page_index"],
        "frame": first["frame"],
        "member_primitive_ids": member_ids,
    }
    return {
        "bundle_id": "CEW-B01-OB-" + _canonical_hash(identity)[:24],
        "source": first["source"],
        "page_index": first["page_index"],
        "frame": first["frame"],
        "geometry": bbox,
        "member_primitive_ids": member_ids,
        "families": sorted({item["family"] for item in ordered}),
        "detectors": sorted({item["detector"] for item in ordered}),
        "members": [
            {
                "primitive_id": item["primitive_id"],
                "family": item["family"],
                "detector": item["detector"],
                "geometry": dict(item["geometry"]),
                "feature_signature": dict(item.get("feature_signature", {})),
            }
            for item in ordered
        ],
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }


def bundle_observations(primitives: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    ordered = sorted(primitives, key=lambda item: item["primitive_id"])
    if len({item["primitive_id"] for item in ordered}) != len(ordered):
        raise ValueError("G2A0_DUPLICATE_PRIMITIVE_ID")

    parent = list(range(len(ordered)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if ra < rb:
            parent[rb] = ra
        else:
            parent[ra] = rb

    for index, first in enumerate(ordered):
        for offset, second in enumerate(ordered[index + 1 :], start=index + 1):
            if _can_union(first, second):
                union(index, offset)

    grouped: dict[int, list[dict[str, Any]]] = {}
    for index, item in enumerate(ordered):
        grouped.setdefault(find(index), []).append(item)

    bundles = [_bundle_for(grouped[root]) for root in sorted(grouped)]
    bundles.sort(key=lambda item: item["bundle_id"])
    membership = {
        primitive_id: bundle["bundle_id"]
        for bundle in bundles
        for primitive_id in bundle["member_primitive_ids"]
    }
    return bundles, dict(sorted(membership.items()))
