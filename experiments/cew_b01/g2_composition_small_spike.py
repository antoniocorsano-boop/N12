from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA_ID = "CEW_B01_G2_COMPOSITION_SMALL_SPIKE"
SCHEMA_VERSION = 1

CORE_EXCLUDE = {
    "TEXT_BLOCK",
    "DIMENSION_LINE_OR_TICK_CANDIDATE",
    "LEADER_OR_CALLOUT_CANDIDATE",
}
LINEISH = {"LINE_SEGMENT", "PARALLEL_LINE_PAIR"}
STRONG_RELATIONS = {"CONTAINS", "CONTAINED_BY", "OVERLAPS", "TOUCHING"}


def _canonical_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _geom(item: dict[str, Any]) -> dict[str, float]:
    return item["geometry"]


def _edges(item: dict[str, Any]) -> tuple[float, float, float, float]:
    g = _geom(item)
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

    ga = _geom(a)
    gb = _geom(b)
    acx, acy = ga["x"] + ga["width"] / 2.0, ga["y"] + ga["height"] / 2.0
    bcx, bcy = gb["x"] + gb["width"] / 2.0, gb["y"] + gb["height"] / 2.0
    if abs(acy - bcy) <= max(3.0, 0.08 * scale):
        result.append("ALIGNED_H")
    if abs(acx - bcx) <= max(3.0, 0.08 * scale):
        result.append("ALIGNED_V")

    oa = a.get("feature_signature", {}).get("orientation")
    ob = b.get("feature_signature", {}).get("orientation")
    if isinstance(oa, str) and isinstance(ob, str):
        if oa == ob:
            result.append("PARALLEL")
        elif {oa, ob} == {"HORIZONTAL", "VERTICAL"}:
            result.append("ORTHOGONAL")
    return tuple(result)


def _candidate(seed: dict[str, Any], primitives: list[dict[str, Any]], *, max_core_members: int) -> dict[str, Any]:
    sg = _geom(seed)
    scale = max(12.0, math.sqrt(sg["width"] * sg["height"]))
    radius = min(180.0, max(36.0, 2.5 * scale))
    nearby = [
        item for item in primitives
        if item["primitive_id"] != seed["primitive_id"] and _gap(seed, item) <= radius
    ]

    core = [seed]
    context: list[dict[str, Any]] = []
    for item in nearby:
        family = item["family"]
        ig = _geom(item)
        rel = set(_relations(seed, item, scale))
        strong = bool(rel & STRONG_RELATIONS)
        huge = max(ig["width"], ig["height"]) > 5.0 * max(sg["width"], sg["height"])
        if family in CORE_EXCLUDE or huge:
            context.append(item)
            continue
        if family in LINEISH:
            if strong and max(ig["width"], ig["height"]) <= 3.5 * max(sg["width"], sg["height"]):
                core.append(item)
            else:
                context.append(item)
            continue
        if strong or ("NEAR" in rel and max(ig["width"], ig["height"]) <= 2.5 * max(sg["width"], sg["height"])):
            core.append(item)
        else:
            context.append(item)

    core = sorted(
        {item["primitive_id"]: item for item in core}.values(),
        key=lambda item: (_gap(seed, item), item["primitive_id"]),
    )[:max_core_members]
    core_ids = {item["primitive_id"] for item in core}
    context = sorted(
        {item["primitive_id"]: item for item in context if item["primitive_id"] not in core_ids}.values(),
        key=lambda item: (_gap(seed, item), item["primitive_id"]),
    )[:20]

    relation_counts: collections.Counter[str] = collections.Counter()
    edges: list[dict[str, Any]] = []
    for index, first in enumerate(core):
        for second in core[index + 1:]:
            rel = _relations(first, second, scale)
            if rel:
                relation_counts.update(rel)
                edges.append({
                    "a": first["primitive_id"],
                    "b": second["primitive_id"],
                    "relations": list(rel),
                })

    family_counts = collections.Counter(item["family"] for item in core)
    xs = [_geom(item)["x"] for item in core]
    ys = [_geom(item)["y"] for item in core]
    x1s = [_geom(item)["x"] + _geom(item)["width"] for item in core]
    y1s = [_geom(item)["y"] + _geom(item)["height"] for item in core]
    bbox = {
        "x": min(xs),
        "y": min(ys),
        "width": max(x1s) - min(xs),
        "height": max(y1s) - min(ys),
    }
    short = max(1.0, min(bbox["width"], bbox["height"]))
    aspect_bin = round((max(bbox["width"], bbox["height"]) / short) * 2.0) / 2.0
    descriptor = {
        "core_count": len(core),
        "family_counts": dict(sorted(family_counts.items())),
        "aspect_bin": aspect_bin,
        "relation_counts": dict(sorted((key, min(value, 9)) for key, value in relation_counts.items() if value)),
    }
    identity = {
        "source_sha256": seed["source"]["sha256"],
        "page_index": seed["page_index"],
        "seed_primitive_id": seed["primitive_id"],
        "core_primitive_ids": sorted(core_ids),
        "descriptor": descriptor,
    }
    return {
        "candidate_id": "CEW-B01-SC-" + _canonical_hash(identity)[:24],
        "source": seed["source"],
        "page_index": seed["page_index"],
        "frame": seed["frame"],
        "seed_primitive_id": seed["primitive_id"],
        "core_bbox": bbox,
        "core_primitive_ids": [item["primitive_id"] for item in core],
        "context_primitive_ids": [item["primitive_id"] for item in context],
        "relations": edges,
        "neutral_composition_descriptor": descriptor,
        "review_state": "UNREVIEWED",
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }


