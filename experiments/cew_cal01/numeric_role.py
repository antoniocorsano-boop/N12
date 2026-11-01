from __future__ import annotations

from math import hypot
from typing import Any, Iterable, Sequence


ROLE_LINEAR_DIMENSION = "LINEAR_DIMENSION"
ROLE_SECTION_MEASURE = "SECTION_MEASURE"
ROLE_UNRESOLVED = "UNRESOLVED"


def expected_dimension_orientation(rotation_degrees: int) -> str:
    rotation = int(rotation_degrees) % 360
    if rotation in {0, 180}:
        return "HORIZONTAL"
    if rotation in {90, 270}:
        return "VERTICAL"
    raise ValueError("CAL01_TEXT_ROTATION_UNSUPPORTED")


def _segments(raw: Iterable[Sequence[float]]) -> list[tuple[float, float, float, float]]:
    result: list[tuple[float, float, float, float]] = []
    for item in raw:
        if len(item) != 4:
            raise ValueError("CAL01_LINE_SEGMENT_INVALID")
        result.append(tuple(float(value) for value in item))
    return result


def _bbox(raw: Sequence[float]) -> tuple[float, float, float, float]:
    if len(raw) != 4:
        raise ValueError("CAL01_TOKEN_BBOX_INVALID")
    left, top, right, bottom = (float(value) for value in raw)
    if right <= left or bottom <= top:
        raise ValueError("CAL01_TOKEN_BBOX_INVALID")
    return left, top, right, bottom


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


def _same_span(a0: float, a1: float, b0: float, b1: float, *, tolerance: float = 12.0) -> bool:
    return abs(a0 - b0) <= tolerance and abs(a1 - b1) <= tolerance


