from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

from experiments.cew_cal01.numeric_role import (
    ROLE_LINEAR_DIMENSION,
    ROLE_SECTION_MEASURE,
    ROLE_UNRESOLVED,
)
from experiments.cew_cal01.semantic_replay import refine_numeric_proposal


AUTHORITY_CLOSED = {
    "primary_anchor_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def build_semantic_inventory(
    proposals: Iterable[dict[str, Any]],
    local_contexts: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build a deterministic document-role inventory from bounded local evidence.

    This function classifies document role only. It deliberately does not create
    PrimaryMetricAnchor records, metric coordinates, canonical geometry, or any
    M0-G/engineering authority.
    """

    proposal_rows = [dict(item) for item in proposals]
    seen_ids: set[str] = set()
    refined_rows: list[dict[str, Any]] = []

    for proposal in sorted(proposal_rows, key=lambda item: str(item.get("proposal_id") or "")):
        proposal_id = str(proposal.get("proposal_id") or "").strip()
        if not proposal_id:
            raise ValueError("CAL01_SEMANTIC_PROPOSAL_ID_REQUIRED")
        if proposal_id in seen_ids:
            raise ValueError("CAL01_SEMANTIC_PROPOSAL_ID_DUPLICATE")
        seen_ids.add(proposal_id)

        context = local_contexts.get(proposal_id)
        if context is None:
            raise ValueError(f"CAL01_SEMANTIC_CONTEXT_MISSING:{proposal_id}")

        refined = refine_numeric_proposal(
            proposal,
            local_readings=context.get("local_readings", []),
            line_segments=context.get("line_segments", []),
            nearby_closed_frame=bool(context.get("nearby_closed_frame", False)),
        )
        refined_rows.append(refined)

    role_counts = {
        ROLE_LINEAR_DIMENSION: 0,
        ROLE_SECTION_MEASURE: 0,
        ROLE_UNRESOLVED: 0,
    }
    for row in refined_rows:
        role = row.get("role")
        if role not in role_counts:
            raise ValueError(f"CAL01_SEMANTIC_ROLE_UNSUPPORTED:{role}")
        role_counts[role] += 1
        if row.get("primary_anchor_authorized") is not False:
            raise ValueError("CAL01_SEMANTIC_AUTHORITY_DRIFT")
        if row.get("canonical_geometry_authorized") is not False:
            raise ValueError("CAL01_SEMANTIC_AUTHORITY_DRIFT")
        if row.get("canonical_write_authorized") is not False:
            raise ValueError("CAL01_SEMANTIC_AUTHORITY_DRIFT")
        if row.get("m0g_authorized") is not False:
            raise ValueError("CAL01_SEMANTIC_AUTHORITY_DRIFT")

    result = {
        "schema": "CEW_CAL01_SEMANTIC_ROLE_INVENTORY_v1",
        "program": "CEW-CAL-01",
        "proposal_count": len(refined_rows),
        "role_counts": role_counts,
        "primary_anchor_count": 0,
        "rows": refined_rows,
        "authority": dict(AUTHORITY_CLOSED),
    }
    result["semantic_inventory_digest"] = _canonical_digest(result)
    return result
