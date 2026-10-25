from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Callable

from cew_cad_gateway.adapters.opencadstudio import (
    _default_client_factory,
    _mapping,
    _tool_names,
    _validate_capabilities_payload,
)
from cew_cad_gateway.canonical import canonical_json_bytes, sha256_file, sha256_json


class CapabilityProbeError(ValueError):
    pass


def _differences(before: object, after: object, path: str = "$") -> list[dict[str, object]]:
    if isinstance(before, dict) and isinstance(after, dict):
        result: list[dict[str, object]] = []
        for key in sorted(set(before) | set(after), key=str):
            child = f"{path}.{key}"
            if key not in before:
                result.append({"path": child, "kind": "added", "before": None, "after": after[key]})
            elif key not in after:
                result.append({"path": child, "kind": "removed", "before": before[key], "after": None})
            else:
                result.extend(_differences(before[key], after[key], child))
        return result

    if isinstance(before, list) and isinstance(after, list):
        result = []
        common = min(len(before), len(after))
        for index in range(common):
            result.extend(_differences(before[index], after[index], f"{path}[{index}]"))
        for index in range(common, len(before)):
            result.append({"path": f"{path}[{index}]", "kind": "removed", "before": before[index], "after": None})
        for index in range(common, len(after)):
            result.append({"path": f"{path}[{index}]", "kind": "added", "before": None, "after": after[index]})
        return result

    if before != after:
        return [{"path": path, "kind": "changed", "before": before, "after": after}]
    return []


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value))


async def capture_capability_samples(
    *,
    executable: Path,
    expected_executable_sha256: str,
    output_dir: Path,
    client_factory: Callable[[Path], Any] | None = None,
) -> dict[str, object]:
    executable = Path(executable)
    output_dir = Path(output_dir)

    if not executable.exists() or not executable.is_file():
        raise CapabilityProbeError("OCS_EXECUTABLE_MISSING")
    if sha256_file(executable) != expected_executable_sha256:
        raise CapabilityProbeError("OCS_EXECUTABLE_HASH_MISMATCH")
    if output_dir.exists():
        raise CapabilityProbeError("PROBE_OUTPUT_ALREADY_EXISTS")
    output_dir.mkdir(parents=True, exist_ok=False)

    factory = client_factory or _default_client_factory
    async with factory(executable) as client:
        tools = await _tool_names(client)
        if not {"ocs_sessions", "ocs_read"}.issubset(tools):
            raise CapabilityProbeError("OCS_READ_SURFACE_MISSING")

        sessions_payload = _mapping(await client.call_tool("ocs_sessions", {"launch_if_none": False}))
        sessions = sessions_payload.get("result")
        if not isinstance(sessions, list) or len(sessions) != 1 or not isinstance(sessions[0], dict):
            raise CapabilityProbeError("OCS_SESSION_AMBIGUOUS")
        session_id = sessions[0].get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise CapabilityProbeError("OCS_SESSION_ID_MISSING")

        samples: list[dict[str, Any]] = []
        for _ in range(2):
            payload = _mapping(
                await client.call_tool(
                    "ocs_read",
                    {"ocs_session_id": session_id, "op": "capabilities"},
                )
            )
            _validate_capabilities_payload(payload)
            samples.append(payload)

    differences = _differences(samples[0], samples[1])
    raw_sha256 = [sha256_json(sample) for sample in samples]
    result: dict[str, object] = {
        "mode": "READ_ONLY_CAPABILITY_PROBE",
        "mutation_authorized": False,
        "identity_classification_performed": False,
        "session_id": session_id,
        "tools": sorted(tools),
        "sample_count": 2,
        "raw_sha256": raw_sha256,
        "difference_count": len(differences),
        "differences": differences,
    }

    _write_json(output_dir / "capabilities-1.json", samples[0])
    _write_json(output_dir / "capabilities-2.json", samples[1])
    _write_json(output_dir / "capabilities-diff.json", {"differences": differences})
    _write_json(output_dir / "capabilities-probe-result.json", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cew-cad-capability-probe",
        description="Read-only two-sample OpenCADStudio capability drift probe.",
    )
    parser.add_argument("--ocs-executable", required=True, type=Path)
    parser.add_argument("--ocs-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = asyncio.run(
        capture_capability_samples(
            executable=args.ocs_executable,
            expected_executable_sha256=args.ocs_sha256,
            output_dir=args.output_dir,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
