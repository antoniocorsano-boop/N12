#!/usr/bin/env python3
"""CEW Civil Existing Workflow — Multi-Mode Existing Assessment Engine v1.

This engine does NOT perform structural analysis and does NOT invent missing
engineering parameters. It compiles an auditable scenario manifest from:
- a project assessment profile,
- the CEW assessment contract,
- a requested assessment mode.

The manifest is the controlled handoff to future deterioration, investigation,
3D-model and solver adapters.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


EVIDENCE_STATES = {"DOC", "MIS", "RIF", "INF", "INC", "ND"}
DERIVED_STATES = {"MOD", "POST"}
ALL_STATES = EVIDENCE_STATES | DERIVED_STATES


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class ModePolicy:
    mode: str
    mode_id: str
    derived_state: str
    requires_probability_model: bool = False
    requires_test_evidence: bool = False


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get_mode_policy(contract: Dict[str, Any], mode: str) -> ModePolicy:
    modes = contract.get("modes", {})
    if mode not in modes:
        raise ContractError(f"Unknown mode {mode!r}; allowed: {sorted(modes)}")
    raw = modes[mode]
    return ModePolicy(
        mode=mode,
        mode_id=raw["id"],
        derived_state=raw["derived_state"],
        requires_probability_model=bool(raw.get("requires_probability_model", False)),
        requires_test_evidence=bool(raw.get("requires_test_evidence", False)),
    )


def validate_claim(claim: Dict[str, Any], idx: int) -> None:
    required = {"claim_id", "domain", "state", "value"}
    missing = required - claim.keys()
    if missing:
        raise ContractError(f"claim[{idx}] missing fields: {sorted(missing)}")
    state = claim["state"]
    if state not in EVIDENCE_STATES:
        raise ContractError(
            f"claim[{idx}] uses {state!r}; project input claims must be source/evidence states, not derived states"
        )
    if state == "ND" and claim["value"] not in (None, "ND"):
        raise ContractError(f"claim[{idx}] state ND must have null or 'ND' value")
    if state != "ND" and not claim.get("provenance"):
        raise ContractError(f"claim[{idx}] non-ND value requires provenance")


def validate_rule(rule: Dict[str, Any], idx: int) -> None:
    required = {"rule_id", "domain", "applicable_modes", "output_state", "assumption_class"}
    missing = required - rule.keys()
    if missing:
        raise ContractError(f"model_rule[{idx}] missing fields: {sorted(missing)}")
    if rule["output_state"] not in DERIVED_STATES:
        raise ContractError(f"model_rule[{idx}] output_state must be MOD or POST")
    if not rule.get("rationale"):
        raise ContractError(f"model_rule[{idx}] requires rationale")


def validate_profile(profile: Dict[str, Any]) -> None:
    for field in ("schema_version", "project_id", "canonical_model_ref", "claims", "model_rules", "blocking_domains"):
        if field not in profile:
            raise ContractError(f"profile missing required field {field!r}")

    for idx, claim in enumerate(profile["claims"]):
        validate_claim(claim, idx)
    for idx, rule in enumerate(profile["model_rules"]):
        validate_rule(rule, idx)

    claim_ids = [c["claim_id"] for c in profile["claims"]]
    if len(claim_ids) != len(set(claim_ids)):
        raise ContractError("duplicate claim_id")
    rule_ids = [r["rule_id"] for r in profile["model_rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        raise ContractError("duplicate rule_id")


def active_rules(profile: Dict[str, Any], policy: ModePolicy) -> List[Dict[str, Any]]:
    rules = []
    for rule in profile["model_rules"]:
        if policy.mode in rule["applicable_modes"]:
            rules.append(rule)
    return rules


def active_probability_models(profile: Dict[str, Any], policy: ModePolicy) -> List[Dict[str, Any]]:
    models = []
    for model in profile.get("probability_models", []):
        if policy.mode in model.get("applicable_modes", []):
            models.append(model)
    return models


def test_evidence(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [c for c in profile["claims"] if c.get("evidence_kind") in {"TEST", "LAB", "IN_SITU_TEST"} and c["state"] in {"MIS", "DOC"}]


def unresolved_domains(profile: Dict[str, Any], policy: ModePolicy, rules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    covered = {rule["domain"] for rule in rules}
    residuals: List[Dict[str, Any]] = []
    modeled: List[Dict[str, Any]] = []

    for item in profile["blocking_domains"]:
        domain = item["domain"]
        if domain in covered:
            matching = [r for r in rules if r["domain"] == domain]
            modeled.append({
                **item,
                "scenario_resolution": "MODELED_NOT_MEASURED",
                "model_rule_ids": [r["rule_id"] for r in matching],
                "derived_state": matching[0]["output_state"],
            })
        else:
            residuals.append({**item, "scenario_resolution": "UNRESOLVED"})

    return residuals, modeled


def determine_authorization(policy: ModePolicy, residuals: List[Dict[str, Any]], probability_models: List[Dict[str, Any]], tests: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    watches: List[str] = []

    if policy.requires_probability_model and not probability_models:
        watches.append("MODE_REQUIRES_PROBABILITY_MODEL_BUT_NONE_IS_ACTIVE")
    if policy.requires_test_evidence and not tests:
        watches.append("MODE_REQUIRES_TEST_EVIDENCE_BUT_NONE_IS_REGISTERED")

    if watches:
        return "NOT_EXECUTABLE", watches

    if policy.mode == "MODE-1":
        return ("COMPARATIVE_ONLY" if not residuals else "NOT_EXECUTABLE"), watches
    if policy.mode == "MODE-2":
        return ("EXECUTABLE_WITH_DECLARED_ASSUMPTIONS" if not residuals else "SCREENING_ONLY"), watches
    if policy.mode == "MODE-3":
        return ("COMPARATIVE_ONLY" if not residuals else "SCREENING_ONLY"), watches
    if policy.mode == "MODE-4":
        return ("EXECUTABLE_WITH_DECLARED_ASSUMPTIONS" if not residuals else "SCREENING_ONLY"), watches
    if policy.mode == "MODE-5":
        return ("CURRENT_STATE_VERIFICATION_ELIGIBLE" if not residuals else "NOT_EXECUTABLE"), watches
    raise AssertionError(policy.mode)


def build_scenario(contract_path: Path, profile_path: Path, mode: str) -> Dict[str, Any]:
    contract = load_json(contract_path)
    profile = load_json(profile_path)
    validate_profile(profile)
    policy = get_mode_policy(contract, mode)

    rules = active_rules(profile, policy)
    prob_models = active_probability_models(profile, policy)
    tests = test_evidence(profile)
    residuals, modeled = unresolved_domains(profile, policy, rules)
    authorization, watches = determine_authorization(policy, residuals, prob_models, tests)

    if any(rule["output_state"] != policy.derived_state for rule in rules):
        watches.append("ACTIVE_RULE_OUTPUT_STATE_DIFFERS_FROM_MODE_DEFAULT")

    now = datetime.now(timezone.utc).isoformat()
    scenario_id = f"{profile['project_id']}_{mode}_{policy.mode_id}"

    evidence_summary: Dict[str, int] = {state: 0 for state in sorted(EVIDENCE_STATES)}
    for claim in profile["claims"]:
        evidence_summary[claim["state"]] += 1

    return {
        "schema_version": "1.0",
        "engine": "CEW_EXISTING_ASSESSMENT_ENGINE_v1",
        "generated_at": now,
        "scenario_id": scenario_id,
        "mode": mode,
        "mode_id": policy.mode_id,
        "canonical_model_ref": profile["canonical_model_ref"],
        "scenario_status": "RESIDUAL" if residuals or watches else "READY_FOR_AUTHORIZED_USE",
        "solver_authorization": authorization,
        "epistemic_guard": {
            "derived_state": policy.derived_state,
            "source_evidence_mutated": False,
            "derived_values_may_promote_to_MIS": False,
            "LC_FC_auto_promoted": False,
        },
        "inputs": {
            "profile": str(profile_path),
            "profile_sha256": sha256_file(profile_path),
            "contract": str(contract_path),
            "contract_sha256": sha256_file(contract_path),
            "evidence_claim_count": len(profile["claims"]),
            "evidence_state_summary": evidence_summary,
            "test_evidence_count": len(tests),
        },
        "model_rules": [
            {
                "rule_id": r["rule_id"],
                "domain": r["domain"],
                "output_state": r["output_state"],
                "assumption_class": r["assumption_class"],
                "rationale": r["rationale"],
            }
            for r in rules
        ],
        "probability_models": [
            {
                "model_id": m["model_id"],
                "mechanism": m["mechanism"],
                "calibration_state": m.get("calibration_state", "UNSPECIFIED"),
                "reference_id": m.get("reference_id"),
            }
            for m in prob_models
        ],
        "modeled_blocking_domains": modeled,
        "residuals": residuals,
        "watches": watches,
        "investigation_candidates": profile.get("investigation_candidates", []),
        "provenance_statement": (
            "Scenario values are derived from registered evidence and explicit model rules. "
            "MOD/POST outputs do not replace DOC/MIS/RIF/INF evidence. Solver authorization "
            "describes permitted use of this scenario and is not a declaration of regulatory LC/FC."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=["MODE-1", "MODE-2", "MODE-3", "MODE-4", "MODE-5"])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        scenario = build_scenario(args.contract, args.profile, args.mode)
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"CEW ASSESSMENT ENGINE: FAIL: {exc}")
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scenario, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "CEW ASSESSMENT ENGINE: PASS | "
        f"scenario={scenario['scenario_id']} | "
        f"status={scenario['scenario_status']} | "
        f"authorization={scenario['solver_authorization']} | "
        f"residuals={len(scenario['residuals'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
