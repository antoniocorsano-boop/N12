from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from experiments.cew_cal01.exact_source import AUTHORITY_CLOSED, _canonical_digest
from experiments.cew_cal01.external_dimension_chain import detect_external_dimension_chains


SIDE_ORDER = ["TOP", "RIGHT", "BOTTOM", "LEFT"]


def build_external_chain_result(
    *,
    discovery: dict[str, Any],
    line_segments_by_side: Mapping[str, Sequence[Sequence[float]]],
) -> dict[str, Any]:
    source = dict(discovery.get("source") or {})
    source_id = str(source.get("source_id") or "")
    source_sha256 = str(source.get("sha256") or "")
    if not source_id or len(source_sha256) != 64:
        raise ValueError("CAL01_EXTERNAL_CHAIN_SOURCE_INVALID")

    plan_bbox = list((discovery.get("plan_envelope") or {}).get("envelope_bbox_normalized_px") or [])
    if len(plan_bbox) != 4:
        raise ValueError("CAL01_EXTERNAL_CHAIN_PLAN_ENVELOPE_REQUIRED")

    observations = [dict(row) for row in discovery.get("candidates", [])]
    observations.extend(dict(row) for row in discovery.get("rejected_observations", []))
    observations.sort(key=lambda row: str(row.get("observation_id") or ""))

    bands = discovery.get("bands") or []
    observed_side_order = [str(row.get("side") or "").upper() for row in bands]
    if observed_side_order != SIDE_ORDER:
        raise ValueError("CAL01_EXTERNAL_CHAIN_BAND_ORDER_DRIFT")

    side_results: list[dict[str, Any]] = []
    for side in SIDE_ORDER:
        side_observations = [row for row in observations if str(row.get("search_band") or "").upper() == side]
        side_result = detect_external_dimension_chains(
            side=side,
            line_segments=line_segments_by_side.get(side, []),
            observations=side_observations,
            plan_envelope_bbox=plan_bbox,
        )
        side_results.append(side_result)

    result = {
        "schema": "CEW_CAL01_EXTERNAL_DIMENSION_CHAIN_POSTPROCESS_v1",
        "program": "CEW-CAL-01",
        "source": source,
        "legacy_discovery_digest": str(discovery.get("discovery_digest") or ""),
        "legacy_candidate_count": int(discovery.get("candidate_count") or 0),
        "legacy_numeric_observation_count": int(discovery.get("numeric_observation_count") or 0),
        "side_order": list(SIDE_ORDER),
        "sides": side_results,
        "external_chain_count": sum(int(row.get("chain_count") or 0) for row in side_results),
        "external_chain_member_count": sum(int(row.get("member_observation_count") or 0) for row in side_results),
        "external_chain_unresolved_observation_ids": sorted(
            {
                observation_id
                for row in side_results
                for observation_id in row.get("unresolved_observation_ids", [])
            }
        ),
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["external_chain_digest"] = _canonical_digest(result)
    return result


def _normalize_raster(gray: Any, transform: str) -> Any:
    import cv2

    mode = str(transform or "IDENTITY")
    if mode == "IDENTITY":
        return gray
    if mode == "ROTATE_90_COUNTERCLOCKWISE":
        return cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if mode == "ROTATE_90_CLOCKWISE":
        return cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    if mode == "ROTATE_180":
        return cv2.rotate(gray, cv2.ROTATE_180)
    raise ValueError(f"CAL01_EXTERNAL_CHAIN_NORMALIZATION_UNSUPPORTED:{mode}")


def _extract_band_line_segments(normalized_gray: Any, bbox: Sequence[float]) -> list[tuple[float, float, float, float]]:
    import cv2
    import numpy as np

    if len(bbox) != 4:
        raise ValueError("CAL01_EXTERNAL_CHAIN_BAND_BBOX_INVALID")
    left, top, right, bottom = [int(round(float(value))) for value in bbox]
    if right <= left or bottom <= top:
        raise ValueError("CAL01_EXTERNAL_CHAIN_BAND_BBOX_INVALID")
    crop = normalized_gray[top:bottom, left:right]
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
        threshold=45,
        minLineLength=40,
        maxLineGap=15,
    )
    if lines is None:
        return []
    result: list[tuple[float, float, float, float]] = []
    for row in lines.reshape(-1, 4):
        x1, y1, x2, y2 = [float(value) for value in row]
        result.append((x1 + left, y1 + top, x2 + left, y2 + top))
    result.sort()
    return result


