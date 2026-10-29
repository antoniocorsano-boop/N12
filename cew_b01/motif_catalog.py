from __future__ import annotations

import json
from collections import defaultdict
from typing import Iterable

from .grammar_schema import GraphicPrimitiveObservation, RecurringMotif


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

    ink_ratio = _quantize(signature.get("ink_ratio"), 0.1)
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


def build_recurring_motif_catalog(
    primitives: Iterable[GraphicPrimitiveObservation],
) -> tuple[RecurringMotif, ...]:
    items = tuple(primitives)
    if not all(isinstance(item, GraphicPrimitiveObservation) for item in items):
        raise ValueError("G2_REQUIRES_GRAPHIC_PRIMITIVE_OBSERVATIONS")
    if not items:
        return ()

    groups: dict[tuple[str, int, str], list[GraphicPrimitiveObservation]] = defaultdict(list)
    for item in items:
        groups[_group_key(item)].append(item)

    motifs: list[RecurringMotif] = []
    for key in sorted(groups):
        members = sorted(groups[key], key=lambda item: item.primitive_id)
        source = members[0].source
        if any(member.source != source for member in members):
            raise ValueError("G2_SOURCE_GROUPING_ERROR")
        descriptor = neutral_descriptor_for_primitive(members[0])
        representative = min(
            members,
            key=lambda item: (
                item.y,
                item.x,
                item.width * item.height,
                item.primitive_id,
            ),
        )
        motifs.append(
            RecurringMotif.create(
                source=source,
                member_primitive_ids=tuple(member.primitive_id for member in members),
                representative_primitive_id=representative.primitive_id,
                neutral_descriptor=descriptor,
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
