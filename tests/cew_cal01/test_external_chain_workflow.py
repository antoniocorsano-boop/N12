from pathlib import Path
import unittest


WORKFLOW = Path('.github/workflows/validate-cew-cal01-external-chain.yml')


class ExternalChainWorkflowContractTests(unittest.TestCase):
    def test_workflow_replays_frozen_structural_sources_and_uploads_separate_evidence(self):
        self.assertTrue(WORKFLOW.exists(), 'external chain workflow must exist')
        text = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('78c20a52db4f391ce0d13b9705b9f04737e218c9', text)
        self.assertIn('python -m experiments.cew_cal01.structural_grid_sources', text)
        self.assertIn('python -m experiments.cew_cal01.structural_grid_dimension', text)
        self.assertIn('python -m experiments.cew_cal01.external_chain_postprocess', text)
        self.assertIn('TAV-01S-primary-300dpi.png', text)
        self.assertIn('TAV-02S-primary-300dpi.png', text)
        self.assertIn('cew-cal01-external-dimension-chains', text)
        self.assertIn("assert payload['primary_anchor_count'] == 0", text)
        self.assertIn("assert payload['eligible_for_metric_calibration'] is False", text)
        self.assertIn("assert payload['authority']['canonical_geometry_authorized'] is False", text)
        self.assertIn("assert payload['authority']['canonical_write_authorized'] is False", text)


if __name__ == '__main__':
    unittest.main()
