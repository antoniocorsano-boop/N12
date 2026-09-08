#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import statistics
import subprocess
from pathlib import Path
from typing import Any

import build_cew_raster_geometry_consolidation as r2m_builder

ROOT = Path(__file__).resolve().parents[1]
R2_ROOT = ROOT / ".cew_raster_geometry_candidates"
R2_MANIFEST = R2_ROOT / "manifest.json"
R2Q_MANIFEST = ROOT / ".cew_raster_geometry_quality/manifest.json"
R2M_ROOT = ROOT / ".cew_raster_geometry_consolidation"
R2M_MANIFEST = R2M_ROOT / "manifest.json"
ASSET_ROOT = ROOT / ".cew_raster_geometry_topology"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
TOUCH_TOLERANCE_NORM = 0.004
INTERSECTION_EPS = 1e-9


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2T_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    w = pos - lo
    return ordered[lo] * (1.0 - w) + ordered[hi] * w


def _point(candidate: dict[str, Any], key: str) -> tuple[float, float]:
    value = candidate["geometry_normalized"][key]
    return float(value[0]), float(value[1])


def _cross(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: tuple[float, float], b: tuple[float, float], p: tuple[float, float]) -> bool:
    if abs(_cross(a, b, p)) > INTERSECTION_EPS:
        return False
    return (
        min(a[0], b[0]) - INTERSECTION_EPS <= p[0] <= max(a[0], b[0]) + INTERSECTION_EPS
        and min(a[1], b[1]) - INTERSECTION_EPS <= p[1] <= max(a[1], b[1]) + INTERSECTION_EPS
    )


def _segments_intersect(a: dict[str, Any], b: dict[str, Any]) -> bool:
    p1, p2 = _point(a, "a"), _point(a, "b")
    q1, q2 = _point(b, "a"), _point(b, "b")
    c1 = _cross(p1, p2, q1)
    c2 = _cross(p1, p2, q2)
    c3 = _cross(q1, q2, p1)
    c4 = _cross(q1, q2, p2)
    if ((c1 > INTERSECTION_EPS and c2 < -INTERSECTION_EPS) or (c1 < -INTERSECTION_EPS and c2 > INTERSECTION_EPS)) and (
        (c3 > INTERSECTION_EPS and c4 < -INTERSECTION_EPS) or (c3 < -INTERSECTION_EPS and c4 > INTERSECTION_EPS)
    ):
        return True
    return (
        _on_segment(p1, p2, q1)
        or _on_segment(p1, p2, q2)
        or _on_segment(q1, q2, p1)
        or _on_segment(q1, q2, p2)
    )


