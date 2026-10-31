from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any


QUALIFIED_COL03A_SHA = "0d4a43cf02eadd2ab6f4b2641888395586c08a98"

CHANNEL_KEYS = (
    "internal_text_evidence",
    "intersecting_text_evidence",
    "nearby_text_evidence",
    "high_resolution_read_evidence",
    "callout_evidence",
    "local_topology_evidence",
    "cross_document_evidence",
)

CLOSED_AUTHORITY_KEYS = (
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


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _pretty_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def finalize_evidence_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(bundle)
    missing: list[str] = []
    for channel in CHANNEL_KEYS:
        values = result.get(channel)
        if not isinstance(values, list) or not values:
            missing.append(channel)
    result["missing_channels"] = missing
    result["documentary_evidence_state"] = "COMPLETE" if not missing else "PARTIAL"
    if not result.get("documentary_identity_resolution_state"):
        result["documentary_identity_resolution_state"] = "UNRESOLVED"
    return result


def build_documentary_reconciliation(
    bundles: list[dict[str, Any]],
    *,
    historical_manifest: dict[str, Any],
) -> dict[str, Any]:
    ordered = sorted((deepcopy(row) for row in bundles), key=lambda row: str(row.get("occurrence_id") or ""))
    counts = {channel: 0 for channel in CHANNEL_KEYS}
    no_evidence_counts = {channel: 0 for channel in CHANNEL_KEYS}
    hypothesis_states: dict[str, int] = {}
    ambiguous_occurrences: list[str] = []
    contradictory_occurrences: list[str] = []
    uses_historical = False

    for bundle in ordered:
        for channel in CHANNEL_KEYS:
            values = bundle.get(channel)
            if not isinstance(values, list):
                continue
            counts[channel] += len(values)
            no_evidence_counts[channel] += sum(
                1 for item in values if isinstance(item, dict) and item.get("evidence_class") in {"NO_EVIDENCE", "NOT_APPLICABLE"}
            )
            if channel == "cross_document_evidence":
                uses_historical = uses_historical or any(
                    isinstance(item, dict) and item.get("evidence_class") != "NO_EVIDENCE" for item in values
                )
        for hypothesis in bundle.get("hypotheses", []):
            if isinstance(hypothesis, dict):
                state = str(hypothesis.get("state") or "UNSPECIFIED")
                hypothesis_states[state] = hypothesis_states.get(state, 0) + 1
        if bundle.get("conflict_state") in {"AMBIGUOUS_TEXT_BINDING", "AMBIGUOUS_CROSS_DOCUMENT_MATCH"}:
            ambiguous_occurrences.append(str(bundle.get("occurrence_id")))
        if bundle.get("conflict_state") == "CONTRADICTORY_DOCUMENTARY_EVIDENCE":
            contradictory_occurrences.append(str(bundle.get("occurrence_id")))

    artifacts = historical_manifest.get("artifacts", []) if isinstance(historical_manifest, dict) else []
    historical_provenance_complete = True
    if uses_historical:
        if not isinstance(artifacts, list) or not artifacts:
            historical_provenance_complete = False
        else:
            for artifact in artifacts:
                if not isinstance(artifact, dict) or any(not artifact.get(key) for key in ("artifact_id", "path", "version", "sha256")):
                    historical_provenance_complete = False
                    break

    return {
        "occurrence_count": len(ordered),
        "occurrence_ids": [str(row.get("occurrence_id") or "") for row in ordered],
        "evidence_counts_by_channel": counts,
        "explicit_no_evidence_counts_by_channel": no_evidence_counts,
        "hypothesis_states": dict(sorted(hypothesis_states.items())),
        "ambiguous_occurrence_ids": sorted(ambiguous_occurrences),
        "contradictory_occurrence_ids": sorted(contradictory_occurrences),
        "historical_artifact_count": len(artifacts) if isinstance(artifacts, list) else 0,
        "historical_provenance_complete": historical_provenance_complete,
        "human_review_required": bool(ambiguous_occurrences or contradictory_occurrences),
        "bundle_digest": hashlib.sha256(_canonical_bytes(ordered)).hexdigest(),
    }


def build_documentary_closure(
    *,
    bundles: list[dict[str, Any]],
    reconciliation: dict[str, Any],
    predecessor_closure: dict[str, Any],
    qualified_base_sha: str,
) -> dict[str, Any]:
    ordered = sorted((deepcopy(row) for row in bundles), key=lambda row: str(row.get("occurrence_id") or ""))
    blocking: list[str] = []
    expected_ids = [f"COL-OCC-{index:04d}" for index in range(1, 23)]
    ids = [str(row.get("occurrence_id") or "") for row in ordered]

    if qualified_base_sha != QUALIFIED_COL03A_SHA:
        blocking.append("QUALIFIED_BASE_SHA_DRIFT")
    if predecessor_closure.get("occurrence_ledger_complete") is not True:
        blocking.append("PREDECESSOR_NOT_COMPLETE")
    if ids != expected_ids or len(ordered) != 22:
        blocking.append("OCCURRENCE_SET_DRIFT")
    if reconciliation.get("occurrence_count") != 22:
        blocking.append("RECONCILIATION_COUNT_DRIFT")
    if reconciliation.get("historical_provenance_complete") is not True:
        blocking.append("HISTORICAL_ARTIFACT_PROVENANCE_MISSING")

    if any(row.get("documentary_evidence_state") != "COMPLETE" or row.get("missing_channels") not in ([], None) for row in ordered):
        blocking.append("EVIDENCE_COLLECTION_INCOMPLETE")
    if any(row.get("exact_source_reconstructible") is not True for row in ordered):
        blocking.append("SOURCE_RECONSTRUCTION_FAILED")
    if any(row.get("lineage_complete") is not True for row in ordered):
        blocking.append("COL03A_LINEAGE_DRIFT")
    if any(any(row.get(key) is not False for key in CLOSED_AUTHORITY_KEYS) for row in ordered):
        blocking.append("AUTHORITY_DRIFT")

    blocking = sorted(set(blocking))
    all_resolved = bool(ordered) and all(row.get("documentary_identity_resolved") is True for row in ordered)
    return {
        "qualified_col03a_sha": qualified_base_sha,
        "documentary_identity_evidence_collection_complete": not blocking,
        "all_occurrences_identity_resolved": all_resolved,
        "occurrence_count": len(ordered),
        "blocking_reasons": blocking,
        "human_review_required": bool(reconciliation.get("human_review_required")),
        "authority": {key: False for key in CLOSED_AUTHORITY_KEYS},
        "bundle_digest": reconciliation.get("bundle_digest"),
    }


def write_col03b_artifacts(
    output_dir: Path,
    *,
    bundles: list[dict[str, Any]],
    reconciliation: dict[str, Any],
    closure: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted((deepcopy(row) for row in bundles), key=lambda row: str(row.get("occurrence_id") or ""))
    hypotheses = sorted(
        [deepcopy(hypothesis) for bundle in ordered for hypothesis in bundle.get("hypotheses", []) if isinstance(hypothesis, dict)],
        key=lambda row: (str(row.get("occurrence_id") or ""), str(row.get("hypothesis_id") or "")),
    )
    payloads = {
        "documentary-identity-evidence-ledger.json": {
            "occurrence_count": len(ordered),
            "occurrences": ordered,
        },
        "documentary-identity-hypotheses.json": {
            "hypothesis_count": len(hypotheses),
            "hypotheses": hypotheses,
        },
        "documentary-identity-reconciliation.json": deepcopy(reconciliation),
        "documentary-identity-evidence-closure.json": deepcopy(closure),
    }
    digests: dict[str, str] = {}
    for filename, payload in sorted(payloads.items()):
        data = _pretty_bytes(payload)
        (output_dir / filename).write_bytes(data)
        digests[filename] = _digest_bytes(data)
    return digests
