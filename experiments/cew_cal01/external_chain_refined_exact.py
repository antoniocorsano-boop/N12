from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from experiments.cew_cal01.exact_source import AUTHORITY_CLOSED, _canonical_digest
from experiments.cew_cal01.external_chain_postprocess import SIDE_ORDER, _normalize_raster, _write_overlay
from experiments.cew_cal01.external_chain_refinement import (
    _cluster_positions,
    _horizontal,
    _merge_axis_segments,
    _side_plausible,
    _supporting_observations,
    _vertical,
    build_refined_external_chains,
)


_LONGITUDINAL_EXTENSION_FRACTION = 0.15
_PIXEL_TICK_MIN_RUN_PX = 30
_PIXEL_ENDPOINT_MIN_RUN_PX = 4
_PIXEL_ENDPOINT_DISTANCE_PX = 50.0
_SYNTHETIC_TICK_HALF_LENGTH_PX = 30.0


def _expanded_band_bbox(
    *,
    side: str,
    bbox: Sequence[float],
    plan_bbox: Sequence[float],
    image_width: int,
    image_height: int,
) -> list[int]:
    left, top, right, bottom = [int(round(float(value))) for value in bbox]
    plan_left, plan_top, plan_right, plan_bottom = [int(round(float(value))) for value in plan_bbox]
    if side in {"TOP", "BOTTOM"}:
        extension = int(round((plan_right - plan_left) * _LONGITUDINAL_EXTENSION_FRACTION))
        return [max(0, left - extension), top, min(image_width, right + extension), bottom]
    extension = int(round((plan_bottom - plan_top) * _LONGITUDINAL_EXTENSION_FRACTION))
    return [left, max(0, top - extension), right, min(image_height, bottom + extension)]


def _extract_hough_segments(normalized_gray: Any, bbox: Sequence[int]) -> list[tuple[float, float, float, float]]:
    import cv2
    import numpy as np

    left, top, right, bottom = [int(value) for value in bbox]
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
        np.pi / 360.0,
        threshold=30,
        minLineLength=30,
        maxLineGap=20,
    )
    result: list[tuple[float, float, float, float]] = []
    if lines is None:
        return result
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        result.append(
            (
                float(x1 + left),
                float(y1 + top),
                float(x2 + left),
                float(y2 + top),
            )
        )
    result.sort()
    return result


def _pixel_crossing_extent(
    *,
    binary: Any,
    horizontal_carrier: bool,
    carrier_axis: float,
    position: float,
    along_radius_px: int = 3,
    cross_radius_px: int = 250,
) -> int | None:
    import numpy as np

    axis = int(round(carrier_axis))
    along = int(round(position))
    if horizontal_carrier:
        y0 = max(0, axis - cross_radius_px)
        y1 = min(binary.shape[0], axis + cross_radius_px + 1)
        x0 = max(0, along - along_radius_px)
        x1 = min(binary.shape[1], along + along_radius_px + 1)
        projection = (binary[y0:y1, x0:x1] > 0).any(axis=1)
        center = axis - y0
    else:
        y0 = max(0, along - along_radius_px)
        y1 = min(binary.shape[0], along + along_radius_px + 1)
        x0 = max(0, axis - cross_radius_px)
        x1 = min(binary.shape[1], axis + cross_radius_px + 1)
        projection = (binary[y0:y1, x0:x1] > 0).any(axis=0)
        center = axis - x0

    indexes = np.where(projection)[0]
    if len(indexes) == 0:
        return None
    runs: list[tuple[int, int]] = []
    start = previous = int(indexes[0])
    for raw_index in indexes[1:]:
        index = int(raw_index)
        if index <= previous + 2:
            previous = index
        else:
            runs.append((start, previous))
            start = previous = index
    runs.append((start, previous))
    crossing = [run for run in runs if run[0] - 5 <= center <= run[1] + 5]
    if not crossing:
        return None
    selected = min(crossing, key=lambda run: abs(((run[0] + run[1]) / 2.0) - center))
    return int(selected[1] - selected[0] + 1)


def _filtered_tick_segments(
    *,
    side: str,
    line_segments: list[tuple[float, float, float, float]],
    binary: Any,
    plan_bbox: Sequence[float],
    observations: list[dict[str, Any]],
) -> tuple[list[tuple[float, float, float, float]], list[dict[str, Any]]]:
    horizontal = side in {"TOP", "BOTTOM"}
    synthetic: list[tuple[float, float, float, float]] = []
    carrier_diagnostics: list[dict[str, Any]] = []

    for carrier in _merge_axis_segments(
        side=side,
        axis_segments=line_segments,
        plan_envelope_bbox=plan_bbox,
    ):
        if not _side_plausible(side=side, carrier_axis=carrier["axis"], plan_envelope_bbox=plan_bbox):
            continue
        support = _supporting_observations(side=side, carrier=carrier, observations=observations)
        if not support:
            continue
        accepted_positions: list[float] = []
        for line in line_segments:
            if horizontal:
                is_tick, cross_start, cross_end, position = _vertical(line)
            else:
                is_tick, cross_start, cross_end, position = _horizontal(line)
            if not is_tick:
                continue
            if not (carrier["start"] - 12.0 <= position <= carrier["end"] + 12.0):
                continue
            if not (cross_start - 6.0 <= carrier["axis"] <= cross_end + 6.0):
                continue
            pixel_run = _pixel_crossing_extent(
                binary=binary,
                horizontal_carrier=horizontal,
                carrier_axis=carrier["axis"],
                position=position,
            )
            if pixel_run is None:
                continue
            endpoint_distance = min(
                abs(position - carrier["start"]),
                abs(position - carrier["end"]),
            )
            if pixel_run >= _PIXEL_TICK_MIN_RUN_PX or (
                pixel_run >= _PIXEL_ENDPOINT_MIN_RUN_PX
                and endpoint_distance <= _PIXEL_ENDPOINT_DISTANCE_PX
            ):
                accepted_positions.append(float(position))

        clustered = _cluster_positions(accepted_positions)
        for position in clustered:
            axis = float(carrier["axis"])
            if horizontal:
                synthetic.append(
                    (
                        float(position),
                        axis - _SYNTHETIC_TICK_HALF_LENGTH_PX,
                        float(position),
                        axis + _SYNTHETIC_TICK_HALF_LENGTH_PX,
                    )
                )
            else:
                synthetic.append(
                    (
                        axis - _SYNTHETIC_TICK_HALF_LENGTH_PX,
                        float(position),
                        axis + _SYNTHETIC_TICK_HALF_LENGTH_PX,
                        float(position),
                    )
                )
        carrier_diagnostics.append(
            {
                "carrier_axis_px": float(carrier["axis"]),
                "carrier_start_px": float(carrier["start"]),
                "carrier_end_px": float(carrier["end"]),
                "supporting_observation_ids": [row[2] for row in support],
                "pixel_qualified_tick_positions_px": [float(value) for value in clustered],
            }
        )

    synthetic.sort()
    carrier_diagnostics.sort(key=lambda row: (row["carrier_axis_px"], row["carrier_start_px"]))
    return synthetic, carrier_diagnostics


