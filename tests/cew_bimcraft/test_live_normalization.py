from __future__ import annotations

from pathlib import Path
import unittest

from cew_bimcraft.command_plan import load_benchmark_fixture
from cew_bimcraft.reconcile import normalize_bimcraft_queries, reconcile_fixture


FIXTURE_PATH = Path(
    "governance/cew-bimcraft-01/fixtures/STAGE_A_STRUCTURAL_FIXTURE_v1.json"
)
SRC = "155988ef53273829f9ac98181095bedf5a5320d4bac207e63e040a3441ebe6e7"


def prov(object_id: str):
    return {
        "CEW_AUTHORITY": "BENCHMARK_ONLY",
        "CEW_EPISTEMIC_STATE": "RIF",
        "CEW_EVIDENCE_ID": "FIXTURE:SYNTHETIC",
        "CEW_OBJECT_ID": object_id,
        "CEW_REVISION": "stage-a-v1",
        "CEW_SOURCE_SHA256": SRC,
    }


def live_queries():
    return {
        "level": {
            "elements": [
                {"guid": "g-l1", "name": "BENCH-L1", "elevation": 6000.0},
                {"guid": "g-l2", "name": "BENCH-L2", "elevation": 9000.0},
            ]
        },
        "structuralcolumn": {
            "elements": [{
                "category": "structuralcolumn", "id": 100004, "at": [0.0, 0.0],
                "type": "CEW-COL-400x400", "level": "g-l1", "top_level": "g-l2",
                "params": prov("SYN-COL-001"),
            }]
        },
        "beam": {
            "elements": [{
                "category": "beam", "id": 100005, "start": [0.0, 0.0], "end": [5000.0, 0.0],
                "type": "CEW-BEAM-300x600", "level": "g-l2", "justify": "top",
                "params": prov("SYN-BEAM-001"),
            }]
        },
        "footing": {
            "elements": [{
                "category": "footing", "id": 100006, "at": [0.0, 0.0],
                "type": "CEW-FOOT-1200x1200", "level": "g-l1", "height": 500.0,
                "base_offset": -500.0, "params": prov("SYN-FOOT-001"),
            }]
        },
        "floor": {
            "elements": [{
                "category": "floor", "id": 100007,
                "boundary": [[0.0, 0.0], [5000.0, 0.0], [5000.0, 4000.0], [0.0, 4000.0]],
                "level": "g-l2", "structural": True, "params": prov("SYN-SLAB-001"),
            }]
        },
    }


class BIMCraftLiveNormalizationTests(unittest.TestCase):
    def test_observed_bimcraft_shape_normalizes_to_fixture_semantics(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        observations = normalize_bimcraft_queries(fixture, live_queries())
        result = reconcile_fixture(fixture, observations)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.differences, ())

    def test_unknown_level_guid_stays_visible_as_mismatch(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        queries = live_queries()
        queries["beam"]["elements"][0]["level"] = "unknown-guid"
        observations = normalize_bimcraft_queries(fixture, queries)
        result = reconcile_fixture(fixture, observations)
        self.assertEqual(result.status, "REWORK")
        self.assertTrue(any(d.code == "PARAM_MISMATCH" for d in result.differences))

    def test_missing_provenance_identity_is_not_silently_dropped(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        queries = live_queries()
        queries["floor"]["elements"][0]["params"].pop("CEW_OBJECT_ID")
        observations = normalize_bimcraft_queries(fixture, queries)
        result = reconcile_fixture(fixture, observations)
        self.assertEqual(result.status, "REWORK")
        codes = {d.code for d in result.differences}
        self.assertTrue("MISSING_OBJECT" in codes or "INVALID_OBSERVATION" in codes)


if __name__ == "__main__":
    unittest.main()
