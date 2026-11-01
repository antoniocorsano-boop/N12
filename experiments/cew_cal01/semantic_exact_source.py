from __future__ import annotations

import argparse
import json
from math import hypot
from pathlib import Path
import re
from typing import Any

from experiments.cew_cal01.anchor_discovery import normalize_dimension_text
from experiments.cew_cal01.exact_source import SOURCE_SHA256, _canonical_digest
from experiments.cew_cal01.oriented_discovery import (
    DEFAULT_OCR_SCALE,
    _map_oriented_bbox_to_page,
    _prepare_for_numeric_ocr,
    _rotate_image,
    _run_numeric_tesseract,
)
from experiments.cew_cal01.role_verification import detect_nearby_closed_frame, select_ocr_consensus
from experiments.cew_cal01.semantic_replay import refine_location_cluster


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}
_NUMERIC_TEXT_RE = re.compile(r"^\d+(?:[\.,]\d+)?$")
_CONFIRMATION_MODES = ("RAW_GRAYSCALE", "LINE_SUPPRESSED")
_CONFIRMATION_PSM = 6


def _normalize_hough_lines(lines: Any) -> list[list[float]]:
    if lines is None:
        return []
    raw = lines.tolist() if hasattr(lines, "tolist") else list(lines)
    result: list[list[float]] = []
    for item in raw:
        value = item
        if isinstance(value, (list, tuple)) and len(value) == 1 and isinstance(value[0], (list, tuple)):
            value = value[0]
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            continue
        result.append([float(component) for component in value])
    return result


def _bbox_centroid(bbox: list[float] | tuple[float, float, float, float]) -> tuple[float, float]:
    if len(bbox) != 4:
        raise ValueError("CAL01_CONFIRMATION_BBOX_INVALID")
    left, top, right, bottom = (float(value) for value in bbox)
    if right <= left or bottom <= top:
        raise ValueError("CAL01_CONFIRMATION_BBOX_INVALID")
    return (left + right) / 2.0, (top + bottom) / 2.0


def build_confirmation_pass_plan(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    """Build bounded PSM6 confirmation passes only from already observed source tiles."""

    observations = cluster.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("CAL01_CONFIRMATION_OBSERVATIONS_REQUIRED")
    unique: dict[tuple[int, tuple[int, int, int, int], int], dict[str, Any]] = {}
    for observation in observations:
        tile_index = int(observation.get("tile_index"))
        raw_bounds = observation.get("tile_bounds_px")
        if not isinstance(raw_bounds, (list, tuple)) or len(raw_bounds) != 4:
            raise ValueError("CAL01_CONFIRMATION_TILE_BOUNDS_REQUIRED")
        bounds = tuple(int(round(float(value))) for value in raw_bounds)
        rotation = int(observation.get("ocr_rotation_degrees")) % 360
        if rotation not in {0, 90, 180, 270}:
            raise ValueError("CAL01_CONFIRMATION_ROTATION_INVALID")
        unique[(tile_index, bounds, rotation)] = {
            "tile_index": tile_index,
            "tile_bounds_px": list(bounds),
            "rotation_degrees": rotation,
        }

    plan: list[dict[str, Any]] = []
    for _, base in sorted(unique.items(), key=lambda item: (item[0][0], item[0][2], item[0][1])):
        for mode in _CONFIRMATION_MODES:
            plan.append({
                **base,
                "preprocess_mode": mode,
                "psm": _CONFIRMATION_PSM,
                "ocr_scale": DEFAULT_OCR_SCALE,
            })
    return plan


def select_confirmation_token(
    tokens: list[dict[str, Any]],
    *,
    target_bbox_px: list[float] | tuple[float, float, float, float],
) -> dict[str, Any] | None:
    """Select only the nearest numeric token compatible with the same source location."""

    target_cx, target_cy = _bbox_centroid(target_bbox_px)
    left, top, right, bottom = (float(value) for value in target_bbox_px)
    diagonal = hypot(right - left, bottom - top)
    tolerance = min(90.0, max(24.0, diagonal * 0.65))
    candidates: list[tuple[float, float, str, dict[str, Any]]] = []
    for token in tokens:
        text = str(token.get("text") or "").strip().replace(" ", "")
        if not _NUMERIC_TEXT_RE.fullmatch(text):
            continue
        bbox = token.get("bbox_px")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        try:
            cx, cy = _bbox_centroid(bbox)
        except ValueError:
            continue
        distance = hypot(cx - target_cx, cy - target_cy)
        if distance > tolerance:
            continue
        candidates.append((distance, -float(token.get("confidence", 0.0)), text, token))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return dict(candidates[0][3])


def _extract_local_line_segments(gray: Any, bbox_px: list[float]) -> list[list[float]]:
    import cv2
    import numpy as np

    height, width = gray.shape[:2]
    left, top, right, bottom = [float(value) for value in bbox_px]
    token_span = max(right - left, bottom - top)
    padding = int(min(360.0, max(140.0, token_span * 4.0)))
    x0 = max(0, int(left) - padding)
    y0 = max(0, int(top) - padding)
    x1 = min(width, int(right) + padding)
    y1 = min(height, int(bottom) + padding)
    crop = gray[y0:y1, x0:x1]
    if crop.size == 0:
        return []

    blurred = cv2.GaussianBlur(crop, (3, 3), 0)
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        11,
    )
    lines = cv2.HoughLinesP(
        binary,
        1,
        np.pi / 180.0,
        threshold=24,
        minLineLength=10,
        maxLineGap=8,
    )
    result: list[list[float]] = []
    for x_a, y_a, x_b, y_b in _normalize_hough_lines(lines):
        result.append([x_a + x0, y_a + y0, x_b + x0, y_b + y0])
    result.sort(key=lambda item: (item[1], item[0], item[3], item[2]))
    return result


