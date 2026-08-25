#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def writer_admission(candidate: dict) -> tuple[bool,list[str]]:
    reasons=[]
    if candidate.get("source_authority") != "VALIDATED_HUMAN_DIRECT_PRIMARY": reasons.append("AUTHORITATIVE_HUMAN_DIRECT_PRIMARY_REQUIRED")
    if candidate.get("canonical_write_authorized") is not True: reasons.append("EXPLICIT_WRITE_AUTHORIZATION_REQUIRED")
    if not candidate.get("canonical_locator"): reasons.append("CANONICAL_LOCATOR_REQUIRED")
    if not candidate.get("operation"): reasons.append("CANONICAL_OPERATION_REQUIRED")
    return (len(reasons)==0,reasons)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--candidates",required=True); a=ap.parse_args()
    b=json.loads(Path(a.candidates).read_text(encoding="utf-8"))
    if b.get("authority")!="PATCH_CANDIDATE_ONLY_NO_CANONICAL_WRITE" or b.get("canonical_write_performed") is not False: raise AssertionError("candidate bundle authority drift")
    if b.get("current_n12_patch_candidates")!=[]: raise AssertionError("current N12 patch candidate unexpectedly exists")
    fixtures=b.get("policy_fixture_patch_candidates",[])
    if len(fixtures)!=1: raise AssertionError("expected exactly one positive policy fixture patch candidate")
    admitted=[]
    for c in fixtures:
        ok,reasons=writer_admission(c)
        admitted.append(ok)
        if ok: raise AssertionError("governed writer admitted policy fixture")
        if "AUTHORITATIVE_HUMAN_DIRECT_PRIMARY_REQUIRED" not in reasons or "EXPLICIT_WRITE_AUTHORIZATION_REQUIRED" not in reasons: raise AssertionError("writer rejection reasons incomplete")
    synthetic_authoritative={
        "canonical_locator":"DERIVED_CANONICAL_PROJECTION/REINFORCEMENT",
        "operation":"ADD_OR_REPLACE_ASSERTION",
        "source_authority":"VALIDATED_HUMAN_DIRECT_PRIMARY",
        "canonical_write_authorized":True
    }
    ok,reasons=writer_admission(synthetic_authoritative)
    if not ok or reasons: raise AssertionError("writer policy shape rejects fully authoritative synthetic admission")
    print("GOVERNED_WRITER_BOUNDARY_PASS")
    print("CURRENT_N12_PATCH_CANDIDATES=0")
    print("POLICY_FIXTURE_CANDIDATES_REJECTED=1/1")
    print("HUMAN_DIRECT_PRIMARY_REQUIRED=PASS")
    print("EXPLICIT_WRITE_AUTHORIZATION_REQUIRED=PASS")
    print("SYNTHETIC_AUTHORITATIVE_POLICY_SHAPE=ADMISSIBLE_NOT_EXECUTED")
    print("CANONICAL_WRITE_EXECUTED=0")
    return 0
if __name__=="__main__": raise SystemExit(main())
