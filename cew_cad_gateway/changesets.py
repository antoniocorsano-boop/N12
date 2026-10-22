from __future__ import annotations

import math
from dataclasses import dataclass

from .canonical import sha256_json
from .policy import GatewayPolicy
from .types import Changeset, CreatePolyline, EpistemicState, InspectionReceipt, PathClass


class ChangesetError(ValueError):
    pass


@dataclass(frozen=True)
class ProposalRequest:
    changeset_id: str
    intent: str
    operations: tuple[object, ...]
    evidence_refs: tuple[str, ...]
    claim_refs: tuple[str, ...]
    decision_refs: tuple[str, ...]
    coordinate_states: tuple[EpistemicState, ...]
    epistemic_states: tuple[EpistemicState, ...]
    preconditions: tuple[str, ...]
    postconditions: tuple[str, ...]
    expected_changed_entities: tuple[str, ...]
    forbidden_side_effects: tuple[str, ...]
    unresolved: tuple[str, ...]
    influential_unresolved: bool
    target_unique: bool
    output_path: str | None
    cad_data: tuple[str, ...] = ()


def changeset_digest_payload(changeset: Changeset) -> dict[str, object]:
    return {
        "schema": changeset.schema,
        "changeset_id": changeset.changeset_id,
        "intent": changeset.intent,
        "session_id": changeset.session_id,
        "document": changeset.document,
        "capabilities": changeset.capabilities,
        "evidence_refs": changeset.evidence_refs,
        "claim_refs": changeset.claim_refs,
        "decision_refs": changeset.decision_refs,
        "epistemic_states": changeset.epistemic_states,
        "operations": changeset.operations,
        "preconditions": changeset.preconditions,
        "postconditions": changeset.postconditions,
        "expected_changed_entities": changeset.expected_changed_entities,
        "forbidden_side_effects": changeset.forbidden_side_effects,
        "unresolved": changeset.unresolved,
    }


def verify_changeset_digest(changeset: Changeset) -> bool:
    return sha256_json(changeset_digest_payload(changeset)) == changeset.changeset_sha256


class ChangesetService:
    def __init__(
        self,
        policy: GatewayPolicy,
        *,
        known_evidence: set[str],
        known_claims: set[str],
        known_decisions: set[str],
    ) -> None:
        self.policy = policy
        self.known_evidence = set(known_evidence)
        self.known_claims = set(known_claims)
        self.known_decisions = set(known_decisions)

    def _validate_refs(self, values: tuple[str, ...], known: set[str], label: str) -> None:
        if any(not value or value not in known for value in values):
            raise ChangesetError(f"UNRESOLVED_{label}_REF")

    def _validate_request(self, request: ProposalRequest, inspection: InspectionReceipt) -> CreatePolyline:
        if inspection.status.path_class is not PathClass.WORKING:
            raise ChangesetError("PROPOSAL_TARGET_NOT_WORKING")
        if not request.changeset_id or not request.intent:
            raise ChangesetError("PROPOSAL_IDENTITY_MISSING")
        if request.output_path is not None:
            raise ChangesetError("MODEL_OUTPUT_PATH_FORBIDDEN")
        if request.influential_unresolved and request.unresolved:
            raise ChangesetError("INFLUENTIAL_INPUT_UNRESOLVED")
        if not request.target_unique:
            raise ChangesetError("TARGET_NOT_UNIQUE")
        if len(request.operations) != 1 or len(request.operations) > self.policy.max_primary_operations:
            raise ChangesetError("PRIMARY_OPERATION_COUNT_INVALID")
        self._validate_refs(request.evidence_refs, self.known_evidence, "EVIDENCE")
        self._validate_refs(request.claim_refs, self.known_claims, "CLAIM")
        self._validate_refs(request.decision_refs, self.known_decisions, "DECISION")
        operation = request.operations[0]
        if not isinstance(operation, CreatePolyline):
            raise ChangesetError("MUTATION_TYPE_NOT_AUTHORIZED")
        if "create_polyline" not in self.policy.allowed_mutating_operations:
            raise ChangesetError("CREATE_POLYLINE_NOT_AUTHORIZED")
        if operation.layer != "CEW-LAB":
            raise ChangesetError("CREATION_LAYER_NOT_AUTHORIZED")
        if len(request.coordinate_states) != len(operation.points):
            raise ChangesetError("COORDINATE_PROVENANCE_INCOMPLETE")
        if EpistemicState.ND in request.coordinate_states:
            raise ChangesetError("ND_COORDINATE_FORBIDDEN")
        if not set(request.coordinate_states).issubset(set(request.epistemic_states)):
            raise ChangesetError("EPISTEMIC_STATE_NOT_PRESERVED")
        for point in operation.points:
            if len(point) != 2 or any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) for value in point):
                raise ChangesetError("INVALID_POLYLINE_COORDINATE")
        return operation

    def propose(self, request: ProposalRequest, inspection: InspectionReceipt) -> Changeset:
        operation = self._validate_request(request, inspection)
        provisional = Changeset(
            schema="cew.cad.changeset.v1",
            changeset_id=request.changeset_id,
            intent=request.intent,
            session_id=inspection.status.session_id,
            document=inspection.status.document,
            capabilities=inspection.status.capabilities,
            evidence_refs=request.evidence_refs,
            claim_refs=request.claim_refs,
            decision_refs=request.decision_refs,
            epistemic_states=request.epistemic_states,
            operations=(operation,),
            preconditions=request.preconditions,
            postconditions=request.postconditions,
            expected_changed_entities=request.expected_changed_entities,
            forbidden_side_effects=request.forbidden_side_effects,
            unresolved=request.unresolved,
            changeset_sha256="0" * 64,
        )
        digest = sha256_json(changeset_digest_payload(provisional))
        return Changeset(
            schema=provisional.schema,
            changeset_id=provisional.changeset_id,
            intent=provisional.intent,
            session_id=provisional.session_id,
            document=provisional.document,
            capabilities=provisional.capabilities,
            evidence_refs=provisional.evidence_refs,
            claim_refs=provisional.claim_refs,
            decision_refs=provisional.decision_refs,
            epistemic_states=provisional.epistemic_states,
            operations=provisional.operations,
            preconditions=provisional.preconditions,
            postconditions=provisional.postconditions,
            expected_changed_entities=provisional.expected_changed_entities,
            forbidden_side_effects=provisional.forbidden_side_effects,
            unresolved=provisional.unresolved,
            changeset_sha256=digest,
        )

    def verify_digest(self, changeset: Changeset) -> bool:
        return verify_changeset_digest(changeset)