def _short_diagonal(line: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2 = line
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    length = hypot(dx, dy)
    if not 10.0 <= length <= 80.0:
        return False
    if dx < 4.0 or dy < 4.0:
        return False
    # TAV.5 uses hand-drawn slash ticks; keep a broad but bounded 45-degree family.
    return min(dx, dy) / max(dx, dy) >= 0.45


def _point_segment_distance(
    px: float,
    py: float,
    line: tuple[float, float, float, float],
) -> float:
    x1, y1, x2, y2 = line
    dx = x2 - x1
    dy = y2 - y1
    denom = dx * dx + dy * dy
    if denom <= 0.0:
        return hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / denom
    t = max(0.0, min(1.0, t))
    qx = x1 + t * dx
    qy = y1 + t * dy
    return hypot(px - qx, py - qy)


def _diagonal_tick_near(
    segments: list[tuple[float, float, float, float]],
    *,
    point_x: float,
    point_y: float,
) -> tuple[float, float, float, float] | None:
    candidates: list[tuple[float, float, tuple[float, float, float, float]]] = []
    for line in segments:
        if not _short_diagonal(line):
            continue
        x1, y1, x2, y2 = line
        midpoint_distance = hypot(((x1 + x2) / 2.0) - point_x, ((y1 + y2) / 2.0) - point_y)
        distance = _point_segment_distance(point_x, point_y, line)
        if distance <= 10.0 and midpoint_distance <= 24.0:
            candidates.append((distance, midpoint_distance, line))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    return candidates[0][2]


def dimension_tick_relation(
    line_segments: Iterable[Sequence[float]],
    *,
    token_bbox_px: Sequence[float],
    expected_orientation: str,
) -> dict[str, Any]:
    """Confirm bounded TAV.5 dimension grammar.

    A relation requires a principal dimension line near the numeric token plus
    two short terminal marks. Both perpendicular ticks and the source's short
    diagonal slash convention are supported. Long structural crossings and
    long diagonal members are rejected. A parallel closed-frame pattern is not
    accepted as a dimension.
    """

    orientation = str(expected_orientation).upper()
    if orientation not in {"HORIZONTAL", "VERTICAL"}:
        raise ValueError("CAL01_DIMENSION_ORIENTATION_INVALID")
    segments = _segments(line_segments)
    left, top, right, bottom = _bbox(token_bbox_px)
    cx = (left + right) / 2.0
    cy = (top + bottom) / 2.0
    token_w = right - left
    token_h = bottom - top
    closed_frame_seen = False

    if orientation == "VERTICAL":
        main_candidates: list[tuple[float, float, float]] = []
        tick_candidates: list[tuple[float, float, float]] = []
        for line in segments:
            is_v, y0, y1, x = _vertical(line)
            if is_v and y1 - y0 >= max(50.0, token_h * 1.5) and abs(x - cx) <= max(70.0, token_w * 4.0):
                main_candidates.append((x, y0, y1))
            is_h, x0, x1, y = _horizontal(line)
            length = x1 - x0
            if is_h and 10.0 <= length <= 80.0:
                tick_candidates.append((y, x0, x1))

        main_candidates.sort(key=lambda item: (abs(item[0] - cx), -(item[2] - item[1]), item[1]))
        for x, y0, y1 in main_candidates:
            ticks = [
                (y, x0, x1)
                for y, x0, x1 in tick_candidates
                if x0 - 6.0 <= x <= x1 + 6.0 and y0 - 8.0 <= y <= y1 + 8.0
            ]
            if len(ticks) >= 2:
                ticks.sort(key=lambda item: item[0])
                first = min(ticks, key=lambda item: abs(item[0] - y0))
                last = min(ticks, key=lambda item: abs(item[0] - y1))
                if first is not last and abs(first[0] - y0) <= 14.0 and abs(last[0] - y1) <= 14.0 and last[0] - first[0] >= max(40.0, token_h * 1.25):
                    parallel = [
                        (other_x, other_y0, other_y1)
                        for other_x, other_y0, other_y1 in main_candidates
                        if other_x != x
                        and 10.0 <= abs(other_x - x) <= 80.0
                        and _same_span(y0, y1, other_y0, other_y1)
                    ]
                    if any(
                        first[1] - 6.0 <= other_x <= first[2] + 6.0
                        and last[1] - 6.0 <= other_x <= last[2] + 6.0
                        for other_x, _, _ in parallel
                    ):
                        closed_frame_seen = True
                    else:
                        return {
                            "confirmed": True,
                            "orientation": "VERTICAL",
                            "terminal_tick_count": 2,
                            "tick_style": "PERPENDICULAR",
                            "endpoint_a_px": [float(x), float(first[0])],
                            "endpoint_b_px": [float(x), float(last[0])],
                            "reason": None,
                        }

            first_slash = _diagonal_tick_near(segments, point_x=x, point_y=y0)
            last_slash = _diagonal_tick_near(segments, point_x=x, point_y=y1)
            if first_slash is not None and last_slash is not None and first_slash != last_slash and y1 - y0 >= max(40.0, token_h * 1.25):
                return {
                    "confirmed": True,
                    "orientation": "VERTICAL",
                    "terminal_tick_count": 2,
                    "tick_style": "DIAGONAL_SLASH",
                    "endpoint_a_px": [float(x), float(y0)],
                    "endpoint_b_px": [float(x), float(y1)],
                    "reason": None,
                }
    else:
        main_candidates: list[tuple[float, float, float]] = []
        tick_candidates: list[tuple[float, float, float]] = []
        for line in segments:
            is_h, x0, x1, y = _horizontal(line)
            if is_h and x1 - x0 >= max(50.0, token_w * 1.5) and abs(y - cy) <= max(70.0, token_h * 4.0):
                main_candidates.append((y, x0, x1))
            is_v, y0, y1, x = _vertical(line)
            length = y1 - y0
            if is_v and 10.0 <= length <= 80.0:
                tick_candidates.append((x, y0, y1))

        main_candidates.sort(key=lambda item: (abs(item[0] - cy), -(item[2] - item[1]), item[1]))
        for y, x0, x1 in main_candidates:
            ticks = [
                (x, y0, y1)
                for x, y0, y1 in tick_candidates
                if y0 - 6.0 <= y <= y1 + 6.0 and x0 - 8.0 <= x <= x1 + 8.0
            ]
            if len(ticks) >= 2:
                ticks.sort(key=lambda item: item[0])
                first = min(ticks, key=lambda item: abs(item[0] - x0))
                last = min(ticks, key=lambda item: abs(item[0] - x1))
                if first is not last and abs(first[0] - x0) <= 14.0 and abs(last[0] - x1) <= 14.0 and last[0] - first[0] >= max(40.0, token_w * 1.25):
                    parallel = [
                        (other_y, other_x0, other_x1)
                        for other_y, other_x0, other_x1 in main_candidates
                        if other_y != y
                        and 10.0 <= abs(other_y - y) <= 80.0
                        and _same_span(x0, x1, other_x0, other_x1)
                    ]
                    if any(
                        first[1] - 6.0 <= other_y <= first[2] + 6.0
                        and last[1] - 6.0 <= other_y <= last[2] + 6.0
                        for other_y, _, _ in parallel
                    ):
                        closed_frame_seen = True
                    else:
                        return {
                            "confirmed": True,
                            "orientation": "HORIZONTAL",
                            "terminal_tick_count": 2,
                            "tick_style": "PERPENDICULAR",
                            "endpoint_a_px": [float(first[0]), float(y)],
                            "endpoint_b_px": [float(last[0]), float(y)],
                            "reason": None,
                        }

            first_slash = _diagonal_tick_near(segments, point_x=x0, point_y=y)
            last_slash = _diagonal_tick_near(segments, point_x=x1, point_y=y)
            if first_slash is not None and last_slash is not None and first_slash != last_slash and x1 - x0 >= max(40.0, token_w * 1.25):
                return {
                    "confirmed": True,
                    "orientation": "HORIZONTAL",
                    "terminal_tick_count": 2,
                    "tick_style": "DIAGONAL_SLASH",
                    "endpoint_a_px": [float(x0), float(y)],
                    "endpoint_b_px": [float(x1), float(y)],
                    "reason": None,
                }

    return {
        "confirmed": False,
        "orientation": orientation,
        "terminal_tick_count": 0,
        "tick_style": None,
        "endpoint_a_px": None,
        "endpoint_b_px": None,
        "reason": "CLOSED_FRAME_PATTERN" if closed_frame_seen else "TWO_SHORT_TERMINAL_TICKS_NOT_OBSERVED",
    }


def _canonical_ocr_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "").replace(",", ".")
    return text or None


