from __future__ import annotations

import hashlib
import json
import math
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from ..canonical import sha256_file, sha256_json
from ..types import CADOperation, CADStatus, CapabilityIdentity, CreatePolyline, DocumentIdentity

_REQUIRED_TOOLS = {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
_REQUIRED_CAPABILITIES = {"query", "audit", "capture", "save_verified"}


class OpenCADStudioError(ValueError):
    pass


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    structured = getattr(value, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    structured = getattr(value, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    content = getattr(value, "content", None)
    if isinstance(content, list):
        for item in content:
            text = getattr(item, "text", None)
            if isinstance(text, str):
                try:
                    decoded = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(decoded, dict):
                    return decoded
    raise OpenCADStudioError("INVALID_MCP_RESPONSE")


async def _tool_names(client: Any) -> set[str]:
    result = await client.list_tools()
    if isinstance(result, set) and all(isinstance(item, str) for item in result):
        return set(result)
    tools = getattr(result, "tools", result)
    if isinstance(tools, (list, tuple, set)):
        names: set[str] = set()
        for item in tools:
            if isinstance(item, str):
                names.add(item)
            else:
                name = getattr(item, "name", None)
                if isinstance(name, str):
                    names.add(name)
        return names
    raise OpenCADStudioError("INVALID_TOOL_LIST")


def _format_number(value: float) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise OpenCADStudioError("INVALID_POLYLINE_COORDINATE")
    text = format(float(value), ".15g")
    return "0" if text == "-0" else text


def _compile_polyline(operation: CreatePolyline) -> str:
    if operation.layer != "CEW-LAB":
        raise OpenCADStudioError("CREATION_LAYER_NOT_AUTHORIZED")
    if len(operation.points) < 2:
        raise OpenCADStudioError("POLYLINE_TOO_SHORT")
    tokens = [f"{_format_number(x)},{_format_number(y)}" for x, y in operation.points]
    suffix = " C" if operation.closed else ""
    return "PLINE " + " ".join(tokens) + suffix


@asynccontextmanager
async def _default_client_factory(executable: Path) -> AsyncIterator[Any]:
    from mcp import Client, StdioServerParameters

    params = StdioServerParameters(command=str(executable), args=["--mcp"])
    async with Client(params) as client:
        yield client


class OpenCADStudioAdapter:
    def __init__(
        self,
        executable: Path,
        expected_executable_sha256: str | None = None,
        *,
        client_factory: Callable[[Path], Any] | None = None,
    ) -> None:
        self.executable = executable
        self.expected_executable_sha256 = expected_executable_sha256
        self._client_factory = client_factory or _default_client_factory
        self._bound_session_id: str | None = None
        self._bound_document_id: int | None = None
        self._bound_document_path: str | None = None

    def _verify_executable(self) -> None:
        if not self.executable.exists() or not self.executable.is_file():
            raise OpenCADStudioError("OCS_EXECUTABLE_MISSING")
        if self.expected_executable_sha256 is not None:
            observed = sha256_file(self.executable)
            if observed != self.expected_executable_sha256:
                raise OpenCADStudioError("OCS_EXECUTABLE_HASH_MISMATCH")

    async def _call(self, client: Any, name: str, arguments: dict[str, object]) -> dict[str, Any]:
        return _mapping(await client.call_tool(name, arguments))

    async def status(self) -> CADStatus:
        self._verify_executable()
        async with self._client_factory(self.executable) as client:
            tools = await _tool_names(client)
            if not _REQUIRED_TOOLS.issubset(tools):
                raise OpenCADStudioError("OCS_REQUIRED_TOOL_MISSING")

            sessions_payload = await self._call(client, "ocs_sessions", {})
            sessions = sessions_payload.get("sessions")
            if not isinstance(sessions, list) or len(sessions) != 1:
                raise OpenCADStudioError("OCS_SESSION_AMBIGUOUS")
            session = sessions[0]
            if not isinstance(session, dict) or not isinstance(session.get("session_id"), str) or not session["session_id"]:
                raise OpenCADStudioError("OCS_SESSION_INVALID")
            session_id = session["session_id"]

            capabilities_payload = await self._call(
                client,
                "ocs_read",
                {"ocs_session_id": session_id, "op": "capabilities"},
            )
            build = capabilities_payload.get("build") or capabilities_payload.get("version")
            capability_map = capabilities_payload.get("capabilities")
            if not isinstance(build, str) or not build:
                raise OpenCADStudioError("OCS_BUILD_MISSING")
            if not isinstance(capability_map, dict):
                raise OpenCADStudioError("OCS_CAPABILITIES_INVALID")
            if any(capability_map.get(name) is not True for name in _REQUIRED_CAPABILITIES):
                raise OpenCADStudioError("OCS_REQUIRED_CAPABILITY_MISSING")

            state_payload = await self._call(
                client,
                "ocs_read",
                {"ocs_session_id": session_id, "op": "state"},
            )
            document_payload = state_payload.get("document") if isinstance(state_payload.get("document"), dict) else state_payload
            document_id = document_payload.get("document_id")
            revision = document_payload.get("revision")
            path = document_payload.get("path")
            source_sha256 = document_payload.get("source_sha256") or document_payload.get("sha256")
            command = state_payload.get("command")
            if command is None and isinstance(document_payload.get("command"), dict):
                command = document_payload.get("command")

            if not isinstance(document_id, int) or isinstance(document_id, bool) or document_id < 1:
                raise OpenCADStudioError("OCS_DOCUMENT_ID_INVALID")
            if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
                raise OpenCADStudioError("OCS_REVISION_INVALID")
            if not isinstance(path, str) or not path:
                raise OpenCADStudioError("OCS_DOCUMENT_PATH_MISSING")
            if not isinstance(source_sha256, str) or len(source_sha256) != 64:
                raise OpenCADStudioError("OCS_SOURCE_HASH_MISSING")
            if isinstance(command, dict):
                command_status = command.get("status")
                if command_status not in (None, "idle", "completed"):
                    raise OpenCADStudioError("OCS_INTERACTIVE_STATE_ACTIVE")

            if self._bound_session_id is None:
                self._bound_session_id = session_id
                self._bound_document_id = document_id
                self._bound_document_path = path
            else:
                if session_id != self._bound_session_id:
                    raise OpenCADStudioError("OCS_SESSION_CHANGED")
                if document_id != self._bound_document_id or path != self._bound_document_path:
                    raise OpenCADStudioError("OCS_DOCUMENT_CHANGED")

            return CADStatus(
                session_id=session_id,
                document=DocumentIdentity(
                    path=path,
                    sha256=source_sha256,
                    document_id=document_id,
                    revision=revision,
                ),
                capabilities=CapabilityIdentity(
                    cad_build=build,
                    capabilities_sha256=sha256_json(capabilities_payload),
                ),
                path_class=None,
            )

    async def inspect(self, request: dict[str, object]) -> dict[str, object]:
        status = await self.status()
        async with self._client_factory(self.executable) as client:
            payload = dict(request)
            payload.setdefault("op", "query")
            return await self._call(client, "ocs_read", {"ocs_session_id": status.session_id, **payload})

    async def measure(self, request: dict[str, object]) -> dict[str, object]:
        return await self.inspect(request)

    async def audit(self, target: dict[str, object]) -> dict[str, object]:
        status = await self.status()
        return await self._read_with_status(status, "audit", target)

    async def capture(self, request: dict[str, object]) -> dict[str, object]:
        status = await self.status()
        async with self._client_factory(self.executable) as client:
            return await self._call(client, "ocs_capture", {"ocs_session_id": status.session_id, **request})

    async def _read_with_status(self, status: CADStatus, op: str, parameters: dict[str, object]) -> dict[str, object]:
        async with self._client_factory(self.executable) as client:
            return await self._call(
                client,
                "ocs_read",
                {"ocs_session_id": status.session_id, "op": op, "parameters": parameters},
            )

    async def apply_operation(
        self,
        operation: CADOperation,
        *,
        request_id: str,
        expected: DocumentIdentity,
    ) -> dict[str, object]:
        if not isinstance(operation, CreatePolyline):
            raise OpenCADStudioError("MUTATION_TYPE_NOT_AUTHORIZED")
        if not isinstance(request_id, str) or not request_id or len(request_id.encode("utf-8")) > 128:
            raise OpenCADStudioError("INVALID_REQUEST_ID")
        cmd = _compile_polyline(operation)
        status = await self.status()
        if status.document != expected:
            raise OpenCADStudioError("EXPECTED_DOCUMENT_STATE_MISMATCH")
        async with self._client_factory(self.executable) as client:
            return await self._call(
                client,
                "ocs_execute",
                {
                    "ocs_session_id": status.session_id,
                    "response_detail": "changed_entities",
                    "request": {
                        "op": "run",
                        "request_id": request_id,
                        "document_id": expected.document_id,
                        "revision": expected.revision,
                        "cmd": cmd,
                    },
                },
            )

    async def operation_status(self, request_id: str) -> dict[str, object]:
        status = await self.status()
        return await self._read_with_status(status, "operation_status", {"request_id": request_id})

    async def save_verified(
        self,
        path: Path,
        *,
        target_format: str,
        target_version: str,
        expected: DocumentIdentity,
    ) -> dict[str, object]:
        if not path.is_absolute():
            raise OpenCADStudioError("VERIFIED_PATH_MUST_BE_ABSOLUTE")
        resolved = path.resolve()
        if resolved.exists():
            raise OpenCADStudioError("VERIFIED_OUTPUT_ALREADY_EXISTS")
        if not resolved.parent.exists() or not resolved.parent.is_dir():
            raise OpenCADStudioError("VERIFIED_OUTPUT_PARENT_MISSING")
        if target_format not in {"dwg", "dxf"} or not target_version:
            raise OpenCADStudioError("INVALID_VERIFIED_TARGET")

        status = await self.status()
        if status.document != expected:
            raise OpenCADStudioError("EXPECTED_DOCUMENT_STATE_MISMATCH")
        material = f"{resolved}|{target_format}|{target_version}|{expected.document_id}|{expected.revision}"
        request_id = "cew-cad-save-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
        async with self._client_factory(self.executable) as client:
            return await self._call(
                client,
                "ocs_execute",
                {
                    "ocs_session_id": status.session_id,
                    "response_detail": "full",
                    "request": {
                        "op": "save_verified",
                        "request_id": request_id,
                        "path": str(resolved),
                        "target_format": target_format,
                        "target_version": target_version,
                        "overwrite": False,
                    },
                },
            )
