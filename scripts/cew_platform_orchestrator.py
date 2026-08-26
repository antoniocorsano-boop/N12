from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "automation" / "CEW_PLATFORM_WORK_QUEUE_v0.json"
CONTRACT_PATH = ROOT / "automation" / "CEW_AGENT_RESULT_CONTRACT_v0.json"

VALID_STATUSES = {
    "COMPLETE",
    "READY",
    "WAITING",
    "BLOCKED_EVIDENCE",
    "BLOCKED_CANONICAL_GATE",
    "BLOCKED_HUMAN_DECISION",
    "FAIL_STOP",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate() -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not QUEUE_PATH.is_file():
        return False, [f"missing queue: {QUEUE_PATH}"]
    if not CONTRACT_PATH.is_file():
        return False, [f"missing result contract: {CONTRACT_PATH}"]

    queue = load_json(QUEUE_PATH)
    contract = load_json(CONTRACT_PATH)
    items = queue.get("items", [])
    ids = [item.get("id") for item in items]

    if not items:
        errors.append("queue has no items")
    if None in ids:
        errors.append("every work item must have id")
    if len(ids) != len(set(ids)):
        errors.append("duplicate work item ids")

    idset = set(ids)
    for item in items:
        wid = item.get("id", "<missing>")
        status = item.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{wid}: invalid status {status}")
        for dep in item.get("depends_on", []):
            if dep not in idset:
                errors.append(f"{wid}: unknown dependency {dep}")
        if not item.get("completion"):
            errors.append(f"{wid}: no completion criteria")

    outcomes = set(contract.get("allowed_outcomes", []))
    required_outcomes = {
        "COMPLETE_PASS",
        "COMPLETE_PASS_WITH_REVIEW",
        "BLOCKED_HUMAN_DECISION",
        "BLOCKED_EVIDENCE",
        "BLOCKED_CANONICAL_GATE",
        "FAIL_STOP",
    }
    missing_outcomes = required_outcomes - outcomes
    if missing_outcomes:
        errors.append(f"result contract missing outcomes: {sorted(missing_outcomes)}")

    required_fields = set(contract.get("required_fields", []))
    for field in {"work_item_id", "outcome", "head_sha", "outputs", "gates", "residuals"}:
        if field not in required_fields:
            errors.append(f"result contract missing required field: {field}")

    return not errors, errors


def dependency_complete(item: dict, by_id: dict[str, dict]) -> bool:
    return all(by_id[dep].get("status") == "COMPLETE" for dep in item.get("depends_on", []))


def eligible_items(queue: dict) -> list[dict]:
    items = queue.get("items", [])
    by_id = {item["id"]: item for item in items}
    return [
        item
        for item in items
        if item.get("status") == "READY" and dependency_complete(item, by_id)
    ]


def cmd_validate(_: argparse.Namespace) -> int:
    ok, errors = validate()
    payload = {
        "status": "PASS" if ok else "FAIL",
        "queue": str(QUEUE_PATH.relative_to(ROOT)),
        "result_contract": str(CONTRACT_PATH.relative_to(ROOT)),
        "errors": errors,
        "canonical_promotion": "DISABLED",
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if ok else 2


def cmd_status(_: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue = load_json(QUEUE_PATH)
    counts: dict[str, int] = {}
    for item in queue["items"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    eligible = eligible_items(queue)
    print(
        json.dumps(
            {
                "status": "PASS",
                "queue_status": queue.get("status"),
                "canonical_boundary": queue.get("canonical_boundary"),
                "counts": counts,
                "eligible": [
                    {"id": x["id"], "title": x["title"], "workstream": x["workstream"]}
                    for x in eligible
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_next(_: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue = load_json(QUEUE_PATH)
    eligible = eligible_items(queue)
    if not eligible:
        print(json.dumps({"status": "NO_ELIGIBLE_WORK", "canonical_promotion": "DISABLED"}, indent=2))
        return 0
    item = eligible[0]
    print(
        json.dumps(
            {
                "status": "READY_FOR_AGENT",
                "work_item": item,
                "result_contract": str(CONTRACT_PATH.relative_to(ROOT)),
                "communication_protocol": queue.get("communication_protocol"),
                "instruction": "Complete the coherent work item end-to-end; self-repair technical failures; stop only on a contract outcome.",
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_result_template(args: argparse.Namespace) -> int:
    ok, errors = validate()
    if not ok:
        print(json.dumps({"status": "FAIL", "errors": errors}, indent=2, ensure_ascii=False))
        return 2
    queue = load_json(QUEUE_PATH)
    by_id = {item["id"]: item for item in queue["items"]}
    if args.work_item_id not in by_id:
        print(json.dumps({"status": "FAIL", "error": "unknown work item"}, indent=2))
        return 2
    template = {
        "work_item_id": args.work_item_id,
        "outcome": "",
        "repository": "antoniocorsano-boop/N12",
        "branch": "",
        "head_sha": "",
        "input_generations": [],
        "outputs": [],
        "gates": [],
        "residuals": [],
        "human_decisions": [],
        "next_eligible_action": "",
    }
    print(json.dumps(template, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CEW Platform OS deterministic orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("next")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("result-template")
    p.add_argument("work_item_id")
    p.set_defaults(func=cmd_result_template)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
