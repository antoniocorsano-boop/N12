from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from experiments.cew_col01.number_anchor import parse_support_like_tsv
from experiments.cew_col03b.local_evidence import classify_text_relation
from experiments.cew_col03f.acquisition import (
    AUTHORITY_KEYS,
    CANDIDATE_STATES,
    EXPECTED_OCCURRENCE_IDS,
    build_primary_bridge_ledger,
    inspection_priority,
)


QUALIFIED_COL03E_SHA = "cbf57e9261228a7376df826baadc79abe2da254c"
SOURCE_CONTRACT_PATH = Path("governance/cew-b01/N12_TAV5_SOURCE_v1.json")
SOURCE_VERSION_ID = "CEW-N12-SRC-TAV05S-V2143DBCF"
PAGE_ID = "CEW-N12-PAGE-TAV05S-P001"
PAGE_TRANSFORM_ID = "CEW-N12-XFORM-TAV05S-P001"
SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
RENDER_DPI = 300
OCR_SCALE = 2.0
OCR_CONFIGURATIONS = {"PSM6": 6, "PSM11": 11}
_REQUIRED_JSON_FILENAMES = {
    "primary-bridge-evidence-ledger.json",
    "primary-bridge-inspection-queue.json",
    "primary-bridge-closure.json",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"COL03F_JSON_OBJECT_REQUIRED:{path}")
    return payload


