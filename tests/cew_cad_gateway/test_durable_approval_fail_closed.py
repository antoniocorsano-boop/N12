from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cew_cad_gateway.approval import ApprovalError, ApprovalVerifier, sign_approval
from cew_cad_gateway.receipts import ReceiptStore, ReceiptStoreError
from cew_cad_gateway.types import CapabilityIdentity, Changeset, CreatePolyline, DocumentIdentity, EpistemicState


class FailingReceiptStore(ReceiptStore):
    def write(self, kind: str, value: object):
        if kind == "consumed_approval":
            raise ReceiptStoreError("SIMULATED_PERSISTENCE_FAILURE")
        return super().write(kind, value)


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
        self.assertEqual(stored.path.name, "consumed_approval-5dc3641194a160aec4f3790205305973874000340859e50fb256c5bb25f23004.json")


if __name__ == "__main__":
    unittest.main()
