#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_ERW_CONTRACT_v1.json"
REGISTRY = ROOT / "knowledge" / "ARTIFACT_REGISTRY_CEW_SOURCE_VIEWER_PATCH_v1.csv"
ORDER = {"ND": 0, "INF": 1, "RIF": 2, "MIS": 3, "DOC": 4}


def evaluate(*, human: bool, outcome: str, direct_primary: bool, requested: str | None, ceiling: str, rejected_candidate: bool = False) -> tuple[bool, list[str]]:
    reasons=[]
    if not human: reasons.append("HUMAN_DECISION_REQUIRED")
    if outcome in {"UNREADABLE","UNBOUND"}: reasons.append("TERMINAL_NON_PROMOTABLE_OUTCOME")
    if outcome == "REJECTED" or rejected_candidate: reasons.append("REJECTED_CANDIDATE")
    if not direct_primary: reasons.append("DIRECT_PRIMARY_EVIDENCE_REQUIRED")
    if requested is None: reasons.append("REQUESTED_EPISTEMIC_STATE_REQUIRED")
    elif requested not in ORDER or ceiling not in ORDER or ORDER[requested] > ORDER[ceiling]: reasons.append("EPISTEMIC_CEILING_EXCEEDED")
    return (len(reasons)==0, reasons)


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--queue-bundle",required=True); ap.add_argument("--receipts",required=True); args=ap.parse_args()
    contract=json.loads(CONTRACT.read_text(encoding="utf-8")); queue=json.loads(Path(args.queue_bundle).read_text(encoding="utf-8")); bundle=json.loads(Path(args.receipts).read_text(encoding="utf-8"))
    b=contract["decision_promotion_boundary"]
    required_false=["reference_or_machine_conformance_decision_may_promote","unreadable_or_unbound_may_promote","rejected_candidate_may_promote","promotion_gate_may_write_canonical_directly"]
    if any(b[k] is not False for k in required_false): raise AssertionError("decision boundary weakened")
    if b["human_decision_required_for_promotion_request"] is not True or b["direct_primary_evidence_required_for_promotion"] is not True: raise AssertionError("promotion prerequisites weakened")
    if bundle.get("human_decisions_present") is not False or bundle.get("canonical_write_performed") is not False: raise AssertionError("conformance bundle claims human/canonical authority")
    ds=bundle.get("decisions",[]); ws=queue.get("workspaces",[])
    if len(ds)!=4 or len(ws)!=4: raise AssertionError("4/4 E2E coverage required")
    expected={w["task"]["task_id"]:w["reference_disposition_receipt"]["outcome"] for w in ws}
    for item in ds:
        d=item["decision"]; r=item["promotion_eligibility_receipt"]
        if d["review_mode"]!="NON_HUMAN_CONFORMANCE" or d["reviewer"]!="REFERENCE_NON_HUMAN_CONFORMANCE": raise AssertionError("fixture impersonates human reviewer")
        if d["outcome"]!=expected[d["task_id"]]: raise AssertionError("decision outcome drift from bounded queue")
        if r["eligible"] is not False or r["canonical_write_requested"] is not False or r["canonical_write_performed"] is not False or r["terminal_action"]!="RETAIN_RESIDUAL": raise AssertionError("current residual was promoted")
    outcomes=sorted(d["decision"]["outcome"] for d in ds)
    if outcomes!=["UNBOUND","UNREADABLE","UNREADABLE","UNREADABLE"]: raise AssertionError("current terminal disposition inventory drift")

    negative=[
      evaluate(human=False,outcome="CONFIRMED",direct_primary=True,requested="DOC",ceiling="DOC"),
      evaluate(human=True,outcome="CONFIRMED",direct_primary=False,requested="DOC",ceiling="DOC"),
      evaluate(human=True,outcome="CONFIRMED",direct_primary=True,requested="DOC",ceiling="INF"),
      evaluate(human=True,outcome="UNBOUND",direct_primary=True,requested="DOC",ceiling="DOC"),
      evaluate(human=True,outcome="REJECTED",direct_primary=True,requested="DOC",ceiling="DOC",rejected_candidate=True),
    ]
    if any(ok for ok,_ in negative): raise AssertionError("negative promotion guard accepted")
    positive=evaluate(human=True,outcome="CONFIRMED",direct_primary=True,requested="DOC",ceiling="DOC")
    if positive!=(True,[]): raise AssertionError("eligible human/direct-evidence conformance case rejected")
    # Even a synthetically eligible request is only an eligibility result, never a canonical write.
    if b["promotion_gate_output"]!="PROMOTION_ELIGIBILITY_RECEIPT_ONLY" or b["canonical_update_requires_separate_governed_write"] is not True: raise AssertionError("promotion gate gained write authority")
    registry=REGISTRY.read_text(encoding="utf-8")
    if "CI-CEW-ERW-003" not in registry or "32887439649" not in registry or "2583f56df14b95ff09e03d6e3e892203ca0e50b5e56a431f99db3ea4acb7ff55" not in registry: raise AssertionError("certified synchronized workspace evidence not registered")
    print("ERW_E2E_PASS")
    print("TASKS=4/4")
    print("CURRENT_TERMINAL_DISPOSITIONS=3_UNREADABLE+1_UNBOUND")
    print("CURRENT_PROMOTIONS=0")
    print("NEGATIVE_PROMOTION_GUARDS=5/5_REJECTED")
    print("POSITIVE_POLICY_CONFORMANCE=ELIGIBILITY_ONLY")
    print("HUMAN_DECISION_REQUIRED=YES")
    print("DIRECT_PRIMARY_EVIDENCE_REQUIRED=YES")
    print("CANONICAL_WRITE_BY_GATE=FORBIDDEN")
    print("M0G_REOPEN=FORBIDDEN")
    return 0

if __name__=="__main__": raise SystemExit(main())
