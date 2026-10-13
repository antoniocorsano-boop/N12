#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

ALLOWED_GATE_STATUS = {
    "PASS",
    "FAIL",
    "REVIEW_REQUIRED",
    "BLOCKED_INPUT",
    "BLOCKED_SOURCE",
    "NOT_RUN",
}
EXPECTED_OPERATIONAL_COMMIT = "d806dcca72779b5a186defe557a7a9b739575a90"
FEM_DEBT_CHAIN = "ModelGeneration → SolverRun → Result → Verification → Receipt"

REGISTRATION_FIXTURE = Path("evidence/cew-contract-01/fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json")
MODEL_GENERATION_MANIFEST = Path("evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json")
MODEL_GENERATION_RECEIPT = Path("evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json")
MINIMALITY = Path("evidence/cew-contract-01/CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv")
GATE_MATRIX = Path("docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.csv")
QUALIFICATION_REPORT = Path("docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_gate_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"count": 0, "pass_count": 0, "all_pass": False, "distribution": {}}
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    statuses = [str(row.get("status", "")).strip() for row in rows]
    ids = [str(row.get("test_id", "")).strip() for row in rows]
    expected_ids = [f"C01-T{i:02d}" for i in range(1, 12)]
    allowed = all(status in ALLOWED_GATE_STATUS for status in statuses)
    unique_ids = len(ids) == len(set(ids))
    exact_ids = sorted(ids) == expected_ids
    pass_count = sum(status == "PASS" for status in statuses)
    return {
        "count": len(rows),
        "pass_count": pass_count,
        "all_pass": len(rows) == 11 and pass_count == 11 and allowed and unique_ids and exact_ids,
        "distribution": dict(Counter(statuses)),
        "allowed_statuses_only": allowed,
        "exact_test_ids": exact_ids and unique_ids,
    }


def fem_debt_declared(text: str) -> bool:
    return "CEW-FEM-01" in text and FEM_DEBT_CHAIN in text


def validate_registration_uncertainty(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("uncertainty_type") != "REGISTRATION_UNCERTAINTY":
        errors.append("REGISTRATION_UNCERTAINTY_TYPE_INVALID")
    if data.get("source_commit") != EXPECTED_OPERATIONAL_COMMIT:
        errors.append("REGISTRATION_SOURCE_COMMIT_INVALID")
    if data.get("source_path") != "data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv":
        errors.append("REGISTRATION_SOURCE_PATH_INVALID")
    examples = data.get("examples")
    if not isinstance(examples, list) or not examples:
        errors.append("REGISTRATION_EXAMPLES_MISSING")
    else:
        statuses = set()
        for index, item in enumerate(examples):
            if item.get("unit") != "px":
                errors.append(f"REGISTRATION_EXAMPLE_{index}_UNIT_INVALID")
            if not isinstance(item.get("observed"), dict) or not isinstance(item.get("predicted"), dict):
                errors.append(f"REGISTRATION_EXAMPLE_{index}_COORDINATES_MISSING")
            residual = item.get("residual")
            if not isinstance(residual, dict) or not {"du", "dv", "scalar"}.issubset(residual):
                errors.append(f"REGISTRATION_EXAMPLE_{index}_RESIDUAL_MISSING")
            if item.get("derived_bound") is not None and not item.get("derived_bound_rule"):
                errors.append(f"REGISTRATION_EXAMPLE_{index}_UNSOURCED_BOUND")
            statuses.add(item.get("diagnostic_status"))
        if len(examples) >= 2 and not {"PASS_DIAGNOSTIC", "WATCH"}.issubset(statuses):
            errors.append("REGISTRATION_PASS_AND_WATCH_CASES_REQUIRED")
    guard = str(data.get("interpretive_guard", ""))
    lowered = guard.lower()
    if not guard:
        errors.append("REGISTRATION_INTERPRETIVE_GUARD_MISSING")
    overclaim_patterns = (
        "is the certified accuracy",
        "is certified accuracy",
        "is the tolerance",
        "is a tolerance",
        "is the standard error",
        "is the standard uncertainty",
    )
    if any(pattern in lowered for pattern in overclaim_patterns):
        errors.append("REGISTRATION_METROLOGY_OVERCLAIM")
    return errors


def validate_model_generation(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = {
        "model_generation_id",
        "canonical_snapshot_id",
        "scenario_id",
        "generation_profile",
        "builder",
        "parameters",
        "inputs",
        "output",
        "warnings",
        "generated_at",
        "verification",
        "receipt_ref",
        "solver_authorized",
        "calculation_model_ready",
    }
    missing = sorted(required - data.keys())
    if missing:
        errors.append("MODEL_GENERATION_FIELDS_MISSING:" + ",".join(missing))
        return errors
    builder = data.get("builder") or {}
    if builder.get("source_commit") != EXPECTED_OPERATIONAL_COMMIT:
        errors.append("MODEL_GENERATION_BUILDER_COMMIT_INVALID")
    if data.get("solver_authorized") is not False:
        errors.append("MODEL_GENERATION_SOLVER_MUST_REMAIN_UNAUTHORIZED")
    if data.get("calculation_model_ready") is not False:
        errors.append("MODEL_GENERATION_CALCULATION_MODEL_READY_MUTATED")
    inputs = data.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        errors.append("MODEL_GENERATION_INPUTS_MISSING")
    else:
        for index, item in enumerate(inputs):
            if not item.get("path") or not item.get("sha256"):
                errors.append(f"MODEL_GENERATION_INPUT_{index}_DIGEST_MISSING")
    output = data.get("output") or {}
    if not output.get("identity") or not output.get("sha256"):
        errors.append("MODEL_GENERATION_OUTPUT_DIGEST_MISSING")
    verification = data.get("verification") or {}
    if verification.get("status") not in {"PASS", "WARNING", "REVIEW_REQUIRED", "FAIL"}:
        errors.append("MODEL_GENERATION_VERIFICATION_STATUS_INVALID")
    return errors


def validate_minimality(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return ["STRUCTURAL_TYPE_MINIMALITY_MISSING"]
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    allowed = {"CORE_REQUIRED", "SUPPORTED_EXTENSION", "DEFERRED"}
    wall_seen = False
    for row in rows:
        kind = str(row.get("structural_type", "")).strip()
        classification = str(row.get("classification", "")).strip()
        case_ref = str(row.get("case_ref", "")).strip()
        if classification not in allowed:
            errors.append(f"MINIMALITY_CLASS_INVALID:{kind}")
        if classification == "CORE_REQUIRED" and not case_ref:
            errors.append(f"MINIMALITY_CORE_WITHOUT_CASE:{kind}")
        if kind == "Wall":
            wall_seen = True
            if classification != "SUPPORTED_EXTENSION":
                errors.append("WALL_MUST_BE_SUPPORTED_EXTENSION")
    if not wall_seen:
        errors.append("WALL_TAXONOMY_ROW_MISSING")
    return errors


def validate_project(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    fixture_path = root / REGISTRATION_FIXTURE
    if not fixture_path.exists():
        errors.append("REGISTRATION_UNCERTAINTY_FIXTURE_MISSING")
    else:
        errors.extend(validate_registration_uncertainty(load_json(fixture_path)))

    model_path = root / MODEL_GENERATION_MANIFEST
    if not model_path.exists():
        errors.append("MODEL_GENERATION_MANIFEST_MISSING")
    else:
        errors.extend(validate_model_generation(load_json(model_path)))

    receipt_path = root / MODEL_GENERATION_RECEIPT
    if not receipt_path.exists():
        errors.append("MODEL_GENERATION_RECEIPT_MISSING")

    errors.extend(validate_minimality(root / MINIMALITY))

    gate = read_gate_status(root / GATE_MATRIX)
    if not gate["all_pass"]:
        errors.append("C01_GATE_NOT_11_OF_11_PASS")

    report_path = root / QUALIFICATION_REPORT
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    if not fem_debt_declared(report_text):
        errors.append("CEW_FEM_01_DEBT_NOT_DECLARED")

    synthetic_solver_result = False
    calculation_model_ready_mutated = False
    if model_path.exists():
        model = load_json(model_path)
        synthetic_solver_result = bool(model.get("synthetic_solver_result", False))
        calculation_model_ready_mutated = model.get("calculation_model_ready") is not False
        if synthetic_solver_result:
            errors.append("SYNTHETIC_SOLVER_RESULT_FORBIDDEN")
        if calculation_model_ready_mutated:
            errors.append("N12_CALCULATION_MODEL_READY_MUST_REMAIN_FALSE")

    return {
        "qualified": not errors and gate["all_pass"],
        "errors": errors,
        "gate": gate,
        "synthetic_solver_result": synthetic_solver_result,
        "calculation_model_ready_mutated": calculation_model_ready_mutated,
        "fem_debt_declared": fem_debt_declared(report_text),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    result = validate_project(root)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["qualified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
