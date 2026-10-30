from __future__ import annotations

import unittest
from types import SimpleNamespace

from experiments.cew_col01.exact_source_audit import (
    evaluate_benchmark,
    source_identity_metadata,
)


def record(identifier: str, state: str = "P2_NUMBER_FOOTPRINT_NO_AXES") -> dict:
    return {
        "anchor_id": identifier,
        "graphical_state": state,
        "review_eligible": state != "NO_PLAUSIBLE_FOOTPRINT",
    }


class ExactSourceAuditContractTests(unittest.TestCase):
    def test_source_identity_metadata_uses_canonical_contract_path(self):
        contract = SimpleNamespace(
            repository="antoniocorsano-boop/N12",
            commit="78c20a52db4f391ce0d13b9705b9f04737e218c9",
            path="archive/documentazione_originaria/tavola 5.pdf",
            git_blob_sha="ec32cd621877e9037cb26ebc083164140a8e3e68",
            sha256="2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
            page_index=0,
            source_role="PRIMARY_IMMUTABLE_QUALIFICATION_SOURCE",
        )
        materialized = SimpleNamespace(sha256=contract.sha256)
        binding = SimpleNamespace(raster_width_px=7016, raster_height_px=12530)
        metadata = source_identity_metadata(
            contract,
            materialized,
            binding,
            zone_set_digest="zone-digest",
        )
        self.assertEqual(metadata["path"], contract.path)
        self.assertEqual(metadata["repository"], contract.repository)
        self.assertEqual(metadata["commit"], contract.commit)
        self.assertEqual(metadata["git_blob_sha"], contract.git_blob_sha)
        self.assertEqual(metadata["sha256"], contract.sha256)
        self.assertEqual(metadata["page_index"], 0)
        self.assertEqual(metadata["raster_width_px"], 7016)
        self.assertEqual(metadata["raster_height_px"], 12530)
        self.assertEqual(metadata["zone_set_digest"], "zone-digest")

    def test_benchmark_reports_matches_misses_duplicates_without_creating_candidates(self):
        records = [record("1"), record("2"), record("2")]
        before = list(records)
        result = evaluate_benchmark(
            records,
            benchmark_ids=["1", "2", "3"],
            elongated_ids=["2"],
        )
        self.assertEqual(records, before)
        self.assertEqual(result["matched_ids"], ["1", "2"])
        self.assertEqual(result["unmatched_ids"], ["3"])
        self.assertEqual(result["duplicate_ids"], {"2": 2})
        self.assertAlmostEqual(result["coverage_fraction"], 2 / 3)
        self.assertEqual(result["h_col_01_status"], "REJECTED")
        self.assertEqual(result["elongated_witnesses"][0]["identifier"], "2")
        self.assertEqual(result["elongated_witnesses"][0]["observation_count"], 2)

    def test_number_without_plausible_footprint_does_not_count_as_support_match(self):
        result = evaluate_benchmark(
            [
                record("18", "NO_PLAUSIBLE_FOOTPRINT"),
                record("23", "P2_NUMBER_FOOTPRINT_NO_AXES"),
            ],
            benchmark_ids=["18", "23"],
            elongated_ids=["18", "23"],
        )
        self.assertEqual(result["matched_ids"], ["23"])
        self.assertEqual(result["unmatched_ids"], ["18"])
        self.assertAlmostEqual(result["coverage_fraction"], 0.5)
        by_id = {item["identifier"]: item for item in result["elongated_witnesses"]}
        self.assertEqual(by_id["18"]["observation_count"], 0)
        self.assertEqual(by_id["23"]["observation_count"], 1)

    def test_ninety_percent_identifier_coverage_supports_hypothesis_only(self):
        records = [record(str(value)) for value in range(1, 10)]
        result = evaluate_benchmark(
            records,
            benchmark_ids=[str(value) for value in range(1, 11)],
            elongated_ids=["3"],
        )
        self.assertEqual(result["h_col_01_status"], "SUPPORTED")
        self.assertAlmostEqual(result["coverage_fraction"], 0.9)
        self.assertFalse(result["engineering_fact_authorized"])

    def test_empty_benchmark_is_unverified(self):
        result = evaluate_benchmark([], benchmark_ids=[], elongated_ids=[])
        self.assertEqual(result["h_col_01_status"], "UNVERIFIED")
        self.assertIsNone(result["coverage_fraction"])
        self.assertEqual(result["matched_ids"], [])
        self.assertEqual(result["unmatched_ids"], [])

    def test_elongated_witness_preserves_graphical_states(self):
        result = evaluate_benchmark(
            [
                record("18", "P2_NUMBER_FOOTPRINT_NO_AXES"),
                record("23", "P1_NUMBER_FOOTPRINT_AXES"),
            ],
            benchmark_ids=["18", "23", "30"],
            elongated_ids=["18", "23", "30"],
        )
        by_id = {item["identifier"]: item for item in result["elongated_witnesses"]}
        self.assertEqual(by_id["18"]["graphical_states"], ["P2_NUMBER_FOOTPRINT_NO_AXES"])
        self.assertEqual(by_id["23"]["graphical_states"], ["P1_NUMBER_FOOTPRINT_AXES"])
        self.assertEqual(by_id["30"]["observation_count"], 0)


if __name__ == "__main__":
    unittest.main()
