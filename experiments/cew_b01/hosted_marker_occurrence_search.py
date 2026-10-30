from __future__ import annotations

import math
from collections import deque
from typing import Any, Sequence

from .beam_hosted_marker_hybrid import build_hybrid_hosted_marker_candidates


def _scope_key(item: dict[str, Any]) -> tuple[str, int, str]:
    source = item.get("source", {})
    return (
        str(source.get("sha256", "")),
        int(item.get("page_index", 0)),
        str(item.get("frame", "")),
    )


def _intersect_area(first: dict[str, Any], second: dict[str, Any]) -> float:
    ax0 = float(first["x"])
    ay0 = float(first["y"])
    ax1 = ax0 + float(first["width"])
    ay1 = ay0 + float(first["height"])
    bx0 = float(second["x"])
    by0 = float(second["y"])
    bx1 = bx0 + float(second["width"])
    by1 = by0 + float(second["height"])
    return max(0.0, min(ax1, bx1) - max(ax0, bx0)) * max(0.0, min(ay1, by1) - max(ay0, by0))


def _inner_geometry(geometry: dict[str, Any]) -> dict[str, float]:
    width = max(float(geometry["width"]), 1.0)
    height = max(float(geometry["height"]), 1.0)
    inset = max(2.0, round(min(width, height) * 0.08, 6))
    inner_width = max(0.0, width - 2.0 * inset)
    inner_height = max(0.0, height - 2.0 * inset)
    return {
        "x": float(geometry["x"]) + inset,
        "y": float(geometry["y"]) + inset,
        "width": inner_width,
        "height": inner_height,
    }


def _binary_dimensions(binary_ink: Sequence[Sequence[Any]]) -> tuple[int, int]:
    height = len(binary_ink)
    width = len(binary_ink[0]) if height else 0
    return width, height


def _enclosed_ink_components(
    binary_ink: Sequence[Sequence[Any]],
    geometry: dict[str, Any],
) -> list[int]:
    """Return areas of ink components enclosed inside the marker footprint.

    Marker borders and carrier/transverse lines reach the marker boundary and
    are intentionally excluded. Compact components fully enclosed away from the
    boundary are retained as neutral evidence of annotation-like internal ink.
    """

    image_width, image_height = _binary_dimensions(binary_ink)
    if image_width <= 0 or image_height <= 0:
        return []

    x0 = max(0, int(math.floor(float(geometry["x"]))))
    y0 = max(0, int(math.floor(float(geometry["y"]))))
    x1 = min(image_width, int(math.ceil(float(geometry["x"]) + float(geometry["width"]))))
    y1 = min(image_height, int(math.ceil(float(geometry["y"]) + float(geometry["height"]))))
    if x1 <= x0 or y1 <= y0:
        return []

    width = x1 - x0
    height = y1 - y0
    border_band = max(2, int(round(min(width, height) * 0.08)))
    visited: set[tuple[int, int]] = set()
    enclosed: list[int] = []

    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x, y) in visited or not bool(binary_ink[y][x]):
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited.add((x, y))
            area = 0
            touches_border_band = False
            while queue:
                px, py = queue.popleft()
                area += 1
                if (
                    px < x0 + border_band
                    or px >= x1 - border_band
                    or py < y0 + border_band
                    or py >= y1 - border_band
                ):
                    touches_border_band = True
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = px + dx, py + dy
                        if nx < x0 or nx >= x1 or ny < y0 or ny >= y1:
                            continue
                        if (nx, ny) in visited or not bool(binary_ink[ny][nx]):
                            continue
                        visited.add((nx, ny))
                        queue.append((nx, ny))
            if not touches_border_band and area >= 4:
                enclosed.append(area)

    return sorted(enclosed, reverse=True)


def _effective_text_component_area(primitive: dict[str, Any], overlap_area: float) -> float:
    """Estimate real TEXT_BLOCK ink inside the marker, not its bounding-box area."""

    geometry = primitive.get("geometry", {})
    bbox_area = max(float(geometry.get("width", 0.0)) * float(geometry.get("height", 0.0)), 0.0)
    if bbox_area <= 0.0 or overlap_area <= 0.0:
        return 0.0

    signature = primitive.get("feature_signature") or {}
    component_area = signature.get("component_area")
    if component_area is not None:
        full_component_area = max(float(component_area), 0.0)
    elif signature.get("ink_ratio") is not None:
        full_component_area = max(bbox_area * float(signature["ink_ratio"]), 0.0)
    else:
        # Compatibility fallback for legacy/synthetic TEXT_BLOCK observations
        # without ink metadata. The overlap is kept conservatively as evidence.
        full_component_area = bbox_area

    overlap_fraction = min(1.0, max(0.0, overlap_area / bbox_area))
    return full_component_area * overlap_fraction


