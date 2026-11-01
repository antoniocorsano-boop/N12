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
    from experiments.cew_col03d.historical_quality import audit_historical_semantics
except (ImportError, ModuleNotFoundError):
    parse_csv_member = None
    audit_historical_semantics = None


CSV_NAMES = (
    "ABACO_TOPOLOGICO_TAV5_v11.csv",
    "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
    "MATRICE_PILASTRI_27x5_v22.csv",
    "ABACO_TRAVI_TAV6_v23.csv",
    "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv",
)


class HistoricalSemanticQualityTests(unittest.TestCase):
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

    def _audit(self):
        self.assertIsNotNone(parse_csv_member, "COL-03D CSV parser missing")
        self.assertIsNotNone(audit_historical_semantics, "COL-03D historical quality auditor missing")
        parsed = [parse_csv_member(name, (self.root / name).read_bytes()) for name in CSV_NAMES]
        return audit_historical_semantics(parsed)

    def test_historical_states_are_preserved_not_promoted(self):
        audit = self._audit()
        self.assertEqual(
            audit["historical_state_counts"],
            {
                "ND": 135,
                "PREDOC_TOPOLOGICO": 57,
                "PROPOSTA_GEOMETRICA": 46,
                "RIF": 230,
                "VER": 794,
            },
        )
        self.assertFalse(audit["identity_promotion_authorized"])
        self.assertFalse(audit["structural_identity_authorized"])
        self.assertFalse(audit["section_assignment_authorized"])
        self.assertFalse(audit["vertical_chain_assignment_authorized"])

    def test_historical_non_demonstration_notes_become_machine_visible_blockers(self):
        audit = self._audit()
        self.assertEqual(audit["column_association_not_demonstrated_count"], 27)
        self.assertEqual(audit["beam_geometry_only_association_count"], 46)
        self.assertIn("COLUMN_ASSOCIATION_NOT_DEMONSTRATED", audit["blocking_findings"])
        self.assertIn("BEAM_ASSOCIATION_GEOMETRY_ONLY", audit["blocking_findings"])

    def test_recovered_row_cardinalities_are_reported_as_evidence_only(self):
        audit = self._audit()
        self.assertEqual(
            audit["row_counts"],
            {
                "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv": 27,
                "ABACO_TOPOLOGICO_TAV5_v11.csv": 57,
                "ABACO_TRAVI_TAV6_v23.csv": 46,
                "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv": 46,
                "MATRICE_PILASTRI_27x5_v22.csv": 135,
            },
        )
        self.assertEqual(audit["status"], "EVIDENCE_ONLY")


if __name__ == "__main__":
    unittest.main()
