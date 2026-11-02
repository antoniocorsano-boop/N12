from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from experiments.cew_cal01.anchor_inventory import AUTHORITY_CLOSED


EXPECTED_SOURCE_ID = "TAV-02S"
EXPECTED_TOP_INTERVAL_COUNT = 6
EXPECTED_RIGHT_INTERVAL_COUNT = 2


def _canonical_digest(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _require_closed_authority(payload: dict[str, Any]) -> None:
    authority = dict(payload.get("authority") or {})
    if not authority:
        raise ValueError("CAL01_REFERENCE_LATTICE_AUTHORITY_INVALID")
    for key, value in authority.items():
        if key.endswith("_authorized") and value is not False:
            raise ValueError("CAL01_REFERENCE_LATTICE_AUTHORITY_ESCALATION")
    if authority.get("engineering_authority_effect", "NONE") != "NONE":
        raise ValueError("CAL01_REFERENCE_LATTICE_AUTHORITY_ESCALATION")


def _select_chain(
    network: dict[str, Any],
    *,
    side: str,
    chain_id: str,
    orientation: str,
    expected_count: int,
    incomplete_error: str,
) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in network.get("relations", [])
        if row.get("side") == side
        and row.get("chain_id") == chain_id
        and row.get("orientation") == orientation
    ]
    rows.sort(key=lambda row: int(row.get("interval_index", -1)))
    if len(rows) != expected_count:
        raise ValueError(incomplete_error)
    if [int(row.get("interval_index", -1)) for row in rows] != list(range(expected_count)):
        raise ValueError(incomplete_error)

    for row in rows:
        if float(row.get("validated_value_m", 0.0)) <= 0:
            raise ValueError("CAL01_REFERENCE_LATTICE_VALUE_INVALID")
        if float(row.get("pixel_span", 0.0)) <= 0:
            raise ValueError("CAL01_REFERENCE_LATTICE_SPAN_INVALID")
        if row.get("eligible_for_metric_calibration") is not False:
            raise ValueError("CAL01_REFERENCE_LATTICE_AUTHORITY_ESCALATION")
        if row.get("primary_anchor_authorized") is not False:
            raise ValueError("CAL01_REFERENCE_LATTICE_AUTHORITY_ESCALATION")
        a = row.get("source_point_a_px")
        b = row.get("source_point_b_px")
        if not isinstance(a, list) or len(a) != 2 or not isinstance(b, list) or len(b) != 2:
            raise ValueError("CAL01_REFERENCE_LATTICE_GEOMETRY_INVALID")

    for previous, current in zip(rows, rows[1:]):
        previous_b = [float(v) for v in previous["source_point_b_px"]]
        current_a = [float(v) for v in current["source_point_a_px"]]
        if any(abs(a - b) > 1e-6 for a, b in zip(previous_b, current_a)):
            raise ValueError(incomplete_error)

    return rows


def _axis_references(rows: list[dict[str, Any]], axis_index: int) -> list[dict[str, Any]]:
    first = rows[0]
    first_px = float(first["source_point_a_px"][axis_index])
    references = [
        {
            "reference_index": 0,
            "source_position_px": first_px,
            "local_m": 0.0,
            "relation_refs": [],
            "metric_provenance": "RIF",
        }
    ]
    cumulative = 0.0
    relation_refs: list[str] = []
    for index, row in enumerate(rows, start=1):
        cumulative = round(cumulative + float(row["validated_value_m"]), 10)
        relation_refs.append(str(row["review_id"]))
        references.append(
            {
                "reference_index": index,
                "source_position_px": float(row["source_point_b_px"][axis_index]),
                "local_m": cumulative,
                "relation_refs": list(relation_refs),
                "metric_provenance": "RIF",
            }
        )
    return references


