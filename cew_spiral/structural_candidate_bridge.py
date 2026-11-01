from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from cew_b01.evidence_schema import AxisAlignedEvidenceRegion, EvidenceRegionCandidate
from cew_b01.object_mapping import (
    ReviewDecision,
    ReviewDisposition,
    freeze_pre_comparator_bundle,
    map_reviewed_evidence,
)
from cew_b01.records import CoordinateFrame, SourceIdentity


_POSITIVE_GRAPHICAL_DECISIONS = {
    "COLUMN_FOOTPRINT_CONFIRMED",
    "PILASTRO",
    "PASS",
}

_CLOSED_AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "structural_identity_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _validate_raster_binding(
    *,
    raster_width_px: int,
    raster_height_px: int,
    raster_sha256: str,
    renderer_tool_version: str,
) -> None:
    if isinstance(raster_width_px, bool) or not isinstance(raster_width_px, int) or raster_width_px <= 0:
        raise ValueError("GOVERNED_RASTER_DIMENSIONS_REQUIRED")
    if isinstance(raster_height_px, bool) or not isinstance(raster_height_px, int) or raster_height_px <= 0:
        raise ValueError("GOVERNED_RASTER_DIMENSIONS_REQUIRED")
    if not isinstance(raster_sha256, str) or not _HEX64.fullmatch(raster_sha256):
        raise ValueError("GOVERNED_RASTER_DIGEST_REQUIRED")
    if not isinstance(renderer_tool_version, str) or not renderer_tool_version.strip():
        raise ValueError("GOVERNED_RENDERER_VERSION_REQUIRED")


def _validate_ledger(ledger: dict[str, Any], source: SourceIdentity) -> list[dict[str, Any]]:
    if not isinstance(ledger, dict):
        raise ValueError("COL03A_LEDGER_REQUIRED")
    if ledger.get("schema_id") != "CEW_COL03A_GOVERNED_COLUMN_OCCURRENCE_LEDGER" or ledger.get("schema_version") != 1:
        raise ValueError("COL03A_LEDGER_SCHEMA_INVALID")

    authority = ledger.get("authority")
    if not isinstance(authority, dict) or any(authority.get(key) is not False for key in _CLOSED_AUTHORITY_KEYS):
        raise ValueError("LEDGER_AUTHORITY_DRIFT")

    ledger_source = ledger.get("source")
    if not isinstance(ledger_source, dict):
        raise ValueError("LEDGER_SOURCE_DRIFT")
    if (
        ledger_source.get("source_path") != source.path
        or ledger_source.get("source_sha256") != source.sha256
        or ledger_source.get("page_index") != source.page_index
    ):
        raise ValueError("LEDGER_SOURCE_DRIFT")

    occurrences = ledger.get("occurrences")
    if not isinstance(occurrences, list):
        raise ValueError("COL03A_OCCURRENCES_REQUIRED")
    if ledger.get("occurrence_count") != len(occurrences):
        raise ValueError("COL03A_OCCURRENCE_COUNT_DRIFT")
    conflicts = ledger.get("conflicts")
    if not isinstance(conflicts, list) or ledger.get("conflict_count") != len(conflicts):
        raise ValueError("COL03A_CONFLICT_COUNT_DRIFT")
    if conflicts:
        raise ValueError("COL03A_LEDGER_CONFLICTS_OPEN")
    return occurrences


