from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any, Iterable

from experiments.cew_cal01.anchor_inventory import AUTHORITY_CLOSED


ALLOWED_EVIDENCE_KIND = "PRIMARY_SOURCE_HOMOLOGY"
CLASSIFICATIONS = ("AMBIGUOUS", "HOMOLOGY_PROPOSAL", "UNMATCHED")


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _require_closed_authority(payload: dict[str, Any], error_code: str) -> None:
    authority = dict(payload.get("authority") or {})
    if not authority:
        raise ValueError(error_code)
    for key, value in authority.items():
        if key.endswith("_authorized") and value is not False:
            raise ValueError(error_code)
    if authority.get("engineering_authority_effect", "NONE") != "NONE":
        raise ValueError(error_code)


def _validated_bridge(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if payload.get("schema") != "CEW_SPIRAL_EXACT_SOURCE_STRUCTURAL_CANDIDATE_BRIDGE_v1":
        raise ValueError("CAL01_INTERSOURCE_BRIDGE_SCHEMA_INVALID")
    bridge = dict(payload.get("bridge") or {})
    source = dict(bridge.get("source") or {})
    raster = dict(bridge.get("governed_raster") or {})
    if not source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_TAV5_SOURCE_INVALID")
    if raster.get("frame") != "RASTER_PIXEL" or not raster.get("raster_sha256"):
        raise ValueError("CAL01_INTERSOURCE_TAV5_RASTER_INVALID")
    width = float(raster.get("width_px", 0))
    height = float(raster.get("height_px", 0))
    if width <= 0 or height <= 0:
        raise ValueError("CAL01_INTERSOURCE_TAV5_RASTER_INVALID")
    if bridge.get("historical_comparator_loaded") is not False:
        raise ValueError("CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN")
    if bridge.get("historical_support_identifier_required") is not False:
        raise ValueError("CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN")
    _require_closed_authority(bridge, "CAL01_INTERSOURCE_AUTHORITY_ESCALATION")

    rows = [dict(row) for row in bridge.get("occurrence_bridge", [])]
    if int(bridge.get("occurrence_count", len(rows))) != len(rows):
        raise ValueError("CAL01_INTERSOURCE_OCCURRENCE_COUNT_DRIFT")
    if int(bridge.get("structural_candidate_count", len(rows))) != len(rows):
        raise ValueError("CAL01_INTERSOURCE_OCCURRENCE_COUNT_DRIFT")
    return bridge, rows


def _validated_lattice(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    if payload.get("schema") != "CEW_CAL01_TAV02_REFERENCE_LATTICE_v1":
        raise ValueError("CAL01_INTERSOURCE_LATTICE_SCHEMA_INVALID")
    source = dict(payload.get("source") or {})
    if source.get("source_id") != "TAV-02S" or not source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_TAV02_SOURCE_INVALID")
    if payload.get("coordinate_frame") != "LOCAL_RELATIVE_METRIC":
        raise ValueError("CAL01_INTERSOURCE_LATTICE_FRAME_INVALID")
    if payload.get("absolute_origin_authorized") is not False:
        raise ValueError("CAL01_INTERSOURCE_AUTHORITY_ESCALATION")
    if payload.get("eligible_for_metric_calibration") is not False:
        raise ValueError("CAL01_INTERSOURCE_AUTHORITY_ESCALATION")
    _require_closed_authority(payload, "CAL01_INTERSOURCE_AUTHORITY_ESCALATION")

    nodes = [dict(row) for row in payload.get("lattice_nodes", [])]
    if int(payload.get("lattice_node_count", len(nodes))) != len(nodes):
        raise ValueError("CAL01_INTERSOURCE_LATTICE_COUNT_DRIFT")
    by_id: dict[str, dict[str, Any]] = {}
    for row in nodes:
        node_id = str(row.get("lattice_node_id") or "")
        if not node_id or node_id in by_id:
            raise ValueError("CAL01_INTERSOURCE_LATTICE_NODE_INVALID")
        source_point = row.get("source_point_normalized_px")
        metric_point = row.get("local_metric_xy_m")
        if not isinstance(source_point, list) or len(source_point) != 2:
            raise ValueError("CAL01_INTERSOURCE_LATTICE_NODE_INVALID")
        if not isinstance(metric_point, list) or len(metric_point) != 2:
            raise ValueError("CAL01_INTERSOURCE_LATTICE_NODE_INVALID")
        if row.get("fit_eligible") is not False or row.get("primary_anchor_authorized") is not False:
            raise ValueError("CAL01_INTERSOURCE_AUTHORITY_ESCALATION")
        by_id[node_id] = row
    return source, by_id


def _occurrence_candidate(row: dict[str, Any], raster: dict[str, Any]) -> dict[str, Any]:
    occurrence_id = str(row.get("occurrence_id") or "")
    if not occurrence_id:
        raise ValueError("CAL01_INTERSOURCE_OCCURRENCE_INVALID")
    geometry = dict(row.get("pixel_geometry") or {})
    if geometry.get("frame") != raster.get("frame"):
        raise ValueError("CAL01_INTERSOURCE_TAV5_FRAME_DRIFT")
    x = float(geometry.get("x", -1.0))
    y = float(geometry.get("y", -1.0))
    width = float(geometry.get("width", 0.0))
    height = float(geometry.get("height", 0.0))
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ValueError("CAL01_INTERSOURCE_TAV5_GEOMETRY_INVALID")
    center = [x + width / 2.0, y + height / 2.0]
    if center[0] > float(raster["width_px"]) or center[1] > float(raster["height_px"]):
        raise ValueError("CAL01_INTERSOURCE_TAV5_GEOMETRY_INVALID")

    evidence_refs = sorted(
        set(str(value) for value in row.get("source_evidence_ids", []) if str(value))
        | set(str(value) for value in row.get("human_review_receipts", []) if str(value))
    )
    if not evidence_refs:
        raise ValueError("CAL01_INTERSOURCE_TAV5_EVIDENCE_MISSING")
    if row.get("structural_identity_authorized") is not False:
        raise ValueError("CAL01_INTERSOURCE_AUTHORITY_ESCALATION")
    if row.get("canonical_write_authorized") is not False:
        raise ValueError("CAL01_INTERSOURCE_AUTHORITY_ESCALATION")

    return {
        "occurrence_id": occurrence_id,
        "object_candidate_id": str(row.get("object_candidate_id") or ""),
        "source_candidate_id": str(row.get("source_candidate_id") or ""),
        "source_point_px": [float(center[0]), float(center[1])],
        "source_frame": str(raster["frame"]),
        "source_evidence_refs": evidence_refs,
        "classification": "UNMATCHED",
        "target_lattice_node_ids": [],
        "proposal_evidence_refs": [],
        "governed_correspondence": False,
        "fit_eligible": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
    }


def discover_correspondence_candidates(
    structural_candidate_bridge: dict[str, Any],
    reference_lattice: dict[str, Any],
    proposal_bindings: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    bridge, occurrence_rows = _validated_bridge(structural_candidate_bridge)
    tav02_source, lattice_by_id = _validated_lattice(reference_lattice)
    tav5_source = dict(bridge["source"])
    tav5_raster = dict(bridge["governed_raster"])

    candidate_by_id: dict[str, dict[str, Any]] = {}
    for row in occurrence_rows:
        candidate = _occurrence_candidate(row, tav5_raster)
        occurrence_id = candidate["occurrence_id"]
        if occurrence_id in candidate_by_id:
            raise ValueError("CAL01_INTERSOURCE_OCCURRENCE_DUPLICATE")
        candidate_by_id[occurrence_id] = candidate

    bindings_by_occurrence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw in proposal_bindings or []:
        binding = dict(raw)
        occurrence_id = str(binding.get("occurrence_id") or "")
        node_id = str(binding.get("lattice_node_id") or "")
        if occurrence_id not in candidate_by_id:
            raise ValueError("CAL01_INTERSOURCE_OCCURRENCE_UNKNOWN")
        if node_id not in lattice_by_id:
            raise ValueError("CAL01_INTERSOURCE_LATTICE_NODE_UNKNOWN")
        if binding.get("evidence_kind") != ALLOWED_EVIDENCE_KIND:
            raise ValueError("CAL01_INTERSOURCE_EVIDENCE_KIND_INVALID")
        refs = sorted(set(str(value) for value in binding.get("evidence_refs", []) if str(value)))
        if not refs:
            raise ValueError("CAL01_INTERSOURCE_EVIDENCE_REFERENCE_MISSING")
        bindings_by_occurrence[occurrence_id].append(
            {
                "lattice_node_id": node_id,
                "evidence_refs": refs,
            }
        )

    for occurrence_id, rows in bindings_by_occurrence.items():
        candidate = candidate_by_id[occurrence_id]
        target_ids = sorted({row["lattice_node_id"] for row in rows})
        evidence_refs = sorted({ref for row in rows for ref in row["evidence_refs"]})
        candidate["target_lattice_node_ids"] = target_ids
        candidate["proposal_evidence_refs"] = evidence_refs
        candidate["classification"] = "HOMOLOGY_PROPOSAL" if len(target_ids) == 1 else "AMBIGUOUS"

    candidates = sorted(candidate_by_id.values(), key=lambda row: row["occurrence_id"])
    classification_counts = Counter(row["classification"] for row in candidates)
    counts = {name: int(classification_counts.get(name, 0)) for name in CLASSIFICATIONS}

    target_lattice_nodes = [
        {
            "lattice_node_id": node_id,
            "source_point_normalized_px": [float(v) for v in row["source_point_normalized_px"]],
            "local_metric_xy_m": [float(v) for v in row["local_metric_xy_m"]],
            "fit_eligible": False,
            "primary_anchor_authorized": False,
        }
        for node_id, row in sorted(lattice_by_id.items())
    ]

    output: dict[str, Any] = {
        "schema": "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_CANDIDATES_v1",
        "program": "CEW-CAL-01",
        "tav5_source": tav5_source,
        "tav5_raster": tav5_raster,
        "tav02_source": tav02_source,
        "tav02_lattice_digest": reference_lattice.get("lattice_digest"),
        "tav02_coordinate_frame": "LOCAL_RELATIVE_METRIC",
        "source_candidate_count": len(candidates),
        "target_lattice_node_count": len(target_lattice_nodes),
        "classification_counts": counts,
        "governed_correspondence_count": 0,
        "candidates": candidates,
        "target_lattice_nodes": target_lattice_nodes,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "eligible_for_registration_fit": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    output["candidate_digest"] = _canonical_digest(output)
    return output
