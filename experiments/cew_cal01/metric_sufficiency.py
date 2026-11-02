from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from statistics import median
from typing import Any

from experiments.cew_cal01.anchor_inventory import AUTHORITY_CLOSED


VALIDATED_REVIEW_STATES = {"REUSED_HUMAN_RECEIPT", "DIRECT_HUMAN_DECISION"}
PENDING_REVIEW_STATE = "PENDING_HUMAN_REVIEW"
SUPPORTED_ORIENTATIONS = {"HORIZONTAL", "VERTICAL"}
SCALE_TOLERANCE_RATIO = 0.05
MIN_RELATIONS = 4
MIN_PER_ORIENTATION = 2
MIN_SIDES = 2
MIN_COMPLETE_CHAINS = 1
MIN_ELIGIBLE_ANCHORS = 4
FIT_POINT_COUNT = 3


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


def _validate_network(network: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if network.get("schema") != "CEW_CAL01_METRIC_RELATION_NETWORK_v1":
        raise ValueError("CAL01_METRIC_GATE_NETWORK_SCHEMA_INVALID")
    _source(network)
    _require_closed_authority(network, "CAL01_METRIC_GATE_AUTHORITY_ESCALATION")
    if network.get("eligible_for_metric_calibration") is not False or int(network.get("primary_anchor_count", 0)) != 0:
        raise ValueError("CAL01_METRIC_GATE_AUTHORITY_ESCALATION")

    relations = [dict(row) for row in network.get("relations", [])]
    pending = [dict(row) for row in network.get("pending_reviews", [])]
    if int(network.get("relation_count", len(relations))) != len(relations):
        raise ValueError("CAL01_METRIC_GATE_RELATION_COUNT_DRIFT")
    if int(network.get("pending_review_count", len(pending))) != len(pending):
        raise ValueError("CAL01_METRIC_GATE_PENDING_COUNT_DRIFT")

    relation_ids: set[str] = set()
    for row in relations:
        review_id = str(row.get("review_id") or "")
        if not review_id or review_id in relation_ids:
            raise ValueError("CAL01_METRIC_GATE_REVIEW_ID_INVALID")
        relation_ids.add(review_id)
        if str(row.get("orientation") or "") not in SUPPORTED_ORIENTATIONS:
            raise ValueError("CAL01_METRIC_GATE_ORIENTATION_INVALID")
        if float(row.get("pixel_span", 0.0)) <= 0 or float(row.get("validated_value_m", 0.0)) <= 0:
            raise ValueError("CAL01_METRIC_GATE_RELATION_INVALID")
        if float(row.get("px_per_m", 0.0)) <= 0:
            raise ValueError("CAL01_METRIC_GATE_RELATION_INVALID")
        if row.get("eligible_for_metric_calibration") is not False or row.get("primary_anchor_authorized") is not False:
            raise ValueError("CAL01_METRIC_GATE_AUTHORITY_ESCALATION")

    pending_ids: set[str] = set()
    for row in pending:
        review_id = str(row.get("review_id") or "")
        if not review_id or review_id in pending_ids or review_id in relation_ids:
            raise ValueError("CAL01_METRIC_GATE_REVIEW_ID_INVALID")
        pending_ids.add(review_id)
        if str(row.get("orientation") or "") not in SUPPORTED_ORIENTATIONS:
            raise ValueError("CAL01_METRIC_GATE_ORIENTATION_INVALID")
        if row.get("validated_value_m") is not None:
            raise ValueError("CAL01_METRIC_GATE_PENDING_VALUE_PRESENT")
    return relations, pending


def audit_metric_relation_network(network: dict[str, Any]) -> dict[str, Any]:
    relations, _ = _validate_network(network)
    blockers: list[str] = []

    if len(relations) < MIN_RELATIONS:
        blockers.append("RELATION_COUNT_INSUFFICIENT")

    orientation_diagnostics: dict[str, dict[str, Any]] = {}
    orientation_medians: dict[str, float] = {}
    for orientation in ("HORIZONTAL", "VERTICAL"):
        rows = [row for row in relations if row["orientation"] == orientation]
        values = [float(row["px_per_m"]) for row in rows]
        if len(values) < MIN_PER_ORIENTATION:
            blockers.append(f"{orientation}_RELATION_COUNT_INSUFFICIENT")
        if values:
            med = float(median(values))
            max_deviation = max(abs(value - med) / med for value in values)
            orientation_medians[orientation] = med
        else:
            med = None
            max_deviation = None
        orientation_diagnostics[orientation] = {
            "relation_count": len(values),
            "median_px_per_m": med,
            "max_relative_deviation": max_deviation,
        }
        if max_deviation is not None and max_deviation > SCALE_TOLERANCE_RATIO:
            blockers.append(f"{orientation}_SCALE_OUTLIER")

    side_count = len({str(row.get("side") or "") for row in relations if str(row.get("side") or "")})
    if side_count < MIN_SIDES:
        blockers.append("SIDE_COVERAGE_INSUFFICIENT")

    complete_chain_ids = sorted(str(value) for value in network.get("complete_chain_ids", []) if str(value))
    if len(complete_chain_ids) < MIN_COMPLETE_CHAINS:
        blockers.append("COMPLETE_CHAIN_REQUIRED")

    cross_orientation_drift = None
    if set(orientation_medians) == SUPPORTED_ORIENTATIONS:
        horizontal = orientation_medians["HORIZONTAL"]
        vertical = orientation_medians["VERTICAL"]
        reference = (horizontal + vertical) / 2.0
        cross_orientation_drift = abs(horizontal - vertical) / reference
        if cross_orientation_drift > SCALE_TOLERANCE_RATIO:
            blockers.append("ORIENTATION_SCALE_DRIFT")

    blockers = sorted(set(blockers))
    audit: dict[str, Any] = {
        "schema": "CEW_CAL01_METRIC_RELATION_AUDIT_v1",
        "program": "CEW-CAL-01",
        "source": dict(network["source"]),
        "network_digest": network.get("network_digest"),
        "diagnostic_status": (
            "RELATION_NETWORK_DIAGNOSTIC_SUFFICIENT"
            if not blockers
            else "RELATION_NETWORK_DIAGNOSTIC_INSUFFICIENT"
        ),
        "relation_count": len(relations),
        "side_count": side_count,
        "complete_chain_ids": complete_chain_ids,
        "orientation_diagnostics": orientation_diagnostics,
        "cross_orientation_median_drift_ratio": cross_orientation_drift,
        "scale_tolerance_ratio": SCALE_TOLERANCE_RATIO,
        "blockers": blockers,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    audit["audit_digest"] = _canonical_digest(audit)
    return audit


def rank_targeted_human_review(network: dict[str, Any], limit: int = 4) -> list[str]:
    relations, pending = _validate_network(network)
    if limit <= 0:
        return []

    planned_orientation_counts = Counter(str(row["orientation"]) for row in relations)
    planned_sides = {str(row.get("side") or "") for row in relations}
    chain_stats = {
        str(row.get("chain_id") or ""): dict(row)
        for row in network.get("chain_stats", [])
        if str(row.get("chain_id") or "")
    }
    remaining = [dict(row) for row in pending]
    selected: list[str] = []

    while remaining and len(selected) < limit:
        def rank(row: dict[str, Any]) -> tuple[Any, ...]:
            chain_id = str(row["chain_id"])
            stat = chain_stats.get(chain_id, {})
            validated = int(stat.get("validated_interval_count", 0))
            pending_count = int(stat.get("pending_interval_count", 0))
            one_missing_partial_chain = validated > 0 and pending_count == 1
            orientation_count = int(planned_orientation_counts[str(row["orientation"])])
            new_side = str(row["side"]) not in planned_sides
            partial_chain = validated > 0
            return (
                0 if one_missing_partial_chain else 1,
                orientation_count,
                0 if new_side else 1,
                0 if partial_chain else 1,
                str(row["review_id"]),
            )

        chosen = min(remaining, key=rank)
        selected.append(str(chosen["review_id"]))
        planned_orientation_counts[str(chosen["orientation"])] += 1
        planned_sides.add(str(chosen["side"]))
        remaining.remove(chosen)

    return selected


def _triangle_area2(points: list[list[float]]) -> float:
    (x1, y1), (x2, y2), (x3, y3) = points
    return abs((x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1))


def _anchor_readiness(network: dict[str, Any], anchor_inventory: dict[str, Any] | None) -> dict[str, Any]:
    if anchor_inventory is None:
        return {
            "eligible_primary_anchor_count": 0,
            "holdout_anchor_capacity": 0,
            "fit_geometry_nondegenerate": False,
            "blockers": ["PRIMARY_ANCHOR_REQUIRED"],
        }

    if anchor_inventory.get("artifact") != "CEW_CAL01_PRIMARY_ANCHOR_INVENTORY_v1":
        raise ValueError("CAL01_METRIC_GATE_ANCHOR_INVENTORY_SCHEMA_INVALID")
    _require_closed_authority(anchor_inventory, "CAL01_METRIC_GATE_AUTHORITY_ESCALATION")
    source_sha = str(network["source"]["sha256"])
    if anchor_inventory.get("source_version_sha256") != source_sha:
        raise ValueError("CAL01_METRIC_GATE_ANCHOR_SOURCE_DRIFT")

    anchors = [dict(row) for row in anchor_inventory.get("anchors", [])]
    eligible = []
    for row in anchors:
        _require_closed_authority(row, "CAL01_METRIC_GATE_AUTHORITY_ESCALATION")
        if row.get("eligible_for_fit") is not True:
            continue
        if row.get("source_version_sha256") != source_sha:
            raise ValueError("CAL01_METRIC_GATE_ANCHOR_SOURCE_DRIFT")
        source_point = row.get("source_point_px")
        metric_point = row.get("metric_xy_m")
        if not isinstance(source_point, list) or len(source_point) != 2:
            raise ValueError("CAL01_METRIC_GATE_ANCHOR_GEOMETRY_INVALID")
        if not isinstance(metric_point, list) or len(metric_point) != 2:
            raise ValueError("CAL01_METRIC_GATE_ANCHOR_GEOMETRY_INVALID")
        eligible.append(row)

    count = len(eligible)
    geometry_nondegenerate = False
    if count >= FIT_POINT_COUNT:
        for triple in combinations(eligible, FIT_POINT_COUNT):
            source_points = [[float(v) for v in row["source_point_px"]] for row in triple]
            metric_points = [[float(v) for v in row["metric_xy_m"]] for row in triple]
            if _triangle_area2(source_points) > 1e-9 and _triangle_area2(metric_points) > 1e-9:
                geometry_nondegenerate = True
                break

    blockers: list[str] = []
    if count < MIN_ELIGIBLE_ANCHORS:
        blockers.append("PRIMARY_ANCHOR_COUNT_INSUFFICIENT")
    if count >= FIT_POINT_COUNT and not geometry_nondegenerate:
        blockers.append("PRIMARY_ANCHOR_GEOMETRY_DEGENERATE")
    elif count < FIT_POINT_COUNT:
        blockers.append("PRIMARY_ANCHOR_GEOMETRY_INSUFFICIENT")
    holdout_capacity = max(0, count - FIT_POINT_COUNT)
    if holdout_capacity < 1:
        blockers.append("PRIMARY_ANCHOR_HOLDOUT_REQUIRED")

    return {
        "eligible_primary_anchor_count": count,
        "holdout_anchor_capacity": holdout_capacity,
        "fit_geometry_nondegenerate": geometry_nondegenerate,
        "blockers": sorted(set(blockers)),
    }


def evaluate_metric_sufficiency(
    network: dict[str, Any],
    anchor_inventory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    audit = audit_metric_relation_network(network)
    _, pending = _validate_network(network)
    targeted_ids: list[str] = []
    blockers: list[str]
    eligible = False

    if audit["diagnostic_status"] != "RELATION_NETWORK_DIAGNOSTIC_SUFFICIENT":
        blockers = list(audit["blockers"])
        if pending:
            gate_state = "TARGETED_HUMAN_REVIEW"
            next_action = "TARGETED_HUMAN_REVIEW"
            targeted_ids = rank_targeted_human_review(network)
        else:
            gate_state = "INSUFFICIENT"
            next_action = "ACQUIRE_METRIC_RELATIONS"
        anchor_readiness = {
            "eligible_primary_anchor_count": 0,
            "holdout_anchor_capacity": 0,
            "fit_geometry_nondegenerate": False,
            "blockers": [],
        }
    else:
        anchor_readiness = _anchor_readiness(network, anchor_inventory)
        blockers = list(anchor_readiness["blockers"])
        if blockers:
            gate_state = "INSUFFICIENT"
            next_action = "PRIMARY_ANCHOR_DISCOVERY"
        else:
            gate_state = "SUFFICIENT_FOR_CALIBRATION_CANDIDATE"
            next_action = "BUILD_CALIBRATION_CANDIDATE"
            eligible = True

    gate: dict[str, Any] = {
        "schema": "CEW_CAL01_METRIC_SUFFICIENCY_GATE_v1",
        "program": "CEW-CAL-01",
        "source": dict(network["source"]),
        "network_digest": network.get("network_digest"),
        "gate_state": gate_state,
        "blockers": sorted(set(blockers)),
        "next_action": next_action,
        "targeted_human_review_ids": targeted_ids,
        "relation_audit": audit,
        "eligible_primary_anchor_count": int(anchor_readiness["eligible_primary_anchor_count"]),
        "holdout_anchor_capacity": int(anchor_readiness["holdout_anchor_capacity"]),
        "fit_geometry_nondegenerate": bool(anchor_readiness["fit_geometry_nondegenerate"]),
        "eligible_for_metric_calibration": eligible,
        "primary_anchor_authorized": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    gate["gate_digest"] = _canonical_digest(gate)
    return gate


def materialize_metric_sufficiency(review_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    review_dir = Path(review_dir)
    manifest_path = review_dir / "interval-text-review-manifest.json"
    packet_path = review_dir / "external-chain-human-review-packet.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    network = build_metric_relation_network(manifest, packet)
    gate = evaluate_metric_sufficiency(network)
    (review_dir / "metric-relation-network.json").write_text(
        json.dumps(network, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (review_dir / "metric-sufficiency-gate.json").write_text(
        json.dumps(gate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return network, gate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize CEW-CAL-01 metric sufficiency artifacts")
    parser.add_argument("--review-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    network, gate = materialize_metric_sufficiency(args.review_dir)
    print(
        json.dumps(
            {
                "source_id": network["source"]["source_id"],
                "relation_count": network["relation_count"],
                "pending_review_count": network["pending_review_count"],
                "gate_state": gate["gate_state"],
                "next_action": gate["next_action"],
                "network_digest": network["network_digest"],
                "gate_digest": gate["gate_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
