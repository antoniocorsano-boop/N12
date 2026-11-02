from __future__ import annotations

from math import hypot
from typing import Any, Iterable, Sequence


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}

_VALID_SIDES = {"TOP", "BOTTOM", "LEFT", "RIGHT"}
_AXIS_TOLERANCE_PX = 8.0
_TICK_CLUSTER_TOLERANCE_PX = 8.0
_CARRIER_GAP_TOLERANCE_PX = 80.0
_AMBIGUITY_TOLERANCE_PX = 8.0


def _segment(raw: Sequence[float]) -> tuple[float, float, float, float]:
    if len(raw) != 4:
        raise ValueError("CAL01_EXTERNAL_CHAIN_LINE_SEGMENT_INVALID")
    return tuple(float(value) for value in raw)


def _bbox(raw: Sequence[float]) -> tuple[float, float, float, float]:
    if len(raw) != 4:
        raise ValueError("CAL01_EXTERNAL_CHAIN_BBOX_INVALID")
    left, top, right, bottom = (float(value) for value in raw)
    if right <= left or bottom <= top:
        raise ValueError("CAL01_EXTERNAL_CHAIN_BBOX_INVALID")
    return left, top, right, bottom


def _horizontal(line: tuple[float, float, float, float]) -> tuple[bool, float, float, float]:
    x1, y1, x2, y2 = line
    length = abs(x2 - x1)
    return (
        length >= 1.0 and abs(y2 - y1) <= max(3.0, length * 0.04),
        min(x1, x2),
        max(x1, x2),
        (y1 + y2) / 2.0,
    )


def _vertical(line: tuple[float, float, float, float]) -> tuple[bool, float, float, float]:
    x1, y1, x2, y2 = line
    length = abs(y2 - y1)
    return (
        length >= 1.0 and abs(x2 - x1) <= max(3.0, length * 0.04),
        min(y1, y2),
        max(y1, y2),
        (x1 + x2) / 2.0,
    )


