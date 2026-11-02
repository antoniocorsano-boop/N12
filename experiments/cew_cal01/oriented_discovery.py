from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from experiments.cew_cal01.anchor_discovery import normalize_dimension_text, proposal_from_ocr_token
from experiments.cew_cal01.exact_source import SOURCE_SHA256, _canonical_digest, _dimension_geometry_cv2
from experiments.cew_cal01.oriented_refinement import cluster_numeric_observations_by_location


ORIENTATIONS = (0, 90, 180, 270)
DEFAULT_TILE_SIZE = 2200
DEFAULT_OVERLAP = 400
DEFAULT_OCR_SCALE = 2.0
MIN_INK_FRACTION = 0.002
MAX_INK_FRACTION = 0.12


def _axis_starts(length: int, tile_size: int, overlap: int) -> list[int]:
    if length <= 0 or tile_size <= 0 or overlap < 0 or overlap >= tile_size:
        raise ValueError("CAL01_TILE_GEOMETRY_INVALID")
    if length <= tile_size:
        return [0]
    step = tile_size - overlap
    starts = list(range(0, length - tile_size + 1, step))
    last = length - tile_size
    if starts[-1] != last:
        starts.append(last)
    return starts


def _iter_tile_bounds(page_width: int, page_height: int, *, tile_size: int = DEFAULT_TILE_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[tuple[int, int, int, int]]:
    xs = _axis_starts(page_width, tile_size, overlap)
    ys = _axis_starts(page_height, tile_size, overlap)
    return [(x, y, min(page_width, x + tile_size), min(page_height, y + tile_size)) for y in ys for x in xs]


def _inverse_rotated_point(x: float, y: float, width: float, height: float, rotation_degrees: int) -> tuple[float, float]:
    rotation = int(rotation_degrees) % 360
    if rotation == 0:
        return x, y
    if rotation == 90:
        return y, height - x
    if rotation == 180:
        return width - x, height - y
    if rotation == 270:
        return width - y, x
    raise ValueError("CAL01_OCR_ROTATION_UNSUPPORTED")


def _map_oriented_bbox_to_page(bbox: list[float] | tuple[float, float, float, float], *, tile_bounds: tuple[int, int, int, int], rotation_degrees: int, ocr_scale: float) -> list[float]:
    if len(bbox) != 4 or ocr_scale <= 0:
        raise ValueError("CAL01_ORIENTED_BBOX_INVALID")
    tile_left, tile_top, tile_right, tile_bottom = tile_bounds
    width = float(tile_right - tile_left)
    height = float(tile_bottom - tile_top)
    if width <= 0 or height <= 0:
        raise ValueError("CAL01_TILE_BOUNDS_INVALID")
    left, top, right, bottom = (float(value) / float(ocr_scale) for value in bbox)
    if right <= left or bottom <= top:
        raise ValueError("CAL01_ORIENTED_BBOX_INVALID")
    corners = [
        _inverse_rotated_point(left, top, width, height, rotation_degrees),
        _inverse_rotated_point(right, top, width, height, rotation_degrees),
        _inverse_rotated_point(left, bottom, width, height, rotation_degrees),
        _inverse_rotated_point(right, bottom, width, height, rotation_degrees),
    ]
    xs = [point[0] + tile_left for point in corners]
    ys = [point[1] + tile_top for point in corners]
    return [min(xs), min(ys), max(xs), max(ys)]


def _rotate_image(image: Any, rotation_degrees: int) -> Any:
    import cv2
    rotation = int(rotation_degrees) % 360
    if rotation == 0:
        return image
    if rotation == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if rotation == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    if rotation == 270:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    raise ValueError("CAL01_OCR_ROTATION_UNSUPPORTED")


def _ink_fraction(gray: Any) -> float:
    import numpy as np
    if gray.size == 0:
        return 0.0
    return float(np.count_nonzero(gray < 180)) / float(gray.size)


def _prepare_for_numeric_ocr(gray: Any) -> Any:
    import cv2
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 11)
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (35, 1)))
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35)))
    line_mask = cv2.bitwise_or(horizontal, vertical)
    text_mask = cv2.subtract(binary, line_mask)
    text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)))
    return 255 - text_mask


