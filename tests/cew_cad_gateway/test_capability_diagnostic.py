from __future__ import annotations

import asyncio
import importlib
import json
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path


class CapabilityDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.exe = self.root / "OpenCADStudio.exe"
        self.exe.write_bytes(b"fake-ocs")
        self.output = self.root / "diagnostic"

    def _load_capture(self):
        try:
            module = importlib.import_module("cew_cad_gateway.capability_diagnostic")
        except ModuleNotFoundError:
            self.fail("CEW-CAD-INT-02 read-only capability diagnostic is missing")
        capture = getattr(module, "capture_capability_diagnostic", None)
        self.assertTrue(callable(capture), "capture_capability_diagnostic is missing")
        return capture

    def test_diagnostic_reads_capabilities_twice_without_execute_and_writes_canonical_diff(self) -> None:
        capture = self._load_capture()

        first = {
            "ok": True,
            "api": "ocs-cad-automation",
            "version": 1,
            "bridge": {
                "name": "OpenCADStudio",
                "version": "2026.42",
                "build_rev": "b6fbac39ffc7",
                "tool_schema": "schema-1",
            },
            "geometry": {"query": True},
            "operations": {"audit": True, "capture": True, "verified_save": True},
            "runtime": {"nonce": "first"},
        }
        second = {
            **first,
            "runtime": {"nonce": "second"},
        }

        class FakeClient:
            def __init__(self) -> None:
                self.calls: list[tuple[str, dict[str, object]]] = []
                self.capability_reads = 0

            async def list_tools(self):
                return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}

            async def call_tool(self, name, arguments):
                self.calls.append((name, arguments))
                if name == "ocs_sessions":
                    return {
                        "result": [{
                            "session_id": "s1",
                            "bridge": {
                                "name": "OpenCADStudio",
                                "version": "2026.42",
                                "build_rev": "b6fbac39ffc7",
                                "tool_schema": "schema-1",
                            },
                        }]
                    }
                if name == "ocs_read" and arguments.get("op") == "capabilities":
                    payload = first if self.capability_reads == 0 else second
                    self.capability_reads += 1
                    return payload
                raise AssertionError((name, arguments))

        client = FakeClient()

        @asynccontextmanager
        async def factory(_executable: Path):
            yield client

        result = asyncio.run(
            capture(
                executable=self.exe,
                expected_executable_sha256=None,
                output_dir=self.output,
                client_factory=factory,
            )
        )

        self.assertEqual(client.capability_reads, 2)
        self.assertFalse(any(name == "ocs_execute" for name, _ in client.calls))
        self.assertEqual(
            [name for name, _ in client.calls],
            ["ocs_sessions", "ocs_read", "ocs_read"],
        )
        self.assertEqual(
            [args.get("op") for name, args in client.calls if name == "ocs_read"],
            ["capabilities", "capabilities"],
        )

        first_path = Path(result["first_payload_path"])
        second_path = Path(result["second_payload_path"])
        diff_path = Path(result["diff_path"])
        self.assertTrue(first_path.is_file())
        self.assertTrue(second_path.is_file())
        self.assertTrue(diff_path.is_file())
        self.assertEqual(json.loads(first_path.read_text(encoding="utf-8")), first)
        self.assertEqual(json.loads(second_path.read_text(encoding="utf-8")), second)

        diff = json.loads(diff_path.read_text(encoding="utf-8"))
        self.assertEqual(diff["session_id"], "s1")
        self.assertEqual(diff["cad_build"], "2026.42@b6fbac39ffc7")
        self.assertEqual(diff["changed_paths"], ["runtime.nonce"])
        self.assertNotEqual(diff["first_sha256"], diff["second_sha256"])


if __name__ == "__main__":
    unittest.main()
