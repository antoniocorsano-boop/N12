from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping


class ToolchainContractError(ValueError):
    """Raised when the governed CEW-B01 toolchain contract is invalid."""


EXPECTED_TOOL_IDS = {
    "docling",
    "docling-parse",
    "pypdfium2",
    "pdfplumber",
    "ocrmypdf",
    "tesseract",
    "opencv",
    "ezdxf",
    "build123d",
    "ocp",
    "cadcraft",
}

ALLOWED_SLICE_STATUSES = {
    "ADOPT",
    "ADOPT_BENCHMARK_N12",
    "ADOPT_CONDITIONAL",
    "FOUNDATION",
    "DEFER_FOR_THIS_SLICE_NO_IMMUTABLE_DXF_SOURCE",
    "BENCHMARK_N12_NON_CORE",
}

_PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([^=\s]+)$")


def _normalise_package(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_pin(value: str) -> tuple[str, str]:
    match = _PIN.fullmatch(value)
    if not match:
        raise ToolchainContractError(f"required Python package is not exact-pinned: {value!r}")
    return _normalise_package(match.group(1)), match.group(2)


@dataclass(frozen=True)
class ToolchainContract:
    schema_id: str
    schema_version: int
    qualification_environment: Mapping[str, Any]
    required_python_packages: tuple[str, ...]
    tools: tuple[Mapping[str, Any], ...]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ToolchainContract":
        if not isinstance(raw, Mapping):
            raise ToolchainContractError("toolchain contract must be a JSON object")
        if raw.get("schema_id") != "CEW_B01_EXTERNAL_TOOLCHAIN":
            raise ToolchainContractError("unexpected toolchain schema_id")
        if raw.get("schema_version") != 1:
            raise ToolchainContractError("unexpected toolchain schema_version")

        environment = raw.get("qualification_environment")
        if not isinstance(environment, Mapping):
            raise ToolchainContractError("qualification_environment must be an object")
        if environment.get("python") != "3.12.15" or environment.get("runner") != "ubuntu-24.04":
            raise ToolchainContractError("qualification environment must remain frozen")

        required = raw.get("required_python_packages")
        if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
            raise ToolchainContractError("required_python_packages must be a string list")

        pins: dict[str, str] = {}
        for item in required:
            name, version = _parse_pin(item)
            if name == "pymupdf":
                raise ToolchainContractError("PyMuPDF is prohibited from the CEW-B01 required toolchain")
            if name in pins:
                raise ToolchainContractError(f"duplicate Python package pin: {name}")
            pins[name] = version

        tools = raw.get("tools")
        if not isinstance(tools, list) or not all(isinstance(item, Mapping) for item in tools):
            raise ToolchainContractError("tools must be an object list")

        ids = [item.get("tool_id") for item in tools]
        if len(ids) != len(set(ids)):
            raise ToolchainContractError("tool_id values must be unique")
        if set(ids) != EXPECTED_TOOL_IDS:
            raise ToolchainContractError(
                f"tool set mismatch; missing={sorted(EXPECTED_TOOL_IDS - set(ids))}, "
                f"extra={sorted(set(ids) - EXPECTED_TOOL_IDS)}"
            )

        by_id: dict[str, Mapping[str, Any]] = {}
        directly_required_python: dict[str, str] = {}
        for item in tools:
            tool_id = item.get("tool_id")
            assert isinstance(tool_id, str)
            by_id[tool_id] = item

            status = item.get("slice_status")
            if status not in ALLOWED_SLICE_STATUSES:
                raise ToolchainContractError(f"unknown slice_status for {tool_id}: {status!r}")
            if not isinstance(item.get("blocking"), bool):
                raise ToolchainContractError(f"blocking must be boolean for {tool_id}")
            if not isinstance(item.get("install_for_slice"), bool):
                raise ToolchainContractError(f"install_for_slice must be boolean for {tool_id}")
            for field in ("execution_mode", "license", "source"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise ToolchainContractError(f"{field} must be non-empty for {tool_id}")

            package = item.get("python_package")
            if package is not None and (not isinstance(package, str) or not package.strip()):
                raise ToolchainContractError(f"python_package must be null or non-empty for {tool_id}")

            if item["install_for_slice"] and package:
                version = item.get("version")
                if not isinstance(version, str) or not version.strip():
                    raise ToolchainContractError(f"installed Python tool requires exact version: {tool_id}")
                normalised = _normalise_package(package)
                directly_required_python[normalised] = version
                if pins.get(normalised) != version:
                    raise ToolchainContractError(
                        f"manifest/lock version mismatch for {tool_id}: "
                        f"manifest={version!r}, lock={pins.get(normalised)!r}"
                    )

        if pins != directly_required_python:
            raise ToolchainContractError(
                f"required Python package set mismatch; manifest={directly_required_python}, lock={pins}"
            )

        for tool_id in ("ocrmypdf", "tesseract"):
            item = by_id[tool_id]
            if item.get("slice_status") != "ADOPT_CONDITIONAL":
                raise ToolchainContractError(f"{tool_id} must remain ADOPT_CONDITIONAL")
            if item.get("execution_mode") != "CONDITIONAL_TRIGGER_ONLY":
                raise ToolchainContractError(f"{tool_id} must remain trigger-only")

        ezdxf = by_id["ezdxf"]
        if (
            ezdxf.get("slice_status") != "DEFER_FOR_THIS_SLICE_NO_IMMUTABLE_DXF_SOURCE"
            or ezdxf.get("blocking") is not False
            or ezdxf.get("install_for_slice") is not False
        ):
            raise ToolchainContractError("ezdxf direct qualification must remain deferred for B01")

        cadcraft = by_id["cadcraft"]
        if (
            cadcraft.get("slice_status") != "BENCHMARK_N12_NON_CORE"
            or cadcraft.get("blocking") is not False
            or cadcraft.get("install_for_slice") is not False
        ):
            raise ToolchainContractError("CADCraft must remain a separate non-blocking benchmark")

        return cls(
            schema_id="CEW_B01_EXTERNAL_TOOLCHAIN",
            schema_version=1,
            qualification_environment=dict(environment),
            required_python_packages=tuple(required),
            tools=tuple(dict(item) for item in tools),
        )


def load_toolchain_contract(path: Path | str) -> ToolchainContract:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolchainContractError(f"cannot load toolchain contract: {source}") from exc
    return ToolchainContract.from_mapping(raw)


def validate_lock_text(contract: ToolchainContract, lock_text: str) -> None:
    pins = [
        line.strip()
        for line in lock_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if tuple(pins) != contract.required_python_packages:
        raise ToolchainContractError("lock file does not exactly match required_python_packages order/content")
    for pin in pins:
        name, _ = _parse_pin(pin)
        if name == "pymupdf":
            raise ToolchainContractError("PyMuPDF is prohibited from the CEW-B01 lock")
