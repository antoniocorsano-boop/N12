from __future__ import annotations

import math
import re
from typing import Any


_WITNESS_PROVENANCE = "HISTORICAL_NONREPLAYABLE_WITNESS"
_ROT90_FRAME = "ROT90_CCW_300DPI"
_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _as_positive_float(value: Any, error: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(error) from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(error)
    return number


def _as_float(value: Any, error: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(error) from exc
    if not math.isfinite(number):
        raise ValueError(error)
    return number


def _closed_authority(mapping: Any) -> bool:
    if not isinstance(mapping, dict):
        return False
    keys = (
        "structural_identity_authorized",
        "canonical_geometry_authorized",
        "canonical_write_authorized",
        "m0g_authorized",
    )
    return all(mapping.get(key) is False for key in keys)


def _validate_registration(
    *,
    structural_bridge: dict[str, Any],
    registration: dict[str, Any],
    registration_commit: str,
    registration_provenance: str,
) -> tuple[float, float]:
    if registration_provenance != _WITNESS_PROVENANCE:
        raise ValueError("REGISTRATION_PROVENANCE_NOT_WITNESS")
    if not isinstance(registration_commit, str) or not _HEX40.fullmatch(registration_commit):
        raise ValueError("REGISTRATION_COMMIT_INVALID")
    if not isinstance(structural_bridge, dict) or not isinstance(registration, dict):
        raise ValueError("REGISTRATION_INPUT_INVALID")
    if not _closed_authority(structural_bridge.get("authority")):
        raise ValueError("STRUCTURAL_BRIDGE_AUTHORITY_DRIFT")
    if registration.get("source_frame") != _ROT90_FRAME:
        raise ValueError("REGISTRATION_FRAME_UNSUPPORTED")
    if registration.get("validation_state") != "CROSS_VALIDATED":
        raise ValueError("REGISTRATION_NOT_CROSS_VALIDATED")
    if registration.get("usage_rule") != "REGISTER_SHEET_TO_COMMON_PT_XY":
        raise ValueError("REGISTRATION_USAGE_RULE_INVALID")

    raster = structural_bridge.get("governed_raster")
    if not isinstance(raster, dict) or raster.get("frame") != "RASTER_PIXEL":
        raise ValueError("GOVERNED_RASTER_REQUIRED")
    raster_width = _as_positive_float(raster.get("width_px"), "GOVERNED_RASTER_DIMENSIONS_REQUIRED")
    raster_height = _as_positive_float(raster.get("height_px"), "GOVERNED_RASTER_DIMENSIONS_REQUIRED")
    frame_width = _as_positive_float(registration.get("frame_width_px"), "REGISTRATION_FRAME_MISMATCH")
    frame_height = _as_positive_float(registration.get("frame_height_px"), "REGISTRATION_FRAME_MISMATCH")
    if abs(frame_width - raster_height) > 1e-9 or abs(frame_height - raster_width) > 1e-9:
        raise ValueError("REGISTRATION_FRAME_MISMATCH")
    return raster_width, raster_height


def _project_center(
    *,
    geometry: dict[str, Any],
    raster_width: float,
    raster_height: float,
    registration: dict[str, Any],
) -> tuple[float, float, float, float, float, float]:
    if not isinstance(geometry, dict) or geometry.get("frame") != "RASTER_PIXEL":
        raise ValueError("CANDIDATE_PIXEL_GEOMETRY_REQUIRED")
    x = _as_float(geometry.get("x"), "CANDIDATE_PIXEL_GEOMETRY_INVALID")
    y = _as_float(geometry.get("y"), "CANDIDATE_PIXEL_GEOMETRY_INVALID")
    width = _as_positive_float(geometry.get("width"), "CANDIDATE_PIXEL_GEOMETRY_INVALID")
    height = _as_positive_float(geometry.get("height"), "CANDIDATE_PIXEL_GEOMETRY_INVALID")
    center_x = x + width / 2.0
    center_y = y + height / 2.0
    if center_x < 0.0 or center_y < 0.0 or center_x > raster_width or center_y > raster_height:
        raise ValueError("CANDIDATE_PIXEL_GEOMETRY_OUTSIDE_RASTER")

    frame_width = float(registration["frame_width_px"])
    frame_height = float(registration["frame_height_px"])
    registered_u = (center_y / raster_height) * frame_width
    registered_v = ((raster_width - center_x) / raster_width) * frame_height

    projected_x = (
        _as_float(registration.get("metric_x_from_u"), "REGISTRATION_COEFFICIENT_INVALID") * registered_u
        + _as_float(registration.get("metric_x_from_v"), "REGISTRATION_COEFFICIENT_INVALID") * registered_v
        + _as_float(registration.get("metric_x_offset"), "REGISTRATION_COEFFICIENT_INVALID")
    )
    projected_y = (
        _as_float(registration.get("metric_y_from_u"), "REGISTRATION_COEFFICIENT_INVALID") * registered_u
        + _as_float(registration.get("metric_y_from_v"), "REGISTRATION_COEFFICIENT_INVALID") * registered_v
        + _as_float(registration.get("metric_y_offset"), "REGISTRATION_COEFFICIENT_INVALID")
    )
    return center_x, center_y, registered_u, registered_v, projected_x, projected_y


def build_metric_registration_witness(
    *,
    structural_bridge: dict[str, Any],
    registration: dict[str, Any],
    registration_commit: str,
    registration_provenance: str,
) -> dict[str, Any]:
    """Project governed raster candidates into the historical common XY frame.

    The historical affine coefficients are retained strictly as a non-replayable
    witness. The result cannot assign structural identity, canonical geometry,
    or write authority.
    """

    raster_width, raster_height = _validate_registration(
        structural_bridge=structural_bridge,
        registration=registration,
        registration_commit=registration_commit,
        registration_provenance=registration_provenance,
    )
    rows = structural_bridge.get("occurrence_bridge")
    if not isinstance(rows, list):
        raise ValueError("STRUCTURAL_CANDIDATES_REQUIRED")
    if structural_bridge.get("structural_candidate_count") != len(rows):
        raise ValueError("STRUCTURAL_CANDIDATE_COUNT_DRIFT")

    projections: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: str(item.get("occurrence_id") or "")):
        if row.get("structural_identity_authorized") is not False or row.get("canonical_write_authorized") is not False:
            raise ValueError("STRUCTURAL_CANDIDATE_AUTHORITY_DRIFT")
        occurrence_id = str(row.get("occurrence_id") or "").strip()
        if not occurrence_id:
            raise ValueError("OCCURRENCE_ID_REQUIRED")
        center_x, center_y, registered_u, registered_v, projected_x, projected_y = _project_center(
            geometry=row.get("pixel_geometry"),
            raster_width=raster_width,
            raster_height=raster_height,
            registration=registration,
        )
        projections.append(
            {
                "occurrence_id": occurrence_id,
                "object_candidate_id": row.get("object_candidate_id"),
                "evidence_candidate_id": row.get("evidence_candidate_id"),
                "source_center_x_px": center_x,
                "source_center_y_px": center_y,
                "registered_u_px": registered_u,
                "registered_v_px": registered_v,
                "projected_x_m": projected_x,
                "projected_y_m": projected_y,
                "metric_state": "HISTORICAL_WITNESS_PROJECTION_ONLY",
                "registration_provenance": registration_provenance,
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "canonical_write_authorized": False,
            }
        )

    return {
        "schema": "CEW_SPIRAL_METRIC_REGISTRATION_WITNESS_v1",
        "sheet_id": registration.get("sheet_id"),
        "level_id": registration.get("level_id"),
        "registration_commit": registration_commit,
        "registration_provenance": registration_provenance,
        "registration_method": registration.get("registration_method"),
        "registration_validation_state": registration.get("validation_state"),
        "projection_count": len(projections),
        "projections": projections,
        "authority": {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }


def compare_witness_to_historical_supports(
    *,
    witness: dict[str, Any],
    supports: list[dict[str, Any]],
    level_id: str,
) -> dict[str, Any]:
    if not isinstance(witness, dict) or witness.get("registration_provenance") != _WITNESS_PROVENANCE:
        raise ValueError("METRIC_WITNESS_REQUIRED")
    if not _closed_authority(witness.get("authority")):
        raise ValueError("METRIC_WITNESS_AUTHORITY_DRIFT")
    candidates = [
        row
        for row in supports
        if isinstance(row, dict) and row.get("level_id") == level_id and row.get("node_role") == "SUPPORT_CORE"
    ]
    if not candidates:
        raise ValueError("HISTORICAL_SUPPORTS_REQUIRED")

    comparisons: list[dict[str, Any]] = []
    for projection in witness.get("projections") or []:
        px = _as_float(projection.get("projected_x_m"), "METRIC_PROJECTION_INVALID")
        py = _as_float(projection.get("projected_y_m"), "METRIC_PROJECTION_INVALID")
        ranked: list[tuple[float, str, dict[str, Any]]] = []
        for support in candidates:
            sx = _as_float(support.get("x_m"), "HISTORICAL_SUPPORT_COORDINATES_INVALID")
            sy = _as_float(support.get("y_m"), "HISTORICAL_SUPPORT_COORDINATES_INVALID")
            node_id = str(support.get("node_id") or "")
            if not node_id:
                raise ValueError("HISTORICAL_SUPPORT_NODE_ID_REQUIRED")
            ranked.append((math.hypot(px - sx, py - sy), node_id, support))
        distance, _, nearest = min(ranked, key=lambda item: (item[0], item[1]))
        comparisons.append(
            {
                "occurrence_id": projection.get("occurrence_id"),
                "object_candidate_id": projection.get("object_candidate_id"),
                "projected_x_m": px,
                "projected_y_m": py,
                "nearest_historical_node_id": nearest.get("node_id"),
                "nearest_historical_support_id": nearest.get("support_id"),
                "nearest_distance_m": distance,
                "binding_status": "NO_AUTOMATIC_BINDING",
                "historical_witness_may_mutate_current_candidate": False,
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "canonical_write_authorized": False,
            }
        )

    return {
        "schema": "CEW_SPIRAL_METRIC_WITNESS_HISTORICAL_COMPARISON_v1",
        "level_id": level_id,
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "authority": {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }
