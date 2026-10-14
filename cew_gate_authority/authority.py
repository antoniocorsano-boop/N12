from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_EXPECTED_INVARIANTS = tuple(f"I{i:02d}" for i in range(1, 18))
_EXPECTED_TEST_IDS = tuple(f"C01-T{i:02d}" for i in range(1, 12))
_BOUNDARY_KEYS = {"solver_authorized", "calculation_model_ready", "synthetic_solver_result", "solver_run", "result_entity_created"}
_EXPECTED_DOCUMENT_CONTRACT_PATHS = (
    "qualification/cew-contract-01/n12/qualification.json",
    "qualification/cew-contract-01/n12/evidence-index.json",
    "qualification/cew-contract-01/n12/registration-uncertainty.json",
    "qualification/cew-contract-01/n12/model-generation.json",
    "qualification/cew-contract-01/n12/model-generation-receipt.json",
    "qualification/cew-contract-01/n12/conformance-matrix.csv",
    "qualification/cew-contract-01/n12/structural-type-minimality.csv",
)
_EXPECTED_AUTHORITY_FIELDS = {
    "schema_id",
    "schema_version",
    "authority_id",
    "source_repository",
    "operational_commit",
    "canonical_snapshot_id",
    "model_generation_id",
    "model_generation_profile",
    "builder",
    "inputs",
    "registration",
    "output",
    "authority_boundary",
    "invariants",
    "candidate_allowlist",
    "evidence_bindings",
    "markdown_sha256",
    "document_contracts",
    "limits",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class BuilderAuthority:
    path: str
    git_blob_sha: str
    declared_builder: str


@dataclass(frozen=True)
class RegistrationAuthority:
    fixture_id: str
    uncertainty_type: str
    source_path: str
    source_git_blob_sha: str
    support_ids: tuple[str, ...]
    examples: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class OutputAuthority:
    identity: str
    generation_id_inside_artifact: str
    sha256: str
    size_bytes: int
    generated_at: str


@dataclass(frozen=True)
class CandidateLimits:
    max_blobs: int
    max_blob_bytes: int
    max_aggregate_bytes: int
    max_json_depth: int
    max_csv_rows: int


@dataclass(frozen=True)
class DocumentContract:
    path: str
    format: str
    schema_identity: tuple[tuple[str, Any], ...] = ()
    allowed_fields: tuple[str, ...] = ()
    csv_header: tuple[str, ...] = ()
    csv_rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class FrozenAuthority:
    authority_id: str
    source_sha256: str
    source_repository: str
    operational_commit: str
    canonical_snapshot_id: str
    model_generation_id: str
    model_generation_profile: str
    evidence_bindings: tuple[tuple[str, str], ...]
    markdown_sha256: tuple[tuple[str, str], ...]
    document_contracts: tuple[DocumentContract, ...]
    builder: BuilderAuthority
    inputs: tuple[tuple[str, str], ...]
    registration: RegistrationAuthority
    output: OutputAuthority
    authority_boundary: dict[str, bool]
    invariants: tuple[str, ...]
    candidate_allowlist: tuple[str, ...]
    limits: CandidateLimits


def _required(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise ValueError(f"authority missing required field: {key}")
    return data[key]


def _load_document_contracts(data: dict[str, Any], allowlist: tuple[str, ...]) -> tuple[DocumentContract, ...]:
    raw_contracts = dict(_required(data, "document_contracts"))
    if set(raw_contracts) != set(_EXPECTED_DOCUMENT_CONTRACT_PATHS):
        raise ValueError("authority document contracts must cover exactly the seven structured candidate documents")

    contracts: list[DocumentContract] = []
    for path in _EXPECTED_DOCUMENT_CONTRACT_PATHS:
        if path not in allowlist:
            raise ValueError("authority document contract outside candidate allowlist")
        raw = dict(raw_contracts[path])
        fmt = str(_required(raw, "format"))
        if fmt == "json":
            if set(raw) != {"format", "schema_identity", "allowed_fields"}:
                raise ValueError("json document contract has unexpected fields")
            schema_identity = tuple(dict(_required(raw, "schema_identity")).items())
            allowed_fields = tuple(str(v) for v in _required(raw, "allowed_fields"))
            if not schema_identity:
                raise ValueError("json document contract must freeze schema identity")
            if not allowed_fields or len(set(allowed_fields)) != len(allowed_fields):
                raise ValueError("json document contract allowed_fields must be unique and non-empty")
            if any(key not in allowed_fields for key, _ in schema_identity):
                raise ValueError("json document contract schema identity must be part of allowed_fields")
            contracts.append(DocumentContract(path=path, format=fmt, schema_identity=schema_identity, allowed_fields=allowed_fields))
        elif fmt == "csv":
            if not {"format", "header"} <= set(raw) <= {"format", "header", "rows"}:
                raise ValueError("csv document contract has unexpected fields")
            header = tuple(str(v) for v in _required(raw, "header"))
            if not header or len(set(header)) != len(header):
                raise ValueError("csv document contract header must be unique and non-empty")
            rows: list[tuple[str, ...]] = []
            for item in raw.get("rows", []):
                if not isinstance(item, dict) or set(item) != set(header):
                    raise ValueError("csv document contract rows must match the frozen header exactly")
                row = tuple(str(item[field]) for field in header)
                if any(not value for value in row):
                    raise ValueError("csv document contract row values must be non-empty")
                rows.append(row)
            if len(rows) != len(set(rows)):
                raise ValueError("csv document contract rows must be unique")
            contracts.append(DocumentContract(path=path, format=fmt, csv_header=header, csv_rows=tuple(rows)))
        else:
            raise ValueError("unsupported authority document contract format")
    return tuple(contracts)


def load_authority(path: Path) -> FrozenAuthority:
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if data.get("schema_id") != "CEW_FROZEN_QUALIFICATION_AUTHORITY" or data.get("schema_version") != 1:
        raise ValueError("unsupported authority schema")
    if set(data) != _EXPECTED_AUTHORITY_FIELDS:
        raise ValueError("authority schema contains unexpected or missing fields")

    inputs_raw = _required(data, "inputs")
    if not isinstance(inputs_raw, list) or len(inputs_raw) != 6:
        raise ValueError("authority inputs must contain exactly six entries")
    inputs = tuple((str(_required(item, "path")), str(_required(item, "sha256"))) for item in inputs_raw)
    if len({p for p, _ in inputs}) != 6:
        raise ValueError("authority input paths must be unique")

    boundary = dict(_required(data, "authority_boundary"))
    if set(boundary) != _BOUNDARY_KEYS or any(v is not False for v in boundary.values()):
        raise ValueError("authority boundary must contain exactly five explicit false flags")

    invariants = tuple(str(v) for v in _required(data, "invariants"))
    if invariants != _EXPECTED_INVARIANTS:
        raise ValueError("authority invariants must be exactly I01..I17 in order")

    allowlist = tuple(str(v) for v in _required(data, "candidate_allowlist"))
    if len(allowlist) != len(set(allowlist)):
        raise ValueError("candidate allowlist contains duplicates")

    evidence_map = dict(_required(data, "evidence_bindings"))
    if tuple(evidence_map) != _EXPECTED_TEST_IDS:
        raise ValueError("authority evidence bindings must be exactly C01-T01..C01-T11 in order")
    evidence_bindings = tuple((key, str(evidence_map[key])) for key in _EXPECTED_TEST_IDS)
    if len({bound_path for _, bound_path in evidence_bindings}) != len(evidence_bindings):
        raise ValueError("authority evidence bindings must be unique")
    if any(bound_path not in allowlist for _, bound_path in evidence_bindings):
        raise ValueError("authority evidence binding outside candidate allowlist")

    markdown_paths = tuple(path for path in allowlist if path.endswith(".md"))
    markdown_map = dict(_required(data, "markdown_sha256"))
    if set(markdown_map) != set(markdown_paths):
        raise ValueError("authority markdown digests must cover exactly every allowlisted Markdown artifact")
    markdown_sha256 = tuple((path, str(markdown_map[path])) for path in markdown_paths)
    if any(_SHA256.fullmatch(digest) is None for _, digest in markdown_sha256):
        raise ValueError("authority markdown digests must be lowercase SHA-256 values")

    document_contracts = _load_document_contracts(data, allowlist)
    builder = _required(data, "builder")
    registration = _required(data, "registration")
    output = _required(data, "output")
    limits = _required(data, "limits")
    examples = tuple(dict(item) for item in _required(registration, "examples"))
    if tuple(str(item.get("support_id")) for item in examples) != tuple(str(v) for v in _required(registration, "support_ids")):
        raise ValueError("registration examples do not match support_ids")

    source_repository = str(_required(data, "source_repository"))
    if not source_repository or "/" not in source_repository:
        raise ValueError("authority source_repository must be owner/name")

    model_generation_profile = str(_required(data, "model_generation_profile"))
    declared_builder = str(_required(builder, "declared_builder"))
    fixture_id = str(_required(registration, "fixture_id"))
    uncertainty_type = str(_required(registration, "uncertainty_type"))
    if not model_generation_profile or not declared_builder or not fixture_id or not uncertainty_type:
        raise ValueError("authority semantic identities must be non-empty")

    return FrozenAuthority(
        authority_id=str(_required(data, "authority_id")),
        source_sha256=hashlib.sha256(raw).hexdigest(),
        source_repository=source_repository,
        operational_commit=str(_required(data, "operational_commit")),
        canonical_snapshot_id=str(_required(data, "canonical_snapshot_id")),
        model_generation_id=str(_required(data, "model_generation_id")),
        model_generation_profile=model_generation_profile,
        evidence_bindings=evidence_bindings,
        markdown_sha256=markdown_sha256,
        document_contracts=document_contracts,
        builder=BuilderAuthority(
            str(_required(builder, "path")),
            str(_required(builder, "git_blob_sha")),
            declared_builder,
        ),
        inputs=inputs,
        registration=RegistrationAuthority(
            fixture_id,
            uncertainty_type,
            str(_required(registration, "source_path")),
            str(_required(registration, "source_git_blob_sha")),
            tuple(str(v) for v in _required(registration, "support_ids")),
            examples,
        ),
        output=OutputAuthority(
            str(_required(output, "identity")),
            str(_required(output, "generation_id_inside_artifact")),
            str(_required(output, "sha256")),
            int(_required(output, "size_bytes")),
            str(_required(output, "generated_at")),
        ),
        authority_boundary=boundary,
        invariants=invariants,
        candidate_allowlist=allowlist,
        limits=CandidateLimits(
            int(_required(limits, "max_blobs")),
            int(_required(limits, "max_blob_bytes")),
            int(_required(limits, "max_aggregate_bytes")),
            int(_required(limits, "max_json_depth")),
            int(_required(limits, "max_csv_rows")),
        ),
    )
