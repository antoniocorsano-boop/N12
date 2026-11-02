from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from experiments.cew_cal01.anchor_discovery import normalize_dimension_text, proposal_from_ocr_token
from experiments.cew_cal01.exact_source import AUTHORITY_CLOSED, _canonical_digest, _dimension_geometry_cv2
from experiments.cew_cal01.oriented_discovery import _map_oriented_bbox_to_page, _rotate_image
from experiments.cew_cal01.perimeter_dimension import (
    INNER_OVERLAP_FRACTION,
    OCR_PREPROCESS_MODES,
    OCR_ROTATIONS,
    OCR_SCALE,
    OUTER_MARGIN_FRACTION,
    _normalize_image_for_plan_detection,
    _normalized_bbox_to_source,
    _prepare_ocr_variant,
    _run_numeric_tesseract,
    build_perimeter_bands,
    detect_structural_plan_envelope,
)


_SOURCE_ORDER = {"TAV-01S": 0, "TAV-02S": 1}


def classify_structural_grid_observations(observations: Iterable[dict[str, Any]]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for raw in observations:
        observation = dict(raw)
        geometry = observation.get("geometry") or {}
        if geometry.get("geometrically_bound") is True and geometry.get("geometry_role") == "DIMENSION_LINE_WITH_TWO_REFERENCES":
            observation["semantic_role"] = "STRUCTURAL_GRID_LINEAR_DIMENSION_CANDIDATE"
            observation["primary_visual_validation_required"] = True
            observation["fit_eligible"] = False
            observation["metric_anchor_promoted"] = False
            candidates.append(observation)
        else:
            observation["semantic_role"] = "REJECTED_NUMERIC_OBSERVATION"
            observation["fit_eligible"] = False
            observation["metric_anchor_promoted"] = False
            rejected.append(observation)
    candidates.sort(key=lambda row: str(row.get("observation_id") or ""))
    rejected.sort(key=lambda row: str(row.get("observation_id") or ""))
    return {
        "candidate_count": len(candidates),
        "candidates": candidates,
        "rejected_observation_count": len(rejected),
        "rejected_observations": rejected,
        "status": "STRUCTURAL_GRID_DIMENSION_CHAINS_OBSERVED" if candidates else "STRUCTURAL_GRID_DIMENSION_CHAINS_NOT_OBSERVED",
        "primary_anchor_count": 0,
    }


def _source_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    source_id = str((row.get("source") or {}).get("source_id") or "")
    return (_SOURCE_ORDER.get(source_id, 1000), source_id)


def build_cross_sheet_summary(discoveries: Iterable[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted((dict(row) for row in discoveries), key=_source_sort_key)
    sources = [
        {
            "source_id": str((row.get("source") or {}).get("source_id") or ""),
            "sha256": str((row.get("source") or {}).get("sha256") or ""),
            "candidate_count": int(row.get("candidate_count") or 0),
            "discovery_digest": str(row.get("discovery_digest") or ""),
        }
        for row in ordered
    ]
    summary = {
        "schema": "CEW_CAL01_STRUCTURAL_GRID_CROSS_SHEET_SUMMARY_v1",
        "program": "CEW-CAL-01",
        "source_order": [row["source_id"] for row in sources],
        "sources": sources,
        "cross_sheet_relation_count": 0,
        "cross_sheet_matching_status": "PENDING_HUMAN_VALIDATION",
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    summary["cross_sheet_digest"] = _canonical_digest(summary)
    return summary


def _write_review_overlay(*, gray: Any, discovery: dict[str, Any], output_path: Path) -> None:
    import cv2

    canvas = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    source_id = str((discovery.get("source") or {}).get("source_id") or "SOURCE")
    for row in discovery.get("bands", []):
        bbox = [int(round(value)) for value in row.get("source_bbox_px", [])]
        if len(bbox) == 4:
            cv2.rectangle(canvas, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (160, 160, 160), 2)
    for row in discovery.get("candidates", []):
        bbox = [int(round(value)) for value in row.get("bbox_px", [])]
        if len(bbox) != 4:
            continue
        cv2.rectangle(canvas, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 0), 5)
        label = f"{source_id} {row.get('normalized_metric_text', '')}"
        cv2.putText(canvas, label, (bbox[0], max(30, bbox[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), canvas):
        raise RuntimeError("CAL01_STRUCTURAL_GRID_OVERLAY_WRITE_FAILED")


def discover_structural_grid_dimensions(*, image_path: Path, source_record: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    import cv2

    source_id = str(source_record.get("source_id") or "")
    source_sha256 = str(source_record.get("sha256") or "")
    raster = source_record.get("raster") or {}
    if not source_id or len(source_sha256) != 64:
        raise ValueError("CAL01_STRUCTURAL_GRID_SOURCE_RECORD_INVALID")

    source_gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if source_gray is None:
        raise RuntimeError(f"CAL01_STRUCTURAL_GRID_RASTER_UNREADABLE:{source_id}")
    source_height, source_width = source_gray.shape[:2]
    if source_width != int(raster.get("width_px") or 0) or source_height != int(raster.get("height_px") or 0):
        raise RuntimeError(f"CAL01_STRUCTURAL_GRID_RASTER_FRAME_DRIFT:{source_id}")

    normalized, frame = _normalize_image_for_plan_detection(source_gray)
    normalized_height, normalized_width = normalized.shape[:2]
    envelope = detect_structural_plan_envelope(source_gray)
    envelope_bbox = [int(value) for value in envelope["envelope_bbox_normalized_px"]]
    outer_margin = max(1, int(round(normalized_height * OUTER_MARGIN_FRACTION)))
    inner_overlap = max(1, int(round(normalized_height * INNER_OVERLAP_FRACTION)))
    bands = build_perimeter_bands(
        envelope_bbox,
        page_width=normalized_width,
        page_height=normalized_height,
        outer_margin_px=outer_margin,
        inner_overlap_px=inner_overlap,
    )
    for band in bands:
        band["source_bbox_px"] = _normalized_bbox_to_source([float(v) for v in band["bbox_px"]], frame)

    by_key: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    support: dict[tuple[str, str, int, int], set[tuple[str, int]]] = {}
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
                            "source_id": source_id,
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
                    support.setdefault(key, set()).add((preprocess_mode, rotation))
                    current = by_key.get(key)
                    if current is None or float(proposal.get("ocr_confidence") or -1.0) > float(current.get("ocr_confidence") or -1.0):
                        by_key[key] = proposal

    observations: list[dict[str, Any]] = []
    for key, proposal in sorted(by_key.items(), key=lambda item: item[0]):
        proposal = dict(proposal)
        families = sorted([list(value) for value in support.get(key, set())])
        proposal["supporting_ocr_families"] = families
        proposal["observation_id"] = f"{source_id}:{key[0]}:{key[1]}:{key[2]}:{key[3]}"
        observations.append(proposal)

    classified = classify_structural_grid_observations(observations)
    result = {
        "schema": "CEW_CAL01_STRUCTURAL_GRID_DIMENSION_DISCOVERY_v1",
        "program": "CEW-CAL-01",
        "source": {
            "source_id": source_id,
            "sha256": source_sha256,
            "path": str(source_record.get("path") or ""),
            "source_commit": str(source_record.get("source_commit") or ""),
        },
        "raster": {
            "path": image_path.name,
            "width_px": source_width,
            "height_px": source_height,
            "dpi": int(raster.get("dpi") or 300),
            "pixel_sha256": str(raster.get("pixel_sha256") or ""),
        },
        "plan_envelope": envelope,
        "bands": bands,
        "ocr_pass_count": ocr_pass_count,
        "numeric_observation_count": len(observations),
        "candidate_count": classified["candidate_count"],
        "candidates": classified["candidates"],
        "rejected_observation_count": classified["rejected_observation_count"],
        "rejected_observations": classified["rejected_observations"],
        "status": classified["status"],
        "primary_anchor_count": 0,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["discovery_digest"] = _canonical_digest(result)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "structural-grid-dimension-discovery.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_review_overlay(gray=source_gray, discovery=result, output_path=output_dir / "structural-grid-review-overlay.png")
    return result


def run_multi_source_discovery(*, source_manifest_path: Path, raster_root: Path, output_dir: Path) -> dict[str, Any]:
    manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    discoveries: list[dict[str, Any]] = []
    for source in manifest.get("sources", []):
        source_id = str(source.get("source_id") or "")
        raster_path = raster_root / str((source.get("raster") or {}).get("path") or "")
        discoveries.append(
            discover_structural_grid_dimensions(
                image_path=raster_path,
                source_record=source,
                output_dir=output_dir / source_id,
            )
        )
    summary = build_cross_sheet_summary(discoveries)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "structural-grid-cross-sheet-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover CEW-CAL-01 structural-grid perimeter dimension chains")
    parser.add_argument("--source-manifest", required=True)
    parser.add_argument("--raster-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    summary = run_multi_source_discovery(
        source_manifest_path=Path(args.source_manifest),
        raster_root=Path(args.raster_root),
        output_dir=Path(args.output_dir),
    )
    print(json.dumps({"source_order": summary["source_order"], "cross_sheet_digest": summary["cross_sheet_digest"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
