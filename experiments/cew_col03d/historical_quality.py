from __future__ import annotations

from collections import Counter
from typing import Any


_COLUMN_BLOCKER = "associazione al singolo pilastro non ancora dimostrata"
_BEAM_BLOCKER = "associazione proposta dalla sola morfologia; richiede richiamo/posizione inequivoca"


def audit_historical_semantics(parsed_members: list[dict[str, Any]]) -> dict[str, Any]:
    state_counts: Counter[str] = Counter()
    row_counts: dict[str, int] = {}
    column_not_demonstrated = 0
    beam_geometry_only = 0

    for parsed in sorted(parsed_members, key=lambda row: str(row.get("artifact_name") or "")):
        name = str(parsed.get("artifact_name") or "")
        if parsed.get("authority") != "HISTORICAL_DERIVED_EVIDENCE" or parsed.get("promotion_authorized") is not False:
            raise ValueError(f"HISTORICAL_EVIDENCE_AUTHORITY_DRIFT:{name}")
        records = list(parsed.get("records") or [])
        row_counts[name] = len(records)
        for record in records:
            values = dict(record.get("values") or {})
            for key, value in values.items():
                if "stato" in str(key).lower() and value:
                    state_counts[str(value)] += 1
            note = str(values.get("nota") or "").casefold()
            if _COLUMN_BLOCKER in note:
                column_not_demonstrated += 1
            if _BEAM_BLOCKER in note:
                beam_geometry_only += 1

    blocking_findings: list[str] = []
    if column_not_demonstrated:
        blocking_findings.append("COLUMN_ASSOCIATION_NOT_DEMONSTRATED")
    if beam_geometry_only:
        blocking_findings.append("BEAM_ASSOCIATION_GEOMETRY_ONLY")

    return {
        "status": "EVIDENCE_ONLY",
        "row_counts": dict(sorted(row_counts.items())),
        "historical_state_counts": dict(sorted(state_counts.items())),
        "column_association_not_demonstrated_count": column_not_demonstrated,
        "beam_geometry_only_association_count": beam_geometry_only,
        "blocking_findings": sorted(blocking_findings),
        "identity_promotion_authorized": False,
        "structural_identity_authorized": False,
        "section_assignment_authorized": False,
        "vertical_chain_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
    }
