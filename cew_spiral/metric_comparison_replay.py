from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
from pathlib import Path
from typing import Any

from cew_spiral.exact_source_metric_comparison import build_metric_comparison_bundle


REGISTRATION_COMMIT = "15b55e3711f27f4499eb97a9e4d99bfa5f8f2e57"
REGISTRATION_PATH = "data/canonical/STOREY_SUPPORT_XY_REGISTRATION_v1.csv"
COMPARATOR_COMMIT = "dba5c4c2f09161b731a26bb0f8eab5826f1d136b"
COMPARATOR_PATH = "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv"


def _csv_rows(text: str, error: str) -> list[dict[str, str]]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError(error)
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise ValueError(error)
    return rows


def build_metric_comparison_replay(
    *,
    structural_bridge_payload: dict[str, Any],
    registration_csv: str,
    historical_nodes_csv: str,
    registration_commit: str,
    comparator_commit: str,
) -> dict[str, Any]:
    if not isinstance(structural_bridge_payload, dict):
        raise ValueError("STRUCTURAL_BRIDGE_PAYLOAD_REQUIRED")
    if structural_bridge_payload.get("schema") != "CEW_SPIRAL_EXACT_SOURCE_STRUCTURAL_CANDIDATE_BRIDGE_v1":
        raise ValueError("STRUCTURAL_BRIDGE_SCHEMA_INVALID")
    qualification = structural_bridge_payload.get("qualification")
    if not isinstance(qualification, dict) or qualification.get("exact_source_replayable") is not True:
        raise ValueError("STRUCTURAL_BRIDGE_NOT_EXACT_SOURCE_QUALIFIED")
    if qualification.get("historical_comparator_loaded") is not False:
        raise ValueError("HISTORICAL_COMPARATOR_PRELOADED")
    bridge = structural_bridge_payload.get("bridge")
    if not isinstance(bridge, dict):
        raise ValueError("STRUCTURAL_BRIDGE_REQUIRED")
    candidate_count = qualification.get("structural_candidate_count")
    if candidate_count != bridge.get("structural_candidate_count"):
        raise ValueError("STRUCTURAL_BRIDGE_COUNT_DRIFT")

    registration_rows = _csv_rows(registration_csv, "REGISTRATION_CSV_REQUIRED")
    historical_supports = _csv_rows(historical_nodes_csv, "HISTORICAL_NODES_CSV_REQUIRED")
    comparison = build_metric_comparison_bundle(
        structural_bridge=bridge,
        registration_rows=registration_rows,
        historical_supports=historical_supports,
        registration_commit=registration_commit,
        comparator_commit=comparator_commit,
    )
    if comparison.get("comparison_count") != candidate_count:
        raise ValueError("METRIC_REPLAY_COUNT_DRIFT")

    return {
        "schema": "CEW_SPIRAL_METRIC_COMPARISON_REPLAY_v1",
        "input_boundary": {
            "structural_candidate_count": candidate_count,
            "historical_comparator_loaded_before_replay": False,
            "registration_commit": registration_commit,
            "registration_path": REGISTRATION_PATH,
            "comparator_commit": comparator_commit,
            "comparator_path": COMPARATOR_PATH,
        },
        "comparison": comparison,
        "authority": {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
            "engineering_authority_effect": "NONE",
        },
    }


def _git_show(commit: str, path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": ")) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay the non-authoritative CEW-SPIRAL metric witness comparison")
    parser.add_argument(
        "--structural-bridge",
        type=Path,
        default=Path("evidence/cew-spiral01/structural-candidate/structural-candidate-bridge.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/cew-spiral01/metric-comparison/metric-comparison-replay.json"),
    )
    parser.add_argument("--registration-commit", default=REGISTRATION_COMMIT)
    parser.add_argument("--comparator-commit", default=COMPARATOR_COMMIT)
    args = parser.parse_args(argv)

    structural_bridge_payload = json.loads(args.structural_bridge.read_text(encoding="utf-8"))
    result = build_metric_comparison_replay(
        structural_bridge_payload=structural_bridge_payload,
        registration_csv=_git_show(args.registration_commit, REGISTRATION_PATH),
        historical_nodes_csv=_git_show(args.comparator_commit, COMPARATOR_PATH),
        registration_commit=args.registration_commit,
        comparator_commit=args.comparator_commit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(_canonical_bytes(result))
    summary = result["comparison"]["summary"]
    print(
        "CEW_SPIRAL_METRIC_COMPARISON_REPLAY="
        + json.dumps(
            {
                "status": "PASS",
                "comparison_count": result["comparison"]["comparison_count"],
                "min_distance_m": summary["min_distance_m"],
                "median_distance_m": summary["median_distance_m"],
                "max_distance_m": summary["max_distance_m"],
                "unique_nearest_historical_node_count": summary["unique_nearest_historical_node_count"],
                "canonical_write_authorized": False,
                "m0g_authorized": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
