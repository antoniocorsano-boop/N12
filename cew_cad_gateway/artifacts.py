from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, sha256_json
from .changesets import verify_changeset_digest
from .receipts import ReceiptStore, ReceiptStoreError
from .types import (
    ApprovalReceipt,
    CapabilityIdentity,
    ChangeReceipt,
    Changeset,
    CreatePolyline,
    DocumentIdentity,
    EpistemicState,
    TechnicalVerificationReceipt,
)
from .workspace import Workspace

_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ArtifactError(ValueError):
    pass


def _strict_json(path: Path) -> dict[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ArtifactError("DUPLICATE_JSON_KEY")
            out[key] = value
        return out

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
    except ArtifactError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactError("INVALID_ARTIFACT_JSON") from exc
    if not isinstance(value, dict):
        raise ArtifactError("ARTIFACT_ROOT_MUST_BE_OBJECT")
    return value


def _require_safe_id(value: str, field: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise ArtifactError(f"INVALID_{field.upper()}")
    return value


def _require_digest(value: str, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ArtifactError(f"INVALID_{field.upper()}")
    return value


def _exact_keys(raw: dict[str, Any], expected: set[str], label: str) -> None:
    if set(raw) != expected:
        raise ArtifactError(f"INVALID_{label}_FIELDS")


def _tuple_text(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ArtifactError(f"INVALID_{field.upper()}")
    return tuple(value)


class ArtifactRepository:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.changeset_root = workspace.zone_path("CHANGESETS")
        self.audit_root = workspace.zone_path("AUDITS")
        self.receipt_store = ReceiptStore(self.audit_root)

    def _write_new(self, path: Path, value: object) -> Path:
        try:
            with path.open("xb") as handle:
                handle.write(canonical_json_bytes(value))
                handle.write(b"\n")
        except FileExistsError as exc:
            raise ArtifactError("ARTIFACT_ALREADY_EXISTS") from exc
        except OSError as exc:
            raise ArtifactError("ARTIFACT_WRITE_FAILED") from exc
        return path

    def changeset_path(self, changeset_id: str) -> Path:
        return self.changeset_root / f"changeset-{_require_safe_id(changeset_id, 'changeset_id')}.json"

    def approval_path(self, approval_id: str) -> Path:
        return self.changeset_root / f"approval-{_require_safe_id(approval_id, 'approval_id')}.json"

    def store_changeset(self, changeset: Changeset) -> Path:
        if not verify_changeset_digest(changeset):
            raise ArtifactError("CHANGESET_DIGEST_MISMATCH")
        return self._write_new(self.changeset_path(changeset.changeset_id), changeset)

    def load_changeset(self, changeset_id: str) -> Changeset:
        path = self.changeset_path(changeset_id)
        raw = _strict_json(path)
        _exact_keys(
            raw,
            {
                "schema", "changeset_id", "intent", "session_id", "document", "capabilities",
                "evidence_refs", "claim_refs", "decision_refs", "epistemic_states", "operations",
                "preconditions", "postconditions", "expected_changed_entities",
                "forbidden_side_effects", "unresolved", "changeset_sha256",
            },
            "CHANGESET",
        )
        document = raw["document"]
        capabilities = raw["capabilities"]
        operations = raw["operations"]
        if not isinstance(document, dict) or set(document) != {"path", "sha256", "document_id", "revision"}:
            raise ArtifactError("INVALID_CHANGESET_DOCUMENT")
        if not isinstance(capabilities, dict) or set(capabilities) != {"cad_build", "capabilities_sha256"}:
            raise ArtifactError("INVALID_CHANGESET_CAPABILITIES")
        if not isinstance(operations, list) or len(operations) != 1 or not isinstance(operations[0], dict):
            raise ArtifactError("INVALID_CHANGESET_OPERATIONS")
        op = operations[0]
        if set(op) != {"layer", "points", "closed"}:
            raise ArtifactError("INVALID_CHANGESET_OPERATION")
        points_raw = op["points"]
        if not isinstance(points_raw, list) or any(
            not isinstance(point, list)
            or len(point) != 2
            or any(not isinstance(value, (int, float)) or isinstance(value, bool) for value in point)
            for point in points_raw
        ):
            raise ArtifactError("INVALID_CHANGESET_POINTS")
        try:
            changeset = Changeset(
                schema=raw["schema"],
                changeset_id=raw["changeset_id"],
                intent=raw["intent"],
                session_id=raw["session_id"],
                document=DocumentIdentity(
                    path=document["path"],
                    sha256=document["sha256"],
                    document_id=document["document_id"],
                    revision=document["revision"],
                ),
                capabilities=CapabilityIdentity(
                    cad_build=capabilities["cad_build"],
                    capabilities_sha256=capabilities["capabilities_sha256"],
                ),
                evidence_refs=_tuple_text(raw["evidence_refs"], "evidence_refs"),
                claim_refs=_tuple_text(raw["claim_refs"], "claim_refs"),
                decision_refs=_tuple_text(raw["decision_refs"], "decision_refs"),
                epistemic_states=tuple(EpistemicState(item) for item in _tuple_text(raw["epistemic_states"], "epistemic_states")),
                operations=(CreatePolyline(
                    layer=op["layer"],
                    points=tuple((float(point[0]), float(point[1])) for point in points_raw),
                    closed=op["closed"],
                ),),
                preconditions=_tuple_text(raw["preconditions"], "preconditions"),
                postconditions=_tuple_text(raw["postconditions"], "postconditions"),
                expected_changed_entities=_tuple_text(raw["expected_changed_entities"], "expected_changed_entities"),
                forbidden_side_effects=_tuple_text(raw["forbidden_side_effects"], "forbidden_side_effects"),
                unresolved=_tuple_text(raw["unresolved"], "unresolved"),
                changeset_sha256=raw["changeset_sha256"],
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise ArtifactError("INVALID_CHANGESET") from exc
        if changeset.changeset_id != changeset_id:
            raise ArtifactError("CHANGESET_ID_MISMATCH")
        if not verify_changeset_digest(changeset):
            raise ArtifactError("CHANGESET_DIGEST_MISMATCH")
        return changeset

    def store_approval(self, approval: ApprovalReceipt) -> Path:
        return self._write_new(self.approval_path(approval.approval_id), approval)

    def load_approval(self, approval_id: str) -> ApprovalReceipt:
        raw = _strict_json(self.approval_path(approval_id))
        expected = {
            "schema", "approval_id", "changeset_id", "changeset_sha256", "document_sha256",
            "document_id", "base_revision", "decision", "approved_by", "approved_at", "signature",
        }
        _exact_keys(raw, expected, "APPROVAL")
        try:
            receipt = ApprovalReceipt(**raw)
        except (TypeError, ValueError) as exc:
            raise ArtifactError("INVALID_APPROVAL") from exc
        if receipt.approval_id != approval_id:
            raise ArtifactError("APPROVAL_ID_MISMATCH")
        return receipt

    def store_change(self, receipt: ChangeReceipt) -> str:
        try:
            return self.receipt_store.write("change", receipt).sha256
        except ReceiptStoreError as exc:
            raise ArtifactError("CHANGE_RECEIPT_STORE_FAILED") from exc

    def load_change(self, change_id: str) -> ChangeReceipt:
        digest = _require_digest(change_id, "change_id")
        raw = _strict_json(self.audit_root / f"change-{digest}.json")
        expected = {
            "schema", "changeset_sha256", "approval_sha256", "request_id", "revision_before",
            "revision_after", "changed_entities", "status",
        }
        _exact_keys(raw, expected, "CHANGE_RECEIPT")
        raw["changed_entities"] = _tuple_text(raw["changed_entities"], "changed_entities")
        try:
            receipt = ChangeReceipt(**raw)
        except (TypeError, ValueError) as exc:
            raise ArtifactError("INVALID_CHANGE_RECEIPT") from exc
        if sha256_json(receipt) != digest:
            raise ArtifactError("CHANGE_RECEIPT_DIGEST_MISMATCH")
        return receipt

    def load_verification(self, verification_id: str) -> TechnicalVerificationReceipt:
        digest = _require_digest(verification_id, "verification_id")
        raw = _strict_json(self.audit_root / f"verification-{digest}.json")
        expected = {
            "schema", "changeset_sha256", "change_receipt_sha256", "session_id", "document_id",
            "verified_revision", "source_sha256", "capabilities_sha256", "postconditions",
            "unrelated_change", "audit_sha256", "decision",
        }
        _exact_keys(raw, expected, "VERIFICATION_RECEIPT")
        if not isinstance(raw["postconditions"], dict) or any(
            not isinstance(key, str) or type(value) is not bool for key, value in raw["postconditions"].items()
        ):
            raise ArtifactError("INVALID_VERIFICATION_POSTCONDITIONS")
        try:
            receipt = TechnicalVerificationReceipt(**raw)
        except (TypeError, ValueError) as exc:
            raise ArtifactError("INVALID_VERIFICATION_RECEIPT") from exc
        if sha256_json(receipt) != digest:
            raise ArtifactError("VERIFICATION_RECEIPT_DIGEST_MISMATCH")
        return receipt
