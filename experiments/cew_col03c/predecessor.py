from __future__ import annotations

from copy import deepcopy
from typing import Any


QUALIFIED_COL03B_SHA = "cfd9382b703d0a974daf63c23dc2b6d3d81eadad"

CLOSED_AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "vertical_chain_assignment_authorized",
    "structural_identity_authorized",
    "canonical_node_assignment_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)


def _assert_authority_closed(payload: dict[str, Any], *, label: str) -> None:
    for key in CLOSED_AUTHORITY_KEYS:
        if payload.get(key) is True:
            raise ValueError(f"{label} authority drift: {key}")


def validate_col03b_predecessor(
    *,
    ledger: dict[str, Any],
    reconciliation: dict[str, Any],
    closure: dict[str, Any],
    expected_sha: str,
) -> list[dict[str, Any]]:
    if expected_sha != QUALIFIED_COL03B_SHA:
        raise ValueError("COL-03B predecessor SHA drift")

    occurrences = ledger.get("occurrences") if isinstance(ledger, dict) else None
    if not isinstance(occurrences, list) or ledger.get("occurrence_count") != 22 or len(occurrences) != 22:
        raise ValueError("COL-03B occurrence set drift")
    ordered = sorted((deepcopy(row) for row in occurrences), key=lambda row: str(row.get("occurrence_id") or ""))
    expected_ids = [f"COL-OCC-{index:04d}" for index in range(1, 23)]
    if [str(row.get("occurrence_id") or "") for row in ordered] != expected_ids:
        raise ValueError("COL-03B occurrence ID drift")

    if closure.get("documentary_identity_evidence_collection_complete") is not True:
        raise ValueError("COL-03B documentary evidence collection is not complete")
    if closure.get("all_occurrences_identity_resolved") is not False:
        raise ValueError("COL-03B identity state drift: predecessor must remain unresolved")
    if closure.get("blocking_reasons") not in ([], None):
        raise ValueError("COL-03B predecessor has blocking reasons")

    closure_authority = closure.get("authority")
    if not isinstance(closure_authority, dict):
        raise ValueError("COL-03B closure authority missing")
    _assert_authority_closed(closure_authority, label="COL-03B closure")
    for row in ordered:
        _assert_authority_closed(row, label=str(row.get("occurrence_id") or "occurrence"))

    if reconciliation.get("occurrence_count") != 22:
        raise ValueError("COL-03B reconciliation occurrence count drift")
    if reconciliation.get("historical_artifacts_materialized") is not False:
        raise ValueError("COL-03B historical materialization boundary drift")
    if reconciliation.get("historical_inventory_ref") != "archive/ARTEFATTI_STORICI.md":
        raise ValueError("COL-03B historical inventory provenance drift")
    if reconciliation.get("historical_gap_reason") != "INVENTORY_PRESENT_HISTORICAL_DXF_CSV_NOT_MATERIALIZED_ON_QUALIFIED_BRANCH":
        raise ValueError("COL-03B historical gap semantics drift")

    return ordered