def _point_segment_distance(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    denom = dx * dx + dy * dy
    if denom <= 1e-18:
        return math.hypot(point[0] - a[0], point[1] - a[1])
    t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / denom
    t = min(1.0, max(0.0, t))
    projection = (a[0] + t * dx, a[1] + t * dy)
    return math.hypot(point[0] - projection[0], point[1] - projection[1])


def _segment_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    if _segments_intersect(a, b):
        return 0.0
    a1, a2 = _point(a, "a"), _point(a, "b")
    b1, b2 = _point(b, "a"), _point(b, "b")
    return min(
        _point_segment_distance(a1, b1, b2),
        _point_segment_distance(a2, b1, b2),
        _point_segment_distance(b1, a1, a2),
        _point_segment_distance(b2, a1, a2),
    )


def _components(adjacency: list[set[int]]) -> list[list[int]]:
    seen: set[int] = set()
    result: list[list[int]] = []
    for start in range(len(adjacency)):
        if start in seen:
            continue
        stack = [start]
        component: list[int] = []
        seen.add(start)
        while stack:
            current = stack.pop()
            component.append(current)
            for nxt in sorted(adjacency[current]):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        result.append(sorted(component))
    result.sort(key=lambda row: (-len(row), row))
    return result


def _r2_stability_map(r2: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for entry in r2["region_entries"]:
        result = _load(R2_ROOT / entry["result_filename"])
        for candidate in result.get("stable_candidates") or []:
            candidate_id = candidate["candidate_id"]
            if candidate_id in scores:
                raise AssertionError(f"R2T_DUPLICATE_R2_CANDIDATE_ID:{candidate_id}")
            scores[candidate_id] = float(candidate["support"]["stability_score"])
    return scores


def _topology_for_region(result: dict[str, Any], stability_map: dict[str, float]) -> dict[str, Any]:
    candidates = result["consolidated_candidates"]
    count = len(candidates)
    adjacency: list[set[int]] = [set() for _ in range(count)]
    exact_pairs = 0
    near_pairs = 0
    residual_compatible_pairs = 0

    adapted = [
        {
            "candidate_id": row["consolidated_candidate_id"],
            "geometry_normalized": row["geometry_normalized"],
        }
        for row in candidates
    ]

    for i in range(count):
        for j in range(i + 1, count):
            intersects = _segments_intersect(candidates[i], candidates[j])
            distance = 0.0 if intersects else _segment_distance(candidates[i], candidates[j])
            if intersects:
                exact_pairs += 1
                adjacency[i].add(j)
                adjacency[j].add(i)
            elif distance <= TOUCH_TOLERANCE_NORM:
                near_pairs += 1
                adjacency[i].add(j)
                adjacency[j].add(i)
            if r2m_builder._compatible(adapted[i], adapted[j]):
                residual_compatible_pairs += 1

    components = _components(adjacency)
    degrees = [len(row) for row in adjacency]
    isolated = sum(1 for degree in degrees if degree == 0)
    largest = len(components[0]) if components else 0

    group_stability_medians: list[float] = []
    support_scores: list[float] = []
    support_ids_seen: list[str] = []
    for candidate in candidates:
        group_scores = []
        for support_id in candidate["support_candidate_ids"]:
            if support_id not in stability_map:
                raise AssertionError(f"R2T_UNKNOWN_R2_SUPPORT:{support_id}")
            score = stability_map[support_id]
            group_scores.append(score)
            support_scores.append(score)
            support_ids_seen.append(support_id)
        group_stability_medians.append(statistics.median(group_scores))

    return {
        "evidence_region_id": result["evidence_region_id"],
        "source_code": result["source_code"],
        "source_version_id": result["source_version_id"],
        "source_sha256": result["source_sha256"],
        "page_id": result["page_id"],
        "transform_id": result["transform_id"],
        "consolidated_candidate_count": count,
        "exact_intersection_pair_count": exact_pairs,
        "near_contact_pair_count": near_pairs,
        "graph_edge_count": sum(degrees) // 2,
        "connected_component_count": len(components),
        "largest_component_size": largest,
        "largest_component_fraction": round(largest / count, 8) if count else 0.0,
        "isolated_candidate_count": isolated,
        "isolated_candidate_fraction": round(isolated / count, 8) if count else 0.0,
        "mean_graph_degree": round(sum(degrees) / count, 8) if count else 0.0,
        "max_graph_degree": max(degrees, default=0),
        "residual_r2m_compatible_pair_count": residual_compatible_pairs,
        "support_stability": {
            "support_count": len(support_scores),
            "min": round(min(support_scores), 8) if support_scores else 0.0,
            "p10": round(_quantile(support_scores, 0.10), 8),
            "median": round(statistics.median(support_scores), 8) if support_scores else 0.0,
            "group_median_p10": round(_quantile(group_stability_medians, 0.10), 8),
            "group_median_median": round(statistics.median(group_stability_medians), 8) if group_stability_medians else 0.0,
        },
        "support_candidate_ids": sorted(support_ids_seen),
        "topology_role": "GEOMETRIC_DIAGNOSTIC_ONLY",
        "structural_node_interpretation_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def build() -> dict[str, Any]:
    revision = _revision()
    r2 = _load(R2_MANIFEST)
    r2q = _load(R2Q_MANIFEST)
    r2m = _load(R2M_MANIFEST)
    for name, artifact in (("R2", r2), ("R2Q", r2q), ("R2M", r2m)):
        if artifact.get("build_revision") != revision:
            raise AssertionError(f"R2T_{name}_REVISION_MISMATCH")
    if r2m.get("decision_state") != "CONSOLIDATION_COMPLETE_REVIEW_REQUIRED":
        raise AssertionError("R2T_REQUIRES_R2M_COMPLETE")
    if r2m.get("support_retention") != "100%":
        raise AssertionError("R2T_REQUIRES_FULL_R2_SUPPORT")
    if any(artifact.get("r2c_scene_adapter_authorized") is not False for artifact in (r2, r2q, r2m)):
        raise AssertionError("R2T_REQUIRES_R2C_BLOCKED")

    stability_map = _r2_stability_map(r2)
    r2m_entries = {row["evidence_region_id"]: row for row in r2m["regions"]}
    if set(r2m_entries) != EXPECTED_REGIONS:
        raise AssertionError("R2T_REGION_COVERAGE_MISMATCH")

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    regions: list[dict[str, Any]] = []
    global_support: list[str] = []
    for region_id in sorted(EXPECTED_REGIONS):
        entry = r2m_entries[region_id]
        result = _load(R2M_ROOT / entry["result_filename"])
        metrics = _topology_for_region(result, stability_map)
        global_support.extend(metrics["support_candidate_ids"])
        region_path = ASSET_ROOT / f"{region_id}.json"
        region_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        metrics["result_filename"] = region_path.name
        regions.append(metrics)

    if len(global_support) != 230 or len(set(global_support)) != 230:
        raise AssertionError("R2T_GLOBAL_SUPPORT_COVERAGE_FAILURE")

    manifest = {
        "schema_version": "1.0",
        "diagnostic_contract": "CEW_PWB005_R2T_TOPOLOGY_COHERENCE_v1",
        "build_revision": revision,
        "region_coverage": "4/4",
        "touch_tolerance_norm": TOUCH_TOLERANCE_NORM,
        "input_consolidated_candidate_total": r2m["consolidated_candidate_total"],
        "r2_support_total": len(global_support),
        "regions": regions,
        "decision_state": "TOPOLOGY_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED",
        "topology_authority": "NONE",
        "structural_node_interpretation_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2T_TOPOLOGY_COHERENCE_BUILD = PASS")
    print("REGION_COVERAGE = 4/4")
    print("CONSOLIDATED_CANDIDATE_TOTAL = " + str(manifest["input_consolidated_candidate_total"]))
    print("R2_SUPPORT_TOTAL = 230")
    for row in regions:
        print(
            "R2T_REGION",
            row["evidence_region_id"],
            "lines=" + str(row["consolidated_candidate_count"]),
            "exact=" + str(row["exact_intersection_pair_count"]),
            "near=" + str(row["near_contact_pair_count"]),
            "components=" + str(row["connected_component_count"]),
            "largest=" + str(row["largest_component_fraction"]),
            "isolated=" + str(row["isolated_candidate_fraction"]),
            "degree_mean=" + str(row["mean_graph_degree"]),
            "residual=" + str(row["residual_r2m_compatible_pair_count"]),
            "stability=" + str(row["support_stability"]["median"]),
        )
    print("R2T_DIAGNOSTIC_AUTHORITY = NONE")
    print("STRUCTURAL_NODE_INTERPRETATION_AUTHORIZED = false")
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


if __name__ == "__main__":
    build()
