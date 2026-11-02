from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from experiments.cew_cal01.anchor_inventory import AUTHORITY_CLOSED


HUMAN_DECISION_SCHEMA = "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_DECISION_v1"
SOURCE_NATIVE_SCHEMA = "CEW_CAL01_INTERSOURCE_SOURCE_NATIVE_EQUIVALENCE_v1"
CANDIDATE_SCHEMA = "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_CANDIDATES_v1"
GOVERNED_SCHEMA = "CEW_CAL01_INTERSOURCE_GOVERNED_CORRESPONDENCES_v1"
REVIEW_PACKET_SCHEMA = "CEW_CAL01_INTERSOURCE_HUMAN_REVIEW_PACKET_v1"

_ALLOWED_VALIDATION = {
    HUMAN_DECISION_SCHEMA: {
        "decision": "CONFIRM_PRIMARY_HOMOLOGY",
        "validation_state": "PRIMARY_HOMOLOGY_VALIDATED",
        "evidence_kind": "HUMAN_PROFESSIONAL_PRIMARY_HOMOLOGY",
        "reviewer_role": "HUMAN_PROFESSIONAL_USER",
    },
    SOURCE_NATIVE_SCHEMA: {
        "decision": "SOURCE_NATIVE_EQUIVALENCE",
        "validation_state": "SOURCE_NATIVE_EQUIVALENCE_VERIFIED",
        "evidence_kind": "PRIMARY_SOURCE_NATIVE_EQUIVALENCE",
        "reviewer_role": None,
    },
}

_FORBIDDEN_EVIDENCE_MARKERS = (
    "M0-G",
    "HISTORICAL_M0G",
    "HISTORICAL_AFFINE",
    "HISTORICAL_CEW",
)


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
    if authority != AUTHORITY_CLOSED:
        raise ValueError(error_code)


