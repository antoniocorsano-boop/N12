from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

from .adapters.base import CADAdapter
from .approval import ApprovalError, ApprovalVerifier
from .canonical import sha256_file, sha256_json
from .changesets import verify_changeset_digest
from .policy import GatewayPolicy
from .receipts import ReceiptStore
from .types import ApprovalReceipt, ChangeReceipt, Changeset, CreatePolyline, PathClass
from .workspace import Workspace, WorkspaceError


class ExecutionError(ValueError):
    pass


class ExecutionService:
    def __init__(
        self,
        *,
        adapter: CADAdapter,
        workspace: Workspace,
        policy: GatewayPolicy,
        approval_verifier: ApprovalVerifier,
        receipt_store: ReceiptStore,
    ) -> None:
        self.adapter = adapter
        self.workspace = workspace
        self.policy = policy
        self.approval_verifier = approval_verifier
        self.receipt_store = receipt_store

    @staticmethod
    def _request_id(changeset: Changeset) -> str:
        digest = hashlib.sha256(f"{changeset.changeset_id}:0".encode("utf-8")).hexdigest()
        return f"cew-cad-{digest[:32]}"

    def _validate_operation(self, changeset: Changeset) -> CreatePolyline:
        if len(changeset.operations) != 1 or len(changeset.operations) > self.policy.max_primary_operations:
            raise ExecutionError("PRIMARY_OPERATION_COUNT_INVALID")
        operation = changeset.operations[0]
        if not isinstance(operation, CreatePolyline):
            raise ExecutionError("MUTATION_TYPE_NOT_AUTHORIZED")
        if operation.layer != "CEW-LAB" or "create_polyline" not in self.policy.allowed_mutating_operations:
            raise ExecutionError("POLICY_MUTATION_REJECTED")
        return operation

    async def _preflight(self, changeset: Changeset, approval: ApprovalReceipt):
        if not verify_changeset_digest(changeset):
            raise ExecutionError("CHANGESET_DIGEST_MISMATCH")
        current = await self.adapter.status()
        if current.session_id != changeset.session_id:
            raise ExecutionError("CAD_SESSION_MISMATCH")
        if current.document.path != changeset.document.path:
            raise ExecutionError("CAD_DOCUMENT_PATH_MISMATCH")
        try:
            if self.workspace.classify(Path(current.document.path)) is not PathClass.WORKING:
                raise ExecutionError("CAD_TARGET_NOT_WORKING")
        except WorkspaceError as exc:
            raise ExecutionError("CAD_TARGET_NOT_WORKING") from exc
        if current.document.document_id != changeset.document.document_id:
            raise ExecutionError("CAD_DOCUMENT_ID_MISMATCH")
        if current.document.revision != changeset.document.revision:
            raise ExecutionError("CAD_REVISION_STALE")
        if current.document.sha256 != changeset.document.sha256:
            raise ExecutionError("CAD_SOURCE_HASH_MISMATCH")
        try:
            local_hash = sha256_file(Path(current.document.path))
        except OSError as exc:
            raise ExecutionError("CAD_SOURCE_NOT_READABLE") from exc
        if local_hash != changeset.document.sha256:
            raise ExecutionError("CAD_LOCAL_HASH_MISMATCH")
        if current.capabilities != changeset.capabilities:
            raise ExecutionError("CAD_CAPABILITY_IDENTITY_MISMATCH")
        operation = self._validate_operation(changeset)
        try:
            self.approval_verifier.consume(approval, changeset)
        except ApprovalError as exc:
            raise ExecutionError("APPROVAL_REJECTED") from exc
        return current, operation

    async def _execute_with_idempotency(self, operation: CreatePolyline, *, request_id: str, expected):
        try:
            return await self.adapter.apply_operation(operation, request_id=request_id, expected=expected)
        except (asyncio.TimeoutError, TimeoutError):
            status = await self.adapter.operation_status(request_id)
            state = status.get("status")
            if state == "completed":
                return status
            if state == "running":
                raise ExecutionError("MUTATION_STILL_RUNNING")
            if state == "not_found":
                try:
                    return await self.adapter.apply_operation(operation, request_id=request_id, expected=expected)
                except (asyncio.TimeoutError, TimeoutError) as exc:
                    raise ExecutionError("MUTATION_RETRY_AMBIGUOUS") from exc
            raise ExecutionError("MUTATION_STATUS_UNKNOWN")

    async def apply(self, changeset: Changeset, approval: ApprovalReceipt) -> ChangeReceipt:
        current, operation = await self._preflight(changeset, approval)
        request_id = self._request_id(changeset)
        result = await self._execute_with_idempotency(operation, request_id=request_id, expected=current.document)
        if result.get("status") != "completed":
            raise ExecutionError("MUTATION_NOT_COMPLETED")
        revision_after = result.get("revision")
        changed = result.get("changed_entities")
        if not isinstance(revision_after, int) or isinstance(revision_after, bool) or revision_after <= current.document.revision:
            raise ExecutionError("MUTATION_REVISION_INVALID")
        if not isinstance(changed, list) or any(not isinstance(item, str) or not item for item in changed):
            raise ExecutionError("MUTATION_CHANGESET_INVALID")
        receipt = ChangeReceipt(
            schema="cew.cad.change.v1",
            changeset_sha256=changeset.changeset_sha256,
            approval_sha256=sha256_json(approval),
            request_id=request_id,
            revision_before=current.document.revision,
            revision_after=revision_after,
            changed_entities=tuple(changed),
            status="COMPLETED",
        )
        self.receipt_store.write("change", receipt)
        return receipt