def _write_overlay(*, normalized_gray: Any, result: dict[str, Any], observations: list[dict[str, Any]], output_path: Path) -> None:
    import cv2

    canvas = cv2.cvtColor(normalized_gray, cv2.COLOR_GRAY2BGR)
    observation_by_id = {str(row.get("observation_id") or ""): row for row in observations}
    for side in result.get("sides", []):
        for chain in side.get("chains", []):
            axis = float(chain["carrier_axis_px"])
            start = float(chain["carrier_start_px"])
            end = float(chain["carrier_end_px"])
            if chain.get("orientation") == "HORIZONTAL":
                a = (int(round(start)), int(round(axis)))
                b = (int(round(end)), int(round(axis)))
                cv2.line(canvas, a, b, (0, 0, 0), 4)
                for tick in chain.get("tick_positions_px", []):
                    x = int(round(float(tick)))
                    y = int(round(axis))
                    cv2.line(canvas, (x, y - 16), (x, y + 16), (0, 0, 0), 3)
            else:
                a = (int(round(axis)), int(round(start)))
                b = (int(round(axis)), int(round(end)))
                cv2.line(canvas, a, b, (0, 0, 0), 4)
                for tick in chain.get("tick_positions_px", []):
                    x = int(round(axis))
                    y = int(round(float(tick)))
                    cv2.line(canvas, (x - 16, y), (x + 16, y), (0, 0, 0), 3)
            for observation_id in chain.get("member_observation_ids", []):
                row = observation_by_id.get(str(observation_id))
                bbox = list((row or {}).get("bbox_normalized_px") or [])
                if len(bbox) == 4:
                    left, top, right, bottom = [int(round(float(value))) for value in bbox]
                    cv2.rectangle(canvas, (left, top), (right, bottom), (0, 0, 0), 3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), canvas):
        raise RuntimeError("CAL01_EXTERNAL_CHAIN_OVERLAY_WRITE_FAILED")


def run_exact_source_postprocess(*, discovery_path: Path, image_path: Path, output_dir: Path) -> dict[str, Any]:
    import cv2

    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    source_gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if source_gray is None:
        raise RuntimeError("CAL01_EXTERNAL_CHAIN_RASTER_UNREADABLE")
    transform = str(((discovery.get("plan_envelope") or {}).get("normalization") or {}).get("transform") or "IDENTITY")
    normalized = _normalize_raster(source_gray, transform)

    line_segments_by_side: dict[str, list[tuple[float, float, float, float]]] = {}
    for band in discovery.get("bands", []):
        side = str(band.get("side") or "").upper()
        line_segments_by_side[side] = _extract_band_line_segments(normalized, band.get("bbox_px") or [])

    result = build_external_chain_result(discovery=discovery, line_segments_by_side=line_segments_by_side)
    result["line_segment_counts"] = {
        side: len(line_segments_by_side.get(side, [])) for side in SIDE_ORDER
    }
    result["external_chain_digest"] = _canonical_digest({key: value for key, value in result.items() if key != "external_chain_digest"})

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "external-dimension-chain-postprocess.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    observations = [dict(row) for row in discovery.get("candidates", [])]
    observations.extend(dict(row) for row in discovery.get("rejected_observations", []))
    _write_overlay(
        normalized_gray=normalized,
        result=result,
        observations=observations,
        output_path=output_dir / "external-dimension-chain-overlay.png",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-process structural-grid discovery into external dimension chains")
    parser.add_argument("--discovery", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run_exact_source_postprocess(
        discovery_path=Path(args.discovery),
        image_path=Path(args.image),
        output_dir=Path(args.output_dir),
    )
    print(
        json.dumps(
            {
                "source_id": result["source"]["source_id"],
                "external_chain_count": result["external_chain_count"],
                "external_chain_member_count": result["external_chain_member_count"],
                "external_chain_digest": result["external_chain_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
