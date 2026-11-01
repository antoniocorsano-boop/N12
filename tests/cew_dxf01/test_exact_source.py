from copy import deepcopy
import tempfile
import unittest
from pathlib import Path

from experiments.cew_col03d.member_verification import HISTORICAL_TRANSPORT_ROOT

try:
    from experiments.cew_dxf01.exact_source import (
        build_exact_source_artifacts,
        write_exact_source_artifacts,
    )
    from experiments.cew_dxf01.validate_artifact import validate_payloads
except (ImportError, ModuleNotFoundError):
    build_exact_source_artifacts = None
    write_exact_source_artifacts = None
    validate_payloads = None


ROOT = Path(__file__).resolve().parents[2]
TRANSPORT = ROOT / HISTORICAL_TRANSPORT_ROOT
EXPECTED_FILES = {
    "dxf-observations.json",
    "dxf-observation-receipt.json",
    "dxf-read-query-closure.json",
}


class Dxf01ExactSourceContractTests(unittest.TestCase):
    def test_exact_source_builder_is_deterministic_and_authority_closed(self):
        self.assertIsNotNone(
            build_exact_source_artifacts,
            "CEW-DXF-01 Task 3 RED: exact-source builder is not implemented",
        )
        artifacts_a = build_exact_source_artifacts(TRANSPORT)
        artifacts_b = build_exact_source_artifacts(TRANSPORT)
        self.assertEqual(artifacts_a, artifacts_b)
        self.assertEqual(set(artifacts_a), EXPECTED_FILES)

        receipt = artifacts_a["dxf-observation-receipt.json"]
        closure = artifacts_a["dxf-read-query-closure.json"]
        self.assertEqual(receipt["source_count"], 3)
        self.assertEqual(receipt["toolchain"]["ezdxf_version"], "1.4.5")
        self.assertEqual(receipt["authority"]["authority_effect"], "NONE")
        self.assertFalse(receipt["authority"]["primary_source_identity_bridge"])
        self.assertFalse(receipt["authority"]["structural_identity_authorized"])
        self.assertFalse(receipt["authority"]["canonical_write_authorized"])
        self.assertTrue(closure["exact_source_replay_complete"])
        self.assertEqual(closure["next_action"], "PORT_ENGINEERING_GRAMMAR_BOUNDARY")

    def test_writer_emits_only_governed_json_surface(self):
        self.assertIsNotNone(write_exact_source_artifacts)
        artifacts = build_exact_source_artifacts(TRANSPORT)
        with tempfile.TemporaryDirectory() as tmp:
            written = write_exact_source_artifacts(Path(tmp), artifacts)
            self.assertEqual({path.name for path in written}, EXPECTED_FILES)
            self.assertEqual({path.name for path in Path(tmp).iterdir()}, EXPECTED_FILES)

    def test_historical_receipt_cannot_promote_primary_identity_authority(self):
        self.assertIsNotNone(validate_payloads)
        artifacts = build_exact_source_artifacts(TRANSPORT)
        drifted = deepcopy(artifacts)
        drifted["dxf-observation-receipt.json"]["authority"]["primary_source_identity_bridge"] = True
        with self.assertRaisesRegex(ValueError, "AUTHORITY_DRIFT"):
            validate_payloads(drifted)


if __name__ == "__main__":
    unittest.main()
