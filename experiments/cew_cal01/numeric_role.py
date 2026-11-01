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
    return length >= 1.0 and abs(y2 - y1) <= max(3.0, length * 0.05), min(x1, x2), max(x1, x2), (y1 + y2) / 2.0


def _vertical(line: tuple[float, float, float, float]) -> tuple[bool, float, float, float]:
    x1, y1, x2, y2 = line
    length = abs(y2 - y1)
    return length >= 1.0 and abs(x2 - x1) <= max(3.0, length * 0.05), min(y1, y2), max(y1, y2), (x1 + x2) / 2.0


def _same_span(a0: float, a1: float, b0: float, b1: float, *, tolerance: float = 12.0) -> bool:
    return abs(a0 - b0) <= tolerance and abs(a1 - b1) <= tolerance


def _short_diagonal(line: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2 = line
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    length = hypot(dx, dy)
    if not 10.0 <= length <= 80.0 or dx < 4.0 or dy < 4.0:
        return False
    # Scanned slash ticks fragment into several nearby slopes; length remains bounded.
    return min(dx, dy) / max(dx, dy) >= 0.30


def _diagonal_intersection_y(line: tuple[float, float, float, float], x: float) -> float | None:
    if not _short_diagonal(line):
        return None
    x1, y1, x2, y2 = line
    dx = x2 - x1
    if abs(dx) < 1e-9:
        return None
    t = (x - x1) / dx
    if t < -0.20 or t > 1.20:
        return None
    return y1 + t * (y2 - y1)


def _diagonal_intersection_x(line: tuple[float, float, float, float], y: float) -> float | None:
    if not _short_diagonal(line):
        return None
    x1, y1, x2, y2 = line
    dy = y2 - y1
    if abs(dy) < 1e-9:
        return None
    t = (y - y1) / dy
    if t < -0.20 or t > 1.20:
        return None
    return x1 + t * (x2 - x1)


def _bracketing_pair(positions: list[float], before: float, after: float, minimum_span: float) -> tuple[float, float] | None:
    upper = [value for value in positions if value <= before]
    lower = [value for value in positions if value >= after]
    if not upper or not lower:
        return None
    first = max(upper)
    last = min(lower)
    if last - first < minimum_span:
        return None
    return first, last


def dimension_tick_relation(
    line_segments: Iterable[Sequence[float]],
    *,
    token_bbox_px: Sequence[float],
    expected_orientation: str,
) -> dict[str, Any]:
    """Confirm bounded TAV.5 dimension grammar.

    The Hough representation may extend beyond the actual dimension ticks. Tick
    intersections therefore define the documented endpoints; Hough segment ends
    do not. Both perpendicular terminal marks and short diagonal slash marks are
    accepted, while long structural crossings remain excluded.
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
            if is_h and 10.0 <= x1 - x0 <= 80.0:
                tick_candidates.append((y, x0, x1))

        main_candidates.sort(key=lambda item: (abs(item[0] - cx), -(item[2] - item[1]), item[1]))
        for x, y0, y1 in main_candidates:
            ticks = [(y, x0, x1) for y, x0, x1 in tick_candidates if x0 - 6.0 <= x <= x1 + 6.0 and y0 - 8.0 <= y <= y1 + 8.0]
            if len(ticks) >= 2:
                first = min(ticks, key=lambda item: abs(item[0] - y0))
                last = min(ticks, key=lambda item: abs(item[0] - y1))
                if first is not last and abs(first[0] - y0) <= 14.0 and abs(last[0] - y1) <= 14.0 and last[0] - first[0] >= max(40.0, token_h * 1.25):
                    parallel = [(ox, oy0, oy1) for ox, oy0, oy1 in main_candidates if ox != x and 10.0 <= abs(ox - x) <= 80.0 and _same_span(y0, y1, oy0, oy1)]
                    if any(first[1] - 6.0 <= ox <= first[2] + 6.0 and last[1] - 6.0 <= ox <= last[2] + 6.0 for ox, _, _ in parallel):
                        closed_frame_seen = True
                    else:
                        return {"confirmed": True, "orientation": "VERTICAL", "terminal_tick_count": 2, "tick_style": "PERPENDICULAR", "endpoint_a_px": [float(x), float(first[0])], "endpoint_b_px": [float(x), float(last[0])], "reason": None}

            slash_positions = []
            for line in segments:
                y = _diagonal_intersection_y(line, x)
                if y is not None and y0 - 8.0 <= y <= y1 + 8.0:
                    slash_positions.append(float(y))
            pair = _bracketing_pair(slash_positions, top + 20.0, bottom - 20.0, max(40.0, token_h * 1.25))
            if pair is not None:
                first_y, last_y = pair
                return {"confirmed": True, "orientation": "VERTICAL", "terminal_tick_count": 2, "tick_style": "DIAGONAL_SLASH", "endpoint_a_px": [float(x), float(first_y)], "endpoint_b_px": [float(x), float(last_y)], "reason": None}

    else:
        main_candidates: list[tuple[float, float, float]] = []
        tick_candidates: list[tuple[float, float, float]] = []
        for line in segments:
            is_h, x0, x1, y = _horizontal(line)
            if is_h and x1 - x0 >= max(50.0, token_w * 1.5) and abs(y - cy) <= max(70.0, token_h * 4.0):
                main_candidates.append((y, x0, x1))
            is_v, y0, y1, x = _vertical(line)
            if is_v and 10.0 <= y1 - y0 <= 80.0:
                tick_candidates.append((x, y0, y1))

        main_candidates.sort(key=lambda item: (abs(item[0] - cy), -(item[2] - item[1]), item[1]))
        for y, x0, x1 in main_candidates:
            ticks = [(x, y0, y1) for x, y0, y1 in tick_candidates if y0 - 6.0 <= y <= y1 + 6.0 and x0 - 8.0 <= x <= x1 + 8.0]
            if len(ticks) >= 2:
                first = min(ticks, key=lambda item: abs(item[0] - x0))
                last = min(ticks, key=lambda item: abs(item[0] - x1))
                if first is not last and abs(first[0] - x0) <= 14.0 and abs(last[0] - x1) <= 14.0 and last[0] - first[0] >= max(40.0, token_w * 1.25):
                    parallel = [(oy, ox0, ox1) for oy, ox0, ox1 in main_candidates if oy != y and 10.0 <= abs(oy - y) <= 80.0 and _same_span(x0, x1, ox0, ox1)]
                    if any(first[1] - 6.0 <= oy <= first[2] + 6.0 and last[1] - 6.0 <= oy <= last[2] + 6.0 for oy, _, _ in parallel):
                        closed_frame_seen = True
                    else:
                        return {"confirmed": True, "orientation": "HORIZONTAL", "terminal_tick_count": 2, "tick_style": "PERPENDICULAR", "endpoint_a_px": [float(first[0]), float(y)], "endpoint_b_px": [float(last[0]), float(y)], "reason": None}

            slash_positions = []
            for line in segments:
                x = _diagonal_intersection_x(line, y)
                if x is not None and x0 - 8.0 <= x <= x1 + 8.0:
                    slash_positions.append(float(x))
            pair = _bracketing_pair(slash_positions, left + 20.0, right - 20.0, max(40.0, token_w * 1.25))
            if pair is not None:
                first_x, last_x = pair
                return {"confirmed": True, "orientation": "HORIZONTAL", "terminal_tick_count": 2, "tick_style": "DIAGONAL_SLASH", "endpoint_a_px": [float(first_x), float(y)], "endpoint_b_px": [float(last_x), float(y)], "reason": None}

    return {"confirmed": False, "orientation": orientation, "terminal_tick_count": 0, "tick_style": None, "endpoint_a_px": None, "endpoint_b_px": None, "reason": "CLOSED_FRAME_PATTERN" if closed_frame_seen else "TWO_SHORT_TERMINAL_TICKS_NOT_OBSERVED"}


def _canonical_ocr_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "").replace(",", ".")
    return text or None


def classify_numeric_graphic_role(
    *, raw_text: str, consensus_text: str | None, consensus_count: int, ocr_rotation_degrees: int,
    token_bbox_px: Sequence[float], line_segments: Iterable[Sequence[float]], nearby_closed_frame: bool,
) -> dict[str, Any]:
    raw = _canonical_ocr_text(raw_text)
    consensus = _canonical_ocr_text(consensus_text)
    if not raw:
        raise ValueError("CAL01_NUMERIC_TEXT_REQUIRED")
    if isinstance(consensus_count, bool) or int(consensus_count) < 0:
        raise ValueError("CAL01_CONSENSUS_COUNT_INVALID")
    base = {"documented_text": consensus or raw, "metric_value_m": None, "primary_anchor_authorized": False, "canonical_geometry_authorized": False, "engineering_authority_effect": "NONE"}
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
