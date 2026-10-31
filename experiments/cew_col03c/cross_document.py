from __future__ import annotations

from copy import deepcopy
import hashlib
import json
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


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _closed_authority() -> dict[str, bool]:
    return {key: False for key in CLOSED_AUTHORITY_KEYS}


def _normalize_label(value: Any) -> str:
    return " ".join(str(value or "").split())


def _historical_gaps(historical_artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for artifact in historical_artifacts:
        if not isinstance(artifact, dict):
            raise ValueError("historical artifact must be a mapping")
        state = str(artifact.get("materialization_state") or "")
        if state == "MATERIALIZED_VERIFIED":
            continue
        gap = {
            "artifact_name": str(artifact.get("artifact_name") or ""),
            "materialization_state": state or "NOT_FOUND",
            "bytes_available": artifact.get("bytes_available") is True,
            "row_level_evidence_usable": artifact.get("row_level_evidence_usable") is True,
            "authority": str(artifact.get("authority") or "REFERENCE_ONLY"),
            "inventory_source_ref": artifact.get("inventory_source_ref"),
            "gap_class": "HISTORICAL_RECOVERY_GAP",
        }
        if not gap["artifact_name"]:
            raise ValueError("historical artifact name missing")
        gaps.append(gap)
    return sorted(gaps, key=lambda row: row["artifact_name"])


def _predecessor_label_candidates(occurrence: dict[str, Any]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for hypothesis in occurrence.get("hypotheses", []):
        if not isinstance(hypothesis, dict):
            continue
        if hypothesis.get("hypothesis_kind") != "DOCUMENTARY_LABEL_CANDIDATE":
            continue
        if hypothesis.get("promotion_authorized") is not False:
            raise ValueError(f"COL-03B hypothesis authority drift: {occurrence.get('occurrence_id')}")
        candidate_value = _normalize_label(hypothesis.get("candidate_value"))
        hypothesis_id = str(hypothesis.get("hypothesis_id") or "")
        if candidate_value and hypothesis_id:
            candidates.append({"candidate_value": candidate_value, "hypothesis_id": hypothesis_id})
    return sorted(candidates, key=lambda row: (row["candidate_value"], row["hypothesis_id"]))


def _observation_index(observations: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    seen_ids: set[str] = set()
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("TAV.7 observation must be a mapping")
        observation_id = str(observation.get("observation_id") or "")
        if not observation_id or observation_id in seen_ids:
            raise ValueError("TAV.7 observation IDs must be present and unique")
        seen_ids.add(observation_id)
        if observation.get("binding_state") != "UNBOUND" or observation.get("identity_promotion_authorized") is not False:
            raise ValueError(f"TAV.7 observation authority drift: {observation_id}")
        label = _normalize_label(observation.get("normalized_text"))
        if not label:
            continue
        index.setdefault(label, []).append(deepcopy(observation))
    for label in index:
        index[label] = sorted(index[label], key=lambda row: str(row["observation_id"]))
    return index


def _build_label_hypotheses(
    occurrence: dict[str, Any],
    observation_index: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], str, str]:
    occurrence_id = str(occurrence.get("occurrence_id") or "")
    hypotheses: list[dict[str, Any]] = []
    ambiguous = False
    for candidate in _predecessor_label_candidates(occurrence):
        matches = observation_index.get(candidate["candidate_value"], [])
        if not matches:
            continue
        supporting_ids = [candidate["hypothesis_id"]] + [str(row["observation_id"]) for row in matches]
        state = "AMBIGUOUS" if len(matches) > 1 else "SINGLE_CHANNEL_CANDIDATE"
        ambiguous = ambiguous or len(matches) > 1
        digest_seed = {
            "occurrence_id": occurrence_id,
            "candidate_value": candidate["candidate_value"],
            "supporting_evidence_ids": supporting_ids,
        }
        hypotheses.append(
            {
                "hypothesis_id": f"COL03C-HYP-{hashlib.sha256(_canonical_bytes(digest_seed)).hexdigest()[:16].upper()}",
                "occurrence_id": occurrence_id,
                "hypothesis_kind": "CROSS_DOCUMENT_LABEL_CANDIDATE",
                "candidate_value": candidate["candidate_value"],
                "supporting_evidence_ids": supporting_ids,
                "supporting_channels": ["COL03B_DOCUMENTARY_LABEL", "TAV07_EXACT_LABEL"],
                "contradicting_evidence_ids": [],
                "channel_count": 2,
                "state": state,
                "promotion_authorized": False,
            }
        )
    hypotheses = sorted(hypotheses, key=lambda row: (row["candidate_value"], row["hypothesis_id"]))
    if len(hypotheses) > 1:
        ambiguous = True
        for hypothesis in hypotheses:
            hypothesis["state"] = "AMBIGUOUS"
    if ambiguous:
        return hypotheses, "AMBIGUOUS", "AMBIGUOUS_CROSS_DOCUMENT_MATCH"
    if len(hypotheses) == 1:
        return hypotheses, "SINGLE_CANDIDATE", "NONE"
    return [], "EVALUATED_NO_MATCH", "NONE"


def build_cross_document_bundles(
    *,
    predecessor_occurrences: list[dict[str, Any]],
    tav07_source: dict[str, Any],
    tav07_observations: list[dict[str, Any]],
    historical_artifacts: list[dict[str, Any]],
    derived_reference_quality: dict[str, Any],
) -> list[dict[str, Any]]:
    if tav07_source.get("materialization_state") != "MATERIALIZED_VERIFIED":
        raise ValueError("TAV.7 primary source is not MATERIALIZED_VERIFIED")
    if tav07_source.get("authority") != "PRIMARY_DOCUMENTARY_SOURCE":
        raise ValueError("TAV.7 primary source authority drift")
    if tav07_source.get("identity_promotion_authorized") is not False:
        raise ValueError("TAV.7 source identity promotion drift")

    ordered_occurrences = sorted((deepcopy(row) for row in predecessor_occurrences), key=lambda row: str(row.get("occurrence_id") or ""))
    expected_ids = [f"COL-OCC-{index:04d}" for index in range(1, 23)]
    if len(ordered_occurrences) != 22 or [str(row.get("occurrence_id") or "") for row in ordered_occurrences] != expected_ids:
        raise ValueError("COL-03C occurrence subject drift")

    observation_index = _observation_index(tav07_observations)
    gaps = _historical_gaps(historical_artifacts)
    derived_state = deepcopy(derived_reference_quality)
    bundles: list[dict[str, Any]] = []
    for occurrence in ordered_occurrences:
        occurrence_id = str(occurrence["occurrence_id"])
        hypotheses, match_state, conflict_state = _build_label_hypotheses(occurrence, observation_index)
        bundle: dict[str, Any] = {
            "occurrence_id": occurrence_id,
            "predecessor_lineage": {
                "qualified_col03b_sha": QUALIFIED_COL03B_SHA,
                "exact_source_reconstructible": occurrence.get("exact_source_reconstructible") is True,
                "lineage_complete": occurrence.get("lineage_complete") is True,
            },
            "tav07_source_state": "MATERIALIZED_VERIFIED",
            "tav07_source_ref": {
                "catalogue_id": tav07_source.get("catalogue_id"),
                "archive_commit": tav07_source.get("archive_commit"),
                "source_path": tav07_source.get("source_path"),
                "sha256": tav07_source.get("sha256"),
            },
            "tav07_match_state": match_state,
            "hypotheses": hypotheses,
            "historical_recovery_gaps": deepcopy(gaps),
            "derived_reference_state": deepcopy(derived_state),
            "conflict_state": conflict_state,
            "cross_document_evidence_evaluated": True,
            "cross_document_identity_resolved": False,
            **_closed_authority(),
        }
        bundles.append(bundle)
    return bundles


def build_cross_document_reconciliation(
    *,
    bundles: list[dict[str, Any]],
    historical_artifacts: list[dict[str, Any]],
    derived_reference_quality: dict[str, Any],
    tav07_source: dict[str, Any],
) -> dict[str, Any]:
    ordered = sorted((deepcopy(row) for row in bundles), key=lambda row: str(row.get("occurrence_id") or ""))
    ambiguous_ids = sorted(
        str(row.get("occurrence_id") or "")
        for row in ordered
        if row.get("conflict_state") == "AMBIGUOUS_CROSS_DOCUMENT_MATCH"
    )
    contradictory_ids = sorted(
        str(row.get("occurrence_id") or "")
        for row in ordered
        if row.get("conflict_state") == "CONTRADICTORY_CROSS_DOCUMENT_EVIDENCE"
    )
    historical_states = {
        str(row.get("artifact_name") or ""): str(row.get("materialization_state") or "NOT_FOUND")
        for row in sorted(historical_artifacts, key=lambda item: str(item.get("artifact_name") or ""))
        if isinstance(row, dict) and str(row.get("artifact_name") or "")
    }
    historical_complete = bool(historical_states) and all(state == "MATERIALIZED_VERIFIED" for state in historical_states.values())
    topology = deepcopy(derived_reference_quality.get("topology_reference", {})) if isinstance(derived_reference_quality, dict) else {}
    candidate_matrix = deepcopy(derived_reference_quality.get("candidate_matrix_reference", {})) if isinstance(derived_reference_quality, dict) else {}
    return {
        "occurrence_count": len(ordered),
        "occurrence_ids": [str(row.get("occurrence_id") or "") for row in ordered],
        "tav07_source_state": tav07_source.get("materialization_state"),
        "tav07_source_sha256": tav07_source.get("sha256"),
        "historical_artifact_states": historical_states,
        "historical_derived_artifact_recovery_complete": historical_complete,
        "topology_reference_identity_use_state": topology.get("identity_use_state"),
        "topology_reference_unresolved_endpoint_ids": sorted(topology.get("unresolved_endpoint_ids", [])),
        "candidate_matrix_reference_role": candidate_matrix.get("reference_role"),
        "ambiguous_occurrence_ids": ambiguous_ids,
        "contradictory_occurrence_ids": contradictory_ids,
        "human_review_required": bool(ambiguous_ids or contradictory_ids),
        "bundle_digest": hashlib.sha256(_canonical_bytes(ordered)).hexdigest(),
    }


def build_cross_document_closure(
    *,
    bundles: list[dict[str, Any]],
    reconciliation: dict[str, Any],
    qualified_col03b_sha: str,
) -> dict[str, Any]:
    ordered = sorted((deepcopy(row) for row in bundles), key=lambda row: str(row.get("occurrence_id") or ""))
    expected_ids = [f"COL-OCC-{index:04d}" for index in range(1, 23)]
    ids = [str(row.get("occurrence_id") or "") for row in ordered]
    blocking: list[str] = []
    if qualified_col03b_sha != QUALIFIED_COL03B_SHA:
        blocking.append("QUALIFIED_BASE_SHA_DRIFT")
    if len(ordered) != 22 or ids != expected_ids or reconciliation.get("occurrence_count") != 22:
        blocking.append("OCCURRENCE_SET_DRIFT")
    if reconciliation.get("tav07_source_state") != "MATERIALIZED_VERIFIED":
        blocking.append("PRIMARY_SOURCE_RECONSTRUCTION_FAILED")
    if any(row.get("cross_document_evidence_evaluated") is not True for row in ordered):
        blocking.append("CROSS_DOCUMENT_EVALUATION_INCOMPLETE")
    if any(row.get("predecessor_lineage", {}).get("exact_source_reconstructible") is not True for row in ordered):
        blocking.append("PREDECESSOR_SOURCE_RECONSTRUCTION_DRIFT")
    if any(row.get("predecessor_lineage", {}).get("lineage_complete") is not True for row in ordered):
        blocking.append("PREDECESSOR_LINEAGE_DRIFT")
    if any(any(row.get(key) is not False for key in CLOSED_AUTHORITY_KEYS) for row in ordered):
        blocking.append("AUTHORITY_DRIFT")
    if any(
        gap.get("materialization_state") == "KNOWN_INVENTORY_NOT_MATERIALIZED" and gap.get("gap_class") != "HISTORICAL_RECOVERY_GAP"
        for row in ordered
        for gap in row.get("historical_recovery_gaps", [])
        if isinstance(gap, dict)
    ):
        blocking.append("HISTORICAL_GAP_SEMANTICS_DRIFT")
    blocking = sorted(set(blocking))
    return {
        "qualified_col03b_sha": qualified_col03b_sha,
        "available_cross_document_evidence_evaluated": not blocking,
        "historical_derived_artifact_recovery_complete": reconciliation.get("historical_derived_artifact_recovery_complete") is True,
        "all_occurrences_cross_document_resolved": False,
        "occurrence_count": len(ordered),
        "blocking_reasons": blocking,
        "human_review_required": bool(reconciliation.get("human_review_required")),
        "authority": _closed_authority(),
        "bundle_digest": reconciliation.get("bundle_digest"),
    }
