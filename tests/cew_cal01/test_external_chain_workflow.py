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
        self.assertIn('python -m experiments.cew_cal01.external_chain_refined_exact', text)
        self.assertIn('python -m experiments.cew_cal01.interval_text_review_exact', text)
        self.assertIn('python -m experiments.cew_cal01.interval_ocr_exact', text)
        self.assertIn('TAV-01S-primary-300dpi.png', text)
        self.assertIn('TAV-02S-primary-300dpi.png', text)
        self.assertIn('refined-external-dimension-chain.json', text)
        self.assertIn('interval-text-review-manifest.json', text)
        self.assertIn('interval-ocr-comparison.json', text)
        self.assertIn('cew-cal01-external-dimension-chains', text)
        self.assertIn("assert payload['primary_anchor_count'] == 0", text)
        self.assertIn("assert payload['eligible_for_metric_calibration'] is False", text)
        self.assertIn("assert payload['authority']['canonical_geometry_authorized'] is False", text)
        self.assertIn("assert payload['authority']['canonical_write_authorized'] is False", text)
        self.assertIn("assert tav02['refined_external_chain_count'] == 5", text)
        self.assertIn("assert tav02_side_counts == {'TOP': 1, 'RIGHT': 2, 'BOTTOM': 1, 'LEFT': 1}", text)
        self.assertIn("assert tav02_interval_counts == {'TOP': [6], 'RIGHT': [3, 2], 'BOTTOM': [4], 'LEFT': [4]}", text)
        self.assertIn("assert tav01_review['review_request_count'] == 15", text)
        self.assertIn("assert tav02_review['review_request_count'] == 19", text)
        self.assertIn("assert all(row['recognition_status'] == 'HANDWRITTEN_RECOGNIZER_REQUIRED'", text)
        self.assertIn("assert all(row['primary_anchor_authorized'] is False", text)
        self.assertIn("assert tav01_ocr['review_count'] == 15", text)
        self.assertIn("assert tav02_ocr['review_count'] == 19", text)
        self.assertIn("assert all(row['human_review_required'] is True for row in ocr['reviews'])", text)
        self.assertIn("assert all(row['primary_anchor_authorized'] is False for row in ocr['reviews'])", text)
        self.assertIn("assert all(row['eligible_for_metric_calibration'] is False for row in ocr['reviews'])", text)
        self.assertIn("assert ocr['primary_anchor_count'] == 0", text)
        self.assertIn("assert ocr['eligible_for_metric_calibration'] is False", text)
        self.assertIn("assert ocr['authority']['canonical_geometry_authorized'] is False", text)
        self.assertIn("assert ocr['authority']['canonical_write_authorized'] is False", text)
        self.assertIn("assert comparison_crops == manifest_crops", text)


if __name__ == '__main__':
    unittest.main()
