from __future__ import annotations

from typing import Any, Iterable, Sequence

from experiments.cew_cal01.exact_source import AUTHORITY_CLOSED


_VALID_SIDES = {"TOP", "RIGHT", "BOTTOM", "LEFT"}
_AXIS_BASE_TOLERANCE_PX = 12.0
_AXIS_MAX_TOLERANCE_PX = 30.0
_TICK_CLUSTER_TOLERANCE_PX = 8.0
_MIN_CROSSING_TICK_PX = 50.0
_MAX_CROSSING_TICK_PX = 120.0
_MIN_BALANCED_SHORT_TICK_PX = 36.0
_MIN_BALANCED_ARM_PX = 15.0
_ENDPOINT_TICK_DISTANCE_PX = 50.0
_OBSERVATION_SUPPORT_DISTANCE_PX = 100.0
_ASSIGNMENT_AMBIGUITY_PX = 8.0
_MAX_PERIMETER_OFFSET_PX = 500.0


def _segment(raw: Sequence[float]) -> tuple[float, float, float, float]:
    if len(raw) != 4:
        raise ValueError("CAL01_EXTERNAL_CHAIN_REFINEMENT_SEGMENT_INVALID")
    return tuple(float(value) for value in raw)


def _bbox(raw: Sequence[float]) -> tuple[float, float, float, float]:
    if len(raw) != 4:
        raise ValueError("CAL01_EXTERNAL_CHAIN_REFINEMENT_BBOX_INVALID")
    left, top, right, bottom = (float(value) for value in raw)
    if right <= left or bottom <= top:
        raise ValueError("CAL01_EXTERNAL_CHAIN_REFINEMENT_BBOX_INVALID")
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


