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

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
R2_ROOT = ROOT / ".cew_raster_geometry_candidates"
R2_MANIFEST = R2_ROOT / "manifest.json"
R2M_ROOT = ROOT / ".cew_raster_geometry_consolidation"
R2M_MANIFEST = R2M_ROOT / "manifest.json"
R2T_MANIFEST = ROOT / ".cew_raster_geometry_topology/manifest.json"
ASSET_ROOT = ROOT / ".cew_raster_support_continuity"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
LINE_SAMPLE_STEP_PX = 4.0
MIN_LINE_SAMPLES = 16
MAX_LINE_SAMPLES = 256
ANGLE_TOLERANCE_DEG = 3.0
PERPENDICULAR_SEPARATION_NORM = 0.008
MAX_PROJECTED_GAP_NORM = 0.05


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2S_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def _distribution(values: list[float]) -> dict[str, float]:
    return {
        "min": round(min(values), 8) if values else 0.0,
        "p10": round(_quantile(values, 0.10), 8),
        "median": round(statistics.median(values), 8) if values else 0.0,
        "p90": round(_quantile(values, 0.90), 8),
        "max": round(max(values), 8) if values else 0.0,
    }


def _load_gray_png(path: Path) -> tuple[int, int, bytes]:
    pix = pymupdf.Pixmap(str(path))
    width, height, channels = int(pix.width), int(pix.height), int(pix.n)
    raw = bytes(pix.samples)
    if width <= 0 or height <= 0 or channels <= 0:
        raise AssertionError(f"R2S_INVALID_RASTER:{path}")
    expected = width * height * channels
    if len(raw) != expected:
        raise AssertionError(f"R2S_RASTER_SAMPLE_COUNT_MISMATCH:{path}:{len(raw)}:{expected}")
    if channels == 1:
        return width, height, raw
    gray = bytearray(width * height)
    if channels == 2:
        for idx in range(width * height):
            gray[idx] = raw[idx * 2]
    else:
        for idx in range(width * height):
            base = idx * channels
            r = raw[base]
            g = raw[base + 1]
            b = raw[base + 2]
            gray[idx] = (77 * r + 150 * g + 29 * b) >> 8
    return width, height, bytes(gray)


def _otsu_threshold(gray: bytes) -> int:
    hist = [0] * 256
    for value in gray:
        hist[value] += 1
    total = len(gray)
    if total == 0:
        raise AssertionError("R2S_EMPTY_RASTER")
    sum_total = sum(index * count for index, count in enumerate(hist))
    sum_background = 0.0
    weight_background = 0
    best_variance = -1.0
    best_threshold = 127
    for threshold in range(256):
        weight_background += hist[threshold]
        if weight_background == 0:
            continue
        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break
        sum_background += threshold * hist[threshold]
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        variance = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2
        if variance > best_variance:
            best_variance = variance
            best_threshold = threshold
    return int(best_threshold)


def _pixel(gray: bytes, width: int, height: int, x: float, y: float) -> int | None:
    ix, iy = int(round(x)), int(round(y))
    if ix < 0 or iy < 0 or ix >= width or iy >= height:
        return None
    return gray[iy * width + ix]


def _sample_support(
    a_norm: list[float],
    b_norm: list[float],
    width: int,
    height: int,
    gray: bytes,
    threshold: int,
    dpi: int,
) -> dict[str, Any]:
    ax, ay = float(a_norm[0]) * (width - 1), float(a_norm[1]) * (height - 1)
    bx, by = float(b_norm[0]) * (width - 1), float(b_norm[1]) * (height - 1)
    dx, dy = bx - ax, by - ay
    length_px = math.hypot(dx, dy)
    if length_px <= 1e-9:
        return {
            "sample_count": 0,
            "band_radius_px": 0,
            "support_fraction": 0.0,
            "longest_supported_run_fraction": 0.0,
            "mean_min_band_luma": 255.0,
        }
    ux, uy = dx / length_px, dy / length_px
    nx, ny = -uy, ux
    sample_count = min(MAX_LINE_SAMPLES, max(MIN_LINE_SAMPLES, int(math.ceil(length_px / LINE_SAMPLE_STEP_PX)) + 1))
    band_radius = max(1, int(round(dpi / 100.0)))
    supported: list[bool] = []
    min_luma: list[int] = []
    for index in range(sample_count):
        t = index / (sample_count - 1) if sample_count > 1 else 0.5
        px = ax + t * dx
        py = ay + t * dy
        values = []
        for offset in range(-band_radius, band_radius + 1):
            value = _pixel(gray, width, height, px + offset * nx, py + offset * ny)
            if value is not None:
                values.append(value)
        minimum = min(values) if values else 255
        min_luma.append(minimum)
        supported.append(minimum <= threshold)

    longest = 0
    current = 0
    for value in supported:
        if value:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    support_count = sum(1 for value in supported if value)
    return {
        "sample_count": sample_count,
        "band_radius_px": band_radius,
        "support_fraction": round(support_count / sample_count, 8),
        "longest_supported_run_fraction": round(longest / sample_count, 8),
        "mean_min_band_luma": round(sum(min_luma) / len(min_luma), 4) if min_luma else 255.0,
    }