def run_refined_exact_source(*, discovery_path: Path, image_path: Path, output_dir: Path) -> dict[str, Any]:
    import cv2

    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    source_gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if source_gray is None:
        raise RuntimeError("CAL01_REFINED_EXTERNAL_CHAIN_RASTER_UNREADABLE")
    transform = str(((discovery.get("plan_envelope") or {}).get("normalization") or {}).get("transform") or "IDENTITY")
    normalized = _normalize_raster(source_gray, transform)
    _, binary = cv2.threshold(normalized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    plan_bbox = list((discovery.get("plan_envelope") or {}).get("envelope_bbox_normalized_px") or [])
    if len(plan_bbox) != 4:
        raise ValueError("CAL01_REFINED_EXTERNAL_CHAIN_PLAN_ENVELOPE_REQUIRED")
    observations = [dict(row) for row in discovery.get("candidates", [])]
    observations.extend(dict(row) for row in discovery.get("rejected_observations", []))
    observations.sort(key=lambda row: str(row.get("observation_id") or ""))

    bands = {str(row.get("side") or "").upper(): row for row in discovery.get("bands", [])}
    if list(bands) != SIDE_ORDER:
        raise ValueError("CAL01_REFINED_EXTERNAL_CHAIN_BAND_ORDER_DRIFT")

    side_results: list[dict[str, Any]] = []
    extraction: dict[str, Any] = {}
    for side in SIDE_ORDER:
        band = bands[side]
        expanded_bbox = _expanded_band_bbox(
            side=side,
            bbox=band.get("bbox_px") or [],
            plan_bbox=plan_bbox,
            image_width=normalized.shape[1],
            image_height=normalized.shape[0],
        )
        line_segments = _extract_hough_segments(normalized, expanded_bbox)
        tick_segments, carrier_diagnostics = _filtered_tick_segments(
            side=side,
            line_segments=line_segments,
            binary=binary,
            plan_bbox=plan_bbox,
            observations=observations,
        )
        side_observations = [
            row for row in observations if str(row.get("search_band") or "").upper() == side
        ]
        refined = build_refined_external_chains(
            side=side,
            axis_segments=line_segments,
            tick_segments=tick_segments,
            observations=side_observations,
            plan_envelope_bbox=plan_bbox,
        )
        side_results.append(refined)
        extraction[side] = {
            "expanded_band_bbox_px": expanded_bbox,
            "hough_segment_count": len(line_segments),
            "synthetic_tick_segment_count": len(tick_segments),
            "carrier_diagnostics": carrier_diagnostics,
        }

    source = dict(discovery.get("source") or {})
    result = {
        "schema": "CEW_CAL01_REFINED_EXTERNAL_DIMENSION_CHAIN_EXACT_v1",
        "program": "CEW-CAL-01",
        "source": source,
        "legacy_discovery_digest": str(discovery.get("discovery_digest") or ""),
        "legacy_candidate_count": int(discovery.get("candidate_count") or 0),
        "legacy_numeric_observation_count": int(discovery.get("numeric_observation_count") or 0),
        "side_order": list(SIDE_ORDER),
        "sides": side_results,
        "extraction": extraction,
        "refined_external_chain_count": sum(int(row.get("chain_count") or 0) for row in side_results),
        "refined_external_chain_member_count": sum(int(row.get("member_observation_count") or 0) for row in side_results),
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["refined_external_chain_digest"] = _canonical_digest(result)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "refined-external-dimension-chain.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_overlay(
        normalized_gray=normalized,
        result={"sides": side_results},
        observations=observations,
        output_path=output_dir / "refined-external-dimension-chain-overlay.png",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Refine exact-source external dimension chains from frozen structural-grid rasters")
    parser.add_argument("--discovery", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run_refined_exact_source(
        discovery_path=Path(args.discovery),
        image_path=Path(args.image),
        output_dir=Path(args.output_dir),
    )
    print(
        json.dumps(
            {
                "source_id": result["source"]["source_id"],
                "refined_external_chain_count": result["refined_external_chain_count"],
                "refined_external_chain_member_count": result["refined_external_chain_member_count"],
                "refined_external_chain_digest": result["refined_external_chain_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
