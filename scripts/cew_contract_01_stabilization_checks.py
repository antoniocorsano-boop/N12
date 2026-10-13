from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

AUTHORITY = Path("evidence/cew-contract-01/stabilization/N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json")
HISTORICAL = Path("evidence/cew-contract-01/stabilization/N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _input_map(items: Any) -> dict[str, str]:
    if not isinstance(items, list):
        return {}
    return {
        str(item.get("path")): str(item.get("sha256"))
        for item in items
        if item.get("path") and item.get("sha256")
    }


def validate_stabilization(
    root: Path,
    model: dict[str, Any],
    receipt: dict[str, Any],
    fixture: dict[str, Any],
    operational_root: Path | None,
    replay_result: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    authority_path = root / AUTHORITY
    historical_path = root / HISTORICAL
    if not authority_path.is_file():
        return ["AUTHORITY_IDENTITY_PROFILE_MISSING"]
    if not historical_path.is_file():
        return ["AUTHORITY_IDENTITY_HISTORICAL_RECEIPT_MISSING"]
    authority = load_json(authority_path)
    historical = load_json(historical_path)

    if sorted(authority.get("gate_evidence", {})) != [f"C01-T{i:02d}" for i in range(1, 12)]:
        errors.append("GATE_MATRIX_AUTHORITY_SET_INVALID")

    comparisons = (
        ("AUTHORITY_IDENTITY_OPERATIONAL_COMMIT_MISMATCH", model.get("builder", {}).get("source_commit"), authority.get("operational_commit")),
        ("AUTHORITY_IDENTITY_SNAPSHOT_MISMATCH", model.get("canonical_snapshot_id"), authority.get("canonical_snapshot_id")),
        ("AUTHORITY_IDENTITY_GENERATION_PROFILE_MISMATCH", model.get("generation_profile"), authority.get("generation_profile")),
        ("BUILDER_IDENTITY_PATH_MISMATCH", model.get("builder", {}).get("path"), authority.get("builder", {}).get("path")),
        ("BUILDER_IDENTITY_DECLARED_BLOB_MISMATCH", model.get("builder", {}).get("git_blob_sha"), authority.get("builder", {}).get("git_blob_sha")),
        ("OUTPUT_AUTHORITY_MISMATCH:identity", model.get("output", {}).get("identity"), authority.get("output", {}).get("identity")),
        ("OUTPUT_AUTHORITY_MISMATCH:sha256", model.get("output", {}).get("sha256"), authority.get("output", {}).get("sha256")),
        ("OUTPUT_AUTHORITY_MISMATCH:size_bytes", model.get("output", {}).get("size_bytes"), authority.get("output", {}).get("size_bytes")),
        ("REPLAY_TIMESTAMP_AUTHORITY_MISMATCH", model.get("generated_at"), authority.get("generated_at")),
    )
    for code, actual, expected in comparisons:
        if actual != expected:
            errors.append(code)

    if _input_map(model.get("inputs")) != _input_map(authority.get("inputs")):
        errors.append("INPUT_SET_AUTHORITY_MISMATCH")

    builder_rel = str(authority.get("builder", {}).get("path", ""))
    if operational_root is None:
        errors.append("BUILDER_IDENTITY_SOURCE_ROOT_MISSING")
    else:
        builder = operational_root / builder_rel
        if not builder.is_file():
            errors.append("BUILDER_IDENTITY_FILE_MISSING")
        elif git_blob_sha_file(builder) != str(authority.get("builder", {}).get("git_blob_sha", "")):
            errors.append("BUILDER_IDENTITY_BLOB_MISMATCH")

    expected_supports = [str(value) for value in authority.get("registration", {}).get("support_ids", [])]
    actual_supports = [str(item.get("support_id", "")) for item in fixture.get("examples", [])]
    if actual_supports != expected_supports or len(set(actual_supports)) != len(actual_supports):
        errors.append("REGISTRATION_EXAMPLE_SET_INVALID")
    if fixture.get("source_commit") != authority.get("operational_commit"):
        errors.append("REGISTRATION_AUTHORITY_COMMIT_MISMATCH")
    if fixture.get("source_path") != authority.get("registration", {}).get("source_path"):
        errors.append("REGISTRATION_AUTHORITY_PATH_MISMATCH")
    if fixture.get("source_git_blob_sha") != authority.get("registration", {}).get("source_git_blob_sha"):
        errors.append("REGISTRATION_AUTHORITY_BLOB_MISMATCH")

    flags = authority.get("authority_flags", {})
    model_flags = {
        "solver_authorized": model.get("solver_authorized"),
        "calculation_model_ready": model.get("calculation_model_ready"),
        "synthetic_solver_result": model.get("synthetic_solver_result"),
    }
    receipt_flags = {
        "solver_run": receipt.get("solver_run"),
        "result_entity_created": receipt.get("result_entity_created"),
    }
    for name, expected in flags.items():
        actual = model_flags[name] if name in model_flags else receipt_flags.get(name)
        if actual is not expected:
            errors.append(f"AUTHORITY_BOUNDARY_INVALID:{name}")

    if replay_result is None:
        errors.append("REPLAY_RESULT_MISSING")
    else:
        if replay_result.get("passed") is not True:
            errors.append("REPLAY_NOT_PASS")
        for field in ("identity", "sha256", "size_bytes"):
            if replay_result.get(field) != authority.get("output", {}).get(field):
                errors.append(f"REPLAY_OUTPUT_MISMATCH:{field}")
        if replay_result.get("generated_at") != authority.get("generated_at"):
            errors.append("REPLAY_TIMESTAMP_MISMATCH")

    if historical.get("runtime_dependency") is not False:
        errors.append("AUTHORITY_IDENTITY_HISTORICAL_RUNTIME_DEPENDENCY")
    run = historical.get("run", {})
    artifact = historical.get("artifact", {})
    hist_output = historical.get("output", {})
    if (
        run.get("head_sha") != authority.get("operational_commit")
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
    ):
        errors.append("AUTHORITY_IDENTITY_HISTORICAL_RUN_INVALID")
    if (
        run.get("id") != model.get("workflow", {}).get("workflow_run_id")
        or run.get("workflow_path") != model.get("workflow", {}).get("path")
    ):
        errors.append("AUTHORITY_IDENTITY_HISTORICAL_RUN_MISMATCH")
    for field, historical_value, model_value in (
        ("artifact_id", artifact.get("id"), model.get("output", {}).get("artifact_id")),
        ("artifact_name", artifact.get("name"), model.get("output", {}).get("artifact_name")),
        ("artifact_archive_digest", artifact.get("archive_digest"), model.get("output", {}).get("artifact_archive_digest")),
        ("identity", hist_output.get("identity"), model.get("output", {}).get("identity")),
        ("sha256", hist_output.get("sha256"), model.get("output", {}).get("sha256")),
        ("size_bytes", hist_output.get("size_bytes"), model.get("output", {}).get("size_bytes")),
    ):
        if historical_value != model_value:
            errors.append(f"AUTHORITY_IDENTITY_HISTORICAL_MISMATCH:{field}")
    return errors


def workflow_contract_errors(text: str) -> list[str]:
    import re

    errors: list[str] = []
    if "github.event.pull_request.head.sha" not in text:
        errors.append("CI_BYPASS_EXACT_HEAD_MISSING")
    if "persist-credentials: false" not in text:
        errors.append("CI_BYPASS_PERSISTED_CREDENTIALS")
    for action in re.findall(r"uses:\s*(actions/(?:checkout|setup-python)@[^\s]+)", text):
        ref = action.rsplit("@", 1)[1]
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            errors.append(f"CI_BYPASS_UNPINNED_ACTION:{action}")
    if re.search(r"(?m)^\s*(?:-\s*)?if\s*:", text):
        errors.append("CI_BYPASS_CONDITIONAL_STEP")
    if "continue-on-error:" in text or "|| true" in text or "; true" in text:
        errors.append("CI_BYPASS_FAILURE_OVERRIDE")
    if any(marker in text for marker in ("/actions/artifacts/", "artifact.zip", "CEW_MODEL_OUTPUT_ROOT")):
        errors.append("CI_BYPASS_EPHEMERAL_ACTIONS_DEPENDENCY")
    if "python scripts/cew_contract_01_replay.py" not in text:
        errors.append("CI_BYPASS_REPLAY_STEP_MISSING")
    if "python scripts/validate_cew_contract_01_closure.py" not in text:
        errors.append("CI_BYPASS_ENFORCEMENT_MISSING")
    return errors