def _normalized_bbox(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ValueError("OCCURRENCE_NORMALIZED_BBOX_REQUIRED")
    try:
        x = float(value["x"])
        y = float(value["y"])
        width = float(value["width"])
        height = float(value["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("OCCURRENCE_NORMALIZED_BBOX_REQUIRED") from exc
    if x < 0.0 or y < 0.0 or width <= 0.0 or height <= 0.0:
        raise ValueError("OCCURRENCE_NORMALIZED_BBOX_INVALID")
    if x + width > 1.0 + 1e-12 or y + height > 1.0 + 1e-12:
        raise ValueError("OCCURRENCE_NORMALIZED_BBOX_INVALID")
    return {"x": x, "y": y, "width": width, "height": height}


def _validate_occurrence(row: dict[str, Any], source: SourceIdentity) -> tuple[str, dict[str, float], list[str]]:
    if not isinstance(row, dict):
        raise ValueError("OCCURRENCE_OBJECT_REQUIRED")
    occurrence_id = str(row.get("occurrence_id") or "").strip()
    if not occurrence_id.startswith("COL-OCC-"):
        raise ValueError("OCCURRENCE_ID_INVALID")
    if row.get("exact_source_reconstructible") is not True or row.get("lineage_complete") is not True:
        raise ValueError("OCCURRENCE_LINEAGE_INCOMPLETE")
    if str(row.get("conflict_state") or "NONE") != "NONE":
        raise ValueError("OCCURRENCE_CONFLICT_NOT_CLOSED")
    if row.get("source_path") != source.path or row.get("source_sha256") != source.sha256 or row.get("page_index") != source.page_index:
        raise ValueError("OCCURRENCE_SOURCE_DRIFT")
    if row.get("canonical_write_authorized") is not False:
        raise ValueError("OCCURRENCE_AUTHORITY_DRIFT")

    decisions = row.get("graphical_decisions")
    if not isinstance(decisions, list) or not decisions:
        raise ValueError("OCCURRENCE_NOT_HUMAN_POSITIVE")
    normalized_decisions = {str(value) for value in decisions if value is not None}
    if not normalized_decisions or not normalized_decisions.issubset(_POSITIVE_GRAPHICAL_DECISIONS):
        raise ValueError("OCCURRENCE_NOT_HUMAN_POSITIVE")

    receipts = row.get("human_review_receipts")
    if not isinstance(receipts, list) or not receipts or any(not isinstance(value, str) or not value.strip() for value in receipts):
        raise ValueError("OCCURRENCE_HUMAN_REVIEW_PROVENANCE_REQUIRED")
    return occurrence_id, _normalized_bbox(row.get("normalized_bbox")), sorted(set(receipts))


def build_structural_candidate_bridge(
    *,
    ledger: dict[str, Any],
    source: SourceIdentity,
    raster_width_px: int,
    raster_height_px: int,
    raster_sha256: str,
    renderer_tool_version: str,
) -> dict[str, Any]:
    """Normalize governed COL-03A human-positive occurrences into B01 candidates.

    This is not a new human review and does not resolve the historical support
    identifier. Geometry comes only from the governed occurrence bbox transformed
    through explicit governed raster dimensions. Historical comparison is kept
    outside the frozen pre-comparator bundle.
    """

    if not isinstance(source, SourceIdentity):
        raise ValueError("EXACT_SOURCE_IDENTITY_REQUIRED")
    _validate_raster_binding(
        raster_width_px=raster_width_px,
        raster_height_px=raster_height_px,
        raster_sha256=raster_sha256,
        renderer_tool_version=renderer_tool_version,
    )
    occurrences = _validate_ledger(ledger, source)

    evidence_candidates: list[EvidenceRegionCandidate] = []
    decisions: list[ReviewDecision] = []
    bridge_rows: list[dict[str, Any]] = []
    occurrence_ids: set[str] = set()

    for row in sorted(occurrences, key=lambda item: str(item.get("occurrence_id") or "")):
        occurrence_id, bbox, receipts = _validate_occurrence(row, source)
        if occurrence_id in occurrence_ids:
            raise ValueError("OCCURRENCE_ID_DUPLICATE")
        occurrence_ids.add(occurrence_id)

        pixel_geometry = AxisAlignedEvidenceRegion(
            frame=CoordinateFrame.RASTER_PIXEL,
            x=bbox["x"] * raster_width_px,
            y=bbox["y"] * raster_height_px,
            width=bbox["width"] * raster_width_px,
            height=bbox["height"] * raster_height_px,
        )
        evidence = EvidenceRegionCandidate.create(
            source=source,
            geometry=pixel_geometry,
            method="COL03A_GOVERNED_HUMAN_POSITIVE_OCCURRENCE_V1",
            tool_id="cew-spiral-structural-candidate-bridge",
            tool_version="1.0.0",
            confidence=1.0,
        )
        decision = ReviewDecision(
            candidate_id=evidence.candidate_id,
            disposition=ReviewDisposition.ACCEPT,
            semantic_label="COLUMN",
            support_identifier=None,
            section_family=None,
            note=f"NORMALIZED_EXISTING_HUMAN_GRAPHICAL_REVIEW:{occurrence_id}",
        )
        evidence_candidates.append(evidence)
        decisions.append(decision)
        bridge_rows.append(
            {
                "occurrence_id": occurrence_id,
                "source_candidate_id": str(row.get("candidate_id") or ""),
                "source_proposal_ids": sorted(str(value) for value in (row.get("source_proposal_ids") or []) if value),
                "source_evidence_ids": sorted(str(value) for value in (row.get("evidence_ids") or []) if value),
                "human_review_receipts": receipts,
                "graphical_decisions": sorted(str(value) for value in (row.get("graphical_decisions") or []) if value),
                "normalized_bbox": deepcopy(bbox),
                "pixel_geometry": pixel_geometry.to_mapping(),
                "evidence_candidate_id": evidence.candidate_id,
                "evidence_geometry_digest": evidence.geometry_digest,
                "review_normalized_from_existing_human_receipt": True,
                "new_human_review_performed": False,
                "historical_support_identifier_required": False,
                "support_identifier": None,
                "section_family": None,
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
            }
        )

    mapped = map_reviewed_evidence(tuple(evidence_candidates), tuple(decisions))
    pre_comparator = freeze_pre_comparator_bundle(tuple(evidence_candidates), tuple(decisions))
    object_by_evidence = {item.evidence_candidate_id: item for item in mapped}
    for bridge in bridge_rows:
        object_candidate = object_by_evidence.get(bridge["evidence_candidate_id"])
        if object_candidate is None:
            raise ValueError("STRUCTURAL_CANDIDATE_MAPPING_INCOMPLETE")
        bridge["object_candidate_id"] = object_candidate.object_candidate_id

    if len(mapped) != len(bridge_rows) or pre_comparator.get("structural_candidate_count") != len(bridge_rows):
        raise ValueError("STRUCTURAL_CANDIDATE_MAPPING_INCOMPLETE")

    return {
        "schema": "CEW_SPIRAL_STRUCTURAL_CANDIDATE_BRIDGE_v1",
        "source": source.to_mapping(),
        "governed_raster": {
            "frame": CoordinateFrame.RASTER_PIXEL.value,
            "width_px": raster_width_px,
            "height_px": raster_height_px,
            "raster_sha256": raster_sha256,
            "renderer_tool_id": "pypdfium2",
            "renderer_tool_version": renderer_tool_version,
        },
        "occurrence_count": len(bridge_rows),
        "structural_candidate_count": len(mapped),
        "occurrence_bridge": bridge_rows,
        "structural_candidates": [item.to_mapping() for item in mapped],
        "pre_comparator_bundle": pre_comparator,
        "review_semantics": "NORMALIZED_EXISTING_HUMAN_GRAPHICAL_DECISION_NOT_NEW_HUMAN_REVIEW",
        "historical_support_identifier_required": False,
        "historical_comparator_loaded": False,
        "authority": {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "family_assignment_authorized": False,
            "section_assignment_authorized": False,
            "m0g_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }
