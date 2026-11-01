from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cew_b01.evidence_schema import Task3RasterBinding
from cew_b01.pdf_probe import probe_pdf
from cew_b01.source_contract import load_source_contract, materialize_source, validate_frozen_n12_tav5
from cew_spiral.structural_candidate_bridge import build_structural_candidate_bridge


SOURCE_CONTRACT_PATH = Path("governance/cew-b01/N12_TAV5_SOURCE_v1.json")


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, separators=(",", ": ")) + "\n").encode("utf-8")


def build_exact_source_structural_candidate_bridge(
    *,
    ledger_path: Path,
    closure_path: Path,
    output_path: Path,
    probe_root: Path,
) -> dict[str, Any]:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    closure = json.loads(closure_path.read_text(encoding="utf-8"))
    if closure.get("occurrence_ledger_complete") is not True:
        raise ValueError("COL03A_LEDGER_NOT_QUALIFIED")
    if ledger.get("occurrence_count") != 22 or ledger.get("conflict_count") != 0:
        raise ValueError("COL03A_LEDGER_SURFACE_DRIFT")

    contract = load_source_contract(SOURCE_CONTRACT_PATH)
    validate_frozen_n12_tav5(contract)
    runner_temp = Path(os.environ.get("RUNNER_TEMP") or probe_root.parent)
    materialized = materialize_source(
        contract,
        ".",
        runner_temp / "tavola5-spiral-structural-candidate-source.pdf",
    )
    probe = probe_pdf(materialized, probe_root)
    binding = Task3RasterBinding.from_probe_mapping(probe.to_mapping())

    kwargs = {
        "ledger": ledger,
        "source": binding.source,
        "raster_width_px": binding.raster_width_px,
        "raster_height_px": binding.raster_height_px,
        "raster_sha256": binding.raster_sha256,
        "renderer_tool_version": binding.renderer_tool_version,
    }
    first = build_structural_candidate_bridge(**kwargs)
    second = build_structural_candidate_bridge(**kwargs)
    if _canonical_bytes(first) != _canonical_bytes(second):
        raise ValueError("STRUCTURAL_CANDIDATE_BRIDGE_NONDETERMINISTIC")

    if first.get("occurrence_count") != 22 or first.get("structural_candidate_count") != 22:
        raise ValueError("STRUCTURAL_CANDIDATE_BRIDGE_COUNT_DRIFT")
    bundle = first.get("pre_comparator_bundle") or {}
    if bundle.get("evidence_candidate_count") != 22 or bundle.get("structural_candidate_count") != 22:
        raise ValueError("PRE_COMPARATOR_BUNDLE_COUNT_DRIFT")
    if bundle.get("historical_comparator_loaded") is not False:
        raise ValueError("HISTORICAL_COMPARATOR_LOADED_TOO_EARLY")
    for row in first.get("structural_candidates") or []:
        if row.get("semantic_label") != "COLUMN":
            raise ValueError("STRUCTURAL_CANDIDATE_SEMANTIC_DRIFT")
        if row.get("support_identifier") is not None or row.get("section_family") is not None:
            raise ValueError("STRUCTURAL_CANDIDATE_PREMATURE_DOCUMENTARY_BINDING")
        if row.get("canonical") is not False or row.get("structural_identity_authorized") is not False:
            raise ValueError("STRUCTURAL_CANDIDATE_AUTHORITY_DRIFT")

    payload = {
        "schema": "CEW_SPIRAL_EXACT_SOURCE_STRUCTURAL_CANDIDATE_BRIDGE_v1",
        "col03a_ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        "col03a_closure_sha256": hashlib.sha256(closure_path.read_bytes()).hexdigest(),
        "bridge": first,
        "qualification": {
            "exact_source_replayable": True,
            "deterministic_replay": True,
            "occurrence_count": 22,
            "structural_candidate_count": 22,
            "historical_support_identifier_required": False,
            "historical_comparator_loaded": False,
            "canonical_write_authorized": False,
            "structural_identity_authorized": False,
            "m0g_authorized": False,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_canonical_bytes(payload))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay the first CEW-SPIRAL StructuralObjectCandidate bridge")
    parser.add_argument("--ledger", type=Path, default=Path("evidence/cew-col03a/column-occurrence-ledger.json"))
    parser.add_argument("--closure", type=Path, default=Path("evidence/cew-col03a/column-occurrence-ledger-closure.json"))
    parser.add_argument("--output", type=Path, default=Path("evidence/cew-spiral01/structural-candidate-bridge.json"))
    parser.add_argument("--probe-root", type=Path, default=Path("evidence/cew-spiral01/source-probe"))
    args = parser.parse_args(argv)
    payload = build_exact_source_structural_candidate_bridge(
        ledger_path=args.ledger,
        closure_path=args.closure,
        output_path=args.output,
        probe_root=args.probe_root,
    )
    summary = {
        "status": "PASS",
        "occurrence_count": payload["qualification"]["occurrence_count"],
        "structural_candidate_count": payload["qualification"]["structural_candidate_count"],
        "historical_support_identifier_required": payload["qualification"]["historical_support_identifier_required"],
        "historical_comparator_loaded": payload["qualification"]["historical_comparator_loaded"],
    }
    print("CEW_SPIRAL_STRUCTURAL_CANDIDATE_BRIDGE=" + json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
