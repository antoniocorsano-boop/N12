#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R2_ROOT = ROOT / ".cew_raster_geometry_candidates"
R2_MANIFEST = R2_ROOT / "manifest.json"
ASSET_ROOT = ROOT / ".cew_raster_geometry_quality"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
AXIS_TOLERANCE_DEG = 5.0
DUPLICATE_ANGLE_TOLERANCE_DEG = 1.5
DUPLICATE_ENDPOINT_ERROR_NORM = 0.008
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
    weight = pos - lo
    return ordered[lo] * (1.0 - weight) + ordered[hi] * weight


def _angle_diff(a: float, b: float) -> float:
    value = abs(a - b) % 180.0
    return min(value, 180.0 - value)


def _line_angle(candidate: dict[str, Any]) -> float:
    a = candidate["geometry_normalized"]["a"]
    b = candidate["geometry_normalized"]["b"]
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def _line_length(candidate: dict[str, Any]) -> float:
    a = candidate["geometry_normalized"]["a"]
    b = candidate["geometry_normalized"]["b"]
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _endpoint_error(a: dict[str, Any], b: dict[str, Any]) -> float:
    a1 = a["geometry_normalized"]["a"]
    a2 = a["geometry_normalized"]["b"]
    b1 = b["geometry_normalized"]["a"]
    b2 = b["geometry_normalized"]["b"]
    direct = (math.hypot(a1[0] - b1[0], a1[1] - b1[1]) + math.hypot(a2[0] - b2[0], a2[1] - b2[1])) / 2.0
    reverse = (math.hypot(a1[0] - b2[0], a1[1] - b2[1]) + math.hypot(a2[0] - b1[0], a2[1] - b1[1])) / 2.0
    return min(direct, reverse)


def _endpoint_cell(point: list[float]) -> tuple[int, int]:
    return (
        int(round(point[0] / ENDPOINT_GRID_NORM)),
        int(round(point[1] / ENDPOINT_GRID_NORM)),
    )


