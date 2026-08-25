#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_ERW_CONTRACT_v1.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue-bundle", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    queue = json.loads(Path(args.queue_bundle).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    decisions = []
    for w in queue["workspaces"]:
        task = w["task"]
        disp = w["reference_disposition_receipt"]
        outcome = disp["outcome"]
        reasons = ["NON_HUMAN_CONFORMANCE_DECISION"]
        if outcome == "UNREADABLE":
            reasons.append("UNREADABLE_CANNOT_PROMOTE")
        elif outcome == "UNBOUND":
            reasons.append("UNBOUND_CANNOT_PROMOTE")
        else:
            reasons.append("REFERENCE_DISPOSITION_NOT_PROMOTABLE")
        decision_id = f"CEW-F6-CONFORMANCE-{task['task_id']}"
        decisions.append({
            "decision": {
                "decision_id": decision_id,
                "task_id": task["task_id"],
                "outcome": outcome,
                "selected_candidate": None,
                "human_observation": None,
                "reason": "Reference conformance receipt mirrors the evidence-bounded terminal disposition; it is not a human adjudication.",
                "evidence_regions": list(task["source_regions"]),
                "review_view": "SYNCHRONIZED_ERW_REFERENCE",
                "requested_epistemic_state": None,
                "reviewer": "REFERENCE_NON_HUMAN_CONFORMANCE",
                "timestamp": None,
                "review_mode": "NON_HUMAN_CONFORMANCE"
            },
            "promotion_eligibility_receipt": {
                "receipt_id": f"PE-{decision_id}",
                "decision_id": decision_id,
                "eligible": False,
                "reason_codes": reasons,
                "requested_epistemic_state": None,
                "evidence_ceiling": w["source"]["observation"].get("epistemic_state", "ND"),
                "canonical_write_requested": False,
                "canonical_write_performed": False,
                "terminal_action": "RETAIN_RESIDUAL"
            }
        })

    bundle = {
        "schema_version": "1.0",
        "contract_id": contract["contract_id"],
        "milestone": contract["milestone"],
        "authority": "DERIVED_CONFORMANCE_RECEIPTS_ONLY",
        "human_decisions_present": False,
        "canonical_write_performed": False,
        "decisions": decisions
    }
    path = out / "decision_receipts.json"
    path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    print("ERW_DECISION_RECEIPTS_BUILT")
    print(f"DECISIONS={len(decisions)}")
    print("HUMAN_DECISIONS=0")
    print("PROMOTABLE_DECISIONS=0")
    print("TERMINAL_ACTION=RETAIN_RESIDUAL")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
