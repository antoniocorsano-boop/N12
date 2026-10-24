from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cew_cad_gateway.artifacts import ArtifactRepository
from cew_cad_gateway.changesets import ChangesetService, ProposalRequest
from cew_cad_gateway.cli import build_parser, run_approve
from cew_cad_gateway.policy import GatewayPolicy
from cew_cad_gateway.types import CADStatus, CapabilityIdentity, CreatePolyline, DocumentIdentity, EpistemicState, InspectionReceipt, PathClass
from cew_cad_gateway.workspace import Workspace


class CLIBoundaryTests(unittest.TestCase):
    def test_serve_parser_requires_executable_hash_and_has_no_private_key_argument(self) -> None:
        parser = build_parser()
        serve = parser.parse_args([
            "serve",
            "--workspace-root", "C:/lab",
            "--policy", "policy.json",
            "--ocs-executable", "OpenCADStudio.exe",
            "--ocs-sha256", "0" * 64,
            "--approval-public-key", "public.pem",
            "--target-version", "2018",
        ])
        self.assertEqual(serve.command, "serve")
        self.assertEqual(serve.approval_public_key, "public.pem")
        self.assertEqual(serve.ocs_sha256, "0" * 64)
        self.assertFalse(hasattr(serve, "private_key"))
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "serve",
                "--workspace-root", "C:/lab",
                "--policy", "policy.json",
                "--ocs-executable", "OpenCADStudio.exe",
                "--ocs-sha256", "0" * 64,
                "--approval-public-key", "public.pem",
                "--target-version", "2018",
                "--private-key", "secret.pem",
            ])

    def test_approve_command_signs_stored_changeset_outside_mcp_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "CivilExisting"; root.mkdir()
            zones = {"SOURCE":"00_sources","BASELINE":"01_baseline","WORKING":"02_working","EVIDENCE":"03_evidence","CHANGESETS":"04_changesets","AUDITS":"05_audits","VERIFIED":"06_verified","ISSUED":"07_issued"}
            for zone in zones.values(): (root / zone).mkdir()
            policy = GatewayPolicy(zones=zones, mutable_path_classes=("WORKING",), max_primary_operations=1, allow_overwrite=False, allowed_mutating_operations=("create_polyline","undo_own_change"), allowed_property_paths=(), required_capabilities=("query","audit","capture","save_verified"))
            workspace = Workspace(root, policy)
            artifacts = ArtifactRepository(workspace)
            inspection = InspectionReceipt(
                schema="cew.cad.inspection.v1",
                status=CADStatus(
                    session_id="session-1",
                    document=DocumentIdentity(path=str(root / "02_working" / "lab.dwg"), sha256="0"*64, document_id=1, revision=7),
                    capabilities=CapabilityIdentity(cad_build="fake", capabilities_sha256="1"*64),
                    path_class=PathClass.WORKING,
                ),
                audit_sha256="2"*64,
                observed_at="2026-10-22T06:00:00+02:00",
            )
            service = ChangesetService(policy, known_evidence={"E-001"}, known_claims={"C-001"}, known_decisions={"D-001"})
            changeset = service.propose(
                ProposalRequest(
                    changeset_id="CS-1", intent="lab", operations=(CreatePolyline(layer="CEW-LAB", points=((0.0,0.0),(1.0,0.0))),),
                    evidence_refs=("E-001",), claim_refs=("C-001",), decision_refs=("D-001",),
                    coordinate_states=(EpistemicState.MIS,EpistemicState.MIS), epistemic_states=(EpistemicState.MIS,),
                    preconditions=(), postconditions=(), expected_changed_entities=("NEW:Polyline",), forbidden_side_effects=(), unresolved=(),
                    influential_unresolved=False, target_unique=True, output_path=None,
                ),
                inspection,
            )
            artifacts.store_changeset(changeset)
            private = Ed25519PrivateKey.generate()
            private_path = Path(tmp) / "private.pem"
            private_path.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            approval_id = run_approve(
                workspace_root=root,
                policy=policy,
                changeset_id="CS-1",
                private_key=private_path,
                approval_id="APP-1",
                approved_by="human",
                approved_at="2026-10-22T06:05:00+02:00",
                expected_changeset_sha256=changeset.changeset_sha256,
            )
            self.assertEqual(approval_id, "APP-1")
            stored = artifacts.load_approval("APP-1")
            self.assertEqual(stored.changeset_id, "CS-1")
            self.assertTrue(stored.signature)

    def test_approve_requires_changeset_sha256_confirmation(self) -> None:
        """
        The approve command must require an explicit --changeset-sha256 argument
        that matches the stored changeset's digest. This prevents a model from
        tricking a human into signing a different changeset than intended.
        """
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "approve",
                "--workspace-root", "C:/lab",
                "--policy", "policy.json",
                "--changeset-id", "CS-1",
                "--private-key", "private.pem",
                "--approval-id", "APP-1",
                "--approved-by", "human",
            ])

    def test_approve_rejects_wrong_changeset_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "CivilExisting"; root.mkdir()
            zones = {"SOURCE":"00_sources","BASELINE":"01_baseline","WORKING":"02_working","EVIDENCE":"03_evidence","CHANGESETS":"04_changesets","AUDITS":"05_audits","VERIFIED":"06_verified","ISSUED":"07_issued"}
            for zone in zones.values(): (root / zone).mkdir()
            policy = GatewayPolicy(zones=zones, mutable_path_classes=("WORKING",), max_primary_operations=1, allow_overwrite=False, allowed_mutating_operations=("create_polyline","undo_own_change"), allowed_property_paths=(), required_capabilities=("query","audit","capture","save_verified"))
            workspace = Workspace(root, policy)
            artifacts = ArtifactRepository(workspace)
            inspection = InspectionReceipt(
                schema="cew.cad.inspection.v1",
                status=CADStatus(
                    session_id="session-1",
                    document=DocumentIdentity(path=str(root / "02_working" / "lab.dwg"), sha256="0"*64, document_id=1, revision=7),
                    capabilities=CapabilityIdentity(cad_build="fake", capabilities_sha256="1"*64),
                    path_class=PathClass.WORKING,
                ),
                audit_sha256="2"*64,
                observed_at="2026-10-22T06:00:00+02:00",
            )
            service = ChangesetService(policy, known_evidence={"E-001"}, known_claims={"C-001"}, known_decisions={"D-001"})
            changeset = service.propose(
                ProposalRequest(
                    changeset_id="CS-1", intent="lab", operations=(CreatePolyline(layer="CEW-LAB", points=((0.0,0.0),(1.0,0.0))),),
                    evidence_refs=("E-001",), claim_refs=("C-001",), decision_refs=("D-001",),
                    coordinate_states=(EpistemicState.MIS,EpistemicState.MIS), epistemic_states=(EpistemicState.MIS,),
                    preconditions=(), postconditions=(), expected_changed_entities=("NEW:Polyline",), forbidden_side_effects=(), unresolved=(),
                    influential_unresolved=False, target_unique=True, output_path=None,
                ),
                inspection,
            )
            artifacts.store_changeset(changeset)
            private = Ed25519PrivateKey.generate()
            private_path = Path(tmp) / "private.pem"
            private_path.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            
            # Wrong digest should fail
            from cew_cad_gateway.cli import run_approve
            with self.assertRaises(ValueError) as cm:
                run_approve(
                    workspace_root=root,
                    policy=policy,
                    changeset_id="CS-1",
                    private_key=private_path,
                    approval_id="APP-1",
                    approved_by="human",
                    approved_at="2026-10-22T06:05:00+02:00",
                    expected_changeset_sha256="f" * 64,  # Wrong digest
                )
            self.assertEqual(str(cm.exception), "CHANGESET_DIGEST_CONFIRMATION_MISMATCH")
            
            # Correct digest should succeed
            approval_id = run_approve(
                workspace_root=root,
                policy=policy,
                changeset_id="CS-1",
                private_key=private_path,
                approval_id="APP-1",
                approved_by="human",
                approved_at="2026-10-22T06:05:00+02:00",
                expected_changeset_sha256=changeset.changeset_sha256,
            )
            self.assertEqual(approval_id, "APP-1")

    def test_approve_displays_changeset_summary_before_signing(self) -> None:
        """
        The approve command should display the Changeset summary (ID, SHA256, intent, operation)
        before signing so the human can verify.
        """
        # This test verifies the CLI prints the summary. We check the output is captured.
        import io
        import sys
        from contextlib import redirect_stdout
        
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "CivilExisting"; root.mkdir()
            zones = {"SOURCE":"00_sources","BASELINE":"01_baseline","WORKING":"02_working","EVIDENCE":"03_evidence","CHANGESETS":"04_changesets","AUDITS":"05_audits","VERIFIED":"06_verified","ISSUED":"07_issued"}
            for zone in zones.values(): (root / zone).mkdir()
            policy = GatewayPolicy(zones=zones, mutable_path_classes=("WORKING",), max_primary_operations=1, allow_overwrite=False, allowed_mutating_operations=("create_polyline","undo_own_change"), allowed_property_paths=(), required_capabilities=("query","audit","capture","save_verified"))
            workspace = Workspace(root, policy)
            artifacts = ArtifactRepository(workspace)
            inspection = InspectionReceipt(
                schema="cew.cad.inspection.v1",
                status=CADStatus(
                    session_id="session-1",
                    document=DocumentIdentity(path=str(root / "02_working" / "lab.dwg"), sha256="0"*64, document_id=1, revision=7),
                    capabilities=CapabilityIdentity(cad_build="fake", capabilities_sha256="1"*64),
                    path_class=PathClass.WORKING,
                ),
                audit_sha256="2"*64,
                observed_at="2026-10-22T06:00:00+02:00",
            )
            service = ChangesetService(policy, known_evidence={"E-001"}, known_claims={"C-001"}, known_decisions={"D-001"})
            changeset = service.propose(
                ProposalRequest(
                    changeset_id="CS-DISPLAY", intent="test display", operations=(CreatePolyline(layer="CEW-LAB", points=((0.0,0.0),(1.0,0.0))),),
                    evidence_refs=("E-001",), claim_refs=("C-001",), decision_refs=("D-001",),
                    coordinate_states=(EpistemicState.MIS,EpistemicState.MIS), epistemic_states=(EpistemicState.MIS,),
                    preconditions=(), postconditions=(), expected_changed_entities=("NEW:Polyline",), forbidden_side_effects=(), unresolved=(),
                    influential_unresolved=False, target_unique=True, output_path=None,
                ),
                inspection,
            )
            artifacts.store_changeset(changeset)
            private = Ed25519PrivateKey.generate()
            private_path = Path(tmp) / "private.pem"
            private_path.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            
            from cew_cad_gateway.cli import run_approve
            f = io.StringIO()
            with redirect_stdout(f):
                run_approve(
                    workspace_root=root,
                    policy=policy,
                    changeset_id="CS-DISPLAY",
                    private_key=private_path,
                    approval_id="APP-DISPLAY",
                    approved_by="human",
                    approved_at="2026-10-22T06:05:00+02:00",
                    expected_changeset_sha256=changeset.changeset_sha256,
                )
            output = f.getvalue()
            self.assertIn("CS-DISPLAY", output)
            self.assertIn(changeset.changeset_sha256[:16], output)
            self.assertIn("test display", output)


if __name__ == "__main__":
    unittest.main()
