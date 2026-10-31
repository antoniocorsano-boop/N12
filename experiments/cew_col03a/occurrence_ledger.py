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
