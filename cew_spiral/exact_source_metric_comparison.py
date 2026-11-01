from __future__ import annotations

from collections import Counter
import re
import statistics
from typing import Any

from cew_spiral.metric_registration_witness import (
    build_metric_registration_witness,
    compare_witness_to_historical_supports,
)


_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _validate_commit(value: str, error: str) -> None:
    if not isinstance(value, str) or not _HEX40.fullmatch(value):
        raise ValueError(error)


def _select_tav05_registration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("sheet_id") == "TAV-05S"
        and row.get("level_id") == "G4"
    ]
    if len(selected) != 1:
        raise ValueError("TAV05_REGISTRATION_REQUIRED")
    return selected[0]


def build_metric_comparison_bundle(
    *,
    structural_bridge: dict[str, Any],
    registration_rows: list[dict[str, Any]],
    historical_supports: list[dict[str, Any]],
    registration_commit: str,
    comparator_commit: str,
) -> dict[str, Any]:
    """Compare current source-bound column candidates with historical M0-G positions.

    Both the affine registration and the M0-G support set are treated only as
    historical witnesses. Distances are reported without a capture radius,
    acceptance threshold, identity binding, or canonical geometry effect.
    """

    _validate_commit(registration_commit, "REGISTRATION_COMMIT_INVALID")
    _validate_commit(comparator_commit, "COMPARATOR_COMMIT_INVALID")
    if not isinstance(registration_rows, list):
        raise ValueError("REGISTRATION_ROWS_REQUIRED")
    if not isinstance(historical_supports, list):
        raise ValueError("HISTORICAL_SUPPORTS_REQUIRED")

    registration = _select_tav05_registration(registration_rows)
    witness = build_metric_registration_witness(
        structural_bridge=structural_bridge,
        registration=registration,
        registration_commit=registration_commit,
        registration_provenance="HISTORICAL_NONREPLAYABLE_WITNESS",
    )
    comparison = compare_witness_to_historical_supports(
        witness=witness,
        supports=historical_supports,
        level_id="G4",
    )

    comparisons = list(comparison["comparisons"])
    distances = [float(row["nearest_distance_m"]) for row in comparisons]
    if len(distances) != witness["projection_count"]:
        raise ValueError("METRIC_COMPARISON_COUNT_DRIFT")
    nearest_counts = Counter(str(row["nearest_historical_node_id"]) for row in comparisons)

    summary = {
        "distance_count": len(distances),
        "min_distance_m": min(distances) if distances else None,
        "median_distance_m": statistics.median(distances) if distances else None,
        "max_distance_m": max(distances) if distances else None,
        "unique_nearest_historical_node_count": len(nearest_counts),
        "nearest_historical_node_reuse": [
            {"node_id": node_id, "comparison_count": count}
            for node_id, count in sorted(nearest_counts.items())
            if count > 1
        ],
    }

    return {
        "schema": "CEW_SPIRAL_EXACT_SOURCE_METRIC_COMPARISON_v1",
        "registration_commit": registration_commit,
        "registration_provenance": "HISTORICAL_NONREPLAYABLE_WITNESS",
        "comparator_commit": comparator_commit,
        "comparator_provenance": "HISTORICAL_NONCANONICAL_COMPARATOR",
        "projection_count": witness["projection_count"],
        "comparison_count": comparison["comparison_count"],
        "comparisons": comparisons,
        "summary": summary,
        "comparison_semantics": "DISTANCE_AUDIT_ONLY_NO_BINDING_NO_THRESHOLD",
        "authority": {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }
