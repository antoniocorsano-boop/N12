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
from cew_cad_gateway.types import CADStatus, CapabilityIdentity, CreatePolyline, DocumentIdentity, EpistemicState, InspectionReceipt, PathClass
from cew_cad_gateway.workspace import Workspace


class FakeExecutionAdapter:
    def __init__(self, status: CADStatus, mode: str = "ok") -> None:
        self.current = status; self.mode = mode
        self.apply_calls: list[tuple[object, str, DocumentIdentity]] = []; self.status_calls: list[str] = []
    async def status(self): return self.current
    async def apply_operation(self, operation, *, request_id, expected):
        self.apply_calls.append((operation, request_id, expected))
        if self.mode in {"timeout_completed", "timeout_running"}: raise asyncio.TimeoutError()
        if self.mode == "timeout_not_found_then_ok" and len(self.apply_calls) == 1: raise asyncio.TimeoutError()
        return {"status":"completed","revision":expected.revision + 1,"changed_entities":["A1"]}
    async def operation_status(self, request_id):
        self.status_calls.append(request_id)
        if self.mode == "timeout_completed": return {"status":"completed","revision":self.current.document.revision + 1,"changed_entities":["A1"]}
        if self.mode == "timeout_running": return {"status":"running"}
        if self.mode == "timeout_not_found_then_ok": return {"status":"not_found"}
        return {"status":"completed"}
    async def inspect(self, request): raise AssertionError
    async def measure(self, request): raise AssertionError
    async def audit(self, target): raise AssertionError
    async def capture(self, request): raise AssertionError
    async def save_verified(self, *args, **kwargs): raise AssertionError


class ExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "CivilExisting"; self.root.mkdir()
        zones = {"SOURCE":"00_sources","BASELINE":"01_baseline","WORKING":"02_working","EVIDENCE":"03_evidence","CHANGESETS":"04_changesets","AUDITS":"05_audits","VERIFIED":"06_verified","ISSUED":"07_issued"}
        for zone in zones.values(): (self.root / zone).mkdir()
        self.policy = GatewayPolicy(zones=zones, mutable_path_classes=("WORKING",), max_primary_operations=1, allow_overwrite=False, allowed_mutating_operations=("create_polyline","undo_own_change"), allowed_property_paths=(), required_capabilities=("query","audit","capture","save_verified"))
        self.workspace = Workspace(self.root, self.policy)
        self.drawing = self.root / "02_working" / "lab.dwg"; self.drawing.write_bytes(b"lab-drawing")
        self.document = DocumentIdentity(path=str(self.drawing), sha256=sha256_file(self.drawing), document_id=1, revision=7)
        self.capabilities = CapabilityIdentity(cad_build="2026.41", capabilities_sha256="1" * 64)
        self.status = CADStatus(session_id="session-1", document=self.document, capabilities=self.capabilities)
        inspection = InspectionReceipt(schema="cew.cad.inspection.v1", status=replace(self.status, path_class=PathClass.WORKING), audit_sha256="2" * 64, observed_at="2026-10-22T05:25:00+02:00")
        proposal = ProposalRequest(changeset_id="CEW-CAD-CS-000001", intent="lab polyline", operations=(CreatePolyline(layer="CEW-LAB", points=((0.0,0.0),(1.0,0.0))),), evidence_refs=("E-001",), claim_refs=("C-001",), decision_refs=("D-001",), coordinate_states=(EpistemicState.MIS, EpistemicState.MIS), epistemic_states=(EpistemicState.MIS,), preconditions=(), postconditions=(), expected_changed_entities=("NEW:Polyline",), forbidden_side_effects=(), unresolved=(), influential_unresolved=False, target_unique=True, output_path=None)
        self.changeset_service = ChangesetService(self.policy, known_evidence={"E-001"}, known_claims={"C-001"}, known_decisions={"D-001"})
        self.changeset = self.changeset_service.propose(proposal, inspection)
        key = Ed25519PrivateKey.generate(); self.private_path = Path(self.tmp.name) / "private.pem"; self.public_path = Path(self.tmp.name) / "public.pem"
        self.private_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        self.public_path.write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
        self.approval = sign_approval(changeset=self.changeset, private_key_path=self.private_path, approval_id="CEW-CAD-APP-000001", approved_by="human", approved_at="2026-10-22T05:30:00+02:00")
        self._service_counter = 0

    def service(self, adapter):
        self._service_counter += 1
        receipt_root = self.root / "05_audits" / f"case-{self._service_counter}"; receipt_root.mkdir()
        receipt_store = ReceiptStore(receipt_root)
        verifier = ApprovalVerifier(self.public_path, now=lambda: "2026-10-22T05:31:00+02:00", max_age_seconds=900, receipt_store=receipt_store)
        return ExecutionService(adapter=adapter, workspace=self.workspace, policy=self.policy, approval_verifier=verifier, receipt_store=receipt_store)

    def test_happy_path_binds_session_status_approval_policy_and_request_id(self) -> None:
        adapter = FakeExecutionAdapter(self.status); receipt = asyncio.run(self.service(adapter).apply(self.changeset, self.approval))
        self.assertEqual(len(adapter.apply_calls), 1); operation, request_id, expected = adapter.apply_calls[0]
        self.assertIsInstance(operation, CreatePolyline); self.assertEqual(expected, self.document); self.assertEqual(receipt.request_id, request_id)
        self.assertEqual(receipt.revision_before, 7); self.assertEqual(receipt.revision_after, 8); self.assertEqual(receipt.changed_entities, ("A1",)); self.assertEqual(receipt.status, "COMPLETED"); self.assertEqual(self.changeset.session_id, "session-1")

    def test_stale_session_document_source_revision_capabilities_and_zone_fail_before_mutation(self) -> None:
        variants = (replace(self.status, session_id="session-2"), replace(self.status, document=replace(self.document, document_id=2)), replace(self.status, document=replace(self.document, sha256="f" * 64)), replace(self.status, document=replace(self.document, revision=8)), replace(self.status, capabilities=replace(self.capabilities, capabilities_sha256="e" * 64)), replace(self.status, document=replace(self.document, path=str(self.root / "01_baseline" / "lab.dwg"))))
        (self.root / "01_baseline" / "lab.dwg").write_bytes(b"baseline")
        for status in variants:
            with self.subTest(status=status):
                adapter = FakeExecutionAdapter(status)
                with self.assertRaises(ExecutionError): asyncio.run(self.service(adapter).apply(self.changeset, self.approval))
                self.assertEqual(adapter.apply_calls, [])

    def test_tampered_changeset_digest_fails_before_mutation(self) -> None:
        adapter = FakeExecutionAdapter(self.status); tampered = replace(self.changeset, changeset_sha256="f" * 64)
        with self.assertRaises(ExecutionError): asyncio.run(self.service(adapter).apply(tampered, self.approval))
        self.assertEqual(adapter.apply_calls, [])

    def test_timeout_queries_status_before_retry_and_never_blind_replays(self) -> None:
        completed = FakeExecutionAdapter(self.status, mode="timeout_completed"); receipt = asyncio.run(self.service(completed).apply(self.changeset, self.approval))
        self.assertEqual(len(completed.apply_calls), 1); self.assertEqual(len(completed.status_calls), 1); self.assertEqual(receipt.status, "COMPLETED")
        running = FakeExecutionAdapter(self.status, mode="timeout_running")
        with self.assertRaises(ExecutionError): asyncio.run(self.service(running).apply(self.changeset, self.approval))
        self.assertEqual(len(running.apply_calls), 1); self.assertEqual(len(running.status_calls), 1)
        retry = FakeExecutionAdapter(self.status, mode="timeout_not_found_then_ok"); receipt2 = asyncio.run(self.service(retry).apply(self.changeset, self.approval))
        self.assertEqual(len(retry.apply_calls), 2); self.assertEqual(retry.apply_calls[0][1], retry.apply_calls[1][1]); self.assertEqual(len(retry.status_calls), 1); self.assertEqual(receipt2.status, "COMPLETED")

    def test_request_id_binds_to_changeset_sha256_not_just_id(self) -> None:
        """
        Two Changesets with identical changeset_id but different changeset_sha256
        must generate different request_ids. The same Changeset replay must
        generate the same request_id.
        """
        adapter = FakeExecutionAdapter(self.status)
        service = self.service(adapter)
        
        # First apply - get the request_id
        receipt1 = asyncio.run(service.apply(self.changeset, self.approval))
        request_id_1 = receipt1.request_id
        
        # Create another changeset with SAME id but DIFFERENT sha256
        # (simulating a different content with same ID)
        import hashlib
        fake_sha = "f" * 64
        changeset2 = self.changeset
        # We can't easily replace the sha256 in a frozen dataclass, so we test
        # the static method directly
        request_id_1_static = ExecutionService._request_id(self.changeset)
        
        # The request_id should include the changeset_sha256 in its hash input
        # Verify that changing the sha256 would change the request_id
        # by creating a mock changeset with different sha256 but same id
        class MockChangeset:
            changeset_id = "CEW-CAD-CS-000001"
            changeset_sha256 = "a" * 64
        
        class MockChangeset2:
            changeset_id = "CEW-CAD-CS-000001"
            changeset_sha256 = "b" * 64
        
        rid1 = ExecutionService._request_id(MockChangeset())
        rid2 = ExecutionService._request_id(MockChangeset2())
        self.assertNotEqual(rid1, rid2, "Different changeset_sha256 must produce different request_ids")
        
        # Same changeset must produce same request_id (idempotent)
        rid3 = ExecutionService._request_id(MockChangeset())
        self.assertEqual(rid1, rid3, "Same changeset must produce same request_id")
        
        # The actual changeset's request_id should match the static method
        self.assertEqual(receipt1.request_id, request_id_1_static)


if __name__ == "__main__": unittest.main()
