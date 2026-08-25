#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_PROMOTION_ENGINE_CONTRACT_v1.json"
TARGETS = ROOT / "data" / "canonical" / "CEW_PROMOTION_TARGET_REGISTRY_v1.csv"
MILESTONES = ROOT / "data" / "canonical" / "CEW_SYSTEM_MILESTONES_v1.csv"
ENGINE = ROOT / "scripts" / "run_cew_promotion_engine.py"


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_engine():
    spec = importlib.util.spec_from_file_location("cew_promotion_engine", ENGINE)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load promotion engine")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--evaluations", required=True); args = ap.parse_args()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    bundle = json.loads(Path(args.evaluations).read_text(encoding="utf-8"))
    inv = contract["authority_invariants"]
    required_false = [
        "engine_may_impersonate_human_reviewer",
        "engine_may_promote_unreadable_or_unbound",
        "engine_may_promote_rejected_candidate",
        "engine_may_exceed_evidence_ceiling",
        "engine_may_invent_canonical_target",
        "engine_may_write_canonical_directly",
        "engine_may_modify_f2_geometry",
        "engine_may_reopen_m0g_without_protocol"
    ]
    if any(inv[k] is not False for k in required_false): raise AssertionError("F7 authority invariant weakened")
    if inv["direct_primary_evidence_required"] is not True or inv["validated_human_decision_required"] is not True: raise AssertionError("F7 promotion prerequisites weakened")
    ms = {r["milestone_id"].strip(): r["status"].strip() for r in rows(MILESTONES)}
    if any(ms.get(x) != "COMPLETE" for x in ("CEW-F0","CEW-F1","CEW-F2","CEW-F3","CEW-F4","CEW-F5","CEW-F6")) or ms.get("CEW-F7") != "IN_PROGRESS": raise AssertionError("F7 milestone governance invalid")
    if bundle.get("authority") != "PROMOTION_EVALUATION_ONLY_NO_CANONICAL_WRITE" or bundle.get("canonical_write_performed") is not False: raise AssertionError("engine gained canonical write authority")

    current = bundle.get("current_n12", [])
    if len(current) != 4: raise AssertionError("current N12 decision inventory must remain 4")
    if any(x["eligible"] for x in current): raise AssertionError("current retained residual became promotable")
    if any(x["terminal_action"] != "RETAIN_RESIDUAL" for x in current): raise AssertionError("current N12 residual not retained")
    reason_inventory = {r for x in current for r in x["reason_codes"]}
    for required in ("VALIDATED_HUMAN_DECISION_REQUIRED", "DIRECT_PRIMARY_EVIDENCE_REQUIRED", "OUTCOME_NOT_PROMOTABLE", "TERMINAL_NON_PROMOTABLE_OUTCOME", "REGISTERED_ACTIVE_TARGET_REQUIRED"):
        if required not in reason_inventory: raise AssertionError(f"current N12 guard missing: {required}")

    fixtures = {x["fixture_id"]: x for x in bundle.get("policy_fixtures", [])}
    if set(fixtures) != {"CEW-F7-FIX-ELIGIBLE-NONGEOMETRY", "CEW-F7-FIX-GEOMETRY-NO-REOPEN"}: raise AssertionError("policy fixture set drift")
    positive = fixtures["CEW-F7-FIX-ELIGIBLE-NONGEOMETRY"]
    if positive["eligible"] is not True or positive["terminal_action"] != "EMIT_CANONICAL_PATCH_CANDIDATE" or positive["canonical_write_performed"] is not False: raise AssertionError("eligible policy path failed")
    blocked = fixtures["CEW-F7-FIX-GEOMETRY-NO-REOPEN"]
    if blocked["eligible"] is not False or "APPROVED_GEOMETRY_REOPEN_REQUIRED" not in blocked["reason_codes"] or blocked["terminal_action"] != "RETAIN_RESIDUAL": raise AssertionError("geometry reopen guard failed")
    if any(x.get("fixture_only") is not True for x in fixtures.values()): raise AssertionError("policy fixture masquerades as production decision")

    mod = load_engine()
    targets = {r["target_id"].strip(): r for r in rows(TARGETS)}
    base = {
        "decision_id": "NEGATIVE-GUARD",
        "outcome": "CONFIRMED",
        "validated_human_decision": True,
        "direct_primary_evidence": True,
        "requested_epistemic_state": "DOC",
        "evidence_ceiling": "DOC",
        "target_id": "CEW-TARGET-REINFORCEMENT-OBSERVATION",
        "reopen_approval": None
    }
    negatives = [
        {**base, "validated_human_decision": False},
        {**base, "direct_primary_evidence": False},
        {**base, "outcome": "UNREADABLE"},
        {**base, "outcome": "UNBOUND"},
        {**base, "requested_epistemic_state": "DOC", "evidence_ceiling": "INF"},
        {**base, "target_id": "UNREGISTERED-TARGET"},
        {**base, "target_id": "CEW-TARGET-STRUCTURAL-BINDING"}
    ]
    results = [mod.evaluate(x, targets) for x in negatives]
    if any(r["eligible"] for r in results): raise AssertionError("negative promotion guard accepted")
    expected_codes = {
        "VALIDATED_HUMAN_DECISION_REQUIRED",
        "DIRECT_PRIMARY_EVIDENCE_REQUIRED",
        "TERMINAL_NON_PROMOTABLE_OUTCOME",
        "EPISTEMIC_CEILING_EXCEEDED",
        "REGISTERED_ACTIVE_TARGET_REQUIRED",
        "APPROVED_GEOMETRY_REOPEN_REQUIRED"
    }
    got = {code for r in results for code in r["reason_codes"]}
    if not expected_codes.issubset(got): raise AssertionError(f"negative guard coverage incomplete: {sorted(expected_codes-got)}")

    print("PROMOTION_ENGINE_SLICE_PASS")
    print("CURRENT_N12_DECISIONS=4")
    print("CURRENT_N12_PROMOTIONS=0")
    print("CURRENT_N12_ACTION=RETAIN_RESIDUAL")
    print("POLICY_ELIGIBLE_PATCH_CANDIDATE=PASS")
    print("POLICY_FIXTURE_IS_NOT_HUMAN_DECISION=PASS")
    print("NEGATIVE_PROMOTION_GUARDS=7/7_REJECTED")
    print("GEOMETRY_REOPEN_GUARD=PASS")
    print("CANONICAL_WRITE_BY_ENGINE=FORBIDDEN")
    print("F2_GEOMETRY_MUTATION=FORBIDDEN")
    print("M0G_REOPEN_WITHOUT_PROTOCOL=FORBIDDEN")
    return 0

if __name__ == "__main__": raise SystemExit(main())
