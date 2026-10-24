from __future__ import annotations

import asyncio
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path

from cew_cad_gateway.adapters.opencadstudio import OpenCADStudioAdapter, OpenCADStudioError
from cew_cad_gateway.types import CreatePolyline, DocumentIdentity


class FakeClient:
    def __init__(self, exe_path) -> None:
        self.exe_path = exe_path
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def list_tools(self):
        return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "ocs_sessions":
            return {"result": [{"ok": True, "session_id": "s1", "document_id": 1, "revision": 7, "bridge": {"name": "OpenCADStudio", "version": "2026.41", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 7}], "command": {"status": "idle"}}]}
        if name == "ocs_read" and arguments.get("op") == "capabilities":
            return {
                "ok": True,
                "api": "ocs-cad-automation",
                "version": 1,
                "bridge": {"name": "OpenCADStudio", "version": "2026.41", "build_rev": "rev1", "tool_schema": "ts1"},
                "concurrency": {"document_id": True, "request_id": True, "revision": True},
                "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
                "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
                "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
                "records": {"collections": [], "filters": []},
                "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
            }
        if name == "ocs_read" and arguments.get("op") == "state":
            return {"ok": True, "document_id": 1, "revision": 7, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 7}], "command": {"status": "idle"}}
        if name == "ocs_execute":
            request = arguments["request"]
            if request["op"] == "save_verified":
                return {"ok": True, "status": "completed", "semantic_verification_passed": True, "sha256": "2" * 64, "actual_version": "2018"}
            return {"status": "completed", "revision": 8, "changed_entities": ["A1"]}
        raise AssertionError((name, arguments))


class MutationCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.exe = Path(self.tmp.name) / "OpenCADStudio.exe"
        self.exe.write_bytes(b"fake")
        self.client = FakeClient(self.exe)

        @asynccontextmanager
        async def factory(_):
            yield self.client

        self.adapter = OpenCADStudioAdapter(self.exe, client_factory=factory)
        import hashlib

        expected_sha = hashlib.sha256(b"fake").hexdigest()
        self.expected = DocumentIdentity(path=str(self.exe), sha256=expected_sha, document_id=1, revision=7)

    def test_create_polyline_compiles_only_numeric_internal_pline_template(self) -> None:
        operation = CreatePolyline(layer="CEW-LAB", points=((0.0, 0.0), (4.5, 0.0), (4.5, 3.0)), closed=True)
        result = asyncio.run(self.adapter.apply_operation(operation, request_id="req-1", expected=self.expected))
        self.assertEqual(result["status"], "completed")
        execute = [args for name, args in self.client.calls if name == "ocs_execute"]
        self.assertEqual(len(execute), 1)
        request = execute[0]["request"]
        self.assertEqual(request["op"], "run")
        self.assertEqual(request["request_id"], "req-1")
        self.assertEqual(request["document_id"], 1)
        self.assertEqual(request["revision"], 7)
        self.assertEqual(request["cmd"], "PLINE 0,0 4.5,0 4.5,3 C")

    def test_wrong_layer_and_non_polyline_operation_are_rejected_before_execute(self) -> None:
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(self.adapter.apply_operation(CreatePolyline(layer="WALLS", points=((0.0, 0.0), (1.0, 0.0))), request_id="req-2", expected=self.expected))
        self.assertEqual([name for name, _ in self.client.calls if name == "ocs_execute"], [])

    def test_save_verified_requires_absolute_new_path_and_compiles_no_overwrite_request(self) -> None:
        output = Path(self.tmp.name) / "verified.dwg"
        result = asyncio.run(self.adapter.save_verified(output, target_format="dwg", target_version="2018", expected=self.expected))
        self.assertTrue(result["ok"])
        execute = [args for name, args in self.client.calls if name == "ocs_execute"]
        self.assertEqual(len(execute), 1)
        request = execute[0]["request"]
        self.assertEqual(request["op"], "save_verified")
        self.assertEqual(request["path"], str(output.resolve()))
        self.assertEqual(request["target_format"], "dwg")
        self.assertEqual(request["target_version"], "2018")
        self.assertIs(request["overwrite"], False)
        self.assertRegex(request["request_id"], r"^cew-cad-save-[0-9a-f]{32}$")

    def test_save_verified_rejects_relative_existing_or_stale_target_before_execute(self) -> None:
        relative = Path("relative.dwg")
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(self.adapter.save_verified(relative, target_format="dwg", target_version="2018", expected=self.expected))

        existing = Path(self.tmp.name) / "existing.dwg"
        existing.write_bytes(b"x")
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(self.adapter.save_verified(existing, target_format="dwg", target_version="2018", expected=self.expected))

        stale = DocumentIdentity(path=str(self.exe), sha256="0" * 64, document_id=1, revision=6)
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(self.adapter.save_verified(Path(self.tmp.name) / "new.dwg", target_format="dwg", target_version="2018", expected=stale))
        self.assertEqual([name for name, _ in self.client.calls if name == "ocs_execute"], [])


if __name__ == "__main__":
    unittest.main()