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
_MIN_CHAIN_INTERVAL_PX = 32.0
_MIN_CHAIN_INTERVAL_FRACTION = 0.04
_LOCATION_OVERLAP_FRACTION = 0.50
_LOCATION_CENTER_TOLERANCE_PX = 16.0


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


def _normalize_tick_sequence(
    *,
    positions: Sequence[float],
    carrier: dict[str, float],
    horizontal: bool,
    plan_envelope_bbox: Sequence[float],
) -> list[float] | None:
    ordered = sorted(float(value) for value in positions)
    if not ordered:
        return []
    left, top, right, bottom = _bbox(plan_envelope_bbox)
    plan_span = (right - left) if horizontal else (bottom - top)
    minimum_interval = max(_MIN_CHAIN_INTERVAL_PX, plan_span * _MIN_CHAIN_INTERVAL_FRACTION)

    proximity_groups: list[list[float]] = [[ordered[0]]]
    for value in ordered[1:]:
        if value - proximity_groups[-1][-1] < minimum_interval:
            proximity_groups[-1].append(value)
        else:
            proximity_groups.append([value])

    normalized: list[float] = []
    for group in proximity_groups:
        if len(group) == 1:
            normalized.append(group[0])
            continue
        if len(group) >= 3:
            return None
        endpoint_candidates = [
            value
            for value in group
            if min(
                abs(value - float(carrier["start"])),
                abs(value - float(carrier["end"])),
            )
            <= _ENDPOINT_TICK_DISTANCE_PX
        ]
        if len(endpoint_candidates) != 1:
            return None
        normalized.append(endpoint_candidates[0])
    return normalized


def _same_graphic_location(left_observation: dict[str, Any], right_observation: dict[str, Any]) -> bool:
    left = _bbox(left_observation.get("bbox_normalized_px") or [])
    right = _bbox(right_observation.get("bbox_normalized_px") or [])
    lx0, ly0, lx1, ly1 = left
    rx0, ry0, rx1, ry1 = right
    intersection_width = max(0.0, min(lx1, rx1) - max(lx0, rx0))
    intersection_height = max(0.0, min(ly1, ry1) - max(ly0, ry0))
    intersection_area = intersection_width * intersection_height
    left_area = (lx1 - lx0) * (ly1 - ly0)
    right_area = (rx1 - rx0) * (ry1 - ry0)
    if min(left_area, right_area) > 0.0:
        overlap_fraction = intersection_area / min(left_area, right_area)
        if overlap_fraction >= _LOCATION_OVERLAP_FRACTION:
            return True
    left_center = ((lx0 + lx1) / 2.0, (ly0 + ly1) / 2.0)
    right_center = ((rx0 + rx1) / 2.0, (ry0 + ry1) / 2.0)
    return (
        abs(left_center[0] - right_center[0]) <= _LOCATION_CENTER_TOLERANCE_PX
        and abs(left_center[1] - right_center[1]) <= _LOCATION_CENTER_TOLERANCE_PX
    )


def _cluster_observation_locations(
    observation_ids: Iterable[str],
    *,
    observation_by_id: dict[str, dict[str, Any]],
    horizontal: bool,
) -> list[list[str]]:
    rows: list[tuple[float, float, str]] = []
    for observation_id in sorted(set(str(value) for value in observation_ids)):
        observation = observation_by_id[observation_id]
        cx, cy = _observation_center(observation)
        rows.append((cx if horizontal else cy, cy if horizontal else cx, observation_id))
    rows.sort(key=lambda row: (row[0], row[1], row[2]))

    groups: list[list[str]] = []
    for _along, _perpendicular, observation_id in rows:
        observation = observation_by_id[observation_id]
        target_group = None
        for group_index, group in enumerate(groups):
            if any(
                _same_graphic_location(observation, observation_by_id[member_id])
                for member_id in group
            ):
                target_group = group_index
                break
        if target_group is None:
            groups.append([observation_id])
        else:
            groups[target_group].append(observation_id)

    for group in groups:
        group.sort()
    return groups


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
    observation_by_id: dict[str, dict[str, Any]] = {}
    for observation in observation_rows:
        observation_id = str(observation.get("observation_id") or "")
        if not observation_id:
            raise ValueError("CAL01_EXTERNAL_CHAIN_REFINEMENT_OBSERVATION_ID_REQUIRED")
        observation_by_id[observation_id] = observation
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
        raw_tick_positions = _crossing_tick_positions(
            side=normalized_side,
            carrier=carrier,
            tick_segments=tick_segments,
        )
        tick_positions = _normalize_tick_sequence(
            positions=raw_tick_positions,
            carrier=carrier,
            horizontal=horizontal,
            plan_envelope_bbox=plan_envelope_bbox,
        )
        if tick_positions is None or len(tick_positions) < 3:
            continue
        intervals = [
            {
                "interval_index": index,
                "start_px": float(tick_positions[index]),
                "end_px": float(tick_positions[index + 1]),
                "member_observation_ids": [],
            }
            for index in range(len(tick_positions) - 1)
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
        chains[chain_index]["member_observation_ids"].append(observation_id)

    for chain in chains:
        chain_location_groups = _cluster_observation_locations(
            chain["member_observation_ids"],
            observation_by_id=observation_by_id,
            horizontal=horizontal,
        )
        chain["member_location_groups"] = chain_location_groups
        chain["member_observation_ids"] = [
            observation_id
            for group in chain_location_groups
            for observation_id in group
        ]
        chain["member_observation_count"] = len(chain_location_groups)
        for interval in chain["intervals"]:
            interval_location_groups = _cluster_observation_locations(
                interval["member_observation_ids"],
                observation_by_id=observation_by_id,
                horizontal=horizontal,
            )
            interval["member_location_groups"] = interval_location_groups
            interval["member_observation_ids"] = [
                observation_id
                for group in interval_location_groups
                for observation_id in group
            ]
            interval["member_observation_count"] = len(interval_location_groups)

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