def _float_point(value: Any, error_code: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(error_code)
    try:
        point = [float(value[0]), float(value[1])]
    except (TypeError, ValueError) as exc:
        raise ValueError(error_code) from exc
    return point


def _points_equal(left: Any, right: Any) -> bool:
    return _float_point(left, "CAL01_INTERSOURCE_DECISION_POINT_INVALID") == _float_point(
        right, "CAL01_INTERSOURCE_DECISION_POINT_INVALID"
    )


def _validate_candidates(payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if payload.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_CANDIDATE_SCHEMA_INVALID")
    if payload.get("historical_comparator_loaded") is not False:
        raise ValueError("CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN")
    if payload.get("historical_affine_loaded") is not False:
        raise ValueError("CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN")
    if payload.get("eligible_for_registration_fit") is not False:
        raise ValueError("CAL01_INTERSOURCE_AUTHORITY_ESCALATION")
    _require_closed_authority(payload, "CAL01_INTERSOURCE_AUTHORITY_ESCALATION")

    tav5_source = dict(payload.get("tav5_source") or {})
    tav5_raster = dict(payload.get("tav5_raster") or {})
    tav02_source = dict(payload.get("tav02_source") or {})
    if not tav5_source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_TAV5_SOURCE_INVALID")
    if tav5_raster.get("frame") != "RASTER_PIXEL" or not tav5_raster.get("raster_sha256"):
        raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_TAV5_RASTER_INVALID")
    if tav02_source.get("source_id") != "TAV-02S" or not tav02_source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_TAV02_SOURCE_INVALID")
    if payload.get("tav02_coordinate_frame") != "LOCAL_RELATIVE_METRIC":
        raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_TAV02_FRAME_INVALID")
    if not payload.get("tav02_lattice_digest"):
        raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_LATTICE_DIGEST_INVALID")

    candidate_by_id: dict[str, dict[str, Any]] = {}
    for raw in payload.get("candidates", []):
        row = dict(raw)
        occurrence_id = str(row.get("occurrence_id") or "")
        if not occurrence_id or occurrence_id in candidate_by_id:
            raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_OCCURRENCE_INVALID")
        _float_point(row.get("source_point_px"), "CAL01_INTERSOURCE_GOVERNANCE_SOURCE_POINT_INVALID")
        if row.get("source_frame") != "RASTER_PIXEL":
            raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_SOURCE_FRAME_INVALID")
        if row.get("governed_correspondence") is not False or row.get("fit_eligible") is not False:
            raise ValueError("CAL01_INTERSOURCE_AUTHORITY_ESCALATION")
        candidate_by_id[occurrence_id] = row
    if int(payload.get("source_candidate_count", len(candidate_by_id))) != len(candidate_by_id):
        raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_CANDIDATE_COUNT_DRIFT")

    node_by_id: dict[str, dict[str, Any]] = {}
    for raw in payload.get("target_lattice_nodes", []):
        row = dict(raw)
        node_id = str(row.get("lattice_node_id") or "")
        if not node_id or node_id in node_by_id:
            raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_LATTICE_NODE_INVALID")
        _float_point(
            row.get("source_point_normalized_px"),
            "CAL01_INTERSOURCE_GOVERNANCE_LATTICE_NODE_INVALID",
        )
        _float_point(row.get("local_metric_xy_m"), "CAL01_INTERSOURCE_GOVERNANCE_LATTICE_NODE_INVALID")
        if row.get("fit_eligible") is not False or row.get("primary_anchor_authorized") is not False:
            raise ValueError("CAL01_INTERSOURCE_AUTHORITY_ESCALATION")
        node_by_id[node_id] = row
    if int(payload.get("target_lattice_node_count", len(node_by_id))) != len(node_by_id):
        raise ValueError("CAL01_INTERSOURCE_GOVERNANCE_LATTICE_COUNT_DRIFT")
    return candidate_by_id, node_by_id


def _validate_evidence_refs(refs: Any) -> list[str]:
    values = sorted(set(str(value) for value in refs or [] if str(value)))
    if not values:
        raise ValueError("CAL01_INTERSOURCE_DECISION_EVIDENCE_MISSING")
    upper = "\n".join(values).upper()
    if any(marker in upper for marker in _FORBIDDEN_EVIDENCE_MARKERS):
        raise ValueError("CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN")
    return values


def _validate_decision(
    raw: dict[str, Any],
    candidates: dict[str, Any],
    candidate_by_id: dict[str, dict[str, Any]],
    node_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    decision = dict(raw)
    schema = decision.get("schema")
    contract = _ALLOWED_VALIDATION.get(schema)
    if contract is None:
        raise ValueError("CAL01_INTERSOURCE_DECISION_SCHEMA_INVALID")
    if decision.get("decision") != contract["decision"]:
        raise ValueError("CAL01_INTERSOURCE_DECISION_STATE_INVALID")
    if decision.get("validation_state") != contract["validation_state"]:
        raise ValueError("CAL01_INTERSOURCE_DECISION_STATE_INVALID")
    if decision.get("evidence_kind") != contract["evidence_kind"]:
        raise ValueError("CAL01_INTERSOURCE_DECISION_EVIDENCE_KIND_INVALID")
    required_role = contract["reviewer_role"]
    if required_role is not None and decision.get("reviewer_role") != required_role:
        raise ValueError("CAL01_INTERSOURCE_DECISION_REVIEWER_INVALID")
    if any(
        decision.get(key) is not False
        for key in ("historical_comparator_loaded", "historical_affine_loaded", "historical_m0g_loaded")
    ):
        raise ValueError("CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN")
    if decision.get("historical_affine_coefficients") is not None:
        raise ValueError("CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN")
    if decision.get("historical_m0g_coordinate") is not None:
        raise ValueError("CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN")
    _require_closed_authority(decision, "CAL01_INTERSOURCE_AUTHORITY_ESCALATION")

    occurrence_id = str(decision.get("occurrence_id") or "")
    node_id = str(decision.get("tav02_lattice_node_id") or "")
    if occurrence_id not in candidate_by_id:
        raise ValueError("CAL01_INTERSOURCE_DECISION_OCCURRENCE_UNKNOWN")
    if node_id not in node_by_id:
        raise ValueError("CAL01_INTERSOURCE_DECISION_LATTICE_NODE_UNKNOWN")

    tav5_source = candidates["tav5_source"]
    tav5_raster = candidates["tav5_raster"]
    tav02_source = candidates["tav02_source"]
    if decision.get("tav5_source_sha256") != tav5_source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_DECISION_SOURCE_DRIFT")
    if decision.get("tav5_raster_sha256") != tav5_raster.get("raster_sha256"):
        raise ValueError("CAL01_INTERSOURCE_DECISION_RASTER_DRIFT")
    if decision.get("tav02_source_sha256") != tav02_source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_DECISION_SOURCE_DRIFT")
    if decision.get("tav02_lattice_digest") != candidates.get("tav02_lattice_digest"):
        raise ValueError("CAL01_INTERSOURCE_DECISION_LATTICE_DRIFT")
    if decision.get("tav5_source_frame") != "RASTER_PIXEL":
        raise ValueError("CAL01_INTERSOURCE_DECISION_FRAME_DRIFT")

    source_row = candidate_by_id[occurrence_id]
    node_row = node_by_id[node_id]
    if not _points_equal(decision.get("tav5_source_point_px"), source_row.get("source_point_px")):
        raise ValueError("CAL01_INTERSOURCE_DECISION_POINT_DRIFT")
    if not _points_equal(
        decision.get("tav02_source_point_normalized_px"),
        node_row.get("source_point_normalized_px"),
    ):
        raise ValueError("CAL01_INTERSOURCE_DECISION_POINT_DRIFT")

    evidence_refs = _validate_evidence_refs(decision.get("evidence_refs"))
    basis = "HUMAN_PROFESSIONAL_CONFIRMATION" if schema == HUMAN_DECISION_SCHEMA else "SOURCE_NATIVE_EQUIVALENCE"
    return {
        "occurrence_id": occurrence_id,
        "tav5_source_point_px": [float(v) for v in source_row["source_point_px"]],
        "tav5_source_frame": "RASTER_PIXEL",
        "tav5_source_evidence_refs": sorted(
            set(str(v) for v in source_row.get("source_evidence_refs", []) if str(v))
        ),
        "tav02_lattice_node_id": node_id,
        "tav02_source_point_normalized_px": [float(v) for v in node_row["source_point_normalized_px"]],
        "tav02_source_frame": "NORMALIZED_RASTER_PIXEL",
        "tav02_local_metric_xy_m": [float(v) for v in node_row["local_metric_xy_m"]],
        "validation_state": str(decision["validation_state"]),
        "validation_basis": basis,
        "evidence_refs": evidence_refs,
        "governed_correspondence": True,
        "fit_eligible": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


def govern_correspondences(
    candidates: dict[str, Any],
    confirmations: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    candidate_by_id, node_by_id = _validate_candidates(candidates)

    by_source: dict[str, dict[str, Any]] = {}
    by_target: dict[str, str] = {}
    for raw in confirmations or []:
        row = _validate_decision(dict(raw), candidates, candidate_by_id, node_by_id)
        occurrence_id = row["occurrence_id"]
        node_id = row["tav02_lattice_node_id"]
        previous = by_source.get(occurrence_id)
        if previous is not None and previous["tav02_lattice_node_id"] != node_id:
            raise ValueError("CAL01_INTERSOURCE_CONFLICTING_PARTNER")
        source_for_target = by_target.get(node_id)
        if source_for_target is not None and source_for_target != occurrence_id:
            raise ValueError("CAL01_INTERSOURCE_CONFLICTING_PARTNER")
        if previous is not None:
            merged = sorted(set(previous["evidence_refs"]) | set(row["evidence_refs"]))
            previous["evidence_refs"] = merged
            continue
        by_source[occurrence_id] = row
        by_target[node_id] = occurrence_id

    correspondences: list[dict[str, Any]] = []
    for occurrence_id, row in sorted(by_source.items()):
        identity = {
            "occurrence_id": occurrence_id,
            "tav5_source_point_px": row["tav5_source_point_px"],
            "tav02_lattice_node_id": row["tav02_lattice_node_id"],
            "tav02_source_point_normalized_px": row["tav02_source_point_normalized_px"],
        }
        governed = dict(row)
        governed["correspondence_id"] = "CEW-CAL01-CORR-" + _canonical_digest(identity).split(":", 1)[1][:20]
        correspondences.append(governed)

    governed_ids = {row["occurrence_id"] for row in correspondences}
    unconfirmed = [
        dict(candidate_by_id[key])
        for key in sorted(candidate_by_id)
        if key not in governed_ids
    ]
    governed_count = len(correspondences)
    if governed_count >= 4:
        readiness_state = "READY_FOR_REGISTRATION_SPLIT"
        missing_conditions: list[str] = []
        next_action = "FREEZE_REGISTRATION_SPLIT"
        eligible_for_registration_split = True
    else:
        readiness_state = "INSUFFICIENT_INTERSOURCE_CORRESPONDENCES"
        missing_conditions = ["MINIMUM_GOVERNED_CORRESPONDENCES_4"]
        next_action = "TARGETED_INTERSOURCE_HUMAN_REVIEW"
        eligible_for_registration_split = False

    output: dict[str, Any] = {
        "schema": GOVERNED_SCHEMA,
        "program": "CEW-CAL-01",
        "candidate_digest": candidates.get("candidate_digest"),
        "tav5_source": dict(candidates["tav5_source"]),
        "tav5_raster": dict(candidates["tav5_raster"]),
        "tav02_source": dict(candidates["tav02_source"]),
        "tav02_lattice_digest": candidates.get("tav02_lattice_digest"),
        "governed_correspondence_count": governed_count,
        "correspondences": correspondences,
        "unconfirmed_candidate_count": len(unconfirmed),
        "unconfirmed_candidates": unconfirmed,
        "readiness_state": readiness_state,
        "missing_conditions": missing_conditions,
        "next_action": next_action,
        "eligible_for_registration_split": eligible_for_registration_split,
        "eligible_for_registration_fit": False,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "historical_m0g_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    output["governed_digest"] = _canonical_digest(output)
    return output


def build_correspondence_review_packet(candidates: dict[str, Any]) -> dict[str, Any]:
    candidate_by_id, node_by_id = _validate_candidates(candidates)
    review_items = []
    for occurrence_id in sorted(candidate_by_id):
        row = candidate_by_id[occurrence_id]
        review_items.append(
            {
                "review_item_id": f"CEW-CAL01-INTERSOURCE-REVIEW:{occurrence_id}",
                "occurrence_id": occurrence_id,
                "source_context_view": {
                    "source_point_px": [float(v) for v in row["source_point_px"]],
                    "source_frame": "RASTER_PIXEL",
                    "source_evidence_refs": sorted(
                        set(str(v) for v in row.get("source_evidence_refs", []) if str(v))
                    ),
                },
                "target_context_view": {
                    "tav02_source_sha256": candidates["tav02_source"]["sha256"],
                    "lattice_digest": candidates["tav02_lattice_digest"],
                    "coordinate_frame": "LOCAL_RELATIVE_METRIC",
                    "lattice_node_count": len(node_by_id),
                },
                "decision_required": "IDENTIFY_PRIMARY_HOMOLOGOUS_LATTICE_NODE_OR_REJECT",
                "human_confirmation_required": True,
            }
        )

    packet: dict[str, Any] = {
        "schema": REVIEW_PACKET_SCHEMA,
        "program": "CEW-CAL-01",
        "candidate_digest": candidates.get("candidate_digest"),
        "tav5_source": dict(candidates["tav5_source"]),
        "tav5_raster": dict(candidates["tav5_raster"]),
        "tav02_source": dict(candidates["tav02_source"]),
        "tav02_lattice_digest": candidates.get("tav02_lattice_digest"),
        "review_item_count": len(review_items),
        "target_lattice_node_count": len(node_by_id),
        "review_items": review_items,
        "target_lattice_context": [
            {
                "lattice_node_id": node_id,
                "source_point_normalized_px": [float(v) for v in row["source_point_normalized_px"]],
                "local_metric_xy_m": [float(v) for v in row["local_metric_xy_m"]],
            }
            for node_id, row in sorted(node_by_id.items())
        ],
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "historical_m0g_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    packet["review_packet_digest"] = _canonical_digest(packet)
    return packet
