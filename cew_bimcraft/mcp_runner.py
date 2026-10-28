from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Protocol, TextIO

from .command_plan import BIMCraftCommandPlan


MCP_PROTOCOL_VERSION = "2025-06-18"


class BIMCraftMCPError(RuntimeError):
    """Raised when the BIMCraft MCP boundary fails closed."""


class ToolClient(Protocol):
    def tool(self, name: str, arguments: dict | None = None) -> Any: ...


@dataclass(frozen=True)
class MCPExecutionResult:
    bindings: Mapping[str, int]
    command_results: tuple[Any, ...]


def parse_tool_response(response: Mapping[str, Any]) -> Any:
    if "error" in response:
        error = response.get("error")
        raise BIMCraftMCPError(f"BIMCRAFT_MCP_PROTOCOL_ERROR: {error}")
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise BIMCraftMCPError("BIMCRAFT_MCP_RESULT_MISSING")
    content = result.get("content")
    if result.get("isError") is True:
        message = "BIMCraft tool failed"
        if isinstance(content, list) and content and isinstance(content[0], Mapping):
            text = content[0].get("text")
            if isinstance(text, str) and text:
                message = text
        raise BIMCraftMCPError(f"BIMCRAFT_MCP_TOOL_ERROR: {message}")
    if not isinstance(content, list) or not content:
        raise BIMCraftMCPError("BIMCRAFT_MCP_CONTENT_MISSING")
    first = content[0]
    if not isinstance(first, Mapping):
        raise BIMCraftMCPError("BIMCRAFT_MCP_CONTENT_INVALID")
    if first.get("type") != "text":
        return dict(first)
    text = first.get("text")
    if not isinstance(text, str):
        raise BIMCraftMCPError("BIMCRAFT_MCP_TEXT_MISSING")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def extract_bound_id(result: Any) -> int:
    if not isinstance(result, Mapping):
        raise BIMCraftMCPError("BIMCRAFT_BIND_ID_MISSING")
    direct = result.get("id")
    if isinstance(direct, int) and not isinstance(direct, bool):
        return direct
    ids = result.get("ids")
    if isinstance(ids, list):
        numeric = [value for value in ids if isinstance(value, int) and not isinstance(value, bool)]
        if len(ids) == 1 and len(numeric) == 1:
            return numeric[0]
        if len(ids) > 1:
            raise BIMCraftMCPError("BIMCRAFT_BIND_ID_AMBIGUOUS")
    raise BIMCraftMCPError("BIMCRAFT_BIND_ID_MISSING")


def execute_command_plan(client: ToolClient, plan: BIMCraftCommandPlan) -> MCPExecutionResult:
    if plan.authority != "BENCHMARK_ONLY":
        raise BIMCraftMCPError("BIMCRAFT_PLAN_AUTHORITY_FORBIDDEN")

    client.tool("new_model", {"name": plan.project})
    bindings: dict[str, int] = {}
    command_results: list[Any] = []

    for item in plan.commands:
        params = json.loads(json.dumps(dict(item.params)))
        if item.ref is not None:
            if item.ref not in bindings:
                raise BIMCraftMCPError(f"BIMCRAFT_SYMBOLIC_REF_UNRESOLVED: {item.ref}")
            if "id" in params or "ids" in params:
                raise BIMCraftMCPError("BIMCRAFT_SYMBOLIC_REF_ID_COLLISION")
            params = {"id": bindings[item.ref], **params}

        result = client.tool("execute", {"command": item.command, "params": params})
        command_results.append(result)
        if item.bind is not None:
            if item.bind in bindings:
                raise BIMCraftMCPError(f"BIMCRAFT_SYMBOLIC_BIND_DUPLICATE: {item.bind}")
            bindings[item.bind] = extract_bound_id(result)

    return MCPExecutionResult(bindings=dict(bindings), command_results=tuple(command_results))


