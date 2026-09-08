#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np

ANGLE_TOLERANCE_DEG = 2.0
ENDPOINT_TOLERANCE_NORM = 0.01
RELATIVE_LENGTH_TOLERANCE = 0.08
MIDPOINT_BUCKET_NORM = 0.02
ANGLE_BUCKET_DEG = 5.0
MAX_MATCHING_LINES_PER_SCALE = 4000


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def _angle_diff(a: float, b: float) -> float:
    value = abs(a - b) % 180.0
    return min(value, 180.0 - value)


def _canonical_line(x1: float, y1: float, x2: float, y2: float, width: int, height: int, line_id: str) -> dict[str, Any]:
    p1 = (x1 / width, y1 / height)
    p2 = (x2 / width, y2 / height)
    if p2 < p1:
        p1, p2 = p2, p1
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx)) % 180.0
    return {
        "line_id": line_id,
        "a": [round(p1[0], 8), round(p1[1], 8)],
        "b": [round(p2[0], 8), round(p2[1], 8)],
        "midpoint": [round((p1[0] + p2[0]) / 2.0, 8), round((p1[1] + p2[1]) / 2.0, 8)],
        "length_norm": round(length, 8),
        "angle_deg": round(angle, 6),
    }


def _extract_lines(path: Path, dpi: int) -> dict[str, Any]:
    gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise AssertionError(f"cannot read raster crop: {path}")
    height, width = gray.shape[:2]
    if width <= 0 or height <= 0:
        raise AssertionError(f"zero-sized raster crop: {path}")

    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    otsu_threshold, _ = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    low = max(20, int(0.50 * otsu_threshold))
    high = max(low + 1, min(255, int(1.25 * otsu_threshold)))
    edges = cv2.Canny(blur, low, high, apertureSize=3, L2gradient=True)

    diagonal = math.hypot(width, height)
    min_line_length = max(40, int(round(diagonal * 0.015)))
    max_line_gap = max(4, int(round(diagonal * 0.002)))
    hough_threshold = max(35, int(round(min(width, height) * 0.015)))

    detected = cv2.HoughLinesP(
        edges,
        rho=1.0,
        theta=np.pi / 360.0,
        threshold=hough_threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap,
    )

    lines: list[dict[str, Any]] = []
    if detected is not None:
        for index, item in enumerate(detected[:, 0, :].tolist()):
            x1, y1, x2, y2 = [float(value) for value in item]
            lines.append(_canonical_line(x1, y1, x2, y2, width, height, f"L{dpi}-{index:06d}"))

    # Matching is bounded deterministically by normalized length, not by detector
    # return order. All raw detections remain counted and the bound is explicit.
    lines.sort(key=lambda row: (-row["length_norm"], row["a"], row["b"], row["line_id"]))
    matching_lines = lines[:MAX_MATCHING_LINES_PER_SCALE]

    edge_ratio = float(np.count_nonzero(edges)) / float(edges.size)
    return {
        "dpi": dpi,
        "width_px": int(width),
        "height_px": int(height),
        "otsu_threshold": float(otsu_threshold),
        "canny_low": int(low),
        "canny_high": int(high),
        "edge_pixel_ratio": round(edge_ratio, 8),
        "hough_threshold": int(hough_threshold),
        "min_line_length_px": int(min_line_length),
        "max_line_gap_px": int(max_line_gap),
        "raw_line_count": len(lines),
        "matching_line_count": len(matching_lines),
        "matching_truncated": len(lines) > len(matching_lines),
        "lines": matching_lines,
    }


def _bucket_key(line: dict[str, Any]) -> tuple[int, int, int]:
    mx, my = line["midpoint"]
    return (
        int(math.floor(mx / MIDPOINT_BUCKET_NORM)),
        int(math.floor(my / MIDPOINT_BUCKET_NORM)),
        int(math.floor(line["angle_deg"] / ANGLE_BUCKET_DEG)),
    )


def _endpoint_error(a: dict[str, Any], b: dict[str, Any]) -> float:
    direct = (
        math.hypot(a["a"][0] - b["a"][0], a["a"][1] - b["a"][1])
        + math.hypot(a["b"][0] - b["b"][0], a["b"][1] - b["b"][1])
    ) / 2.0
    reversed_error = (
        math.hypot(a["a"][0] - b["b"][0], a["a"][1] - b["b"][1])
        + math.hypot(a["b"][0] - b["a"][0], a["b"][1] - b["a"][1])
    ) / 2.0
    return min(direct, reversed_error)


