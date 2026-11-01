from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.cew_cal01.exact_source import SOURCE_SHA256, _canonical_digest
from experiments.cew_cal01.role_verification import detect_nearby_closed_frame
from experiments.cew_cal01.semantic_replay import refine_location_cluster


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


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
    for cluster_index, cluster in enumerate(clusters):
        representative = cluster.get("representative") or {}
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
            cluster,
            line_segments=segments,
            nearby_closed_frame=bool(frame["detected"]),
        )
        refined.update(
            {
                "cluster_index": cluster_index,
                "cluster_centroid_px": list(cluster.get("cluster_centroid_px") or []),
                "source_observation_count": int(cluster.get("observation_count") or 0),
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
        "schema": "CEW_CAL01_SEMANTIC_ROLE_REPLAY_v1",
        "program": "CEW-CAL-01",
        "source": dict(oriented["source"]),
        "oriented_discovery_digest": oriented["oriented_discovery_digest"],
        "location_cluster_count": len(clusters),
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
        "consensus_confirmed_count": result["consensus_confirmed_count"],
        "role_counts": result["role_counts"],
        "semantic_replay_digest": result["semantic_replay_digest"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
