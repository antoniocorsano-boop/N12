from __future__ import annotations

import unittest

from cew_gate_authority.candidate_reader import normalize_candidate_path
from cew_gate_authority.qualification import parse_csv_limited


class CandidatePathPropertyTests(unittest.TestCase):
    def test_deterministic_path_corpus_rejects_ambiguous_or_escaping_forms(self):
        bad = ["", "/absolute", "../escape", "a/../../escape", "a\\windows", "./relative", "a//double", "qualification/../escape"]
        for value in bad:
            with self.subTest(value=value):
                with self.assertRaises(ValueError): normalize_candidate_path(value)

    def test_normal_path_round_trips(self):
        values = ["qualification/cew-contract-01/n12/qualification.json", "qualification/cew-contract-01/n12/evidence/CASE_01_DOCUMENTED_PROPERTY.md"]
        self.assertEqual([normalize_candidate_path(value) for value in values], values)

    def test_csv_row_limit_is_enforced_before_semantic_evaluation(self):
        text = "test_id,status,evidence_id\n" + "\n".join("x,PASS,e" for _ in range(250001)) + "\n"
        with self.assertRaisesRegex(ValueError, "CANDIDATE_CSV_ROWS_EXCEEDED"):
            parse_csv_limited(text, 250000)


if __name__ == "__main__": unittest.main()
