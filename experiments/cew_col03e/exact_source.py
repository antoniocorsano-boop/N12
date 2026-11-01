from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from .adjudication import AUTHORITY_KEYS, build_adjudication_dossiers


QUALIFIED_COL03D_BIN01_SHA = "df4a0a38d00d18dace597e9ca1cf449edfefca03"
OUTPUT_NAMES = (
    "identity-adjudication-dossiers.json",
    "identity-adjudication-readiness.json",
    "identity-adjudication-closure.json",
)


def build_exact_source_artifacts(
    *,
    col03b_ledger: dict[str, Any],
    col03c_ledger: dict[str, Any],
    historical_quality: dict[str, Any],
    predecessor_sha: str,
) -> dict[str, dict[str, Any]]:
    """Build the governed COL-03E evidence surface without promoting identity."""

    if predecessor_sha != QUALIFIED_COL03D_BIN01_SHA:
        raise ValueError("COL03E_PREDECESSOR_SHA_DRIFT")

    for key in ("structural_identity_authorized", "canonical_geometry_authorized", "canonical_write_authorized"):
        if historical_quality.get(key) is not False:
            raise ValueError(f"COL03E_HISTORICAL_AUTHORITY_DRIFT:{key}")

    dossiers = build_adjudication_dossiers(
        col03b_ledger=col03b_ledger,
        col03c_ledger=col03c_ledger,
        historical_quality=historical_quality,
        predecessor_sha=predecessor_sha,
    )
    if len(dossiers) != 22:
        raise ValueError("COL03E_DOSSIER_COUNT_DRIFT")

    state_counts = Counter(str(row["review_readiness_state"]) for row in dossiers)
    state_occurrence_ids = {
        state: [row["occurrence_id"] for row in dossiers if row["review_readiness_state"] == state]
        for state in sorted(state_counts)
    }
    documentary_candidate_occurrence_ids = [
        row["occurrence_id"] for row in dossiers if row["documentary_candidates"]
    ]
    ready_ids = state_occurrence_ids.get("READY_FOR_HUMAN_REVIEW", [])

    resolution_blockers = sorted(
        {
            blocker
            for row in dossiers
            for blocker in row.get("missing_evidence", [])
            if blocker in {"NO_GOVERNED_HISTORICAL_BRIDGE", "NO_TAV07_CROSS_DOCUMENT_MATCH"}
        }
    )

    dossiers_artifact: dict[str, Any] = {
        "schema": "CEW_COL03E_IDENTITY_ADJUDICATION_DOSSIERS_v1",
        "predecessor_sha": predecessor_sha,
        "occurrence_count": len(dossiers),
        "dossiers": dossiers,
        "identity_promotion_authorized": False,
    }

    readiness_artifact: dict[str, Any] = {
        "schema": "CEW_COL03E_IDENTITY_ADJUDICATION_READINESS_v1",
        "predecessor_sha": predecessor_sha,
        "occurrence_count": len(dossiers),
        "state_counts": dict(sorted(state_counts.items())),
        "state_occurrence_ids": state_occurrence_ids,
        "ready_for_human_review_count": len(ready_ids),
        "ready_for_human_review_occurrence_ids": ready_ids,
        "documentary_candidate_occurrence_ids": documentary_candidate_occurrence_ids,
        "identity_promotion_authorized": False,
    }

    closure: dict[str, Any] = {
        "schema": "CEW_COL03E_IDENTITY_ADJUDICATION_CLOSURE_v1",
        "predecessor_sha": predecessor_sha,
        "occurrence_count": len(dossiers),
        "adjudication_dossiers_complete": True,
        "any_identity_resolved": False,
        "qualification_blockers": [],
        "identity_resolution_blockers": resolution_blockers,
        "next_required_action": "ACQUIRE_NEW_IDENTITY_BRIDGE_EVIDENCE",
        "human_receipt_gate_required": True,
    }
    for key in AUTHORITY_KEYS:
        closure[key] = False

    return {
        "identity-adjudication-dossiers.json": dossiers_artifact,
        "identity-adjudication-readiness.json": readiness_artifact,
        "identity-adjudication-closure.json": closure,
    }


def write_col03e_artifacts(
    output_root: str | Path,
    artifacts: dict[str, dict[str, Any]],
) -> list[Path]:
    if set(artifacts) != set(OUTPUT_NAMES):
        raise ValueError("COL03E_OUTPUT_SURFACE_DRIFT")

    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    unexpected = sorted(path.name for path in root.iterdir() if path.name not in OUTPUT_NAMES)
    if unexpected:
        raise ValueError(f"UNEXPECTED_COL03E_OUTPUT_SURFACE:{','.join(unexpected)}")

    written: list[Path] = []
    for name in OUTPUT_NAMES:
        path = root / name
        payload = json.dumps(
            artifacts[name],
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            separators=(",", ": "),
        ) + "\n"
        path.write_text(payload, encoding="utf-8", newline="\n")
        written.append(path)
    return written
