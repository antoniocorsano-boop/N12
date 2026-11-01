from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Iterable, Sequence


def _canonical_numeric_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "").replace(",", ".")
    if not text:
        return None
    allowed = set("0123456789.")
    if any(char not in allowed for char in text) or text.count(".") > 1:
        return None
    text = text.strip(".")
    return text or None


def select_ocr_consensus(
    readings: Iterable[Any],
    *,
    minimum_count: int = 3,
    minimum_margin: int = 2,
) -> dict[str, Any]:
    """Select a repeated OCR reading without repairing or inferring digits."""

    if minimum_count < 1 or minimum_margin < 0:
        raise ValueError("CAL01_OCR_CONSENSUS_POLICY_INVALID")
    normalized = [value for raw in readings if (value := _canonical_numeric_text(raw)) is not None]
    counts = Counter(normalized)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    if not ranked:
        return {
            "confirmed": False,
            "text": None,
            "count": 0,
            "runner_up_count": 0,
            "reading_count": 0,
            "reason": "OCR_CONSENSUS_EMPTY",
        }

    top_text, top_count = ranked[0]
    runner_up_count = ranked[1][1] if len(ranked) > 1 else 0
    confirmed = top_count >= minimum_count and top_count - runner_up_count >= minimum_margin
    return {
        "confirmed": confirmed,
        "text": top_text if confirmed else None,
        "count": top_count,
        "runner_up_count": runner_up_count,
        "reading_count": len(normalized),
        "reason": "OCR_CONSENSUS_CONFIRMED" if confirmed else "OCR_CONSENSUS_NOT_DOMINANT",
    }


def _segments(raw: Iterable[Sequence[float]]) -> list[tuple[float, float, float, float]]:
    result: list[tuple[float, float, float, float]] = []
    for item in raw:
        if len(item) != 4:
            raise ValueError("CAL01_FRAME_SEGMENT_INVALID")
        result.append(tuple(float(value) for value in item))
    return result


def _horizontal(line: tuple[float, float, float, float]) -> tuple[bool, float, float, float]:
    x1, y1, x2, y2 = line
    length = abs(x2 - x1)
    return (
        length >= 1.0 and abs(y2 - y1) <= max(3.0, length * 0.05),
        min(x1, x2),
        max(x1, x2),
        (y1 + y2) / 2.0,
    )


def _vertical(line: tuple[float, float, float, float]) -> tuple[bool, float, float, float]:
    x1, y1, x2, y2 = line
    length = abs(y2 - y1)
    return (
        length >= 1.0 and abs(x2 - x1) <= max(3.0, length * 0.05),
        min(y1, y2),
        max(y1, y2),
        (x1 + x2) / 2.0,
    )


def _bbox_distance(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    dx = max(ax0 - bx1, bx0 - ax1, 0.0)
    dy = max(ay0 - by1, by0 - ay1, 0.0)
    return (dx * dx + dy * dy) ** 0.5


def detect_nearby_closed_frame(
    line_segments: Iterable[Sequence[float]],
    *,
    token_bbox_px: Sequence[float],
    max_distance_px: float = 60.0,
    corner_tolerance_px: float = 8.0,
    min_side_px: float = 12.0,
    max_side_px: float = 220.0,
) -> dict[str, Any]:
    """Detect a bounded axis-aligned closed frame near a numeric token.

    This is only document-role context. It does not identify a column, section,
    or structural object and never authorizes metric/canonical promotion.
    """

    if len(token_bbox_px) != 4:
        raise ValueError("CAL01_FRAME_TOKEN_BBOX_INVALID")
    token = tuple(float(value) for value in token_bbox_px)
    if token[2] <= token[0] or token[3] <= token[1] or max_distance_px < 0:
        raise ValueError("CAL01_FRAME_TOKEN_BBOX_INVALID")

    horizontals: list[tuple[float, float, float]] = []
    verticals: list[tuple[float, float, float]] = []
    for line in _segments(line_segments):
        is_h, x0, x1, y = _horizontal(line)
        if is_h and min_side_px <= x1 - x0 <= max_side_px:
            horizontals.append((y, x0, x1))
        is_v, y0, y1, x = _vertical(line)
        if is_v and min_side_px <= y1 - y0 <= max_side_px:
            verticals.append((x, y0, y1))

    candidates: list[tuple[float, tuple[float, float, float, float]]] = []
    for first_h, second_h in combinations(horizontals, 2):
        y0, y1 = sorted((first_h[0], second_h[0]))
        height = y1 - y0
        if not (min_side_px <= height <= max_side_px):
            continue
        for first_v, second_v in combinations(verticals, 2):
            x0, x1 = sorted((first_v[0], second_v[0]))
            width = x1 - x0
            if not (min_side_px <= width <= max_side_px):
                continue

            horizontal_span_ok = all(
                h[1] - corner_tolerance_px <= x0 <= h[2] + corner_tolerance_px
                and h[1] - corner_tolerance_px <= x1 <= h[2] + corner_tolerance_px
                for h in (first_h, second_h)
            )
            vertical_span_ok = all(
                v[1] - corner_tolerance_px <= y0 <= v[2] + corner_tolerance_px
                and v[1] - corner_tolerance_px <= y1 <= v[2] + corner_tolerance_px
                for v in (first_v, second_v)
            )
            if not (horizontal_span_ok and vertical_span_ok):
                continue

            frame = (x0, y0, x1, y1)
            distance = _bbox_distance(frame, token)
            if distance <= max_distance_px:
                candidates.append((distance, frame))

    if not candidates:
        return {
            "detected": False,
            "bbox_px": None,
            "distance_px": None,
            "role": "CLOSED_FRAME_CONTEXT_NOT_OBSERVED",
            "engineering_authority_effect": "NONE",
        }

    candidates.sort(key=lambda item: (item[0], item[1]))
    distance, frame = candidates[0]
    return {
        "detected": True,
        "bbox_px": [float(value) for value in frame],
        "distance_px": float(distance),
        "role": "NEARBY_CLOSED_FRAME_CONTEXT",
        "engineering_authority_effect": "NONE",
    }
