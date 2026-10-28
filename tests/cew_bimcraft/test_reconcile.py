from __future__ import annotations

from pathlib import Path
import unittest

from cew_bimcraft.command_plan import load_benchmark_fixture
from cew_bimcraft.reconcile import reconcile_fixture


FIXTURE_PATH = Path(
    "governance/cew-bimcraft-01/fixtures/STAGE_A_STRUCTURAL_FIXTURE_v1.json"
)
CATEGORY = {
    "structural_column": "structuralcolumn",
    "beam": "beam",
    "footing": "footing",
    "floor": "floor",
}


def expected_observations():
    fixture = load_benchmark_fixture(FIXTURE_PATH)
    return [
        {
            "object_id": obj.object_id,
            "category": CATEGORY[obj.command],
            "params": dict(obj.params),
            "provenance": dict(obj.provenance),
        }
        for obj in fixture.objects
    ]


class BIMCraftReadBackTests(unittest.TestCase):
    def test_exact_readback_passes(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        result = reconcile_fixture(fixture, expected_observations())
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.differences, ())
        self.assertEqual(result.expected_count, 4)
        self.assertEqual(result.observed_count, 4)

    def test_missing_object_is_rework(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        observations = expected_observations()[:-1]
        result = reconcile_fixture(fixture, observations)
        self.assertEqual(result.status, "REWORK")
        self.assertTrue(any(d.code == "MISSING_OBJECT" for d in result.differences))

    def test_extra_object_is_rework(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        observations = expected_observations()
        observations.append(
            {
                "object_id": "UNEXPECTED-001",
                "category": "beam",
                "params": {},
                "provenance": {},
            }
        )
        result = reconcile_fixture(fixture, observations)
        self.assertEqual(result.status, "REWORK")
        self.assertTrue(any(d.code == "EXTRA_OBJECT" for d in result.differences))

    def test_category_and_geometry_mismatch_are_explicit(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        observations = expected_observations()
        observations[1]["category"] = "floor"
        observations[1]["params"]["points"] = [[0, 0], [4900, 0]]
        result = reconcile_fixture(fixture, observations)
        codes = {d.code for d in result.differences}
        self.assertEqual(result.status, "REWORK")
        self.assertIn("CATEGORY_MISMATCH", codes)
        self.assertIn("PARAM_MISMATCH", codes)

    def test_provenance_loss_is_explicit(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        observations = expected_observations()
        observations[0]["provenance"].pop("CEW_EVIDENCE_ID")
        result = reconcile_fixture(fixture, observations)
        self.assertEqual(result.status, "REWORK")
        self.assertTrue(any(d.code == "PROVENANCE_MISMATCH" for d in result.differences))


if __name__ == "__main__":
    unittest.main()
