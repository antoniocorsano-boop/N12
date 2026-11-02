from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any

from experiments.cew_cal01.anchor_inventory import AUTHORITY_CLOSED


VALIDATED_REVIEW_STATES = {"REUSED_HUMAN_RECEIPT", "DIRECT_HUMAN_DECISION"}
PENDING_REVIEW_STATE = "PENDING_HUMAN_REVIEW"
SUPPORTED_ORIENTATIONS = {"HORIZONTAL", "VERTICAL"}


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


def _source(payload: dict[str, Any]) -> dict[str, str]:
    source = dict(payload.get("source") or {})
    source_id = str(source.get("source_id") or "")
    source_sha = str(source.get("sha256") or "")
    if not source_id or not source_sha:
        raise ValueError("CAL01_METRIC_NETWORK_SOURCE_INVALID")
    return {"source_id": source_id, "sha256": source_sha}


def _endpoints(request: dict[str, Any]) -> tuple[list[float], list[float], float]:
    orientation = str(request.get("orientation") or "")
    if orientation not in SUPPORTED_ORIENTATIONS:
        raise ValueError("CAL01_METRIC_NETWORK_ORIENTATION_INVALID")
    carrier = float(request.get("carrier_axis_px"))
    start = float(request.get("interval_start_px"))
    end = float(request.get("interval_end_px"))
    span = end - start
    if span <= 0:
        raise ValueError("CAL01_METRIC_NETWORK_SPAN_INVALID")
    if orientation == "HORIZONTAL":
        return [start, carrier], [end, carrier], span
    return [carrier, start], [carrier, end], span


