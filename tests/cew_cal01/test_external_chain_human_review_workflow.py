from pathlib import Path
import unittest


WORKFLOW = Path('.github/workflows/validate-cew-cal01-external-chain.yml')


class ExternalChainHumanReviewWorkflowContractTests(unittest.TestCase):
    def test_workflow_materializes_human_review_packets_from_exact_crops_and_existing_receipts(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('python -m experiments.cew_cal01.external_chain_human_review', text)
        self.assertIn('CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T01_01_v1.json', text)
        self.assertIn('CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T01_02_v1.json', text)
        self.assertIn('CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T02_01_v1.json', text)
        self.assertIn('CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T02_02_v1.json', text)
        self.assertIn('--source-width-px 9933', text)
        self.assertIn('--source-width-px 7016', text)
        self.assertIn('external-chain-human-review-packet.json', text)
        self.assertIn('external-chain-human-review.html', text)
        self.assertIn("assert tav01_human['review_count'] == 15", text)
        self.assertIn("assert tav01_human['reused_human_receipt_count'] == 1", text)
        self.assertIn("assert tav01_human['pending_human_review_count'] == 14", text)
        self.assertIn("assert tav02_human['review_count'] == 19", text)
        self.assertIn("assert tav02_human['reused_human_receipt_count'] == 2", text)
        self.assertIn("assert tav02_human['pending_human_review_count'] == 17", text)
        self.assertIn("assert all(row['eligible_for_metric_calibration'] is False for row in human['reviews'])", text)
        self.assertIn("assert all(row['primary_anchor_authorized'] is False for row in human['reviews'])", text)
        self.assertIn("assert human['primary_anchor_count'] == 0", text)
        self.assertIn("assert human['eligible_for_metric_calibration'] is False", text)
        self.assertIn("assert human['authority']['canonical_geometry_authorized'] is False", text)
        self.assertIn("assert human['authority']['canonical_write_authorized'] is False", text)
        self.assertIn("assert packet_crops == manifest_crops", text)


if __name__ == '__main__':
    unittest.main()
