from __future__ import annotations

import argparse
from importlib.metadata import version as distribution_version
import json
from pathlib import Path
import tempfile
from typing import Any

from experiments.cew_col03d.member_verification import (
    HISTORICAL_TRANSPORT_ROOT,
    REQUIRED_MEMBER_CONTRACTS,
    reconstruct_required_member_directory,
)
from experiments.cew_dxf01.normalize import canonical_sha256
from experiments.cew_dxf01.reader import read_dxf_path


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_FILENAMES = (
    "dxf-observations.json",
    "dxf-observation-receipt.json",
    "dxf-read-query-closure.json",
)
DXF_CONTRACTS = tuple(
    row
    for row in REQUIRED_MEMBER_CONTRACTS
    if str(row["artifact_name"]).lower().endswith(".dxf")
)
_AUTHORITY = {
    "authority_effect": "NONE",
    "primary_source_identity_bridge": False,
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "family_assignment_authorized": False,
    "section_assignment_authorized": False,
    "m0g_authorized": False,
}


def _observation_summary(observation: dict[str, Any]) -> dict[str, Any]:
    source = observation["source"]
    inventories = observation["inventories"]
    return {
        "artifact_name": source["artifact_name"],
        "source_sha256": source["sha256"],
        "size_bytes": source["size_bytes"],
        "dxf_version": source["dxf_version"],
        "normalized_sha256": observation["normalized_sha256"],
        "entity_counts": inventories["entity_counts"],
        "layer_count": len(inventories["layers"]),
        "text_entity_count": len(inventories["text_entities"]),
        "insert_count": len(inventories["inserts"]),
        "dimension_count": len(inventories["dimensions"]),
        "authority_effect": observation["authority"]["authority_effect"],
    }


def build_exact_source_artifacts(transport_root: str | Path) -> dict[str, dict[str, Any]]:
    transport_path = Path(transport_root)
    if not transport_path.is_dir():
        raise ValueError(f"TRANSPORT_ROOT_NOT_FOUND:{transport_path}")

    with tempfile.TemporaryDirectory() as tmp:
        member_root = Path(tmp) / "members"
        reconstructed = reconstruct_required_member_directory(
            transport_path,
            member_root,
            contracts=DXF_CONTRACTS,
        )
        reconstructed_by_name = {row["artifact_name"]: row for row in reconstructed}

        observations: list[dict[str, Any]] = []
        for contract in sorted(DXF_CONTRACTS, key=lambda row: str(row["artifact_name"])):
            name = str(contract["artifact_name"])
            replay = reconstructed_by_name.get(name)
            if replay is None or replay.get("transport_reconstruction_state") != "LOSSLESS_RECONSTRUCTED":
                raise ValueError(f"TRANSPORT_REPLAY_INCOMPLETE:{name}")
            observations.append(
                read_dxf_path(
                    member_root / name,
                    artifact_name=name,
                    expected_sha256=str(contract["sha256"]),
                    expected_size_bytes=int(contract["size_bytes"]),
                )
            )

    observations_payload: dict[str, Any] = {
        "schema": "CEW_DXF01_OBSERVATIONS_v1",
        "slice": "CEW-DXF-01",
        "source_count": len(observations),
        "source_lineage": "archive/historical_packages/v25/transport -> lossless reconstructed members",
        "observations": observations,
        "authority": dict(_AUTHORITY),
    }
    observation_bundle_sha256 = canonical_sha256(observations_payload)

    receipt_payload: dict[str, Any] = {
        "schema": "CEW_DXF01_OBSERVATION_RECEIPT_v1",
        "slice": "CEW-DXF-01",
        "status": "READ_QUERY_PASS",
        "source_count": len(observations),
        "toolchain": {
            "ezdxf_version": distribution_version("ezdxf"),
            "direct_pin": "ezdxf==1.4.5",
            "qualification_scope": "CEW-DXF-01_ONLY",
        },
        "observations": [_observation_summary(row) for row in observations],
        "authority": dict(_AUTHORITY),
        "observation_bundle_sha256": observation_bundle_sha256,
    }

    closure_payload: dict[str, Any] = {
        "schema": "CEW_DXF01_READ_QUERY_CLOSURE_v1",
        "slice": "CEW-DXF-01",
        "exact_source_replay_complete": True,
        "source_count": len(observations),
        "observation_bundle_sha256": observation_bundle_sha256,
        "historical_dxf_is_primary_identity_bridge": False,
        "authority": dict(_AUTHORITY),
        "unresolved_primary_identity_residual_carries_forward": True,
        "next_action": "PORT_ENGINEERING_GRAMMAR_BOUNDARY",
    }

    return {
        "dxf-observations.json": observations_payload,
        "dxf-observation-receipt.json": receipt_payload,
        "dxf-read-query-closure.json": closure_payload,
    }


def _encode_json(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def write_exact_source_artifacts(
    output_root: str | Path,
    artifacts: dict[str, dict[str, Any]],
) -> list[Path]:
    if set(artifacts) != set(EXPECTED_FILENAMES):
        raise ValueError("ARTIFACT_SURFACE_DRIFT")
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in EXPECTED_FILENAMES:
        path = output_path / name
        path.write_bytes(_encode_json(artifacts[name]))
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CEW-DXF-01 exact-source evidence")
    parser.add_argument(
        "--transport",
        default=str(ROOT / HISTORICAL_TRANSPORT_ROOT),
        help="Recovered historical package transport root",
    )
    parser.add_argument("--output", required=True, help="Output directory for governed JSON evidence")
    args = parser.parse_args()

    artifacts = build_exact_source_artifacts(Path(args.transport))
    write_exact_source_artifacts(Path(args.output), artifacts)
    print("CEW_DXF01_EXACT_SOURCE_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