def _short_diagonal(line: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2 = line
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    length = hypot(dx, dy)
    return 10.0 <= length <= 80.0 and dx >= 4.0 and dy >= 4.0 and min(dx, dy) / max(dx, dy) >= 0.30


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


def _cluster_positions(values: Iterable[float], *, tolerance: float = _TICK_CLUSTER_TOLERANCE_PX) -> list[float]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return []
    clusters: list[list[float]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - clusters[-1][-1] <= tolerance:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return [round(sum(cluster) / len(cluster), 6) for cluster in clusters]


def _merge_carrier_fragments(
    segments: list[tuple[float, float, float]],
    *,
    minimum_length: float,
) -> list[dict[str, float]]:
    if not segments:
        return []
    by_axis: list[list[tuple[float, float, float]]] = []
    for row in sorted(segments, key=lambda item: (item[0], item[1], item[2])):
        if not by_axis or abs(row[0] - sum(item[0] for item in by_axis[-1]) / len(by_axis[-1])) > _AXIS_TOLERANCE_PX:
            by_axis.append([row])
        else:
            by_axis[-1].append(row)

    carriers: list[dict[str, float]] = []
    for axis_group in by_axis:
        axis = sum(item[0] for item in axis_group) / len(axis_group)
        spans = sorted((item[1], item[2]) for item in axis_group)
        merged: list[list[float]] = []
        for start, end in spans:
            if not merged or start - merged[-1][1] > _CARRIER_GAP_TOLERANCE_PX:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        for start, end in merged:
            if end - start >= minimum_length:
                carriers.append({"axis": round(axis, 6), "start": float(start), "end": float(end)})
    return carriers


def _carrier_candidates(
    *,
    side: str,
    segments: list[tuple[float, float, float, float]],
    plan_bbox: tuple[float, float, float, float],
) -> list[dict[str, float]]:
    left, top, right, bottom = plan_bbox
    horizontal_side = side in {"TOP", "BOTTOM"}
    plan_span = (right - left) if horizontal_side else (bottom - top)
    minimum_length = max(120.0, plan_span * 0.25)
    side_margin = max(30.0, ((bottom - top) if horizontal_side else (right - left)) * 0.10)

    axis_segments: list[tuple[float, float, float]] = []
    for line in segments:
        if horizontal_side:
            is_axis, start, end, axis = _horizontal(line)
            if not is_axis:
                continue
            if side == "TOP" and axis > top + side_margin:
                continue
            if side == "BOTTOM" and axis < bottom - side_margin:
                continue
        else:
            is_axis, start, end, axis = _vertical(line)
            if not is_axis:
                continue
            if side == "LEFT" and axis > left + side_margin:
                continue
            if side == "RIGHT" and axis < right - side_margin:
                continue
        axis_segments.append((axis, start, end))

    return _merge_carrier_fragments(axis_segments, minimum_length=minimum_length)


def _tick_positions(
    *,
    orientation: str,
    carrier: dict[str, float],
    segments: list[tuple[float, float, float, float]],
) -> list[float]:
    axis = carrier["axis"]
    start = carrier["start"]
    end = carrier["end"]
    positions: list[float] = []

    if orientation == "HORIZONTAL":
        for line in segments:
            is_v, y0, y1, x = _vertical(line)
            if is_v and 10.0 <= y1 - y0 <= 120.0 and start - 8.0 <= x <= end + 8.0 and y0 - 6.0 <= axis <= y1 + 6.0:
                positions.append(float(x))
                continue
            slash_x = _diagonal_intersection_x(line, axis)
            if slash_x is not None and start - 8.0 <= slash_x <= end + 8.0:
                positions.append(float(slash_x))
    else:
        for line in segments:
            is_h, x0, x1, y = _horizontal(line)
            if is_h and 10.0 <= x1 - x0 <= 120.0 and start - 8.0 <= y <= end + 8.0 and x0 - 6.0 <= axis <= x1 + 6.0:
                positions.append(float(y))
                continue
            slash_y = _diagonal_intersection_y(line, axis)
            if slash_y is not None and start - 8.0 <= slash_y <= end + 8.0:
                positions.append(float(slash_y))

    return _cluster_positions(positions)


def _carrier_order(side: str, axis: float, plan_bbox: tuple[float, float, float, float]) -> tuple[float, float]:
    left, top, right, bottom = plan_bbox
    edge = {"TOP": top, "BOTTOM": bottom, "LEFT": left, "RIGHT": right}[side]
    return (abs(axis - edge), axis)


def _observation_center(observation: dict[str, Any]) -> tuple[float, float, float, float]:
    left, top, right, bottom = _bbox(observation.get("bbox_normalized_px") or [])
    return (left + right) / 2.0, (top + bottom) / 2.0, right - left, bottom - top


def detect_external_dimension_chains(
    *,
    side: str,
    line_segments: Iterable[Sequence[float]],
    observations: Iterable[dict[str, Any]],
    plan_envelope_bbox: Sequence[float],
) -> dict[str, Any]:
    normalized_side = str(side).upper()
    if normalized_side not in _VALID_SIDES:
        raise ValueError("CAL01_EXTERNAL_CHAIN_SIDE_INVALID")
    plan_bbox = _bbox(plan_envelope_bbox)
    segments = [_segment(row) for row in line_segments]
    rows = [dict(row) for row in observations]
    orientation = "HORIZONTAL" if normalized_side in {"TOP", "BOTTOM"} else "VERTICAL"

    raw_carriers = _carrier_candidates(side=normalized_side, segments=segments, plan_bbox=plan_bbox)
    qualified: list[dict[str, Any]] = []
    for carrier in raw_carriers:
        ticks = _tick_positions(orientation=orientation, carrier=carrier, segments=segments)
        ticks = [value for value in ticks if carrier["start"] - 8.0 <= value <= carrier["end"] + 8.0]
        if len(ticks) < 3:
            continue
        intervals = [
            {
                "interval_index": index,
                "start_px": float(ticks[index]),
                "end_px": float(ticks[index + 1]),
                "member_observation_ids": [],
            }
            for index in range(len(ticks) - 1)
            if ticks[index + 1] - ticks[index] >= 20.0
        ]
        if len(intervals) < 2:
            continue
        qualified.append(
            {
                "orientation": orientation,
                "carrier_axis_px": float(carrier["axis"]),
                "carrier_start_px": float(carrier["start"]),
                "carrier_end_px": float(carrier["end"]),
                "tick_positions_px": [float(value) for value in ticks],
                "intervals": intervals,
                "member_observation_ids": [],
            }
        )

    qualified.sort(key=lambda row: _carrier_order(normalized_side, row["carrier_axis_px"], plan_bbox))
    for index, chain in enumerate(qualified):
        chain["chain_id"] = f"{normalized_side}:{index + 1}"

    assignments: dict[str, tuple[int, int, float, float]] = {}
    unresolved: list[str] = []
    for observation in rows:
        observation_id = str(observation.get("observation_id") or "")
        if not observation_id:
            raise ValueError("CAL01_EXTERNAL_CHAIN_OBSERVATION_ID_REQUIRED")
        search_band = str(observation.get("search_band") or normalized_side).upper()
        if search_band != normalized_side:
            continue
        cx, cy, token_w, token_h = _observation_center(observation)
        along = cx if orientation == "HORIZONTAL" else cy
        perpendicular = cy if orientation == "HORIZONTAL" else cx
        token_perp = token_h if orientation == "HORIZONTAL" else token_w
        max_distance = max(120.0, token_perp * 4.0)
        options: list[tuple[float, int, int]] = []
        for chain_index, chain in enumerate(qualified):
            distance = abs(perpendicular - float(chain["carrier_axis_px"]))
            if distance > max_distance:
                continue
            for interval_index, interval in enumerate(chain["intervals"]):
                if float(interval["start_px"]) <= along <= float(interval["end_px"]):
                    options.append((distance, chain_index, interval_index))
        if not options:
            unresolved.append(observation_id)
            continue
        options.sort(key=lambda item: (item[0], item[1], item[2]))
        if len(options) > 1 and abs(options[1][0] - options[0][0]) <= _AMBIGUITY_TOLERANCE_PX:
            unresolved.append(observation_id)
            continue
        distance, chain_index, interval_index = options[0]
        assignments[observation_id] = (chain_index, interval_index, along, distance)

    for observation_id, (chain_index, interval_index, along, _distance) in assignments.items():
        chain = qualified[chain_index]
        chain["intervals"][interval_index]["member_observation_ids"].append((along, observation_id))
        chain["member_observation_ids"].append((along, observation_id))

    for chain in qualified:
        for interval in chain["intervals"]:
            interval["member_observation_ids"] = [
                observation_id for _along, observation_id in sorted(interval["member_observation_ids"], key=lambda item: (item[0], item[1]))
            ]
        chain["member_observation_ids"] = [
            observation_id for _along, observation_id in sorted(chain["member_observation_ids"], key=lambda item: (item[0], item[1]))
        ]
        chain["member_observation_count"] = len(chain["member_observation_ids"])
        chain["primary_anchor_authorized"] = False
        chain["eligible_for_metric_calibration"] = False

    member_count = sum(int(chain["member_observation_count"]) for chain in qualified)
    return {
        "schema": "CEW_CAL01_EXTERNAL_DIMENSION_CHAIN_v1",
        "side": normalized_side,
        "orientation": orientation,
        "chain_count": len(qualified),
        "chains": qualified,
        "member_observation_count": member_count,
        "unresolved_observation_ids": sorted(set(unresolved)),
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
