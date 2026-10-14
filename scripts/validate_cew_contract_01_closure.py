#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

try:
    from scripts.cew_contract_01_stabilization_checks import validate_stabilization
except ModuleNotFoundError:
    from cew_contract_01_stabilization_checks import validate_stabilization

ALLOWED_GATE_STATUS = {
    "PASS",
    "FAIL",
    "REVIEW_REQUIRED",
    "BLOCKED_INPUT",
    "BLOCKED_SOURCE",
    "NOT_RUN",
}
EXPECTED_OPERATIONAL_COMMIT = "d806dcca72779b5a186defe557a7a9b739575a90"
EXPECTED_CANONICAL_SNAPSHOT_ID = f"N12-FROZEN-INPUTSET@{EXPECTED_OPERATIONAL_COMMIT}"
EXPECTED_REGISTRATION_SOURCE_PATH = "data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv"
EXPECTED_MODEL_INPUT_PATHS = (
    "data/canonical/M0G_GEOMETRY_HANDOFF_v1.json",
    "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv",
    "data/canonical/M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv",
    "data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv",
    "data/canonical/M1F_FOUNDATION_MODEL_CURRENT_v1.csv",
    "data/canonical/M1E_FOUNDATION_XY_SOLVER_PROJECTION_RULE_v1.json",
)
FEM_DEBT_CHAIN = "ModelGeneration → SolverRun → Result → Verification → Receipt"
FEM_DEBT_MARKER = "CEW_FEM_01_REQUIRED=true"

