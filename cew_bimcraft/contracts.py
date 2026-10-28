from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


_HEX40 = 40
_HEX64 = 64


class BIMCraftContractError(ValueError):
    """Raised when the governed BIMCraft benchmark contract fails closed."""


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BIMCraftContractError(f"{name} must be a mapping")
    return value


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BIMCraftContractError(f"{name} must be a non-empty string")
    return value.strip()


def _hex(value: Any, name: str, length: int) -> str:
    text = _text(value, name).lower()
    if len(text) != length or any(char not in "0123456789abcdef" for char in text):
        raise BIMCraftContractError(f"{name} must be {length}-character lowercase hex")
    return text


def _false(value: Any, name: str) -> bool:
    if value is not False:
        raise BIMCraftContractError(f"{name} must remain false for benchmark authority")
    return False


@dataclass(frozen=True)
class BIMCraftToolchainContract:
    schema_id: str
    schema_version: int
    benchmark_id: str
    canonical_task: str
    adoption_state: str
    upstream_repository: str
    release: str
    tag_object_sha: str
    upstream_commit_sha: str
    published_at: str
    asset_platform: str
    asset_name: str
    asset_url: str
    asset_sha256: str
    cli_asset_platform: str
    cli_asset_name: str
    cli_asset_url: str
    cli_asset_sha256: str
    cli_binary: str
    ifc_validator_package: str
    ifc_validator_version: str
    ifc_validator_role: str
    observed_project_format: int
    project_file_canonical_authority: bool
    regenerable_projection_only: bool
    canonical_write_authorized: bool
    structural_identity_authorized: bool
    fem_authorized: bool
    master_change_authorized: bool
    n12_stage_b_authorized: bool


def load_toolchain_contract(path: str | Path) -> BIMCraftToolchainContract:
    source = Path(path)
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BIMCraftContractError("BIMCRAFT_TOOLCHAIN_CONTRACT_UNREADABLE") from exc

    root = _mapping(raw, "contract")
    upstream = _mapping(root.get("upstream"), "upstream")
    asset = _mapping(root.get("asset"), "asset")
    cli_asset = _mapping(root.get("cli_asset"), "cli_asset")
    ifc_validator = _mapping(root.get("ifc_validator"), "ifc_validator")
    project_policy = _mapping(root.get("project_file_policy"), "project_file_policy")
    authority = _mapping(root.get("authority"), "authority")

    schema_version = root.get("schema_version")
    observed_format = project_policy.get("observed_format")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != 1:
        raise BIMCraftContractError("schema_version must equal 1")
    if isinstance(observed_format, bool) or not isinstance(observed_format, int) or observed_format <= 0:
        raise BIMCraftContractError("observed_format must be a positive integer")
    if project_policy.get("regenerable_projection_only") is not True:
        raise BIMCraftContractError("regenerable_projection_only must remain true")

    contract = BIMCraftToolchainContract(
        schema_id=_text(root.get("schema_id"), "schema_id"),
        schema_version=schema_version,
        benchmark_id=_text(root.get("benchmark_id"), "benchmark_id"),
        canonical_task=_text(root.get("canonical_task"), "canonical_task"),
        adoption_state=_text(root.get("adoption_state"), "adoption_state"),
        upstream_repository=_text(upstream.get("repository"), "upstream.repository"),
        release=_text(upstream.get("release"), "upstream.release"),
        tag_object_sha=_hex(upstream.get("tag_object_sha"), "upstream.tag_object_sha", _HEX40),
        upstream_commit_sha=_hex(upstream.get("commit_sha"), "upstream.commit_sha", _HEX40),
        published_at=_text(upstream.get("published_at"), "upstream.published_at"),
        asset_platform=_text(asset.get("platform"), "asset.platform"),
        asset_name=_text(asset.get("name"), "asset.name"),
        asset_url=_text(asset.get("url"), "asset.url"),
        asset_sha256=_hex(asset.get("sha256"), "asset.sha256", _HEX64),
        cli_asset_platform=_text(cli_asset.get("platform"), "cli_asset.platform"),
        cli_asset_name=_text(cli_asset.get("name"), "cli_asset.name"),
        cli_asset_url=_text(cli_asset.get("url"), "cli_asset.url"),
        cli_asset_sha256=_hex(cli_asset.get("sha256"), "cli_asset.sha256", _HEX64),
        cli_binary=_text(cli_asset.get("binary"), "cli_asset.binary"),
        ifc_validator_package=_text(ifc_validator.get("package"), "ifc_validator.package"),
        ifc_validator_version=_text(ifc_validator.get("version"), "ifc_validator.version"),
        ifc_validator_role=_text(ifc_validator.get("role"), "ifc_validator.role"),
        observed_project_format=observed_format,
        project_file_canonical_authority=_false(
            project_policy.get("canonical_authority"),
            "project_file_policy.canonical_authority",
        ),
        regenerable_projection_only=True,
        canonical_write_authorized=_false(
            authority.get("canonical_write_authorized"),
            "authority.canonical_write_authorized",
        ),
        structural_identity_authorized=_false(
            authority.get("structural_identity_authorized"),
            "authority.structural_identity_authorized",
        ),
        fem_authorized=_false(authority.get("fem_authorized"), "authority.fem_authorized"),
        master_change_authorized=_false(
            authority.get("master_change_authorized"),
            "authority.master_change_authorized",
        ),
        n12_stage_b_authorized=_false(
            authority.get("n12_stage_b_authorized"),
            "authority.n12_stage_b_authorized",
        ),
    )

    if contract.schema_id != "CEW_BIMCRAFT_TOOLCHAIN":
        raise BIMCraftContractError("unexpected BIMCraft toolchain schema_id")
    if contract.benchmark_id != "CEW-BIMCRAFT-01":
        raise BIMCraftContractError("unexpected benchmark_id")
    if contract.canonical_task != "CEW-B01":
        raise BIMCraftContractError("canonical_task must remain CEW-B01")
    if contract.adoption_state != "BENCHMARK":
        raise BIMCraftContractError("adoption_state must remain BENCHMARK")
    if contract.ifc_validator_package != "ifcopenshell" or contract.ifc_validator_role != "READ_QUERY_VALIDATE_IFC":
        raise BIMCraftContractError("unexpected IFC validator contract")

    return contract


def verify_asset_identity(contract: BIMCraftToolchainContract, path: str | Path) -> str:
    candidate = Path(path)
    try:
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    except OSError as exc:
        raise BIMCraftContractError("BIMCRAFT_ASSET_UNREADABLE") from exc
    if digest != contract.asset_sha256:
        raise BIMCraftContractError("BIMCRAFT_ASSET_SHA256_MISMATCH")
    return digest
