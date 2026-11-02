from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from experiments.cew_cal01.anchor_discovery import normalize_dimension_text, proposal_from_ocr_token
from experiments.cew_cal01.exact_source import AUTHORITY_CLOSED, SOURCE_SHA256, _canonical_digest, _dimension_geometry_cv2
from experiments.cew_cal01.oriented_discovery import _map_oriented_bbox_to_page, _rotate_image


DETECTION_TARGET_WIDTH_PX = 2200
DETECTION_THRESHOLD = 190
DETECTION_DILATION_KERNEL = 9
MIN_PLAN_WIDTH_FRACTION = 0.45
MIN_PLAN_HEIGHT_FRACTION = 0.60
OUTER_MARGIN_FRACTION = 0.10
INNER_OVERLAP_FRACTION = 0.035
OCR_SCALE = 2.0
OCR_ROTATIONS = (0, 90, 180, 270)
OCR_PREPROCESS_MODES = ("RAW_GRAYSCALE", "CLAHE", "BINARY_OTSU")


def _normalized_plan_frame(*, source_width_px: int, source_height_px: int) -> dict[str, Any]:
    if source_width_px <= 0 or source_height_px <= 0:
        raise ValueError("CAL01_PLAN_FRAME_INVALID")
    if source_height_px > source_width_px:
        return {
            "transform": "ROTATE_90_COUNTERCLOCKWISE",
            "source_width_px": int(source_width_px),
            "source_height_px": int(source_height_px),
            "normalized_width_px": int(source_height_px),
            "normalized_height_px": int(source_width_px),
        }
    return {
        "transform": "NONE",
        "source_width_px": int(source_width_px),
        "source_height_px": int(source_height_px),
        "normalized_width_px": int(source_width_px),
        "normalized_height_px": int(source_height_px),
    }


def _select_structural_envelope_bbox(
    components: list[dict[str, Any]],
    *,
    page_width: int,
    page_height: int,
    min_width_fraction: float = MIN_PLAN_WIDTH_FRACTION,
    min_height_fraction: float = MIN_PLAN_HEIGHT_FRACTION,
) -> list[int]:
    if page_width <= 0 or page_height <= 0:
        raise ValueError("CAL01_PLAN_FRAME_INVALID")
    qualified: list[tuple[int, int, list[int]]] = []
    for component in components:
        bbox = [int(value) for value in component.get("bbox_px", [])]
        if len(bbox) != 4:
            continue
        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            continue
        if width < page_width * min_width_fraction or height < page_height * min_height_fraction:
            continue
        bbox_area = width * height
        ink_area = int(component.get("ink_area_px") or 0)
        qualified.append((bbox_area, ink_area, bbox))
    if not qualified:
        raise RuntimeError("CAL01_PLAN_ENVELOPE_NOT_FOUND")
    qualified.sort(key=lambda row: (row[0], row[1], -row[2][1], -row[2][0]), reverse=True)
    return qualified[0][2]


def build_perimeter_bands(
    envelope_bbox: list[int] | tuple[int, int, int, int],
    *,
    page_width: int,
    page_height: int,
    outer_margin_px: int,
    inner_overlap_px: int,
) -> list[dict[str, Any]]:
    if len(envelope_bbox) != 4 or page_width <= 0 or page_height <= 0:
        raise ValueError("CAL01_PERIMETER_BAND_INPUT_INVALID")
    left, top, right, bottom = [int(value) for value in envelope_bbox]
    if not (0 <= left < right <= page_width and 0 <= top < bottom <= page_height):
        raise ValueError("CAL01_PLAN_ENVELOPE_BOUNDS_INVALID")
    if outer_margin_px < 0 or inner_overlap_px < 0:
        raise ValueError("CAL01_PERIMETER_MARGIN_INVALID")

    def clipped(bbox: list[int]) -> list[int]:
        x0, y0, x1, y1 = bbox
        return [
            max(0, min(page_width, x0)),
            max(0, min(page_height, y0)),
            max(0, min(page_width, x1)),
            max(0, min(page_height, y1)),
        ]

    return [
        {"side": "TOP", "bbox_px": clipped([left, top - outer_margin_px, right, top + inner_overlap_px])},
        {"side": "RIGHT", "bbox_px": clipped([right - inner_overlap_px, top, right + outer_margin_px, bottom])},
        {"side": "BOTTOM", "bbox_px": clipped([left, bottom - inner_overlap_px, right, bottom + outer_margin_px])},
        {"side": "LEFT", "bbox_px": clipped([left - outer_margin_px, top, left + inner_overlap_px, bottom])},
    ]


