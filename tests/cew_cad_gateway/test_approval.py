from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from cew_cad_gateway.approval import ApprovalError, ApprovalVerifier, sign_approval
from cew_cad_gateway.types import (
    CapabilityIdentity,
    Changeset,
    CreatePolyline,
    DocumentIdentity,
    EpistemicState,
)


class ApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        private_key = Ed25519PrivateKey.generate()
        self.private_path = root / "human-private.pem"
        self.public_path = root / "APPROVAL_PUBLIC_KEY.pem"
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
            changeset_id="CEW-CAD-CS-000001",
            intent="lab polyline",
            document=DocumentIdentity(path="02_working/lab.dwg", sha256="0" * 64, document_id=1, revision=7),
            capabilities=CapabilityIdentity(cad_build="2026.41", capabilities_sha256="1" * 64),
            evidence_refs=("E-001",), claim_refs=("C-001",), decision_refs=("D-001",),
            epistemic_states=(EpistemicState.MIS,),
            operations=(CreatePolyline(layer="CEW-LAB", points=((0.0, 0.0), (1.0, 0.0))),),
            preconditions=(), postconditions=(), expected_changed_entities=("NEW:Polyline",),
            forbidden_side_effects=(), unresolved=(), changeset_sha256="2" * 64,
        )

    def sign(self, **overrides):
        params = dict(
            changeset=self.changeset,
            private_key_path=self.private_path,
            approval_id="CEW-CAD-APP-000001",
            approved_by="human",
            approved_at="2026-10-22T05:20:00+02:00",
        )
        params.update(overrides)
        return sign_approval(**params)

    def verifier(self):
        return ApprovalVerifier(
            self.public_path,
            now=lambda: "2026-10-22T05:25:00+02:00",
            max_age_seconds=900,
        )

    def test_exact_signed_approval_verifies_and_can_be_consumed_once(self) -> None:
        receipt = self.sign()
        verifier = self.verifier()
        verifier.verify(receipt, self.changeset)
        verifier.consume(receipt, self.changeset)
        with self.assertRaises(ApprovalError):
            verifier.consume(receipt, self.changeset)

    def test_tampering_document_revision_hash_id_or_changeset_is_rejected(self) -> None:
        receipt = self.sign()
        variants = (
            replace(receipt, changeset_sha256="f" * 64),
            replace(receipt, document_sha256="e" * 64),
            replace(receipt, document_id=2),
            replace(receipt, base_revision=8),
            replace(receipt, changeset_id="CEW-CAD-CS-OTHER"),
            replace(receipt, signature="AAAA"),
        )
        for variant in variants:
            with self.subTest(variant=variant):
                with self.assertRaises(ApprovalError):
                    self.verifier().verify(variant, self.changeset)

    def test_changed_changeset_binding_is_rejected(self) -> None:
        receipt = self.sign()
        changed = replace(self.changeset, changeset_sha256="3" * 64)
        with self.assertRaises(ApprovalError):
            self.verifier().verify(receipt, changed)

    def test_expired_approval_is_rejected(self) -> None:
        receipt = self.sign(approved_at="2026-10-22T04:00:00+02:00")
        with self.assertRaises(ApprovalError):
            self.verifier().verify(receipt, self.changeset)

    def test_malformed_public_key_and_missing_signature_fail_closed(self) -> None:
        malformed = Path(self.tmp.name) / "bad.pem"
        malformed.write_text("not a public key", encoding="utf-8")
        receipt = self.sign()
        with self.assertRaises(ApprovalError):
            ApprovalVerifier(malformed, now=lambda: "2026-10-22T05:25:00+02:00").verify(receipt, self.changeset)
        with self.assertRaises(ValueError):
            replace(receipt, signature="")


if __name__ == "__main__":
    unittest.main()