def classify_numeric_graphic_role(
    *,
    raw_text: str,
    consensus_text: str | None,
    consensus_count: int,
    ocr_rotation_degrees: int,
    token_bbox_px: Sequence[float],
    line_segments: Iterable[Sequence[float]],
    nearby_closed_frame: bool,
) -> dict[str, Any]:
    raw = _canonical_ocr_text(raw_text)
    consensus = _canonical_ocr_text(consensus_text)
    if not raw:
        raise ValueError("CAL01_NUMERIC_TEXT_REQUIRED")
    if isinstance(consensus_count, bool) or int(consensus_count) < 0:
        raise ValueError("CAL01_CONSENSUS_COUNT_INVALID")

    base = {
        "documented_text": consensus or raw,
        "metric_value_m": None,
        "primary_anchor_authorized": False,
        "canonical_geometry_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    if consensus is None or int(consensus_count) < 2:
        return {**base, "role": ROLE_UNRESOLVED, "reason": "OCR_CONSENSUS_INSUFFICIENT", "dimension_relation": None}

    orientation = expected_dimension_orientation(ocr_rotation_degrees)
    relation = dimension_tick_relation(line_segments, token_bbox_px=token_bbox_px, expected_orientation=orientation)
    if relation["confirmed"] and bool(nearby_closed_frame):
        return {**base, "role": ROLE_UNRESOLVED, "reason": "DIMENSION_SECTION_ROLE_CONFLICT", "dimension_relation": relation}
    if relation["confirmed"]:
        return {**base, "role": ROLE_LINEAR_DIMENSION, "reason": "CONSENSUS_AND_DIMENSION_TICK_GRAMMAR_CONFIRMED", "dimension_relation": relation}
    if bool(nearby_closed_frame):
        return {**base, "role": ROLE_SECTION_MEASURE, "reason": "CONSENSUS_NEAR_CLOSED_FRAME_WITHOUT_DIMENSION_TICK_GRAMMAR", "dimension_relation": relation}
    return {**base, "role": ROLE_UNRESOLVED, "reason": "DIMENSION_ROLE_NOT_CONFIRMED", "dimension_relation": relation}
