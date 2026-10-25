from __future__ import annotations

import asyncio
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from cew_cad_gateway.canonical import sha256_json
from cew_cad_gateway.runtime import GatewayRuntimeImpl
from cew_cad_gateway.types import (
    ApprovalReceipt,
    CapabilityIdentity,
    ChangeReceipt,
    Changeset,
    CreatePolyline,
    DocumentIdentity,
    EpistemicState,
    TechnicalVerificationReceipt,
    VerifiedCopyReceipt,
)


class FakeArtifacts:
    def __init__(self, changeset, approval) -> None:
        self.changeset = changeset
        self.approval = approval

    def load_changeset(self, changeset_id):
        self.loaded_changeset_id = changeset_id
        return self.changeset

    def load_approval(self, approval_id):
        self.loaded_approval_id = approval_id
        return self.approval


class RecoveryExecution:
    def __init__(self, change) -> None:
        self.change = change
        self.reconcile_calls = []
        self.apply_calls = 0

    async def reconcile(self, changeset, approval):
        self.reconcile_calls.append((changeset, approval))
        return self.change

    async def apply(self, changeset, approval):
        self.apply_calls += 1
        raise AssertionError("recovery must not enter apply")


class RecoveryVerification:
    def __init__(self, verification, verified_copy) -> None:
        self.verification = verification
        self.verified_copy = verified_copy
        self.verify_calls = []
        self.save_calls = []

    async def verify(self, changeset, change):
        self.verify_calls.append((changeset, change))
        return self.verification

    async def save_verified_copy(self, changeset, verification, source_ref):
        self.save_calls.append((changeset, verification, source_ref))
        return self.verified_copy


class FakeWorkspace:
    def reference_for(self, path, path_class):
        return "02_working/lab.dwg"


class RuntimeRecoveryTests(unittest.TestCase):
    def test_recovery_reconciles_then_verifies_and_saves_without_apply(self) -> None:
        document = DocumentIdentity(path="/tmp/lab.dwg", sha256="0" * 64, document_id=3, revision=1)
        changeset = Changeset(
            schema="cew.cad.changeset.v1",
            changeset_id="CEW-CAD-LAB-004C",
            intent="lab",
            session_id="session-1",
            document=document,
            capabilities=CapabilityIdentity(cad_build="2026.42@build", capabilities_sha256="1" * 64),
            evidence_refs=("E",), claim_refs=("C",), decision_refs=("D",),
            epistemic_states=(EpistemicState.RIF,),
            operations=(CreatePolyline(layer="CEW-LAB", points=((0.0, 0.0), (1.0, 0.0))),),
            preconditions=(), postconditions=(), expected_changed_entities=("NEW:Polyline",),
            forbidden_side_effects=(), unresolved=(), changeset_sha256="2" * 64,
        )
        approval = ApprovalReceipt(
            schema="cew.cad.approval.v1", approval_id="APP-004G", changeset_id=changeset.changeset_id,
            changeset_sha256=changeset.changeset_sha256, document_sha256=document.sha256,
            document_id=3, base_revision=1, decision="APPROVED", approved_by="human",
            approved_at="2026-10-25T06:00:00+00:00", signature="sig",
        )
        change = ChangeReceipt(
            schema="cew.cad.change.v1", changeset_sha256=changeset.changeset_sha256,
            approval_sha256=sha256_json(approval), request_id="cew-cad-req",
            revision_before=1, revision_after=2, changed_entities=("87",), status="COMPLETED",
        )
        verification = TechnicalVerificationReceipt(
            schema="cew.cad.verification.v1", changeset_sha256=changeset.changeset_sha256,
            change_receipt_sha256=sha256_json(change), session_id="session-1", document_id=3,
            verified_revision=2, source_sha256=document.sha256, capabilities_sha256="1" * 64,
            postconditions={"source_integrity": True}, unrelated_change=False,
            audit_sha256="3" * 64, decision="PASS",
        )
        verified_copy = VerifiedCopyReceipt(
            schema="cew.cad.verified-copy.v1", verification_receipt_sha256=sha256_json(verification),
            output_path="/tmp/verified.dwg", target_format="dwg", target_version="2018",
            output_sha256="4" * 64, semantic_verification_passed=True,
            status="CANDIDATE_FOR_HUMAN_REVIEW",
        )
        execution = RecoveryExecution(change)
        verifier = RecoveryVerification(verification, verified_copy)
        runtime = GatewayRuntimeImpl(
            inspection_service=object(), changeset_service=object(), execution_service=execution,
            verification_service=verifier, artifacts=FakeArtifacts(changeset, approval),
            workspace=FakeWorkspace(), target_format="dwg", target_version="2018",
        )

        result = asyncio.run(runtime.recover_approved_changeset("CEW-CAD-LAB-004C", "APP-004G"))

        self.assertEqual(execution.apply_calls, 0)
        self.assertEqual(len(execution.reconcile_calls), 1)
        self.assertEqual(len(verifier.verify_calls), 1)
        self.assertEqual(len(verifier.save_calls), 1)
        self.assertEqual(result["status"], "RECOVERED_AND_SAVED")
        self.assertEqual(result["change_id"], sha256_json(change))
        self.assertEqual(result["verification_id"], sha256_json(verification))


if __name__ == "__main__":
    unittest.main()
