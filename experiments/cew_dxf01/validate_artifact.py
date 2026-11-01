from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.cew_col03d.member_verification import REQUIRED_MEMBER_CONTRACTS
from experiments.cew_dxf01.exact_source import EXPECTED_FILENAMES
from experiments.cew_dxf01.normalize import canonical_sha256


_CLOSED_AUTHORITY = {
    "authority_effect": "NONE",
    "primary_source_identity_bridge": False,
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "family_assignment_authorized": False,
    "section_assignment_authorized": False,
    "m0g_authorized": False,
}
_EXPECTED_DXF = {
    str(row["artifact_name"]): {
        "sha256": str(row["sha256"]),
        "size_bytes": int(row["size_bytes"]),
    }
    for row in REQUIRED_MEMBER_CONTRACTS
    if str(row["artifact_name"]).lower().endswith(".dxf")
}


def _assert_closed_authority(authority: Any, *, label: str) -> None:
    if authority != _CLOSED_AUTHORITY:
        raise ValueError(f"AUTHORITY_DRIFT:{label}")


def validate_payloads(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if set(payloads) != set(EXPECTED_FILENAMES):
        raise ValueError("ARTIFACT_SURFACE_DRIFT")

    observations = payloads["dxf-observations.json"]
    receipt = payloads["dxf-observation-receipt.json"]
    closure = payloads["dxf-read-query-closure.json"]

    if observations.get("schema") != "CEW_DXF01_OBSERVATIONS_v1":
        raise ValueError("OBSERVATIONS_SCHEMA_DRIFT")
    if receipt.get("schema") != "CEW_DXF01_OBSERVATION_RECEIPT_v1":
        raise ValueError("RECEIPT_SCHEMA_DRIFT")
    if closure.get("schema") != "CEW_DXF01_READ_QUERY_CLOSURE_v1":
        raise ValueError("CLOSURE_SCHEMA_DRIFT")

    _assert_closed_authority(observations.get("authority"), label="OBSERVATIONS")
    _assert_closed_authority(receipt.get("authority"), label="RECEIPT")
    _assert_closed_authority(closure.get("authority"), label="CLOSURE")

    if receipt.get("status") != "READ_QUERY_PASS":
        raise ValueError("RECEIPT_STATUS_DRIFT")
    toolchain = receipt.get("toolchain") or {}
    if toolchain.get("ezdxf_version") != "1.4.5" or toolchain.get("direct_pin") != "ezdxf==1.4.5":
        raise ValueError("TOOLCHAIN_DRIFT")
    if toolchain.get("qualification_scope") != "CEW-DXF-01_ONLY":
        raise ValueError("TOOLCHAIN_AUTHORITY_DRIFT")

    observed_rows = observations.get("observations")
    if not isinstance(observed_rows, list) or len(observed_rows) != 3:
        raise ValueError("OBSERVATION_COUNT_DRIFT")
    if observations.get("source_count") != 3 or receipt.get("source_count") != 3:
        raise ValueError("SOURCE_COUNT_DRIFT")

    seen: dict[str, dict[str, Any]] = {}
    for observation in observed_rows:
        if not isinstance(observation, dict):
            raise ValueError("OBSERVATION_SHAPE_DRIFT")
        source = observation.get("source") or {}
        name = str(source.get("artifact_name") or "")
        expected = _EXPECTED_DXF.get(name)
        if expected is None:
            raise ValueError(f"UNEXPECTED_SOURCE:{name}")
        if source.get("sha256") != expected["sha256"] or source.get("size_bytes") != expected["size_bytes"]:
            raise ValueError(f"PROVENANCE_MISMATCH:{name}")
        if source.get("dxf_version") != "AC1027":
            raise ValueError(f"DXF_VERSION_DRIFT:{name}")
        _assert_closed_authority(observation.get("authority"), label=f"OBSERVATION:{name}")
        if observation.get("source_bytes_unchanged") is not True:
            raise ValueError(f"SOURCE_MUTATION_FLAG_DRIFT:{name}")
        digest = str(observation.get("normalized_sha256") or "")
        if len(digest) != 64:
            raise ValueError(f"NORMALIZED_DIGEST_DRIFT:{name}")
        seen[name] = observation
    if set(seen) != set(_EXPECTED_DXF):
        raise ValueError("SOURCE_SET_DRIFT")

    expected_bundle = canonical_sha256(observations)
    if receipt.get("observation_bundle_sha256") != expected_bundle:
        raise ValueError("OBSERVATION_BUNDLE_DIGEST_DRIFT")
    if closure.get("observation_bundle_sha256") != expected_bundle:
        raise ValueError("CLOSURE_BUNDLE_DIGEST_DRIFT")

    summaries = receipt.get("observations")
    if not isinstance(summaries, list) or len(summaries) != 3:
        raise ValueError("RECEIPT_OBSERVATION_SUMMARY_DRIFT")
    summary_names = {str(row.get("artifact_name") or "") for row in summaries if isinstance(row, dict)}
    if summary_names != set(_EXPECTED_DXF):
        raise ValueError("RECEIPT_SOURCE_SET_DRIFT")
    for row in summaries:
        if row.get("authority_effect") != "NONE":
            raise ValueError("AUTHORITY_DRIFT:RECEIPT_OBSERVATION")

    if closure.get("exact_source_replay_complete") is not True:
        raise ValueError("EXACT_SOURCE_REPLAY_NOT_COMPLETE")
    if closure.get("historical_dxf_is_primary_identity_bridge") is not False:
        raise ValueError("AUTHORITY_DRIFT:HISTORICAL_PRIMARY_BRIDGE")
    if closure.get("unresolved_primary_identity_residual_carries_forward") is not True:
        raise ValueError("PRIMARY_IDENTITY_RESIDUAL_LOST")
    if closure.get("next_action") != "PORT_ENGINEERING_GRAMMAR_BOUNDARY":
        raise ValueError("NEXT_ACTION_DRIFT")

    return {
        "status": "PASS",
        "source_count": 3,
        "observation_bundle_sha256": expected_bundle,
        "authority_effect": "NONE",
    }


def load_payloads(root: str | Path) -> dict[str, dict[str, Any]]:
    root_path = Path(root)
    if not root_path.is_dir():
        raise ValueError(f"ARTIFACT_ROOT_NOT_FOUND:{root_path}")
    actual_files = {path.name for path in root_path.iterdir() if path.is_file()}
    if actual_files != set(EXPECTED_FILENAMES):
        raise ValueError("ARTIFACT_SURFACE_DRIFT")
    payloads: dict[str, dict[str, Any]] = {}
    for name in EXPECTED_FILENAMES:
        try:
            payloads[name] = json.loads((root_path / name).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"ARTIFACT_READ_FAILED:{name}") from exc
    return payloads


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CEW-DXF-01 exact-source evidence")
    parser.add_argument("artifact_root")
    args = parser.parse_args()

    result = validate_payloads(load_payloads(Path(args.artifact_root)))
    print(
        "CEW_DXF01_ARTIFACT_VALIDATION=PASS "
        f"sources={result['source_count']} "
        f"bundle_sha256={result['observation_bundle_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
