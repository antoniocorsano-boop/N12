from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

AUTHORITY = Path("evidence/cew-contract-01/stabilization/N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json")
HISTORICAL = Path("evidence/cew-contract-01/stabilization/N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json")
EXPECTED_CHECKOUT_REF = "${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}"
EXPECTED_REPLAY_COMMAND = (
    "python scripts/cew_contract_01_replay.py "
    "--authority evidence/cew-contract-01/stabilization/N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json "
    "--source-root \"$CEW_OPERATIONAL_SOURCE_ROOT\" "
    "--output \"$CEW_REPLAY_OUTPUT_PATH\" "
    "--result \"$CEW_REPLAY_RESULT_PATH\""
)
EXPECTED_MANDATORY_SHELL = "bash"


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


def _unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_yaml_mapping_line(line: str) -> tuple[str, str] | None:
    match = re.match(r"^\s*(.+?):(?:\s*(.*))?$", line)
    if not match:
        return None
    key = _unquote_yaml_scalar(match.group(1))
    if not re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return None
    return key, (match.group(2) or "").strip()


def _parse_workflow_steps(text: str) -> list[dict[str, Any]]:
    """Parse only the workflow step structure needed by the gate contract.

    The parser deliberately treats block-scalar contents as shell text, not YAML.
    This prevents an inert heredoc from impersonating a real `- name`/`run` step.
    """

    lines = text.splitlines()
    steps: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)-\s+name:\s*(.+?)\s*$", lines[index])
        if not match:
            index += 1
            continue

        step_indent = len(match.group(1))
        step: dict[str, Any] = {"name": _unquote_yaml_scalar(match.group(2))}
        index += 1

        while index < len(lines):
            line = lines[index]
            if not line.strip():
                index += 1
                continue
            line_indent = _indent(line)
            if line_indent <= step_indent:
                break
            if line_indent != step_indent + 2:
                index += 1
                continue

            parsed = _parse_yaml_mapping_line(line)
            if parsed is None:
                index += 1
                continue
            key, raw_value = parsed

            if key == "with" and not raw_value:
                mapping: dict[str, str] = {}
                index += 1
                while index < len(lines):
                    nested = lines[index]
                    if not nested.strip():
                        index += 1
                        continue
                    nested_indent = _indent(nested)
                    if nested_indent <= step_indent + 2:
                        break
                    if nested_indent == step_indent + 4:
                        nested_parsed = _parse_yaml_mapping_line(nested)
                        if nested_parsed is not None:
                            nested_key, nested_value = nested_parsed
                            mapping[nested_key] = _unquote_yaml_scalar(nested_value)
                    index += 1
                step["with"] = mapping
                continue

            if key == "run" and raw_value in {"|", ">", "|-", "|+", ">-", ">+"}:
                block_indent = line_indent
                block: list[str] = []
                index += 1
                while index < len(lines):
                    block_line = lines[index]
                    if not block_line.strip():
                        block.append("")
                        index += 1
                        continue
                    if _indent(block_line) <= block_indent:
                        break
                    cut = min(len(block_line), block_indent + 2)
                    block.append(block_line[cut:])
                    index += 1
                step["run"] = "\n".join(block).strip()
                continue

            step[key] = _unquote_yaml_scalar(raw_value)
            index += 1

        steps.append(step)
    return steps


def _parse_defaults_shell(lines: list[str], defaults_index: int, defaults_indent: int) -> str | None:
    index = defaults_index + 1
    run_indent = defaults_indent + 2
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        line_indent = _indent(line)
        if line_indent <= defaults_indent:
            break
        if line_indent == run_indent:
            parsed = _parse_yaml_mapping_line(line)
            if parsed is not None and parsed[0] == "run" and not parsed[1]:
                index += 1
                while index < len(lines):
                    nested = lines[index]
                    if not nested.strip():
                        index += 1
                        continue
                    nested_indent = _indent(nested)
                    if nested_indent <= run_indent:
                        break
                    if nested_indent == run_indent + 2:
                        nested_parsed = _parse_yaml_mapping_line(nested)
                        if nested_parsed is not None and nested_parsed[0] == "shell":
                            return _unquote_yaml_scalar(nested_parsed[1])
                    index += 1
                return None
        index += 1
    return None