def _annotation_evidence(
    candidate: dict[str, Any],
    primitives: list[dict[str, Any]],
    binary_ink: Sequence[Sequence[Any]],
) -> dict[str, Any]:
    geometry = dict(candidate["marker_geometry"])
    inner = _inner_geometry(geometry)
    marker_scope = None
    marker_id = str(candidate["marker_primitive_id"])
    for primitive in primitives:
        if str(primitive.get("primitive_id")) == marker_id:
            marker_scope = _scope_key(primitive)
            break

    marker_area = max(float(geometry["width"]) * float(geometry["height"]), 1.0)
    minimum_text_component_area = max(8.0, marker_area * 0.01)
    overlapping_text_ids: list[str] = []
    ignored_tiny_text_ids: list[str] = []
    text_overlap_areas: dict[str, float] = {}
    text_component_areas: dict[str, float] = {}
    if marker_scope is not None and inner["width"] > 0.0 and inner["height"] > 0.0:
        for primitive in primitives:
            if primitive.get("family") != "TEXT_BLOCK" or _scope_key(primitive) != marker_scope:
                continue
            primitive_id = str(primitive["primitive_id"])
            overlap_area = _intersect_area(inner, primitive["geometry"])
            if overlap_area <= 0.0:
                continue
            effective_component_area = _effective_text_component_area(primitive, overlap_area)
            text_overlap_areas[primitive_id] = round(overlap_area, 6)
            text_component_areas[primitive_id] = round(effective_component_area, 6)
            if effective_component_area >= minimum_text_component_area:
                overlapping_text_ids.append(primitive_id)
            else:
                ignored_tiny_text_ids.append(primitive_id)

    components = _enclosed_ink_components(binary_ink, geometry)
    component_area = sum(components)
    minimum_annotation_area = max(8, int(round(marker_area * 0.01)))
    enclosed_annotation_like = bool(components) and component_area >= minimum_annotation_area
    annotation_dominated = bool(overlapping_text_ids) or enclosed_annotation_like

    return {
        "overlapping_text_block_ids": sorted(overlapping_text_ids),
        "ignored_tiny_text_block_ids": sorted(ignored_tiny_text_ids),
        "text_overlap_areas": {key: text_overlap_areas[key] for key in sorted(text_overlap_areas)},
        "text_component_areas": {key: text_component_areas[key] for key in sorted(text_component_areas)},
        "minimum_text_component_area": round(minimum_text_component_area, 6),
        "enclosed_component_count": len(components),
        "enclosed_component_areas": components,
        "enclosed_component_area": component_area,
        "enclosed_component_area_fraction": round(component_area / marker_area, 12),
        "minimum_annotation_area": minimum_annotation_area,
        "annotation_dominated": annotation_dominated,
        "signals": sorted(
            (["TEXT_BLOCK_OVERLAP"] if overlapping_text_ids else [])
            + (["ENCLOSED_INTERNAL_INK"] if enclosed_annotation_like else [])
        ),
    }


