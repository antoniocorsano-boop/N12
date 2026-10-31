from __future__ import annotations

from copy import deepcopy
from typing import Any


def _validate_artifact_ref(artifact: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(artifact, dict):
        raise ValueError("historical artifact provenance must be an object")
    required = ("artifact_id", "path", "version", "sha256")
    if any(not artifact.get(key) for key in required):
        raise ValueError("historical artifact provenance incomplete")
    digest = str(artifact["sha256"])
    if len(digest) != 64:
        raise ValueError("historical artifact provenance sha256 invalid")
    return deepcopy(artifact)


def validate_historical_artifact_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    artifacts = manifest.get("artifacts") if isinstance(manifest, dict) else None
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("historical artifact provenance manifest missing")
    normalized = [_validate_artifact_ref(row) for row in artifacts]
    ids = [str(row["artifact_id"]) for row in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("historical artifact provenance IDs must be unique")
    return {"artifacts": normalized}


def build_cross_document_candidate(
    *,
    occurrence_id: str,
    artifact_ref: dict[str, Any],
    candidate_id: str,
    matching_discriminants: list[str],
    conflicting_discriminants: list[str],
    transform_ref: dict[str, Any] | None,
) -> dict[str, Any]:
    artifact = _validate_artifact_ref(artifact_ref)
    matches = sorted({str(value) for value in matching_discriminants if str(value)})
    conflicts = sorted({str(value) for value in conflicting_discriminants if str(value)})
    competing = sorted({str(value) for value in artifact.get("competing_candidate_ids", []) if str(value)})
    ambiguous = bool(competing and (len(competing) > 1 or str(candidate_id) not in competing))

    if conflicts:
        status = "CONTRADICTED"
    elif transform_ref is not None and matches and not ambiguous:
        status = "SUPPORTED"
    elif not matches:
        status = "NOT_APPLICABLE"
    else:
        status = "CANDIDATE"

    return {
        "evidence_id": f"XREF-{occurrence_id}-{artifact['artifact_id']}-{candidate_id}",
        "occurrence_id": str(occurrence_id),
        "artifact_ref": artifact,
        "candidate_id": str(candidate_id),
        "matching_discriminants": matches,
        "conflicting_discriminants": conflicts,
        "transform_ref": deepcopy(transform_ref),
        "ambiguous": ambiguous,
        "status": status,
        "evidence_class": "INDEPENDENT_DOCUMENTARY_CORRESPONDENCE",
        "support_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
    }