REGISTRATION_FIXTURE = Path("evidence/cew-contract-01/fixtures/N12_REGISTRATION_UNCERTAINTY_v1.json")
MODEL_GENERATION_MANIFEST = Path("evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json")
MODEL_GENERATION_RECEIPT = Path("evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json")
MINIMALITY = Path("evidence/cew-contract-01/CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv")
GATE_MATRIX = Path("docs/cew-contract/CEW_CONTRACT_01_CONFORMANCE_MATRIX.csv")
QUALIFICATION_REPORT = Path("docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha_file(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _safe_relative_path(value: str) -> bool:
    candidate = Path(value)
    return bool(value) and not candidate.is_absolute() and ".." not in candidate.parts


def _decimal_equal(left: Any, right: Any) -> bool:
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except (InvalidOperation, ValueError):
        return False


def _validate_gate_evidence(root: Path, rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row in rows:
        test_id = str(row.get("test_id", "")).strip()
        status = str(row.get("status", "")).strip()
        if status != "PASS":
            continue
        raw = str(row.get("evidence", "")).strip()
        if not raw:
            errors.append(f"C01_GATE_EVIDENCE_MISSING:{test_id}:EMPTY")
            continue
        for reference in (part.strip() for part in raw.split(";")):
            if not reference:
                errors.append(f"C01_GATE_EVIDENCE_MISSING:{test_id}:EMPTY")
                continue
            if not _safe_relative_path(reference):
                errors.append(f"C01_GATE_EVIDENCE_INVALID_PATH:{test_id}:{reference}")
                continue
            if any(char in reference for char in "*?["):
                matches = [path for path in root.glob(reference) if path.is_file()]
                if not matches:
                    errors.append(f"C01_GATE_EVIDENCE_MISSING:{test_id}:{reference}")
            elif not (root / reference).is_file():
                errors.append(f"C01_GATE_EVIDENCE_MISSING:{test_id}:{reference}")
    return errors


def read_gate_status(path: Path, root: Path | None = None) -> dict[str, Any]:
    if not path.exists():
        return {
            "count": 0,
            "pass_count": 0,
            "all_pass": False,
            "distribution": {},
            "evidence_valid": False if root is not None else True,
            "evidence_errors": [],
        }
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    statuses = [str(row.get("status", "")).strip() for row in rows]
    ids = [str(row.get("test_id", "")).strip() for row in rows]
    expected_ids = [f"C01-T{i:02d}" for i in range(1, 12)]
    allowed = all(status in ALLOWED_GATE_STATUS for status in statuses)
    unique_ids = len(ids) == len(set(ids))
    exact_ids = sorted(ids) == expected_ids
    pass_count = sum(status == "PASS" for status in statuses)
    evidence_errors = _validate_gate_evidence(root, rows) if root is not None else []
    evidence_valid = not evidence_errors
    return {
        "count": len(rows),
        "pass_count": pass_count,
        "all_pass": (
            len(rows) == 11
            and pass_count == 11
            and allowed
            and unique_ids
            and exact_ids
            and evidence_valid
        ),
        "distribution": dict(Counter(statuses)),
        "allowed_statuses_only": allowed,
        "exact_test_ids": exact_ids and unique_ids,
        "evidence_valid": evidence_valid,
        "evidence_errors": evidence_errors,
    }


def fem_debt_declared(text: str) -> bool:
    required_chain = f"CEW-FEM-01: {FEM_DEBT_CHAIN}"
    lines = [line.strip() for line in text.splitlines()]
    return (
        lines.count(FEM_DEBT_MARKER) == 1
        and lines.count(required_chain) == 1
        and "CEW_FEM_01_REQUIRED=false" not in lines
    )


def validate_registration_uncertainty(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("uncertainty_type") != "REGISTRATION_UNCERTAINTY":
        errors.append("REGISTRATION_UNCERTAINTY_TYPE_INVALID")
    if data.get("source_commit") != EXPECTED_OPERATIONAL_COMMIT:
        errors.append("REGISTRATION_SOURCE_COMMIT_INVALID")
    if data.get("source_path") != EXPECTED_REGISTRATION_SOURCE_PATH:
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
        support_ids = [str(item.get("support_id", "")) for item in examples]
        if support_ids != ["1", "19"] or len(set(support_ids)) != 2:
            errors.append("REGISTRATION_EXAMPLE_SET_INVALID")
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


def validate_registration_epistemic_guard(data: dict[str, Any]) -> list[str]:
    guard = data.get("epistemic_guard")
    fields = (
        "residual_is_new_measurement",
        "residual_promotable_to_DOC",
        "residual_promotable_to_MIS",
        "unsourced_plus_minus_interval_allowed",
    )
    if not isinstance(guard, dict):
        return ["REGISTRATION_EPISTEMIC_GUARD_MISSING"]
    return [
        f"REGISTRATION_EPISTEMIC_GUARD_INVALID:{field}"
        for field in fields
        if guard.get(field) is not False
    ]


def validate_registration_source(data: dict[str, Any], operational_source_root: Path | None) -> list[str]:
    errors: list[str] = []
    if operational_source_root is None:
        return ["REGISTRATION_OPERATIONAL_SOURCE_ROOT_MISSING"]
    source_path = str(data.get("source_path", "")).strip()
    if source_path != EXPECTED_REGISTRATION_SOURCE_PATH or not _safe_relative_path(source_path):
        return ["REGISTRATION_SOURCE_PATH_INVALID"]
    source = operational_source_root / source_path
    if not source.is_file():
        return ["REGISTRATION_SOURCE_FILE_MISSING"]
    expected_blob = str(data.get("source_git_blob_sha", "")).strip().lower()
    if not expected_blob:
        errors.append("REGISTRATION_SOURCE_BLOB_SHA_MISSING")
    elif git_blob_sha_file(source) != expected_blob:
        errors.append("REGISTRATION_SOURCE_BLOB_SHA_MISMATCH")

    with source.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = {str(row.get("support_id", "")): row for row in csv.DictReader(fh)}
    mapping = {
        "observed.u": ("observed", "u", "u_observed_px"),
        "observed.v": ("observed", "v", "v_observed_px"),
        "predicted.u": ("predicted", "u", "u_predicted_px"),
        "predicted.v": ("predicted", "v", "v_predicted_px"),
        "residual.du": ("residual", "du", "du_px"),
        "residual.dv": ("residual", "dv", "dv_px"),
        "residual.scalar": ("residual", "scalar", "residual_px"),
    }
    for example in data.get("examples") or []:
        support_id = str(example.get("support_id", ""))
        row = rows.get(support_id)
        if row is None:
            errors.append(f"REGISTRATION_SOURCE_EXAMPLE_MISMATCH:{support_id}:MISSING")
            continue
        for label, (group, key, column) in mapping.items():
            group_value = example.get(group) or {}
            if not _decimal_equal(group_value.get(key), row.get(column)):
                errors.append(f"REGISTRATION_SOURCE_EXAMPLE_MISMATCH:{support_id}:{label}")
        if str(example.get("diagnostic_status", "")) != str(row.get("residual_status", "")):
            errors.append(f"REGISTRATION_SOURCE_EXAMPLE_MISMATCH:{support_id}:diagnostic_status")
        if str(example.get("evidence_class", "")) != str(row.get("evidence_class", "")):
            errors.append(f"REGISTRATION_SOURCE_EXAMPLE_MISMATCH:{support_id}:evidence_class")
    return errors


def validate_model_generation(
    data: dict[str, Any],
    operational_source_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    required = {
        "model_generation_id",
        "canonical_snapshot_id",
        "scenario_id",
        "generation_profile",
        "builder",
        "workflow",
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
    if data.get("canonical_snapshot_id") != EXPECTED_CANONICAL_SNAPSHOT_ID:
        errors.append("MODEL_GENERATION_CANONICAL_SNAPSHOT_INVALID")
    builder = data.get("builder") or {}
    if builder.get("source_commit") != EXPECTED_OPERATIONAL_COMMIT:
        errors.append("MODEL_GENERATION_BUILDER_COMMIT_INVALID")
    if not builder.get("path") or not builder.get("git_blob_sha"):
        errors.append("MODEL_GENERATION_BUILDER_IDENTITY_MISSING")
    builder_path = str(builder.get("path", "")).strip()
    if builder_path and not _safe_relative_path(builder_path):
        errors.append("MODEL_GENERATION_BUILDER_PATH_INVALID")
    elif builder_path and operational_source_root is not None:
        materialized_builder = operational_source_root / builder_path
        if not materialized_builder.is_file():
            errors.append("MODEL_GENERATION_BUILDER_SOURCE_MISSING")
        elif git_blob_sha_file(materialized_builder) != str(builder.get("git_blob_sha", "")).strip().lower():
            errors.append("MODEL_GENERATION_BUILDER_BLOB_MISMATCH")
    workflow = data.get("workflow") or {}
    if not workflow.get("path") or not workflow.get("workflow_run_id"):
        errors.append("MODEL_GENERATION_WORKFLOW_IDENTITY_MISSING")
    if workflow.get("conclusion") != "success":
        errors.append("MODEL_GENERATION_WORKFLOW_NOT_SUCCESS")
    if data.get("solver_authorized") is not False:
        errors.append("MODEL_GENERATION_SOLVER_MUST_REMAIN_UNAUTHORIZED")
    if data.get("calculation_model_ready") is not False:
        errors.append("MODEL_GENERATION_CALCULATION_MODEL_READY_MUTATED")

    inputs = data.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        errors.append("MODEL_GENERATION_INPUTS_MISSING")
    else:
        input_paths = [str(item.get("path", "")).strip() for item in inputs]
        if (
            len(input_paths) != len(EXPECTED_MODEL_INPUT_PATHS)
            or len(set(input_paths)) != len(input_paths)
            or set(input_paths) != set(EXPECTED_MODEL_INPUT_PATHS)
        ):
            errors.append("MODEL_GENERATION_INPUT_SET_INVALID")
        if operational_source_root is None:
            errors.append("MODEL_GENERATION_OPERATIONAL_SOURCE_ROOT_MISSING")
        for index, item in enumerate(inputs):
            input_path = str(item.get("path", "")).strip()
            expected_digest = str(item.get("sha256", "")).strip().lower()
            if not input_path or not expected_digest:
                errors.append(f"MODEL_GENERATION_INPUT_{index}_DIGEST_MISSING")
                continue
            if not _safe_relative_path(input_path):
                errors.append(f"MODEL_GENERATION_INPUT_{index}_PATH_INVALID")
                continue
            if operational_source_root is None:
                continue
            materialized = operational_source_root / input_path
            if not materialized.is_file():
                errors.append(f"MODEL_GENERATION_INPUT_{index}_SOURCE_MISSING")
                continue
            if sha256_file(materialized) != expected_digest:
                errors.append(f"MODEL_GENERATION_INPUT_{index}_DIGEST_MISMATCH")

    output = data.get("output") or {}
    required_output = (
        "identity",
        "sha256",
        "size_bytes",
        "artifact_id",
        "artifact_name",
        "artifact_archive_digest",
    )
    if any(output.get(field) in (None, "") for field in required_output):
        errors.append("MODEL_GENERATION_OUTPUT_IDENTITY_MISSING")
    verification = data.get("verification") or {}
    if verification.get("status") != "PASS":
        errors.append("MODEL_GENERATION_VERIFICATION_NOT_PASS")
    if verification.get("workflow_run_id") != workflow.get("workflow_run_id"):
        errors.append("MODEL_GENERATION_VERIFICATION_RUN_MISMATCH")
    return errors


def validate_receipt(receipt: dict[str, Any], model: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if receipt.get("receipt_class") != "QUALIFICATION_RECEIPT":
        errors.append("MODEL_GENERATION_RECEIPT_CLASS_INVALID")
    for field in ("engineering_result", "solver_run", "result_entity_created"):
        if receipt.get(field) is not False:
            errors.append(f"MODEL_GENERATION_RECEIPT_AUTHORITY_INVALID:{field}")

    builder = model.get("builder") or {}
    workflow = model.get("workflow") or {}
    verification = model.get("verification") or {}
    output = model.get("output") or {}
    expected_inputs = {
        str(item.get("path")): str(item.get("sha256"))
        for item in model.get("inputs", [])
        if item.get("path") and item.get("sha256")
    }

    comparisons = (
        ("source_commit", receipt.get("source_commit"), builder.get("source_commit")),
        ("builder_path", receipt.get("builder_path"), builder.get("path")),
        ("workflow_path", receipt.get("workflow_path"), workflow.get("path")),
        ("workflow_run_id", receipt.get("workflow_run_id"), workflow.get("workflow_run_id")),
        ("artifact_id", receipt.get("artifact_id"), output.get("artifact_id")),
        ("artifact_name", receipt.get("artifact_name"), output.get("artifact_name")),
        ("artifact_archive_digest", receipt.get("artifact_archive_digest"), output.get("artifact_archive_digest")),
        ("output_file", receipt.get("output_file"), output.get("identity")),
        ("output_sha256", receipt.get("output_sha256"), output.get("sha256")),
        ("output_size_bytes", receipt.get("output_size_bytes"), output.get("size_bytes")),
    )
    for field, actual, expected in comparisons:
        if actual != expected:
            errors.append(f"MODEL_GENERATION_RECEIPT_MISMATCH:{field}")

    if receipt.get("source_commit") != EXPECTED_OPERATIONAL_COMMIT:
        errors.append("MODEL_GENERATION_RECEIPT_SOURCE_COMMIT_INVALID")
    if receipt.get("workflow_conclusion") != "success":
        errors.append("MODEL_GENERATION_RECEIPT_WORKFLOW_NOT_SUCCESS")
    if receipt.get("input_sha256") != expected_inputs:
        errors.append("MODEL_GENERATION_RECEIPT_INPUT_DIGESTS_MISMATCH")
    receipt_verification = receipt.get("verification") or {}
    if receipt_verification.get("status") != "PASS":
        errors.append("MODEL_GENERATION_RECEIPT_VERIFICATION_NOT_PASS")
    if receipt_verification.get("workflow_run_id") != verification.get("workflow_run_id"):
        errors.append("MODEL_GENERATION_RECEIPT_VERIFICATION_RUN_MISMATCH")
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
    operational_root_value = os.environ.get("CEW_OPERATIONAL_SOURCE_ROOT", "").strip()
    operational_root = Path(operational_root_value) if operational_root_value else None
    replay_result: dict[str, Any] | None = None
    replay_result_value = os.environ.get("CEW_REPLAY_RESULT_PATH", "").strip()
    if replay_result_value:
        try:
            replay_result = load_json(Path(replay_result_value))
        except (OSError, json.JSONDecodeError):
            errors.append("REPLAY_RESULT_INVALID")
    else:
        errors.append("REPLAY_RESULT_MISSING")

    fixture: dict[str, Any] | None = None
    fixture_path = root / REGISTRATION_FIXTURE
    if not fixture_path.exists():
        errors.append("REGISTRATION_UNCERTAINTY_FIXTURE_MISSING")
    else:
        fixture = load_json(fixture_path)
        errors.extend(validate_registration_uncertainty(fixture))
        errors.extend(validate_registration_epistemic_guard(fixture))
        errors.extend(validate_registration_source(fixture, operational_root))

    model: dict[str, Any] | None = None
    model_path = root / MODEL_GENERATION_MANIFEST
    if not model_path.exists():
        errors.append("MODEL_GENERATION_MANIFEST_MISSING")
    else:
        model = load_json(model_path)
        errors.extend(validate_model_generation(model, operational_root))
        if model.get("receipt_ref") != MODEL_GENERATION_RECEIPT.as_posix():
            errors.append("MODEL_GENERATION_RECEIPT_REF_INVALID")

    receipt: dict[str, Any] | None = None
    receipt_path = root / MODEL_GENERATION_RECEIPT
    if not receipt_path.exists():
        errors.append("MODEL_GENERATION_RECEIPT_MISSING")
    elif model is not None:
        receipt = load_json(receipt_path)
        errors.extend(validate_receipt(receipt, model))

    if fixture is not None and model is not None and receipt is not None:
        errors.extend(validate_stabilization(root, model, receipt, fixture, operational_root, replay_result))

    errors.extend(validate_minimality(root / MINIMALITY))

    gate = read_gate_status(root / GATE_MATRIX, root=root)
    errors.extend(gate.get("evidence_errors", []))
    if not gate["all_pass"]:
        errors.append("C01_GATE_NOT_11_OF_11_PASS")

    report_path = root / QUALIFICATION_REPORT
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    if not fem_debt_declared(report_text):
        errors.append("CEW_FEM_01_DEBT_NOT_DECLARED")

    synthetic_solver_result = False
    calculation_model_ready_mutated = False
    if model is not None:
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