def _match_lines(lines_200: list[dict[str, Any]], lines_300: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    buckets: dict[tuple[int, int, int], list[int]] = {}
    for index, line in enumerate(lines_200):
        buckets.setdefault(_bucket_key(line), []).append(index)

    used_200: set[int] = set()
    matches: list[dict[str, Any]] = []

    for line_300 in lines_300:
        bx, by, ba = _bucket_key(line_300)
        candidate_indices: set[int] = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for da in (-1, 0, 1):
                    candidate_indices.update(buckets.get((bx + dx, by + dy, ba + da), []))

        best: tuple[float, int, float, float] | None = None
        for index in sorted(candidate_indices):
            if index in used_200:
                continue
            line_200 = lines_200[index]
            angle_error = _angle_diff(line_200["angle_deg"], line_300["angle_deg"])
            if angle_error > ANGLE_TOLERANCE_DEG:
                continue
            endpoint_error = _endpoint_error(line_200, line_300)
            if endpoint_error > ENDPOINT_TOLERANCE_NORM:
                continue
            denominator = max(line_200["length_norm"], line_300["length_norm"], 1e-12)
            relative_length_error = abs(line_200["length_norm"] - line_300["length_norm"]) / denominator
            if relative_length_error > RELATIVE_LENGTH_TOLERANCE:
                continue
            score_key = endpoint_error + (angle_error / 180.0) + relative_length_error
            item = (score_key, index, angle_error, relative_length_error)
            if best is None or item < best:
                best = item

        if best is None:
            continue
        _, index_200, angle_error, relative_length_error = best
        line_200 = lines_200[index_200]
        used_200.add(index_200)
        endpoint_error = _endpoint_error(line_200, line_300)
        stability_score = max(
            0.0,
            1.0 - (
                endpoint_error / ENDPOINT_TOLERANCE_NORM
                + angle_error / ANGLE_TOLERANCE_DEG
                + relative_length_error / RELATIVE_LENGTH_TOLERANCE
            ) / 3.0,
        )
        matches.append({
            "line_200_id": line_200["line_id"],
            "line_300_id": line_300["line_id"],
            "line_300": line_300,
            "endpoint_error_norm": round(endpoint_error, 8),
            "angle_error_deg": round(angle_error, 6),
            "relative_length_error": round(relative_length_error, 8),
            "stability_score": round(stability_score, 8),
        })

    return matches, len(lines_200) - len(used_200), len(lines_300) - len(matches)


def _source_point(normalized: list[float], source_rect: list[float]) -> list[float]:
    x0, y0, x1, y1 = source_rect
    x = x0 + normalized[0] * (x1 - x0)
    y = y0 + normalized[1] * (y1 - y0)
    return [round(x, 6), round(y, 6)]


def _stable_candidates(region: dict[str, Any], matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    source_rect = region["source_rect_pt"]
    for match in matches:
        line = match["line_300"]
        quantized = [round(value, 6) for value in (*line["a"], *line["b"])]
        candidate_id = _stable_id("RGC", region["evidence_region_id"], *quantized)
        result.append({
            "candidate_id": candidate_id,
            "object_family": "RasterGeometryCandidate",
            "geometry_type": "LINE",
            "coordinate_space": "EVIDENCE_REGION_NORMALIZED_0_1",
            "geometry_normalized": {"a": line["a"], "b": line["b"]},
            "geometry_source_page_pt": {
                "a": _source_point(line["a"], source_rect),
                "b": _source_point(line["b"], source_rect),
            },
            "support": {
                "line_200_id": match["line_200_id"],
                "line_300_id": match["line_300_id"],
                "endpoint_error_norm": match["endpoint_error_norm"],
                "angle_error_deg": match["angle_error_deg"],
                "relative_length_error": match["relative_length_error"],
                "stability_score": match["stability_score"],
            },
            "semantic_classification": "UNASSIGNED",
            "candidate_state": "STABLE_ACROSS_200_300_DPI",
            "technical_identity_authorized": False,
            "structural_identity_authorized": False,
            "scene_materialization_authorized": False,
            "canonical_write_authorized": False,
        })
    result.sort(key=lambda row: row["candidate_id"])
    return result


def _svg(candidates: list[dict[str, Any]], target: Path) -> None:
    lines = []
    for candidate in candidates:
        a = candidate["geometry_normalized"]["a"]
        b = candidate["geometry_normalized"]["b"]
        lines.append(
            f'<line x1="{a[0] * 1000:.3f}" y1="{a[1] * 1000:.3f}" x2="{b[0] * 1000:.3f}" y2="{b[1] * 1000:.3f}" />'
        )
    body = "\n  ".join(lines)
    target.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000">\n'
        '  <g fill="none" stroke="currentColor" stroke-width="1">\n  '
        + body
        + '\n  </g>\n</svg>\n',
        encoding="utf-8",
    )


def _process_region(region: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    scale_200 = _extract_lines(Path(region["crop_200_path"]), 200)
    scale_300 = _extract_lines(Path(region["crop_300_path"]), 300)
    matches, unmatched_200, unmatched_300 = _match_lines(scale_200["lines"], scale_300["lines"])
    stable = _stable_candidates(region, matches)
    quality_state = "STABLE_CANDIDATES_PRESENT" if stable else "NO_STABLE_CANDIDATES"

    region_dir = output_dir / region["evidence_region_id"]
    region_dir.mkdir(parents=True, exist_ok=True)
    preview = region_dir / "stable_candidates.svg"
    _svg(stable, preview)

    result = {
        "schema_version": "1.0",
        "evidence_region_id": region["evidence_region_id"],
        "source_code": region["source_code"],
        "source_id": region["source_id"],
        "source_version_id": region["source_version_id"],
        "source_sha256": region["source_sha256"],
        "page_id": region["page_id"],
        "transform_id": region["transform_id"],
        "source_rect_pt": region["source_rect_pt"],
        "r1_classification": region["r1_classification"],
        "crops": {
            "200": region["crop_200"],
            "300": region["crop_300"],
        },
        "detector": {
            "opencv_version": cv2.__version__,
            "numpy_version": np.__version__,
            "algorithm": "CANNY_PLUS_PROBABILISTIC_HOUGH_MULTI_SCALE",
            "angle_tolerance_deg": ANGLE_TOLERANCE_DEG,
            "endpoint_tolerance_norm": ENDPOINT_TOLERANCE_NORM,
            "relative_length_tolerance": RELATIVE_LENGTH_TOLERANCE,
            "max_matching_lines_per_scale": MAX_MATCHING_LINES_PER_SCALE,
        },
        "scale_200": {key: value for key, value in scale_200.items() if key != "lines"},
        "scale_300": {key: value for key, value in scale_300.items() if key != "lines"},
        "stable_candidate_count": len(stable),
        "unmatched_matching_lines_200": unmatched_200,
        "unmatched_matching_lines_300": unmatched_300,
        "stable_candidates": stable,
        "preview_filename": str(preview.relative_to(output_dir)),
        "quality_state": quality_state,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "scene_materialization_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    result_path = region_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result["result_filename"] = str(result_path.relative_to(output_dir))
    return result


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: worker JOB_JSON OUTPUT_DIR")
    job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)
    results = [_process_region(region, output_dir) for region in job["regions"]]
    payload = {
        "worker_schema_version": "1.0",
        "opencv_version": cv2.__version__,
        "numpy_version": np.__version__,
        "regions": results,
    }
    (output_dir / "worker_output.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("CEW_RASTER_GEOMETRY_CANDIDATE_WORKER = PASS")
    print(f"OPENCV_VERSION = {cv2.__version__}")
    print(f"REGION_COVERAGE = {len(results)}/4")
    for row in results:
        print(
            "R2_REGION",
            row["evidence_region_id"],
            "raw200=" + str(row["scale_200"]["raw_line_count"]),
            "raw300=" + str(row["scale_300"]["raw_line_count"]),
            "stable=" + str(row["stable_candidate_count"]),
            "quality=" + row["quality_state"],
        )
    print("SCENE_MATERIALIZATION_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
