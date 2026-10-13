from __future__ import annotations

import unittest

from cew_gate_authority.receipt import canonical_receipt_bytes, receipt_sha256
from cew_gate_authority.types import (
    AuthorityIdentity,
    CandidateIdentity,
    ControlPlaneIdentity,
    GateCoreIdentity,
    InvariantResult,
    OperationalIdentity,
    QualificationReceipt,
)

EXPECTED_INVARIANTS = tuple(f"I{i:02d}" for i in range(1, 18))


def make_receipt(*, invariant_overrides=None, qualified=True) -> QualificationReceipt:
    invariants = {key: InvariantResult.PASS for key in EXPECTED_INVARIANTS}
    if invariant_overrides:
        invariants.update(invariant_overrides)
    return QualificationReceipt(
        schema_id="CEW_QUALIFICATION_RECEIPT",
        schema_version=1,
        qualified_at="2026-10-13T00:00:00+00:00",
        control_plane=ControlPlaneIdentity(base_commit_sha="a" * 40),
        gate_core=GateCoreIdentity(repository="antoniocorsano-boop/N12", commit_sha="b" * 40, version="G0"),
        authority=AuthorityIdentity(authority_id="N12_CEW_CONTRACT_01_A0", authority_sha256="c" * 64),
        candidate=CandidateIdentity(
            base_repository="antoniocorsano-boop/N12",
            pr_number=148,
            head_repository="antoniocorsano-boop/N12",
            head_sha="d" * 40,
        ),
        operational_authority=OperationalIdentity(commit_sha="d806dcca72779b5a186defe557a7a9b739575a90"),
        qualification_bundle_sha256="e" * 64,
        replay={
            "output_identity": "N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json",
            "output_sha256": "4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2",
            "output_size_bytes": 1068121,
            "historical_generated_at": "2026-08-26T09:54:00.472520+00:00",
        },
        invariants=invariants,
        failure_codes=(),
        authority_boundary={
            "solver_authorized": False,
            "calculation_model_ready": False,
            "synthetic_solver_result": False,
            "solver_run": False,
            "result_entity_created": False,
        },
        cew_fem_01_required=True,
        qualified=qualified,
    )


class IdentityAndReceiptTests(unittest.TestCase):
    def test_candidate_identity_requires_pr_head_repository_and_exact_sha(self):
        identity = CandidateIdentity(
            base_repository="antoniocorsano-boop/N12",
            pr_number=148,
            head_repository="antoniocorsano-boop/N12",
            head_sha="1" * 40,
        )
        self.assertEqual(identity.pr_number, 148)
        self.assertEqual(identity.head_repository, "antoniocorsano-boop/N12")
        self.assertEqual(identity.head_sha, "1" * 40)
        with self.assertRaises(ValueError):
            CandidateIdentity(
                base_repository="antoniocorsano-boop/N12",
                pr_number=0,
                head_repository="antoniocorsano-boop/N12",
                head_sha="not-a-sha",
            )

    def test_receipt_requires_exact_i01_to_i17_set(self):
        receipt = make_receipt()
        self.assertEqual(tuple(sorted(receipt.invariants)), EXPECTED_INVARIANTS)
        with self.assertRaises(ValueError):
            make_receipt(invariant_overrides={"I18": InvariantResult.PASS})

    def test_qualified_true_is_rejected_when_any_applicable_invariant_fails(self):
        with self.assertRaises(ValueError):
            make_receipt(invariant_overrides={"I10": InvariantResult.FAIL}, qualified=True)

    def test_canonical_serialization_is_byte_stable_and_digest_includes_no_terminal_newline(self):
        first = make_receipt()
        second = make_receipt()
        first_bytes = canonical_receipt_bytes(first)
        second_bytes = canonical_receipt_bytes(second)
        self.assertEqual(first_bytes, second_bytes)
        self.assertFalse(first_bytes.endswith(b"\n"))
        self.assertEqual(len(receipt_sha256(first)), 64)


if __name__ == "__main__":
    unittest.main()
