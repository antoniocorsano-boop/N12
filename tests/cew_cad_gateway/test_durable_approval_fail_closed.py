from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cew_cad_gateway.approval import ApprovalError, ApprovalVerifier, sign_approval
from cew_cad_gateway.cli import build_live_runtime
from cew_cad_gateway.receipts import ReceiptStore, ReceiptStoreError
from cew_cad_gateway.types import CapabilityIdentity, Changeset, CreatePolyline, DocumentIdentity, EpistemicState


class FailingReceiptStore(ReceiptStore):
    def write(self, kind: str, value: object):
        if kind == "consumed_approval":
            raise ReceiptStoreError("SIMULATED_PERSISTENCE_FAILURE")
        return super().write(kind, value)

    def claim_once(self, kind: str, key: str, value: object):
        if kind == "consumed_approval":
            raise ReceiptStoreError("SIMULATED_PERSISTENCE_FAILURE")
        return super().claim_once(kind, key, value)


class DurableApprovalFailClosedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        private_key = Ed25519PrivateKey.generate()
        self.private_path = self.root / "human-private.pem"
        self.public_path = self.root / "APPROVAL_PUBLIC_KEY.pem"
        self.private_path.write_bytes(
            private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        self.public_path.write_bytes(
            private_key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

        self.changeset = Changeset(
            schema="cew.cad.changeset.v1",
            changeset_id="CEW-CAD-CS-P1-FAIL-CLOSED",
            intent="lab polyline",
            session_id="session-1",
            document=DocumentIdentity(
                path="02_working/lab.dwg",
                sha256="0" * 64,
                document_id=1,
                revision=7,
            ),
            capabilities=CapabilityIdentity(
                cad_build="2026.42",
                capabilities_sha256="1" * 64,
            ),
            evidence_refs=("E-001",),
            claim_refs=("C-001",),
            decision_refs=("D-001",),
            epistemic_states=(EpistemicState.MIS,),
            operations=(
                CreatePolyline(
                    layer="CEW-LAB",
                    points=((0.0, 0.0), (1.0, 0.0)),
                ),
            ),
            preconditions=(),
            postconditions=(),
            expected_changed_entities=("NEW:Polyline",),
            forbidden_side_effects=(),
            unresolved=(),
            changeset_sha256="2" * 64,
        )
        self.approval = sign_approval(
            changeset=self.changeset,
            private_key_path=self.private_path,
            approval_id="CEW-CAD-APP-P1-FAIL-CLOSED",
            approved_by="human",
            approved_at="2026-10-24T20:00:00+02:00",
        )

    def test_consumption_rejects_when_durable_receipt_cannot_be_written(self) -> None:
        audit_root = self.root / "audits"
        audit_root.mkdir()
        verifier = ApprovalVerifier(
            self.public_path,
            now=lambda: "2026-10-24T20:05:00+02:00",
            max_age_seconds=900,
            receipt_store=FailingReceiptStore(audit_root),
        )

        with self.assertRaises(ApprovalError) as cm:
            verifier.consume(self.approval, self.changeset)

        self.assertEqual(str(cm.exception), "APPROVAL_CONSUMPTION_PERSISTENCE_FAILED")

    def test_receipt_store_claim_once_is_deterministic_and_exclusive(self) -> None:
        audit_root = self.root / "atomic-claims"
        audit_root.mkdir()
        store = ReceiptStore(audit_root)

        self.assertTrue(
            hasattr(store, "claim_once"),
            "ReceiptStore must provide an atomic claim_once primitive",
        )

        first = {
            "approval_id": "CEW-CAD-APP-ATOMIC-1",
            "consumed_at": "2026-10-24T20:05:00+02:00",
        }
        second = {
            "approval_id": "CEW-CAD-APP-ATOMIC-1",
            "consumed_at": "2026-10-24T20:05:01+02:00",
        }

        stored = store.claim_once(
            "consumed_approval",
            "CEW-CAD-APP-ATOMIC-1",
            first,
        )
        with self.assertRaises(ReceiptStoreError) as cm:
            store.claim_once(
                "consumed_approval",
                "CEW-CAD-APP-ATOMIC-1",
                second,
            )

        self.assertEqual(str(cm.exception), "RECEIPT_ALREADY_CLAIMED")
        self.assertEqual(stored.path.name, "consumed_approval-74b173dc7da8b628c3b7fa6819c643ac28c1a9fe3bcd22c1a74962a6cbae1b3a.json")

    def test_live_runtime_wires_shared_receipt_store_into_approval_verifier(self) -> None:
        """The live serve path must use durable approval consumption, not the in-memory fallback."""
        policy = Mock(required_capabilities=("query",))
        workspace = Mock()
        receipt_store = Mock(spec=ReceiptStore)
        runtime = Mock()

        with (
            patch("cew_cad_gateway.cli.GatewayPolicy.load", return_value=policy),
            patch("cew_cad_gateway.cli.Workspace", return_value=workspace),
            patch("cew_cad_gateway.cli.OpenCADStudioAdapter", return_value=Mock()),
            patch("cew_cad_gateway.cli.ReceiptStore", return_value=receipt_store),
            patch("cew_cad_gateway.cli.InspectionService", return_value=Mock()),
            patch("cew_cad_gateway.cli.ChangesetService", return_value=Mock()),
            patch("cew_cad_gateway.cli.ApprovalVerifier", return_value=Mock()) as verifier_cls,
            patch("cew_cad_gateway.cli.ExecutionService", return_value=Mock()),
            patch("cew_cad_gateway.cli.VerificationService", return_value=Mock()),
            patch("cew_cad_gateway.cli.ArtifactRepository", return_value=Mock()),
            patch("cew_cad_gateway.cli.GatewayRuntimeImpl", return_value=runtime),
        ):
            workspace.zone_path.return_value = self.root
            result = build_live_runtime(
                workspace_root=self.root,
                policy_path=self.root / "policy.json",
                ocs_executable=self.root / "OpenCADStudio.exe",
                ocs_sha256="0" * 64,
                approval_public_key=self.public_path,
                evidence_refs=set(),
                claim_refs=set(),
                decision_refs=set(),
                target_format="dwg",
                target_version="2018",
            )

        self.assertIs(result, runtime)
        verifier_cls.assert_called_once_with(
            self.public_path,
            now=unittest.mock.ANY,
            max_age_seconds=900,
            receipt_store=receipt_store,
        )

    def test_claim_once_fsyncs_parent_directory_before_success(self) -> None:
        """A durable claim requires both file data and its directory entry to reach stable storage."""
        audit_root = self.root / "durable-directory"
        audit_root.mkdir()
        store = ReceiptStore(audit_root)

        real_open = os.open
        real_fsync = os.fsync
        opened_targets: list[object] = []
        fsynced_fds: list[int] = []

        def recording_open(path, flags, mode=0o777):
            opened_targets.append(path)
            return real_open(path, flags, mode)

        def recording_fsync(fd: int) -> None:
            fsynced_fds.append(fd)
            real_fsync(fd)

        with (
            patch("cew_cad_gateway.receipts.os.open", side_effect=recording_open),
            patch("cew_cad_gateway.receipts.os.fsync", side_effect=recording_fsync),
        ):
            store.claim_once(
                "consumed_approval",
                "CEW-CAD-APP-DIRSYNC-1",
                {"approval_id": "CEW-CAD-APP-DIRSYNC-1", "consumed_at": "2026-10-24T20:10:00+02:00"},
            )

        normalized_targets = {Path(target).resolve() for target in opened_targets if isinstance(target, (str, os.PathLike))}
        self.assertIn(store.root, normalized_targets, "claim_once must open the receipt directory for fsync")
        self.assertGreaterEqual(len(fsynced_fds), 2, "claim_once must fsync both the claim file and its parent directory")

    def test_windows_directory_flush_requests_generic_write_access(self) -> None:
        """FlushFileBuffers requires a handle opened with GENERIC_WRITE on Windows."""
        audit_root = self.root / "windows-directory-flush"
        audit_root.mkdir()
        store = ReceiptStore(audit_root)

        kernel32 = Mock()
        kernel32.CreateFileW = Mock(return_value=123)
        kernel32.FlushFileBuffers = Mock(return_value=1)
        kernel32.CloseHandle = Mock(return_value=1)

        with (
            patch("cew_cad_gateway.receipts.os.name", "nt"),
            patch("cew_cad_gateway.receipts.ctypes.WinDLL", return_value=kernel32, create=True),
        ):
            store._fsync_root_directory()

        desired_access = kernel32.CreateFileW.call_args.args[1]
        generic_write = 0x40000000
        self.assertEqual(
            desired_access & generic_write,
            generic_write,
            "Windows directory handle used with FlushFileBuffers must include GENERIC_WRITE",
        )
        kernel32.FlushFileBuffers.assert_called_once_with(123)
        kernel32.CloseHandle.assert_called_once_with(123)


if __name__ == "__main__":
    unittest.main()