def classify_perimeter_observations(observations: list[dict[str, Any]]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for observation in observations:
        geometry = observation.get("geometry") or {}
        if geometry.get("geometrically_bound") is True and geometry.get("geometry_role") == "DIMENSION_LINE_WITH_TWO_REFERENCES":
            candidate = dict(observation)
            candidate["semantic_role"] = "PERIMETER_LINEAR_DIMENSION_CANDIDATE"
            candidate["primary_visual_validation_required"] = True
            candidate["fit_eligible"] = False
            candidates.append(candidate)
        else:
            rejected.append(dict(observation))
    candidates.sort(key=lambda row: str(row.get("observation_id") or ""))
    rejected.sort(key=lambda row: str(row.get("observation_id") or ""))
    return {
        "candidate_count": len(candidates),
        "candidates": candidates,
        "rejected_observation_count": len(rejected),
        "rejected_observations": rejected,
        "status": "PERIMETER_DIMENSION_CHAINS_OBSERVED" if candidates else "PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED",
        "primary_anchor_count": 0,
    }


def _normalize_image_for_plan_detection(gray: Any) -> tuple[Any, dict[str, Any]]:
    import cv2

    height, width = gray.shape[:2]
    record = _normalized_plan_frame(source_width_px=int(width), source_height_px=int(height))
    if record["transform"] == "ROTATE_90_COUNTERCLOCKWISE":
        return cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE), record
    return gray, record


def _normalized_bbox_to_source(bbox: list[float], frame: dict[str, Any]) -> list[float]:
    if len(bbox) != 4:
        raise ValueError("CAL01_PLAN_BBOX_INVALID")
    left, top, right, bottom = [float(value) for value in bbox]
    if frame["transform"] == "NONE":
        return [left, top, right, bottom]
    source_width = float(frame["source_width_px"])
    return [source_width - bottom, left, source_width - top, right]