def _workflow_default_shell(text: str) -> str | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _indent(line) != 0:
            continue
        parsed = _parse_yaml_mapping_line(line)
        if parsed is not None and parsed[0] == "defaults" and not parsed[1]:
            return _parse_defaults_shell(lines, index, 0)
    return None


def _parse_workflow_job(text: str, job_name: str) -> dict[str, Any] | None:
    lines = text.splitlines()
    jobs_index: int | None = None
    for index, line in enumerate(lines):
        if _indent(line) != 0:
            continue
        parsed = _parse_yaml_mapping_line(line)
        if parsed is not None and parsed[0] == "jobs" and not parsed[1]:
            jobs_index = index
            break
    if jobs_index is None:
        return None

    job_index: int | None = None
    job_indent: int | None = None
    for index in range(jobs_index + 1, len(lines)):
        line = lines[index]
        if not line.strip():
            continue
        line_indent = _indent(line)
        if line_indent == 0:
            break
        if line_indent != 2:
            continue
        parsed = _parse_yaml_mapping_line(line)
        if parsed is not None and parsed[0] == job_name and not parsed[1]:
            job_index = index
            job_indent = line_indent
            break
    if job_index is None or job_indent is None:
        return None

    job: dict[str, Any] = {}
    index = job_index + 1
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        line_indent = _indent(line)
        if line_indent <= job_indent:
            break
        if line_indent != job_indent + 2:
            index += 1
            continue
        parsed = _parse_yaml_mapping_line(line)
        if parsed is None:
            index += 1
            continue
        key, raw_value = parsed
        if key in {"if", "continue-on-error"}:
            job[key] = _unquote_yaml_scalar(raw_value)
        elif key == "defaults" and not raw_value:
            shell = _parse_defaults_shell(lines, index, line_indent)
            if shell is not None:
                job["defaults.run.shell"] = shell
        index += 1
    return job


def _normalize_run_command(value: str) -> str:
    parts: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.endswith("\\"):
            line = line[:-1].rstrip()
        parts.append(line)
    return " ".join(parts)


