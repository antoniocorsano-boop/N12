from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


QUALIFIED_COL03B_SHA = "cfd9382b703d0a974daf63c23dc2b6d3d81eadad"
EXPECTED_OCCURRENCE_IDS = tuple(f"COL-OCC-{index:04d}" for index in range(1, 23))
EXPECTED_DOCUMENTARY_CANDIDATES = {
    "COL-OCC-0001": ["4"],
    "COL-OCC-0015": ["30"],
}

_AUTHORITY_KEYS = (
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
_COL03C_AUTHORITY_KEYS = _AUTHORITY_KEYS + (
    "vertical_chain_assignment_authorized",
    "canonical_node_assignment_authorized",
)


def _load_json(root: Path, name: str) -> dict[str, Any]:
    path = root / name
    if not path.is_file():
        raise ValueError(f"COL03E_PREDECESSOR_FILE_MISSING:{name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"COL03E_PREDECESSOR_FILE_INVALID:{name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"COL03E_PREDECESSOR_FILE_INVALID:{name}")
    return value


def _assert_authority_closed(row: dict[str, Any], keys: tuple[str, ...], context: str) -> None:
    for key in keys:
        if row.get(key) is not False:
            raise ValueError(f"COL03E_AUTHORITY_DRIFT:{context}:{key}")


def _assert_occurrence_set(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows = ledger.get("occurrences")
    if not isinstance(rows, list):
        raise ValueError("COL03E_OCCURRENCE_SET_DRIFT")
    ids = [str(row.get("occurrence_id") or "") for row in rows if isinstance(row, dict)]
    if (
        ledger.get("occurrence_count") != len(EXPECTED_OCCURRENCE_IDS)
        or len(rows) != len(EXPECTED_OCCURRENCE_IDS)
        or ids != list(EXPECTED_OCCURRENCE_IDS)
    ):
        raise ValueError("COL03E_OCCURRENCE_SET_DRIFT")
    return rows


def load_qualified_predecessor_evidence(
    col03b_root: str | Path,
    col03c_root: str | Path,
) -> dict[str, Any]:
    """Load exact-source COL-03B/C outputs and fail closed on predecessor drift."""

    b_root = Path(col03b_root)
    c_root = Path(col03c_root)
    b_ledger = _load_json(b_root, "documentary-identity-evidence-ledger.json")
    b_closure = _load_json(b_root, "documentary-identity-evidence-closure.json")
    c_ledger = _load_json(c_root, "cross-document-evidence-ledger.json")
    c_closure = _load_json(c_root, "cross-document-evidence-closure.json")
    c_source = _load_json(c_root, "source-materialization-manifest.json")

    b_rows = _assert_occurrence_set(b_ledger)
    c_rows = _assert_occurrence_set(c_ledger)
    if [row["occurrence_id"] for row in b_rows] != [row["occurrence_id"] for row in c_rows]:
        raise ValueError("COL03E_OCCURRENCE_SET_DRIFT")

    if (
        b_closure.get("occurrence_count") != 22
        or b_closure.get("documentary_identity_evidence_collection_complete") is not True
        or b_closure.get("all_occurrences_identity_resolved") is not False
        or b_closure.get("blocking_reasons") != []
    ):
        raise ValueError("COL03E_PREDECESSOR_STATE_DRIFT")

    if (
        c_source.get("qualified_col03b_sha") != QUALIFIED_COL03B_SHA
        or c_closure.get("qualified_col03b_sha") != QUALIFIED_COL03B_SHA
    ):
        raise ValueError("COL03E_COL03B_LINEAGE_DRIFT")
    if (
        c_closure.get("occurrence_count") != 22
        or c_closure.get("available_cross_document_evidence_evaluated") is not True
        or c_closure.get("all_occurrences_cross_document_resolved") is not False
        or c_closure.get("blocking_reasons") != []
    ):
        raise ValueError("COL03E_PREDECESSOR_STATE_DRIFT")

    b_authority = b_closure.get("authority")
    c_authority = c_closure.get("authority")
    if not isinstance(b_authority, dict) or not isinstance(c_authority, dict):
        raise ValueError("COL03E_AUTHORITY_DRIFT:closure")
    _assert_authority_closed(b_authority, _AUTHORITY_KEYS, "col03b-closure")
    _assert_authority_closed(c_authority, _COL03C_AUTHORITY_KEYS, "col03c-closure")

    documentary_candidates: dict[str, list[str]] = {}
    for row in b_rows:
        _assert_authority_closed(row, _AUTHORITY_KEYS, str(row["occurrence_id"]))
        hypotheses = row.get("hypotheses")
        if not isinstance(hypotheses, list):
            raise ValueError("COL03E_PREDECESSOR_STATE_DRIFT")
        values: list[str] = []
        for hypothesis in hypotheses:
            if not isinstance(hypothesis, dict) or hypothesis.get("promotion_authorized") is not False:
                raise ValueError("COL03E_AUTHORITY_DRIFT:documentary-hypothesis")
            value = str(hypothesis.get("candidate_value") or "")
            if not value:
                raise ValueError("COL03E_PREDECESSOR_STATE_DRIFT")
            values.append(value)
        if values:
            documentary_candidates[str(row["occurrence_id"])] = sorted(values)

    if documentary_candidates != EXPECTED_DOCUMENTARY_CANDIDATES:
        raise ValueError("COL03E_PREDECESSOR_STATE_DRIFT")

    cross_document_candidate_count = 0
    for row in c_rows:
        _assert_authority_closed(row, _COL03C_AUTHORITY_KEYS, str(row["occurrence_id"]))
        hypotheses = row.get("hypotheses")
        if not isinstance(hypotheses, list):
            raise ValueError("COL03E_PREDECESSOR_STATE_DRIFT")
        cross_document_candidate_count += len(hypotheses)
        if (
            row.get("tav07_match_state") != "EVALUATED_NO_MATCH"
            or hypotheses
            or row.get("cross_document_identity_resolved") is not False
        ):
            raise ValueError("COL03E_PREDECESSOR_STATE_DRIFT")

    return {
        "predecessor_evidence_validated": True,
        "occurrence_ids": list(EXPECTED_OCCURRENCE_IDS),
        "documentary_candidates": documentary_candidates,
        "cross_document_candidate_count": cross_document_candidate_count,
        "col03b_ledger": deepcopy(b_ledger),
        "col03b_closure": deepcopy(b_closure),
        "col03c_ledger": deepcopy(c_ledger),
        "col03c_closure": deepcopy(c_closure),
        "col03c_source": deepcopy(c_source),
    }
