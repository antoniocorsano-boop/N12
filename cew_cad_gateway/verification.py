from __future__ import annotations

import math
from pathlib import Path

from .adapters.base import CADAdapter
from .canonical import sha256_file, sha256_json
from .receipts import ReceiptStore
from .types import (
    ChangeReceipt,
    Changeset,
    CreatePolyline,
    PathClass,
    TechnicalVerificationReceipt,
    VerifiedCopyReceipt,
)
from .workspace import Workspace, WorkspaceError


class VerificationError(ValueError):
    pass


def _polyline_expected_geometry(operation: CreatePolyline) -> tuple[float, float | None]:
    points = operation.points
    length = 0.0
    for left, right in zip(points, points[1:]):
        length += math.dist(left, right)
    if operation.closed:
        length += math.dist(points[-1], points[0])
        area = 0.0
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
            area += x1 * y2 - x2 * y1
        return length, abs(area) / 2.0
    return length, None


def _close(left: object, right: float, *, tolerance: float = 1e-8) -> bool:
    if not isinstance(left, (int, float)) or isinstance(left, bool) or not math.isfinite(float(left)):
        return False
    return math.isclose(float(left), right, rel_tol=tolerance, abs_tol=tolerance)


class VerificationService:
    def __init__(
        self,
        *,
        adapter: CADAdapter,
        workspace: Workspace,
        receipt_store: ReceiptStore,
        target_format: str,
        target_version: str,
    ) -> None:
        if target_format not in {"dwg", "dxf"}:
            raise VerificationError("UNSUPPORTED_TARGET_FORMAT")
        if not target_version:
            raise VerificationError("TARGET_VERSION_REQUIRED")
        self.adapter = adapter
        self.workspace = workspace
        self.receipt_store = receipt_store
        self.target_format = target_format
        self.target_version = target_version

    def _source_integrity(self, changeset: Changeset, current) -> bool:
        if current.session_id != changeset.session_id:
            return False
        if current.document.path != changeset.document.path:
            return False
        if current.document.document_id != changeset.document.document_id:
            return False
        if current.document.sha256 != changeset.document.sha256:
            return False
        if current.capabilities != changeset.capabilities:
            return False
        try:
            if self.workspace.classify(Path(current.document.path)) is not PathClass.WORKING:
                return False
            if sha256_file(Path(current.document.path)) != changeset.document.sha256:
                return False
        except (OSError, WorkspaceError):
            return False
        return True

    @staticmethod
    def _resolve_changed_entity_scope(changeset: Changeset, actual_handles: tuple[str, ...]) -> tuple[tuple[str, ...], bool, bool]:
        expected = tuple(changeset.expected_changed_entities)
        if expected == ("NEW:Polyline",):
            exact = len(actual_handles) == 1 and isinstance(actual_handles[0], str) and bool(actual_handles[0])
            unrelated = len(actual_handles) > 1
            return actual_handles if exact else (), exact, unrelated
        exact = len(actual_handles) == len(expected) and set(actual_handles) == set(expected)
        unrelated = bool(set(actual_handles) - set(expected))
        return expected if exact else (), exact, unrelated

    @staticmethod
    def _entity_geometry_ok(
        changeset: Changeset,
        resolved_handle: str,
        inspect_data: dict[str, object],
        measure_data: dict[str, object],
    ) -> bool:
        if len(changeset.operations) != 1 or not isinstance(changeset.operations[0], CreatePolyline):
            return False
        entities = inspect_data.get("entities")
        if not isinstance(entities, list) or len(entities) != 1 or not isinstance(entities[0], dict):
            return False
        entity = entities[0]
        operation = changeset.operations[0]
        if entity.get("handle") != resolved_handle:
            return False
        if entity.get("type") not in {"Polyline", "LwPolyline", "LWPolyline"}:
            return False
        if entity.get("layer") != operation.layer:
            return False
        if entity.get("closed") is not operation.closed:
            return False
        if measure_data.get("handle") != resolved_handle:
            return False
        if measure_data.get("closed") is not operation.closed:
            return False
        expected_length, expected_area = _polyline_expected_geometry(operation)
        if not _close(measure_data.get("length"), expected_length):
            return False
        if expected_area is not None and not _close(measure_data.get("area"), expected_area):
            return False
        return True

    def _audit_ok(self, audit: dict[str, object]) -> bool:
        return (
            audit.get("ok") is True
            and audit.get("target_format") == self.target_format
            and audit.get("target_version") == self.target_version
            and audit.get("target_compatible") is True
            and audit.get("dropped_on_save") == []
        )

    async def verify(self, changeset: Changeset, change: ChangeReceipt) -> TechnicalVerificationReceipt:
        if change.changeset_sha256 != changeset.changeset_sha256:
            raise VerificationError("CHANGE_RECEIPT_BINDING_MISMATCH")
        if change.status != "COMPLETED":
            raise VerificationError("CHANGE_NOT_COMPLETED")
        if change.revision_before != changeset.document.revision:
            raise VerificationError("CHANGE_BASE_REVISION_MISMATCH")

        current = await self.adapter.status()
        source_ok = self._source_integrity(changeset, current)
        revision_ok = current.document.revision == change.revision_after and change.revision_after > change.revision_before

        actual_handles = tuple(change.changed_entities)
        resolved_handles, exact_changed_set, unrelated_change = self._resolve_changed_entity_scope(changeset, actual_handles)

        inspect_data: dict[str, object]
        measure_data: dict[str, object]
        if len(resolved_handles) == 1:
            resolved_handle = resolved_handles[0]
            inspect_data = await self.adapter.inspect({"op": "query", "handle": resolved_handle})
            measure_data = await self.adapter.measure({"handle": resolved_handle, "op": "geometry"})
        else:
            inspect_data = {}
            measure_data = {}
        geometry_ok = (
            exact_changed_set
            and len(resolved_handles) == 1
            and self._entity_geometry_ok(changeset, resolved_handles[0], inspect_data, measure_data)
        )

        capture = await self.adapter.capture({"scope": "viewport", "diff": True})
        diff = capture.get("diff")
        capture_ok = isinstance(capture.get("resource_uri"), str) and bool(capture.get("resource_uri"))
        if isinstance(diff, dict):
            capture_ok = capture_ok and diff.get("changed") is True
        else:
            capture_ok = False

        audit = await self.adapter.audit({"target_format": self.target_format, "target_version": self.target_version})
        audit_ok = self._audit_ok(audit)

        checks: dict[str, bool] = {
            "source_integrity": source_ok,
            "post_revision_matches": revision_ok,
            "changed_entity_scope_exact": exact_changed_set,
            "geometry_kernel_matches": geometry_ok,
            "visual_change_captured": capture_ok,
            "target_audit_lossless": audit_ok,
        }
        governed_postcondition_ok = geometry_ok and audit_ok and source_ok and revision_ok and exact_changed_set
        model_postconditions: dict[str, bool] = {}
        for postcondition in changeset.postconditions:
            if postcondition in checks:
                model_postconditions[postcondition] = governed_postcondition_ok
            else:
                model_postconditions[postcondition] = governed_postcondition_ok

        for key, value in model_postconditions.items():
            checks[f"model:{key}"] = value

        decision = "PASS" if all(checks.values()) and not unrelated_change else "FAIL"
        receipt = TechnicalVerificationReceipt(
            schema="cew.cad.verification.v1",
            changeset_sha256=changeset.changeset_sha256,
            change_receipt_sha256=sha256_json(change),
            session_id=current.session_id,
            document_id=current.document.document_id,
            verified_revision=current.document.revision,
            source_sha256=current.document.sha256,
            capabilities_sha256=current.capabilities.capabilities_sha256,
            postconditions=checks,
            unrelated_change=unrelated_change,
            audit_sha256=sha256_json(audit),
            decision=decision,
        )
        self.receipt_store.write("verification", receipt)
        return receipt

    async def save_verified_copy(
        self,
        changeset: Changeset,
        verification: TechnicalVerificationReceipt,
        source_ref: str,
    ) -> VerifiedCopyReceipt:
        if verification.decision != "PASS":
            raise VerificationError("VERIFICATION_NOT_PASS")
        if verification.changeset_sha256 != changeset.changeset_sha256:
            raise VerificationError("VERIFICATION_CHANGESET_MISMATCH")

        try:
            source = self.workspace.resolve_ref(source_ref, PathClass.WORKING)
        except WorkspaceError as exc:
            raise VerificationError("SOURCE_REF_NOT_WORKING") from exc
        if source.resolve() != Path(changeset.document.path).resolve():
            raise VerificationError("SOURCE_REF_DOCUMENT_MISMATCH")
        if sha256_file(source) != changeset.document.sha256:
            raise VerificationError("SOURCE_CHANGED_AFTER_VERIFICATION")

        current = await self.adapter.status()
        if (
            current.session_id != verification.session_id
            or current.document.document_id != verification.document_id
            or current.document.revision != verification.verified_revision
            or current.document.path != changeset.document.path
            or current.document.sha256 != verification.source_sha256
            or current.capabilities.capabilities_sha256 != verification.capabilities_sha256
        ):
            raise VerificationError("VERIFICATION_STATE_STALE")

        suffix = "." + self.target_format
        try:
            output = self.workspace.verified_output(source_ref, changeset.changeset_id, suffix)
        except WorkspaceError as exc:
            raise VerificationError("VERIFIED_OUTPUT_REJECTED") from exc

        source_hash_before = sha256_file(source)
        result = await self.adapter.save_verified(
            output,
            target_format=self.target_format,
            target_version=self.target_version,
            expected=current.document,
        )
        if result.get("ok") is not True or result.get("semantic_verification_passed") is not True:
            raise VerificationError("VERIFIED_SAVE_FAILED")
        if result.get("target_format") not in (None, self.target_format):
            raise VerificationError("VERIFIED_SAVE_FORMAT_MISMATCH")
        if result.get("target_version") not in (None, self.target_version):
            raise VerificationError("VERIFIED_SAVE_VERSION_MISMATCH")
        if result.get("actual_version") not in (None, self.target_version):
            raise VerificationError("VERIFIED_SAVE_ACTUAL_VERSION_MISMATCH")
        if not output.exists() or not output.is_file():
            raise VerificationError("VERIFIED_OUTPUT_MISSING")
        output_hash = sha256_file(output)
        if result.get("sha256") != output_hash:
            raise VerificationError("VERIFIED_OUTPUT_HASH_MISMATCH")
        if sha256_file(source) != source_hash_before or source_hash_before != changeset.document.sha256:
            raise VerificationError("SOURCE_CHANGED_DURING_SAVE")

        receipt = VerifiedCopyReceipt(
            schema="cew.cad.verified-copy.v1",
            verification_receipt_sha256=sha256_json(verification),
            output_path=str(output),
            target_format=self.target_format,
            target_version=self.target_version,
            output_sha256=output_hash,
            semantic_verification_passed=True,
            status="CANDIDATE_FOR_HUMAN_REVIEW",
        )
        self.receipt_store.write("verified-copy", receipt)
        return receipt
