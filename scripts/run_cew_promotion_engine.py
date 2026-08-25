#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_PROMOTION_ENGINE_CONTRACT_v1.json"
TARGETS = ROOT / "data" / "canonical" / "CEW_PROMOTION_TARGET_REGISTRY_v1.csv"
ORDER = {"ND": 0, "INF": 1, "RIF": 2, "MIS": 3, "DOC": 4}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def epi(raw: str | None) -> str:
    u = (raw or "ND").strip().upper()
    for state in ("DOC", "MIS", "RIF", "INF", "ND"):
        if u.startswith(state):
            return state
    return "ND"


def evaluate(req: dict, targets: dict[str, dict[str, str]]) -> dict:
    reasons: list[str] = []
    outcome = (req.get("outcome") or "").strip().upper()
    requested = epi(req.get("requested_epistemic_state")) if req.get("requested_epistemic_state") else None
    ceiling = epi(req.get("evidence_ceiling"))
    target_id = req.get("target_id")
    target = targets.get(target_id or "")

    if req.get("validated_human_decision") is not True:
        reasons.append("VALIDATED_HUMAN_DECISION_REQUIRED")
    if req.get("direct_primary_evidence") is not True:
        reasons.append("DIRECT_PRIMARY_EVIDENCE_REQUIRED")
    if outcome != "CONFIRMED":
        reasons.append("OUTCOME_NOT_PROMOTABLE")
    if outcome in {"UNREADABLE", "UNBOUND", "REJECTED", "NEEDS_BETTER_SOURCE", "NEEDS_SITE_SURVEY", "DEFER"}:
        reasons.append("TERMINAL_NON_PROMOTABLE_OUTCOME")
    if requested is None:
        reasons.append("REQUESTED_EPISTEMIC_STATE_REQUIRED")
    elif ORDER[requested] > ORDER[ceiling]:
        reasons.append("EPISTEMIC_CEILING_EXCEEDED")
    if target is None or target.get("status", "").strip() != "ACTIVE":
        reasons.append("REGISTERED_ACTIVE_TARGET_REQUIRED")
    elif requested is not None and ORDER[requested] > ORDER[epi(target.get("max_epistemic_state"))]:
        reasons.append("TARGET_EPISTEMIC_CEILING_EXCEEDED")

    reopen_required = bool(target and target.get("geometry_sensitive", "").strip().upper() == "YES")
    reopen = req.get("reopen_approval")
    reopen_satisfied = not reopen_required
    if reopen_required:
        reopen_satisfied = bool(
            isinstance(reopen, dict)
            and reopen.get("approved") is True
            and reopen.get("impact_analysis_receipt")
            and reopen.get("reviewer")
        )
        if not reopen_satisfied:
            reasons.append("APPROVED_GEOMETRY_REOPEN_REQUIRED")

    eligible = len(reasons) == 0
    return {
        "receipt_id": "PROMOTION-EVAL-" + req["decision_id"],
        "decision_id": req["decision_id"],
        "eligible": eligible,
        "reason_codes": reasons,
        "terminal_action": "EMIT_CANONICAL_PATCH_CANDIDATE" if eligible else "RETAIN_RESIDUAL",
        "target_id": target_id,
        "requested_epistemic_state": requested,
        "evidence_ceiling": ceiling,
        "canonical_write_performed": False,
        "reopen_required": reopen_required,
        "reopen_satisfied": reopen_satisfied,
        "authority": "PROMOTION_EVALUATION_ONLY_NO_CANONICAL_WRITE"
    }


def current_requests(receipts: dict) -> list[dict]:
    out = []
    for item in receipts.get("decisions", []):
        d = item["decision"]
        e = item["promotion_eligibility_receipt"]
        out.append({
            "decision_id": d["decision_id"],
            "task_id": d["task_id"],
            "outcome": d["outcome"],
            "validated_human_decision": d.get("review_mode") == "HUMAN_REVIEW" and bool(d.get("reviewer")),
            "direct_primary_evidence": False,
            "requested_epistemic_state": d.get("requested_epistemic_state"),
            "evidence_ceiling": e.get("evidence_ceiling", "ND"),
            "target_id": None,
            "reopen_approval": None,
            "source": "CURRENT_F6_RESOLUTION_RECEIPT"
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipts", required=True)
    ap.add_argument("--fixtures")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("milestone") != "CEW-F7":
        raise AssertionError("promotion engine contract not F7")
    targets = {r["target_id"].strip(): r for r in rows(TARGETS)}
    receipts = json.loads(Path(args.receipts).read_text(encoding="utf-8"))
    current = [evaluate(r, targets) for r in current_requests(receipts)]

    fixtures = []
    if args.fixtures:
        fixture_bundle = json.loads(Path(args.fixtures).read_text(encoding="utf-8"))
        if fixture_bundle.get("authority") != "POLICY_CONFORMANCE_ONLY_NOT_A_HUMAN_DECISION_NOT_CANONICAL_EVIDENCE":
            raise AssertionError("fixture authority drift")
        for f in fixture_bundle.get("fixtures", []):
            result = evaluate(f, targets)
            result["fixture_id"] = f["fixture_id"]
            result["fixture_only"] = True
            result["expected_eligible"] = f["expected_eligible"]
            result["expected_terminal_action"] = f["expected_terminal_action"]
            fixtures.append(result)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    bundle = {
        "schema_version": "1.0",
        "contract_id": contract["contract_id"],
        "milestone": "CEW-F7",
        "authority": "PROMOTION_EVALUATION_ONLY_NO_CANONICAL_WRITE",
        "current_n12": current,
        "policy_fixtures": fixtures,
        "canonical_write_performed": False
    }
    (out / "promotion_evaluations.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    print("CEW_PROMOTION_ENGINE_EVALUATED")
    print(f"CURRENT_N12_DECISIONS={len(current)}")
    print(f"CURRENT_N12_ELIGIBLE={sum(1 for x in current if x['eligible'])}")
    print(f"POLICY_FIXTURES={len(fixtures)}")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
