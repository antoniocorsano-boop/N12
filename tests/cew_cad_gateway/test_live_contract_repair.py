"""
GREEN tests for CEW-CAD-01 Live Contract Repair.

These tests verify that the three defects identified in the live pilot are FIXED:
1. Layer mutation contract - entity creation now uses typed OCS primitive with explicit layer
2. OCS settled-response contract - response normalization handles real OCS v2026.42 shape
3. Approval single-use - consumption is now durable across process boundaries via ReceiptStore
"""
from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from cew_cad_gateway.adapters.opencadstudio import OpenCADStudioAdapter, OpenCADStudioError, _normalize_ocs_mutation_response, _build_typed_polyline_request
from cew_cad_gateway.approval import ApprovalVerifier, ApprovalError, sign_approval
from cew_cad_gateway.canonical import sha256_file
from cew_cad_gateway.receipts import ReceiptStore
from cew_cad_gateway.types import CADStatus, CapabilityIdentity, CreatePolyline, DocumentIdentity, EpistemicState


# ============================================================================
# GREEN A — typed creation preserves CEW-LAB layer
# ============================================================================

class LayerContractGreenTests(unittest.TestCase):
    """Test that entity creation now materializes layer = CEW-LAB via typed primitive."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.exe = Path(self.tmp.name) / "OpenCADStudio.exe"
        self.exe.write_bytes(b"fake-ocs")

    def factory(self, client):
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def make_client(_executable: Path):
            yield client
        return make_client

    def test_typed_entity_creation_uses_entities_create_primitive(self):
        """
        GREEN: The adapter now uses typed OCS entity creation primitive (entities_create)
        with explicit layer="CEW-LAB", not a raw PLINE command.
        """
        class TypedClient:
            def __init__(self, exe_path):
                self.exe_path = exe_path
                self.calls = []
            async def list_tools(self):
                return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}
            async def call_tool(self, name, args):
                self.calls.append((name, args))
                if name == "ocs_sessions":
                    return {"result": [{"ok": True, "session_id": "s1", "document_id": 1, "revision": 7, "bridge": {"name": "OpenCADStudio", "version": "2026.42", "build_rev": "rev1", "tool_schema": "ts1"}, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 7}], "command": {"status": "idle"}}]}
                if name == "ocs_read" and args.get("op") == "capabilities":
                    return {
                        "ok": True, "api": "ocs-cad-automation", "version": 1,
                        "bridge": {"name": "OpenCADStudio", "version": "2026.42", "build_rev": "rev1", "tool_schema": "ts1"},
                        "concurrency": {"document_id": True, "request_id": True, "revision": True},
                        "editor": {"capture": True, "commands": True, "events": True, "files": True, "properties": True, "selection": True},
                        "geometry": {"query": True, "spatial_filters": True, "kernel_measurements": True, "interactive_commands": True},
                        "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
                        "records": {"collections": [], "filters": []},
                        "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
                    }
                if name == "ocs_read" and args.get("op") == "state":
                    return {"ok": True, "document_id": 1, "revision": 7, "documents": [{"id": 1, "path": str(self.exe_path), "revision": 7}], "command": {"status": "idle"}}
                if name == "ocs_execute":
                    request = args["request"]
                    if request["op"] == "entities_create":
                        # Verify the typed request structure
                        entities = request["entities"]
                        assert len(entities) == 1
                        entity = entities[0]
                        assert entity["type"] == "LwPolyline"
                        assert entity["layer"] == "CEW-LAB"
                        assert entity["closed"] == True
                        assert len(entity["vertices"]) == 4
                        # Return real OCS v2026.42 response
                        return {
                            "ok": True, "status": "completed", "request_id": request["request_id"],
                            "result": {"entities": [{"handle": "85", "type": "LwPolyline", "layer": "CEW-LAB"}]},
                            "changes": {"created": ["85"], "modified": [], "deleted": []},
                            "state": {"revision": 8, "geometry_revision": 26, "document_id": 1, "dirty": True}
                        }
                    if request["op"] == "run":
                        # Legacy - should not be used
                        return {"status": "completed", "revision": 8, "changed_entities": ["A1"]}
                raise AssertionError((name, args))

        client = TypedClient(self.exe)
        adapter = OpenCADStudioAdapter(self.exe, client_factory=self.factory(client))
        
        import hashlib
        expected_sha = hashlib.sha256(b"fake-ocs").hexdigest()
        expected = DocumentIdentity(path=str(self.exe), sha256=expected_sha, document_id=1, revision=7)
        
        operation = CreatePolyline(
            layer="CEW-LAB",
            points=((0.0, 0.0), (4000.0, 0.0), (4000.0, 3000.0), (0.0, 3000.0)),
            closed=True
        )
        
        result = asyncio.run(adapter.apply_operation(operation, request_id="req-1", expected=expected))
        
        # Verify the request used entities_create, not run
        execute_calls = [args for name, args in client.calls if name == "ocs_execute"]
        self.assertEqual(len(execute_calls), 1)
        request = execute_calls[0]["request"]
        self.assertEqual(request["op"], "entities_create")
        self.assertEqual(request["entities"][0]["layer"], "CEW-LAB")
        
        # Verify normalized response
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["revision"], 8)
        self.assertEqual(result["changed_entities"], ["85"])

    def test_build_typed_polyline_request_includes_layer(self):
        """Test that _build_typed_polyline_request creates proper typed request with layer."""
        operation = CreatePolyline(
            layer="CEW-LAB",
            points=((0.0, 0.0), (4000.0, 0.0), (4000.0, 3000.0), (0.0, 3000.0)),
            closed=True
        )
        
        request = _build_typed_polyline_request(operation)
        
        self.assertEqual(request["type"], "LwPolyline")
        self.assertEqual(request["layer"], "CEW-LAB")
        self.assertEqual(request["closed"], True)
        self.assertEqual(len(request["vertices"]), 4)
        self.assertEqual(request["vertices"][0], {"x": 0.0, "y": 0.0})
        self.assertEqual(request["vertices"][3], {"x": 0.0, "y": 3000.0})


# ============================================================================
# GREEN B — normalize real OCS settled response
# ============================================================================

class OCSResponseNormalizationGreenTests(unittest.TestCase):
    """Test that OCS response normalization handles real OCS v2026.42 response shape."""

    def test_normalize_real_ocs_v2026_42_settled_response(self):
        """
        GREEN: _normalize_ocs_mutation_response correctly extracts revision and 
        changed_entities from real OCS v2026.42 nested response shape.
        """
        real_ocs_response = {
            "ok": True,
            "status": "completed",
            "request_id": "cew-cad-abc123",
            "result": {"entities": [{"handle": "85", "type": "LwPolyline", "layer": "CEW-LAB"}]},
            "changes": {"created": ["85"], "modified": [], "deleted": []},
            "state": {"revision": 1, "geometry_revision": 26, "document_id": 1, "dirty": True}
        }
        
        normalized = _normalize_ocs_mutation_response(real_ocs_response)
        
        self.assertEqual(normalized["status"], "completed")
        self.assertEqual(normalized["revision"], 1)
        self.assertEqual(normalized["changed_entities"], ["85"])
        self.assertEqual(normalized["request_id"], "cew-cad-abc123")
        self.assertTrue(normalized["ok"])

    def test_normalize_fallback_to_result_entities(self):
        """Test fallback extraction from result.entities[*].handle when changes.created missing."""
        response = {
            "ok": True,
            "status": "completed",
            "request_id": "req-1",
            "result": {"entities": [{"handle": "H1", "type": "LwPolyline"}, {"handle": "H2", "type": "Line"}]},
            "state": {"revision": 5, "geometry_revision": 10, "document_id": 1, "dirty": True}
        }
        
        normalized = _normalize_ocs_mutation_response(response)
        
        self.assertEqual(normalized["status"], "completed")
        self.assertEqual(normalized["revision"], 5)
        self.assertEqual(normalized["changed_entities"], ["H1", "H2"])

    def test_normalize_legacy_top_level_fields(self):
        """Test backward compatibility with legacy response shape (top-level revision/changed_entities)."""
        legacy_response = {
            "status": "completed",
            "revision": 10,
            "changed_entities": ["LEGACY1", "LEGACY2"],
            "request_id": "legacy-req"
        }
        
        normalized = _normalize_ocs_mutation_response(legacy_response)
        
        self.assertEqual(normalized["status"], "completed")
        self.assertEqual(normalized["revision"], 10)
        self.assertEqual(normalized["changed_entities"], ["LEGACY1", "LEGACY2"])

    def test_normalize_fails_on_missing_status(self):
        """Test that normalization fails closed when status is missing."""
        response = {"revision": 1, "changed_entities": ["A1"]}
        with self.assertRaises(OpenCADStudioError) as cm:
            _normalize_ocs_mutation_response(response)
        self.assertEqual(str(cm.exception), "OCS_RESPONSE_STATUS_MISSING")

    def test_normalize_fails_on_missing_revision(self):
        """Test that normalization fails closed when revision is missing."""
        response = {"status": "completed", "changed_entities": ["A1"]}
        with self.assertRaises(OpenCADStudioError) as cm:
            _normalize_ocs_mutation_response(response)
        self.assertEqual(str(cm.exception), "OCS_RESPONSE_REVISION_MISSING")

    def test_normalize_fails_on_missing_changed_entities(self):
        """Test that normalization fails closed when changed_entities is missing."""
        response = {"status": "completed", "revision": 1}
        with self.assertRaises(OpenCADStudioError) as cm:
            _normalize_ocs_mutation_response(response)
        self.assertEqual(str(cm.exception), "OCS_RESPONSE_CHANGED_ENTITIES_MISSING")


# ============================================================================
# GREEN C — approval single-use across process/runtime boundary
# ============================================================================

class DurableApprovalGreenTests(unittest.TestCase):
    """Test that approval consumption is now durable across process boundaries."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        
        private_key = Ed25519PrivateKey.generate()
        self.private_path = self.root / "human-private.pem"
        self.public_path = self.root / "APPROVAL_PUBLIC_KEY.pem"
        self.private_path.write_bytes(private_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        ))
        self.public_path.write_bytes(private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ))
        
        from cew_cad_gateway.types import CapabilityIdentity, Changeset, CreatePolyline, DocumentIdentity
        
        self.changeset = Changeset(
            schema="cew.cad.changeset.v1",
            changeset_id="CEW-CAD-CS-000001",
            intent="lab polyline",
            session_id="session-1",
            document=DocumentIdentity(path="02_working/lab.dwg", sha256="0" * 64, document_id=1, revision=7),
            capabilities=CapabilityIdentity(cad_build="2026.41", capabilities_sha256="1" * 64),
            evidence_refs=("E-001",),
            claim_refs=("C-001",),
            decision_refs=("D-001",),
            epistemic_states=(EpistemicState.MIS,),
            operations=(CreatePolyline(layer="CEW-LAB", points=((0.0, 0.0), (1.0, 0.0))),),
            preconditions=(),
            postconditions=(),
            expected_changed_entities=("NEW:Polyline",),
            forbidden_side_effects=(),
            unresolved=(),
            changeset_sha256="2" * 64,
        )

    def test_approval_consumption_durable_across_instances_with_receipt_store(self):
        """
        GREEN: ApprovalVerifier with ReceiptStore now persists consumed approvals.
        New verifier instance (simulating new process/runtime) will reject already-consumed approval.
        """
        approval = sign_approval(
            changeset=self.changeset,
            private_key_path=self.private_path,
            approval_id="CEW-CAD-APP-000001",
            approved_by="human",
            approved_at="2026-10-22T05:20:00+02:00"
        )
        
        audit_root = self.root / "audits"
        audit_root.mkdir(parents=True, exist_ok=True)
        receipt_store = ReceiptStore(audit_root)
        
        # Process/Runtime A - first verifier instance with receipt_store
        verifier_a = ApprovalVerifier(
            self.public_path,
            now=lambda: "2026-10-22T05:25:00+02:00",
            max_age_seconds=900,
            receipt_store=receipt_store
        )
        
        # First consumption succeeds
        verifier_a.verify(approval, self.changeset)
        verifier_a.consume(approval, self.changeset)
        
        # Second consumption in same instance fails (correct)
        with self.assertRaises(ApprovalError) as cm:
            verifier_a.consume(approval, self.changeset)
        self.assertEqual(str(cm.exception), "APPROVAL_ALREADY_CONSUMED")
        
        # Process/Runtime B - NEW verifier instance with SAME receipt_store
        # This simulates a restart/new process with access to the same workspace
        verifier_b = ApprovalVerifier(
            self.public_path,
            now=lambda: "2026-10-22T05:25:00+02:00",
            max_age_seconds=900,
            receipt_store=receipt_store
        )
        
        # GREEN: This should now FAIL because the approval was persisted
        with self.assertRaises(ApprovalError) as cm:
            verifier_b.verify(approval, self.changeset)
            verifier_b.consume(approval, self.changeset)
        self.assertEqual(str(cm.exception), "APPROVAL_ALREADY_CONSUMED")

    def test_approval_without_receipt_store_still_works_in_memory(self):
        """
        GREEN: ApprovalVerifier without receipt_store still works (in-memory only),
        maintaining backward compatibility for tests that don't need durability.
        """
        approval = sign_approval(
            changeset=self.changeset,
            private_key_path=self.private_path,
            approval_id="CEW-CAD-APP-000002",
            approved_by="human",
            approved_at="2026-10-22T05:20:00+02:00"
        )
        
        # Verifier WITHOUT receipt_store (backward compatible)
        verifier = ApprovalVerifier(
            self.public_path,
            now=lambda: "2026-10-22T05:25:00+02:00",
            max_age_seconds=900
        )
        
        verifier.verify(approval, self.changeset)
        verifier.consume(approval, self.changeset)
        
        # Second consumption in same instance fails
        with self.assertRaises(ApprovalError):
            verifier.consume(approval, self.changeset)
        
        # New instance WITHOUT receipt_store allows re-consumption (in-memory only)
        # This is expected behavior when no receipt_store is provided
        verifier2 = ApprovalVerifier(
            self.public_path,
            now=lambda: "2026-10-22T05:25:00+02:00",
            max_age_seconds=900
        )
        verifier2.verify(approval, self.changeset)
        verifier2.consume(approval, self.changeset)  # This works because no persistence


if __name__ == "__main__":
    unittest.main()