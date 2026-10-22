from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase 64-hex SHA-256")


def _require_positive_int(value: int, field: str, *, allow_zero: bool = False) -> None:
    minimum = 0 if allow_zero else 1
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        comparator = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field} must be a {comparator} integer")


class EpistemicState(str, Enum):
    DOC = "DOC"
    MIS = "MIS"
    RIF = "RIF"
    INF = "INF"
    INC = "INC"
    ND = "ND"


class PathClass(str, Enum):
    SOURCE = "SOURCE"
    BASELINE = "BASELINE"
    WORKING = "WORKING"
    VERIFIED = "VERIFIED"
    ISSUED = "ISSUED"


@dataclass(frozen=True)
class DocumentIdentity:
    path: str
    sha256: str
    document_id: int
    revision: int

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("path is required")
        _require_sha256(self.sha256, "sha256")
        _require_positive_int(self.document_id, "document_id")
        _require_positive_int(self.revision, "revision", allow_zero=True)


@dataclass(frozen=True)
class CapabilityIdentity:
    cad_build: str
    capabilities_sha256: str

    def __post_init__(self) -> None:
        if not self.cad_build:
            raise ValueError("cad_build is required")
        _require_sha256(self.capabilities_sha256, "capabilities_sha256")


@dataclass(frozen=True)
class CADStatus:
    session_id: str
    document: DocumentIdentity
    capabilities: CapabilityIdentity
    path_class: PathClass | None = None

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id is required")


@dataclass(frozen=True)
class CreatePolyline:
    layer: str
    points: tuple[tuple[float, float], ...]
    closed: bool = True

    def __post_init__(self) -> None:
        if not self.layer:
            raise ValueError("layer is required")
        if len(self.points) < 2:
            raise ValueError("polyline requires at least two points")


@dataclass(frozen=True)
class SetProperties:
    handle: str
    updates: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.handle:
            raise ValueError("handle is required")
        if not self.updates:
            raise ValueError("updates are required")


CADOperation = CreatePolyline | SetProperties


@dataclass(frozen=True)
class Changeset:
    schema: str
    changeset_id: str
    intent: str
    session_id: str
    document: DocumentIdentity
    capabilities: CapabilityIdentity
    evidence_refs: tuple[str, ...]
    claim_refs: tuple[str, ...]
    decision_refs: tuple[str, ...]
    epistemic_states: tuple[EpistemicState, ...]
    operations: tuple[CADOperation, ...]
    preconditions: tuple[str, ...]
    postconditions: tuple[str, ...]
    expected_changed_entities: tuple[str, ...]
    forbidden_side_effects: tuple[str, ...]
    unresolved: tuple[str, ...]
    changeset_sha256: str

    def __post_init__(self) -> None:
        if self.schema != "cew.cad.changeset.v1":
            raise ValueError("unsupported changeset schema")
        if not self.changeset_id or not self.intent or not self.session_id:
            raise ValueError("changeset id, intent and session_id are required")
        _require_sha256(self.changeset_sha256, "changeset_sha256")


@dataclass(frozen=True)
class ApprovalReceipt:
    schema: str
    approval_id: str
    changeset_id: str
    changeset_sha256: str
    document_sha256: str
    document_id: int
    base_revision: int
    decision: str
    approved_by: str
    approved_at: str
    signature: str

    def __post_init__(self) -> None:
        if self.schema != "cew.cad.approval.v1":
            raise ValueError("unsupported approval schema")
        if not self.approval_id or not self.changeset_id:
            raise ValueError("approval_id and changeset_id are required")
        _require_sha256(self.changeset_sha256, "changeset_sha256")
        _require_sha256(self.document_sha256, "document_sha256")
        _require_positive_int(self.document_id, "document_id")
        _require_positive_int(self.base_revision, "base_revision", allow_zero=True)
        if self.decision != "APPROVED":
            raise ValueError("approval decision must be APPROVED")
        if not self.approved_by or not self.approved_at or not self.signature:
            raise ValueError("approval identity, timestamp and signature are required")


@dataclass(frozen=True)
class InspectionReceipt:
    schema: str
    status: CADStatus
    audit_sha256: str
    observed_at: str

    def __post_init__(self) -> None:
        if self.schema != "cew.cad.inspection.v1":
            raise ValueError("unsupported inspection schema")
        _require_sha256(self.audit_sha256, "audit_sha256")
        if not self.observed_at:
            raise ValueError("observed_at is required")


@dataclass(frozen=True)
class ChangeReceipt:
    schema: str
    changeset_sha256: str
    approval_sha256: str
    request_id: str
    revision_before: int
    revision_after: int
    changed_entities: tuple[str, ...]
    status: str

    def __post_init__(self) -> None:
        if self.schema != "cew.cad.change.v1":
            raise ValueError("unsupported change schema")
        _require_sha256(self.changeset_sha256, "changeset_sha256")
        _require_sha256(self.approval_sha256, "approval_sha256")
        if not self.request_id:
            raise ValueError("request_id is required")
        _require_positive_int(self.revision_before, "revision_before", allow_zero=True)
        _require_positive_int(self.revision_after, "revision_after", allow_zero=True)


@dataclass(frozen=True)
class TechnicalVerificationReceipt:
    schema: str
    changeset_sha256: str
    change_receipt_sha256: str
    session_id: str
    document_id: int
    verified_revision: int
    source_sha256: str
    capabilities_sha256: str
    postconditions: Mapping[str, bool]
    unrelated_change: bool
    audit_sha256: str
    decision: str

    def __post_init__(self) -> None:
        if self.schema != "cew.cad.verification.v1":
            raise ValueError("unsupported verification schema")
        _require_sha256(self.changeset_sha256, "changeset_sha256")
        _require_sha256(self.change_receipt_sha256, "change_receipt_sha256")
        _require_sha256(self.source_sha256, "source_sha256")
        _require_sha256(self.capabilities_sha256, "capabilities_sha256")
        _require_sha256(self.audit_sha256, "audit_sha256")
        if not self.session_id:
            raise ValueError("verification session_id is required")
        _require_positive_int(self.document_id, "document_id")
        _require_positive_int(self.verified_revision, "verified_revision", allow_zero=True)
        if self.decision not in {"PASS", "FAIL"}:
            raise ValueError("verification decision must be PASS or FAIL")


@dataclass(frozen=True)
class VerifiedCopyReceipt:
    schema: str
    verification_receipt_sha256: str
    output_path: str
    target_format: str
    target_version: str
    output_sha256: str
    semantic_verification_passed: bool
    status: str

    def __post_init__(self) -> None:
        if self.schema != "cew.cad.verified-copy.v1":
            raise ValueError("unsupported verified-copy schema")
        _require_sha256(self.verification_receipt_sha256, "verification_receipt_sha256")
        _require_sha256(self.output_sha256, "output_sha256")
        if not self.output_path or not self.target_format or not self.target_version:
            raise ValueError("verified-copy target identity is required")
        if self.status != "CANDIDATE_FOR_HUMAN_REVIEW":
            raise ValueError("verified copy must remain candidate for human review")
