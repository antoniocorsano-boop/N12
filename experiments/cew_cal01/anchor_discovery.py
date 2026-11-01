from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Sequence


_DECIMAL_RE = re.compile(r"^(?P<int>\d{1,2})[\.,](?P<frac>\d{1,2})$")
_COMPACT_METRIC_RE = re.compile(r"^(?P<value>[1-9]\d{2})$")


def normalize_dimension_text(value: Any) -> tuple[str, float] | None:
    """Normalize plausible metric dimension text without assigning geometric meaning.

    Decimal strings are interpreted as metres. Three-digit compact strings are
    interpreted as centimetre-style dimension notation (e.g. 470 -> 4.70 m),
    but remain proposals until geometric binding is established.
    """

    text = str(value or "").strip().replace(" ", "")
    if not text or any(char.isalpha() for char in text) or "x" in text.lower() or "×" in text:
        return None

    match = _DECIMAL_RE.fullmatch(text)
    if match:
        integer = int(match.group("int"))
        frac_raw = match.group("frac")
        frac = int(frac_raw.ljust(2, "0")[:2])
        metric = integer + frac / 100.0
        if metric <= 0 or metric > 50:
            return None
        return f"{metric:.2f}", metric

    compact = _COMPACT_METRIC_RE.fullmatch(text)
    if compact:
        metric = int(compact.group("value")) / 100.0
        if metric <= 0 or metric > 50:
            return None
        return f"{metric:.2f}", metric

    return None


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def proposal_from_ocr_token(
    token: dict[str, Any],
    *,
    page_width: int,
    page_height: int,
) -> dict[str, Any]:
    normalized = normalize_dimension_text(token.get("text"))
    if normalized is None:
        raise ValueError("CAL01_OCR_TOKEN_NOT_METRIC_PROPOSAL")
    if page_width <= 0 or page_height <= 0:
        raise ValueError("CAL01_PAGE_DIMENSIONS_INVALID")
    raw_box = token.get("bbox_px")
    if not isinstance(raw_box, (list, tuple)) or len(raw_box) != 4:
        raise ValueError("CAL01_OCR_TOKEN_BBOX_INVALID")
    left, top, right, bottom = (float(value) for value in raw_box)
    if left < 0 or top < 0 or right <= left or bottom <= top or right > page_width or bottom > page_height:
        raise ValueError("CAL01_OCR_TOKEN_BBOX_INVALID")

    normalized_text, metric_value = normalized
    identity = {
        "normalized_metric_text": normalized_text,
        "metric_value_m": metric_value,
        "bbox_px": [left, top, right, bottom],
        "page_width_px": int(page_width),
        "page_height_px": int(page_height),
    }
    return {
        "proposal_id": "CEW-CAL01-DIMPROP-" + _canonical_digest(identity)[:20],
        **identity,
        "ocr_confidence": float(token.get("confidence", 0.0)),
        "state": "NUMERIC_TEXT_PROPOSAL",
        "source_role": "OCR_DERIVATIVE_LOCALIZER_ONLY",
        "eligible_for_anchor": False,
        "metric_anchor_promoted": False,
    }


def _is_dark(value: Any) -> bool:
    try:
        return float(value) <= 80.0
    except (TypeError, ValueError):
        return False


def _image_shape(image: Sequence[Sequence[Any]]) -> tuple[int, int]:
    height = len(image)
    if height == 0:
        raise ValueError("CAL01_IMAGE_EMPTY")
    width = len(image[0])
    if width == 0 or any(len(row) != width for row in image):
        raise ValueError("CAL01_IMAGE_SHAPE_INVALID")
    return width, height


def _longest_horizontal_segment(image: Sequence[Sequence[Any]], y: int) -> tuple[int, int] | None:
    row = image[y]
    best: tuple[int, int] | None = None
    start: int | None = None
    for x, value in enumerate(row):
        if _is_dark(value):
            if start is None:
                start = x
        elif start is not None:
            if best is None or x - start > best[1] - best[0]:
                best = (start, x - 1)
            start = None
    if start is not None:
        if best is None or len(row) - start > best[1] - best[0]:
            best = (start, len(row) - 1)
    return best


def _longest_vertical_segment(image: Sequence[Sequence[Any]], x: int) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    start: int | None = None
    for y, row in enumerate(image):
        if _is_dark(row[x]):
            if start is None:
                start = y
        elif start is not None:
            if best is None or y - start > best[1] - best[0]:
                best = (start, y - 1)
            start = None
    if start is not None:
        if best is None or len(image) - start > best[1] - best[0]:
            best = (start, len(image) - 1)
    return best


