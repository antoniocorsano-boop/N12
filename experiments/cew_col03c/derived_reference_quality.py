from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Any


FROZEN_ARCHIVE_COMMIT = "78c20a52db4f391ce0d13b9705b9f04737e218c9"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _normalized_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("rows must contain mappings")
        normalized.append({str(key): row[key] for key in sorted(row)})
    return sorted(normalized, key=lambda row: _canonical_bytes(row))


def materialize_reference_descriptor(
    *,
    path: str,
    archive_commit: str,
    bytes_sha256: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if archive_commit != FROZEN_ARCHIVE_COMMIT:
        raise ValueError("derived reference archive commit drift")
    if not isinstance(path, str) or not path.strip():
        raise ValueError("derived reference path missing")
    normalized_sha = str(bytes_sha256).lower()
    if not _HEX64.fullmatch(normalized_sha):
        raise ValueError("derived reference sha256 invalid")
    canonical_rows = _normalized_rows(rows)
    return {
        "path": path,
        "archive_commit": archive_commit,
        "sha256": normalized_sha,
        "row_count": len(canonical_rows),
        "row_set_digest": hashlib.sha256(_canonical_bytes(canonical_rows)).hexdigest(),
        "materialization_state": "MATERIALIZED_VERIFIED",
        "authority": "REFERENCE_ONLY",
    }


def audit_topology_reference(
    *,
    nodes: list[dict[str, Any]],
    connections: list[dict[str, Any]],
    provenance: dict[str, Any],
    historical_inventory_claim: dict[str, Any] | None = None,
) -> dict[str, Any]:
    node_rows = _normalized_rows(nodes)
    connection_rows = _normalized_rows(connections)
    declared = sorted({str(row.get("nodo") or "") for row in node_rows if str(row.get("nodo") or "")})
    referenced = sorted(
        {
            str(row.get(key) or "")
            for row in connection_rows
            for key in ("nodo_1", "nodo_2")
            if str(row.get(key) or "")
        }
    )
    unresolved = sorted(set(referenced) - set(declared))
    result: dict[str, Any] = {
        "reference_kind": "TAV5_TOPOLOGY_DERIVED_REFERENCE",
        "provenance": deepcopy(provenance),
        "node_row_count": len(node_rows),
        "connection_row_count": len(connection_rows),
        "declared_node_ids": declared,
        "referenced_endpoint_ids": referenced,
        "unresolved_endpoint_ids": unresolved,
        "identity_use_state": "DATA_QUALITY_BLOCKED" if unresolved else "REFERENCE_READY",
        "identity_evidence_usable": not unresolved,
        "authority": "REFERENCE_ONLY",
        "historical_inventory_claim": deepcopy(historical_inventory_claim) if historical_inventory_claim is not None else None,
        "node_rows_digest": hashlib.sha256(_canonical_bytes(node_rows)).hexdigest(),
        "connection_rows_digest": hashlib.sha256(_canonical_bytes(connection_rows)).hexdigest(),
    }
    digest_payload = deepcopy(result)
    result["quality_digest"] = hashlib.sha256(_canonical_bytes(digest_payload)).hexdigest()
    return result


def audit_candidate_matrix_reference(
    *,
    rows: list[dict[str, Any]],
    provenance: dict[str, Any],
) -> dict[str, Any]:
    canonical_rows = _normalized_rows(rows)
    hypotheses = sorted({str(row.get("hypothesis") or "") for row in canonical_rows if str(row.get("hypothesis") or "")})
    evidence_states = sorted({str(row.get("evidence_status") or "") for row in canonical_rows if str(row.get("evidence_status") or "")})
    result: dict[str, Any] = {
        "reference_kind": "TAV5_CANDIDATE_MATRIX_DERIVED_REFERENCE",
        "provenance": deepcopy(provenance),
        "row_count": len(canonical_rows),
        "hypothesis_ids": hypotheses,
        "evidence_states": evidence_states,
        "reference_role": "CANDIDATE_HYPOTHESES_ONLY",
        "historical_27x5_matrix": False,
        "identity_evidence_usable": False,
        "authority": "REFERENCE_ONLY",
        "rows_digest": hashlib.sha256(_canonical_bytes(canonical_rows)).hexdigest(),
    }
    digest_payload = deepcopy(result)
    result["quality_digest"] = hashlib.sha256(_canonical_bytes(digest_payload)).hexdigest()
    return result