def merge_local_line_evidence(
    primary: list[list[float]],
    short_tick_channel: list[list[float]],
    *,
    max_tick_length_px: float = 90.0,
) -> list[list[float]]:
    """Append only bounded short-line evidence without replacing main-line evidence.

    The primary Hough channel remains authoritative for local line reconstruction.
    A secondary channel may contribute short terminal-tick candidates only; long
    structural diagonals are discarded before the document-grammar gate.
    """

    if max_tick_length_px <= 0:
        raise ValueError("CAL01_LOCAL_TICK_LENGTH_POLICY_INVALID")

    result: list[list[float]] = []
    seen: set[tuple[float, float, float, float]] = set()

    def add(line: list[float]) -> None:
        if not isinstance(line, (list, tuple)) or len(line) != 4:
            raise ValueError("CAL01_LOCAL_LINE_SEGMENT_INVALID")
        normalized = [float(value) for value in line]
        key = tuple(normalized)
        if key in seen:
            return
        seen.add(key)
        result.append(normalized)

    for line in primary:
        add(line)

    for line in short_tick_channel:
        if not isinstance(line, (list, tuple)) or len(line) != 4:
            raise ValueError("CAL01_LOCAL_LINE_SEGMENT_INVALID")
        x1, y1, x2, y2 = (float(value) for value in line)
        length = hypot(x2 - x1, y2 - y1)
        if length < 4.0 or length > max_tick_length_px:
            continue
        add([x1, y1, x2, y2])

    return result


