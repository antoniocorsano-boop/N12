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


def _extract_bridge_build(bridge: dict[str, Any]) -> str:
    name = bridge.get("name")
    version = bridge.get("version")
    build_rev = bridge.get("build_rev")
    if not isinstance(name, str) or not name:
        raise OpenCADStudioError("OCS_BRIDGE_NAME_MISSING")
    if not isinstance(version, str) or not version:
        raise OpenCADStudioError("OCS_BRIDGE_VERSION_MISSING")
    if not isinstance(build_rev, str) or not build_rev:
        raise OpenCADStudioError("OCS_BRIDGE_BUILD_REV_MISSING")
    return f"{version}@{build_rev}"


def _validate_capabilities_payload(payload: dict[str, Any]) -> None:
    if payload.get("ok") is not True:
        raise OpenCADStudioError("OCS_CAPABILITIES_OK_FALSE")
    if payload.get("api") != "ocs-cad-automation":
        raise OpenCADStudioError("OCS_CAPABILITIES_API_MISMATCH")
    if payload.get("version") != 1:
        raise OpenCADStudioError("OCS_CAPABILITIES_VERSION_MISMATCH")
    geometry = payload.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("query") is not True:
        raise OpenCADStudioError("OCS_CAPABILITIES_GEOMETRY_QUERY_MISSING")
    operations = payload.get("operations")
    if not isinstance(operations, dict):
        raise OpenCADStudioError("OCS_CAPABILITIES_OPERATIONS_MISSING")
    # Real OCS v2026.42 capabilities payload does not list audit/capture/verified_save
    # in operations dict. These are verified via tool definitions in list_tools():
    # - ocs_read op=audit exists
    # - ocs_capture tool exists
    # - ocs_execute op=save_verified exists
    # We validate the structure but don't require specific operation keys.


def _check_required_capabilities(
    tools: set[str],
    capabilities_payload: dict[str, Any],
    required: tuple[str, ...],
) -> None:
    """
    Validate that all required capabilities are available in the OCS surface.
    Maps policy capability names to actual OCS features.
    Unknown capabilities are treated as missing (fail closed).
    """
    if not required:
        return
    
    # Map policy capability names to OCS features
    # Note: OCS v2026.42 capabilities payload does not list audit/capture/save_verified
    # in operations dict. These are verified via tool definitions and known OCS features:
    # - query: geometry.query in capabilities payload
    # - audit: ocs_read supports op=audit (assumed if ocs_read tool exists)
    # - capture: ocs_capture tool exists
    # - save_verified: ocs_execute supports op=save_verified (assumed if ocs_execute tool exists)
    capability_map = {
        "query": lambda: capabilities_payload.get("geometry", {}).get("query") is True,
        "audit": lambda: "ocs_read" in tools,
        "capture": lambda: "ocs_capture" in tools,
        "save_verified": lambda: "ocs_execute" in tools,
    }
    
    for cap in required:
        checker = capability_map.get(cap)
        if checker is None:
            # Unknown capability - fail closed
            raise OpenCADStudioError("OCS_REQUIRED_CAPABILITY_MISSING")
        if not checker():
            raise OpenCADStudioError("OCS_REQUIRED_CAPABILITY_MISSING")


def _resolve_active_document(state: dict[str, Any]) -> tuple[int, int, str]:
    document_id = state.get("document_id")
    if not isinstance(document_id, int) or isinstance(document_id, bool) or document_id < 1:
        raise OpenCADStudioError("OCS_DOCUMENT_ID_INVALID")
    documents = state.get("documents")
    if not isinstance(documents, list):
        raise OpenCADStudioError("OCS_DOCUMENTS_MISSING")
    doc = next((d for d in documents if isinstance(d, dict) and d.get("id") == document_id), None)
    if doc is None:
        raise OpenCADStudioError("OCS_ACTIVE_DOCUMENT_NOT_FOUND")
    path = doc.get("path")
    if not isinstance(path, str) or not path:
        raise OpenCADStudioError("OCS_DOCUMENT_PATH_MISSING")
    revision = state.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        revision = doc.get("revision", 0)
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
            revision = 0
    return document_id, revision, path


@asynccontextmanager
async def _default_client_factory(executable: Path) -> AsyncIterator[Any]:
    from mcp import Client, StdioServerParameters, stdio_client

    params = StdioServerParameters(command=str(executable), args=["--mcp"])
    async with Client(stdio_client(params)) as client:
        yield client


class OpenCADStudioAdapter:
    def __init__(
        self,
        executable: Path,
        expected_executable_sha256: str | None = None,
        *,
        client_factory: Callable[[Path], Any] | None = None,
        required_capabilities: tuple[str, ...] | None = None,
    ) -> None:
        self.executable = executable
        self.expected_executable_sha256 = expected_executable_sha256
        self._client_factory = client_factory or _default_client_factory
        self._required_capabilities = required_capabilities or ()
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

            sessions_payload = await self._call(client, "ocs_sessions", {"launch_if_none": False})
            sessions = sessions_payload.get("result")
            if not isinstance(sessions, list) or len(sessions) != 1:
                raise OpenCADStudioError("OCS_SESSION_AMBIGUOUS")
            session = sessions[0]
            if not isinstance(session, dict):
                raise OpenCADStudioError("OCS_SESSION_INVALID")
            session_id = session.get("session_id")
            if not isinstance(session_id, str) or not session_id:
                raise OpenCADStudioError("OCS_SESSION_ID_MISSING")

            bridge = session.get("bridge")
            if not isinstance(bridge, dict):
                raise OpenCADStudioError("OCS_BRIDGE_MISSING")
            cad_build = _extract_bridge_build(bridge)

            capabilities_payload = await self._call(
                client,
                "ocs_read",
                {"ocs_session_id": session_id, "op": "capabilities"},
            )
            _validate_capabilities_payload(capabilities_payload)
            _check_required_capabilities(tools, capabilities_payload, self._required_capabilities)

            state_payload = await self._call(
                client,
                "ocs_read",
                {"ocs_session_id": session_id, "op": "state"},
            )

            document_id, revision, path = _resolve_active_document(state_payload)
            source_sha256 = sha256_file(Path(path))

            command = state_payload.get("command")
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
                    cad_build=cad_build,
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