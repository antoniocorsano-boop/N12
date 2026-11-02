from __future__ import annotations

import hashlib
import itertools
import json
import math
from typing import Any

from experiments.cew_cal01.anchor_inventory import AUTHORITY_CLOSED


GOVERNED_SCHEMA = "CEW_CAL01_INTERSOURCE_GOVERNED_CORRESPONDENCES_v1"
SPLIT_SCHEMA = "CEW_CAL01_INTERSOURCE_REGISTRATION_SPLIT_v1"


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _point(value: Any, error_code: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(error_code)
    try:
        point = [float(value[0]), float(value[1])]
    except (TypeError, ValueError) as exc:
        raise ValueError(error_code) from exc
    if not all(math.isfinite(component) for component in point):
        raise ValueError(error_code)
    return point


def _has_noncollinear_triple(points: list[list[float]]) -> bool:
    if len(points) < 3:
        return False
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    scale = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    tolerance = 1e-10 * scale * scale
    for first, second, third in itertools.combinations(points, 3):
        twice_area = abs(
            (second[0] - first[0]) * (third[1] - first[1])
            - (second[1] - first[1]) * (third[0] - first[0])
        )
        if twice_area > tolerance:
            return True
    return False


def _normalized_radial_score(rows: list[dict[str, Any]], row: dict[str, Any]) -> float:
    def score_for(field: str) -> float:
        points = [item[field] for item in rows]
        cx = sum(point[0] for point in points) / len(points)
        cy = sum(point[1] for point in points) / len(points)
        span_x = max(point[0] for point in points) - min(point[0] for point in points)
        span_y = max(point[1] for point in points) - min(point[1] for point in points)
        scale = max(span_x, span_y, 1.0)
        point = row[field]
        return ((point[0] - cx) / scale) ** 2 + ((point[1] - cy) / scale) ** 2

    return score_for("tav5_source_point_px") + score_for("tav02_source_point_normalized_px")


def _validate_governed(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("schema") != GOVERNED_SCHEMA:
        raise ValueError("CAL01_INTERSOURCE_SPLIT_SCHEMA_INVALID")
    if any(
        payload.get(key) is not False
        for key in ("historical_comparator_loaded", "historical_affine_loaded", "historical_m0g_loaded")
    ):
        raise ValueError("CAL01_INTERSOURCE_SPLIT_HISTORICAL_INPUT_FORBIDDEN")
    if dict(payload.get("authority") or {}) != AUTHORITY_CLOSED:
        raise ValueError("CAL01_INTERSOURCE_SPLIT_AUTHORITY_ESCALATION")
    if payload.get("eligible_for_registration_fit") is not False:
        raise ValueError("CAL01_INTERSOURCE_SPLIT_AUTHORITY_ESCALATION")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_occurrences: set[str] = set()
    seen_targets: set[str] = set()
    for raw in payload.get("correspondences", []):
        correspondence_id = str(raw.get("correspondence_id") or "")
        occurrence_id = str(raw.get("occurrence_id") or "")
        target_id = str(raw.get("tav02_lattice_node_id") or "")
        if not correspondence_id or correspondence_id in seen_ids:
            raise ValueError("CAL01_INTERSOURCE_SPLIT_CORRESPONDENCE_ID_INVALID")
        if not occurrence_id or occurrence_id in seen_occurrences:
            raise ValueError("CAL01_INTERSOURCE_SPLIT_DUPLICATE_PARTNER")
        if not target_id or target_id in seen_targets:
            raise ValueError("CAL01_INTERSOURCE_SPLIT_DUPLICATE_PARTNER")
        if raw.get("governed_correspondence") is not True:
            raise ValueError("CAL01_INTERSOURCE_SPLIT_UNGOVERNED_INPUT")
        if raw.get("fit_eligible") is not False:
            raise ValueError("CAL01_INTERSOURCE_SPLIT_AUTHORITY_ESCALATION")
        if raw.get("tav5_source_frame") != "RASTER_PIXEL":
            raise ValueError("CAL01_INTERSOURCE_SPLIT_FRAME_INVALID")
        if raw.get("tav02_source_frame") != "NORMALIZED_RASTER_PIXEL":
            raise ValueError("CAL01_INTERSOURCE_SPLIT_FRAME_INVALID")
        if dict(raw.get("authority") or {}) != AUTHORITY_CLOSED:
            raise ValueError("CAL01_INTERSOURCE_SPLIT_AUTHORITY_ESCALATION")

        row = {
            "correspondence_id": correspondence_id,
            "occurrence_id": occurrence_id,
            "tav5_source_point_px": _point(
                raw.get("tav5_source_point_px"),
                "CAL01_INTERSOURCE_SPLIT_SOURCE_POINT_INVALID",
            ),
            "tav5_source_frame": "RASTER_PIXEL",
            "tav02_lattice_node_id": target_id,
            "tav02_source_point_normalized_px": _point(
                raw.get("tav02_source_point_normalized_px"),
                "CAL01_INTERSOURCE_SPLIT_TARGET_POINT_INVALID",
            ),
            "tav02_source_frame": "NORMALIZED_RASTER_PIXEL",
            "validation_state": str(raw.get("validation_state") or ""),
            "validation_basis": str(raw.get("validation_basis") or ""),
            "governed_correspondence": True,
            "fit_eligible": False,
            "authority": dict(AUTHORITY_CLOSED),
        }
        rows.append(row)
        seen_ids.add(correspondence_id)
        seen_occurrences.add(occurrence_id)
        seen_targets.add(target_id)

    rows.sort(key=lambda item: item["correspondence_id"])
    if int(payload.get("governed_correspondence_count", len(rows))) != len(rows):
        raise ValueError("CAL01_INTERSOURCE_SPLIT_CORRESPONDENCE_COUNT_DRIFT")
    return rows


def _base_output(payload: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": SPLIT_SCHEMA,
        "program": "CEW-CAL-01",
        "governed_digest": payload.get("governed_digest"),
        "candidate_digest": payload.get("candidate_digest"),
        "tav5_source": dict(payload.get("tav5_source") or {}),
        "tav5_raster": dict(payload.get("tav5_raster") or {}),
        "tav02_source": dict(payload.get("tav02_source") or {}),
        "tav02_lattice_digest": payload.get("tav02_lattice_digest"),
        "governed_correspondence_count": len(rows),
        "holdout_selection_policy": "MAX_NORMALIZED_RADIAL_COVERAGE_THEN_CORRESPONDENCE_ID",
        "residual_fields_considered": False,
        "affine_fit_performed": False,
        "eligible_for_metric_anchor_promotion": False,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "historical_m0g_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


def _insufficient(
    payload: dict[str, Any],
    rows: list[dict[str, Any]],
    missing_conditions: list[str],
) -> dict[str, Any]:
    output = _base_output(payload, rows)
    output.update(
        {
            "state": "INSUFFICIENT_INTERSOURCE_CORRESPONDENCES",
            "missing_conditions": list(missing_conditions),
            "fit_count": 0,
            "holdout_count": 0,
            "fit_correspondence_ids": [],
            "holdout_correspondence_ids": [],
            "frozen_correspondences": [],
            "source_fit_geometry_noncollinear": False,
            "target_fit_geometry_noncollinear": False,
            "ready_for_affine_fit": False,
            "next_action": "TARGETED_INTERSOURCE_HUMAN_REVIEW",
        }
    )
    output["split_digest"] = _canonical_digest(output)
    return output


def freeze_registration_split(governed: dict[str, Any]) -> dict[str, Any]:
    rows = _validate_governed(governed)
    if len(rows) < 4:
        return _insufficient(
            governed,
            rows,
            ["MINIMUM_GOVERNED_CORRESPONDENCES_4"],
        )

    source_points = [row["tav5_source_point_px"] for row in rows]
    target_points = [row["tav02_source_point_normalized_px"] for row in rows]
    source_global_noncollinear = _has_noncollinear_triple(source_points)
    target_global_noncollinear = _has_noncollinear_triple(target_points)
    missing: list[str] = []
    if not source_global_noncollinear:
        missing.append("NONCOLLINEAR_SOURCE_FIT_GEOMETRY_REQUIRED")
    if not target_global_noncollinear:
        missing.append("NONCOLLINEAR_TARGET_FIT_GEOMETRY_REQUIRED")
    if missing:
        return _insufficient(governed, rows, missing)

    holdout_order = sorted(
        rows,
        key=lambda row: (
            -_normalized_radial_score(rows, row),
            row["correspondence_id"],
        ),
    )
    chosen_holdout: dict[str, Any] | None = None
    fit_rows: list[dict[str, Any]] = []
    for candidate in holdout_order:
        trial_fit = [
            row for row in rows if row["correspondence_id"] != candidate["correspondence_id"]
        ]
        if len(trial_fit) < 3:
            continue
        if not _has_noncollinear_triple([row["tav5_source_point_px"] for row in trial_fit]):
            continue
        if not _has_noncollinear_triple(
            [row["tav02_source_point_normalized_px"] for row in trial_fit]
        ):
            continue
        chosen_holdout = candidate
        fit_rows = trial_fit
        break

    if chosen_holdout is None:
        return _insufficient(
            governed,
            rows,
            ["NONDEGENERATE_COMMON_FIT_SUBSET_REQUIRED"],
        )

    fit_ids = [row["correspondence_id"] for row in fit_rows]
    holdout_ids = [chosen_holdout["correspondence_id"]]
    frozen: list[dict[str, Any]] = []
    for row in rows:
        frozen_row = dict(row)
        frozen_row["split_role"] = (
            "HOLDOUT" if row["correspondence_id"] == chosen_holdout["correspondence_id"] else "FIT"
        )
        frozen.append(frozen_row)

    output = _base_output(governed, rows)
    output.update(
        {
            "state": "REGISTRATION_SPLIT_FROZEN",
            "missing_conditions": [],
            "fit_count": len(fit_rows),
            "holdout_count": 1,
            "fit_correspondence_ids": fit_ids,
            "holdout_correspondence_ids": holdout_ids,
            "frozen_correspondences": frozen,
            "source_fit_geometry_noncollinear": True,
            "target_fit_geometry_noncollinear": True,
            "ready_for_affine_fit": True,
            "next_action": "BUILD_INTERSOURCE_AFFINE_REGISTRATION",
        }
    )
    output["split_digest"] = _canonical_digest(output)
    return output
