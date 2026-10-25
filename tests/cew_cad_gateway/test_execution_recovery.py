from __future__ import annotations

import asyncio
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cew_cad_gateway.approval import ApprovalVerifier, sign_approval
from cew_cad_gateway.canonical import sha256_file
from cew_cad_gateway.changesets import ChangesetService, ProposalRequest
from cew_cad_gateway.execution import ExecutionError, ExecutionService
from cew_cad_gateway.policy import GatewayPolicy
from cew_cad_gateway.receipts import ReceiptStore
from cew_cad_gateway.types import (
    CADStatus,
    CapabilityIdentity,
    CreatePolyline,
    DocumentIdentity,
    EpistemicState,
    InspectionReceipt,
    PathClass,
)
from cew_cad_gateway.workspace import Workspace


class RecoveryAdapter:
    def __init__(self, current: CADStatus) -> None:
        self.current = current
        self.apply_calls = 0
        self.status_queries: list[str] = []
        self.operation_result = {"status": "completed", "revision": 8, "changed_entities": ["87"]}

    async def status(self):
        return self.current

    async def apply_operation(self, operation, *, request_id, expected):
        self.apply_calls += 1
        raise AssertionError("recovery must never apply a mutation")

    async def operation_status(self, request_id):
        self.status_queries.append(request_id)
        return dict(self.operation_result)

    async def inspect(self, request): raise AssertionError
    async def measure(self, request): raise AssertionError
    async def audit(self, target): raise AssertionError
    async def capture(self, request): raise AssertionError
    async def save_verified(self, *args, **kwargs): raise AssertionError


class ExecutionRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "CivilExisting"
        self.root.mkdir()
        zones = {
            "SOURCE": "00_sources",
            "BASELINE": "01_baseline",
            "WORKING": "02_working",
            "EVIDENCE": "03_evidence",
            "CHANGESETS": "04_changesets",
            "AUDITS": "05_audits",
            "VERIFIED": "06_verified",
            "ISSUED": "07_issued",
        }
        for zone in zones.values():
            (self.root / zone).mkdir()
        self.policy = GatewayPolicy(
            zones=zones,
            mutable_path_classes=("WORKING",),
            max_primary_operations=1,
            allow_overwrite=False,
            allowed_mutating_operations=("create_polyline", "undo_own_change"),
            allowed_property_paths=(),
            required_capabilities=("query", "audit", "capture", "save_verified"),
        )
        self.workspace = Workspace(self.root, self.policy)
        self.drawing = self.root / "02_working" / "lab.dwg"
        self.drawing.write_bytes(b"lab-drawing")
        self.document = DocumentIdentity(
            path=str(self.drawing),
            sha256=sha256_file(self.drawing),
            document_id=3,
            revision=7,
        )
        self.capabilities = CapabilityIdentity(cad_build="2026.42@b6fbac39ffc7", capabilities_sha256="1" * 64)
        self.base_status = CADStatus(session_id="session-lab", document=self.document, capabilities=self.capabilities)
        inspection = InspectionReceipt(
            schema="cew.cad.inspection.v1",
            status=replace(self.base_status, path_class=PathClass.WORKING),
            audit_sha256="2" * 64,
            observed_at="2026-10-25T06:00:00+00:00",
        )
        proposal = ProposalRequest(
            changeset_id="CEW-CAD-LAB-RECOVERY",
            intent="recover completed lab mutation",
            operations=(CreatePolyline(layer="CEW-LAB", points=((0.0, 0.0), (1.0, 0.0))),),
            evidence_refs=("LAB-E",),
            claim_refs=("LAB-C",),
            decision_refs=("LAB-D",),
            coordinate_states=(EpistemicState.RIF, EpistemicState.RIF),
            epistemic_states=(EpistemicState.RIF,),
            preconditions=(),
            postconditions=(),
            expected_changed_entities=("NEW:Polyline",),
            forbidden_side_effects=("no unrelated entity changes",),
            unresolved=(),
            influential_unresolved=False,
            target_unique=True,
            output_path=None,
        )
        service = ChangesetService(
            self.policy,
            known_evidence={"LAB-E"},
            known_claims={"LAB-C"},
            known_decisions={"LAB-D"},
        )
        self.changeset = service.propose(proposal, inspection)

        self.key = Ed25519PrivateKey.generate()
        self.private_path = Path(self.tmp.name) / "private.pem"
        self.public_path = Path(self.tmp.name) / "public.pem"
        self.private_path.write_bytes(
            self.key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        )
        self.public_path.write_bytes(
            self.key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        )
        self.approval = sign_approval(
            changeset=self.changeset,
            private_key_path=self.private_path,
            approval_id="CEW-CAD-APP-RECOVERY",
            approved_by="human",
            approved_at="2026-10-25T06:01:00+00:00",
        )
        self.receipt_store = ReceiptStore(self.root / "05_audits")

        initial_verifier = ApprovalVerifier(
            self.public_path,
            now=lambda: "2026-10-25T06:02:00+00:00",
            max_age_seconds=900,
            receipt_store=self.receipt_store,
        )
        initial_verifier.consume(self.approval, self.changeset)

        post_document = replace(self.document, revision=8)
        self.adapter = RecoveryAdapter(replace(self.base_status, document=post_document))
        self.execution = self._execution(now="2026-10-25T06:03:00+00:00")

    def _execution(self, *, now: str) -> ExecutionService:
        recovery_verifier = ApprovalVerifier(
            self.public_path,
            now=lambda: now,
            max_age_seconds=900,
            receipt_store=self.receipt_store,
        )
        return ExecutionService(
            adapter=self.adapter,
            workspace=self.workspace,
            policy=self.policy,
            approval_verifier=recovery_verifier,
            receipt_store=self.receipt_store,
        )

    def test_reconcile_completed_operation_without_reapply(self) -> None:
        receipt = asyncio.run(self.execution.reconcile(self.changeset, self.approval))

        self.assertEqual(self.adapter.apply_calls, 0)
        self.assertEqual(self.adapter.status_queries, [receipt.request_id])
        self.assertEqual(receipt.revision_before, 7)
        self.assertEqual(receipt.revision_after, 8)
        self.assertEqual(receipt.changed_entities, ("87",))
        self.assertEqual(receipt.status, "COMPLETED")

    def test_recovery_rejects_approval_that_was_never_consumed(self) -> None:
        unconsumed = sign_approval(
            changeset=self.changeset,
            private_key_path=self.private_path,
            approval_id="CEW-CAD-APP-UNCONSUMED",
            approved_by="human",
            approved_at="2026-10-25T06:01:00+00:00",
        )
        with self.assertRaisesRegex(ExecutionError, "APPROVAL_NOT_CONSUMED"):
            asyncio.run(self.execution.reconcile(self.changeset, unconsumed))
        self.assertEqual(self.adapter.apply_calls, 0)
        self.assertEqual(self.adapter.status_queries, [])

    def test_recovery_rejects_different_signed_approval_reusing_consumed_id(self) -> None:
        different = sign_approval(
            changeset=self.changeset,
            private_key_path=self.private_path,
            approval_id=self.approval.approval_id,
            approved_by="different-human",
            approved_at="2026-10-25T06:01:30+00:00",
        )
        with self.assertRaisesRegex(ExecutionError, "APPROVAL_REJECTED"):
            asyncio.run(self.execution.reconcile(self.changeset, different))
        self.assertEqual(self.adapter.apply_calls, 0)
        self.assertEqual(self.adapter.status_queries, [])

    def test_recovery_rejects_live_revision_different_from_confirmed_operation(self) -> None:
        self.adapter.current = replace(self.adapter.current, document=replace(self.adapter.current.document, revision=9))
        with self.assertRaisesRegex(ExecutionError, "RECOVERY_REVISION_MISMATCH"):
            asyncio.run(self.execution.reconcile(self.changeset, self.approval))
        self.assertEqual(self.adapter.apply_calls, 0)
        self.assertEqual(len(self.adapter.status_queries), 1)

    def test_consumed_approval_may_be_reconciled_after_signing_window_expires(self) -> None:
        delayed_recovery = self._execution(now="2026-10-25T08:00:00+00:00")
        receipt = asyncio.run(delayed_recovery.reconcile(self.changeset, self.approval))
        self.assertEqual(receipt.status, "COMPLETED")
        self.assertEqual(self.adapter.apply_calls, 0)

    def test_recovery_still_rejects_tampered_signature_after_consumption(self) -> None:
        tampered = replace(self.approval, signature="AAAA")
        delayed_recovery = self._execution(now="2026-10-25T08:00:00+00:00")
        with self.assertRaisesRegex(ExecutionError, "APPROVAL_REJECTED"):
            asyncio.run(delayed_recovery.reconcile(self.changeset, tampered))
        self.assertEqual(self.adapter.apply_calls, 0)
        self.assertEqual(self.adapter.status_queries, [])


if __name__ == "__main__":
    unittest.main()
