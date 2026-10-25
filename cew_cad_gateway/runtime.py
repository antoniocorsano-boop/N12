from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifacts import ArtifactRepository
from .canonical import canonical_json_bytes, sha256_json
from .changesets import ChangesetService, ProposalRequest
from .execution import ExecutionService
from .inspection import InspectionService
from .server import PolylineProposalInput
from .types import CreatePolyline, EpistemicState, PathClass
from .verification import VerificationService
from .workspace import Workspace


def _jsonable(value: object) -> dict[str, Any]:
    decoded = json.loads(canonical_json_bytes(value).decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("RUNTIME_RESULT_MUST_BE_OBJECT")
    return decoded


class GatewayRuntimeImpl:
    def __init__(
        self,
        *,
        inspection_service: InspectionService,
        changeset_service: ChangesetService,
        execution_service: ExecutionService,
        verification_service: VerificationService,
        artifacts: ArtifactRepository,
        workspace: Workspace,
        target_format: str,
        target_version: str,
    ) -> None:
        self.inspection_service = inspection_service
        self.changeset_service = changeset_service
        self.execution_service = execution_service
        self.verification_service = verification_service
        self.artifacts = artifacts
        self.workspace = workspace
        self.target_format = target_format
        self.target_version = target_version

    async def status(self) -> dict[str, Any]:
        return _jsonable(await self.inspection_service.status())

    async def inspect(self, request: dict[str, Any]) -> dict[str, Any]:
        return _jsonable(await self.inspection_service.inspect(dict(request)))

    async def measure(self, request: dict[str, Any]) -> dict[str, Any]:
        return _jsonable(await self.inspection_service.measure(dict(request)))

    async def audit(self, target_format: str, target_version: str) -> dict[str, Any]:
        if target_format != self.target_format or target_version != self.target_version:
            raise ValueError("TARGET_NOT_AUTHORIZED")
        result = await self.inspection_service.audit(
            {"target_format": target_format, "target_version": target_version}
        )
        return _jsonable(result)

    async def capture(self, scope: str, diff: bool) -> dict[str, Any]:
        if scope not in {"viewport", "window"}:
            raise ValueError("CAPTURE_SCOPE_NOT_AUTHORIZED")
        return _jsonable(await self.inspection_service.capture({"scope": scope, "diff": bool(diff)}))

    async def propose_changeset(self, proposal: PolylineProposalInput) -> dict[str, Any]:
        audit_result = await self.inspection_service.audit(
            {"target_format": self.target_format, "target_version": self.target_version}
        )
        inspection = audit_result["receipt"]
        points = tuple((float(x), float(y)) for x, y in proposal.points)
        request = ProposalRequest(
            changeset_id=proposal.changeset_id,
            intent=proposal.intent,
            operations=(CreatePolyline(layer="CEW-LAB", points=points, closed=True),),
            evidence_refs=tuple(proposal.evidence_refs),
            claim_refs=tuple(proposal.claim_refs),
            decision_refs=tuple(proposal.decision_refs),
            coordinate_states=tuple(EpistemicState(item) for item in proposal.coordinate_states),
            epistemic_states=tuple(EpistemicState(item) for item in proposal.epistemic_states),
            preconditions=tuple(proposal.preconditions),
            postconditions=tuple(proposal.postconditions),
            expected_changed_entities=("NEW:Polyline",),
            forbidden_side_effects=tuple(proposal.forbidden_side_effects),
            unresolved=tuple(proposal.unresolved),
            influential_unresolved=proposal.influential_unresolved,
            target_unique=proposal.target_unique,
            output_path=None,
            cad_data=(),
        )
        changeset = self.changeset_service.propose(request, inspection)
        self.artifacts.store_changeset(changeset)
        return {
            "status": "PROPOSED",
            "changeset_id": changeset.changeset_id,
            "changeset_sha256": changeset.changeset_sha256,
        }

    async def apply_approved_changeset(self, changeset_id: str, approval_id: str) -> dict[str, Any]:
        changeset = self.artifacts.load_changeset(changeset_id)
        approval = self.artifacts.load_approval(approval_id)
        change = await self.execution_service.apply(changeset, approval)
        change_id = sha256_json(change)
        return {
            "status": change.status,
            "changeset_id": changeset_id,
            "approval_id": approval_id,
            "change_id": change_id,
            "receipt": _jsonable(change),
        }

    async def verify_changeset(self, changeset_id: str, change_id: str) -> dict[str, Any]:
        changeset = self.artifacts.load_changeset(changeset_id)
        change = self.artifacts.load_change(change_id)
        verification = await self.verification_service.verify(changeset, change)
        verification_id = sha256_json(verification)
        return {
            "decision": verification.decision,
            "changeset_id": changeset_id,
            "change_id": change_id,
            "verification_id": verification_id,
            "receipt": _jsonable(verification),
        }

    async def save_verified_copy(self, changeset_id: str, verification_id: str) -> dict[str, Any]:
        changeset = self.artifacts.load_changeset(changeset_id)
        verification = self.artifacts.load_verification(verification_id)
        source_ref = self.workspace.reference_for(Path(changeset.document.path), PathClass.WORKING)
        verified = await self.verification_service.save_verified_copy(changeset, verification, source_ref)
        result = _jsonable(verified)
        result["verification_id"] = verification_id
        return result

    async def recover_approved_changeset(self, changeset_id: str, approval_id: str) -> dict[str, Any]:
        """Recover a mutation already confirmed by OCS, then verify and save it.

        Recovery never calls the mutating apply path and never consumes approval
        again. ExecutionService.reconcile proves the prior operation from the
        deterministic request ID and durable approval-consumption state.
        """
        changeset = self.artifacts.load_changeset(changeset_id)
        approval = self.artifacts.load_approval(approval_id)
        change = await self.execution_service.reconcile(changeset, approval)
        change_id = sha256_json(change)

        verification = await self.verification_service.verify(changeset, change)
        verification_id = sha256_json(verification)
        if verification.decision != "PASS":
            return {
                "status": "RECOVERY_VERIFICATION_FAILED",
                "changeset_id": changeset_id,
                "approval_id": approval_id,
                "change_id": change_id,
                "verification_id": verification_id,
                "change": _jsonable(change),
                "verification": _jsonable(verification),
            }

        source_ref = self.workspace.reference_for(Path(changeset.document.path), PathClass.WORKING)
        verified = await self.verification_service.save_verified_copy(changeset, verification, source_ref)
        return {
            "status": "RECOVERED_AND_SAVED",
            "changeset_id": changeset_id,
            "approval_id": approval_id,
            "change_id": change_id,
            "verification_id": verification_id,
            "change": _jsonable(change),
            "verification": _jsonable(verification),
            "verified_copy": _jsonable(verified),
        }
