from __future__ import annotations

import asyncio
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path

from cew_cad_gateway.adapters.opencadstudio import OpenCADStudioAdapter, OpenCADStudioError
from cew_cad_gateway.canonical import sha256_file


class FakeClient:
    def __init__(self, *, tools=None, sessions=None, capabilities=None, states=None):
        self.tools = tools or {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
        self.sessions = sessions or [{"session_id": "s1"}]
        self.capabilities = capabilities or {
            "build": "2026.41",
            "capabilities": {"query": True, "audit": True, "capture": True, "save_verified": True},
        }
        self.states = list(states or [{
            "document_id": 1,
            "revision": 7,
            "path": "C:/lab/working/lab.dwg",
            "source_sha256": "0" * 64,
            "command": {"status": "idle"},
        }])
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def list_tools(self) -> set[str]:
        return set(self.tools)

    async def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        self.calls.append((name, arguments))
        if name == "ocs_sessions":
            return {"sessions": self.sessions}
        if name == "ocs_read" and arguments.get("op") == "capabilities":
            return self.capabilities
        if name == "ocs_read" and arguments.get("op") == "state":
            if len(self.states) > 1:
                return self.states.pop(0)
            return self.states[0]
        raise AssertionError((name, arguments))


class OpenCADStudioAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.exe = Path(self.tmp.name) / "OpenCADStudio.exe"
        self.exe.write_bytes(b"fake-ocs")

    def factory(self, client: FakeClient):
        @asynccontextmanager
        async def make_client(_executable: Path):
            yield client
        return make_client

    def test_status_handshake_discovers_tools_capabilities_and_document(self) -> None:
        client = FakeClient()
        adapter = OpenCADStudioAdapter(
            self.exe,
            expected_executable_sha256=sha256_file(self.exe),
            client_factory=self.factory(client),
        )
        status = asyncio.run(adapter.status())
        self.assertEqual(status.session_id, "s1")
        self.assertEqual(status.document.document_id, 1)
        self.assertEqual(status.document.revision, 7)
        self.assertEqual(status.capabilities.cad_build, "2026.41")
        self.assertIsNone(status.path_class)
        self.assertEqual([call[0] for call in client.calls], ["ocs_sessions", "ocs_read", "ocs_read"])

    def test_rejects_missing_required_tool(self) -> None:
        client = FakeClient(tools={"ocs_sessions", "ocs_read", "ocs_capture"})
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter.status())

    def test_rejects_missing_required_capability(self) -> None:
        client = FakeClient(capabilities={"build": "2026.41", "capabilities": {"query": True, "audit": True}})
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter.status())

    def test_rejects_ambiguous_sessions_missing_path_and_waiting_command(self) -> None:
        cases = [
            FakeClient(sessions=[{"session_id": "s1"}, {"session_id": "s2"}]),
            FakeClient(states=[{"document_id": 1, "revision": 1, "path": "", "source_sha256": "0" * 64, "command": {"status": "idle"}}]),
            FakeClient(states=[{"document_id": 1, "revision": 1, "path": "C:/lab.dwg", "source_sha256": "0" * 64, "command": {"status": "waiting_input"}}]),
        ]
        for client in cases:
            with self.subTest(client=client):
                adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
                with self.assertRaises(OpenCADStudioError):
                    asyncio.run(adapter.status())

    def test_rejects_executable_hash_mismatch(self) -> None:
        adapter = OpenCADStudioAdapter(
            self.exe,
            expected_executable_sha256="f" * 64,
            client_factory=self.factory(FakeClient()),
        )
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter.status())

    def test_rejects_session_or_document_identity_change_after_binding(self) -> None:
        client = FakeClient()
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        asyncio.run(adapter.status())
        client.sessions = [{"session_id": "s2"}]
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter.status())

        client2 = FakeClient(states=[
            {"document_id": 1, "revision": 1, "path": "C:/lab.dwg", "source_sha256": "0" * 64, "command": {"status": "idle"}},
            {"document_id": 2, "revision": 1, "path": "C:/lab.dwg", "source_sha256": "0" * 64, "command": {"status": "idle"}},
        ])
        adapter2 = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client2))
        asyncio.run(adapter2.status())
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter2.status())


if __name__ == "__main__":
    unittest.main()
