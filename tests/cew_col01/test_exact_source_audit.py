from __future__ import annotations

import unittest

from experiments.cew_col01.exact_source_audit import evaluate_benchmark


def record(identifier: str, state: str = "P2_NUMBER_FOOTPRINT_NO_AXES") -> dict:
    return {
        "anchor_id": identifier,
        "graphical_state": state,
        "review_eligible": state != "NO_PLAUSIBLE_FOOTPRINT",
    }


class ExactSourceAuditContractTests(unittest.TestCase):
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
