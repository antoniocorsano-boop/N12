#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R2_ROOT = ROOT / ".cew_raster_geometry_candidates"
R2_MANIFEST = R2_ROOT / "manifest.json"
R2Q_MANIFEST = ROOT / ".cew_raster_geometry_quality/manifest.json"
ASSET_ROOT = ROOT / ".cew_raster_geometry_consolidation"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
ANGLE_TOLERANCE_DEG = 2.0
PERPENDICULAR_SEPARATION_NORM = 0.006
PROJECTED_GAP_NORM = 0.012
ENDPOINT_GRID_NORM = 0.01


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _stable_id(prefix: str, parts: list[str]) -> str:
    raw = "|".join(parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def _point(candidate: dict[str, Any], key: str) -> tuple[float, float]:
    value = candidate["geometry_normalized"][key]
    return float(value[0]), float(value[1])


def _length(candidate: dict[str, Any]) -> float:
    a = _point(candidate, "a")
    b = _point(candidate, "b")
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _direction(candidate: dict[str, Any]) -> tuple[float, float]:
    a = _point(candidate, "a")
    b = _point(candidate, "b")
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = math.hypot(dx, dy)
    if length <= 1e-12:
        raise AssertionError(f"R2M_ZERO_LENGTH_SUPPORT:{candidate.get('candidate_id')}")
    ux, uy = dx / length, dy / length
    if ux < -1e-12 or (abs(ux) <= 1e-12 and uy < 0):
        ux, uy = -ux, -uy
    return ux, uy


def _angle(candidate: dict[str, Any]) -> float:
    ux, uy = _direction(candidate)
    return math.degrees(math.atan2(uy, ux)) % 180.0


def _angle_diff(a: float, b: float) -> float:
    value = abs(a - b) % 180.0
    return min(value, 180.0 - value)


def _midpoint(candidate: dict[str, Any]) -> tuple[float, float]:
    a = _point(candidate, "a")
    b = _point(candidate, "b")
    return (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0


def _point_line_distance(point: tuple[float, float], line: dict[str, Any]) -> float:
    a = _point(line, "a")
    ux, uy = _direction(line)
    nx, ny = -uy, ux
    return abs((point[0] - a[0]) * nx + (point[1] - a[1]) * ny)


def _projection_interval(candidate: dict[str, Any], ux: float, uy: float) -> tuple[float, float]:
    values = []
    for key in ("a", "b"):
        x, y = _point(candidate, key)
        values.append(x * ux + y * uy)
    return min(values), max(values)


def _interval_gap(a: tuple[float, float], b: tuple[float, float]) -> float:
    if a[1] < b[0]:
        return b[0] - a[1]
    if b[1] < a[0]:
        return a[0] - b[1]
    return 0.0


def _compatible(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if _angle_diff(_angle(a), _angle(b)) > ANGLE_TOLERANCE_DEG:
        return False
    if _point_line_distance(_midpoint(a), b) > PERPENDICULAR_SEPARATION_NORM:
        return False
    if _point_line_distance(_midpoint(b), a) > PERPENDICULAR_SEPARATION_NORM:
        return False
    reference = a if (_length(a), a["candidate_id"]) >= (_length(b), b["candidate_id"]) else b
    ux, uy = _direction(reference)
    if _interval_gap(_projection_interval(a, ux, uy), _projection_interval(b, ux, uy)) > PROJECTED_GAP_NORM:
        return False
    return True


def _group_candidates(candidates: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    ordered = sorted(candidates, key=lambda row: (-_length(row), row["candidate_id"]))
    groups: list[list[dict[str, Any]]] = []
    for candidate in ordered:
        placed = False
        for group in groups:
            if all(_compatible(candidate, member) for member in group):
                group.append(candidate)
                placed = True
                break
        if not placed:
            groups.append([candidate])
    for group in groups:
        group.sort(key=lambda row: row["candidate_id"])
    groups.sort(key=lambda group: tuple(row["candidate_id"] for row in group))
    return groups


def _source_point(normalized: tuple[float, float], source_rect: list[float]) -> list[float]:
    x0, y0, x1, y1 = [float(value) for value in source_rect]
    return [
        round(x0 + normalized[0] * (x1 - x0), 6),
        round(y0 + normalized[1] * (y1 - y0), 6),
    ]


def _consolidated_geometry(group: list[dict[str, Any]]) -> tuple[list[float], list[float]]:
    reference = sorted(group, key=lambda row: (-_length(row), row["candidate_id"]))[0]
    ux, uy = _direction(reference)
    nx, ny = -uy, ux

    projected_endpoints: list[tuple[float, tuple[float, float]]] = []
    weighted_normal = 0.0
    total_weight = 0.0
    for candidate in group:
        length = _length(candidate)
        mx, my = _midpoint(candidate)
        weighted_normal += (mx * nx + my * ny) * length
        total_weight += length
        for key in ("a", "b"):
            point = _point(candidate, key)
            projected_endpoints.append((point[0] * ux + point[1] * uy, point))

    if total_weight <= 1e-12:
        raise AssertionError("R2M_ZERO_TOTAL_SUPPORT_LENGTH")
    normal_offset = weighted_normal / total_weight
    t_min = min(item[0] for item in projected_endpoints)
    t_max = max(item[0] for item in projected_endpoints)
    a = (t_min * ux + normal_offset * nx, t_min * uy + normal_offset * ny)
    b = (t_max * ux + normal_offset * nx, t_max * uy + normal_offset * ny)

    epsilon = 0.002
    for point in (a, b):
        if not (-epsilon <= point[0] <= 1.0 + epsilon and -epsilon <= point[1] <= 1.0 + epsilon):
            raise AssertionError(f"R2M_CONSOLIDATED_GEOMETRY_OUTSIDE_REGION:{point}")
    a = (min(1.0, max(0.0, a[0])), min(1.0, max(0.0, a[1])))
    b = (min(1.0, max(0.0, b[0])), min(1.0, max(0.0, b[1])))
    if b < a:
        a, b = b, a
    return [round(a[0], 8), round(a[1], 8)], [round(b[0], 8), round(b[1], 8)]


def _make_consolidated(group: list[dict[str, Any]], region: dict[str, Any]) -> dict[str, Any]:
    support_ids = sorted(row["candidate_id"] for row in group)
    a, b = _consolidated_geometry(group)
    source_rect = region["source_rect_pt"]
    return {
        "consolidated_candidate_id": _stable_id("RGM", support_ids),
        "object_family": "RasterGeometryConsolidatedCandidate",
        "geometry_type": "LINE",
        "coordinate_space": "EVIDENCE_REGION_NORMALIZED_0_1",
        "geometry_normalized": {"a": a, "b": b},
        "geometry_source_page_pt": {
            "a": _source_point((a[0], a[1]), source_rect),
            "b": _source_point((b[0], b[1]), source_rect),
        },
        "support_candidate_ids": support_ids,
        "support_count": len(support_ids),
        "consolidation_state": "MULTI_SUPPORT_GEOMETRIC_GROUP" if len(support_ids) > 1 else "SINGLETON_PRESERVED",
        "semantic_classification": "UNASSIGNED",
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "scene_materialization_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def _candidate_angle(candidate: dict[str, Any]) -> float:
    a = candidate["geometry_normalized"]["a"]
    b = candidate["geometry_normalized"]["b"]
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def _endpoint_cell(point: list[float]) -> tuple[int, int]:
    return int(round(point[0] / ENDPOINT_GRID_NORM)), int(round(point[1] / ENDPOINT_GRID_NORM))


def _diagnostics(consolidated: list[dict[str, Any]], input_count: int) -> dict[str, Any]:
    occupancy: dict[tuple[int, int], int] = {}
    horizontal = vertical = oblique = 0
    for candidate in consolidated:
        for key in ("a", "b"):
            cell = _endpoint_cell(candidate["geometry_normalized"][key])
            occupancy[cell] = occupancy.get(cell, 0) + 1
        angle = _candidate_angle(candidate)
        if min(angle, 180.0 - angle) <= 5.0:
            horizontal += 1
        elif abs(angle - 90.0) <= 5.0:
            vertical += 1
        else:
            oblique += 1
    total_endpoints = len(consolidated) * 2
    connected = sum(value for value in occupancy.values() if value >= 2)
    multi = sum(1 for row in consolidated if row["support_count"] > 1)
    singleton = len(consolidated) - multi
    return {
        "input_candidate_count": input_count,
        "consolidated_candidate_count": len(consolidated),
        "reduction_ratio": round(1.0 - (len(consolidated) / input_count), 8) if input_count else 0.0,
        "multi_support_group_count": multi,
        "singleton_count": singleton,
        "max_support_count": max((row["support_count"] for row in consolidated), default=0),
        "support_id_count": sum(row["support_count"] for row in consolidated),
        "endpoint_connectivity": {
            "grid_norm": ENDPOINT_GRID_NORM,
            "occupied_cell_count": len(occupancy),
            "connected_endpoint_fraction": round(connected / total_endpoints, 8) if total_endpoints else 0.0,
        },
        "orientation": {
            "horizontal_count": horizontal,
            "vertical_count": vertical,
            "oblique_count": oblique,
        },
    }


def _svg(candidates: list[dict[str, Any]], path: Path) -> None:
    lines = []
    for row in candidates:
        a = row["geometry_normalized"]["a"]
        b = row["geometry_normalized"]["b"]
        lines.append(f'<line x1="{a[0]*1000:.3f}" y1="{a[1]*1000:.3f}" x2="{b[0]*1000:.3f}" y2="{b[1]*1000:.3f}" />')
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">\n'
        '  <g fill="none" stroke="currentColor" stroke-width="1">\n    '
        + '\n    '.join(lines)
        + '\n  </g>\n</svg>\n',
        encoding="utf-8",
    )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2M_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict[str, Any]:
    revision = _revision()
    r2 = _load_json(R2_MANIFEST)
    r2q = _load_json(R2Q_MANIFEST)
    if r2.get("build_revision") != revision or r2q.get("build_revision") != revision:
        raise AssertionError("R2M_INPUT_REVISION_MISMATCH")
    if r2.get("r2c_scene_adapter_authorized") is not False or r2q.get("r2c_scene_adapter_authorized") is not False:
        raise AssertionError("R2M_REQUIRES_R2C_BLOCKED")
    if r2q.get("decision_state") != "QUALITY_DIAGNOSTIC_COMPLETE":
        raise AssertionError("R2M_REQUIRES_R2Q_COMPLETE")

    entries = {row["evidence_region_id"]: row for row in r2.get("region_entries", [])}
    if set(entries) != EXPECTED_REGIONS:
        raise AssertionError("R2M_REGION_COVERAGE_MISMATCH")

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    region_results: list[dict[str, Any]] = []
    global_input_support: set[str] = set()
    global_output_support: list[str] = []

    for region_id in sorted(EXPECTED_REGIONS):
        entry = entries[region_id]
        result_path = R2_ROOT / entry["result_filename"]
        if _sha256(result_path) != entry["result_sha256"]:
            raise AssertionError(f"R2M_R2_RESULT_SHA_MISMATCH:{region_id}")
        result = _load_json(result_path)
        candidates = result.get("stable_candidates") or []
        if len(candidates) != int(entry["stable_candidate_count"]):
            raise AssertionError(f"R2M_R2_COUNT_MISMATCH:{region_id}")
        input_ids = [row["candidate_id"] for row in candidates]
        if len(input_ids) != len(set(input_ids)):
            raise AssertionError(f"R2M_DUPLICATE_R2_SUPPORT_ID:{region_id}")
        global_input_support.update(input_ids)

        groups = _group_candidates(candidates)
        consolidated = [_make_consolidated(group, result) for group in groups]
        output_ids = [support_id for row in consolidated for support_id in row["support_candidate_ids"]]
        if sorted(output_ids) != sorted(input_ids):
            raise AssertionError(f"R2M_SUPPORT_RETENTION_FAILURE:{region_id}")
        if len(output_ids) != len(set(output_ids)):
            raise AssertionError(f"R2M_SUPPORT_ASSIGNED_MORE_THAN_ONCE:{region_id}")
        global_output_support.extend(output_ids)

        region_dir = ASSET_ROOT / region_id
        region_dir.mkdir(parents=True, exist_ok=True)
        preview_path = region_dir / "consolidated_candidates.svg"
        _svg(consolidated, preview_path)
        diagnostics = _diagnostics(consolidated, len(candidates))
        region_payload = {
            "schema_version": "1.0",
            "evidence_region_id": region_id,
            "source_code": result["source_code"],
            "source_version_id": result["source_version_id"],
            "source_sha256": result["source_sha256"],
            "page_id": result["page_id"],
            "transform_id": result["transform_id"],
            "source_rect_pt": result["source_rect_pt"],
            "r2_artifact_contract": r2["artifact_contract"],
            "consolidation_rule": {
                "angle_tolerance_deg": ANGLE_TOLERANCE_DEG,
                "perpendicular_separation_norm": PERPENDICULAR_SEPARATION_NORM,
                "projected_gap_norm": PROJECTED_GAP_NORM,
                "grouping": "DETERMINISTIC_COMPLETE_LINK",
            },
            "diagnostics": diagnostics,
            "consolidated_candidates": consolidated,
            "preview_filename": str(preview_path.relative_to(ASSET_ROOT)),
            "preview_sha256": _sha256(preview_path),
            "support_retention": "100%",
            "r2c_scene_adapter_authorized": False,
            "technical_identity_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
        result_file = region_dir / "result.json"
        result_file.write_text(json.dumps(region_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        region_results.append({
            "evidence_region_id": region_id,
            "result_filename": str(result_file.relative_to(ASSET_ROOT)),
            "result_sha256": _sha256(result_file),
            "preview_filename": region_payload["preview_filename"],
            "preview_sha256": region_payload["preview_sha256"],
            **diagnostics,
        })

    if sorted(global_output_support) != sorted(global_input_support):
        raise AssertionError("R2M_GLOBAL_SUPPORT_RETENTION_FAILURE")
    if len(global_output_support) != len(set(global_output_support)):
        raise AssertionError("R2M_GLOBAL_SUPPORT_DUPLICATION")

    total_input = sum(row["input_candidate_count"] for row in region_results)
    total_output = sum(row["consolidated_candidate_count"] for row in region_results)
    manifest = {
        "schema_version": "1.0",
        "artifact_contract": "CEW_PWB005_R2M_RASTER_GEOMETRY_CONSOLIDATION_v1",
        "build_revision": revision,
        "r2_build_revision": r2["build_revision"],
        "r2q_build_revision": r2q["build_revision"],
        "region_coverage": "4/4",
        "input_candidate_total": total_input,
        "consolidated_candidate_total": total_output,
        "global_reduction_ratio": round(1.0 - total_output / total_input, 8) if total_input else 0.0,
        "support_id_total": len(global_output_support),
        "support_retention": "100%",
        "one_r2_candidate_to_one_r2m_group": True,
        "regions": region_results,
        "decision_state": "CONSOLIDATION_COMPLETE_REVIEW_REQUIRED",
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2M_RASTER_GEOMETRY_CONSOLIDATION_BUILD = PASS")
    print("REGION_COVERAGE = 4/4")
    print("INPUT_CANDIDATE_TOTAL = " + str(total_input))
    print("CONSOLIDATED_CANDIDATE_TOTAL = " + str(total_output))
    print("GLOBAL_REDUCTION_RATIO = " + str(manifest["global_reduction_ratio"]))
    print("SUPPORT_RETENTION = 100%")
    for row in region_results:
        print(
            "R2M_REGION",
            row["evidence_region_id"],
            "input=" + str(row["input_candidate_count"]),
            "output=" + str(row["consolidated_candidate_count"]),
            "reduction=" + str(row["reduction_ratio"]),
            "multi=" + str(row["multi_support_group_count"]),
            "singleton=" + str(row["singleton_count"]),
            "max_support=" + str(row["max_support_count"]),
            "connected=" + str(row["endpoint_connectivity"]["connected_endpoint_fraction"]),
        )
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


if __name__ == "__main__":
    build()
