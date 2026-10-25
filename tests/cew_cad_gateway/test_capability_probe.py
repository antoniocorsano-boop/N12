from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from cew_cad_gateway.canonical import sha256_file
from scripts.cew_cad_capability_probe import capture_capability_samples


class FakeTool:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeToolList:
    def __init__(self, names: list[str]) -> None:
        self.tools = [FakeTool(name) for name in names]


class FakeCapabilityClient:
    def __init__(self, samples: list[dict[str, object]]) -> None:
        self.samples = list(samples)
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def list_tools(self):
        return FakeToolList(["ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"])

    async def call_tool(self, name: str, arguments: dict[str, object]):
        self.calls.append((name, dict(arguments)))
        if name == "ocs_sessions":
            return {
                "result": [
                    {
                        "session_id": "session-probe",
                        "bridge": {"name": "ocs", "version": "2026.42", "build_rev": "b6fbac39ffc7"},
                    }
                ]
            }
        if name == "ocs_read" and arguments.get("op") == "capabilities":
            if not self.samples:
                raise AssertionError("probe requested too many samples")
            return self.samples.pop(0)
        raise AssertionError((name, arguments))


class CapabilityProbeTests(unittest.TestCase):
    def test_probe_reads_two_raw_capability_payloads_and_never_executes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / "OpenCADStudio.exe"
            executable.write_bytes(b"fake-ocs")
            output = root / "evidence"
            first = {
                "ok": True,
                "api": "ocs-cad-automation",
                "version": 1,
                "geometry": {"query": True},
                "operations": {"entities_create": True},
                "runtime_note": "sample-a",
            }
            second = {
                **first,
                "runtime_note": "sample-b",
            }
            client = FakeCapabilityClient([first, second])

            class Factory:
                async def __aenter__(self): return client
                async def __aexit__(self, exc_type, exc, tb): return False

            result = asyncio.run(
                capture_capability_samples(
                    executable=executable,
                    expected_executable_sha256=sha256_file(executable),
                    output_dir=output,
                    client_factory=lambda _: Factory(),
                )
            )

            self.assertEqual(result["session_id"], "session-probe")
            self.assertEqual(result["sample_count"], 2)
            self.assertNotEqual(result["raw_sha256"][0], result["raw_sha256"][1])
            self.assertEqual(result["difference_count"], 1)
            self.assertEqual(result["differences"][0]["path"], "$.runtime_note")

            names = [name for name, _ in client.calls]
            self.assertEqual(names, ["ocs_sessions", "ocs_read", "ocs_read"])
            self.assertNotIn("ocs_execute", names)
            self.assertNotIn("ocs_capture", names)

            sample_1 = json.loads((output / "capabilities-1.json").read_text(encoding="utf-8"))
            sample_2 = json.loads((output / "capabilities-2.json").read_text(encoding="utf-8"))
            diff = json.loads((output / "capabilities-diff.json").read_text(encoding="utf-8"))
            summary = json.loads((output / "capabilities-probe-result.json").read_text(encoding="utf-8"))
            self.assertEqual(sample_1, first)
            self.assertEqual(sample_2, second)
            self.assertEqual(diff["differences"], result["differences"])
            self.assertEqual(summary["mode"], "READ_ONLY_CAPABILITY_PROBE")
            self.assertFalse(summary["mutation_authorized"])
            self.assertFalse(summary["identity_classification_performed"])

    def test_probe_rejects_executable_hash_mismatch_before_mcp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = root / "OpenCADStudio.exe"
            executable.write_bytes(b"fake-ocs")
            called = False

            def factory(_):
                nonlocal called
                called = True
                raise AssertionError("MCP must not open after executable hash mismatch")

            with self.assertRaisesRegex(ValueError, "OCS_EXECUTABLE_HASH_MISMATCH"):
                asyncio.run(
                    capture_capability_samples(
                        executable=executable,
                        expected_executable_sha256="0" * 64,
                        output_dir=root / "evidence",
                        client_factory=factory,
                    )
                )
            self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
