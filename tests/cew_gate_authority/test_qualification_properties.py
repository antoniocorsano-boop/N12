from __future__ import annotations

import unittest

from cew_gate_authority.qualification import parse_csv_limited


class QualificationResourceProperties(unittest.TestCase):
    def test_csv_row_limit_is_enforced_before_semantic_evaluation(self):
        text = "test_id,status,evidence_id\n" + "\n".join("x,PASS,e" for _ in range(250001)) + "\n"
        with self.assertRaisesRegex(ValueError, "CANDIDATE_CSV_ROWS_EXCEEDED"):
            parse_csv_limited(text, 250000)


if __name__ == "__main__": unittest.main()