def _run_numeric_tesseract(image: Any, *, psm: int = 11) -> list[dict[str, Any]]:
    import cv2
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        if not cv2.imwrite(str(temp_path), image):
            raise RuntimeError("CAL01_ORIENTED_TILE_WRITE_FAILED")
        command = ["tesseract", str(temp_path), "stdout", "--psm", str(psm), "-c", "tessedit_char_whitelist=0123456789.,", "tsv"]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"CAL01_ORIENTED_TESSERACT_FAILED:{proc.stderr.strip()}")
        reader = csv.DictReader(proc.stdout.splitlines(), delimiter="\t")
        tokens: list[dict[str, Any]] = []
        for row in reader:
            text = str(row.get("text") or "").strip()
            if not text:
                continue
            try:
                confidence = float(row.get("conf") or -1)
                left = int(row.get("left") or 0)
                top = int(row.get("top") or 0)
                width = int(row.get("width") or 0)
                height = int(row.get("height") or 0)
            except (TypeError, ValueError):
                continue
            if width <= 0 or height <= 0:
                continue
            tokens.append({"text": text, "confidence": confidence, "bbox_px": [left, top, left + width, top + height]})
        return tokens
    finally:
        temp_path.unlink(missing_ok=True)


def build_oriented_dimension_discovery(*, image_path: Path, base_discovery_path: Path, output_dir: Path) -> dict[str, Any]:
    import cv2
    base = json.loads(base_discovery_path.read_text(encoding="utf-8"))
    if base.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise RuntimeError("CAL01_ORIENTED_SOURCE_DIGEST_DRIFT")
    if base.get("historical_comparator_loaded") is not False or base.get("historical_affine_loaded") is not False:
        raise RuntimeError("CAL01_ORIENTED_HISTORICAL_INPUT_FORBIDDEN")

    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise RuntimeError("CAL01_ORIENTED_RASTER_UNREADABLE")
    page_height, page_width = gray.shape[:2]
    expected_width = int(base.get("raster", {}).get("width_px") or 0)
    expected_height = int(base.get("raster", {}).get("height_px") or 0)
    if (page_width, page_height) != (expected_width, expected_height):
        raise RuntimeError("CAL01_ORIENTED_RASTER_FRAME_DRIFT")

    tile_bounds = _iter_tile_bounds(page_width, page_height)
    selected_tiles: list[tuple[tuple[int, int, int, int], float]] = []
    for bounds in tile_bounds:
        left, top, right, bottom = bounds
        crop = gray[top:bottom, left:right]
        fraction = _ink_fraction(crop)
        if MIN_INK_FRACTION <= fraction <= MAX_INK_FRACTION:
            selected_tiles.append((bounds, fraction))

    candidates: list[dict[str, Any]] = []
    ocr_pass_count = 0
    for tile_index, (bounds, fraction) in enumerate(selected_tiles):
        left, top, right, bottom = bounds
        original_tile = gray[top:bottom, left:right]
        prepared = _prepare_for_numeric_ocr(original_tile)
        for rotation in ORIENTATIONS:
            oriented = _rotate_image(prepared, rotation)
            oriented = cv2.resize(oriented, None, fx=DEFAULT_OCR_SCALE, fy=DEFAULT_OCR_SCALE, interpolation=cv2.INTER_CUBIC)
            ocr_pass_count += 1
            for token in _run_numeric_tesseract(oriented, psm=11):
                if normalize_dimension_text(token["text"]) is None:
                    continue
                page_bbox = _map_oriented_bbox_to_page(token["bbox_px"], tile_bounds=bounds, rotation_degrees=rotation, ocr_scale=DEFAULT_OCR_SCALE)
                proposal = proposal_from_ocr_token({"text": token["text"], "confidence": token["confidence"], "bbox_px": page_bbox}, page_width=page_width, page_height=page_height)
                proposal.update({
                    "raw_ocr_text": token["text"],
                    "ocr_method": "TILED_ORIENTED_PSM11_LINE_SUPPRESSED",
                    "ocr_rotation_degrees": rotation,
                    "ocr_scale": DEFAULT_OCR_SCALE,
                    "tile_index": tile_index,
                    "tile_bounds_px": list(bounds),
                    "tile_ink_fraction": fraction,
                })
                proposal["geometry"] = _dimension_geometry_cv2(gray, page_bbox)
                candidates.append(proposal)

    location_clusters = cluster_numeric_observations_by_location(candidates, centroid_tolerance_px=16.0)

    by_key: dict[tuple[str, int, int], dict[str, Any]] = {}
    votes: dict[tuple[str, int, int], set[int]] = {}
    for proposal in candidates:
        left, top, right, bottom = proposal["bbox_px"]
        center_x = (float(left) + float(right)) / 2.0
        center_y = (float(top) + float(bottom)) / 2.0
        key = (proposal["normalized_metric_text"], int(round(center_x / 16.0)), int(round(center_y / 16.0)))
        votes.setdefault(key, set()).add(int(proposal["ocr_rotation_degrees"]))
        current = by_key.get(key)
        if current is None or float(proposal["ocr_confidence"]) > float(current["ocr_confidence"]):
            by_key[key] = proposal

    proposals: list[dict[str, Any]] = []
    for key, proposal in by_key.items():
        enriched = dict(proposal)
        enriched["orientation_votes"] = sorted(votes[key])
        enriched["orientation_vote_count"] = len(votes[key])
        proposals.append(enriched)
    proposals.sort(key=lambda item: (item["bbox_px"][1], item["bbox_px"][0], item["normalized_metric_text"]))

    bound_count = sum(1 for item in proposals if item["geometry"].get("geometrically_bound") is True)
    overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for item in proposals:
        left, top, right, bottom = [int(round(value)) for value in item["bbox_px"]]
        bound = item["geometry"].get("geometrically_bound") is True
        color = (0, 180, 0) if bound else (0, 140, 255)
        cv2.rectangle(overlay, (left, top), (right, bottom), color, 2)
        if bound:
            a = item["geometry"]["endpoint_a_px"]
            b = item["geometry"]["endpoint_b_px"]
            cv2.line(overlay, (int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1]))), color, 2)

    output_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = output_dir / "oriented-dimension-proposal-overlay.png"
    if not cv2.imwrite(str(overlay_path), overlay):
        raise RuntimeError("CAL01_ORIENTED_OVERLAY_WRITE_FAILED")

    result = {
        "schema": "CEW_CAL01_ORIENTED_DIMENSION_DISCOVERY_v2",
        "program": "CEW-CAL-01",
        "source": dict(base["source"]),
        "base_discovery_digest": base["discovery_digest"],
        "tile_strategy": {
            "tile_size_px": DEFAULT_TILE_SIZE,
            "overlap_px": DEFAULT_OVERLAP,
            "ink_fraction_min": MIN_INK_FRACTION,
            "ink_fraction_max": MAX_INK_FRACTION,
            "rotations_degrees": list(ORIENTATIONS),
            "ocr_scale": DEFAULT_OCR_SCALE,
            "line_suppression": True,
            "psm": 11,
        },
        "tile_count_total": len(tile_bounds),
        "tile_count_selected": len(selected_tiles),
        "ocr_pass_count": ocr_pass_count,
        "raw_numeric_observation_count": len(candidates),
        "location_cluster_count": len(location_clusters),
        "oriented_numeric_proposal_count": len(proposals),
        "geometrically_bound_dimension_count": bound_count,
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "tav02s_evidence_loaded": False,
        "location_clusters": location_clusters,
        "proposals": proposals,
        "authority": dict(base["authority"]),
    }
    digest_payload = dict(result)
    result["oriented_discovery_digest"] = _canonical_digest(digest_payload)
    (output_dir / "oriented-dimension-discovery.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--base-discovery", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = build_oriented_dimension_discovery(image_path=Path(args.image), base_discovery_path=Path(args.base_discovery), output_dir=Path(args.output_dir))
    print(json.dumps({
        "tile_count_selected": result["tile_count_selected"],
        "ocr_pass_count": result["ocr_pass_count"],
        "raw_numeric_observation_count": result["raw_numeric_observation_count"],
        "location_cluster_count": result["location_cluster_count"],
        "oriented_numeric_proposal_count": result["oriented_numeric_proposal_count"],
        "geometrically_bound_dimension_count": result["geometrically_bound_dimension_count"],
        "oriented_discovery_digest": result["oriented_discovery_digest"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