def _direction(candidate: dict[str, Any]) -> tuple[float, float]:
    a = candidate["geometry_normalized"]["a"]
    b = candidate["geometry_normalized"]["b"]
    dx, dy = float(b[0]) - float(a[0]), float(b[1]) - float(a[1])
    length = math.hypot(dx, dy)
    if length <= 1e-12:
        raise AssertionError("R2S_ZERO_LENGTH_R2M_CANDIDATE")
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
    a = candidate["geometry_normalized"]["a"]
    b = candidate["geometry_normalized"]["b"]
    return (float(a[0]) + float(b[0])) / 2.0, (float(a[1]) + float(b[1])) / 2.0


def _point_line_distance(point: tuple[float, float], line: dict[str, Any]) -> float:
    a = line["geometry_normalized"]["a"]
    ux, uy = _direction(line)
    nx, ny = -uy, ux
    return abs((point[0] - float(a[0])) * nx + (point[1] - float(a[1])) * ny)


def _projection_interval(candidate: dict[str, Any], ux: float, uy: float) -> tuple[float, float]:
    values = []
    for key in ("a", "b"):
        point = candidate["geometry_normalized"][key]
        values.append(float(point[0]) * ux + float(point[1]) * uy)
    return min(values), max(values)


def _projected_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    reference = a
    ux, uy = _direction(reference)
    ia = _projection_interval(a, ux, uy)
    ib = _projection_interval(b, ux, uy)
    if ia[1] < ib[0]:
        return ib[0] - ia[1]
    if ib[1] < ia[0]:
        return ia[0] - ib[1]
    return 0.0


def _nearest_endpoints(a: dict[str, Any], b: dict[str, Any]) -> tuple[list[float], list[float], float]:
    candidates = []
    for ka in ("a", "b"):
        for kb in ("a", "b"):
            pa = [float(value) for value in a["geometry_normalized"][ka]]
            pb = [float(value) for value in b["geometry_normalized"][kb]]
            distance = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
            candidates.append((distance, pa, pb, ka, kb))
    distance, pa, pb, _, _ = min(candidates, key=lambda row: (row[0], row[3], row[4]))
    return pa, pb, distance


def _gap_eligible(a: dict[str, Any], b: dict[str, Any]) -> tuple[bool, float]:
    if _angle_diff(_angle(a), _angle(b)) > ANGLE_TOLERANCE_DEG:
        return False, 0.0
    if _point_line_distance(_midpoint(a), b) > PERPENDICULAR_SEPARATION_NORM:
        return False, 0.0
    if _point_line_distance(_midpoint(b), a) > PERPENDICULAR_SEPARATION_NORM:
        return False, 0.0
    gap = _projected_gap(a, b)
    if gap <= 1e-8 or gap > MAX_PROJECTED_GAP_NORM:
        return False, gap
    return True, gap


