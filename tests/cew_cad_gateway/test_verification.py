from __future__ import annotations

import asyncio
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from cew_cad_gateway.canonical import sha256_file, sha256_json
from cew_cad_gateway.changesets import ChangesetService, ProposalRequest
from cew_cad_gateway.policy import GatewayPolicy
from cew_cad_gateway.receipts import ReceiptStore
from cew_cad_gateway.types import (
    CADStatus,
    CapabilityIdentity,
    ChangeReceipt,
    CreatePolyline,
    DocumentIdentity,
    EpistemicState,
    InspectionReceipt,
    PathClass,
)
from cew_cad_gateway.verification import VerificationError, VerificationService
from cew_cad_gateway.workspace import Workspace


class FakeVerificationAdapter:
    def __init__(self, status: CADStatus) -> None:
        self.current = status
        self.inspect_result = {
            "entities": [{"handle": "A1", "type": "Polyline", "layer": "CEW-LAB", "closed": True}]
        }
        self.measure_result = {"handle": "A1", "length": 14.0, "area": 12.0, "closed": True}
        self.capture_result = {"resource_uri": "memory://capture/post", "diff": {"changed": True}}
        self.audit_result = {
            "ok": True,
            "target_format": "dwg",
            "target_version": "2018",
            "target_compatible": True,
            "dropped_on_save": [],
        }
        self.save_result = {"ok": True, "semantic_verification_passed": True, "actual_version": "2018"}
        self.calls: list[tuple[str, object]] = []

    async def status(self):
        self.calls.append(("status", None)); return self.current
    async def inspect(self, request):
        self.calls.append(("inspect", request)); return self.inspect_result
    async def measure(self, request):
        self.calls.append(("measure", request)); return self.measure_result
    async def audit(self, target):
        self.calls.append(("audit", target)); return self.audit_result
    async def capture(self, request):
        self.calls.append(("capture", request)); return self.capture_result
    async def save_verified(self, path, *, target_format, target_version, expected):
        self.calls.append(("save_verified", {"path": path, "target_format": target_format, "target_version": target_version, "expected": expected}))
        Path(path).write_bytes(b"verified-output")
        return {**self.save_result, "path": str(path), "sha256": sha256_file(Path(path)), "target_format": target_format, "target_version": target_version}
    async def apply_operation(self, *args, **kwargs): raise AssertionError("verification must not mutate")
    async def operation_status(self, request_id): raise AssertionError("verification must not query mutation status")


class VerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "CivilExisting"; self.root.mkdir()
        zones = {"SOURCE":"00_sources","BASELINE":"01_baseline","WORKING":"02_working","EVIDENCE":"03_evidence","CHANGESETS":"04_changesets","AUDITS":"05_audits","VERIFIED":"06_verified","ISSUED":"07_issued"}
        for zone in zones.values(): (self.root / zone).mkdir()
        self.policy = GatewayPolicy(zones=zones, mutable_path_classes=("WORKING",), max_primary_operations=1, allow_overwrite=False, allowed_mutating_operations=("create_polyline","undo_own_change"), allowed_property_paths=(), required_capabilities=("query","audit","capture","save_verified"))
        self.workspace = Workspace(self.root, self.policy)
        self.source = self.root / "02_working" / "lab.dwg"; self.source.write_bytes(b"original-lab-drawing")
        self.original_hash = sha256_file(self.source)
        document = DocumentIdentity(path=str(self.source), sha256=self.original_hash, document_id=1, revision=7)
        capabilities = CapabilityIdentity(cad_build="2026.41", capabilities_sha256="1" * 64)
        inspection = InspectionReceipt(schema="cew.cad.inspection.v1", status=CADStatus(session_id="session-1", document=document, capabilities=capabilities, path_class=PathClass.WORKING), audit_sha256="2"*64, observed_at="2026-10-22T05:40:00+02:00")
        proposal = ProposalRequest(
            changeset_id="CEW-CAD-CS-000001", intent="create laboratory rectangle",
            operations=(CreatePolyline(layer="CEW-LAB", points=((0.0,0.0),(4.0,0.0),(4.0,3.0),(0.0,3.0)), closed=True),),
            evidence_refs=("E-001",), claim_refs=("C-001",), decision_refs=("D-001",), coordinate_states=(EpistemicState.MIS,)*4, epistemic_states=(EpistemicState.MIS,),
            preconditions=("working copy bound",), postconditions=("geometry matches proposed rectangle","target audit remains lossless"),
            expected_changed_entities=("NEW:Polyline",), forbidden_side_effects=("no unrelated entity changes",), unresolved=(), influential_unresolved=False, target_unique=True, output_path=None,
        )
        service = ChangesetService(self.policy, known_evidence={"E-001"}, known_claims={"C-001"}, known_decisions={"D-001"})
        self.changeset = service.propose(proposal, inspection)
        self.change = ChangeReceipt(schema="cew.cad.change.v1", changeset_sha256=self.changeset.changeset_sha256, approval_sha256="3"*64, request_id="cew-cad-request-1", revision_before=7, revision_after=8, changed_entities=("A1",), status="COMPLETED")
        post_document = replace(document, revision=8)
        self.adapter = FakeVerificationAdapter(CADStatus(session_id="session-1", document=post_document, capabilities=capabilities))
        self.receipt_root = self.root / "05_audits" / "verification"; self.receipt_root.mkdir()
        self.service = VerificationService(adapter=self.adapter, workspace=self.workspace, receipt_store=ReceiptStore(self.receipt_root), target_format="dwg", target_version="2018")

    def test_verify_resolves_new_entity_scope_to_concrete_handle_and_returns_pass(self) -> None:
        receipt = asyncio.run(self.service.verify(self.changeset, self.change))
        self.assertEqual(receipt.decision, "PASS"); self.assertFalse(receipt.unrelated_change); self.assertTrue(all(receipt.postconditions.values()))
        inspect_call = [payload for name,payload in self.adapter.calls if name == "inspect"][0]
        self.assertEqual(inspect_call["handles"], ["A1"])
        self.assertEqual(sha256_file(self.source), self.original_hash)

    def test_unrelated_missing_or_geometry_mismatch_returns_fail_and_blocks_save(self) -> None:
        for change in (replace(self.change, changed_entities=("A1","B2")), replace(self.change, changed_entities=())):
            with self.subTest(change=change):
                adapter = FakeVerificationAdapter(self.adapter.current)
                root = self.root / "05_audits" / f"case-{len(list((self.root/'05_audits').iterdir()))}"; root.mkdir()
                service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
                receipt = asyncio.run(service.verify(self.changeset, change)); self.assertEqual(receipt.decision, "FAIL")
                with self.assertRaises(VerificationError): asyncio.run(service.save_verified_copy(self.changeset, receipt, "02_working/lab.dwg"))
        adapter = FakeVerificationAdapter(self.adapter.current); adapter.measure_result = {"handle":"A1","length":99.0,"area":12.0,"closed":True}
        root = self.root / "05_audits" / "geometry-mismatch"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        self.assertEqual(asyncio.run(service.verify(self.changeset, self.change)).decision, "FAIL")

    def test_source_hash_change_audit_loss_or_target_incompatibility_returns_fail(self) -> None:
        adapter = FakeVerificationAdapter(self.adapter.current); adapter.audit_result["dropped_on_save"]=["HATCH"]
        root=self.root/"05_audits"/"audit-loss"; root.mkdir(); service=VerificationService(adapter=adapter,workspace=self.workspace,receipt_store=ReceiptStore(root),target_format="dwg",target_version="2018")
        self.assertEqual(asyncio.run(service.verify(self.changeset,self.change)).decision,"FAIL")
        adapter2=FakeVerificationAdapter(self.adapter.current); adapter2.audit_result["target_compatible"]=False
        root2=self.root/"05_audits"/"target-incompatible"; root2.mkdir(); service2=VerificationService(adapter=adapter2,workspace=self.workspace,receipt_store=ReceiptStore(root2),target_format="dwg",target_version="2018")
        self.assertEqual(asyncio.run(service2.verify(self.changeset,self.change)).decision,"FAIL")
        self.source.write_bytes(b"tampered"); adapter3=FakeVerificationAdapter(self.adapter.current)
        root3=self.root/"05_audits"/"source-tampered"; root3.mkdir(); service3=VerificationService(adapter=adapter3,workspace=self.workspace,receipt_store=ReceiptStore(root3),target_format="dwg",target_version="2018")
        self.assertEqual(asyncio.run(service3.verify(self.changeset,self.change)).decision,"FAIL")

    def test_verified_save_uses_generated_path_rechecks_hash_and_keeps_source_unchanged(self) -> None:
        verification=asyncio.run(self.service.verify(self.changeset,self.change)); before=sha256_file(self.source)
        receipt=asyncio.run(self.service.save_verified_copy(self.changeset,verification,"02_working/lab.dwg"))
        self.assertEqual(receipt.status,"CANDIDATE_FOR_HUMAN_REVIEW"); self.assertTrue(receipt.semantic_verification_passed)
        output=Path(receipt.output_path); self.assertTrue(output.exists()); self.assertEqual(output.parent,(self.root/"06_verified").resolve()); self.assertEqual(receipt.output_sha256,sha256_file(output)); self.assertEqual(sha256_file(self.source),before)

    def test_verified_save_rejects_output_hash_mismatch(self) -> None:
        verification=asyncio.run(self.service.verify(self.changeset,self.change)); original=self.adapter.save_verified
        async def bad_hash(path,*,target_format,target_version,expected):
            result=await original(path,target_format=target_format,target_version=target_version,expected=expected); result["sha256"]="f"*64; return result
        self.adapter.save_verified=bad_hash
        with self.assertRaises(VerificationError): asyncio.run(self.service.save_verified_copy(self.changeset,verification,"02_working/lab.dwg"))

    def test_capture_fail_closed_on_missing_diff(self) -> None:
        """Capture must fail closed when diff is missing."""
        adapter = FakeVerificationAdapter(self.adapter.current)
        adapter.capture_result = {"resource_uri": "memory://capture/post"}  # No diff key
        root = self.root / "05_audits" / "capture-no-diff"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        receipt = asyncio.run(service.verify(self.changeset, self.change))
        self.assertEqual(receipt.decision, "FAIL")
        self.assertFalse(receipt.postconditions.get("visual_change_captured", True))

    def test_capture_fail_closed_on_none_diff(self) -> None:
        """Capture must fail closed when diff is None."""
        adapter = FakeVerificationAdapter(self.adapter.current)
        adapter.capture_result = {"resource_uri": "memory://capture/post", "diff": None}
        root = self.root / "05_audits" / "capture-none-diff"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        receipt = asyncio.run(service.verify(self.changeset, self.change))
        self.assertEqual(receipt.decision, "FAIL")
        self.assertFalse(receipt.postconditions.get("visual_change_captured", True))

    def test_capture_fail_closed_on_non_dict_diff(self) -> None:
        """Capture must fail closed when diff is not a dict."""
        adapter = FakeVerificationAdapter(self.adapter.current)
        adapter.capture_result = {"resource_uri": "memory://capture/post", "diff": "not-a-dict"}
        root = self.root / "05_audits" / "capture-non-dict-diff"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        receipt = asyncio.run(service.verify(self.changeset, self.change))
        self.assertEqual(receipt.decision, "FAIL")
        self.assertFalse(receipt.postconditions.get("visual_change_captured", True))

    def test_capture_fail_closed_on_changed_false(self) -> None:
        """Capture must fail closed when diff.changed is False."""
        adapter = FakeVerificationAdapter(self.adapter.current)
        adapter.capture_result = {"resource_uri": "memory://capture/post", "diff": {"changed": False}}
        root = self.root / "05_audits" / "capture-changed-false"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        receipt = asyncio.run(service.verify(self.changeset, self.change))
        self.assertEqual(receipt.decision, "FAIL")
        self.assertFalse(receipt.postconditions.get("visual_change_captured", True))

    def test_capture_fail_closed_on_missing_resource_uri(self) -> None:
        """Capture must fail closed when resource_uri is missing."""
        adapter = FakeVerificationAdapter(self.adapter.current)
        adapter.capture_result = {"diff": {"changed": True}}  # No resource_uri
        root = self.root / "05_audits" / "capture-no-resource-uri"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        receipt = asyncio.run(service.verify(self.changeset, self.change))
        self.assertEqual(receipt.decision, "FAIL")
        self.assertFalse(receipt.postconditions.get("visual_change_captured", True))

    def test_capture_fail_closed_on_empty_resource_uri(self) -> None:
        """Capture must fail closed when resource_uri is empty string."""
        adapter = FakeVerificationAdapter(self.adapter.current)
        adapter.capture_result = {"resource_uri": "", "diff": {"changed": True}}
        root = self.root / "05_audits" / "capture-empty-resource-uri"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        receipt = asyncio.run(service.verify(self.changeset, self.change))
        self.assertEqual(receipt.decision, "FAIL")
        self.assertFalse(receipt.postconditions.get("visual_change_captured", True))

    def test_capture_passes_only_with_valid_resource_uri_and_changed_true(self) -> None:
        """Capture passes only with valid resource_uri AND diff.changed=True."""
        adapter = FakeVerificationAdapter(self.adapter.current)
        adapter.capture_result = {"resource_uri": "memory://capture/post", "diff": {"changed": True}}
        root = self.root / "05_audits" / "capture-valid"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        receipt = asyncio.run(service.verify(self.changeset, self.change))
        self.assertEqual(receipt.decision, "PASS")
        self.assertTrue(receipt.postconditions.get("visual_change_captured", False))

    def test_model_postconditions_cannot_overwrite_built_in_checks(self) -> None:
        """
        Model-authored changeset.postconditions must never overwrite built-in
        governed checks such as source_integrity, changed_entity_scope_exact,
        geometry_kernel_matches, visual_change_captured, target_audit_lossless.
        """
        # Create a changeset with a postcondition that collides with a built-in check name
        from dataclasses import replace
        changeset_with_collision = replace(
            self.changeset,
            postconditions=("visual_change_captured", "source_integrity", "custom_postcondition"),
        )
        
        # Create an adapter where the built-in checks would FAIL
        adapter = FakeVerificationAdapter(self.adapter.current)
        adapter.capture_result = {"resource_uri": "memory://capture/post", "diff": {"changed": False}}  # capture fails
        adapter.audit_result = {"ok": False, "target_format": "dwg", "target_version": "2018", "target_compatible": False, "dropped_on_save": ["LOSS"]}  # audit fails
        # Also make source integrity fail by changing the document path
        adapter.current = replace(adapter.current, document=replace(adapter.current.document, path="/fake/path.dwg"))
        
        root = self.root / "05_audits" / "postcondition-isolation"; root.mkdir()
        service = VerificationService(adapter=adapter, workspace=self.workspace, receipt_store=ReceiptStore(root), target_format="dwg", target_version="2018")
        receipt = asyncio.run(service.verify(changeset_with_collision, self.change))
        
        # The decision should be FAIL because built-in checks fail
        self.assertEqual(receipt.decision, "FAIL")
        
        # The built-in check keys should be present with their actual (failed) values
        self.assertFalse(receipt.postconditions.get("visual_change_captured", True))
        self.assertFalse(receipt.postconditions.get("target_audit_lossless", True))
        self.assertFalse(receipt.postconditions.get("source_integrity", True))
        
        # The custom postcondition should be in a separate namespace or not override
        # Since the built-in checks fail, the custom one should also be False
        # but it should not be able to force a PASS
        # Verify model postconditions are prefixed
        self.assertIn("model:custom_postcondition", receipt.postconditions)
        self.assertEqual(receipt.postconditions.get("model:custom_postcondition"), False)


if __name__ == "__main__": unittest.main()