def _load_region_result(relative_path: str, expected_sha: str) -> dict[str, Any]:
    path = R2_ROOT / relative_path
    if not path.is_file():
        raise AssertionError(f"R2Q_REGION_RESULT_MISSING:{relative_path}")
    if _sha256(path) != expected_sha:
        raise AssertionError(f"R2Q_REGION_RESULT_SHA_MISMATCH:{relative_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _region_metrics(entry: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    candidates = result.get("stable_candidates") or []
    lengths = [_line_length(row) for row in candidates]
    angles = [_line_angle(row) for row in candidates]
    stability = [float(row["support"]["stability_score"]) for row in candidates]

    horizontal = sum(1 for angle in angles if min(angle, 180.0 - angle) <= AXIS_TOLERANCE_DEG)
    vertical = sum(1 for angle in angles if abs(angle - 90.0) <= AXIS_TOLERANCE_DEG)
    oblique = len(angles) - horizontal - vertical

    duplicate_pairs = 0
    duplicate_members: set[int] = set()
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            if _angle_diff(angles[i], angles[j]) > DUPLICATE_ANGLE_TOLERANCE_DEG:
                continue
            if _endpoint_error(candidates[i], candidates[j]) <= DUPLICATE_ENDPOINT_ERROR_NORM:
                duplicate_pairs += 1
                duplicate_members.add(i)
                duplicate_members.add(j)

    occupancy: dict[tuple[int, int], int] = {}
    candidate_cells: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for candidate in candidates:
        a = _endpoint_cell(candidate["geometry_normalized"]["a"])
        b = _endpoint_cell(candidate["geometry_normalized"]["b"])
        occupancy[a] = occupancy.get(a, 0) + 1
        occupancy[b] = occupancy.get(b, 0) + 1
        candidate_cells.append((a, b))

    connected_endpoint_count = sum(count for count in occupancy.values() if count >= 2)
    total_endpoints = len(candidates) * 2
    junction_cells = sum(1 for count in occupancy.values() if count >= 3)

    raw200 = int(entry["raw_line_count_200"])
    raw300 = int(entry["raw_line_count_300"])
    stable_count = len(candidates)

    return {
        "evidence_region_id": entry["evidence_region_id"],
        "source_code": entry["source_code"],
        "source_version_id": entry["source_version_id"],
        "source_sha256": entry["source_sha256"],
        "page_id": entry["page_id"],
        "transform_id": entry["transform_id"],
        "stable_candidate_count": stable_count,
        "raw_line_count_200": raw200,
        "raw_line_count_300": raw300,
        "stable_to_raw_200_ratio": round(stable_count / raw200, 8) if raw200 else 0.0,
        "stable_to_raw_300_ratio": round(stable_count / raw300, 8) if raw300 else 0.0,
        "total_normalized_line_length": round(sum(lengths), 8),
        "length_norm": {
            "min": round(min(lengths), 8) if lengths else 0.0,
            "median": round(statistics.median(lengths), 8) if lengths else 0.0,
            "p90": round(_quantile(lengths, 0.90), 8),
            "max": round(max(lengths), 8) if lengths else 0.0,
        },
        "orientation": {
            "axis_tolerance_deg": AXIS_TOLERANCE_DEG,
            "horizontal_count": horizontal,
            "vertical_count": vertical,
            "oblique_count": oblique,
            "horizontal_fraction": round(horizontal / stable_count, 8) if stable_count else 0.0,
            "vertical_fraction": round(vertical / stable_count, 8) if stable_count else 0.0,
            "oblique_fraction": round(oblique / stable_count, 8) if stable_count else 0.0,
        },
        "stability_score": {
            "min": round(min(stability), 8) if stability else 0.0,
            "p10": round(_quantile(stability, 0.10), 8),
            "median": round(statistics.median(stability), 8) if stability else 0.0,
        },
        "near_duplicates": {
            "angle_tolerance_deg": DUPLICATE_ANGLE_TOLERANCE_DEG,
            "endpoint_error_tolerance_norm": DUPLICATE_ENDPOINT_ERROR_NORM,
            "pair_count": duplicate_pairs,
            "member_count": len(duplicate_members),
            "member_fraction": round(len(duplicate_members) / stable_count, 8) if stable_count else 0.0,
        },
        "endpoint_connectivity": {
            "grid_norm": ENDPOINT_GRID_NORM,
            "occupied_cell_count": len(occupancy),
            "connected_endpoint_count": connected_endpoint_count,
            "connected_endpoint_fraction": round(connected_endpoint_count / total_endpoints, 8) if total_endpoints else 0.0,
            "junction_cell_count": junction_cells,
        },
        "quality_state": "QUALITY_DIAGNOSTIC_COMPLETE" if stable_count else "NO_CANDIDATES",
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def build() -> dict[str, Any]:
    if not R2_MANIFEST.is_file():
        raise AssertionError("R2Q_REQUIRES_R2_MANIFEST_ON_SAME_BUILD")
    r2 = json.loads(R2_MANIFEST.read_text(encoding="utf-8"))
    revision = _revision()
    if r2.get("build_revision") != revision:
        raise AssertionError(f"R2Q_R2_REVISION_MISMATCH:{r2.get('build_revision')}:{revision}")
    if r2.get("artifact_contract") != "CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1":
        raise AssertionError("R2Q_R2_CONTRACT_MISMATCH")
    if r2.get("r2c_scene_adapter_authorized") is not False:
        raise AssertionError("R2Q_REQUIRES_R2C_BLOCKED")
    entries = r2.get("region_entries") or []
    if {row.get("evidence_region_id") for row in entries} != EXPECTED_REGIONS:
        raise AssertionError("R2Q_REGION_COVERAGE_MISMATCH")

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    regions: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda row: row["evidence_region_id"]):
        result = _load_region_result(entry["result_filename"], entry["result_sha256"])
        if result.get("evidence_region_id") != entry["evidence_region_id"]:
            raise AssertionError("R2Q_RESULT_IDENTITY_MISMATCH")
        regions.append(_region_metrics(entry, result))

    manifest = {
        "schema_version": "1.0",
        "diagnostic_contract": "CEW_PWB005_R2Q_RASTER_GEOMETRY_QUALITY_v1",
        "build_revision": revision,
        "r2_build_revision": r2["build_revision"],
        "r2_artifact_contract": r2["artifact_contract"],
        "region_coverage": "4/4",
        "stable_candidate_total": sum(row["stable_candidate_count"] for row in regions),
        "regions": regions,
        "decision_state": "QUALITY_DIAGNOSTIC_COMPLETE",
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2Q_RASTER_GEOMETRY_QUALITY_BUILD = PASS")
    print("REGION_COVERAGE = 4/4")
    print("STABLE_CANDIDATE_TOTAL = " + str(manifest["stable_candidate_total"]))
    for row in regions:
        print(
            "R2Q_REGION",
            row["evidence_region_id"],
            "stable=" + str(row["stable_candidate_count"]),
            "median_len=" + str(row["length_norm"]["median"]),
            "p90_len=" + str(row["length_norm"]["p90"]),
            "axis_h=" + str(row["orientation"]["horizontal_count"]),
            "axis_v=" + str(row["orientation"]["vertical_count"]),
            "oblique=" + str(row["orientation"]["oblique_count"]),
            "dup_members=" + str(row["near_duplicates"]["member_count"]),
            "connected=" + str(row["endpoint_connectivity"]["connected_endpoint_fraction"]),
            "stability_med=" + str(row["stability_score"]["median"]),
        )
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


if __name__ == "__main__":
    build()