class StdioMCPClient:
    """Minimal MCP JSON-RPC client for BIMCraft's line-oriented stdio transport."""

    def __init__(self, executable: str | Path) -> None:
        self.executable = str(executable)
        self._process: subprocess.Popen[str] | None = None
        self._stdin: TextIO | None = None
        self._stdout: TextIO | None = None
        self._next_id = 1

    def __enter__(self) -> "StdioMCPClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start(self) -> None:
        if self._process is not None:
            raise BIMCraftMCPError("BIMCRAFT_MCP_ALREADY_STARTED")
        self._process = subprocess.Popen(
            [self.executable, "mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            bufsize=1,
        )
        if self._process.stdin is None or self._process.stdout is None:
            self.close()
            raise BIMCraftMCPError("BIMCRAFT_MCP_STDIO_UNAVAILABLE")
        self._stdin = self._process.stdin
        self._stdout = self._process.stdout
        initialized = self.request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "cew-bimcraft-01", "version": "1"},
            },
        )
        server = initialized.get("serverInfo") if isinstance(initialized, Mapping) else None
        if not isinstance(server, Mapping) or server.get("name") != "bimcraft":
            self.close()
            raise BIMCraftMCPError("BIMCRAFT_MCP_SERVER_IDENTITY_MISMATCH")
        if server.get("version") != "0.9.0":
            self.close()
            raise BIMCraftMCPError("BIMCRAFT_MCP_SERVER_VERSION_MISMATCH")
        self.notify("notifications/initialized", {})

    def close(self) -> None:
        process = self._process
        self._process = None
        self._stdin = None
        self._stdout = None
        if process is None:
            return
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    def _send(self, payload: Mapping[str, Any]) -> None:
        if self._stdin is None:
            raise BIMCraftMCPError("BIMCRAFT_MCP_NOT_STARTED")
        try:
            self._stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
            self._stdin.flush()
        except OSError as exc:
            raise BIMCraftMCPError("BIMCRAFT_MCP_WRITE_FAILED") from exc

    def request(self, method: str, params: Mapping[str, Any] | None = None) -> Any:
        if self._stdout is None:
            raise BIMCraftMCPError("BIMCRAFT_MCP_NOT_STARTED")
        request_id = self._next_id
        self._next_id += 1
        self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": dict(params or {}),
            }
        )
        line = self._stdout.readline()
        if not line:
            code = self._process.poll() if self._process is not None else None
            raise BIMCraftMCPError(f"BIMCRAFT_MCP_EOF: returncode={code}")
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BIMCraftMCPError("BIMCRAFT_MCP_RESPONSE_NOT_JSON") from exc
        if not isinstance(response, Mapping) or response.get("id") != request_id:
            raise BIMCraftMCPError("BIMCRAFT_MCP_RESPONSE_ID_MISMATCH")
        if "error" in response:
            raise BIMCraftMCPError(f"BIMCRAFT_MCP_PROTOCOL_ERROR: {response['error']}")
        if "result" not in response:
            raise BIMCraftMCPError("BIMCRAFT_MCP_RESULT_MISSING")
        return response["result"]

    def notify(self, method: str, params: Mapping[str, Any] | None = None) -> None:
        self._send(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": dict(params or {}),
            }
        )

    def tool(self, name: str, arguments: dict | None = None) -> Any:
        if self._stdout is None:
            raise BIMCraftMCPError("BIMCRAFT_MCP_NOT_STARTED")
        request_id = self._next_id
        self._next_id += 1
        self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": dict(arguments or {})},
            }
        )
        line = self._stdout.readline()
        if not line:
            code = self._process.poll() if self._process is not None else None
            raise BIMCraftMCPError(f"BIMCRAFT_MCP_EOF: returncode={code}")
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BIMCraftMCPError("BIMCRAFT_MCP_RESPONSE_NOT_JSON") from exc
        if not isinstance(response, Mapping) or response.get("id") != request_id:
            raise BIMCraftMCPError("BIMCRAFT_MCP_RESPONSE_ID_MISMATCH")
        return parse_tool_response(response)