def _similarity(first: dict[str, Any], second: dict[str, Any]) -> float:
    a = first["neutral_composition_descriptor"]
    b = second["neutral_composition_descriptor"]
    fa = collections.Counter(a["family_counts"])
    fb = collections.Counter(b["family_counts"])
    keys = set(fa) | set(fb)
    family_overlap = sum(min(fa[key], fb[key]) for key in keys) / max(
        1, sum(max(fa[key], fb[key]) for key in keys)
    )
    ra = set(a["relation_counts"])
    rb = set(b["relation_counts"])
    relation_jaccard = len(ra & rb) / max(1, len(ra | rb))
    aspect_delta = abs(float(a["aspect_bin"]) - float(b["aspect_bin"]))
    aspect_score = max(0.0, 1.0 - aspect_delta / 3.0)
    return round(0.6 * family_overlap + 0.3 * relation_jaccard + 0.1 * aspect_score, 3)


def run(primitive_path: Path, manifest_path: Path) -> dict[str, Any]:
    primitives = json.loads(primitive_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(primitives, list):
        raise ValueError("G2_COMPOSITION_SPIKE_REQUIRES_PRIMITIVE_LIST")
    by_id = {item["primitive_id"]: item for item in primitives}
    if len(by_id) != len(primitives):
        raise ValueError("G2_COMPOSITION_SPIKE_DUPLICATE_PRIMITIVE_ID")
    if len(primitives) != manifest["expected_primitive_count"]:
        raise ValueError("G2_COMPOSITION_SPIKE_PRIMITIVE_COUNT_MISMATCH")

    seeds = manifest["seed_primitive_ids"]
    missing = [seed for seed in seeds if seed not in by_id]
    if missing:
        raise ValueError("G2_COMPOSITION_SPIKE_SEED_NOT_FOUND:" + ",".join(missing))
    source_sha = manifest["source_sha256"]
    if any(by_id[seed]["source"]["sha256"] != source_sha for seed in seeds):
        raise ValueError("G2_COMPOSITION_SPIKE_SOURCE_MISMATCH")

    candidates = [
        _candidate(by_id[seed], primitives, max_core_members=manifest["max_core_members"])
        for seed in seeds
    ]
    pairs = []
    for index, first in enumerate(candidates):
        for second in candidates[index + 1:]:
            pairs.append({
                "a": first["candidate_id"],
                "b": second["candidate_id"],
                "similarity": _similarity(first, second),
            })

    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "experiment_only": True,
        "promotable": False,
        "source_sha256": source_sha,
        "primitive_count": len(primitives),
        "seed_count": len(seeds),
        "candidates": candidates,
        "pairwise_similarity": pairs,
        "authority": {
            "semantic_classification_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "g3_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primitive-census", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.primitive_census, args.manifest)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_count": len(result["candidates"]),
        "core_counts": [len(item["core_primitive_ids"]) for item in result["candidates"]],
        "authority": result["authority"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
