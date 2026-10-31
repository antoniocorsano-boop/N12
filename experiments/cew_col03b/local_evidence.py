from __future__ import annotations

from copy import deepcopy
import math
from typing import Any


def _bbox(value: Any, label: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    try:
        x = float(value["x"])
        y = float(value["y"])
        width = float(value["width"])
        height = float(value["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain numeric x/y/width/height") from exc
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > 1.0 + 1e-12 or y + height > 1.0 + 1e-12:
        raise ValueError(f"{label} exceeds normalized source bounds")
    return {"x": x, "y": y, "width": width, "height": height}


def derive_local_region(
    occurrence: dict[str, Any],
    *,
    margin_x: float,
    margin_y: float,
) -> dict[str, float]:
    if margin_x < 0 or margin_y < 0:
        raise ValueError("local-region margins must be non-negative")
    representation = occurrence.get("primary_graphical_representation")
    if not isinstance(representation, dict):
        raise ValueError("occurrence lacks primary graphical representation")
    box = _bbox(representation.get("bbox"), "occurrence bbox")
    left = max(0.0, box["x"] - margin_x)
    top = max(0.0, box["y"] - margin_y)
    right = min(1.0, box["x"] + box["width"] + margin_x)
    bottom = min(1.0, box["y"] + box["height"] + margin_y)
    return {"x": left, "y": top, "width": right - left, "height": bottom - top}


def _contains(outer: dict[str, float], inner: dict[str, float]) -> bool:
    return (
        inner["x"] >= outer["x"] - 1e-12
        and inner["y"] >= outer["y"] - 1e-12
        and inner["x"] + inner["width"] <= outer["x"] + outer["width"] + 1e-12
        and inner["y"] + inner["height"] <= outer["y"] + outer["height"] + 1e-12
    )


def _intersects(a: dict[str, float], b: dict[str, float]) -> bool:
    return not (
        a["x"] + a["width"] <= b["x"]
        or b["x"] + b["width"] <= a["x"]
        or a["y"] + a["height"] <= b["y"]
        or b["y"] + b["height"] <= a["y"]
    )


def classify_text_relation(
    *,
    occurrence_bbox: dict[str, float],
    text_bbox: dict[str, float],
    local_region: dict[str, float],
) -> str:
    occurrence = _bbox(occurrence_bbox, "occurrence bbox")
    text = _bbox(text_bbox, "text bbox")
    region = _bbox(local_region, "local region")
    if _contains(occurrence, text):
        return "INTERNAL"
    if _intersects(occurrence, text):
        return "INTERSECTING"
    if _intersects(region, text) or _contains(region, text):
        return "NEARBY"
    return "OUTSIDE"


def _center(box: dict[str, float]) -> tuple[float, float]:
    return box["x"] + box["width"] / 2.0, box["y"] + box["height"] / 2.0


def _direction(occurrence: dict[str, float], other: dict[str, float]) -> str:
    ox, oy = _center(occurrence)
    tx, ty = _center(other)
    dx, dy = tx - ox, ty - oy
    if abs(dx) >= abs(dy):
        return "RIGHT" if dx >= 0 else "LEFT"
    return "DOWN" if dy >= 0 else "UP"


def build_text_evidence(
    *,
    evidence_id: str,
    occurrence_id: str,
    occurrence_bbox: dict[str, float],
    text_bbox: dict[str, float],
    local_region: dict[str, float],
    raw_text: str,
    normalized_text: str,
    extraction_method: str,
    provenance_ref: str,
) -> dict[str, Any]:
    occurrence = _bbox(occurrence_bbox, "occurrence bbox")
    text = _bbox(text_bbox, "text bbox")
    relation = classify_text_relation(
        occurrence_bbox=occurrence,
        text_bbox=text,
        local_region=local_region,
    )
    ox, oy = _center(occurrence)
    tx, ty = _center(text)
    distance = math.hypot(tx - ox, ty - oy)
    evidence_class = {
        "INTERNAL": "DIRECT_GRAPHICAL_BINDING",
        "INTERSECTING": "AMBIGUOUS_TEXT",
        "NEARBY": "PROXIMITY_ONLY",
        "OUTSIDE": "NO_EVIDENCE",
    }[relation]
    return {
        "evidence_id": str(evidence_id),
        "occurrence_id": str(occurrence_id),
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "extraction_method": extraction_method,
        "text_bbox": text,
        "relation": relation,
        "evidence_class": evidence_class,
        "normalized_distance": distance,
        "direction": _direction(occurrence, text),
        "provenance_ref": provenance_ref,
        "exact_source_reconstructible": True,
    }


def build_callout_evidence(
    *,
    evidence_id: str,
    occurrence_id: str,
    text_evidence_id: str,
    connector_geometry: dict[str, Any] | None,
    provenance_ref: str,
) -> dict[str, Any]:
    connector = deepcopy(connector_geometry) if connector_geometry is not None else None
    return {
        "evidence_id": str(evidence_id),
        "occurrence_id": str(occurrence_id),
        "text_evidence_id": str(text_evidence_id),
        "connector_geometry": connector,
        "binding_state": "CONNECTOR_PRESENT" if connector is not None else "NO_CONNECTOR",
        "evidence_class": "DIRECT_GRAPHICAL_BINDING" if connector is not None else "PROXIMITY_ONLY",
        "provenance_ref": provenance_ref,
        "exact_source_reconstructible": True,
    }


def build_local_topology_signature(
    *,
    occurrence_id: str,
    neighbors: dict[str, str | None],
    contacts: list[str],
    bay_order: int | None,
    provenance_ref: str,
) -> dict[str, Any]:
    allowed_neighbor_keys = ("left", "right", "up", "down")
    normalized_neighbors = {key: neighbors.get(key) for key in allowed_neighbor_keys}
    return {
        "evidence_id": f"TOPO-{occurrence_id}",
        "occurrence_id": occurrence_id,
        "neighbors": normalized_neighbors,
        "contacts": list(contacts),
        "bay_order": bay_order,
        "evidence_class": "LOCAL_TOPOLOGY_MATCH",
        "provenance_ref": provenance_ref,
        "exact_source_reconstructible": True,
    }
