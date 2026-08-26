from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "automation" / "CEW_INVESTIGATION_PLANNER_CONTRACT_v1.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def voi_gate(contract: dict[str, Any], decision_model: dict[str, Any] | None = None) -> dict[str, Any]:
    required = list(contract.get("future_voi_gate", {}).get("required_before_activation", []))
    supplied = decision_model or {}
    missing = [field for field in required if supplied.get(field) in (None, "", [], {})]
    return {
        "status": "READY" if not missing and required else "NOT_READY",
        "required": required,
        "missing": missing,
        "activation_authority": "HUMAN_ENGINEERING_REVIEW_REQUIRED",
    }


def validate_advisory_plan(plan: dict[str, Any], contract: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if plan.get("status") != "ADVISORY_PLAN_NOT_EVIDENCE":
        errors.append("planner output must remain ADVISORY_PLAN_NOT_EVIDENCE")
    if plan.get("value_of_information_ready") is not False:
        errors.append("v0 planner must not claim Value of Information readiness")
    if plan.get("uncovered_blockers"):
        errors.append("investigation plan leaves assessment blockers uncovered")
    candidates = plan.get("candidates", [])
    if not candidates:
        errors.append("investigation plan has no candidates")
    required_fields = set(contract.get("required_candidate_fields", []))
    for index, candidate in enumerate(candidates):
        missing = sorted(required_fields - set(candidate))
        if missing:
            errors.append(f"candidate {index} missing fields: {missing}")
        if candidate.get("ranking_status") != "ADVISORY_NOT_VALUE_OF_INFORMATION":
            errors.append(f"candidate {candidate.get('investigation_id', index)} has unsafe ranking status")
        if not candidate.get("potentially_closes"):
            errors.append(f"candidate {candidate.get('investigation_id', index)} is not bound to an unresolved blocker")
    ranking = contract.get("ranking_v0", {})
    if ranking.get("not_value_of_information") is not True:
        errors.append("contract must explicitly distinguish heuristic ranking from VoI")
    gate = voi_gate(contract)
    if gate["status"] != "NOT_READY" or not gate["missing"]:
        errors.append("future VoI gate must remain closed without a declared decision model")
    return not errors, errors


def adoption_package(plan: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    ok, errors = validate_advisory_plan(plan, contract)
    gate = voi_gate(contract)
    return {
        "schema_version": "0.1.0",
        "work_item_id": "INV-001",
        "status": "PASS" if ok else "FAIL",
        "provider": "cew-investigation-planner",
        "project_id": plan.get("project_id"),
        "planner_status": plan.get("status"),
        "blocker_count": plan.get("blocker_count"),
        "covered_blocker_count": plan.get("covered_blocker_count"),
        "candidate_count": len(plan.get("candidates", [])),
        "ranking_authority": "ADVISORY_ONLY",
        "value_of_information": gate,
        "human_selection_required_before_project_execution": True,
        "planner_creates_evidence": False,
        "planner_assigns_engineering_values": False,
        "canonical_promotion": "DISABLED",
        "errors": errors,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Adopt CEW Investigation Planner into Platform OS without overstating VoI maturity")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    payload = adoption_package(load(a.plan), load(a.contract))
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if payload["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
