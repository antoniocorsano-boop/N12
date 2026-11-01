from __future__ import annotations

import hashlib
import json
from typing import Any


EXPECTED_OCCURRENCE_IDS = tuple(f"COL-OCC-{index:04d}" for index in range(1, 23))

AUTHORITY_KEYS = (
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


def classify_review_readiness(
    *,
    conflict_state: str,
    candidate_count: int,
    match_state: str,
    provenance_complete: bool,
    historical_semantic_blocked: bool,
) -> str:
    """Return the single fail-closed COL-03E review-readiness state."""

    if conflict_state not in {"", "NONE"}:
        return "CONTRADICTED"
    if candidate_count > 1 or match_state in {"AMBIGUOUS", "DUPLICATE", "MULTIPLE_CANDIDATES"}:
        return "AMBIGUOUS"
    if historical_semantic_blocked:
        return "BLOCKED_BY_HISTORICAL_SEMANTICS"
    if candidate_count != 1 or match_state not in {"SINGLE_CANDIDATE", "MATCHED"} or not provenance_complete:
        return "INSUFFICIENT_EVIDENCE"
    return "READY_FOR_HUMAN_REVIEW"


def _rows_by_occurrence(ledger: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    rows = ledger.get("occurrences")
    if not isinstance(rows, list):
        raise ValueError(f"COL03E_{label}_OCCURRENCE_SET_INVALID")
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"COL03E_{label}_OCCURRENCE_SET_INVALID")
        occurrence_id = str(row.get("occurrence_id") or "")
        if not occurrence_id or occurrence_id in indexed:
            raise ValueError(f"COL03E_{label}_OCCURRENCE_SET_INVALID")
        indexed[occurrence_id] = row
    if set(indexed) != set(EXPECTED_OCCURRENCE_IDS):
        raise ValueError("COL03E_OCCURRENCE_SET_DRIFT")
    return indexed


def _candidate_values(row: dict[str, Any]) -> list[str]:
    hypotheses = row.get("hypotheses") or []
    if not isinstance(hypotheses, list):
        raise ValueError("COL03E_HYPOTHESIS_SURFACE_INVALID")
    values: list[str] = []
    for hypothesis in hypotheses:
        if not isinstance(hypothesis, dict):
            raise ValueError("COL03E_HYPOTHESIS_SURFACE_INVALID")
        value = str(hypothesis.get("candidate_value") or "")
        if value:
            values.append(value)
    return sorted(set(values))


def _historical_context(historical_quality: dict[str, Any]) -> dict[str, Any]:
    csv_evidence = historical_quality.get("csv_evidence") or []
    if not isinstance(csv_evidence, list):
        raise ValueError("COL03E_HISTORICAL_QUALITY_INVALID")

    by_name = {
        str(row.get("artifact_name")): row
        for row in csv_evidence
        if isinstance(row, dict) and row.get("artifact_name")
    }
    association = by_name.get("ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv", {})
    matrix = by_name.get("MATRICE_PILASTRI_27x5_v22.csv", {})

    association_records = association.get("records") or []
    if not isinstance(association_records, list):
        raise ValueError("COL03E_HISTORICAL_QUALITY_INVALID")
    non_demonstrated = 0
    for record in association_records:
        if not isinstance(record, dict):
            continue
        values = record.get("values")
        if not isinstance(values, dict):
            continue
        note = str(values.get("nota") or "").casefold()
        if "associazione al singolo pilastro non ancora dimostrata" in note:
            non_demonstrated += 1

    blocking_findings = historical_quality.get("blocking_findings") or []
    if not isinstance(blocking_findings, list):
        raise ValueError("COL03E_HISTORICAL_QUALITY_INVALID")

    return {
        "bridge_state": "UNBOUND",
        "identity_use_authorized": False,
        "column_association_artifact": "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
        "column_association_row_count": int(association.get("row_count") or 0),
        "column_association_source_sha256": association.get("source_sha256"),
        "association_not_demonstrated_row_count": non_demonstrated,
        "historical_matrix_artifact": "MATRICE_PILASTRI_27x5_v22.csv",
        "historical_matrix_row_count": int(matrix.get("row_count") or 0),
        "historical_matrix_source_sha256": matrix.get("source_sha256"),
        "blocking_findings": sorted(str(value) for value in blocking_findings),
    }


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_adjudication_dossiers(
    *,
    col03b_ledger: dict[str, Any],
    col03c_ledger: dict[str, Any],
    historical_quality: dict[str, Any],
    predecessor_sha: str,
) -> list[dict[str, Any]]:
    """Build deterministic, evidence-only COL-03E dossiers for the 22 governed occurrences."""

    if not predecessor_sha:
        raise ValueError("COL03E_PREDECESSOR_SHA_REQUIRED")

    col03b = _rows_by_occurrence(col03b_ledger, "COL03B")
    col03c = _rows_by_occurrence(col03c_ledger, "COL03C")
    historical_context = _historical_context(historical_quality)
    dossiers: list[dict[str, Any]] = []

    for occurrence_id in EXPECTED_OCCURRENCE_IDS:
        b_row = col03b[occurrence_id]
        c_row = col03c[occurrence_id]
        documentary_candidates = _candidate_values(b_row)
        cross_document_candidates = _candidate_values(c_row)

        conflict_states = {
            str(value)
            for value in (b_row.get("conflict_state"), c_row.get("conflict_state"))
            if value not in (None, "", "NONE")
        }
        conflict_state = sorted(conflict_states)[0] if conflict_states else "NONE"
        match_state = str(c_row.get("tav07_match_state") or "")
        provenance_complete = c_row.get("tav07_source_state") == "MATERIALIZED_VERIFIED"

        # Historical rows are intentionally unbound in COL-03E. They cannot block or
        # support one specific occurrence unless a governed bridge exists upstream.
        historical_semantic_blocked = False
        readiness = classify_review_readiness(
            conflict_state=conflict_state,
            candidate_count=len(cross_document_candidates),
            match_state=match_state,
            provenance_complete=provenance_complete,
            historical_semantic_blocked=historical_semantic_blocked,
        )

        missing_evidence: list[str] = []
        if not documentary_candidates:
            missing_evidence.append("NO_DOCUMENTARY_IDENTITY_CANDIDATE")
        if not cross_document_candidates or match_state == "EVALUATED_NO_MATCH":
            missing_evidence.append("NO_TAV07_CROSS_DOCUMENT_MATCH")
        if historical_context["bridge_state"] == "UNBOUND":
            missing_evidence.append("NO_GOVERNED_HISTORICAL_BRIDGE")
        if not provenance_complete:
            missing_evidence.append("TAV07_PROVENANCE_INCOMPLETE")

        payload: dict[str, Any] = {
            "schema": "CEW_COL03E_IDENTITY_ADJUDICATION_DOSSIER_v1",
            "occurrence_id": occurrence_id,
            "predecessor_sha": predecessor_sha,
            "documentary_candidates": documentary_candidates,
            "documentary_hypothesis_states": sorted(
                str(hypothesis.get("state") or "")
                for hypothesis in (b_row.get("hypotheses") or [])
                if isinstance(hypothesis, dict)
            ),
            "cross_document_candidates": cross_document_candidates,
            "cross_document_match_state": match_state,
            "cross_document_identity_resolved": c_row.get("cross_document_identity_resolved") is True,
            "conflict_state": conflict_state,
            "unbound_historical_context": dict(historical_context),
            "occurrence_specific_historical_ids": [],
            "missing_evidence": sorted(set(missing_evidence)),
            "review_readiness_state": readiness,
            "human_receipt_required_for_promotion": True,
            "identity_promoted": False,
        }
        for key in AUTHORITY_KEYS:
            payload[key] = False
        payload["dossier_digest"] = _digest_payload(payload)
        dossiers.append(payload)

    return dossiers