def _confirmation_observations(gray: Any, cluster: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    import cv2

    representative = cluster.get("representative") or {}
    target_bbox = representative.get("bbox_px")
    if not isinstance(target_bbox, (list, tuple)) or len(target_bbox) != 4:
        raise RuntimeError("CAL01_CONFIRMATION_TARGET_BBOX_INVALID")

    observations: list[dict[str, Any]] = []
    plan = build_confirmation_pass_plan(cluster)
    height, width = gray.shape[:2]
    for pass_index, item in enumerate(plan):
        left, top, right, bottom = item["tile_bounds_px"]
        if left < 0 or top < 0 or right > width or bottom > height or right <= left or bottom <= top:
            raise RuntimeError("CAL01_CONFIRMATION_TILE_FRAME_INVALID")
        source_tile = gray[top:bottom, left:right]
        prepared = source_tile if item["preprocess_mode"] == "RAW_GRAYSCALE" else _prepare_for_numeric_ocr(source_tile)
        oriented = _rotate_image(prepared, item["rotation_degrees"])
        oriented = cv2.resize(
            oriented,
            None,
            fx=float(item["ocr_scale"]),
            fy=float(item["ocr_scale"]),
            interpolation=cv2.INTER_CUBIC,
        )
        mapped_tokens: list[dict[str, Any]] = []
        for token in _run_numeric_tesseract(oriented, psm=int(item["psm"])):
            page_bbox = _map_oriented_bbox_to_page(
                token["bbox_px"],
                tile_bounds=tuple(item["tile_bounds_px"]),
                rotation_degrees=int(item["rotation_degrees"]),
                ocr_scale=float(item["ocr_scale"]),
            )
            mapped_tokens.append({
                "text": token["text"],
                "confidence": token["confidence"],
                "bbox_px": page_bbox,
            })
        selected = select_confirmation_token(mapped_tokens, target_bbox_px=list(target_bbox))
        if selected is None:
            continue
        identity = {
            "tile_index": item["tile_index"],
            "rotation": item["rotation_degrees"],
            "mode": item["preprocess_mode"],
            "psm": item["psm"],
            "text": selected["text"],
            "bbox_px": selected["bbox_px"],
        }
        normalized = normalize_dimension_text(selected["text"])
        observation = {
            "proposal_id": "CEW-CAL01-CONF-" + _canonical_digest(identity).split(":", 1)[1][:20],
            "raw_ocr_text": str(selected["text"]),
            "bbox_px": [float(value) for value in selected["bbox_px"]],
            "ocr_confidence": float(selected.get("confidence", 0.0)),
            "ocr_rotation_degrees": int(item["rotation_degrees"]),
            "tile_index": int(item["tile_index"]),
            "tile_bounds_px": list(item["tile_bounds_px"]),
            "ocr_method": f"CONFIRM_{item['preprocess_mode']}_PSM{item['psm']}",
            "confirmation_pass_index": pass_index,
        }
        if normalized is not None:
            observation["normalized_metric_text"] = normalized[0]
            observation["metric_value_m"] = normalized[1]
        observations.append(observation)
    return observations, len(plan)


def _enhance_cluster_with_confirmation(gray: Any, cluster: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
    existing = [dict(item) for item in (cluster.get("observations") or [])]
    initial_consensus = select_ocr_consensus(cluster.get("readings") or [], minimum_count=3, minimum_margin=2)
    if initial_consensus["confirmed"]:
        return dict(cluster), 0, 0

    added, pass_count = _confirmation_observations(gray, cluster)
    all_observations = existing + added
    if not all_observations:
        return dict(cluster), pass_count, 0
    best = max(
        all_observations,
        key=lambda item: (float(item.get("ocr_confidence", 0.0)), str(item.get("proposal_id") or "")),
    )
    enhanced = dict(cluster)
    enhanced["observations"] = all_observations
    enhanced["readings"] = sorted(str(item.get("raw_ocr_text") or "").strip() for item in all_observations)
    enhanced["observation_count"] = len(all_observations)
    enhanced["representative"] = best
    enhanced["confirmation_observation_count"] = len(added)
    return enhanced, pass_count, len(added)


def build_semantic_role_replay(
    *,
    image_path: Path,
    oriented_discovery_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    import cv2

    oriented = json.loads(oriented_discovery_path.read_text(encoding="utf-8"))
    if oriented.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise RuntimeError("CAL01_SEMANTIC_SOURCE_DIGEST_DRIFT")
    if oriented.get("historical_comparator_loaded") is not False:
        raise RuntimeError("CAL01_SEMANTIC_HISTORICAL_COMPARATOR_FORBIDDEN")
    if oriented.get("historical_affine_loaded") is not False:
        raise RuntimeError("CAL01_SEMANTIC_HISTORICAL_AFFINE_FORBIDDEN")
    if oriented.get("tav02s_evidence_loaded") is not False:
        raise RuntimeError("CAL01_SEMANTIC_TAV02S_FORBIDDEN")

    clusters = oriented.get("location_clusters")
    if not isinstance(clusters, list) or not clusters:
        raise RuntimeError("CAL01_SEMANTIC_LOCATION_CLUSTERS_REQUIRED")

    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise RuntimeError("CAL01_SEMANTIC_RASTER_UNREADABLE")

    results: list[dict[str, Any]] = []
    total_confirmation_passes = 0
    total_confirmation_observations = 0
    for cluster_index, cluster in enumerate(clusters):
        enhanced_cluster, pass_count, added_count = _enhance_cluster_with_confirmation(gray, cluster)
        total_confirmation_passes += pass_count
        total_confirmation_observations += added_count
        representative = enhanced_cluster.get("representative") or {}
        bbox = representative.get("bbox_px")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise RuntimeError("CAL01_SEMANTIC_CLUSTER_BBOX_INVALID")
        segments = _extract_local_line_segments(gray, bbox)
        frame = detect_nearby_closed_frame(
            segments,
            token_bbox_px=bbox,
            max_distance_px=60.0,
        )
        refined = refine_location_cluster(
            enhanced_cluster,
            line_segments=segments,
            nearby_closed_frame=bool(frame["detected"]),
        )
        refined.update(
            {
                "cluster_index": cluster_index,
                "cluster_centroid_px": list(cluster.get("cluster_centroid_px") or []),
                "source_observation_count": int(cluster.get("observation_count") or 0),
                "confirmation_pass_count": pass_count,
                "confirmation_observation_count": added_count,
                "effective_observation_count": int(enhanced_cluster.get("observation_count") or 0),
                "local_line_segment_count": len(segments),
                "closed_frame_context": frame,
            }
        )
        results.append(refined)

    role_counts = {
        "LINEAR_DIMENSION": sum(1 for item in results if item["role"] == "LINEAR_DIMENSION"),
        "SECTION_MEASURE": sum(1 for item in results if item["role"] == "SECTION_MEASURE"),
        "UNRESOLVED": sum(1 for item in results if item["role"] == "UNRESOLVED"),
    }
    consensus_confirmed_count = sum(1 for item in results if item.get("consensus", {}).get("confirmed") is True)

    output = {
        "schema": "CEW_CAL01_SEMANTIC_ROLE_REPLAY_v2",
        "program": "CEW-CAL-01",
        "source": dict(oriented["source"]),
        "oriented_discovery_digest": oriented["oriented_discovery_digest"],
        "location_cluster_count": len(clusters),
        "confirmation_strategy": {
            "scope": "OBSERVED_TILE_ROTATION_PAIRS_ONLY",
            "psm": _CONFIRMATION_PSM,
            "preprocess_modes": list(_CONFIRMATION_MODES),
            "no_global_search_expansion": True,
        },
        "confirmation_pass_count": total_confirmation_passes,
        "confirmation_observation_count": total_confirmation_observations,
        "consensus_confirmed_count": consensus_confirmed_count,
        "role_counts": role_counts,
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "tav02s_evidence_loaded": False,
        "results": results,
        "authority": dict(AUTHORITY_CLOSED),
    }
    digest_payload = dict(output)
    output["semantic_replay_digest"] = _canonical_digest(digest_payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "semantic-role-replay.json").write_text(
        json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--oriented-discovery", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = build_semantic_role_replay(
        image_path=Path(args.image),
        oriented_discovery_path=Path(args.oriented_discovery),
        output_dir=Path(args.output_dir),
    )
    print(json.dumps({
        "location_cluster_count": result["location_cluster_count"],
        "confirmation_pass_count": result["confirmation_pass_count"],
        "confirmation_observation_count": result["confirmation_observation_count"],
        "consensus_confirmed_count": result["consensus_confirmed_count"],
        "role_counts": result["role_counts"],
        "semantic_replay_digest": result["semantic_replay_digest"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
