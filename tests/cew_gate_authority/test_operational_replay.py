from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from cew_gate_authority.authority import load_authority
from cew_gate_authority.operational import materialize_operational_authority
from cew_gate_authority.replay import run_model_generation_replay

A0 = Path("governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json")
EXPECTED_OUTPUT_SHA = "4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2"
EXPECTED_OUTPUT_SIZE = 1068121
EXPECTED_TIMESTAMP = "2026-08-26T09:54:00.472520+00:00"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OperationalReplayTests(unittest.TestCase):
    def test_materializes_only_frozen_operational_authority_and_verifies_all_identities(self):
        authority = load_authority(A0)
        with tempfile.TemporaryDirectory() as temp:
            materialized = materialize_operational_authority(Path("."), authority, Path(temp) / "operational")
            self.assertEqual(materialized.operational_commit, "d806dcca72779b5a186defe557a7a9b739575a90")
            self.assertEqual(materialized.builder_git_blob_sha, "4459fd0f519d8bb9425fa1490cc720a2edb0bd0a")
            self.assertEqual(len(materialized.input_paths), 6)
            self.assertEqual(
                {rel: sha256(path) for rel, path in materialized.input_paths},
                dict(authority.inputs),
            )
            self.assertEqual(materialized.registration_git_blob_sha, "fa28cf034a03d98aaa8e8ac1deb1549ddef6d64a")

    def test_replay_reproduces_historical_output_exactly(self):
        authority = load_authority(A0)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            materialized = materialize_operational_authority(Path("."), authority, root / "operational")
            output = root / authority.output.identity
            result = run_model_generation_replay(materialized, authority, output)
            self.assertTrue(result.passed, result.failure_codes)
            self.assertEqual(result.output_sha256, EXPECTED_OUTPUT_SHA)
            self.assertEqual(result.output_size_bytes, EXPECTED_OUTPUT_SIZE)
            self.assertEqual(result.generated_at, EXPECTED_TIMESTAMP)
            self.assertEqual(sha256(output), EXPECTED_OUTPUT_SHA)
            self.assertEqual(output.stat().st_size, EXPECTED_OUTPUT_SIZE)

    def test_candidate_equivalent_paths_cannot_substitute_for_operational_objects(self):
        authority = load_authority(A0)
        with tempfile.TemporaryDirectory() as temp:
            materialized = materialize_operational_authority(Path("."), authority, Path(temp) / "operational")
            materialized.builder_path.write_text("raise RuntimeError('candidate substitution')\n", encoding="utf-8")
            output = Path(temp) / authority.output.identity
            result = run_model_generation_replay(materialized, authority, output)
            self.assertFalse(result.passed)
            self.assertIn("BUILDER_IDENTITY_BLOB_MISMATCH", result.failure_codes)


if __name__ == "__main__":
    unittest.main()
