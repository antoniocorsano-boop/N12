from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .adapters.opencadstudio import (
    _default_client_factory,
    _mapping,
    _tool_names,
    _validate_capabilities_payload,
)
from .canonical import canonical_json_bytes, sha256_file, sha256_json


_REQUIRED_READ_ONLY_TOOLS = {"ocs_sessions", "ocs_read"}


def _diff_values(before: Any, after: Any, path: str = "$") -> list[dict[str, object]]:
    if isinstance(before, dict) and isinstance(after, dict):
        differences: list[dict[str, object]] = []
        for key in sorted(set(before) | set(after)):
            child_path = f"{path}.{key}"
            if key not in before:
                differences.append({"path": child_path, "before": None, "after": after[key]})
            elif key not in after:
                differences.append({"path": child_path, "before": before[key], "after": None})
            else:
                differences.extend(_diff_values(before[key], after[key], child_path))
        return differences
    if before != after:
        return [{"path": path, "before": before, "after": after}]
    return []


def _write_canonical(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value))


async def capture_capability_diagnostic(
    *,
    executable: Path,
    expected_executable_sha256: str | None,
    output_dir: Path,
    client_factory: Callable[[Path], Any] | None = None,
) -> dict[str, object]:
    executable = Path(executable)
    output_dir = Path(output_dir)
    if not executable.exists() or not executable.is_file():
        raise ValueError("OCS_EXECUTABLE_MISSING")
    executable_sha256 = sha256_file(executable)
    if expected_executable_sha256 is not None and executable_sha256 != expected_executable_sha256:
        raise ValueError("OCS_EXECUTABLE_HASH_MISMATCH")

    factory = client_factory or _default_client_factory
    async with factory(executable) as client:
        tools = await _tool_names(client)
        if not _REQUIRED_READ_ONLY_TOOLS.issubset(tools):
            raise ValueError("OCS_READ_ONLY_DIAGNOSTIC_TOOL_MISSING")

        sessions_payload = _mapping(await client.call_tool("ocs_sessions", {"launch_if_none": False}))
        sessions = sessions_payload.get("result")
        if not isinstance(sessions, list) or len(sessions) != 1 or not isinstance(sessions[0], dict):
            raise ValueError("OCS_SESSION_AMBIGUOUS")
        session = sessions[0]
        session_id = session.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("OCS_SESSION_ID_MISSING")
        bridge = session.get("bridge")
        if not isinstance(bridge, dict):
            raise ValueError("OCS_BRIDGE_MISSING")
        version = bridge.get("version")
        build_rev = bridge.get("build_rev")
        if not isinstance(version, str) or not version or not isinstance(build_rev, str) or not build_rev:
            raise ValueError("OCS_BRIDGE_IDENTITY_MISSING")
        cad_build = f"{version}@{build_rev}"

        first = _mapping(
            await client.call_tool(
                "ocs_read",
                {"ocs_session_id": session_id, "op": "capabilities"},
            )
        )
        second = _mapping(
            await client.call_tool(
                "ocs_read",
                {"ocs_session_id": session_id, "op": "capabilities"},
            )
        )

    _validate_capabilities_payload(first)
    _validate_capabilities_payload(second)

    differences = _diff_values(first, second)
    first_sha256 = sha256_json(first)
    second_sha256 = sha256_json(second)
    changed_paths = [item["path"][2:] for item in differences if isinstance(item.get("path"), str) and item["path"].startswith("$.")]

    output_dir.mkdir(parents=True, exist_ok=True)
    first_path = output_dir / "capabilities-1.json"
    second_path = output_dir / "capabilities-2.json"
    diff_path = output_dir / "capabilities-diff.json"
    result_path = output_dir / "capabilities-probe-result.json"

    diff_payload = {
        "schema": "cew.cad.capability-diagnostic.v1",
        "mode": "READ_ONLY_CAPABILITY_PROBE",
        "session_id": session_id,
        "cad_build": cad_build,
        "first_sha256": first_sha256,
        "second_sha256": second_sha256,
        "difference_count": len(differences),
        "changed_paths": changed_paths,
        "differences": differences,
    }
    result: dict[str, object] = {
        **diff_payload,
        "sample_count": 2,
        "raw_sha256": [first_sha256, second_sha256],
        "executable_sha256": executable_sha256,
        "mutation_authorized": False,
        "identity_classification_performed": False,
        "first_payload_path": str(first_path),
        "second_payload_path": str(second_path),
        "diff_path": str(diff_path),
        "result_path": str(result_path),
    }

    _write_canonical(first_path, first)
    _write_canonical(second_path, second)
    _write_canonical(diff_path, diff_payload)
    _write_canonical(result_path, result)
    return result
