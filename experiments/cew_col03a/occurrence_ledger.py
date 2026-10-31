from __future__ import annotations

from copy import deepcopy
from typing import Any


EXPECTED_PROPOSAL_COUNT = 611
EXPECTED_SOURCE_VERSION_ID = "CEW-N12-SRC-TAV05S-V2143DBCF"
EXPECTED_SOURCE_PATH = "archive/documentazione_originaria/tavola 5.pdf"
EXPECTED_SOURCE_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
EXPECTED_PAGE_ID = "CEW-N12-PAGE-TAV05S-P001"
EXPECTED_PAGE_INDEX = 0
EXPECTED_PAGE_TRANSFORM_ID = "CEW-N12-XFORM-TAV05S-P001"

_POSITIVE_GRAPHICAL_DECISIONS = {
    "COLUMN_FOOTPRINT_CONFIRMED",
    "PILASTRO",
    "PASS",
}
_NEGATIVE_GRAPHICAL_DECISIONS = {
    "NOT_COLUMN",
    "NON_PILASTRO",
    "MISLOCALIZED_NOT_COLUMN",
}
_SOURCE_KEYS = (
    "source_version_id",
    "source_path",
    "source_sha256",
    "page_id",
    "page_index",
    "page_transform_id",
)


def _normalized_bbox(value: Any, label: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    try:
        x = float(value["x"])
        y = float(value["y"])
        width = float(value["width"])
        height = float(value["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain numeric x/y/width/height") from exc
    if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and width > 0.0 and height > 0.0):
        raise ValueError(f"{label} is not a valid normalized bbox")
    if x + width > 1.0 + 1e-12 or y + height > 1.0 + 1e-12:
        raise ValueError(f"{label} exceeds source bounds")
    return {"x": x, "y": y, "width": width, "height": height}


def build_proposal_geometry_index(proposals_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if proposals_payload.get("candidate_count") != EXPECTED_PROPOSAL_COUNT:
        raise ValueError("frozen proposal count drift")
    candidates = proposals_payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != EXPECTED_PROPOSAL_COUNT:
        raise ValueError("frozen proposal payload must contain exactly 611 candidates")

    result: dict[str, dict[str, Any]] = {}
    for row in candidates:
        if not isinstance(row, dict):
            raise ValueError("every frozen proposal must be an object")
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id or candidate_id in result:
            raise ValueError("frozen proposal candidate IDs must be non-empty and unique")
        normalized = deepcopy(row)
        normalized["bbox"] = _normalized_bbox(row.get("bbox"), f"proposal {candidate_id} bbox")
        result[candidate_id] = normalized
    return result


def _validate_source(source: dict[str, Any]) -> None:
    expected = {
        "source_version_id": EXPECTED_SOURCE_VERSION_ID,
        "source_path": EXPECTED_SOURCE_PATH,
        "sha256": EXPECTED_SOURCE_SHA256,
        "page_id": EXPECTED_PAGE_ID,
        "page_index": EXPECTED_PAGE_INDEX,
        "page_transform_id": EXPECTED_PAGE_TRANSFORM_ID,
    }
    for key, value in expected.items():
        if source.get(key) != value:
            raise ValueError(f"exact-source lineage drift: {key}")


def _repair_index(repair_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    repairs = repair_manifest.get("repairs")
    if not isinstance(repairs, list):
        raise ValueError("repair manifest repairs missing")
    result: dict[str, dict[str, Any]] = {}
    for row in repairs:
        if not isinstance(row, dict):
            raise ValueError("repair rows must be objects")
        repair_id = str(row.get("repair_id") or "")
        if not repair_id or repair_id in result:
            raise ValueError("repair IDs must be non-empty and unique")
        result[repair_id] = row
    return result


def attach_exact_source_geometry(
    *,
    evidence_items: list[dict[str, Any]],
    proposal_index: dict[str, dict[str, Any]],
    repair_manifest: dict[str, Any],
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    _validate_source(source)
    repairs = _repair_index(repair_manifest)
    attached: list[dict[str, Any]] = []

    for evidence in evidence_items:
        candidate_id = str(evidence.get("candidate_id") or "")
        evidence_id = str(evidence.get("evidence_id") or "")
        if not candidate_id or not evidence_id:
            raise ValueError("governed evidence lacks candidate/evidence identity")
        proposal = proposal_index.get(candidate_id)
        if proposal is None:
            raise ValueError(f"governed positive missing from frozen proposal index: {candidate_id}")

        anchor_bbox = _normalized_bbox(proposal.get("bbox"), f"proposal {candidate_id} bbox")
        repair_id_value = evidence.get("repair_id")
        repair_id = str(repair_id_value) if repair_id_value else None
        if repair_id is None:
            primary = {
                "kind": "FROZEN_PROPOSAL",
                "candidate_id": candidate_id,
                "repair_id": None,
                "bbox": dict(anchor_bbox),
            }
        else:
            repair = repairs.get(repair_id)
            if repair is None:
                raise ValueError(f"governed repair missing from repair manifest: {repair_id}")
            if repair.get("source_candidate_id") != candidate_id:
                raise ValueError(f"repair source lineage mismatch: {repair_id}")
            if repair.get("status") != "READY_FOR_HUMAN_GRAPHICAL_REVIEW":
                raise ValueError(f"repair is not in governed review-ready state: {repair_id}")
            repaired_bbox = _normalized_bbox(
                repair.get("reconstructed_bbox"),
                f"repair {repair_id} reconstructed_bbox",
            )
            primary = {
                "kind": "GOVERNED_WHOLE_SYMBOL_REPAIR",
                "candidate_id": candidate_id,
                "repair_id": repair_id,
                "bbox": repaired_bbox,
            }

        record = deepcopy(evidence)
        record.update(
            {
                "candidate_id": candidate_id,
                "anchor_bbox": dict(anchor_bbox),
                "normalized_bbox": dict(primary["bbox"]),
                "primary_graphical_representation": primary,
                "source_geometry_ref": candidate_id,
                "source_version_id": source["source_version_id"],
                "source_path": source["source_path"],
                "source_sha256": source["sha256"],
                "page_id": source["page_id"],
                "page_index": source["page_index"],
                "page_transform_id": source["page_transform_id"],
                "exact_source_reconstructible": True,
                "lineage_complete": True,
            }
        )
        attached.append(record)

    return attached


def _stable_unique_strings(values: list[Any]) -> list[str]:
    return sorted({str(value) for value in values if value is not None and str(value)})


def _primary_representation_for_group(records: list[dict[str, Any]]) -> dict[str, Any]:
    repaired = [
        row["primary_graphical_representation"]
        for row in records
        if isinstance(row.get("primary_graphical_representation"), dict)
        and row["primary_graphical_representation"].get("kind") == "GOVERNED_WHOLE_SYMBOL_REPAIR"
    ]
    if repaired:
        canonical = sorted(
            repaired,
            key=lambda item: (
                str(item.get("repair_id") or ""),
                str(item.get("candidate_id") or ""),
            ),
        )
        first = canonical[0]
        if any(item != first for item in canonical[1:]):
            raise ValueError("multiple incompatible governed repair representations in one lineage group")
        return deepcopy(first)

    proposals = [
        row["primary_graphical_representation"]
        for row in records
        if isinstance(row.get("primary_graphical_representation"), dict)
    ]
    if not proposals:
        raise ValueError("lineage group lacks a primary graphical representation")
    first = proposals[0]
    if any(item != first for item in proposals[1:]):
        raise ValueError("inconsistent frozen proposal representations in one lineage group")
    return deepcopy(first)


def collapse_strong_lineage(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse only records sharing the same immutable frozen proposal lineage."""
    if not isinstance(records, list):
        raise ValueError("records must be a list")

    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("every occurrence record must be an object")
        candidate_id = str(row.get("candidate_id") or "")
        evidence_id = str(row.get("evidence_id") or "")
        if not candidate_id or not evidence_id:
            raise ValueError("occurrence record lacks candidate/evidence identity")
        by_candidate.setdefault(candidate_id, []).append(row)

    groups: list[dict[str, Any]] = []
    for candidate_id in sorted(by_candidate):
        members = sorted(by_candidate[candidate_id], key=lambda row: str(row["evidence_id"]))
        first = members[0]
        anchor = _normalized_bbox(first.get("anchor_bbox"), f"{candidate_id} anchor_bbox")
        for row in members[1:]:
            if _normalized_bbox(row.get("anchor_bbox"), f"{candidate_id} anchor_bbox") != anchor:
                raise ValueError(f"anchor geometry drift inside strong lineage group: {candidate_id}")
            for key in _SOURCE_KEYS:
                if row.get(key) != first.get(key):
                    raise ValueError(f"source lineage drift inside strong lineage group: {candidate_id}:{key}")

        decisions = _stable_unique_strings([row.get("graphical_decision") for row in members])
        has_positive = any(value in _POSITIVE_GRAPHICAL_DECISIONS for value in decisions)
        has_negative = any(value in _NEGATIVE_GRAPHICAL_DECISIONS for value in decisions)
        conflict_state = "CONTRADICTORY_GRAPHICAL_DECISIONS" if has_positive and has_negative else "NONE"
        primary = _primary_representation_for_group(members)

        human_events: list[Any] = []
        for row in members:
            events = row.get("human_added_point_event_ids")
            if isinstance(events, list):
                human_events.extend(events)

        repair_lineage = _stable_unique_strings([row.get("repair_id") for row in members])
        group = {
            "candidate_id": candidate_id,
            "source_proposal_ids": [candidate_id],
            "evidence_ids": _stable_unique_strings([row.get("evidence_id") for row in members]),
            "evidence_classes": _stable_unique_strings([row.get("evidence_class") for row in members]),
            "graphical_decisions": decisions,
            "discovery_paths": _stable_unique_strings([row.get("discovery_path") for row in members]),
            "human_review_receipts": _stable_unique_strings([row.get("human_review_receipt") for row in members]),
            "repair_lineage": repair_lineage,
            "human_added_point_event_ids": _stable_unique_strings(human_events),
            "lineage": [deepcopy(row.get("lineage")) for row in members],
            "anchor_bbox": dict(anchor),
            "normalized_bbox": dict(primary["bbox"]),
            "primary_graphical_representation": primary,
            "source_geometry_ref": candidate_id,
            "exact_source_reconstructible": all(row.get("exact_source_reconstructible") is True for row in members),
            "lineage_complete": all(row.get("lineage_complete") is True for row in members),
            "dedup_state": "STRONG_LINEAGE_COLLAPSED" if len(members) > 1 else "SINGLE_GOVERNED_LINEAGE",
            "conflict_state": conflict_state,
        }
        for key in _SOURCE_KEYS:
            group[key] = deepcopy(first.get(key))
        groups.append(group)

    return groups


def smaller_bbox_overlap(a: dict[str, float], b: dict[str, float]) -> float:
    """Return intersection area divided by the smaller bbox area."""
    box_a = _normalized_bbox(a, "bbox a")
    box_b = _normalized_bbox(b, "bbox b")
    left = max(box_a["x"], box_b["x"])
    top = max(box_a["y"], box_b["y"])
    right = min(box_a["x"] + box_a["width"], box_b["x"] + box_b["width"])
    bottom = min(box_a["y"] + box_a["height"], box_b["y"] + box_b["height"])
    if right <= left or bottom <= top:
        return 0.0
    intersection = (right - left) * (bottom - top)
    smaller_area = min(
        box_a["width"] * box_a["height"],
        box_b["width"] * box_b["height"],
    )
    return intersection / smaller_area


def detect_ambiguous_duplicates(
    groups: list[dict[str, Any]],
    *,
    overlap_threshold: float = 0.90,
) -> list[dict[str, Any]]:
    """Flag geometry-only ambiguity across distinct strong-lineage groups; never merge it."""
    if not (0.0 < overlap_threshold <= 1.0):
        raise ValueError("overlap_threshold must be in (0, 1]")
    ordered = sorted(groups, key=lambda row: str(row.get("candidate_id") or ""))
    conflicts: list[dict[str, Any]] = []
    for index, left_group in enumerate(ordered):
        left_id = str(left_group.get("candidate_id") or "")
        if not left_id:
            raise ValueError("lineage group lacks candidate_id")
        left_rep = left_group.get("primary_graphical_representation")
        if not isinstance(left_rep, dict):
            raise ValueError(f"lineage group lacks primary representation: {left_id}")
        for right_group in ordered[index + 1 :]:
            right_id = str(right_group.get("candidate_id") or "")
            if not right_id or right_id == left_id:
                raise ValueError("ambiguous-duplicate detection requires distinct candidate groups")
            right_rep = right_group.get("primary_graphical_representation")
            if not isinstance(right_rep, dict):
                raise ValueError(f"lineage group lacks primary representation: {right_id}")
            overlap = smaller_bbox_overlap(left_rep.get("bbox"), right_rep.get("bbox"))
            if overlap + 1e-12 >= overlap_threshold:
                conflicts.append(
                    {
                        "conflict_state": "AMBIGUOUS_DUPLICATE",
                        "candidate_ids": [left_id, right_id],
                        "overlap_of_smaller_bbox": overlap,
                        "resolution": "HUMAN_REVIEW_REQUIRED",
                    }
                )
    return conflicts
