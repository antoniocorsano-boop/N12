from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from .g2a0_observation_bundles import bundle_observations

CORE_EXCLUDE = {"TEXT_BLOCK", "DIMENSION_LINE_OR_TICK_CANDIDATE", "LEADER_OR_CALLOUT_CANDIDATE"}
LINEISH = {"LINE_SEGMENT", "PARALLEL_LINE_PAIR"}


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _edges(item: dict[str, Any]) -> tuple[float, float, float, float]:
    g = item["geometry"]
    return g["x"], g["y"], g["x"] + g["width"], g["y"] + g["height"]


def _gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    ax0, ay0, ax1, ay1 = _edges(a)
    bx0, by0, bx1, by1 = _edges(b)
    dx = max(bx0 - ax1, ax0 - bx1, 0.0)
    dy = max(by0 - ay1, ay0 - by1, 0.0)
    return math.hypot(dx, dy)


def _overlap_area(a: dict[str, Any], b: dict[str, Any]) -> float:
    ax0, ay0, ax1, ay1 = _edges(a)
    bx0, by0, bx1, by1 = _edges(b)
    return max(0.0, min(ax1, bx1) - max(ax0, bx0)) * max(0.0, min(ay1, by1) - max(ay0, by0))


def _contains(a: dict[str, Any], b: dict[str, Any]) -> bool:
    ax0, ay0, ax1, ay1 = _edges(a)
    bx0, by0, bx1, by1 = _edges(b)
    return ax0 <= bx0 and ay0 <= by0 and ax1 >= bx1 and ay1 >= by1


def _relations(a: dict[str, Any], b: dict[str, Any], scale: float) -> tuple[str, ...]:
    result: list[str] = []
    if _contains(a, b):
        result.append("CONTAINS")
    elif _contains(b, a):
        result.append("CONTAINED_BY")
    gap = _gap(a, b)
    if _overlap_area(a, b) > 0:
        result.append("OVERLAPS")
    elif gap <= 2.0:
        result.append("TOUCHING")
    elif gap <= max(5.0, 0.12 * scale):
        result.append("NEAR")
    ga, gb = a["geometry"], b["geometry"]
    acx, acy = ga["x"] + ga["width"] / 2.0, ga["y"] + ga["height"] / 2.0
    bcx, bcy = gb["x"] + gb["width"] / 2.0, gb["y"] + gb["height"] / 2.0
    if abs(acy - bcy) <= max(3.0, 0.08 * scale):
        result.append("ALIGNED_H")
    if abs(acx - bcx) <= max(3.0, 0.08 * scale):
        result.append("ALIGNED_V")
    return tuple(result)


def _expanded_ids(bundles: list[dict[str, Any]]) -> list[str]:
    return sorted({pid for bundle in bundles for pid in bundle["member_primitive_ids"]})


def build_bundled_candidates(
    primitives: list[dict[str, Any]],
    seed_primitive_ids: list[str],
    *,
    max_core_members: int,
) -> list[dict[str, Any]]:
    bundles, membership = bundle_observations(primitives)
    by_bundle = {bundle["bundle_id"]: bundle for bundle in bundles}
    missing = [seed for seed in seed_primitive_ids if seed not in membership]
    if missing:
        raise ValueError("G2A0_SEED_NOT_FOUND:" + ",".join(missing))

    candidates: list[dict[str, Any]] = []
    for seed_primitive_id in seed_primitive_ids:
        seed_bundle = by_bundle[membership[seed_primitive_id]]
        sg = seed_bundle["geometry"]
        scale = max(12.0, math.sqrt(sg["width"] * sg["height"]))
        radius = min(180.0, max(36.0, 2.5 * scale))
        nearby = [
            bundle for bundle in bundles
            if bundle["bundle_id"] != seed_bundle["bundle_id"] and _gap(seed_bundle, bundle) <= radius
        ]

        core = [seed_bundle]
        context: list[dict[str, Any]] = []
        for bundle in nearby:
            families = set(bundle["families"])
            bg = bundle["geometry"]
            rel = set(_relations(seed_bundle, bundle, scale))
            strong = bool(rel & {"CONTAINS", "CONTAINED_BY", "OVERLAPS", "TOUCHING"})
            huge = max(bg["width"], bg["height"]) > 5.0 * max(sg["width"], sg["height"])
            if families & CORE_EXCLUDE or huge:
                context.append(bundle)
                continue
            if families and families.issubset(LINEISH):
                if strong and max(bg["width"], bg["height"]) <= 3.5 * max(sg["width"], sg["height"]):
                    core.append(bundle)
                else:
                    context.append(bundle)
                continue
            if strong or ("NEAR" in rel and max(bg["width"], bg["height"]) <= 2.5 * max(sg["width"], sg["height"])):
                core.append(bundle)
            else:
                context.append(bundle)

        core = sorted(
            {bundle["bundle_id"]: bundle for bundle in core}.values(),
            key=lambda bundle: (_gap(seed_bundle, bundle), bundle["bundle_id"]),
        )[:max_core_members]
        core_ids = {bundle["bundle_id"] for bundle in core}
        context = sorted(
            {bundle["bundle_id"]: bundle for bundle in context if bundle["bundle_id"] not in core_ids}.values(),
            key=lambda bundle: (_gap(seed_bundle, bundle), bundle["bundle_id"]),
        )[:20]

        edges: list[dict[str, Any]] = []
        for index, first in enumerate(core):
            for second in core[index + 1:]:
                rel = _relations(first, second, scale)
                if rel:
                    edges.append({"a": first["bundle_id"], "b": second["bundle_id"], "relations": list(rel)})

        expanded = _expanded_ids(core)
        identity = {
            "source_sha256": seed_bundle["source"]["sha256"],
            "page_index": seed_bundle["page_index"],
            "seed_primitive_id": seed_primitive_id,
            "core_bundle_ids": sorted(core_ids),
            "core_primitive_ids_expanded": expanded,
        }
        candidates.append({
            "candidate_id": "CEW-B01-SCB-" + _canonical_hash(identity)[:24],
            "source": seed_bundle["source"],
            "page_index": seed_bundle["page_index"],
            "frame": seed_bundle["frame"],
            "seed_primitive_id": seed_primitive_id,
            "seed_bundle_id": seed_bundle["bundle_id"],
            "core_bundle_count": len(core),
            "core_bundle_ids": [bundle["bundle_id"] for bundle in core],
            "core_primitive_ids_expanded": expanded,
            "context_bundle_ids": [bundle["bundle_id"] for bundle in context],
            "context_primitive_ids_expanded": _expanded_ids(context),
            "core_bundles": core,
            "relations": edges,
            "review_state": "UNREVIEWED",
            "semantic_meaning": None,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
        })
    return candidates
