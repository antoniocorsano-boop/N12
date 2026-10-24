from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from cew_cad_gateway.adapters.opencadstudio import OpenCADStudioAdapter, OpenCADStudioError, _default_client_factory
from cew_cad_gateway.canonical import sha256_file


class FakeClient:
    def __init__(self, *, tools=None, sessions=None, capabilities=None, states=None, exe_path=None):
        self.tools = tools or {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
        exe_path_str = str(exe_path) if exe_path is not None else "C:/lab/working/lab.dwg"
        # sessions should be a list of full session objects with bridge, documents, etc.
        default_session = {
            "ok": True,
            "session_id": "s1",
            "document_id": 1,
            "revision": 7,
            "bridge": {
                "name": "OpenCADStudio",
                "version": "2026.41",
                "build_rev": "rev1",
                "tool_schema": "ts1",
            },
            "documents": [
                {"id": 1, "path": exe_path_str, "revision": 7, "start": False, "title": "Drawing1", "dirty": False},
            ],
            "command": {"status": "idle"},
        }
        self.sessions = sessions or [default_session]
        # capabilities should be the real payload shape
        self.capabilities = capabilities or {
            "ok": True,
            "api": "ocs-cad-automation",
            "version": 1,
            "bridge": {
                "name": "OpenCADStudio",
                "version": "2026.41",
                "build_rev": "rev1",
                "tool_schema": "ts1",
            },
            "concurrency": {"document_id": True, "request_id": True, "revision": True},
            "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
            "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
            "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
            "records": {"collections": [], "filters": []},
            "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
        }
        # states should be full state objects
        default_state = {
            "ok": True,
            "document_id": 1,
            "revision": 7,
            "documents": [
                {"id": 1, "path": exe_path_str, "revision": 7, "start": False, "title": "Drawing1", "dirty": False},
            ],
            "command": {"status": "idle"},
        }
        self.states = list(states or [default_state])
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def list_tools(self) -> set[str]:
        return set(self.tools)

    async def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        self.calls.append((name, arguments))
        if name == "ocs_sessions":
            return {"result": self.sessions}
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
        client = FakeClient(exe_path=self.exe)
        adapter = OpenCADStudioAdapter(
            self.exe,
            expected_executable_sha256=sha256_file(self.exe),
            client_factory=self.factory(client),
        )
        status = asyncio.run(adapter.status())
        self.assertEqual(status.session_id, "s1")
        self.assertEqual(status.document.document_id, 1)
        self.assertEqual(status.document.revision, 7)
        self.assertEqual(status.capabilities.cad_build, "2026.41@rev1")
        self.assertIsNone(status.path_class)
        self.assertEqual([call[0] for call in client.calls], ["ocs_sessions", "ocs_read", "ocs_read"])

    def test_rejects_missing_required_tool(self) -> None:
        client = FakeClient(tools={"ocs_sessions", "ocs_read", "ocs_capture"}, exe_path=self.exe)
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter.status())

    def test_rejects_missing_required_capability(self) -> None:
        # Missing geometry.query (validated in real contract)
        bad_caps = {
            "ok": True,
            "api": "ocs-cad-automation",
            "version": 1,
            "bridge": {"name": "OpenCADStudio", "version": "2026.41", "build_rev": "rev1", "tool_schema": "ts1"},
            "concurrency": {"document_id": True, "request_id": True, "revision": True},
            "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
            "geometry": {"spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
            "operations": {"capture": True, "verified_save": True, "batch": True},
            "records": {"collections": [], "filters": []},
            "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
        }
        client = FakeClient(capabilities=bad_caps, exe_path=self.exe)
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter.status())

    def test_rejects_ambiguous_sessions_missing_path_and_waiting_command(self) -> None:
        # Multiple sessions
        client1 = FakeClient(
            sessions=[
                {"ok": True, "session_id": "s1", "document_id": 1, "revision": 0, "bridge": {"name": "OpenCADStudio", "version": "2026.41", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe), "revision": 0}], "command": None},
                {"ok": True, "session_id": "s2", "document_id": 1, "revision": 0, "bridge": {"name": "OpenCADStudio", "version": "2026.41", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe), "revision": 0}], "command": None},
            ],
            exe_path=self.exe,
        )
        # Empty path
        client2 = FakeClient(
            states=[{"ok": True, "document_id": 1, "revision": 1, "documents": [{"id": 1, "path": "", "revision": 1}], "command": {"status": "idle"}}],
            exe_path=self.exe,
        )
        # Waiting input
        client3 = FakeClient(
            states=[{"ok": True, "document_id": 1, "revision": 1, "documents": [{"id": 1, "path": str(self.exe), "revision": 1}], "command": {"status": "waiting_input"}}],
            exe_path=self.exe,
        )
        cases = [client1, client2, client3]
        for client in cases:
            with self.subTest(client=client):
                adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
                with self.assertRaises(OpenCADStudioError):
                    asyncio.run(adapter.status())

    def test_rejects_executable_hash_mismatch(self) -> None:
        adapter = OpenCADStudioAdapter(
            self.exe,
            expected_executable_sha256="f" * 64,
            client_factory=self.factory(FakeClient(exe_path=self.exe)),
        )
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter.status())

    def test_rejects_session_or_document_identity_change_after_binding(self) -> None:
        client = FakeClient(exe_path=self.exe)
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        asyncio.run(adapter.status())
        client.sessions = [{"ok": True, "session_id": "s2", "document_id": 1, "revision": 0, "bridge": {"name": "OpenCADStudio", "version": "2026.41", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe), "revision": 0}], "command": None}]
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter.status())

        client2 = FakeClient(
            states=[
                {"ok": True, "document_id": 1, "revision": 1, "documents": [{"id": 1, "path": str(self.exe), "revision": 1}], "command": {"status": "idle"}},
                {"ok": True, "document_id": 2, "revision": 1, "documents": [{"id": 2, "path": str(self.exe), "revision": 1}], "command": {"status": "idle"}},
            ],
            exe_path=self.exe,
        )
        adapter2 = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client2))
        asyncio.run(adapter2.status())
        with self.assertRaises(OpenCADStudioError):
            asyncio.run(adapter2.status())

    # ===== REGRESSION TESTS FOR REAL OCS v2026.42 MCP CONTRACT =====

    def test_default_client_factory_uses_explicit_stdio_transport(self) -> None:
        """
        Regression test for MCP 2.0.0 stdio transport compatibility.

        With mcp==2.0.0, Client() does not accept bare StdioServerParameters.
        The correct form is Client(stdio_client(params)).
        """
        with patch("mcp.Client") as mock_client_class, \
             patch("mcp.stdio_client") as mock_stdio_client, \
             patch("mcp.StdioServerParameters") as mock_params_class:

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            mock_transport = AsyncMock()
            mock_transport.__aenter__ = AsyncMock(return_value=mock_transport)
            mock_transport.__aexit__ = AsyncMock(return_value=None)
            mock_stdio_client.return_value = mock_transport

            mock_params = MagicMock()
            mock_params_class.return_value = mock_params

            exe = Path("C:/fake/OpenCADStudio.exe")

            async def consume():
                async with _default_client_factory(exe) as client:
                    pass

            asyncio.run(consume())

            mock_params_class.assert_called_once_with(command=str(exe), args=["--mcp"])
            mock_stdio_client.assert_called_once_with(mock_params)
            mock_client_class.assert_called_once_with(mock_transport)

    def test_ocs_sessions_returns_result_array_with_bridge(self) -> None:
        """
        Real contract: ocs_sessions returns {"result": [session_objects]}.
        Each session has bridge {name, version, build_rev, tool_schema}.
        """
        real_sessions_payload = {
            "result": [{
                "ok": True,
                "session_id": "sess-123",
                "document_id": 2,
                "revision": 0,
                "bridge": {
                    "name": "OpenCADStudio",
                    "version": "2026.42",
                    "build_rev": "b6fbac39ffc7",
                    "build_profile": "release",
                    "tool_schema": "d15005e14fc00154501db5d261cb9febae1bcc61f6d9b850e91b7fd1879c3b8e",
                },
                "documents": [
                    {"id": 1, "path": None, "revision": 0, "start": True, "title": "Start", "dirty": False},
                    {"id": 2, "path": str(self.exe), "revision": 0, "start": False, "title": "Drawing1", "dirty": False},
                ],
                "capabilities": ["commands", "audit", "capture", "verified_save"],
                "command": None,
            }]
        }

        class RealContractClient:
            def __init__(self):
                self.calls = []
            async def list_tools(self):
                return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
            async def call_tool(self, name, args):
                self.calls.append((name, args))
                if name == "ocs_sessions":
                    return real_sessions_payload
                if name == "ocs_read" and args.get("op") == "capabilities":
                    return {
                        "ok": True,
                        "api": "ocs-cad-automation",
                        "version": 1,
                        "bridge": {
                            "name": "OpenCADStudio",
                            "version": "2026.42",
                            "build_rev": "b6fbac39ffc7",
                            "tool_schema": "d15005e14fc00154501db5d261cb9febae1bcc61f6d9b850e91b7fd1879c3b8e",
                        },
                        "concurrency": {"document_id": True, "request_id": True, "revision": True},
                        "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
                        "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
                        "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
                        "records": {"collections": [], "filters": []},
                        "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
                    }
                if name == "ocs_read" and args.get("op") == "state":
                    return real_sessions_payload["result"][0]
                raise AssertionError((name, args))

        client = RealContractClient()

        @asynccontextmanager
        async def factory(_exe):
            yield client

        adapter = OpenCADStudioAdapter(self.exe, client_factory=factory)
        status = asyncio.run(adapter.status())

        # Verify bridge identity used for cad_build
        self.assertEqual(status.capabilities.cad_build, "2026.42@b6fbac39ffc7")
        self.assertEqual(status.session_id, "sess-123")
        self.assertEqual(status.document.document_id, 2)
        self.assertEqual(status.document.path, str(self.exe))

    def test_capabilities_payload_is_direct_not_nested(self) -> None:
        """
        Real contract: ocs_read op=capabilities returns direct payload:
        {api, bridge, concurrency, editor, geometry, operations, records, transactions, version}
        NOT {"capabilities": {...}}.
        """
        real_caps_payload = {
            "ok": True,
            "api": "ocs-cad-automation",
            "version": 1,
            "bridge": {
                "name": "OpenCADStudio",
                "version": "2026.42",
                "build_rev": "b6fbac39ffc7",
                "tool_schema": "schema-hash",
            },
            "concurrency": {"document_id": True, "request_id": True, "revision": True},
            "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
            "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
            "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
            "records": {"collections": [], "filters": []},
            "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
        }

        class CapsClient:
            def __init__(self, exe_path):
                self.calls = []
                self.exe_path = exe_path
            async def list_tools(self):
                return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
            async def call_tool(self, name, args):
                self.calls.append((name, args))
                if name == "ocs_sessions":
                    return {"result": [{"ok": True, "session_id": "s1", "document_id": 1, "revision": 0, "bridge": {"name": "OpenCADStudio", "version": "2026.42", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 0}], "command": None}]}
                if name == "ocs_read" and args.get("op") == "capabilities":
                    return real_caps_payload
                if name == "ocs_read" and args.get("op") == "state":
                    return {"ok": True, "document_id": 1, "revision": 0, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 0}], "command": None}
                raise AssertionError((name, args))

        client = CapsClient(self.exe)

        @asynccontextmanager
        async def factory(_exe):
            yield client

        adapter = OpenCADStudioAdapter(self.exe, client_factory=factory)
        status = asyncio.run(adapter.status())

        # If we get here without OCS_CAPABILITIES_INVALID, the contract is handled
        self.assertIsNotNone(status.capabilities.cad_build)

    def test_active_document_resolved_via_documents_array(self) -> None:
        """
        Real contract: state has document_id + documents[] array.
        Active document = documents[document_id - 1] (by matching id).
        Path comes from that document object, not from root.
        """
        real_state_payload = {
            "ok": True,
            "document_id": 2,
            "revision": 5,
            "documents": [
                {"id": 1, "path": None, "revision": 0, "start": True, "title": "Start", "dirty": False},
                {"id": 2, "path": "C:/lab/working/cew-cad-lab.dwg", "revision": 5, "start": False, "title": "Drawing1", "dirty": False},
            ],
            "command": None,
        }

        class StateClient:
            def __init__(self, exe_path):
                self.calls = []
                self.exe_path = exe_path
            async def list_tools(self):
                return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
            async def call_tool(self, name, args):
                self.calls.append((name, args))
                if name == "ocs_sessions":
                    return {"result": [{"ok": True, "session_id": "s1", "document_id": 2, "revision": 5, "bridge": {"name": "OpenCADStudio", "version": "2026.42", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": None, "revision": 0}, {"id": 2, "path": str(self.exe_path), "revision": 5}], "command": None}]}
                if name == "ocs_read" and args.get("op") == "capabilities":
                    return {
                        "ok": True,
                        "api": "ocs-cad-automation",
                        "version": 1,
                        "bridge": {
                            "name": "OpenCADStudio",
                            "version": "2026.42",
                            "build_rev": "rev1",
                            "tool_schema": "ts1",
                        },
                        "concurrency": {"document_id": True, "request_id": True, "revision": True},
                        "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
                        "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
                        "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
                        "records": {"collections": [], "filters": []},
                        "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
                    }
                if name == "ocs_read" and args.get("op") == "state":
                    return {
                        "ok": True,
                        "document_id": 2,
                        "revision": 5,
                        "documents": [
                            {"id": 1, "path": None, "revision": 0, "start": True, "title": "Start", "dirty": False},
                            {"id": 2, "path": str(self.exe_path), "revision": 5, "start": False, "title": "Drawing1", "dirty": False},
                        ],
                        "command": None,
                    }
                raise AssertionError((name, args))

        client = StateClient(self.exe)

        @asynccontextmanager
        async def factory(_exe):
            yield client

        adapter = OpenCADStudioAdapter(self.exe, client_factory=factory)
        status = asyncio.run(adapter.status())

        self.assertEqual(status.document.document_id, 2)
        self.assertEqual(status.document.revision, 5)
        self.assertEqual(status.document.path, str(self.exe))

    def test_sha256_computed_from_active_document_path(self) -> None:
        """
        SHA-256 is computed locally from the active document's path,
        not taken from the server response.
        """
        import hashlib
        test_content = b"test dwg content"
        expected_sha = hashlib.sha256(test_content).hexdigest()

        self.exe.write_bytes(test_content)

        class SHAClient:
            def __init__(self, exe_path):
                self.calls = []
                self.exe_path = exe_path
            async def list_tools(self):
                return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
            async def call_tool(self, name, args):
                self.calls.append((name, args))
                if name == "ocs_sessions":
                    return {"result": [{"ok": True, "session_id": "s1", "document_id": 1, "revision": 0, "bridge": {"name": "OpenCADStudio", "version": "2026.42", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 0}], "command": None}]}
                if name == "ocs_read" and args.get("op") == "capabilities":
                    return {
                        "ok": True,
                        "api": "ocs-cad-automation",
                        "version": 1,
                        "bridge": {
                            "name": "OpenCADStudio",
                            "version": "2026.42",
                            "build_rev": "rev1",
                            "tool_schema": "ts1",
                        },
                        "concurrency": {"document_id": True, "request_id": True, "revision": True},
                        "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
                        "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
                        "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
                        "records": {"collections": [], "filters": []},
                        "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
                    }
                if name == "ocs_read" and args.get("op") == "state":
                    return {"ok": True, "document_id": 1, "revision": 0, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 0}], "command": None}
                raise AssertionError((name, args))

        client = SHAClient(self.exe)

        @asynccontextmanager
        async def factory(_exe):
            yield client

        adapter = OpenCADStudioAdapter(self.exe, client_factory=factory)
        status = asyncio.run(adapter.status())

        self.assertEqual(status.document.sha256, expected_sha)

    def test_enforces_policy_required_capabilities(self) -> None:
        """
        The adapter must enforce policy.required_capabilities.
        If policy requires a capability not present in OCS surface, status() must fail closed.
        """
        # Policy requires "custom_capability" which is not in OCS surface
        policy_required = ("query", "audit", "capture", "save_verified", "custom_capability")
        
        class CapabilityClient:
            def __init__(self, exe_path):
                self.calls = []
                self.exe_path = exe_path
            async def list_tools(self):
                return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
            async def call_tool(self, name, args):
                self.calls.append((name, args))
                if name == "ocs_sessions":
                    return {"result": [{"ok": True, "session_id": "s1", "document_id": 1, "revision": 0, "bridge": {"name": "OpenCADStudio", "version": "2026.42", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 0}], "command": None}]}
                if name == "ocs_read" and args.get("op") == "capabilities":
                    return {
                        "ok": True,
                        "api": "ocs-cad-automation",
                        "version": 1,
                        "bridge": {
                            "name": "OpenCADStudio",
                            "version": "2026.42",
                            "build_rev": "rev1",
                            "tool_schema": "ts1",
                        },
                        "concurrency": {"document_id": True, "request_id": True, "revision": True},
                        "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
                        "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
                        "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
                        "records": {"collections": [], "filters": []},
                        "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
                    }
                if name == "ocs_read" and args.get("op") == "state":
                    return {"ok": True, "document_id": 1, "revision": 0, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 0}], "command": None}
                raise AssertionError((name, args))

        client = CapabilityClient(self.exe)

        @asynccontextmanager
        async def factory(_exe):
            yield client

        # Adapter should accept required_capabilities parameter
        adapter = OpenCADStudioAdapter(self.exe, required_capabilities=policy_required, client_factory=factory)
        
        with self.assertRaises(OpenCADStudioError) as cm:
            asyncio.run(adapter.status())
        self.assertEqual(str(cm.exception), "OCS_REQUIRED_CAPABILITY_MISSING")

    def test_inspect_cannot_override_session_id(self) -> None:
        client = FakeClient(exe_path=self.exe)
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        asyncio.run(adapter.status())
        with self.assertRaises(OpenCADStudioError) as cm:
            asyncio.run(adapter.inspect({"ocs_session_id": "attacker-session", "op": "query"}))
        self.assertEqual(str(cm.exception), "OCS_SESSION_OVERRIDE_FORBIDDEN")

    def test_inspect_unauthorized_op_rejected_before_call(self) -> None:
        client = FakeClient(exe_path=self.exe)
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        asyncio.run(adapter.status())
        calls_before = len(client.calls)
        with self.assertRaises(OpenCADStudioError) as cm:
            asyncio.run(adapter.inspect({"op": "capabilities"}))
        self.assertEqual(str(cm.exception), "OCS_INSPECT_OP_NOT_AUTHORIZED")
        self.assertEqual(len(client.calls), calls_before)

    def test_inspect_unauthorized_fields_rejected(self) -> None:
        client = FakeClient(exe_path=self.exe)
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        asyncio.run(adapter.status())
        calls_before = len(client.calls)
        with self.assertRaises(OpenCADStudioError) as cm:
            asyncio.run(adapter.inspect({"op": "query", "evil": True}))
        self.assertEqual(str(cm.exception), "OCS_INSPECT_FIELD_NOT_AUTHORIZED")
        self.assertEqual(len(client.calls), calls_before)

    def test_inspect_authorized_query_works(self) -> None:
        class InspectClient:
            def __init__(self, exe_path):
                self.exe_path = exe_path
                self.calls = []
            async def list_tools(self):
                return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
            async def call_tool(self, name, args):
                self.calls.append((name, args))
                if name == "ocs_sessions":
                    return {"result": [{"ok": True, "session_id": "s1", "document_id": 1, "revision": 0, "bridge": {"name": "OpenCADStudio", "version": "2026.42", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 0}], "command": None}]}
                if name == "ocs_read" and args.get("op") == "capabilities":
                    return {
                        "ok": True,
                        "api": "ocs-cad-automation",
                        "version": 1,
                        "bridge": {"name": "OpenCADStudio", "version": "2026.42", "build_rev": "rev1", "tool_schema": "ts1"},
                        "concurrency": {"document_id": True, "request_id": True, "revision": True},
                        "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
                        "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
                        "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
                        "records": {"collections": [], "filters": []},
                        "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
                    }
                if name == "ocs_read" and args.get("op") == "state":
                    return {"ok": True, "document_id": 1, "revision": 0, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 0}], "command": None}
                if name == "ocs_read" and args.get("op") == "query":
                    assert args.get("ocs_session_id") == "s1"
                    return {"ok": True}
                raise AssertionError((name, args))

        client = InspectClient(self.exe)
        @asynccontextmanager
        async def factory(_exe):
            yield client
        adapter = OpenCADStudioAdapter(self.exe, client_factory=factory)
        asyncio.run(adapter.status())
        res = asyncio.run(adapter.inspect({"op": "query"}))
        self.assertEqual(res, {"ok": True})

    def test_resolve_revision_zero_valid(self) -> None:
        client = FakeClient(
            states=[{"ok": True, "document_id": 1, "revision": 0, "documents": [{"id": 1, "path": str(self.exe), "revision": 5}], "command": {"status": "idle"}}],
            exe_path=self.exe,
        )
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        status = asyncio.run(adapter.status())
        self.assertEqual(status.document.revision, 0)

    def test_resolve_revision_missing_falls_back_to_document(self) -> None:
        client = FakeClient(
            states=[{"ok": True, "document_id": 1, "documents": [{"id": 1, "path": str(self.exe), "revision": 2}], "command": {"status": "idle"}}],
            exe_path=self.exe,
        )
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        status = asyncio.run(adapter.status())
        self.assertEqual(status.document.revision, 2)

    def test_resolve_revision_none_falls_back_to_document(self) -> None:
        client = FakeClient(
            states=[{"ok": True, "document_id": 1, "revision": None, "documents": [{"id": 1, "path": str(self.exe), "revision": 3}], "command": {"status": "idle"}}],
            exe_path=self.exe,
        )
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        status = asyncio.run(adapter.status())
        self.assertEqual(status.document.revision, 3)

    def test_resolve_revision_false_falls_back_to_document(self) -> None:
        client = FakeClient(
            states=[{"ok": True, "document_id": 1, "revision": False, "documents": [{"id": 1, "path": str(self.exe), "revision": 4}], "command": {"status": "idle"}}],
            exe_path=self.exe,
        )
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        status = asyncio.run(adapter.status())
        self.assertEqual(status.document.revision, 4)

    def test_resolve_revision_negative_falls_back_to_document(self) -> None:
        client = FakeClient(
            states=[{"ok": True, "document_id": 1, "revision": -1, "documents": [{"id": 1, "path": str(self.exe), "revision": 6}], "command": {"status": "idle"}}],
            exe_path=self.exe,
        )
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        status = asyncio.run(adapter.status())
        self.assertEqual(status.document.revision, 6)

    def test_resolve_revision_both_invalid_fails(self) -> None:
        client = FakeClient(
            states=[{"ok": True, "document_id": 1, "documents": [{"id": 1, "path": str(self.exe)}], "command": {"status": "idle"}}],
            exe_path=self.exe,
        )
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        with self.assertRaises(OpenCADStudioError) as cm:
            asyncio.run(adapter.status())
        self.assertEqual(str(cm.exception), "OCS_DOCUMENT_REVISION_MISSING")

    def test_resolve_revision_state_none_document_invalid_fails(self) -> None:
        client = FakeClient(
            states=[{"ok": True, "document_id": 1, "revision": None, "documents": [{"id": 1, "path": str(self.exe), "revision": None}], "command": {"status": "idle"}}],
            exe_path=self.exe,
        )
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        with self.assertRaises(OpenCADStudioError) as cm:
            asyncio.run(adapter.status())
        self.assertEqual(str(cm.exception), "OCS_DOCUMENT_REVISION_MISSING")

    def test_status_unreadable_document_raises_ocs_document_unreadable(self) -> None:
        import builtins
        original_sha256_file = __import__('cew_cad_gateway.canonical', fromlist=['sha256_file']).sha256_file
        def fake_sha256_file(path):
            raise OSError("Permission denied")
        client = FakeClient(exe_path=self.exe)
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        with patch('cew_cad_gateway.adapters.opencadstudio.sha256_file', side_effect=OSError("Permission denied")):
            with self.assertRaises(OpenCADStudioError) as cm:
                asyncio.run(adapter.status())
            self.assertEqual(str(cm.exception), "OCS_DOCUMENT_UNREADABLE")
            self.assertIsInstance(cm.exception.__cause__, OSError)


if __name__ == "__main__":
    unittest.main()