def _region_raster_inputs(r2_entry: dict[str, Any], r2_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    outputs = {}
    for dpi in (200, 300):
        key = str(dpi)
        crop_path = R2_ROOT / r2_entry[f"crop_{dpi}_filename"]
        expected_sha = r2_entry[f"crop_{dpi}_sha256"]
        if not crop_path.is_file() or _sha256(crop_path) != expected_sha:
            raise AssertionError(f"R2S_CROP_IDENTITY_FAILURE:{r2_entry['evidence_region_id']}:{dpi}")
        width, height, gray = _load_gray_png(crop_path)
        metadata = r2_result["crops"][key]
        if abs(width - int(metadata["width_px"])) > 1 or abs(height - int(metadata["height_px"])) > 1:
            raise AssertionError(
                f"R2S_CROP_DIMENSION_MISMATCH:{r2_entry['evidence_region_id']}:{dpi}:{width}x{height}:"
                f"{metadata['width_px']}x{metadata['height_px']}"
            )
        threshold = _otsu_threshold(gray)
        outputs[key] = {
            "dpi": dpi,
            "path": crop_path,
            "sha256": expected_sha,
            "width_px": width,
            "height_px": height,
            "gray": gray,
            "otsu_threshold": threshold,
        }
    return outputs


def build() -> dict[str, Any]:
    revision = _revision()
    r2 = _load(R2_MANIFEST)
    r2m = _load(R2M_MANIFEST)
    r2t = _load(R2T_MANIFEST)
    for name, artifact in (("R2", r2), ("R2M", r2m), ("R2T", r2t)):
        if artifact.get("build_revision") != revision:
            raise AssertionError(f"R2S_{name}_REVISION_MISMATCH")
    if r2m.get("support_retention") != "100%" or r2m.get("input_candidate_total") != 230:
        raise AssertionError("R2S_REQUIRES_R2M_FULL_SUPPORT_RETENTION")
    if r2t.get("decision_state") != "TOPOLOGY_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED":
        raise AssertionError("R2S_REQUIRES_R2T_COMPLETE")
    if any(artifact.get("r2c_scene_adapter_authorized") is not False for artifact in (r2, r2m, r2t)):
        raise AssertionError("R2S_REQUIRES_R2C_BLOCKED")

    r2_entries = {row["evidence_region_id"]: row for row in r2["region_entries"]}
    r2m_entries = {row["evidence_region_id"]: row for row in r2m["regions"]}
    if set(r2_entries) != EXPECTED_REGIONS or set(r2m_entries) != EXPECTED_REGIONS:
        raise AssertionError("R2S_REGION_COVERAGE_MISMATCH")

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    regions = []
    line_total = 0
    gap_total = 0

    for region_id in sorted(EXPECTED_REGIONS):
        r2_entry = r2_entries[region_id]
        r2_result = _load(R2_ROOT / r2_entry["result_filename"])
        r2m_result = _load(R2M_ROOT / r2m_entries[region_id]["result_filename"])
        raster = _region_raster_inputs(r2_entry, r2_result)
        candidates = r2m_result["consolidated_candidates"]
        line_support = []
        support_values = []
        run_values = []

        for candidate in candidates:
            scales = {}
            for dpi in (200, 300):
                image = raster[str(dpi)]
                scales[str(dpi)] = _sample_support(
                    candidate["geometry_normalized"]["a"],
                    candidate["geometry_normalized"]["b"],
                    image["width_px"],
                    image["height_px"],
                    image["gray"],
                    image["otsu_threshold"],
                    dpi,
                )
            cross_support = min(scales["200"]["support_fraction"], scales["300"]["support_fraction"])
            cross_run = min(
                scales["200"]["longest_supported_run_fraction"],
                scales["300"]["longest_supported_run_fraction"],
            )
            support_values.append(cross_support)
            run_values.append(cross_run)
            line_support.append({
                "consolidated_candidate_id": candidate["consolidated_candidate_id"],
                "support_candidate_ids": candidate["support_candidate_ids"],
                "support_count": candidate["support_count"],
                "scale_200": scales["200"],
                "scale_300": scales["300"],
                "cross_scale_min_support_fraction": round(cross_support, 8),
                "cross_scale_min_longest_run_fraction": round(cross_run, 8),
                "diagnostic_only": True,
                "scene_materialization_authorized": False,
            })

        gap_hypotheses = []
        gap_support_values = []
        gap_run_values = []
        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                eligible, projected_gap = _gap_eligible(candidates[i], candidates[j])
                if not eligible:
                    continue
                bridge_a, bridge_b, endpoint_distance = _nearest_endpoints(candidates[i], candidates[j])
                scales = {}
                for dpi in (200, 300):
                    image = raster[str(dpi)]
                    scales[str(dpi)] = _sample_support(
                        bridge_a,
                        bridge_b,
                        image["width_px"],
                        image["height_px"],
                        image["gray"],
                        image["otsu_threshold"],
                        dpi,
                    )
                cross_support = min(scales["200"]["support_fraction"], scales["300"]["support_fraction"])
                cross_run = min(
                    scales["200"]["longest_supported_run_fraction"],
                    scales["300"]["longest_supported_run_fraction"],
                )
                pair_ids = sorted([
                    candidates[i]["consolidated_candidate_id"],
                    candidates[j]["consolidated_candidate_id"],
                ])
                gap_id = "RGH-" + hashlib.sha256("|".join(pair_ids).encode("utf-8")).hexdigest()[:20]
                gap_support_values.append(cross_support)
                gap_run_values.append(cross_run)
                gap_hypotheses.append({
                    "gap_hypothesis_id": gap_id,
                    "candidate_ids": pair_ids,
                    "projected_gap_norm": round(projected_gap, 8),
                    "nearest_endpoint_distance_norm": round(endpoint_distance, 8),
                    "bridge_endpoints_normalized": {"a": bridge_a, "b": bridge_b},
                    "scale_200": scales["200"],
                    "scale_300": scales["300"],
                    "cross_scale_min_support_fraction": round(cross_support, 8),
                    "cross_scale_min_longest_run_fraction": round(cross_run, 8),
                    "hypothesis_only": True,
                    "geometry_materialization_authorized": False,
                    "technical_identity_authorized": False,
                    "structural_identity_authorized": False,
                })

        region_payload = {
            "schema_version": "1.0",
            "evidence_region_id": region_id,
            "source_code": r2m_result["source_code"],
            "source_version_id": r2m_result["source_version_id"],
            "source_sha256": r2m_result["source_sha256"],
            "page_id": r2m_result["page_id"],
            "transform_id": r2m_result["transform_id"],
            "raster_inputs": {
                key: {
                    "dpi": value["dpi"],
                    "sha256": value["sha256"],
                    "width_px": value["width_px"],
                    "height_px": value["height_px"],
                    "otsu_threshold": value["otsu_threshold"],
                }
                for key, value in raster.items()
            },
            "line_count": len(candidates),
            "line_support": line_support,
            "line_cross_scale_support_distribution": _distribution(support_values),
            "line_cross_scale_longest_run_distribution": _distribution(run_values),
            "gap_hypothesis_count": len(gap_hypotheses),
            "gap_hypotheses": gap_hypotheses,
            "gap_cross_scale_support_distribution": _distribution(gap_support_values),
            "gap_cross_scale_longest_run_distribution": _distribution(gap_run_values),
            "ocr_used": False,
            "raster_support_is_technical_identity": False,
            "gap_hypothesis_is_geometry": False,
            "r2c_scene_adapter_authorized": False,
            "technical_identity_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
        region_path = ASSET_ROOT / f"{region_id}.json"
        region_path.write_text(json.dumps(region_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        regions.append({
            "evidence_region_id": region_id,
            "result_filename": region_path.name,
            "result_sha256": _sha256(region_path),
            "line_count": len(candidates),
            "gap_hypothesis_count": len(gap_hypotheses),
            "line_cross_scale_support_distribution": region_payload["line_cross_scale_support_distribution"],
            "line_cross_scale_longest_run_distribution": region_payload["line_cross_scale_longest_run_distribution"],
            "gap_cross_scale_support_distribution": region_payload["gap_cross_scale_support_distribution"],
            "gap_cross_scale_longest_run_distribution": region_payload["gap_cross_scale_longest_run_distribution"],
            "otsu_threshold_200": raster["200"]["otsu_threshold"],
            "otsu_threshold_300": raster["300"]["otsu_threshold"],
        })
        line_total += len(candidates)
        gap_total += len(gap_hypotheses)

    manifest = {
        "schema_version": "1.0",
        "diagnostic_contract": "CEW_PWB005_R2S_RASTER_SUPPORT_CONTINUITY_v1",
        "build_revision": revision,
        "region_coverage": "4/4",
        "line_total": line_total,
        "gap_hypothesis_total": gap_total,
        "sampling": {
            "line_sample_step_px": LINE_SAMPLE_STEP_PX,
            "min_line_samples": MIN_LINE_SAMPLES,
            "max_line_samples": MAX_LINE_SAMPLES,
            "gap_angle_tolerance_deg": ANGLE_TOLERANCE_DEG,
            "gap_perpendicular_separation_norm": PERPENDICULAR_SEPARATION_NORM,
            "max_projected_gap_norm": MAX_PROJECTED_GAP_NORM,
            "threshold_method": "OTSU_PER_EXACT_RASTER_CROP",
        },
        "regions": regions,
        "decision_state": "RASTER_SUPPORT_DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED",
        "ocr_used": False,
        "raster_support_is_technical_identity": False,
        "gap_hypothesis_is_geometry": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2S_RASTER_SUPPORT_CONTINUITY_BUILD = PASS")
    print("REGION_COVERAGE = 4/4")
    print("LINE_TOTAL = " + str(line_total))
    print("GAP_HYPOTHESIS_TOTAL = " + str(gap_total))
    for row in regions:
        print(
            "R2S_REGION",
            row["evidence_region_id"],
            "lines=" + str(row["line_count"]),
            "line_support_med=" + str(row["line_cross_scale_support_distribution"]["median"]),
            "line_run_med=" + str(row["line_cross_scale_longest_run_distribution"]["median"]),
            "gaps=" + str(row["gap_hypothesis_count"]),
            "gap_support_med=" + str(row["gap_cross_scale_support_distribution"]["median"]),
            "gap_run_med=" + str(row["gap_cross_scale_longest_run_distribution"]["median"]),
            "otsu200=" + str(row["otsu_threshold_200"]),
            "otsu300=" + str(row["otsu_threshold_300"]),
        )
    print("OCR_USED = false")
    print("RASTER_SUPPORT_IS_TECHNICAL_IDENTITY = false")
    print("GAP_HYPOTHESIS_IS_GEOMETRY = false")
    print("R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


if __name__ == "__main__":
    build()