def _cluster_positions(values: Iterable[float]) -> list[float]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return []
    groups: list[list[float]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - groups[-1][-1] <= _TICK_CLUSTER_TOLERANCE_PX:
            groups[-1].append(value)
        else:
            groups.append([value])
    return [round(sum(group) / len(group), 6) for group in groups]


def _observation_center(observation: dict[str, Any]) -> tuple[float, float]:
    left, top, right, bottom = _bbox(observation.get("bbox_normalized_px") or [])
    return (left + right) / 2.0, (top + bottom) / 2.0


def _merge_axis_segments(
    *,
    side: str,
    axis_segments: Iterable[Sequence[float]],
    plan_envelope_bbox: Sequence[float],
) -> list[dict[str, float]]:
    left, top, right, bottom = _bbox(plan_envelope_bbox)
    horizontal = side in {"TOP", "BOTTOM"}
    plan_span = (right - left) if horizontal else (bottom - top)
    axis_tolerance = max(
        _AXIS_BASE_TOLERANCE_PX,
        min(_AXIS_MAX_TOLERANCE_PX, plan_span * 0.004),
    )
    gap_tolerance = max(80.0, plan_span * 0.16)
    minimum_span = max(120.0, plan_span * 0.12)

    rows: list[tuple[float, float, float]] = []
    for raw in axis_segments:
        line = _segment(raw)
        is_axis, start, end, axis = _horizontal(line) if horizontal else _vertical(line)
        if is_axis:
            rows.append((axis, start, end))
    rows.sort(key=lambda row: (row[0], row[1], row[2]))

    axis_groups: list[list[tuple[float, float, float]]] = []
    for row in rows:
        matches: list[tuple[float, int]] = []
        for index, group in enumerate(axis_groups):
            group_axis = sum(item[0] for item in group) / len(group)
            distance = abs(row[0] - group_axis)
            if distance <= axis_tolerance:
                matches.append((distance, index))
        if matches:
            axis_groups[min(matches)[1]].append(row)
        else:
            axis_groups.append([row])

    carriers: list[dict[str, float]] = []
    for group in axis_groups:
        axis = sum(item[0] for item in group) / len(group)
        spans = sorted((item[1], item[2]) for item in group)
        merged: list[list[float]] = []
        for start, end in spans:
            if not merged or start - merged[-1][1] > gap_tolerance:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        for start, end in merged:
            if end - start >= minimum_span:
                carriers.append(
                    {
                        "axis": round(float(axis), 6),
                        "start": float(start),
                        "end": float(end),
                    }
                )
    return carriers


def _side_plausible(*, side: str, carrier_axis: float, plan_envelope_bbox: Sequence[float]) -> bool:
    left, top, right, bottom = _bbox(plan_envelope_bbox)
    edge = {"TOP": top, "RIGHT": right, "BOTTOM": bottom, "LEFT": left}[side]
    if abs(carrier_axis - edge) > _MAX_PERIMETER_OFFSET_PX:
        return False
    cross_span = (bottom - top) if side in {"TOP", "BOTTOM"} else (right - left)
    inside_tolerance = max(120.0, cross_span * 0.02)
    if side == "TOP":
        return carrier_axis <= top + inside_tolerance
    if side == "BOTTOM":
        return carrier_axis >= bottom - inside_tolerance
    if side == "LEFT":
        return carrier_axis <= left + inside_tolerance
    return carrier_axis >= right - inside_tolerance


def _supporting_observations(
    *,
    side: str,
    carrier: dict[str, float],
    observations: list[dict[str, Any]],
) -> list[tuple[float, float, str]]:
    horizontal = side in {"TOP", "BOTTOM"}
    support: list[tuple[float, float, str]] = []
    for observation in observations:
        if str(observation.get("search_band") or "").upper() != side:
            continue
        observation_id = str(observation.get("observation_id") or "")
        if not observation_id:
            raise ValueError("CAL01_EXTERNAL_CHAIN_REFINEMENT_OBSERVATION_ID_REQUIRED")
        cx, cy = _observation_center(observation)
        along = cx if horizontal else cy
        perpendicular = cy if horizontal else cx
        if carrier["start"] - 40.0 <= along <= carrier["end"] + 40.0:
            distance = abs(perpendicular - carrier["axis"])
            if distance <= _OBSERVATION_SUPPORT_DISTANCE_PX:
                support.append((distance, along, observation_id))
    support.sort(key=lambda row: (row[0], row[1], row[2]))
    return support


def _crossing_tick_positions(
    *,
    side: str,
    carrier: dict[str, float],
    tick_segments: Iterable[Sequence[float]],
) -> list[float]:
    horizontal = side in {"TOP", "BOTTOM"}
    axis = carrier["axis"]
    positions: list[float] = []

    for raw in tick_segments:
        line = _segment(raw)
        if horizontal:
            is_tick, cross_start, cross_end, position = _vertical(line)
        else:
            is_tick, cross_start, cross_end, position = _horizontal(line)
        if not is_tick:
            continue
        if not (carrier["start"] - 12.0 <= position <= carrier["end"] + 12.0):
            continue
        if not (cross_start - 6.0 <= axis <= cross_end + 6.0):
            continue

        crossing_length = cross_end - cross_start
        before_axis = max(0.0, axis - cross_start)
        after_axis = max(0.0, cross_end - axis)
        endpoint_distance = min(
            abs(position - carrier["start"]),
            abs(position - carrier["end"]),
        )
        strong_tick = _MIN_CROSSING_TICK_PX <= crossing_length <= _MAX_CROSSING_TICK_PX
        balanced_short_tick = (
            _MIN_BALANCED_SHORT_TICK_PX <= crossing_length < _MIN_CROSSING_TICK_PX
            and min(before_axis, after_axis) >= _MIN_BALANCED_ARM_PX
        )
        weak_endpoint_tick = (
            crossing_length >= 16.0
            and crossing_length < _MIN_CROSSING_TICK_PX
            and endpoint_distance <= _ENDPOINT_TICK_DISTANCE_PX
        )
        if strong_tick or balanced_short_tick or weak_endpoint_tick:
            positions.append(float(position))

    return _cluster_positions(positions)


def _carrier_order(side: str, carrier: dict[str, Any], plan_envelope_bbox: Sequence[float]) -> tuple[float, float]:
    left, top, right, bottom = _bbox(plan_envelope_bbox)
    edge = {"TOP": top, "RIGHT": right, "BOTTOM": bottom, "LEFT": left}[side]
    return (abs(float(carrier["carrier_axis_px"]) - edge), float(carrier["carrier_axis_px"]))


def build_refined_external_chains(
    *,
    side: str,
    axis_segments: Iterable[Sequence[float]],
    tick_segments: Iterable[Sequence[float]],
    observations: Iterable[dict[str, Any]],
    plan_envelope_bbox: Sequence[float],
) -> dict[str, Any]:
    normalized_side = str(side).upper()
    if normalized_side not in _VALID_SIDES:
        raise ValueError("CAL01_EXTERNAL_CHAIN_REFINEMENT_SIDE_INVALID")
    _bbox(plan_envelope_bbox)
    observation_rows = [dict(row) for row in observations]
    horizontal = normalized_side in {"TOP", "BOTTOM"}
    orientation = "HORIZONTAL" if horizontal else "VERTICAL"

    chains: list[dict[str, Any]] = []
    for carrier in _merge_axis_segments(
        side=normalized_side,
        axis_segments=axis_segments,
        plan_envelope_bbox=plan_envelope_bbox,
    ):
        if not _side_plausible(
            side=normalized_side,
            carrier_axis=carrier["axis"],
            plan_envelope_bbox=plan_envelope_bbox,
        ):
            continue
        support = _supporting_observations(
            side=normalized_side,
            carrier=carrier,
            observations=observation_rows,
        )
        if not support:
            continue
        tick_positions = _crossing_tick_positions(
            side=normalized_side,
            carrier=carrier,
            tick_segments=tick_segments,
        )
        if len(tick_positions) < 3:
            continue
        intervals = [
            {
                "interval_index": index,
                "start_px": float(tick_positions[index]),
                "end_px": float(tick_positions[index + 1]),
                "member_observation_ids": [],
            }
            for index in range(len(tick_positions) - 1)
            if tick_positions[index + 1] - tick_positions[index] >= 20.0
        ]
        if len(intervals) < 2:
            continue
        chains.append(
            {
                "orientation": orientation,
                "carrier_axis_px": float(carrier["axis"]),
                "carrier_start_px": float(carrier["start"]),
                "carrier_end_px": float(carrier["end"]),
                "tick_positions_px": [float(value) for value in tick_positions],
                "intervals": intervals,
                "member_observation_ids": [],
                "supporting_observation_ids": [row[2] for row in support],
                "primary_anchor_authorized": False,
                "eligible_for_metric_calibration": False,
            }
        )

    chains.sort(key=lambda row: _carrier_order(normalized_side, row, plan_envelope_bbox))
    for index, chain in enumerate(chains):
        chain["chain_id"] = f"{normalized_side}:R{index + 1}"

    unresolved: list[str] = []
    for observation in observation_rows:
        if str(observation.get("search_band") or "").upper() != normalized_side:
            continue
        observation_id = str(observation.get("observation_id") or "")
        if not observation_id:
            raise ValueError("CAL01_EXTERNAL_CHAIN_REFINEMENT_OBSERVATION_ID_REQUIRED")
        cx, cy = _observation_center(observation)
        along = cx if horizontal else cy
        perpendicular = cy if horizontal else cx
        options: list[tuple[float, int, int]] = []
        for chain_index, chain in enumerate(chains):
            distance = abs(perpendicular - float(chain["carrier_axis_px"]))
            if distance > _OBSERVATION_SUPPORT_DISTANCE_PX:
                continue
            for interval_index, interval in enumerate(chain["intervals"]):
                if float(interval["start_px"]) <= along <= float(interval["end_px"]):
                    options.append((distance, chain_index, interval_index))
        if not options:
            unresolved.append(observation_id)
            continue
        options.sort(key=lambda row: (row[0], row[1], row[2]))
        if len(options) > 1 and abs(options[1][0] - options[0][0]) <= _ASSIGNMENT_AMBIGUITY_PX:
            unresolved.append(observation_id)
            continue
        _distance, chain_index, interval_index = options[0]
        chains[chain_index]["intervals"][interval_index]["member_observation_ids"].append(observation_id)
        chains[chain_index]["member_observation_ids"].append((along, observation_id))

    for chain in chains:
        chain["member_observation_ids"] = [
            observation_id
            for _along, observation_id in sorted(chain["member_observation_ids"], key=lambda row: (row[0], row[1]))
        ]
        for interval in chain["intervals"]:
            interval["member_observation_ids"] = sorted(set(interval["member_observation_ids"]))
        chain["member_observation_count"] = len(chain["member_observation_ids"])

    return {
        "schema": "CEW_CAL01_REFINED_EXTERNAL_DIMENSION_CHAIN_v1",
        "side": normalized_side,
        "orientation": orientation,
        "chain_count": len(chains),
        "chains": chains,
        "member_observation_count": sum(int(row["member_observation_count"]) for row in chains),
        "unresolved_observation_ids": sorted(set(unresolved)),
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
