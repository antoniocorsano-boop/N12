#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def writer_admission(candidate: dict) -> tuple[bool, list[str]]:
    reasons = []
    if candidate.get("source_authority") != "VALIDATED_HUMAN_DIRECT_PRIMARY":
        reasons.append("AUTHORITATIVE_HUMAN_DIRECT_PRIMARY_REQUIRED")
    if candidate.get("canonical_write_authorized") is not True:
        reasons.append("EXPLICIT_WRITE_AUTHORIZATION_REQUIRED")
    if not candidate.get("canonical_locator"):
        reasons.append("CANONICAL_LOCATOR_REQUIRED")
    if not candidate.get("operation"):
        reasons.append("CANONICAL_OPERATION_REQUIRED")
    return (len(reasons) == 0, reasons)


def assert_not_admitted(candidate: dict, require_source_guard: bool) -> None:
    ok, reasons = writer_admission(candidate)
    if ok:
        raise AssertionError("governed writer admitted non-authorized patch candidate")
    if "EXPLICIT_WRITE_AUTHORIZATION_REQUIRED" not in reasons:
        raise AssertionError("explicit write authorization guard missing")
    if require_source_guard and "AUTHORITATIVE_HUMAN_DIRECT_PRIMARY_REQUIRED" not in reasons:
        raise AssertionError("authoritative human source guard missing")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    a = ap.parse_args()
    b = json.loads(Path(a.candidates).read_text(encoding="utf-8"))
    if b.get("authority") != "PATCH_CANDIDATE_ONLY_NO_CANONICAL_WRITE" or b.get("canonical_write_performed") is not False:
        raise AssertionError("candidate bundle authority drift")

    current = b.get("current_n12_patch_candidates", [])
    for c in current:
        if c.get("source_authority") != "VALIDATED_HUMAN_DIRECT_PRIMARY":
            raise AssertionError("current N12 candidate lacks validated human direct-primary authority")
        assert_not_admitted(c, require_source_guard=False)

    fixtures = b.get("policy_fixture_patch_candidates", [])
    if len(fixtures) != 1:
        raise AssertionError("expected exactly one positive policy fixture patch candidate")
    for c in fixtures:
        assert_not_admitted(c, require_source_guard=True)

    human_fixtures = b.get("human_receipt_fixture_patch_candidates", [])
    for c in human_fixtures:
        if c.get("source_authority") != "POLICY_FIXTURE_ONLY":
            raise AssertionError("human receipt fixture masquerades as authoritative human data")
        assert_not_admitted(c, require_source_guard=True)

    synthetic_authoritative = {
        "canonical_locator": "DERIVED_CANONICAL_PROJECTION/REINFORCEMENT",
        "operation": "ADD_OR_REPLACE_ASSERTION",
        "source_authority": "VALIDATED_HUMAN_DIRECT_PRIMARY",
        "canonical_write_authorized": True,
    }
    ok, reasons = writer_admission(synthetic_authoritative)
    if not ok or reasons:
        raise AssertionError("writer policy shape rejects fully authoritative synthetic admission")

    print("GOVERNED_WRITER_BOUNDARY_PASS")
    print(f"CURRENT_N12_PATCH_CANDIDATES={len(current)}")
    print("CURRENT_N12_PATCH_CANDIDATES_WRITE_AUTHORIZED=0")
    print("POLICY_FIXTURE_CANDIDATES_REJECTED=1/1")
    print(f"HUMAN_RECEIPT_FIXTURE_CANDIDATES_REJECTED={len(human_fixtures)}/{len(human_fixtures)}")
    print("HUMAN_DIRECT_PRIMARY_REQUIRED=PASS")
    print("EXPLICIT_WRITE_AUTHORIZATION_REQUIRED=PASS")
    print("SYNTHETIC_AUTHORITATIVE_POLICY_SHAPE=ADMISSIBLE_NOT_EXECUTED")
    print("CANONICAL_WRITE_EXECUTED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