def build_reference_lattice(network: dict[str, Any]) -> dict[str, Any]:
    if network.get("schema") != "CEW_CAL01_METRIC_RELATION_NETWORK_v1":
        raise ValueError("CAL01_REFERENCE_LATTICE_NETWORK_SCHEMA_INVALID")
    source = dict(network.get("source") or {})
    if source.get("source_id") != EXPECTED_SOURCE_ID or not source.get("sha256"):
        raise ValueError("CAL01_REFERENCE_LATTICE_SOURCE_INVALID")
    if network.get("eligible_for_metric_calibration") is not False:
        raise ValueError("CAL01_REFERENCE_LATTICE_AUTHORITY_ESCALATION")
    if int(network.get("primary_anchor_count", 0)) != 0:
        raise ValueError("CAL01_REFERENCE_LATTICE_AUTHORITY_ESCALATION")
    _require_closed_authority(network)

    pending = [dict(row) for row in network.get("pending_reviews", [])]
    if any(row.get("validated_value_m") is not None for row in pending):
        raise ValueError("CAL01_REFERENCE_LATTICE_PENDING_VALUE_PRESENT")

    top = _select_chain(
        network,
        side="TOP",
        chain_id="TOP:R1",
        orientation="HORIZONTAL",
        expected_count=EXPECTED_TOP_INTERVAL_COUNT,
        incomplete_error="CAL01_REFERENCE_LATTICE_TOP_CHAIN_INCOMPLETE",
    )
    right = _select_chain(
        network,
        side="RIGHT",
        chain_id="RIGHT:R1",
        orientation="VERTICAL",
        expected_count=EXPECTED_RIGHT_INTERVAL_COUNT,
        incomplete_error="CAL01_REFERENCE_LATTICE_RIGHT_CHAIN_INCOMPLETE",
    )

    x_references = _axis_references(top, 0)
    y_references = _axis_references(right, 1)

    lattice_nodes: list[dict[str, Any]] = []
    for x_ref in x_references:
        for y_ref in y_references:
            x_index = int(x_ref["reference_index"])
            y_index = int(y_ref["reference_index"])
            lattice_nodes.append(
                {
                    "lattice_node_id": f"TAV-02S:LATTICE:X{x_index}:Y{y_index}",
                    "x_reference_index": x_index,
                    "y_reference_index": y_index,
                    "source_point_normalized_px": [
                        float(x_ref["source_position_px"]),
                        float(y_ref["source_position_px"]),
                    ],
                    "local_metric_xy_m": [
                        float(x_ref["local_m"]),
                        float(y_ref["local_m"]),
                    ],
                    "x_relation_refs": list(x_ref["relation_refs"]),
                    "y_relation_refs": list(y_ref["relation_refs"]),
                    "metric_provenance": {"x": "RIF", "y": "RIF"},
                    "fit_eligible": False,
                    "primary_anchor_authorized": False,
                }
            )

    lattice: dict[str, Any] = {
        "schema": "CEW_CAL01_TAV02_REFERENCE_LATTICE_v1",
        "program": "CEW-CAL-01",
        "source": source,
        "metric_network_digest": network.get("network_digest"),
        "coordinate_frame": "LOCAL_RELATIVE_METRIC",
        "reference_origin": {
            "source_point_normalized_px": [
                float(x_references[0]["source_position_px"]),
                float(y_references[0]["source_position_px"]),
            ],
            "local_xy_m": [0.0, 0.0],
            "absolute_origin_authorized": False,
        },
        "x_reference_count": len(x_references),
        "y_reference_count": len(y_references),
        "lattice_node_count": len(lattice_nodes),
        "x_references": x_references,
        "y_references": y_references,
        "lattice_nodes": lattice_nodes,
        "absolute_origin_authorized": False,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }
    lattice["lattice_digest"] = _canonical_digest(lattice)
    return lattice


def materialize_reference_lattice(review_dir: Path) -> dict[str, Any]:
    review_dir = Path(review_dir)
    network_path = review_dir / "metric-relation-network.json"
    network = json.loads(network_path.read_text(encoding="utf-8"))
    lattice = build_reference_lattice(network)
    (review_dir / "tav02-reference-lattice.json").write_text(
        json.dumps(lattice, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return lattice


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize CEW-CAL-01 TAV-02S local reference lattice")
    parser.add_argument("--review-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    lattice = materialize_reference_lattice(args.review_dir)
    print(
        json.dumps(
            {
                "source_id": lattice["source"]["source_id"],
                "x_reference_count": lattice["x_reference_count"],
                "y_reference_count": lattice["y_reference_count"],
                "lattice_node_count": lattice["lattice_node_count"],
                "lattice_digest": lattice["lattice_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
