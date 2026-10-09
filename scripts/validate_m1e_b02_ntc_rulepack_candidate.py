#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "analysis" / "cew" / "N12_M1E_B02_NTC_RULEPACK_CANDIDATE_v1.csv"
GATE = ROOT / "analysis" / "cew" / "N12_M1E_B02_NTC_RULEPACK_GATE_v1.csv"
B02 = ROOT / "data" / "canonical" / "M1E_B02_LOAD_RESIDUAL_REGISTER_v1.csv"

EXPECTED_RULE_IDS = {
    "B02-RP-001-RC-UNIT-WEIGHT",
    "B02-RP-002-RESIDENTIAL-USE",
    "B02-RP-003-STAIRS-BALCONIES-USE",
    "B02-RP-004-ROOF-USE-GUARD",
    "B02-RP-005-SEISMIC-MASS-RULE",
    "B02-RP-006-COMBINATION-RULE",
    "B02-RP-007-EXISTING-BUILDING-GUARD",
}
EXPECTED_TARGETS = {
    "M1L-LM-002", "M1L-LM-005", "M1L-LM-008", "M1L-LM-012", "M1L-LM-015", "M1L-LM-016"
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for path in (RULES, GATE, B02):
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    rules = read_csv(RULES)
    gate = read_csv(GATE)
    b02_ids = {r.get("load_id", "").strip() for r in read_csv(B02)}

    required = {
        "rule_id", "target_load_ids", "rule_kind", "official_source", "source_locator",
        "candidate_expression", "candidate_unit", "applicability_condition", "status",
        "may_assign_model_value", "required_decision", "forbidden_automatic_use", "note",
    }
    if not rules or not required.issubset(rules[0].keys()):
        errors.append("rulepack columns are missing or rulepack is empty")

    ids = {r.get("rule_id", "").strip() for r in rules}
    if ids != EXPECTED_RULE_IDS:
        errors.append(f"rule identity set mismatch: missing={sorted(EXPECTED_RULE_IDS-ids)} extra={sorted(ids-EXPECTED_RULE_IDS)}")

    targeted: set[str] = set()
    for row in rules:
        rid = row.get("rule_id", "<missing>")
        if row.get("status") != "PROPOSE_ONLY_NOT_ADOPTED":
            errors.append(f"{rid}: status must remain PROPOSE_ONLY_NOT_ADOPTED")
        if row.get("may_assign_model_value") != "NO":
            errors.append(f"{rid}: may_assign_model_value must be NO")
        if row.get("required_decision") != "HUMAN_PROFESSIONAL_ADOPTION":
            errors.append(f"{rid}: requires HUMAN_PROFESSIONAL_ADOPTION")
        if not row.get("official_source", "").startswith("DM_17_01_2018_NTC"):
            errors.append(f"{rid}: official_source must identify DM 17-01-2018 NTC")
        if not row.get("source_locator", "").strip():
            errors.append(f"{rid}: source_locator is empty")
        if not row.get("applicability_condition", "").strip():
            errors.append(f"{rid}: applicability_condition is empty")
        if not row.get("forbidden_automatic_use", "").strip():
            errors.append(f"{rid}: forbidden_automatic_use is empty")
        targets = {x.strip() for x in row.get("target_load_ids", "").split(";") if x.strip()}
        if not targets:
            errors.append(f"{rid}: no target load ids")
        unknown = targets - b02_ids
        if unknown:
            errors.append(f"{rid}: unknown B02 targets {sorted(unknown)}")
        targeted |= targets

    if targeted != EXPECTED_TARGETS:
        errors.append(f"target coverage mismatch: expected={sorted(EXPECTED_TARGETS)} actual={sorted(targeted)}")

    by_id = {r.get("rule_id", ""): r for r in rules}
    if by_id.get("B02-RP-001-RC-UNIT-WEIGHT", {}).get("candidate_expression") != "25.0":
        errors.append("RC unit-weight candidate must be 25.0 kN/m3 from NTC Tab. 3.1.I")
    if by_id.get("B02-RP-002-RESIDENTIAL-USE", {}).get("candidate_expression") != "qk=2.00;Qk=2.00;Hk=1.00":
        errors.append("residential-use candidate values mismatch NTC Tab. 3.1.II")
    if by_id.get("B02-RP-003-STAIRS-BALCONIES-USE", {}).get("candidate_expression") != "qk=4.00;Qk=4.00;Hk=2.00":
        errors.append("stairs/balconies candidate values mismatch NTC Tab. 3.1.II")
    if by_id.get("B02-RP-004-ROOF-USE-GUARD", {}).get("candidate_expression") != "NO_VALUE_UNTIL_H_I_K_CLASSIFICATION":
        errors.append("roof guard must not preassign a load before H/I/K classification")
    if "G1+G2+SUM(psi2j*Qkj)" not in by_id.get("B02-RP-005-SEISMIC-MASS-RULE", {}).get("candidate_expression", ""):
        errors.append("seismic-mass candidate must preserve NTC 2.5.7 structure")
    if by_id.get("B02-RP-006-COMBINATION-RULE", {}).get("candidate_expression") != "USE_NTC_2.5.3_COMBINATION_SET_AFTER_ACTION_CLOSURE":
        errors.append("combination rule must remain structural, not emit combinations early")
    if by_id.get("B02-RP-007-EXISTING-BUILDING-GUARD", {}).get("candidate_expression") != "NTC_NEW_BUILDING_ACTIONS_WITH_CH8_EXISTING_BUILDING_GUARDS":
        errors.append("existing-building guard mismatch")

    gg = {r.get("gate_id", "").strip(): r for r in gate}
    expected_gate = {
        "B02-RP-G01": "7",
        "B02-RP-G02": "7",
        "B02-RP-G03": "0",
        "B02-RP-G04": "NO",
        "B02-RP-G05": "PROPOSE_ONLY_NOT_ADOPTED",
        "B02-RP-GATE": "PASS_PROPOSE_ONLY_NO_MODEL_MUTATION",
    }
    for gid, expected in expected_gate.items():
        observed = gg.get(gid, {}).get("observed", "").strip()
        if observed != expected:
            errors.append(f"{gid}: expected {expected!r}, got {observed!r}")

    warnings.append("NTC rulepack is evidence-backed but not adopted: no rule may assign a current model value until a human professional decision is recorded.")
    status = "FAIL" if errors else "PASS_WITH_WATCH"
    print(f"M1E-B02 NTC rulepack candidate validation: {status}")
    print(f"  rules: {len(rules)}")
    print(f"  targeted_b02_rows: {len(targeted)}")
    print("  adopted_rules: 0")
    print("  model_mutation_authorized: NO")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
