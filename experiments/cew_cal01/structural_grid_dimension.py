from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from experiments.cew_cal01.anchor_discovery import normalize_dimension_text, proposal_from_ocr_token
from experiments.cew_cal01.exact_source import AUTHORITY_CLOSED, _canonical_digest, _dimension_geometry_cv2
from experiments.cew_cal01.oriented_discovery import _map_oriented_bbox_to_page, _rotate_image
from experiments.cew_cal01.perimeter_dimension import (
    DETECTION_DILATION_KERNEL,
    DETECTION_TARGET_WIDTH_PX,
    DETECTION_THRESHOLD,
    INNER_OVERLAP_FRACTION,
    MIN_PLAN_HEIGHT_FRACTION,
    MIN_PLAN_WIDTH_FRACTION,
    OCR_PREPROCESS_MODES,
    OCR_ROTATIONS,
    OCR_SCALE,
    OUTER_MARGIN_FRACTION,
    _normalize_image_for_plan_detection,
    _normalized_bbox_to_source,
    _prepare_ocr_variant,
    _run_numeric_tesseract,
    _select_structural_envelope_bbox,
    build_perimeter_bands,
)


_SOURCE_ORDER = {"TAV-01S": 0, "TAV-02S": 1}
_FRAGMENT_CORE_INK_FRACTIONS = (0.002, 0.001, 0.0005, 0.0002, 0.0001, 0.0)


def _component_bbox(component: dict[str, Any]) -> list[int] | None:
    bbox = [int(value) for value in component.get("bbox_px", [])]
    if len(bbox) != 4:
        return None
    left, top, right, bottom = bbox
    if right <= left or bottom <= top:
        return None
    return bbox


def _axis_aligned_neighbors(a: list[int], b: list[int], *, join_gap_px: int) -> bool:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    x_gap = max(ax0 - bx1, bx0 - ax1, 0)
    y_gap = max(ay0 - by1, by0 - ay1, 0)
    x_overlap = min(ax1, bx1) - max(ax0, bx0)
    y_overlap = min(ay1, by1) - max(ay0, by0)
    return (x_gap <= join_gap_px and y_overlap > 0) or (y_gap <= join_gap_px and x_overlap > 0)


def select_structural_grid_envelope_bbox(
    components: list[dict[str, Any]],
    *,
    page_width: int,
    page_height: int,
    join_gap_px: int | None = None,
    min_width_fraction: float = MIN_PLAN_WIDTH_FRACTION,
    min_height_fraction: float = MIN_PLAN_HEIGHT_FRACTION,
) -> dict[str, Any]:
    """Select a structural-plan envelope while allowing an aligned fragmented grid.

    Connected-component bboxes are first clipped to the normalized page frame
    because scale-back rounding can exceed the source boundary by a few pixels.
    If no single component qualifies, horizontally/vertically aligned fragments
    are grouped. Fragment grouping is seeded from progressively weaker ink-area
    cores so tiny page marks cannot form a transitive bridge from the structural
    grid into a title block; the unrestricted grouping remains the final fallback.
    """

    if page_width <= 0 or page_height <= 0:
        raise ValueError("CAL01_PLAN_FRAME_INVALID")
    if join_gap_px is None:
        join_gap_px = max(12, int(round(min(page_width, page_height) * 0.035)))
    if join_gap_px < 0:
        raise ValueError("CAL01_STRUCTURAL_GRID_JOIN_GAP_INVALID")

    bounded: list[dict[str, Any]] = []
    for component in components:
        bbox = _component_bbox(component)
        if bbox is None:
            continue
        left, top, right, bottom = bbox
        clipped = [
            max(0, min(page_width, left)),
            max(0, min(page_height, top)),
            max(0, min(page_width, right)),
            max(0, min(page_height, bottom)),
        ]
        if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
            continue
        bounded.append({**component, "bbox_px": clipped})
    if not bounded:
        raise RuntimeError("CAL01_PLAN_ENVELOPE_NOT_FOUND")

    try:
        bbox = _select_structural_envelope_bbox(
            bounded,
            page_width=page_width,
            page_height=page_height,
            min_width_fraction=min_width_fraction,
            min_height_fraction=min_height_fraction,
        )
        return {
            "bbox_px": bbox,
            "selection_mode": "SINGLE_COMPONENT",
            "member_count": 1,
            "join_gap_px": join_gap_px,
            "core_min_ink_fraction": None,
        }
    except RuntimeError as exc:
        if str(exc) != "CAL01_PLAN_ENVELOPE_NOT_FOUND":
            raise

    page_area = float(page_width * page_height)
    for core_min_ink_fraction in _FRAGMENT_CORE_INK_FRACTIONS:
        min_ink_area = page_area * core_min_ink_fraction
        valid = [
            component
            for component in bounded
            if float(component.get("ink_area_px") or 0) >= min_ink_area
        ]
        if len(valid) < 2:
            continue

        parent = list(range(len(valid)))

        def find(index: int) -> int:
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        def union(left: int, right: int) -> None:
            root_left = find(left)
            root_right = find(right)
            if root_left != root_right:
                parent[root_right] = root_left

        for left in range(len(valid)):
            for right in range(left + 1, len(valid)):
                if _axis_aligned_neighbors(
                    valid[left]["bbox_px"],
                    valid[right]["bbox_px"],
                    join_gap_px=join_gap_px,
                ):
                    union(left, right)

        groups: dict[int, list[dict[str, Any]]] = {}
        for index, component in enumerate(valid):
            groups.setdefault(find(index), []).append(component)

        qualified: list[tuple[int, int, int, list[int]]] = []
        for members in groups.values():
            if len(members) < 2:
                continue
            left = min(row["bbox_px"][0] for row in members)
            top = min(row["bbox_px"][1] for row in members)
            right = max(row["bbox_px"][2] for row in members)
            bottom = max(row["bbox_px"][3] for row in members)
            width = right - left
            height = bottom - top
            if width < page_width * min_width_fraction or height < page_height * min_height_fraction:
                continue
            bbox_area = width * height
            ink_area = sum(int(row.get("ink_area_px") or 0) for row in members)
            qualified.append((ink_area, bbox_area, len(members), [left, top, right, bottom]))

        if not qualified:
            continue
        qualified.sort(
            key=lambda row: (row[0], row[1], row[2], -row[3][1], -row[3][0]),
            reverse=True,
        )
        _ink_area, _bbox_area, member_count, bbox = qualified[0]
        return {
            "bbox_px": bbox,
            "selection_mode": "FRAGMENT_CLUSTER",
            "member_count": member_count,
            "join_gap_px": join_gap_px,
            "core_min_ink_fraction": core_min_ink_fraction,
        }

    raise RuntimeError("CAL01_PLAN_ENVELOPE_NOT_FOUND")


def detect_structural_grid_plan_envelope(gray: Any) -> dict[str, Any]:
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

    selection = select_structural_grid_envelope_bbox(
        components,
        page_width=normalized_width,
        page_height=normalized_height,
    )
    envelope_normalized = selection["bbox_px"]
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
            "selection_mode": selection["selection_mode"],
            "selected_member_count": selection["member_count"],
            "join_gap_px": selection["join_gap_px"],
            "core_min_ink_fraction": selection["core_min_ink_fraction"],
        },
        "envelope_bbox_normalized_px": envelope_normalized,
        "envelope_bbox_source_px": envelope_source,
    }


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
    envelope = detect_structural_grid_plan_envelope(source_gray)
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
