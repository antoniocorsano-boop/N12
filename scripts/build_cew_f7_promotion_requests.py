#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_cew_human_decision_receipt.py"
TASKS = ROOT / "data" / "canonical" / "CEW_ERW_RESOLUTION_TASKS_v1.csv"
CEILING = {"DOC_DIRECT_ONLY": "DOC", "INF_STRONG_DRAFTING_RULE": "INF"}
AUTHORITY = "VALIDATED_HUMAN_RECEIPT_TO_PROMOTION_REQUEST_ONLY_NO_CANONICAL_WRITE"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_validator():
    spec = importlib.util.spec_from_file_location("cew_human_receipt_validator", VALIDATOR)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load F7 human receipt validator")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def normalize_receipt(receipt: dict, task_map: dict[str, dict[str, str]]) -> dict:
    validator = load_validator()
    validator.validate(receipt)
    task = task_map[receipt["task_id"]]
    ceiling = CEILING.get(task["epistemic_ceiling"])
    if ceiling is None:
        raise AssertionError("unsupported task epistemic ceiling")

    request = {
        "decision_id": receipt["decision_id"],
        "task_id": receipt["task_id"],
        "residual_id": receipt["residual_id"],
        "outcome": receipt["outcome"],
        "validated_human_decision": True,
        "direct_primary_evidence": receipt["direct_primary_evidence_observed"],
        "requested_epistemic_state": receipt["requested_epistemic_state"],
        "evidence_ceiling": ceiling,
        "target_id": receipt["target_id"] or None,
        "reopen_approval": None,
        "reopen_approval_id": receipt["reopen_approval_id"] or None,
        "human_observation": receipt["human_observation"],
        "evidence_regions": receipt["evidence_regions"],
        "source_versions": receipt["source_versions"],
        "reviewer": receipt["reviewer"],
        "timestamp": receipt["timestamp"],
        "source": "F7_VALIDATED_HUMAN_RECEIPT",
        "canonical_write_authorized": False,
    }
    if receipt.get("fixture_only") is True:
        request["fixture_only"] = True
    if receipt.get("fixture_id"):
        request["fixture_id"] = receipt["fixture_id"]
    return request


def load_receipts(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "receipts" in raw:
        if raw.get("authority") not in (None, "POLICY_CONFORMANCE_ONLY_NOT_A_HUMAN_DECISION_NOT_CANONICAL_EVIDENCE"):
            raise AssertionError("receipt fixture authority drift")
        return list(raw["receipts"])
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list):
        return raw
    raise AssertionError("unsupported receipt bundle shape")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipts", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    task_map = {r["task_id"]: r for r in rows(TASKS)}
    receipts = load_receipts(Path(args.receipts))
    requests = [normalize_receipt(r, task_map) for r in receipts]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    bundle = {
        "schema_version": "1.0",
        "milestone": "CEW-F7",
        "authority": AUTHORITY,
        "requests": requests,
        "canonical_write_performed": False,
    }
    (out / "promotion_requests.json").write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("CEW_F7_HUMAN_RECEIPT_BRIDGE_PASS")
    print(f"VALIDATED_RECEIPTS={len(requests)}")
    print("FREE_TEXT_INFERENCE=FORBIDDEN")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
