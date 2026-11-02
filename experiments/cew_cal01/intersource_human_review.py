from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from experiments.cew_cal01.anchor_inventory import AUTHORITY_CLOSED


CANDIDATE_SCHEMA = "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_CANDIDATES_v1"
TARGETED_REVIEW_SCHEMA = "CEW_CAL01_INTERSOURCE_TARGETED_HUMAN_REVIEW_v1"
SELECTION_STRATEGY = "SOURCE_ONLY_FARTHEST_POINT_COVERAGE_V1"
DECISION_REQUIRED = "IDENTIFY_PRIMARY_HOMOLOGOUS_LATTICE_NODE_OR_REJECT"


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
        return [float(value[0]), float(value[1])]
    except (TypeError, ValueError) as exc:
        raise ValueError(error_code) from exc


def _require_candidate_contract(candidates: dict[str, Any]) -> tuple[list[dict[str, Any]], float, float]:
    if candidates.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_CANDIDATE_SCHEMA_INVALID")
    if dict(candidates.get("authority") or {}) != AUTHORITY_CLOSED:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_AUTHORITY_ESCALATION")
    if candidates.get("historical_comparator_loaded") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_HISTORICAL_INPUT_FORBIDDEN")
    if candidates.get("historical_affine_loaded") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_HISTORICAL_INPUT_FORBIDDEN")
    if candidates.get("eligible_for_registration_fit") is not False:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_AUTHORITY_ESCALATION")

    raster = dict(candidates.get("tav5_raster") or {})
    if raster.get("frame") != "RASTER_PIXEL" or not raster.get("raster_sha256"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_RASTER_INVALID")
    try:
        width = float(raster.get("width_px", 0))
        height = float(raster.get("height_px", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_RASTER_INVALID") from exc
    if width <= 0 or height <= 0:
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_RASTER_INVALID")

    tav5_source = dict(candidates.get("tav5_source") or {})
    tav02_source = dict(candidates.get("tav02_source") or {})
    if not tav5_source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV5_SOURCE_INVALID")
    if tav02_source.get("source_id") != "TAV-02S" or not tav02_source.get("sha256"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV02_SOURCE_INVALID")
    if candidates.get("tav02_coordinate_frame") != "LOCAL_RELATIVE_METRIC":
        raise ValueError("CAL01_INTERSOURCE_REVIEW_TAV02_FRAME_INVALID")
    if not candidates.get("tav02_lattice_digest"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_LATTICE_DIGEST_INVALID")

    rows = [dict(row) for row in candidates.get("candidates", [])]
    if int(candidates.get("source_candidate_count", len(rows))) != len(rows):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_CANDIDATE_COUNT_DRIFT")
    seen: set[str] = set()
    for row in rows:
        occurrence_id = str(row.get("occurrence_id") or "")
        if not occurrence_id or occurrence_id in seen:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_OCCURRENCE_INVALID")
        seen.add(occurrence_id)
        x, y = _point(row.get("source_point_px"), "CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID")
        if row.get("source_frame") != "RASTER_PIXEL" or x < 0 or y < 0 or x > width or y > height:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID")
        evidence_refs = sorted(set(str(v) for v in row.get("source_evidence_refs", []) if str(v)))
        if not evidence_refs:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_SOURCE_EVIDENCE_MISSING")
        if row.get("governed_correspondence") is not False or row.get("fit_eligible") is not False:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_AUTHORITY_ESCALATION")

    nodes = [dict(row) for row in candidates.get("target_lattice_nodes", [])]
    if int(candidates.get("target_lattice_node_count", len(nodes))) != len(nodes):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_LATTICE_COUNT_DRIFT")
    node_ids = [str(row.get("lattice_node_id") or "") for row in nodes]
    if any(not value for value in node_ids) or len(set(node_ids)) != len(node_ids):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_LATTICE_NODE_INVALID")
    return rows, width, height


def select_targeted_review_batch(candidates: dict[str, Any], batch_size: int = 8) -> list[str]:
    """Select TAV.5 review occurrences without reading target lattice geometry."""

    rows, width, height = _require_candidate_contract(candidates)
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size < 1 or batch_size > len(rows):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_BATCH_SIZE_INVALID")

    by_id = {str(row["occurrence_id"]): row for row in rows}

    def evidence_strength(occurrence_id: str) -> int:
        return len(set(str(v) for v in by_id[occurrence_id].get("source_evidence_refs", []) if str(v)))

    def normalized_point(occurrence_id: str) -> tuple[float, float]:
        x, y = _point(by_id[occurrence_id]["source_point_px"], "CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID")
        return x / width, y / height

    remaining = set(by_id)
    seed = sorted(remaining, key=lambda occurrence_id: (-evidence_strength(occurrence_id), occurrence_id))[0]
    selected = [seed]
    remaining.remove(seed)

    while remaining and len(selected) < batch_size:
        scored: list[tuple[float, int, str]] = []
        selected_points = [normalized_point(occurrence_id) for occurrence_id in selected]
        for occurrence_id in remaining:
            x, y = normalized_point(occurrence_id)
            minimum_distance = min(
                math.hypot(x - selected_x, y - selected_y)
                for selected_x, selected_y in selected_points
            )
            scored.append((minimum_distance, evidence_strength(occurrence_id), occurrence_id))
        best = sorted(scored, key=lambda row: (-row[0], -row[1], row[2]))[0][2]
        selected.append(best)
        remaining.remove(best)

    return selected


def _validate_asset_record(raw: dict[str, Any], *, require_bbox: bool) -> dict[str, Any]:
    row = dict(raw)
    if not row.get("file") or not str(row.get("sha256") or "").startswith("sha256:"):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_ASSET_INVALID")
    if require_bbox:
        bbox = row.get("crop_bbox_px")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValueError("CAL01_INTERSOURCE_REVIEW_ASSET_INVALID")
    return row


def build_targeted_review_manifest(
    candidates: dict[str, Any],
    selected_occurrence_ids: list[str],
    source_assets: dict[str, dict[str, Any]],
    target_overview: dict[str, Any],
) -> dict[str, Any]:
    rows, _, _ = _require_candidate_contract(candidates)
    candidate_by_id = {str(row["occurrence_id"]): row for row in rows}
    selected = [str(value) for value in selected_occurrence_ids]
    if not selected or len(set(selected)) != len(selected) or any(value not in candidate_by_id for value in selected):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_SELECTION_INVALID")
    if set(source_assets) != set(selected):
        raise ValueError("CAL01_INTERSOURCE_REVIEW_SOURCE_ASSET_SET_DRIFT")

    overview = _validate_asset_record(target_overview, require_bbox=False)
    nodes = sorted(
        [dict(row) for row in candidates.get("target_lattice_nodes", [])],
        key=lambda row: str(row.get("lattice_node_id") or ""),
    )
    lattice_context = []
    for row in nodes:
        lattice_context.append(
            {
                "lattice_node_id": str(row["lattice_node_id"]),
                "source_point_normalized_px": _point(
                    row.get("source_point_normalized_px"),
                    "CAL01_INTERSOURCE_REVIEW_LATTICE_NODE_INVALID",
                ),
                "local_metric_xy_m": _point(
                    row.get("local_metric_xy_m"),
                    "CAL01_INTERSOURCE_REVIEW_LATTICE_NODE_INVALID",
                ),
            }
        )

    review_items = []
    for occurrence_id in selected:
        source_row = candidate_by_id[occurrence_id]
        review_items.append(
            {
                "review_item_id": f"CEW-CAL01-TARGETED-INTERSOURCE:{occurrence_id}",
                "occurrence_id": occurrence_id,
                "source_point_px": _point(
                    source_row.get("source_point_px"),
                    "CAL01_INTERSOURCE_REVIEW_SOURCE_POINT_INVALID",
                ),
                "source_frame": "RASTER_PIXEL",
                "source_evidence_refs": sorted(
                    set(str(v) for v in source_row.get("source_evidence_refs", []) if str(v))
                ),
                "source_context_asset": _validate_asset_record(
                    source_assets[occurrence_id], require_bbox=True
                ),
                "decision_required": DECISION_REQUIRED,
                "human_confirmation_required": True,
            }
        )

    result: dict[str, Any] = {
        "schema": TARGETED_REVIEW_SCHEMA,
        "program": "CEW-CAL-01",
        "candidate_digest": candidates.get("candidate_digest"),
        "tav5_source": dict(candidates["tav5_source"]),
        "tav5_raster": dict(candidates["tav5_raster"]),
        "tav02_source": dict(candidates["tav02_source"]),
        "tav02_lattice_digest": candidates.get("tav02_lattice_digest"),
        "tav02_coordinate_frame": "LOCAL_RELATIVE_METRIC",
        "source_candidate_count": len(rows),
        "target_lattice_node_count": len(lattice_context),
        "selection_strategy": SELECTION_STRATEGY,
        "target_geometry_used_for_selection": False,
        "target_node_ranking_performed": False,
        "automatic_homology_proposed": False,
        "selected_occurrence_ids": selected,
        "review_item_count": len(review_items),
        "review_items": review_items,
        "target_overview_asset": overview,
        "target_lattice_context": lattice_context,
        "decision_required": DECISION_REQUIRED,
        "human_confirmation_required": True,
        "eligible_for_registration_fit": False,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "historical_m0g_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["review_package_digest"] = _canonical_digest(result)
    return result
