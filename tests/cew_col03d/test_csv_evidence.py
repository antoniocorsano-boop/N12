from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from experiments.cew_col03d.member_verification import (
    HISTORICAL_TRANSPORT_ROOT,
    REQUIRED_MEMBER_CONTRACTS,
    reconstruct_required_member_directory,
)

try:
    from experiments.cew_col03d.csv_evidence import parse_csv_member
except (ImportError, ModuleNotFoundError):
    parse_csv_member = None


EXPECTED_ROWS = {
    "ABACO_TOPOLOGICO_TAV5_v11.csv": 57,
    "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv": 27,
    "MATRICE_PILASTRI_27x5_v22.csv": 135,
    "ABACO_TRAVI_TAV6_v23.csv": 46,
    "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv": 46,
}


class HistoricalCsvEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "members"
        reconstruct_required_member_directory(
            Path(HISTORICAL_TRANSPORT_ROOT), cls.root, REQUIRED_MEMBER_CONTRACTS
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_exact_recovered_csv_cardinalities_are_preserved(self):
        self.assertIsNotNone(parse_csv_member, "COL-03D CSV evidence parser missing")
        for name, expected_rows in EXPECTED_ROWS.items():
            parsed = parse_csv_member(name, (self.root / name).read_bytes())
            self.assertEqual(parsed["artifact_name"], name)
            self.assertEqual(parsed["delimiter"], ";")
            self.assertEqual(parsed["row_count"], expected_rows)
            self.assertEqual(len(parsed["records"]), expected_rows)
            self.assertTrue(parsed["headers"])
            self.assertEqual(parsed["authority"], "HISTORICAL_DERIVED_EVIDENCE")
            self.assertFalse(parsed["promotion_authorized"])
            self.assertTrue(all(row["source_row_number"] >= 2 for row in parsed["records"]))

    def test_parse_is_deterministic_for_exact_bytes(self):
        self.assertIsNotNone(parse_csv_member, "COL-03D CSV evidence parser missing")
        name = "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv"
        data = (self.root / name).read_bytes()
        self.assertEqual(parse_csv_member(name, data), parse_csv_member(name, data))

    def test_malformed_row_width_fails_closed(self):
        self.assertIsNotNone(parse_csv_member, "COL-03D CSV evidence parser missing")
        malformed = b"a;b\r\n1\r\n"
        with self.assertRaisesRegex(ValueError, "CSV_ROW_WIDTH_MISMATCH"):
            parse_csv_member("malformed.csv", malformed)

    def test_raw_headers_and_row_values_are_not_semantically_rewritten(self):
        self.assertIsNotNone(parse_csv_member, "COL-03D CSV evidence parser missing")
        name = "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv"
        parsed = parse_csv_member(name, (self.root / name).read_bytes())
        self.assertEqual(parsed["headers"][0], "id_predoc")
        self.assertEqual(parsed["headers"][-1], "nota")
        first = parsed["records"][0]["values"]
        self.assertEqual(first["id_predoc"], "N001")
        self.assertEqual(first["stato_associazione"], "VER")
        self.assertIn("associazione al singolo pilastro non ancora dimostrata", first["nota"])


if __name__ == "__main__":
    unittest.main()
