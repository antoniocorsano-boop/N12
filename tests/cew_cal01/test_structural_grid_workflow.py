from pathlib import Path
import unittest


class Cal01StructuralGridWorkflowContractTests(unittest.TestCase):
    def test_workflow_qualifies_frozen_structural_grid_primary_sources(self):
        workflow = Path(".github/workflows/validate-cew-cal01.yml").read_text(encoding="utf-8")
        self.assertIn("cal01-structural-grid-source-discovery:", workflow)
        self.assertIn("python -m experiments.cew_cal01.structural_grid_sources", workflow)
        self.assertIn("python -m experiments.cew_cal01.structural_grid_dimension", workflow)
        self.assertIn("TAV-01S", workflow)
        self.assertIn("TAV-02S", workflow)
        self.assertIn("abd6061c305f2e7222f04659f519d7ee73ed0759b815ac994ff66215f060fec8", workflow)
        self.assertIn("cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f", workflow)
        self.assertIn("primary_anchor_count", workflow)
        self.assertIn("cross_sheet_relation_count", workflow)
        self.assertIn("cew-cal01-structural-grid-primary-sources", workflow)


if __name__ == "__main__":
    unittest.main()