def _normalized_bbox(box: dict[str, Any]) -> dict[str, float]:
    if not isinstance(box, dict):
        raise ValueError("COL03F_BBOX_INVALID")
    try:
        x = float(box["x"])
        y = float(box["y"])
        width = float(box["width"])
        height = float(box["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("COL03F_BBOX_INVALID") from exc
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 1.0 + 1e-12 or y + height > 1.0 + 1e-12:
        raise ValueError("COL03F_BBOX_OUT_OF_RANGE")
    return {"x": x, "y": y, "width": width, "height": height}


def bbox_to_pixels(
    box: dict[str, Any],
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    """Map a normalized source bbox to deterministic clipped page pixel bounds."""

    if width <= 0 or height <= 0:
        raise ValueError("COL03F_PAGE_DIMENSIONS_INVALID")
    normalized = _normalized_bbox(box)
    left = max(0, min(width - 1, int(round(normalized["x"] * width))))
    top = max(0, min(height - 1, int(round(normalized["y"] * height))))
    right = max(left + 1, min(width, int(round((normalized["x"] + normalized["width"]) * width))))
    bottom = max(top + 1, min(height, int(round((normalized["y"] + normalized["height"]) * height))))
    return left, top, right, bottom


def _expand_bounds(
    bounds: tuple[int, int, int, int],
    *,
    margin: int,
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    left, top, right, bottom = bounds
    return (
        max(0, left - margin),
        max(0, top - margin),
        min(width, right + margin),
        min(height, bottom + margin),
    )


def crop_specs(
    box: dict[str, Any],
    width: int,
    height: int,
) -> dict[str, tuple[int, int, int, int]]:
    """Derive nested deterministic FOOTPRINT/LOCAL/CONTEXT source regions."""

    base = bbox_to_pixels(box, width, height)
    span = max(base[2] - base[0], base[3] - base[1])
    footprint_margin = max(12, int(round(span * 0.25)))
    local_margin = max(72, int(round(span * 1.50)))
    context_margin = max(160, int(round(span * 3.00)))
    return {
        "FOOTPRINT": _expand_bounds(base, margin=footprint_margin, width=width, height=height),
        "LOCAL": _expand_bounds(base, margin=local_margin, width=width, height=height),
        "CONTEXT": _expand_bounds(base, margin=context_margin, width=width, height=height),
    }


def context_region_from_bounds(
    bounds: tuple[int, int, int, int],
    *,
    page_width: int,
    page_height: int,
) -> dict[str, float]:
    """Project exact page-pixel bounds to a normalized region for relation classification."""

    if page_width <= 0 or page_height <= 0:
        raise ValueError("COL03F_PAGE_DIMENSIONS_INVALID")
    left, top, right, bottom = bounds
    if left < 0 or top < 0 or right <= left or bottom <= top or right > page_width or bottom > page_height:
        raise ValueError("COL03F_CROP_BOUNDS_INVALID")
    return {
        "x": left / page_width,
        "y": top / page_height,
        "width": (right - left) / page_width,
        "height": (bottom - top) / page_height,
    }


def map_crop_bbox_to_page(
    *,
    token_bbox: dict[str, Any],
    crop_bounds: tuple[int, int, int, int],
    scale: float,
    page_width: int,
    page_height: int,
) -> dict[str, float]:
    """Map a token bbox from a scaled crop back to normalized primary-page coordinates."""

    if scale <= 0 or page_width <= 0 or page_height <= 0:
        raise ValueError("COL03F_COORDINATE_MAPPING_INVALID")
    try:
        tx = float(token_bbox["x"])
        ty = float(token_bbox["y"])
        tw = float(token_bbox["width"])
        th = float(token_bbox["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("COL03F_TOKEN_BBOX_INVALID") from exc
    if tx < 0 or ty < 0 or tw <= 0 or th <= 0:
        raise ValueError("COL03F_TOKEN_BBOX_INVALID")

    left, top, right, bottom = crop_bounds
    if left < 0 or top < 0 or right <= left or bottom <= top or right > page_width or bottom > page_height:
        raise ValueError("COL03F_CROP_BOUNDS_INVALID")

    abs_left = left + tx / scale
    abs_top = top + ty / scale
    abs_right = left + (tx + tw) / scale
    abs_bottom = top + (ty + th) / scale
    abs_left = min(max(abs_left, 0.0), float(page_width))
    abs_top = min(max(abs_top, 0.0), float(page_height))
    abs_right = min(max(abs_right, abs_left), float(page_width))
    abs_bottom = min(max(abs_bottom, abs_top), float(page_height))
    mapped = {
        "x": abs_left / page_width,
        "y": abs_top / page_height,
        "width": (abs_right - abs_left) / page_width,
        "height": (abs_bottom - abs_top) / page_height,
    }
    if mapped["width"] <= 0 or mapped["height"] <= 0:
        raise ValueError("COL03F_MAPPED_TOKEN_BBOX_INVALID")
    return mapped


def _anchor_sort_key(anchor: dict[str, Any]) -> tuple[float, float, str, str]:
    box = anchor.get("bbox") if isinstance(anchor, dict) else None
    if not isinstance(box, dict):
        return float("inf"), float("inf"), "", ""
    return (
        float(box.get("x") or 0.0),
        float(box.get("y") or 0.0),
        str(anchor.get("normalized_id") or ""),
        str(anchor.get("text") or ""),
    )


def normalize_targeted_anchors(
    *,
    anchors: list[dict[str, Any]],
    occurrence_id: str,
    region_class: str,
    ocr_configuration: str,
    crop_bounds: tuple[int, int, int, int],
    scale: float,
    page_width: int,
    page_height: int,
    occurrence_bbox: dict[str, Any],
    local_region: dict[str, Any],
    provenance_prefix: str,
) -> list[dict[str, Any]]:
    """Normalize targeted OCR anchors into deterministic page-provenanced observations."""

    if region_class not in {"FOOTPRINT", "LOCAL"}:
        raise ValueError("COL03F_OCR_REGION_INVALID")
    if ocr_configuration not in OCR_CONFIGURATIONS:
        raise ValueError("COL03F_OCR_CONFIGURATION_INVALID")
    if not occurrence_id or not provenance_prefix:
        raise ValueError("COL03F_OBSERVATION_PROVENANCE_INVALID")

    occurrence = _normalized_bbox(deepcopy(occurrence_bbox))
    local = _normalized_bbox(deepcopy(local_region))
    observations: list[dict[str, Any]] = []
    valid_anchors = [deepcopy(anchor) for anchor in anchors if isinstance(anchor, dict) and isinstance(anchor.get("bbox"), dict)]
    valid_anchors.sort(key=_anchor_sort_key)

    for index, anchor in enumerate(valid_anchors, start=1):
        raw_text = str(anchor.get("text") or "").strip()
        normalized_text = str(anchor.get("normalized_id") or raw_text).strip()
        if not normalized_text:
            continue
        page_bbox = map_crop_bbox_to_page(
            token_bbox=anchor["bbox"],
            crop_bounds=crop_bounds,
            scale=scale,
            page_width=page_width,
            page_height=page_height,
        )
        relation = classify_text_relation(
            occurrence_bbox=occurrence,
            text_bbox=page_bbox,
            local_region=local,
        )
        observation_id = f"{occurrence_id}:{region_class}:{ocr_configuration}:{index:03d}"
        observations.append(
            {
                "observation_id": observation_id,
                "occurrence_id": occurrence_id,
                "region_class": region_class,
                "ocr_configuration": ocr_configuration,
                "raw_text": raw_text,
                "normalized_text": normalized_text,
                "confidence": anchor.get("confidence"),
                "crop_local_bbox": deepcopy(anchor["bbox"]),
                "page_bbox": page_bbox,
                "relation": relation,
                "provenance_ref": f"{provenance_prefix}:{observation_id}",
                "exact_source_reconstructible": True,
            }
        )
    return observations


def parse_targeted_tsv(
    tsv_text: str,
    *,
    occurrence_id: str,
    region_class: str,
    ocr_configuration: str,
    crop_bounds: tuple[int, int, int, int],
    scale: float,
    page_width: int,
    page_height: int,
    occurrence_bbox: dict[str, Any],
    local_region: dict[str, Any],
    provenance_prefix: str,
) -> list[dict[str, Any]]:
    """Parse a frozen Tesseract TSV result and map numeric support-like tokens to the primary page."""

    if ocr_configuration not in OCR_CONFIGURATIONS:
        raise ValueError("COL03F_OCR_CONFIGURATION_INVALID")
    anchors = parse_support_like_tsv(tsv_text, min_confidence=25.0)
    return normalize_targeted_anchors(
        anchors=anchors,
        occurrence_id=occurrence_id,
        region_class=region_class,
        ocr_configuration=ocr_configuration,
        crop_bounds=crop_bounds,
        scale=scale,
        page_width=page_width,
        page_height=page_height,
        occurrence_bbox=occurrence_bbox,
        local_region=local_region,
        provenance_prefix=provenance_prefix,
    )


def _documentary_candidate_map(documentary_ledger: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for row in documentary_ledger.get("occurrences", []):
        if not isinstance(row, dict):
            continue
        occurrence_id = str(row.get("occurrence_id") or "")
        values = sorted(
            {
                str(hypothesis.get("candidate_value"))
                for hypothesis in (row.get("hypotheses") or [])
                if isinstance(hypothesis, dict) and str(hypothesis.get("candidate_value") or "").isdigit()
            },
            key=int,
        )
        if values:
            result[occurrence_id] = values
    return result


def _authority_closed(row: dict[str, Any]) -> bool:
    return (
        row.get("identity_promoted") is False
        and row.get("historical_identity_positive_evidence_used") is False
        and all(row.get(key) is False for key in AUTHORITY_KEYS)
    )


def build_inspection_queue(
    ledger: dict[str, Any],
    *,
    predecessor_sha: str,
) -> dict[str, Any]:
    rows = ledger.get("occurrences")
    order = ledger.get("inspection_order")
    if not isinstance(rows, list) or len(rows) != 22:
        raise ValueError("COL03F_QUEUE_OCCURRENCE_COUNT_INVALID")
    if not isinstance(order, list) or order != ["COL-OCC-0001", "COL-OCC-0015", *[oid for oid in EXPECTED_OCCURRENCE_IDS if oid not in {"COL-OCC-0001", "COL-OCC-0015"}]]:
        raise ValueError("COL03F_QUEUE_ORDER_INVALID")
    rows_by_id = {str(row.get("occurrence_id") or ""): row for row in rows if isinstance(row, dict)}
    if set(rows_by_id) != set(EXPECTED_OCCURRENCE_IDS):
        raise ValueError("COL03F_QUEUE_OCCURRENCE_SET_INVALID")
    if any(not _authority_closed(row) for row in rows_by_id.values()):
        raise ValueError("COL03F_QUEUE_AUTHORITY_NOT_CLOSED")

    entries = []
    for queue_index, occurrence_id in enumerate(order, start=1):
        row = rows_by_id[occurrence_id]
        manifest = row.get("crop_manifest") or {}
        entries.append(
            {
                "queue_index": queue_index,
                "occurrence_id": occurrence_id,
                "acquisition_state": row.get("acquisition_state"),
                "candidate_values": list(row.get("candidate_values") or []),
                "source_only_path": manifest.get("source_only_path"),
                "source_only_sha256": manifest.get("source_only_sha256"),
                "target_overlay_path": manifest.get("target_overlay_path"),
                "target_overlay_sha256": manifest.get("target_overlay_sha256"),
                "identity_promoted": False,
            }
        )
    return {
        "schema": "CEW_COL03F_PRIMARY_BRIDGE_INSPECTION_QUEUE_v1",
        "predecessor_sha": predecessor_sha,
        "occurrence_count": 22,
        "priority_occurrence_ids": ["COL-OCC-0001", "COL-OCC-0015"],
        "inspection_order": list(order),
        "entries": entries,
        "all_authority_closed": True,
        "any_identity_resolved": False,
    }


def build_primary_bridge_closure(
    ledger: dict[str, Any],
    queue: dict[str, Any],
    predecessor_sha: str,
) -> dict[str, Any]:
    rows = ledger.get("occurrences")
    if not isinstance(rows, list) or len(rows) != 22:
        raise ValueError("COL03F_CLOSURE_OCCURRENCE_COUNT_INVALID")
    if queue.get("occurrence_count") != 22 or queue.get("inspection_order") != ledger.get("inspection_order"):
        raise ValueError("COL03F_CLOSURE_QUEUE_DRIFT")
    if any(not _authority_closed(row) for row in rows if isinstance(row, dict)):
        raise ValueError("COL03F_CLOSURE_AUTHORITY_NOT_CLOSED")

    counts = Counter(str(row.get("acquisition_state") or "") for row in rows if isinstance(row, dict))
    candidate_ids = [
        str(row["occurrence_id"])
        for row in rows
        if isinstance(row, dict) and row.get("acquisition_state") in CANDIDATE_STATES
    ]
    unresolved_ids = [
        str(row["occurrence_id"])
        for row in rows
        if isinstance(row, dict) and row.get("acquisition_state") not in CANDIDATE_STATES
    ]
    rows_by_id = {str(row.get("occurrence_id") or ""): row for row in rows if isinstance(row, dict)}
    probes = {
        occurrence_id: {
            "acquisition_state": rows_by_id[occurrence_id].get("acquisition_state"),
            "candidate_values": list(rows_by_id[occurrence_id].get("candidate_values") or []),
            "direct_observed_values": list(rows_by_id[occurrence_id].get("direct_observed_values") or []),
            "documentary_candidate_values": list(rows_by_id[occurrence_id].get("documentary_candidate_values") or []),
        }
        for occurrence_id in ("COL-OCC-0001", "COL-OCC-0015")
    }
    next_action = (
        "HUMAN_ADJUDICATE_PRIMARY_LABEL_BRIDGE_CANDIDATES"
        if candidate_ids
        else "ACQUIRE_EXTERNAL_OR_MANUAL_PRIMARY_IDENTITY_EVIDENCE"
    )
    return {
        "schema": "CEW_COL03F_PRIMARY_BRIDGE_CLOSURE_v1",
        "predecessor_sha": predecessor_sha,
        "occurrence_count": 22,
        "state_counts": dict(sorted(counts.items())),
        "candidate_occurrence_ids": candidate_ids,
        "unresolved_occurrence_ids": unresolved_ids,
        "candidate_probe_results": probes,
        "primary_source_replayable": True,
        "historical_identity_positive_evidence_used": False,
        "any_identity_resolved": False,
        "all_authority_closed": True,
        "identity_promotion_authorized": False,
        "next_required_action": next_action,
    }


def write_col03f_json(
    output_root: Path,
    artifacts: dict[str, dict[str, Any]],
) -> list[Path]:
    if set(artifacts) != _REQUIRED_JSON_FILENAMES:
        raise ValueError("COL03F_JSON_ARTIFACT_SET_INVALID")
    output_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename in sorted(artifacts):
        path = output_root / filename
        path.write_text(
            json.dumps(artifacts[filename], indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written.append(path)
    return written


def run_targeted_ocr(
    crop: Any,
    *,
    occurrence_id: str,
    region_class: str,
    page_bounds: tuple[int, int, int, int],
    page_width: int,
    page_height: int,
    occurrence_bbox: dict[str, Any],
    local_region: dict[str, Any],
    provenance_prefix: str,
) -> list[dict[str, Any]]:
    import cv2

    if region_class not in {"FOOTPRINT", "LOCAL"}:
        raise ValueError("COL03F_OCR_REGION_INVALID")
    if crop is None or getattr(crop, "size", 0) == 0:
        raise ValueError("COL03F_OCR_CROP_EMPTY")
    scaled = cv2.resize(crop, None, fx=OCR_SCALE, fy=OCR_SCALE, interpolation=cv2.INTER_CUBIC)
    observations: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="cew-col03f-ocr-") as tmp:
        image_path = Path(tmp) / "crop.png"
        if not cv2.imwrite(str(image_path), scaled):
            raise RuntimeError("COL03F_OCR_CROP_WRITE_FAILED")
        for config_name, psm in OCR_CONFIGURATIONS.items():
            proc = subprocess.run(
                ["tesseract", str(image_path), "stdout", "--psm", str(psm), "tsv"],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"COL03F_TESSERACT_FAILED:{config_name}:{proc.returncode}:{proc.stderr.strip()}")
            observations.extend(
                parse_targeted_tsv(
                    proc.stdout,
                    occurrence_id=occurrence_id,
                    region_class=region_class,
                    ocr_configuration=config_name,
                    crop_bounds=page_bounds,
                    scale=OCR_SCALE,
                    page_width=page_width,
                    page_height=page_height,
                    occurrence_bbox=occurrence_bbox,
                    local_region=local_region,
                    provenance_prefix=provenance_prefix,
                )
            )
    return sorted(
        observations,
        key=lambda row: (
            str(row.get("region_class") or ""),
            str(row.get("ocr_configuration") or ""),
            str(row.get("normalized_text") or ""),
            str(row.get("provenance_ref") or ""),
        ),
    )


def _bounds_crop(image: Any, bounds: tuple[int, int, int, int]) -> Any:
    left, top, right, bottom = bounds
    return image[top:bottom, left:right].copy()


def _page_bbox_to_context_pixels(
    page_bbox: dict[str, Any],
    *,
    context_bounds: tuple[int, int, int, int],
    page_width: int,
    page_height: int,
) -> tuple[int, int, int, int]:
    abs_bounds = bbox_to_pixels(page_bbox, page_width, page_height)
    left, top, _, _ = context_bounds
    return (
        abs_bounds[0] - left,
        abs_bounds[1] - top,
        abs_bounds[2] - left,
        abs_bounds[3] - top,
    )


def _write_occurrence_review_images(
    *,
    page_image: Any,
    occurrence_id: str,
    occurrence_bbox: dict[str, Any],
    observations: list[dict[str, Any]],
    specs: dict[str, tuple[int, int, int, int]],
    review_root: Path,
) -> dict[str, Any]:
    import cv2

    page_height, page_width = page_image.shape[:2]
    context_bounds = specs["CONTEXT"]
    source_only = _bounds_crop(page_image, context_bounds)
    source_path = review_root / f"{occurrence_id}-source-only.png"
    overlay_path = review_root / f"{occurrence_id}-target-overlay.png"
    review_root.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(source_path), source_only, [cv2.IMWRITE_PNG_COMPRESSION, 9]):
        raise RuntimeError("COL03F_SOURCE_REVIEW_WRITE_FAILED")

    overlay = cv2.cvtColor(source_only, cv2.COLOR_GRAY2BGR)
    ox1, oy1, ox2, oy2 = _page_bbox_to_context_pixels(
        occurrence_bbox,
        context_bounds=context_bounds,
        page_width=page_width,
        page_height=page_height,
    )
    cv2.rectangle(overlay, (ox1, oy1), (ox2, oy2), (0, 0, 255), 2)
    for observation in observations:
        if observation.get("relation") not in {"INTERNAL", "INTERSECTING"}:
            continue
        page_bbox = observation.get("page_bbox")
        if not isinstance(page_bbox, dict):
            continue
        tx1, ty1, tx2, ty2 = _page_bbox_to_context_pixels(
            page_bbox,
            context_bounds=context_bounds,
            page_width=page_width,
            page_height=page_height,
        )
        cv2.rectangle(overlay, (tx1, ty1), (tx2, ty2), (255, 0, 0), 1)
    if not cv2.imwrite(str(overlay_path), overlay, [cv2.IMWRITE_PNG_COMPRESSION, 9]):
        raise RuntimeError("COL03F_OVERLAY_REVIEW_WRITE_FAILED")

    return {
        "FOOTPRINT": {"bounds_px": list(specs["FOOTPRINT"])},
        "LOCAL": {"bounds_px": list(specs["LOCAL"])},
        "CONTEXT": {"bounds_px": list(specs["CONTEXT"])},
        "source_only_path": f"review/{source_path.name}",
        "source_only_sha256": _sha256_file(source_path),
        "target_overlay_path": f"review/{overlay_path.name}",
        "target_overlay_sha256": _sha256_file(overlay_path),
    }


def _write_atlas(
    *,
    output_root: Path,
    ledger: dict[str, Any],
) -> Path:
    import cv2
    import numpy as np

    review_root = output_root / "review"
    panels: list[Any] = []
    rows_by_id = {row["occurrence_id"]: row for row in ledger["occurrences"]}
    for occurrence_id in ledger["inspection_order"]:
        row = rows_by_id[occurrence_id]
        source_path = output_root / row["crop_manifest"]["source_only_path"]
        overlay_path = output_root / row["crop_manifest"]["target_overlay_path"]
        source = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
        overlay = cv2.imread(str(overlay_path), cv2.IMREAD_COLOR)
        if source is None or overlay is None:
            raise RuntimeError(f"COL03F_ATLAS_IMAGE_MISSING:{occurrence_id}")
        target_height = 220
        def resized(image: Any) -> Any:
            height, width = image.shape[:2]
            target_width = max(1, int(round(width * target_height / height)))
            return cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        source_r = resized(source)
        overlay_r = resized(overlay)
        width = max(source_r.shape[1], overlay_r.shape[1], 420)
        header = np.full((56, width * 2, 3), 255, dtype=np.uint8)
        label = f"{occurrence_id} | {row['acquisition_state']} | candidates={','.join(row.get('candidate_values') or []) or '-'}"
        cv2.putText(header, label[:110], (8, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
        left = np.full((target_height, width, 3), 255, dtype=np.uint8)
        right = np.full((target_height, width, 3), 255, dtype=np.uint8)
        left[:, :source_r.shape[1]] = source_r
        right[:, :overlay_r.shape[1]] = overlay_r
        panels.append(np.vstack([header, np.hstack([left, right])]))
    atlas = np.vstack(panels)
    atlas_path = review_root / "primary-bridge-atlas.png"
    if not cv2.imwrite(str(atlas_path), atlas, [cv2.IMWRITE_PNG_COMPRESSION, 9]):
        raise RuntimeError("COL03F_ATLAS_WRITE_FAILED")
    return atlas_path


def acquire_primary_bridge_evidence(
    *,
    occurrence_ledger: dict[str, Any],
    documentary_ledger: dict[str, Any],
    col03e_dossiers: dict[str, Any],
    raster_path: Path,
    source_ref: dict[str, Any],
    output_root: Path,
) -> dict[str, dict[str, Any]]:
    import cv2

    page_image = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    if page_image is None:
        raise RuntimeError("COL03F_RASTER_READ_FAILED")
    page_height, page_width = page_image.shape[:2]
    if int(source_ref.get("raster_width_px") or 0) != page_width or int(source_ref.get("raster_height_px") or 0) != page_height:
        raise ValueError("COL03F_RASTER_DIMENSION_DRIFT")

    occurrence_rows = {
        str(row.get("occurrence_id") or ""): row
        for row in occurrence_ledger.get("occurrences", [])
        if isinstance(row, dict)
    }
    documentary_candidates = _documentary_candidate_map(documentary_ledger)
    order = inspection_priority(list(occurrence_rows), documentary_candidates)
    review_root = output_root / "review"
    focused_observations: dict[str, list[dict[str, Any]]] = {}
    crop_manifests: dict[str, dict[str, Any]] = {}

    for occurrence_id in order:
        occurrence = occurrence_rows[occurrence_id]
        representation = occurrence.get("primary_graphical_representation")
        if not isinstance(representation, dict) or not isinstance(representation.get("bbox"), dict):
            raise ValueError(f"COL03F_OCCURRENCE_BBOX_MISSING:{occurrence_id}")
        occurrence_bbox = deepcopy(representation["bbox"])
        specs = crop_specs(occurrence_bbox, page_width, page_height)
        local_region = context_region_from_bounds(specs["CONTEXT"], page_width=page_width, page_height=page_height)
        observations: list[dict[str, Any]] = []
        for region_class in ("FOOTPRINT", "LOCAL"):
            crop = _bounds_crop(page_image, specs[region_class])
            observations.extend(
                run_targeted_ocr(
                    crop,
                    occurrence_id=occurrence_id,
                    region_class=region_class,
                    page_bounds=specs[region_class],
                    page_width=page_width,
                    page_height=page_height,
                    occurrence_bbox=occurrence_bbox,
                    local_region=local_region,
                    provenance_prefix=f"{PAGE_TRANSFORM_ID}:COL03F",
                )
            )
        observations.sort(
            key=lambda row: (
                str(row.get("region_class") or ""),
                str(row.get("ocr_configuration") or ""),
                str(row.get("normalized_text") or ""),
                str(row.get("provenance_ref") or ""),
            )
        )
        focused_observations[occurrence_id] = observations
        crop_manifests[occurrence_id] = _write_occurrence_review_images(
            page_image=page_image,
            occurrence_id=occurrence_id,
            occurrence_bbox=occurrence_bbox,
            observations=observations,
            specs=specs,
            review_root=review_root,
        )

    ledger = build_primary_bridge_ledger(
        occurrence_ledger=occurrence_ledger,
        documentary_ledger=documentary_ledger,
        col03e_dossiers=col03e_dossiers,
        focused_observations=focused_observations,
        source_ref=source_ref,
        crop_manifests=crop_manifests,
    )
    queue = build_inspection_queue(ledger, predecessor_sha=QUALIFIED_COL03E_SHA)
    atlas_path = _write_atlas(output_root=output_root, ledger=ledger)
    queue["atlas_path"] = "review/primary-bridge-atlas.png"
    queue["atlas_sha256"] = _sha256_file(atlas_path)
    closure = build_primary_bridge_closure(ledger, queue, QUALIFIED_COL03E_SHA)
    closure["atlas_path"] = queue["atlas_path"]
    closure["atlas_sha256"] = queue["atlas_sha256"]

    artifacts = {
        "primary-bridge-evidence-ledger.json": ledger,
        "primary-bridge-inspection-queue.json": queue,
        "primary-bridge-closure.json": closure,
    }
    write_col03f_json(output_root, artifacts)
    return artifacts


def _render_exact_source(runtime_root: Path) -> tuple[Path, dict[str, Any]]:
    from cew_b01.source_contract import load_source_contract, materialize_source
    import pypdfium2 as pdfium

    runtime_root.mkdir(parents=True, exist_ok=True)
    contract = load_source_contract(SOURCE_CONTRACT_PATH)
    materialized = materialize_source(
        contract,
        Path.cwd(),
        runtime_root / "tavola5-col03f-source.pdf",
    )
    pdf_path = Path(materialized.destination)
    if _sha256_file(pdf_path) != SOURCE_SHA256:
        raise ValueError("COL03F_SOURCE_DIGEST_DRIFT")

    document = pdfium.PdfDocument(str(pdf_path))
    try:
        page = document[0]
        try:
            scale = RENDER_DPI / 72.0
            bitmap = page.render(scale=scale, rotation=0)
            try:
                image = bitmap.to_pil().convert("RGB")
                raster_path = runtime_root / "tav5-page0-300dpi-col03f.png"
                image.save(raster_path, format="PNG", optimize=False, compress_level=9)
            finally:
                close_bitmap = getattr(bitmap, "close", None)
                if callable(close_bitmap):
                    close_bitmap()
        finally:
            close_page = getattr(page, "close", None)
            if callable(close_page):
                close_page()
    finally:
        close_document = getattr(document, "close", None)
        if callable(close_document):
            close_document()

    import cv2
    raster = cv2.imread(str(raster_path), cv2.IMREAD_GRAYSCALE)
    if raster is None:
        raise RuntimeError("COL03F_RENDERED_RASTER_READ_FAILED")
    height, width = raster.shape[:2]
    tess = subprocess.run(["tesseract", "--version"], capture_output=True, text=True, check=False)
    if tess.returncode != 0:
        raise RuntimeError("COL03F_TESSERACT_VERSION_PROBE_FAILED")
    source_ref = {
        "source_version_id": SOURCE_VERSION_ID,
        "page_id": PAGE_ID,
        "page_transform_id": PAGE_TRANSFORM_ID,
        "source_sha256": SOURCE_SHA256,
        "raster_sha256": _sha256_file(raster_path),
        "raster_width_px": width,
        "raster_height_px": height,
        "render_dpi": RENDER_DPI,
        "renderer": "pypdfium2",
        "tesseract_version": (tess.stdout or tess.stderr).splitlines()[0].strip(),
        "ocr_scale": OCR_SCALE,
        "ocr_configurations": deepcopy(OCR_CONFIGURATIONS),
        "structural_truth_authorized": False,
    }
    return raster_path, source_ref


def _load_predecessors() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    occurrence_ledger = _read_json(Path("evidence/cew-col03a/column-occurrence-ledger.json"))
    documentary_ledger = _read_json(Path("evidence/cew-col03b/documentary-identity-evidence-ledger.json"))
    col03e_dossiers = _read_json(Path("evidence/cew-col03e/identity-adjudication-dossiers.json"))
    return occurrence_ledger, documentary_ledger, col03e_dossiers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Acquire governed COL-03F primary-source identity bridge evidence")
    parser.add_argument("--output", type=Path, default=Path("evidence/cew-col03f"))
    args = parser.parse_args(argv)

    runtime_root = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "cew-col03f-runtime"
    raster_path, source_ref = _render_exact_source(runtime_root)
    occurrence_ledger, documentary_ledger, col03e_dossiers = _load_predecessors()
    artifacts = acquire_primary_bridge_evidence(
        occurrence_ledger=occurrence_ledger,
        documentary_ledger=documentary_ledger,
        col03e_dossiers=col03e_dossiers,
        raster_path=raster_path,
        source_ref=source_ref,
        output_root=args.output,
    )
    closure = artifacts["primary-bridge-closure.json"]
    print(
        json.dumps(
            {
                "occurrence_count": closure["occurrence_count"],
                "state_counts": closure["state_counts"],
                "candidate_occurrence_ids": closure["candidate_occurrence_ids"],
                "any_identity_resolved": closure["any_identity_resolved"],
                "next_required_action": closure["next_required_action"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
