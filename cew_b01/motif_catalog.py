from __future__ import annotations

import json
import math
from collections import defaultdict
from typing import Iterable

from .grammar_schema import GraphicPrimitiveObservation, PrimitiveFamily, RecurringMotif


_LINEAR_CONTEXT_FAMILIES = {
    PrimitiveFamily.LINE_SEGMENT,
    PrimitiveFamily.PARALLEL_LINE_PAIR,
}


def _quantize(value: object, step: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if step <= 0:
        return round(float(value), 6)
    return round(round(float(value) / step) * step, 6)


def _aspect_bin(item: GraphicPrimitiveObservation) -> float:
    short = min(item.width, item.height)
    long = max(item.width, item.height)
    if short <= 0:
        return 0.0
    return round(round((long / short) / 0.25) * 0.25, 3)


def neutral_descriptor_for_primitive(item: GraphicPrimitiveObservation) -> dict[str, object]:
    """Build a translation/scale-tolerant, nonsemantic descriptor.

    This is deliberately a bounded adapter over the #137 neutral descriptor
    concept: family identity is retained, absolute page coordinates and lengths
    are excluded, and only coarse shape/feature bins participate in recurrence
    grouping. No similarity score or structural label is produced here.
    """

    if not isinstance(item, GraphicPrimitiveObservation):
        raise ValueError("G2_REQUIRES_GRAPHIC_PRIMITIVE_OBSERVATION")

    signature = dict(item.feature_signature)
    descriptor: dict[str, object] = {
        "family": item.family.value,
        "aspect_bin": _aspect_bin(item),
    }

    orientation = signature.get("orientation")
    if isinstance(orientation, str) and orientation:
        descriptor["orientation"] = orientation

    relation = signature.get("relation")
    if isinstance(relation, str) and relation:
        descriptor["relation"] = relation

    vertex_count = signature.get("vertex_count")
    if isinstance(vertex_count, int) and not isinstance(vertex_count, bool):
        descriptor["vertex_count"] = vertex_count

    rectangularity = _quantize(signature.get("rectangularity"), 0.1)
    if rectangularity is not None:
        descriptor["rectangularity_bin"] = rectangularity

    # Raster ink density is noisy under uniform scale and anti-aliasing. Use a
    # deliberately coarser neutral bin than rectangularity so near-identical
    # UNKNOWN/complex motifs are not split by a one-percent density change.
    ink_ratio = _quantize(signature.get("ink_ratio"), 0.2)
    if ink_ratio is not None:
        descriptor["ink_ratio_bin"] = ink_ratio

    near_h = signature.get("near_horizontal_endpoint")
    near_v = signature.get("near_vertical_endpoint")
    if isinstance(near_h, bool):
        descriptor["near_horizontal_endpoint"] = near_h
    if isinstance(near_v, bool):
        descriptor["near_vertical_endpoint"] = near_v

    # Deliberately exclude absolute component area/length. Recurrence discovery
    # must stay invariant to translation and uniform scale; density/aspect bins
    # already preserve useful neutral shape information for UNKNOWN groups.
    return descriptor


def _group_key(item: GraphicPrimitiveObservation) -> tuple[str, int, str]:
    descriptor = neutral_descriptor_for_primitive(item)
    descriptor_json = json.dumps(descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return (item.source.sha256, item.page_index, descriptor_json)


def _spatial_key(item: GraphicPrimitiveObservation) -> tuple[float, float, float, str]:
    return (item.y, item.x, item.width * item.height, item.primitive_id)


def _representative_members(
    members: list[GraphicPrimitiveObservation],
    *,
    limit: int = 4,
) -> tuple[GraphicPrimitiveObservation, ...]:
    ordered = sorted(members, key=_spatial_key)
    if len(ordered) <= limit:
        return tuple(ordered)
    indices = sorted({round(index * (len(ordered) - 1) / (limit - 1)) for index in range(limit)})
    return tuple(ordered[index] for index in indices)


def _source_locator(item: GraphicPrimitiveObservation) -> dict[str, object]:
    return {
        "primitive_id": item.primitive_id,
        "frame": item.frame.value,
        "geometry": {
            "x": item.x,
            "y": item.y,
            "width": item.width,
            "height": item.height,
        },
    }


def _bbox_gap(a: GraphicPrimitiveObservation, b: GraphicPrimitiveObservation) -> float:
    ax1 = a.x + a.width
    ay1 = a.y + a.height
    bx1 = b.x + b.width
    by1 = b.y + b.height
    dx = max(b.x - ax1, a.x - bx1, 0.0)
    dy = max(b.y - ay1, a.y - by1, 0.0)
    return math.hypot(dx, dy)


def _context_radius(item: GraphicPrimitiveObservation) -> float:
    scale = math.sqrt(max(1.0, item.width * item.height))
    return max(12.0, min(180.0, 3.0 * scale))


def _context_descriptor_for_members(
    members: list[GraphicPrimitiveObservation],
    scope_items: tuple[GraphicPrimitiveObservation, ...],
) -> dict[str, object]:
    linear_present = 0
    linear_touching = 0
    text_present = 0

    for member in members:
        radius = _context_radius(member)
        nearby_linear = False
        touching_linear = False
        nearby_text = False
        for other in scope_items:
            if other.primitive_id == member.primitive_id:
                continue
            gap = _bbox_gap(member, other)
            if other.family in _LINEAR_CONTEXT_FAMILIES and gap <= radius:
                nearby_linear = True
                if gap <= 2.0:
                    touching_linear = True
            if other.family == PrimitiveFamily.TEXT_BLOCK and gap <= radius:
                nearby_text = True
        linear_present += int(nearby_linear)
        linear_touching += int(touching_linear)
        text_present += int(nearby_text)

    count = len(members)
    return {
        "nearby_linear": {
            "present_for_any_member": linear_present > 0,
            "member_fraction": round(linear_present / count, 3),
            "touching_for_any_member": linear_touching > 0,
            "touching_member_fraction": round(linear_touching / count, 3),
        },
        "associated_text": {
            "present_for_any_member": text_present > 0,
            "member_fraction": round(text_present / count, 3),
        },
    }


def build_recurring_motif_catalog(
    primitives: Iterable[GraphicPrimitiveObservation],
) -> tuple[RecurringMotif, ...]:
    items = tuple(primitives)
    if not all(isinstance(item, GraphicPrimitiveObservation) for item in items):
        raise ValueError("G2_REQUIRES_GRAPHIC_PRIMITIVE_OBSERVATIONS")
    if not items:
        return ()

    groups: dict[tuple[str, int, str], list[GraphicPrimitiveObservation]] = defaultdict(list)
    scope_items: dict[tuple[str, int], list[GraphicPrimitiveObservation]] = defaultdict(list)
    for item in items:
        groups[_group_key(item)].append(item)
        scope_items[(item.source.sha256, item.page_index)].append(item)

    canonical_scopes = {
        key: tuple(sorted(value, key=lambda item: item.primitive_id))
        for key, value in scope_items.items()
    }

    motifs: list[RecurringMotif] = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda item: item.primitive_id)
        source = members[0].source
        if any(member.source != source for member in members):
            raise ValueError("G2_SOURCE_GROUPING_ERROR")
        descriptor = neutral_descriptor_for_primitive(members[0])
        representatives = _representative_members(members)
        representative = representatives[0]
        context_descriptor = _context_descriptor_for_members(
            members,
            canonical_scopes[(source.sha256, source.page_index)],
        )
        motifs.append(
            RecurringMotif.create(
                source=source,
                member_primitive_ids=tuple(member.primitive_id for member in members),
                representative_primitive_id=representative.primitive_id,
                representative_primitive_ids=tuple(item.primitive_id for item in representatives),
                neutral_descriptor=descriptor,
                context_descriptor=context_descriptor,
                source_locators=tuple(_source_locator(item) for item in representatives),
            )
        )

    return tuple(
        sorted(
            motifs,
            key=lambda item: (
                item.source.sha256,
                item.page_index,
                json.dumps(dict(item.neutral_descriptor), sort_keys=True, separators=(",", ":")),
                item.motif_id,
            ),
        )
    )
