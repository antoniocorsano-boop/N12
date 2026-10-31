from __future__ import annotations

from copy import deepcopy
from typing import Any


QUALIFIED_COL03A_SHA = "0d4a43cf02eadd2ab6f4b2641888395586c08a98"
COL03A_INTERNAL_COL02_BASE_SHA = "0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4"

_CLOSED_AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "structural_identity_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)

_CHANNEL_KEYS = (
    "internal_text_evidence",
    "intersecting_text_evidence",
    "nearby_text_evidence",
    "high_resolution_read_evidence",
    "callout_evidence",
    "local_topology_evidence",
    "cross_document_evidence",
)


def _assert_closed_authority(payload: dict[str, Any], label: str) -> None:
    authority = payload.get("authority")
    if not isinstance(authority, dict):
        raise ValueError(f"{label} authority missing")
    drift = [key for key in _CLOSED_AUTHORITY_KEYS if authority.get(key) is not False]
    if drift:
        raise ValueError(f"{label} authority drift: {','.join(drift)}")


def validate_col03a_predecessor(
    *,
    ledger: dict[str, Any],
    reconciliation: dict[str, Any],
    closure: dict[str, Any],
    expected_sha: str,
) -> list[dict[str, Any]]:
    if expected_sha != QUALIFIED_COL03A_SHA:
        raise ValueError("unexpected COL-03A qualified predecessor SHA")
    if closure.get("qualified_base_sha") not in (None, COL03A_INTERNAL_COL02_BASE_SHA):
        raise ValueError("COL-03A internal COL-02 base drift")
    if closure.get("occurrence_ledger_complete") is not True:
        raise ValueError("COL-03A occurrence ledger is not complete")
    if closure.get("blocking_reasons") not in (None, []):
        raise ValueError("COL-03A closure has blocking reasons")
    if reconciliation.get("final_occurrence_count") != 22:
        raise ValueError("COL-03A reconciliation occurrence count drift")
    if reconciliation.get("conflict_count") != 0:
        raise ValueError("COL-03A reconciliation conflict drift")
    if reconciliation.get("missing_evidence_ids") not in (None, []):
        raise ValueError("COL-03A reconciliation missing evidence")
    if reconciliation.get("orphan_occurrence_ids") not in (None, []):
        raise ValueError("COL-03A reconciliation orphan occurrence")
    if reconciliation.get("bidirectional_closed_set_complete") is not True:
        raise ValueError("COL-03A reconciliation is not bidirectionally complete")

    _assert_closed_authority(ledger, "ledger")
    _assert_closed_authority(closure, "closure")

    occurrences = ledger.get("occurrences")
    if ledger.get("occurrence_count") != 22 or not isinstance(occurrences, list) or len(occurrences) != 22:
        raise ValueError("COL-03A occurrence count drift")

    expected_ids = [f"COL-OCC-{index:04d}" for index in range(1, 23)]
    actual_ids = [str(row.get("occurrence_id") or "") for row in occurrences if isinstance(row, dict)]
    if actual_ids != expected_ids:
        raise ValueError("COL-03A occurrence ID drift")

    for row in occurrences:
        if row.get("exact_source_reconstructible") is not True:
            raise ValueError(f"COL-03A source reconstruction drift: {row.get('occurrence_id')}")
        if row.get("lineage_complete") is not True:
            raise ValueError(f"COL-03A lineage drift: {row.get('occurrence_id')}")
        if row.get("conflict_state") != "NONE":
            raise ValueError(f"COL-03A occurrence conflict drift: {row.get('occurrence_id')}")
        if row.get("canonical_write_authorized") is not False:
            raise ValueError(f"COL-03A occurrence authority drift: {row.get('occurrence_id')}")
        if row.get("g2c_promotion_authorized") is not False:
            raise ValueError(f"COL-03A occurrence authority drift: {row.get('occurrence_id')}")
        if row.get("g3_promotion_authorized") is not False:
            raise ValueError(f"COL-03A occurrence authority drift: {row.get('occurrence_id')}")

    collapsed = [row for row in occurrences if row.get("dedup_state") == "HUMAN_EQUIVALENCE_COLLAPSED"]
    decisions = {
        tuple(sorted(row.get("source_proposal_ids") or [])): tuple(row.get("human_equivalence_decision_ids") or [])
        for row in collapsed
    }
    if decisions != {
        ("COL02-FP-0248", "COL02-FP-0331"): ("A",),
        ("COL02-FP-0073", "COL02-FP-0538"): ("B",),
    }:
        raise ValueError("COL-03A human equivalence lineage drift")

    return deepcopy(occurrences)


def build_evidence_bundle_skeleton(
    occurrence: dict[str, Any],
    *,
    col03a_ledger_digest: str,
) -> dict[str, Any]:
    occurrence_id = str(occurrence.get("occurrence_id") or "")
    if not occurrence_id.startswith("COL-OCC-"):
        raise ValueError("invalid COL-03A occurrence identity")
    if occurrence.get("exact_source_reconstructible") is not True or occurrence.get("lineage_complete") is not True:
        raise ValueError("occurrence is not eligible for COL-03B evidence collection")

    bundle = {
        "occurrence_id": occurrence_id,
        "col03a_ledger_digest": str(col03a_ledger_digest),
        "source_version_id": occurrence.get("source_version_id"),
        "source_path": occurrence.get("source_path"),
        "source_sha256": occurrence.get("source_sha256"),
        "page_id": occurrence.get("page_id"),
        "page_index": occurrence.get("page_index"),
        "page_transform_id": occurrence.get("page_transform_id"),
        "primary_graphical_representation": deepcopy(occurrence.get("primary_graphical_representation")),
        "hypotheses": [],
        "documentary_evidence_state": "NOT_EVALUATED",
        "documentary_identity_resolution_state": "UNRESOLVED",
        "conflict_state": "NONE",
        "missing_channels": list(_CHANNEL_KEYS),
        "exact_source_reconstructible": True,
        "lineage_complete": True,
        "support_identity_authorized": False,
        "text_identity_binding_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
        "notes": [],
    }
    for key in _CHANNEL_KEYS:
        bundle[key] = []
    return bundle