def _single_named_step(steps: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    matches = [step for step in steps if step.get("name") == name]
    return matches[0] if len(matches) == 1 else None


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
        ("GENERATION_IDENTITY_MISMATCH:model_generation_id", model.get("model_generation_id"), authority.get("model_generation_id")),
        ("AUTHORITY_IDENTITY_GENERATION_PROFILE_MISMATCH", model.get("generation_profile"), authority.get("generation_profile")),
        ("BUILDER_IDENTITY_PATH_MISMATCH", model.get("builder", {}).get("path"), authority.get("builder", {}).get("path")),
        ("BUILDER_IDENTITY_DECLARED_BLOB_MISMATCH", model.get("builder", {}).get("git_blob_sha"), authority.get("builder", {}).get("git_blob_sha")),
        ("OUTPUT_AUTHORITY_MISMATCH:identity", model.get("output", {}).get("identity"), authority.get("output", {}).get("identity")),
        (
            "GENERATION_IDENTITY_MISMATCH:generation_id_inside_artifact",
            model.get("output", {}).get("generation_id_inside_artifact"),
            authority.get("output", {}).get("generation_id_inside_artifact"),
        ),
        ("OUTPUT_AUTHORITY_MISMATCH:sha256", model.get("output", {}).get("sha256"), authority.get("output", {}).get("sha256")),
        ("OUTPUT_AUTHORITY_MISMATCH:size_bytes", model.get("output", {}).get("size_bytes"), authority.get("output", {}).get("size_bytes")),
        ("REPLAY_TIMESTAMP_AUTHORITY_MISMATCH", model.get("generated_at"), authority.get("generated_at")),
    )
    for code, actual, expected in comparisons:
        if actual != expected:
            errors.append(code)

    receipt_generation = (
        ("model_generation_id", receipt.get("model_generation_id"), authority.get("model_generation_id")),
        (
            "generation_id_inside_artifact",
            receipt.get("generation_id_inside_artifact"),
            authority.get("output", {}).get("generation_id_inside_artifact"),
        ),
    )
    for field, actual, expected in receipt_generation:
        if actual != expected:
            errors.append(f"RECEIPT_GENERATION_IDENTITY_MISMATCH:{field}")
    if receipt.get("generated_artifact_timestamp") != authority.get("generated_at"):
        errors.append("RECEIPT_GENERATION_TIMESTAMP_MISMATCH")

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
    verification = historical.get("verification")
    required_verification_flags = (
        "archive_sha256_verified",
        "output_sha256_verified",
        "output_size_verified",
    )
    for field in required_verification_flags:
        if not isinstance(verification, dict) or verification.get(field) is not True:
            errors.append(f"AUTHORITY_IDENTITY_HISTORICAL_VERIFICATION_INVALID:{field}")
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
    errors: list[str] = []
    steps = _parse_workflow_steps(text)
    closure_job = _parse_workflow_job(text, "closure")

    if closure_job is not None and "if" in closure_job:
        errors.append("CI_BYPASS_JOB_CONDITIONAL")
    if closure_job is not None and "continue-on-error" in closure_job:
        errors.append("CI_BYPASS_JOB_FAILURE_OVERRIDE")
    if _workflow_default_shell(text) is not None or (
        closure_job is not None and closure_job.get("defaults.run.shell") is not None
    ):
        errors.append("CI_BYPASS_MANDATORY_SHELL")

    checkout = _single_named_step(steps, "Checkout PR exact head")
    checkout_with = checkout.get("with", {}) if checkout else {}
    if checkout is None or str(checkout_with.get("ref", "")).strip() != EXPECTED_CHECKOUT_REF:
        errors.append("CI_BYPASS_EXACT_HEAD_MISSING")
    if checkout is None or str(checkout_with.get("persist-credentials", "")).lower() != "false":
        errors.append("CI_BYPASS_PERSISTED_CREDENTIALS")

    for step in steps:
        action = str(step.get("uses", ""))
        if re.fullmatch(r"actions/(?:checkout|setup-python)@.+", action):
            ref = action.rsplit("@", 1)[1]
            if not re.fullmatch(r"[0-9a-f]{40}", ref):
                errors.append(f"CI_BYPASS_UNPINNED_ACTION:{action}")
        if "if" in step:
            errors.append("CI_BYPASS_CONDITIONAL_STEP")
        if "continue-on-error" in step:
            errors.append("CI_BYPASS_FAILURE_OVERRIDE")

    if "|| true" in text or "; true" in text:
        errors.append("CI_BYPASS_FAILURE_OVERRIDE")
    if any(marker in text for marker in ("/actions/artifacts/", "artifact.zip", "CEW_MODEL_OUTPUT_ROOT")):
        errors.append("CI_BYPASS_EPHEMERAL_ACTIONS_DEPENDENCY")

    replay = _single_named_step(steps, "Run deterministic ModelGeneration replay")
    if replay is None:
        errors.append("CI_BYPASS_REPLAY_STEP_MISSING")
    else:
        replay_run = _normalize_run_command(str(replay.get("run", "")))
        if replay_run != EXPECTED_REPLAY_COMMAND:
            errors.append("CI_BYPASS_REPLAY_COMMAND_INVALID")
        if str(replay.get("shell", "")).strip() != EXPECTED_MANDATORY_SHELL:
            errors.append("CI_BYPASS_MANDATORY_SHELL")

    enforcement = _single_named_step(steps, "Enforce CEW-CONTRACT-01 qualification")
    if enforcement is None or str(enforcement.get("run", "")).strip() != "python scripts/validate_cew_contract_01_closure.py":
        errors.append("CI_BYPASS_ENFORCEMENT_MISSING")
    elif str(enforcement.get("shell", "")).strip() != EXPECTED_MANDATORY_SHELL:
        errors.append("CI_BYPASS_MANDATORY_SHELL")
    return errors
