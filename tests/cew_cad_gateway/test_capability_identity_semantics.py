from __future__ import annotations

import asyncio
import copy
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path

from cew_cad_gateway.adapters.opencadstudio import OpenCADStudioAdapter
from cew_cad_gateway.canonical import sha256_file


_REAL_CAPABILITIES = {
    "api": "ocs-cad-automation",
    "bridge": {
        "build_profile": "release",
        "build_rev": "b6fbac39ffc7",
        "name": "OpenCADStudio",
        "tool_schema": "d15005e14fc00154501db5d261cb9febae1bcc61f6d9b850e91b7fd1879c3b8e",
        "version": "2026.42",
    },
    "concurrency": {"document_id": True, "request_id": True, "revision": True},
    "editor": {
        "capture": True,
        "commands": True,
        "events": True,
        "files": True,
        "properties": True,
        "selection": True,
    },
    "geometry": {
        "interactive_commands": True,
        "kernel_measurements": True,
        "query": True,
        "spatial_filters": True,
    },
    "ok": True,
    "operations": {
        "batch": True,
        "close": True,
        "entities_create": True,
        "entities_delete": True,
        "entities_transform": True,
        "file_identity": True,
        "plot": True,
        "view_focus": True,
        "wblock": True,
    },
    "records": {
        "collections": [
            {"count": 3, "mutable": True, "name": "entities", "root_type": "EntityType"},
            {"count": 48, "mutable": True, "name": "objects", "root_type": "ObjectType"},
            {"count": 2, "mutable": True, "name": "layers", "root_type": "Layer"},
            {"count": 260, "mutable": False, "name": "classes", "root_type": "DxfClass"},
        ],
        "describe": "record_schema",
        "filters": ["eq", "ne", "contains", "exists"],
        "path": "RFC 6901 JSON Pointer relative to properties",
        "read": "records",
        "write": "set_properties",
    },
    "transactions": {
        "atomic_property_updates": True,
        "batch": True,
        "redo": True,
        "undo": True,
    },
    "version": 1,
}


class _CapabilityClient:
    def __init__(self, *, capabilities: dict[str, object], drawing: Path) -> None:
        self.capabilities = capabilities
        self.drawing = drawing

    async def list_tools(self):
        return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}

    async def call_tool(self, name: str, arguments: dict[str, object]):
        if name == "ocs_sessions":
            return {
                "result": [
                    {
                        "session_id": "session-lab005",
                        "bridge": {
                            "name": "OpenCADStudio",
                            "version": "2026.42",
                            "build_rev": "b6fbac39ffc7",
                            "tool_schema": "d15005e14fc00154501db5d261cb9febae1bcc61f6d9b850e91b7fd1879c3b8e",
                        },
                    }
                ]
            }
        if name == "ocs_read" and arguments.get("op") == "capabilities":
            return self.capabilities
        if name == "ocs_read" and arguments.get("op") == "state":
            return {
                "ok": True,
                "document_id": 3,
                "revision": 3,
                "documents": [{"id": 3, "path": str(self.drawing), "revision": 3}],
                "command": {"status": "idle"},
            }
        raise AssertionError((name, arguments))


def _factory(client: _CapabilityClient):
    @asynccontextmanager
    async def factory(_executable: Path):
        yield client

    return factory


class CapabilityIdentitySemanticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.exe = root / "OpenCADStudio.exe"
        self.exe.write_bytes(b"fake-ocs")
        self.drawing = root / "lab.dwg"
        self.drawing.write_bytes(b"unchanged-source")

    def _status(self, capabilities: dict[str, object]):
        client = _CapabilityClient(capabilities=capabilities, drawing=self.drawing)
        adapter = OpenCADStudioAdapter(
            self.exe,
            expected_executable_sha256=sha256_file(self.exe),
            client_factory=_factory(client),
        )
        return asyncio.run(adapter.status())

    def test_document_record_counts_do_not_change_capability_identity(self) -> None:
        before = copy.deepcopy(_REAL_CAPABILITIES)
        after = copy.deepcopy(_REAL_CAPABILITIES)
        before["records"]["collections"][0]["count"] = 2
        before["records"]["collections"][1]["count"] = 47

        before_status = self._status(before)
        after_status = self._status(after)

        self.assertEqual(before_status.capabilities, after_status.capabilities)

    def test_real_operation_capability_change_changes_identity(self) -> None:
        before = copy.deepcopy(_REAL_CAPABILITIES)
        after = copy.deepcopy(_REAL_CAPABILITIES)
        after["operations"]["entities_create"] = False

        before_status = self._status(before)
        after_status = self._status(after)

        self.assertNotEqual(before_status.capabilities, after_status.capabilities)

    def test_record_schema_change_changes_identity(self) -> None:
        before = copy.deepcopy(_REAL_CAPABILITIES)
        after = copy.deepcopy(_REAL_CAPABILITIES)
        after["records"]["collections"][0]["root_type"] = "DifferentEntityType"

        before_status = self._status(before)
        after_status = self._status(after)

        self.assertNotEqual(before_status.capabilities, after_status.capabilities)


if __name__ == "__main__":
    unittest.main()
