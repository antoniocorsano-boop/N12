from __future__ import annotations

from typing import Any

LINEISH = {"LINE_SEGMENT", "PARALLEL_LINE_PAIR"}
CLOSED_OR_COMPLEX = {"RECTILINEAR_CLOSED_SHAPE", "COMPLEX_GRAPHIC_GROUP"}
CONTACT_RELATIONS = {"OVERLAPS", "TOUCHING", "CONTAINS", "CONTAINED_BY"}


def _major_span(bundle: dict[str, Any]) -> float:
    geometry = bundle["geometry"]
    return max(float(geometry["width"]), float(geometry["height"]))


def _area(bundle: dict[str, Any]) -> float:
    geometry = bundle["geometry"]
    return float(geometry["width"]) * float(geometry["height"])


def _seed_relation_map(candidate: dict[str, Any]) -> dict[str, set[str]]:
    seed_bundle_id = candidate["seed_bundle_id"]
    result: dict[str, set[str]] = {}
    for edge in candidate.get("relations", []):
        first = edge.get("a")
        second = edge.get("b")
        if first == seed_bundle_id and isinstance(second, str):
            result.setdefault(second, set()).update(edge.get("relations", []))
        elif second == seed_bundle_id and isinstance(first, str):
            result.setdefault(first, set()).update(edge.get("relations", []))
    return result


def _expanded_ids(bundles: list[dict[str, Any]]) -> list[str]:
    return sorted({
        primitive_id
        for bundle in bundles
        for primitive_id in bundle.get("member_primitive_ids", [])
    })


def refine_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Refine one G2A0 candidate into a neutral G2B CORE/CONTEXT boundary.

    The function is deliberately non-semantic. It can only retain an incoming
    G2A0 CORE bundle or move it to CONTEXT; it never invents or drops evidence.
    """

    seed_bundle_id = candidate["seed_bundle_id"]
    core_by_id = {
        bundle["bundle_id"]: bundle
        for bundle in candidate.get("core_bundles", [])
    }
    if seed_bundle_id not in core_by_id:
        raise ValueError("G2B_SEED_BUNDLE_NOT_IN_CORE")

    seed = core_by_id[seed_bundle_id]
    seed_major = max(1.0, _major_span(seed))
    seed_area = max(1.0, _area(seed))
    relation_map = _seed_relation_map(candidate)

    retained_ids: list[str] = [seed_bundle_id]
    moved_ids: list[str] = []
    decisions: dict[str, dict[str, Any]] = {
        seed_bundle_id: {
            "classification": "CORE",
            "reason": "SEED_ANCHOR",
        }
    }

    for bundle_id in sorted(core_by_id):
        if bundle_id == seed_bundle_id:
            continue

        bundle = core_by_id[bundle_id]
        families = set(bundle.get("families", []))
        relations = relation_map.get(bundle_id, set())
        has_contact = bool(relations & CONTACT_RELATIONS)
        major_ratio = _major_span(bundle) / seed_major
        area_ratio = _area(bundle) / seed_area

        classification = "CORE"
        reason = "RETAIN_COMPACT_CONTACT" if has_contact else "RETAIN_OTHER_G2A0_CORE"

        if "NEAR" in relations and not has_contact:
            classification = "CONTEXT"
            reason = "NEAR_ONLY"
        elif families and families.issubset(LINEISH) and major_ratio > 2.0:
            classification = "CONTEXT"
            reason = "DOMINANT_LINEAR_CONTEXT"
        elif families & CLOSED_OR_COMPLEX and (area_ratio > 1.8 or major_ratio > 1.6):
            classification = "CONTEXT"
            reason = "DOMINANT_CLOSED_OR_COMPLEX_CONTEXT"

        decisions[bundle_id] = {
            "classification": classification,
            "reason": reason,
            "seed_relations": sorted(relations),
            "major_span_ratio_to_seed": round(major_ratio, 6),
            "area_ratio_to_seed": round(area_ratio, 6),
        }

        if classification == "CORE":
            retained_ids.append(bundle_id)
        else:
            moved_ids.append(bundle_id)

    retained_ids = [seed_bundle_id] + sorted(
        bundle_id for bundle_id in retained_ids if bundle_id != seed_bundle_id
    )
    moved_ids = sorted(set(moved_ids))

    existing_context_ids = set(candidate.get("context_bundle_ids", []))
    context_ids = sorted(existing_context_ids | set(moved_ids))

    retained_bundles = [core_by_id[bundle_id] for bundle_id in retained_ids]
    moved_bundles = [core_by_id[bundle_id] for bundle_id in moved_ids]

    incoming_context_primitives = set(candidate.get("context_primitive_ids_expanded", []))
    moved_primitives = set(_expanded_ids(moved_bundles))

    incoming_bundle_ids = set(candidate.get("core_bundle_ids", [])) | existing_context_ids
    outgoing_bundle_ids = set(retained_ids) | set(context_ids)
    if incoming_bundle_ids != outgoing_bundle_ids:
        raise ValueError("G2B_BUNDLE_MEMBERSHIP_NOT_CONSERVED")

    incoming_primitive_ids = (
        set(candidate.get("core_primitive_ids_expanded", []))
        | incoming_context_primitives
    )
    outgoing_core_primitives = set(_expanded_ids(retained_bundles))
    outgoing_context_primitives = incoming_context_primitives | moved_primitives
    if incoming_primitive_ids != outgoing_core_primitives | outgoing_context_primitives:
        raise ValueError("G2B_PRIMITIVE_PROVENANCE_NOT_CONSERVED")

    return {
        "candidate_id": candidate.get("candidate_id"),
        "seed_primitive_id": candidate.get("seed_primitive_id"),
        "seed_bundle_id": seed_bundle_id,
        "incoming_core_bundle_ids": sorted(set(candidate.get("core_bundle_ids", []))),
        "incoming_context_bundle_ids": sorted(existing_context_ids),
        "g2b_core_bundle_ids": retained_ids,
        "g2b_context_bundle_ids": context_ids,
        "g2b_core_primitive_ids_expanded": sorted(outgoing_core_primitives),
        "g2b_context_primitive_ids_expanded": sorted(outgoing_context_primitives),
        "g2b_core_bundles": retained_bundles,
        "g2b_moved_from_core_bundles": moved_bundles,
        "boundary_decisions": decisions,
        "review_state": "UNREVIEWED",
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }
