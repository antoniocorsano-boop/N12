from __future__ import annotations

from copy import deepcopy
from typing import Any

from experiments.cew_col03b.local_evidence import classify_text_relation


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
    if ocr_configuration not in {"PSM6", "PSM11"}:
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
