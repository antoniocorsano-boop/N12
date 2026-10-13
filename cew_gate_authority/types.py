from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_INVARIANTS = tuple(f"I{i:02d}" for i in range(1, 18))
_AUTHORITY_BOUNDARY_KEYS = {
    "solver_authorized",
    "calculation_model_ready",
    "synthetic_solver_result",
    "solver_run",
    "result_entity_created",
}


def _require_sha40(value: str, field: str) -> None:
    if not isinstance(value, str) or not _SHA40.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase 40-hex commit SHA")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase 64-hex SHA-256")


@dataclass(frozen=True)
class CandidateIdentity:
    base_repository: str
    pr_number: int
    head_repository: str
    head_sha: str

    def __post_init__(self) -> None:
        if not self.base_repository or "/" not in self.base_repository:
            raise ValueError("base_repository must be owner/name")
        if not isinstance(self.pr_number, int) or self.pr_number < 1:
            raise ValueError("pr_number must be positive")
        if not self.head_repository or "/" not in self.head_repository:
            raise ValueError("head_repository must be owner/name")
        _require_sha40(self.head_sha, "head_sha")


@dataclass(frozen=True)
class ControlPlaneIdentity:
    base_commit_sha: str

    def __post_init__(self) -> None:
        _require_sha40(self.base_commit_sha, "base_commit_sha")


@dataclass(frozen=True)
class GateCoreIdentity:
    repository: str
    commit_sha: str
    version: str

    def __post_init__(self) -> None:
        if not self.repository or "/" not in self.repository:
            raise ValueError("gate core repository must be owner/name")
        _require_sha40(self.commit_sha, "gate_core.commit_sha")
        if not self.version:
            raise ValueError("gate core version is required")


@dataclass(frozen=True)
class AuthorityIdentity:
    authority_id: str
    authority_sha256: str

    def __post_init__(self) -> None:
        if not self.authority_id:
            raise ValueError("authority_id is required")
        _require_sha256(self.authority_sha256, "authority_sha256")


@dataclass(frozen=True)
class OperationalIdentity:
    commit_sha: str

    def __post_init__(self) -> None:
        _require_sha40(self.commit_sha, "operational_authority.commit_sha")


class InvariantResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class QualificationReceipt:
    schema_id: str
    schema_version: int
    qualified_at: str
    control_plane: ControlPlaneIdentity
    gate_core: GateCoreIdentity
    authority: AuthorityIdentity
    candidate: CandidateIdentity
    operational_authority: OperationalIdentity
    qualification_bundle_sha256: str
    replay: Mapping[str, Any]
    invariants: Mapping[str, InvariantResult]
    failure_codes: tuple[str, ...]
    authority_boundary: Mapping[str, bool]
    cew_fem_01_required: bool
    qualified: bool

    def __post_init__(self) -> None:
        if self.schema_id != "CEW_QUALIFICATION_RECEIPT":
            raise ValueError("unsupported receipt schema_id")
        if self.schema_version != 1:
            raise ValueError("unsupported receipt schema_version")
        if not self.qualified_at:
            raise ValueError("qualified_at is required")
        _require_sha256(self.qualification_bundle_sha256, "qualification_bundle_sha256")
        keys = tuple(sorted(self.invariants))
        if keys != _EXPECTED_INVARIANTS:
            raise ValueError("invariants must be exactly I01..I17")
        values = tuple(self.invariants[key] for key in _EXPECTED_INVARIANTS)
        if any(not isinstance(value, InvariantResult) for value in values):
            raise ValueError("invariant values must be InvariantResult")
        boundary_keys = set(self.authority_boundary)
        if boundary_keys != _AUTHORITY_BOUNDARY_KEYS:
            raise ValueError("authority_boundary keys are invalid")
        if any(type(value) is not bool for value in self.authority_boundary.values()):
            raise ValueError("authority_boundary values must be booleans")
        if self.qualified:
            if any(value is InvariantResult.FAIL for value in values):
                raise ValueError("qualified receipt cannot contain FAIL invariant")
            if any(self.authority_boundary.values()):
                raise ValueError("qualified receipt cannot cross authority boundary")
            if self.cew_fem_01_required is not True:
                raise ValueError("qualified receipt must preserve CEW-FEM-01 separation")
            if self.failure_codes:
                raise ValueError("qualified receipt cannot contain failure codes")