def build_metric_relation_network(manifest: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    source = _source(manifest)
    if _source(packet) != source:
        raise ValueError("CAL01_METRIC_NETWORK_SOURCE_DRIFT")
    if packet.get("review_manifest_digest") != manifest.get("review_digest"):
        raise ValueError("CAL01_METRIC_NETWORK_MANIFEST_DIGEST_DRIFT")

    _require_closed_authority(manifest, "CAL01_METRIC_NETWORK_AUTHORITY_ESCALATION")
    _require_closed_authority(packet, "CAL01_METRIC_NETWORK_AUTHORITY_ESCALATION")

    requests = [dict(row) for row in manifest.get("review_requests", [])]
    reviews = [dict(row) for row in packet.get("reviews", [])]
    if int(manifest.get("review_request_count", len(requests))) != len(requests):
        raise ValueError("CAL01_METRIC_NETWORK_REVIEW_COUNT_DRIFT")
    if int(packet.get("review_count", len(reviews))) != len(reviews) or len(requests) != len(reviews):
        raise ValueError("CAL01_METRIC_NETWORK_REVIEW_COUNT_DRIFT")

    request_by_id: dict[str, dict[str, Any]] = {}
    for row in requests:
        review_id = str(row.get("review_id") or "")
        if not review_id or review_id in request_by_id:
            raise ValueError("CAL01_METRIC_NETWORK_REVIEW_ID_INVALID")
        request_by_id[review_id] = row

    review_by_id: dict[str, dict[str, Any]] = {}
    for row in reviews:
        review_id = str(row.get("review_id") or "")
        if not review_id or review_id in review_by_id:
            raise ValueError("CAL01_METRIC_NETWORK_REVIEW_ID_INVALID")
        review_by_id[review_id] = row

    if set(request_by_id) != set(review_by_id):
        raise ValueError("CAL01_METRIC_NETWORK_REVIEW_ID_DRIFT")

    relations: list[dict[str, Any]] = []
    pending_reviews: list[dict[str, Any]] = []
    chain_totals: Counter[str] = Counter()
    chain_validated: Counter[str] = Counter()

    for review_id in sorted(request_by_id):
        request = request_by_id[review_id]
        review = review_by_id[review_id]
        side = str(request.get("side") or "")
        chain_id = str(request.get("chain_id") or "")
        interval_index = int(request.get("interval_index", -1))
        orientation = str(request.get("orientation") or "")
        if not side or not chain_id or interval_index < 0 or orientation not in SUPPORTED_ORIENTATIONS:
            raise ValueError("CAL01_METRIC_NETWORK_INTERVAL_GEOMETRY_INVALID")
        if (
            str(review.get("side") or "") != side
            or str(review.get("chain_id") or "") != chain_id
            or int(review.get("interval_index", -1)) != interval_index
        ):
            raise ValueError("CAL01_METRIC_NETWORK_REVIEW_GEOMETRY_DRIFT")
        if review.get("eligible_for_metric_calibration") is not False or review.get("primary_anchor_authorized") is not False:
            raise ValueError("CAL01_METRIC_NETWORK_AUTHORITY_ESCALATION")

        point_a, point_b, pixel_span = _endpoints(request)
        chain_totals[chain_id] += 1
        state = str(review.get("review_state") or "")
        value = review.get("validated_value_m")

        if state in VALIDATED_REVIEW_STATES:
            if value is None or float(value) <= 0:
                raise ValueError("CAL01_METRIC_NETWORK_VALUE_INVALID")
            value_m = float(value)
            chain_validated[chain_id] += 1
            relations.append(
                {
                    "review_id": review_id,
                    "side": side,
                    "chain_id": chain_id,
                    "interval_index": interval_index,
                    "orientation": orientation,
                    "source_point_a_px": point_a,
                    "source_point_b_px": point_b,
                    "pixel_span": pixel_span,
                    "validated_value_m": value_m,
                    "px_per_m": pixel_span / value_m,
                    "human_provenance_state": state,
                    "eligible_for_metric_calibration": False,
                    "primary_anchor_authorized": False,
                }
            )
        elif state == PENDING_REVIEW_STATE:
            if value is not None:
                raise ValueError("CAL01_METRIC_NETWORK_PENDING_VALUE_PRESENT")
            pending_reviews.append(
                {
                    "review_id": review_id,
                    "side": side,
                    "chain_id": chain_id,
                    "interval_index": interval_index,
                    "orientation": orientation,
                    "validated_value_m": None,
                }
            )
        else:
            raise ValueError("CAL01_METRIC_NETWORK_REVIEW_STATE_INVALID")

    expected_validated = int(packet.get("validated_human_relation_count", len(relations)))
    expected_pending = int(packet.get("pending_human_review_count", len(pending_reviews)))
    if expected_validated != len(relations) or expected_pending != len(pending_reviews):
        raise ValueError("CAL01_METRIC_NETWORK_PACKET_COUNT_DRIFT")

    chain_stats = [
        {
            "chain_id": chain_id,
            "total_interval_count": int(chain_totals[chain_id]),
            "validated_interval_count": int(chain_validated[chain_id]),
            "pending_interval_count": int(chain_totals[chain_id] - chain_validated[chain_id]),
            "complete": bool(chain_totals[chain_id] and chain_totals[chain_id] == chain_validated[chain_id]),
        }
        for chain_id in sorted(chain_totals)
    ]
    orientation_counts = dict(sorted(Counter(row["orientation"] for row in relations).items()))
    side_counts = dict(sorted(Counter(row["side"] for row in relations).items()))
    complete_chain_ids = [row["chain_id"] for row in chain_stats if row["complete"]]

    network: dict[str, Any] = {
        "schema": "CEW_CAL01_METRIC_RELATION_NETWORK_v1",
        "program": "CEW-CAL-01",
        "source": source,
        "review_manifest_digest": manifest.get("review_digest"),
        "human_review_packet_digest": packet.get("packet_digest"),
        "relation_count": len(relations),
        "pending_review_count": len(pending_reviews),
        "orientation_counts": orientation_counts,
        "side_counts": side_counts,
        "chain_stats": chain_stats,
        "complete_chain_ids": complete_chain_ids,
        "relations": relations,
        "pending_reviews": pending_reviews,
        "primary_anchor_count": 0,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    network["network_digest"] = _canonical_digest(network)
    return network