def analyze_hosted_marker_occurrences(
    primitives: list[dict[str, Any]],
    binary_ink: Sequence[Sequence[Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Preserve all bound occurrences while separating annotation-dominated cases."""

    marker_seed_ids = sorted(
        str(item["primitive_id"])
        for item in primitives
        if item.get("family") == "RECTILINEAR_CLOSED_SHAPE"
    )
    if not marker_seed_ids:
        return {"all_bound": [], "review_eligible": [], "annotation_dominated": []}

    bound = build_hybrid_hosted_marker_candidates(primitives, marker_seed_ids, binary_ink)
    all_bound: list[dict[str, Any]] = []
    review_eligible: list[dict[str, Any]] = []
    annotation_dominated: list[dict[str, Any]] = []

    for candidate in bound:
        item = dict(candidate)
        evidence = _annotation_evidence(item, primitives, binary_ink)
        item["annotation_evidence"] = evidence
        item["candidate_role"] = "ANNOTATION_DOMINATED" if evidence["annotation_dominated"] else "REVIEW_ELIGIBLE"
        all_bound.append(item)
        if evidence["annotation_dominated"]:
            annotation_dominated.append(item)
        else:
            review_eligible.append(item)

    key = lambda item: (str(item["marker_primitive_id"]), str(item["hosted_marker_id"]))
    return {
        "all_bound": sorted(all_bound, key=key),
        "review_eligible": sorted(review_eligible, key=key),
        "annotation_dominated": sorted(annotation_dominated, key=key),
    }


def discover_hosted_marker_occurrences(
    primitives: list[dict[str, Any]],
    binary_ink: Sequence[Sequence[Any]],
) -> list[dict[str, Any]]:
    """Return only review-eligible hosted markers; preserve rejects via analyze()."""

    return analyze_hosted_marker_occurrences(primitives, binary_ink)["review_eligible"]


def pair_evidence_overlay_spec(
    candidate: dict[str, Any],
    tracks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Expose primitive and raster pair evidence separately for review rendering."""

    track_by_id = {str(track["track_id"]): track for track in tracks}
    overlays: list[dict[str, Any]] = []
    for track_id in candidate.get("transverse_pair_track_ids", []):
        track = track_by_id.get(str(track_id))
        if track is None:
            continue
        overlays.append({
            "source": "PRIMITIVE_LOCAL_TRACK_PAIR",
            "track_id": str(track_id),
            "orientation": str(track["orientation"]),
            "centerline": float(track["centerline"]),
            "start": float(track["start"]),
            "end": float(track["end"]),
        })

    raster = candidate.get("raster_transverse_evidence") or {}
    pair_strokes = list(raster.get("pair_strokes") or [])
    if bool(raster.get("pair_detected")) and len(pair_strokes) >= 2:
        orientation = "VERTICAL" if candidate.get("carrier_orientation") == "HORIZONTAL" else "HORIZONTAL"
        start = float(raster.get("cross_search_start", 0.0))
        end = float(raster.get("cross_search_end", 0.0))
        for stroke in pair_strokes[:2]:
            overlays.append({
                "source": "RASTER_LOCAL_PROFILE",
                "track_id": None,
                "orientation": orientation,
                "centerline": float(stroke["center"]),
                "start": start,
                "end": end,
                "width": float(stroke.get("width", 0.0)),
            })

    return sorted(
        overlays,
        key=lambda item: (
            item["source"],
            item["orientation"],
            item["centerline"],
            str(item.get("track_id") or ""),
        ),
    )


def hosted_marker_signature(candidate: dict[str, Any]) -> dict[str, float]:
    """Return scale-normalized neutral geometry used only for review ordering."""

    geometry = candidate["marker_geometry"]
    width = float(geometry["width"])
    height = float(geometry["height"])
    orientation = str(candidate["carrier_orientation"])
    if orientation == "HORIZONTAL":
        long_span, cross_span = width, height
    elif orientation == "VERTICAL":
        long_span, cross_span = height, width
    else:
        raise ValueError("HOSTED_MARKER_SIGNATURE_INVALID_ORIENTATION")

    long_span = max(long_span, 1e-9)
    cross_span = max(cross_span, 1e-9)
    overlap_length = max(
        float(candidate["carrier_overlap_end"]) - float(candidate["carrier_overlap_start"]),
        1e-9,
    )
    signature = {
        "marker_long_to_cross": long_span / cross_span,
        "carrier_separation_to_marker_cross_span": float(candidate["carrier_separation"]) / cross_span,
        "marker_long_span_to_carrier_overlap": long_span / overlap_length,
    }

    raster = candidate.get("raster_transverse_evidence") or {}
    pair_strokes = list(raster.get("pair_strokes") or [])
    if bool(raster.get("pair_detected")) and len(pair_strokes) >= 2:
        centers = sorted(float(stroke["center"]) for stroke in pair_strokes[:2])
        separation = abs(centers[1] - centers[0])
        if separation > 0.0:
            signature["raster_pair_separation_to_marker_long_span"] = separation / long_span

    return {key: round(float(value), 12) for key, value in sorted(signature.items())}


def prototype_distance(
    candidate_signature: dict[str, float],
    prototype_signature: dict[str, float],
) -> float:
    """Compare only shared positive signature components using log-ratio distance."""

    shared = sorted(set(candidate_signature) & set(prototype_signature))
    if not shared:
        raise ValueError("HOSTED_MARKER_PROTOTYPE_NO_SHARED_SIGNATURE")

    distance = 0.0
    compared = 0
    for key in shared:
        candidate_value = float(candidate_signature[key])
        prototype_value = float(prototype_signature[key])
        if candidate_value <= 0.0 or prototype_value <= 0.0:
            continue
        distance += abs(math.log(candidate_value / prototype_value))
        compared += 1
    if compared == 0:
        raise ValueError("HOSTED_MARKER_PROTOTYPE_NO_POSITIVE_SIGNATURE")
    return round(distance, 12)


def _geometry_sort_key(candidate: dict[str, Any]) -> tuple[float, float, float, float]:
    geometry = candidate["marker_geometry"]
    return (
        float(geometry["y"]),
        float(geometry["x"]),
        float(geometry["height"]),
        float(geometry["width"]),
    )


def rank_occurrences_for_review(
    occurrences: list[dict[str, Any]],
    prototype_by_state: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rank additional same-state occurrences by neutral prototype resemblance.

    Frozen prototypes are excluded from the returned review list. Ranking is for
    human-review ordering only and never changes the candidate graphical state.
    """

    prototype_signatures = {
        state: hosted_marker_signature(prototype)
        for state, prototype in prototype_by_state.items()
    }
    prototype_ids = {
        state: str(prototype["marker_primitive_id"])
        for state, prototype in prototype_by_state.items()
    }

    ranked: list[dict[str, Any]] = []
    for occurrence in occurrences:
        state = str(occurrence.get("graphical_state", ""))
        if state not in prototype_by_state:
            continue
        if str(occurrence["marker_primitive_id"]) == prototype_ids[state]:
            continue

        item = dict(occurrence)
        item["prototype_marker_primitive_id"] = prototype_ids[state]
        item["prototype_distance"] = prototype_distance(
            hosted_marker_signature(occurrence),
            prototype_signatures[state],
        )
        item["review_state"] = "UNREVIEWED"
        ranked.append(item)

    return sorted(
        ranked,
        key=lambda item: (
            str(item["graphical_state"]),
            float(item["prototype_distance"]),
            _geometry_sort_key(item),
            str(item["marker_primitive_id"]),
            str(item["hosted_marker_id"]),
        ),
    )