def _has_vertical_reference(
    image: Sequence[Sequence[Any]],
    *,
    x_target: int,
    y_line: int,
    tolerance: int = 6,
    min_span: int = 20,
) -> tuple[int, int, int] | None:
    width, _ = _image_shape(image)
    for x in range(max(0, x_target - tolerance), min(width, x_target + tolerance + 1)):
        segment = _longest_vertical_segment(image, x)
        if segment is None:
            continue
        top, bottom = segment
        if bottom - top + 1 >= min_span and top <= y_line <= bottom:
            return x, top, bottom
    return None


def _has_horizontal_reference(
    image: Sequence[Sequence[Any]],
    *,
    y_target: int,
    x_line: int,
    tolerance: int = 6,
    min_span: int = 20,
) -> tuple[int, int, int] | None:
    _, height = _image_shape(image)
    for y in range(max(0, y_target - tolerance), min(height, y_target + tolerance + 1)):
        segment = _longest_horizontal_segment(image, y)
        if segment is None:
            continue
        left, right = segment
        if right - left + 1 >= min_span and left <= x_line <= right:
            return y, left, right
    return None


def discover_dimension_geometry(
    image: Sequence[Sequence[Any]],
    *,
    token_bbox_px: Sequence[float],
) -> dict[str, Any]:
    """Detect a simple dimension-line pattern around an OCR numeric proposal.

    This function only establishes a geometric relation. It never promotes a
    metric anchor or assigns structural identity.
    """

    width, height = _image_shape(image)
    if len(token_bbox_px) != 4:
        raise ValueError("CAL01_TOKEN_BBOX_INVALID")
    left, top, right, bottom = (float(value) for value in token_bbox_px)
    if left < 0 or top < 0 or right <= left or bottom <= top or right > width or bottom > height:
        raise ValueError("CAL01_TOKEN_BBOX_INVALID")

    cx = (left + right) / 2.0
    cy = (top + bottom) / 2.0
    x_margin = max(40, int(round((right - left) * 4.0)))
    y_margin = max(40, int(round((bottom - top) * 4.0)))

    horizontal_candidates: list[tuple[int, int, int]] = []
    for y in range(max(0, int(top) - y_margin), min(height, int(bottom) + y_margin + 1)):
        segment = _longest_horizontal_segment(image, y)
        if segment is None:
            continue
        seg_left, seg_right = segment
        if seg_right - seg_left + 1 < max(40, int((right - left) * 2.0)):
            continue
        if seg_left <= cx <= seg_right:
            horizontal_candidates.append((y, seg_left, seg_right))

    horizontal_candidates.sort(key=lambda item: (abs(item[0] - cy), -(item[2] - item[1]), item[0]))
    for y_line, seg_left, seg_right in horizontal_candidates:
        ref_a = _has_vertical_reference(image, x_target=seg_left, y_line=y_line)
        ref_b = _has_vertical_reference(image, x_target=seg_right, y_line=y_line)
        if ref_a is not None and ref_b is not None and abs(ref_a[0] - ref_b[0]) >= 20:
            return {
                "geometrically_bound": True,
                "orientation": "HORIZONTAL",
                "endpoint_a_px": [float(ref_a[0]), float(y_line)],
                "endpoint_b_px": [float(ref_b[0]), float(y_line)],
                "geometry_role": "DIMENSION_LINE_WITH_TWO_REFERENCES",
                "metric_anchor_promoted": False,
            }

    vertical_candidates: list[tuple[int, int, int]] = []
    for x in range(max(0, int(left) - x_margin), min(width, int(right) + x_margin + 1)):
        segment = _longest_vertical_segment(image, x)
        if segment is None:
            continue
        seg_top, seg_bottom = segment
        if seg_bottom - seg_top + 1 < max(40, int((bottom - top) * 2.0)):
            continue
        if seg_top <= cy <= seg_bottom:
            vertical_candidates.append((x, seg_top, seg_bottom))

    vertical_candidates.sort(key=lambda item: (abs(item[0] - cx), -(item[2] - item[1]), item[0]))
    for x_line, seg_top, seg_bottom in vertical_candidates:
        ref_a = _has_horizontal_reference(image, y_target=seg_top, x_line=x_line)
        ref_b = _has_horizontal_reference(image, y_target=seg_bottom, x_line=x_line)
        if ref_a is not None and ref_b is not None and abs(ref_a[0] - ref_b[0]) >= 20:
            return {
                "geometrically_bound": True,
                "orientation": "VERTICAL",
                "endpoint_a_px": [float(x_line), float(ref_a[0])],
                "endpoint_b_px": [float(x_line), float(ref_b[0])],
                "geometry_role": "DIMENSION_LINE_WITH_TWO_REFERENCES",
                "metric_anchor_promoted": False,
            }

    return {
        "geometrically_bound": False,
        "orientation": None,
        "endpoint_a_px": None,
        "endpoint_b_px": None,
        "geometry_role": None,
        "reason": "TWO_REFERENCE_LINES_NOT_OBSERVED",
        "metric_anchor_promoted": False,
    }