def detect_structural_plan_envelope(gray: Any) -> dict[str, Any]:
    import cv2

    normalized, frame = _normalize_image_for_plan_detection(gray)
    normalized_height, normalized_width = normalized.shape[:2]
    scale = min(1.0, float(DETECTION_TARGET_WIDTH_PX) / float(normalized_width))
    if scale < 1.0:
        thumbnail = cv2.resize(normalized, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    else:
        thumbnail = normalized
    _, mask = cv2.threshold(thumbnail, DETECTION_THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (DETECTION_DILATION_KERNEL, DETECTION_DILATION_KERNEL))
    joined = cv2.dilate(mask, kernel, iterations=1)
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(joined, 8)

    components: list[dict[str, Any]] = []
    for index in range(1, count):
        x, y, width, height, area = [int(value) for value in stats[index]]
        if width <= 0 or height <= 0:
            continue
        components.append(
            {
                "component_index": index,
                "bbox_px": [
                    int(round(x / scale)),
                    int(round(y / scale)),
                    int(round((x + width) / scale)),
                    int(round((y + height) / scale)),
                ],
                "ink_area_px": int(round(area / (scale * scale))),
            }
        )

    envelope_normalized = _select_structural_envelope_bbox(
        components,
        page_width=normalized_width,
        page_height=normalized_height,
    )
    envelope_source = _normalized_bbox_to_source([float(value) for value in envelope_normalized], frame)
    return {
        "normalization": frame,
        "detection": {
            "target_width_px": DETECTION_TARGET_WIDTH_PX,
            "threshold": DETECTION_THRESHOLD,
            "dilation_kernel_px_at_detection_scale": DETECTION_DILATION_KERNEL,
            "min_width_fraction": MIN_PLAN_WIDTH_FRACTION,
            "min_height_fraction": MIN_PLAN_HEIGHT_FRACTION,
            "scale": scale,
            "component_count": len(components),
        },
        "envelope_bbox_normalized_px": envelope_normalized,
        "envelope_bbox_source_px": envelope_source,
    }


def _prepare_ocr_variant(gray: Any, mode: str) -> Any:
    import cv2

    if mode == "RAW_GRAYSCALE":
        return gray
    if mode == "CLAHE":
        return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    if mode == "BINARY_OTSU":
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    raise ValueError("CAL01_PERIMETER_OCR_PREPROCESS_UNSUPPORTED")


def _run_numeric_tesseract(image: Any, *, psm: int = 11) -> list[dict[str, Any]]:
    import cv2

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        if not cv2.imwrite(str(temp_path), image):
            raise RuntimeError("CAL01_PERIMETER_OCR_IMAGE_WRITE_FAILED")
        proc = subprocess.run(
            [
                "tesseract",
                str(temp_path),
                "stdout",
                "--psm",
                str(psm),
                "-c",
                "tessedit_char_whitelist=0123456789.,",
                "tsv",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"CAL01_PERIMETER_TESSERACT_FAILED:{proc.stderr.strip()}")
        rows: list[dict[str, Any]] = []
        for row in csv.DictReader(proc.stdout.splitlines(), delimiter="\t"):
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
            rows.append({"text": text, "confidence": confidence, "bbox_px": [left, top, left + width, top + height]})
        return rows
    finally:
        temp_path.unlink(missing_ok=True)


def build_perimeter_dimension_discovery(*, image_path: Path, base_discovery_path: Path, output_dir: Path) -> dict[str, Any]:
    import cv2

    base = json.loads(base_discovery_path.read_text(encoding="utf-8"))
    if base.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise RuntimeError("CAL01_PERIMETER_SOURCE_DIGEST_DRIFT")
    if base.get("historical_comparator_loaded") is not False or base.get("historical_affine_loaded") is not False:
        raise RuntimeError("CAL01_PERIMETER_HISTORICAL_INPUT_FORBIDDEN")

    source_gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if source_gray is None:
        raise RuntimeError("CAL01_PERIMETER_RASTER_UNREADABLE")
    source_height, source_width = source_gray.shape[:2]
    if (source_width, source_height) != (
        int(base.get("raster", {}).get("width_px") or 0),
        int(base.get("raster", {}).get("height_px") or 0),
    ):
        raise RuntimeError("CAL01_PERIMETER_RASTER_FRAME_DRIFT")

    normalized, frame = _normalize_image_for_plan_detection(source_gray)
    normalized_height, normalized_width = normalized.shape[:2]
    envelope_record = detect_structural_plan_envelope(source_gray)
    envelope_bbox = [int(value) for value in envelope_record["envelope_bbox_normalized_px"]]
    outer_margin = max(1, int(round(normalized_height * OUTER_MARGIN_FRACTION)))
    inner_overlap = max(1, int(round(normalized_height * INNER_OVERLAP_FRACTION)))
    bands = build_perimeter_bands(
        envelope_bbox,
        page_width=normalized_width,
        page_height=normalized_height,
        outer_margin_px=outer_margin,
        inner_overlap_px=inner_overlap,
    )

    by_key: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    supporting_families: dict[tuple[str, str, int, int], set[tuple[str, int]]] = {}
    ocr_pass_count = 0
    for band in bands:
        band_left, band_top, band_right, band_bottom = [int(value) for value in band["bbox_px"]]
        crop = normalized[band_top:band_bottom, band_left:band_right]
        if crop.size == 0:
            continue
        for preprocess_mode in OCR_PREPROCESS_MODES:
            prepared = _prepare_ocr_variant(crop, preprocess_mode)
            for rotation in OCR_ROTATIONS:
                oriented = _rotate_image(prepared, rotation)
                oriented = cv2.resize(oriented, None, fx=OCR_SCALE, fy=OCR_SCALE, interpolation=cv2.INTER_CUBIC)
                ocr_pass_count += 1
                for token in _run_numeric_tesseract(oriented, psm=11):
                    if normalize_dimension_text(token["text"]) is None:
                        continue
                    normalized_bbox = _map_oriented_bbox_to_page(
                        token["bbox_px"],
                        tile_bounds=(band_left, band_top, band_right, band_bottom),
                        rotation_degrees=rotation,
                        ocr_scale=OCR_SCALE,
                    )
                    source_bbox = _normalized_bbox_to_source(normalized_bbox, frame)
                    proposal = proposal_from_ocr_token(
                        {"text": token["text"], "confidence": token["confidence"], "bbox_px": source_bbox},
                        page_width=source_width,
                        page_height=source_height,
                    )
                    proposal.update(
                        {
                            "search_band": band["side"],
                            "preprocess_mode": preprocess_mode,
                            "ocr_rotation_degrees": rotation,
                            "ocr_scale": OCR_SCALE,
                            "bbox_normalized_px": normalized_bbox,
                        }
                    )
                    proposal["geometry"] = _dimension_geometry_cv2(source_gray, source_bbox)
                    left, top, right, bottom = source_bbox
                    center_x = (left + right) / 2.0
                    center_y = (top + bottom) / 2.0
                    key = (
                        band["side"],
                        proposal["normalized_metric_text"],
                        int(round(center_x / 16.0)),
                        int(round(center_y / 16.0)),
                    )
                    supporting_families.setdefault(key, set()).add((preprocess_mode, rotation))
                    current = by_key.get(key)
                    if current is None or float(proposal["ocr_confidence"]) > float(current["ocr_confidence"]):
                        by_key[key] = proposal

    observations: list[dict[str, Any]] = []
    for key, proposal in by_key.items():
        row = dict(proposal)
        row["supporting_ocr_family_count"] = len(supporting_families[key])
        row["observation_id"] = "CAL01-PER-" + _canonical_digest(
            {
                "side": row["search_band"],
                "text": row["normalized_metric_text"],
                "bbox_px": [round(float(value), 3) for value in row["bbox_px"]],
            }
        ).split(":", 1)[1][:16]
        observations.append(row)
    observations.sort(key=lambda row: (row["bbox_px"][1], row["bbox_px"][0], row["normalized_metric_text"]))

    classified = classify_perimeter_observations(observations)
    overlay = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
    env_left, env_top, env_right, env_bottom = envelope_bbox
    cv2.rectangle(overlay, (env_left, env_top), (env_right, env_bottom), (80, 80, 80), 4)
    for band in bands:
        left, top, right, bottom = band["bbox_px"]
        cv2.rectangle(overlay, (left, top), (right, bottom), (160, 160, 160), 3)
    for candidate in classified["candidates"]:
        source_bbox = candidate["bbox_px"]
        if frame["transform"] == "ROTATE_90_COUNTERCLOCKWISE":
            source_left, source_top, source_right, source_bottom = source_bbox
            normalized_candidate_bbox = [source_top, source_width - source_right, source_bottom, source_width - source_left]
        else:
            normalized_candidate_bbox = source_bbox
        left, top, right, bottom = [int(round(value)) for value in normalized_candidate_bbox]
        cv2.rectangle(overlay, (left, top), (right, bottom), (0, 0, 0), 4)

    output_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = output_dir / "perimeter-search-overlay.png"
    if not cv2.imwrite(str(overlay_path), overlay):
        raise RuntimeError("CAL01_PERIMETER_OVERLAY_WRITE_FAILED")

    result = {
        "schema": "CEW_CAL01_PERIMETER_DIMENSION_DISCOVERY_v1",
        "program": "CEW-CAL-01",
        "source": dict(base["source"]),
        "base_discovery_digest": base["discovery_digest"],
        "normalization": frame,
        "structural_plan_envelope": envelope_record,
        "band_strategy": {
            "outer_margin_fraction": OUTER_MARGIN_FRACTION,
            "inner_overlap_fraction": INNER_OVERLAP_FRACTION,
            "outer_margin_px": outer_margin,
            "inner_overlap_px": inner_overlap,
        },
        "bands": bands,
        "ocr_strategy": {
            "preprocess_modes": list(OCR_PREPROCESS_MODES),
            "rotations_degrees": list(OCR_ROTATIONS),
            "scale": OCR_SCALE,
            "psm": 11,
            "line_suppression": False,
            "numeric_whitelist": "0123456789.,",
        },
        "ocr_pass_count": ocr_pass_count,
        "numeric_observation_count": len(observations),
        "observations": observations,
        "candidate_count": classified["candidate_count"],
        "candidates": classified["candidates"],
        "rejected_observation_count": classified["rejected_observation_count"],
        "status": classified["status"],
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "tav02s_evidence_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    digest_payload = dict(result)
    result["perimeter_discovery_digest"] = _canonical_digest(digest_payload)
    (output_dir / "perimeter-dimension-discovery.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--base-discovery", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = build_perimeter_dimension_discovery(
        image_path=Path(args.image),
        base_discovery_path=Path(args.base_discovery),
        output_dir=Path(args.output_dir),
    )
    print(
        json.dumps(
            {
                "numeric_observation_count": result["numeric_observation_count"],
                "candidate_count": result["candidate_count"],
                "status": result["status"],
                "primary_anchor_count": result["primary_anchor_count"],
                "perimeter_discovery_digest": result["perimeter_discovery_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
