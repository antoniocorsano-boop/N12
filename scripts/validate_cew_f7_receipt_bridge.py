#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_VALIDATOR = ROOT / "scripts" / "validate_cew_human_decision_receipt.py"
PATCH_BUILDER = ROOT / "scripts" / "build_cew_canonical_patch_candidates.py"
BRIDGE_AUTHORITY = "VALIDATED_HUMAN_RECEIPT_TO_PROMOTION_REQUEST_ONLY_NO_CANONICAL_WRITE"
BLOCK_REASON = "SEMANTIC_EXPLICIT_DIRECTIONAL_CLAUSES_REQUIRED"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {name}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def must_reject(validator, receipt: dict) -> None:
    try:
        validator.validate(receipt)
    except SystemExit:
        return
    raise AssertionError("negative human receipt was accepted")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--requests", required=True)
    ap.add_argument("--evaluations", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--fixtures", required=True)
    args = ap.parse_args()

    requests = json.loads(Path(args.requests).read_text(encoding="utf-8"))
    evaluations = json.loads(Path(args.evaluations).read_text(encoding="utf-8"))
    candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    fixtures = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))

    if requests.get("authority") != BRIDGE_AUTHORITY or requests.get("canonical_write_performed") is not False:
        raise AssertionError("F7 bridge authority drift")
    reqs = requests.get("requests", [])
    if len(reqs) != 2 or any(r.get("fixture_only") is not True for r in reqs):
        raise AssertionError("F7 bridge fixture inventory drift")
    if any(r.get("validated_human_decision") is not True for r in reqs):
        raise AssertionError("unvalidated receipt crossed bridge")
    if any(r.get("direct_primary_evidence") is not True for r in reqs):
        raise AssertionError("direct primary evidence flag lost in bridge")
    if any(r.get("canonical_write_authorized") is not False for r in reqs):
        raise AssertionError("bridge acquired write authority")

    evals = evaluations.get("human_receipt_evaluations", [])
    if len(evals) != 2:
        raise AssertionError("human receipt evaluations missing")
    if any(e.get("eligible") is not True for e in evals):
        raise AssertionError("valid non-geometry bridge fixture failed epistemic promotion evaluation")
    if any(e.get("terminal_action") != "EMIT_CANONICAL_PATCH_CANDIDATE" for e in evals):
        raise AssertionError("eligible human bridge fixture did not reach patch-candidate boundary")
    if any(e.get("canonical_write_performed") is not False for e in evals):
        raise AssertionError("promotion evaluation performed canonical write")

    if candidates.get("authority") != "PATCH_CANDIDATE_ONLY_NO_CANONICAL_WRITE" or candidates.get("canonical_write_performed") is not False:
        raise AssertionError("patch candidate authority drift")
    if candidates.get("current_n12_patch_candidates") != []:
        raise AssertionError("synthetic bridge fixture masqueraded as current N12 receipt")

    human_candidates = candidates.get("human_receipt_fixture_patch_candidates", [])
    if len(human_candidates) != 1:
        raise AssertionError("expected exactly one lossless directional human-receipt fixture candidate")
    candidate = human_candidates[0]
    if candidate.get("fixture_id") != "CEW-F7-BRIDGE-FIX-DIRECTIONAL":
        raise AssertionError("wrong human bridge fixture became candidate")
    semantic = candidate.get("semantic_payload") or {}
    if semantic.get("kind") != "REINFORCEMENT_ASSERTION":
        raise AssertionError("reinforcement semantic payload kind drift")
    if semantic.get("raw_human_observation") != "2 Φ12 superiori + 2 Φ12 inferiori":
        raise AssertionError("raw human observation not preserved verbatim")
    if semantic.get("upper") != {"count": 2, "diameter_mm": 12}:
        raise AssertionError("upper reinforcement not preserved separately")
    if semantic.get("lower") != {"count": 2, "diameter_mm": 12}:
        raise AssertionError("lower reinforcement not preserved separately")
    if semantic.get("directional_separation_preserved") is not True:
        raise AssertionError("directional separation invariant lost")
    if candidate.get("canonical_write_authorized") is not False or candidate.get("canonical_write_performed") is not False:
        raise AssertionError("human bridge candidate acquired canonical write authority")

    blocks = candidates.get("human_receipt_semantic_blocks", [])
    aggregate = [b for b in blocks if b.get("fixture_id") == "CEW-F7-BRIDGE-FIX-AGGREGATE"]
    if len(aggregate) != 1 or aggregate[0].get("reason_code") != BLOCK_REASON:
        raise AssertionError("generic 4 Φ12 was not fail-closed at semantic boundary")

    validator = load_module("receipt_validator", RECEIPT_VALIDATOR)
    fixture_receipts = fixtures.get("receipts", [])
    base = copy.deepcopy(fixture_receipts[0])
    bad_ack = copy.deepcopy(base)
    bad_ack["authority_acknowledgement"] = "true"
    must_reject(validator, bad_ack)
    no_primary = copy.deepcopy(base)
    no_primary["direct_primary_evidence_observed"] = False
    must_reject(validator, no_primary)
    unknown_target = copy.deepcopy(base)
    unknown_target["target_id"] = "UNREGISTERED-TARGET"
    must_reject(validator, unknown_target)

    patch_builder = load_module("patch_builder", PATCH_BUILDER)
    exact_text = "2 Φ12 superiori + 2 Φ12 inferiori"
    parsed, reason = patch_builder.reinforcement_payload(exact_text)
    if reason is not None or parsed is None:
        raise AssertionError("exact directional form did not parse")
    if parsed.get("raw_human_observation") != exact_text:
        raise AssertionError("exact directional raw observation changed")

    natural_text = "i filari lunghi 1040 son 2 f 12 superiori e 2 f 12 inferiori"
    natural, natural_reason = patch_builder.reinforcement_payload(natural_text)
    if natural_reason is not None or natural is None:
        raise AssertionError("natural explicit directional text did not parse")
    if natural.get("upper") != {"count": 2, "diameter_mm": 12} or natural.get("lower") != {"count": 2, "diameter_mm": 12}:
        raise AssertionError("natural explicit directional semantics drifted")
    if natural.get("raw_human_observation") != natural_text:
        raise AssertionError("natural raw human observation not preserved verbatim")

    parsed_generic, generic_reason = patch_builder.reinforcement_payload("4 Φ12")
    if parsed_generic is not None or generic_reason != BLOCK_REASON:
        raise AssertionError("generic reinforcement total was semantically inferred")

    print("CEW_F7_HUMAN_RECEIPT_BRIDGE_VALIDATION_PASS")
    print("VALIDATED_RECEIPT_TO_PROMOTION_REQUEST=PASS")
    print("PROMOTION_EVALUATE_REUSED_UNCHANGED=PASS")
    print("UPPER_REINFORCEMENT=2x12_PRESERVED")
    print("LOWER_REINFORCEMENT=2x12_PRESERVED")
    print("NATURAL_DIRECTIONAL_TEXT=PASS_RAW_PRESERVED")
    print("GENERIC_4x12_COLLAPSE=REJECTED")
    print("NEGATIVE_RECEIPT_GUARDS=3/3_REJECTED")
    print("CURRENT_N12_CANONICAL_PATCH=0")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
