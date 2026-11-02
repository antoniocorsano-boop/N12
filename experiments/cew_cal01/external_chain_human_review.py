from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


REQUIRED_REVIEWER_ROLE = "HUMAN_PROFESSIONAL_USER"
REQUIRED_METRIC_RELATION_STATE = "PRIMARY_VISUAL_VALIDATED"
REQUIRED_CALIBRATION_ROLE = "LINEAR_DIMENSION"


def normalize_source_bbox_ccw(
    bbox_source_px: list[float] | tuple[float, float, float, float],
    *,
    source_width_px: float,
) -> list[float]:
    if len(bbox_source_px) != 4:
        raise ValueError("CAL01_HUMAN_RECEIPT_SOURCE_BBOX_INVALID")
    x1, y1, x2, y2 = (float(value) for value in bbox_source_px)
    width = float(source_width_px)
    if width <= 0 or x2 < x1 or y2 < y1:
        raise ValueError("CAL01_HUMAN_RECEIPT_SOURCE_BBOX_INVALID")
    return [y1, width - x2, y2, width - x1]


def _bbox_center(bbox: list[float] | tuple[float, float, float, float]) -> tuple[float, float]:
    x1, y1, x2, y2 = (float(value) for value in bbox)
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def _point_inside_bbox(point: tuple[float, float], bbox: list[float]) -> bool:
    x, y = point
    x1, y1, x2, y2 = (float(value) for value in bbox)
    return x1 <= x <= x2 and y1 <= y <= y2


def _source_bbox(receipt: dict[str, Any]) -> list[float] | None:
    value = receipt.get("source_bbox_px")
    if value is None:
        value = receipt.get("source_bbox_union_px")
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError("CAL01_HUMAN_RECEIPT_SOURCE_BBOX_INVALID")
    return [float(item) for item in value]


def _is_reusable_human_receipt(receipt: dict[str, Any]) -> bool:
    return (
        receipt.get("reviewer_role") == REQUIRED_REVIEWER_ROLE
        and receipt.get("metric_relation_state") == REQUIRED_METRIC_RELATION_STATE
        and receipt.get("calibration_role") == REQUIRED_CALIBRATION_ROLE
        and receipt.get("eligible_for_metric_relation_network") is True
        and receipt.get("eligible_for_metric_calibration") is False
        and receipt.get("primary_anchor_authorized") is False
    )


def _receipt_value_m(receipt: dict[str, Any]) -> float:
    value = receipt.get("value")
    if not isinstance(value, dict) or value.get("length_m") is None:
        raise ValueError("CAL01_HUMAN_RECEIPT_LINEAR_VALUE_MISSING")
    result = float(value["length_m"])
    if result <= 0:
        raise ValueError("CAL01_HUMAN_RECEIPT_LINEAR_VALUE_INVALID")
    return result


def reconcile_human_receipts(
    manifest: dict[str, Any],
    receipts: Iterable[dict[str, Any]],
    *,
    source_width_px: float,
) -> dict[str, Any]:
    source = dict(manifest.get("source") or {})
    source_id = str(source.get("source_id") or "")
    source_sha = str(source.get("sha256") or "")
    if not source_id or not source_sha:
        raise ValueError("CAL01_HUMAN_RECEIPT_SOURCE_INVALID")

    requests = [dict(row) for row in manifest.get("review_requests", [])]
    if int(manifest.get("review_request_count", len(requests))) != len(requests):
        raise ValueError("CAL01_HUMAN_RECEIPT_REVIEW_COUNT_DRIFT")

    request_by_id: dict[str, dict[str, Any]] = {}
    for row in requests:
        review_id = str(row.get("review_id") or "")
        bbox = row.get("crop_bbox_normalized_px")
        if not review_id or review_id in request_by_id:
            raise ValueError("CAL01_HUMAN_RECEIPT_REVIEW_ID_INVALID")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise ValueError("CAL01_HUMAN_RECEIPT_INTERVAL_BBOX_INVALID")
        request_by_id[review_id] = row

    bindings: dict[str, dict[str, Any]] = {}
    unmatched: list[str] = []
    ineligible: list[str] = []
    source_mismatch: list[str] = []
    candidate_bindings: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for raw in receipts:
        receipt = dict(raw)
        receipt_id = str(receipt.get("review_id") or "")
        if not receipt_id:
            raise ValueError("CAL01_HUMAN_RECEIPT_REVIEW_ID_MISSING")

        if not _is_reusable_human_receipt(receipt):
            ineligible.append(receipt_id)
            continue

        if receipt.get("source_document") != source_id or receipt.get("source_sha256") != source_sha:
            source_mismatch.append(receipt_id)
            continue

        source_bbox = _source_bbox(receipt)
        if source_bbox is None:
            ineligible.append(receipt_id)
            continue
        normalized_bbox = normalize_source_bbox_ccw(source_bbox, source_width_px=source_width_px)
        center = _bbox_center(normalized_bbox)
        matched_review_ids = sorted(
            review_id
            for review_id, request in request_by_id.items()
            if _point_inside_bbox(center, request["crop_bbox_normalized_px"])
        )
        if not matched_review_ids:
            unmatched.append(receipt_id)
            continue
        if len(matched_review_ids) != 1:
            raise ValueError("CAL01_HUMAN_RECEIPT_INTERVAL_AMBIGUOUS")

        interval_review_id = matched_review_ids[0]
        candidate_bindings[interval_review_id].append(
            {
                "receipt_review_id": receipt_id,
                "source_bbox_px": source_bbox,
                "normalized_bbox_px": normalized_bbox,
                "value_m": _receipt_value_m(receipt),
                "human_reading": receipt.get("human_reading"),
                "metric_relation_state": receipt.get("metric_relation_state"),
                "metric_source_kind": receipt.get("metric_source_kind"),
                "qualified_discovery_basis": receipt.get("qualified_discovery_basis"),
                "eligible_for_metric_calibration": False,
                "primary_anchor_authorized": False,
            }
        )

    for interval_review_id, rows in sorted(candidate_bindings.items()):
        values = {float(row["value_m"]) for row in rows}
        if len(values) > 1:
            raise ValueError("CAL01_HUMAN_RECEIPT_VALUE_CONFLICT")
        bindings[interval_review_id] = sorted(
            rows,
            key=lambda row: str(row["receipt_review_id"]),
        )[0]

    return {
        "source": source,
        "reused_count": len(bindings),
        "bindings": bindings,
        "unmatched_receipt_ids": sorted(unmatched),
        "ineligible_receipt_ids": sorted(ineligible),
        "source_mismatch_receipt_ids": sorted(source_mismatch),
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
    }
