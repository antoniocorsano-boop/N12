from pathlib import Path
import unittest


WORKFLOW = Path('.github/workflows/validate-cew-cal01-external-chain.yml')


class ExternalChainHumanReviewWorkflowContractTests(unittest.TestCase):
    def test_workflow_materializes_human_review_packets_from_exact_crops_and_human_evidence(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('python -m experiments.cew_cal01.external_chain_human_review', text)
        self.assertIn('CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T01_01_v1.json', text)
        self.assertIn('CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T01_02_v1.json', text)
        self.assertIn('CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T02_01_v1.json', text)
        self.assertIn('CEW_CAL01_PRIMARY_VISUAL_CLASSIFICATION_SG_T02_02_v1.json', text)
        for index in range(6):
            self.assertIn(
                f'--decision governance/cew-cal01/reviews/CEW_CAL01_EXTERNAL_CHAIN_HUMAN_T02_TOP_I{index}_v1.json',
                text,
            )
        for index in range(2):
            self.assertIn(
                f'--decision governance/cew-cal01/reviews/CEW_CAL01_EXTERNAL_CHAIN_HUMAN_T02_RIGHT_I{index}_v1.json',
                text,
            )
        self.assertIn("'governance/cew-cal01/reviews/CEW_CAL01_EXTERNAL_CHAIN_HUMAN_*_v1.json'", text)
        self.assertIn('--source-width-px 9933', text)
        self.assertIn('--source-width-px 7016', text)
        self.assertIn('external-chain-human-review-packet.json', text)
        self.assertIn('external-chain-human-review.html', text)
        self.assertIn("assert tav01_human['review_count'] == 15", text)
        self.assertIn("assert tav01_human['reused_human_receipt_count'] == 1", text)
        self.assertIn("assert tav01_human['direct_human_decision_count'] == 0", text)
        self.assertIn("assert tav01_human['validated_human_relation_count'] == 1", text)
        self.assertIn("assert tav01_human['pending_human_review_count'] == 14", text)
        self.assertIn("assert tav02_human['review_count'] == 19", text)
        self.assertIn("assert tav02_human['reused_human_receipt_count'] == 2", text)
        self.assertIn("assert tav02_human['direct_human_decision_count'] == 8", text)
        self.assertIn("assert tav02_human['validated_human_relation_count'] == 10", text)
        self.assertIn("assert tav02_human['pending_human_review_count'] == 9", text)
        self.assertIn("assert all(row['eligible_for_metric_calibration'] is False for row in human['reviews'])", text)
        self.assertIn("assert all(row['primary_anchor_authorized'] is False for row in human['reviews'])", text)
        self.assertIn("assert human['primary_anchor_count'] == 0", text)
        self.assertIn("assert human['eligible_for_metric_calibration'] is False", text)
        self.assertIn("assert human['authority']['canonical_geometry_authorized'] is False", text)
        self.assertIn("assert human['authority']['canonical_write_authorized'] is False", text)
        self.assertIn("assert packet_crops == manifest_crops", text)
        self.assertIn("assert tav02_states['TAV-02S:TOP:TOP:R1:I0'] == 'DIRECT_HUMAN_DECISION'", text)
        self.assertIn("assert tav02_states['TAV-02S:TOP:TOP:R1:I5'] == 'DIRECT_HUMAN_DECISION'", text)
        self.assertIn("assert tav02_states['TAV-02S:RIGHT:RIGHT:R1:I0'] == 'DIRECT_HUMAN_DECISION'", text)
        self.assertIn("assert tav02_states['TAV-02S:RIGHT:RIGHT:R1:I1'] == 'DIRECT_HUMAN_DECISION'", text)
        self.assertIn("assert tav02_states['TAV-02S:BOTTOM:BOTTOM:R1:I2'] == 'REUSED_HUMAN_RECEIPT'", text)
        self.assertIn("assert tav02_states['TAV-02S:BOTTOM:BOTTOM:R1:I3'] == 'REUSED_HUMAN_RECEIPT'", text)

    def test_workflow_materializes_source_local_metric_sufficiency_gate(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn("'experiments/cew_cal01/metric_sufficiency.py'", text)
        self.assertIn("'tests/cew_cal01/test_metric_sufficiency.py'", text)
        self.assertIn("'tests/cew_cal01/test_metric_sufficiency_gate.py'", text)
        self.assertGreaterEqual(text.count('python -m experiments.cew_cal01.metric_sufficiency'), 2)
        self.assertIn('metric-relation-network.json', text)
        self.assertIn('metric-sufficiency-gate.json', text)
        self.assertIn("assert tav01_metric_gate['gate_state'] == 'TARGETED_HUMAN_REVIEW'", text)
        self.assertIn("assert 1 <= len(tav01_metric_gate['targeted_human_review_ids']) <= 4", text)
        self.assertIn("assert tav02_metric_network['relation_count'] == 10", text)
        self.assertIn("assert tav02_metric_network['orientation_counts'] == {'HORIZONTAL': 8, 'VERTICAL': 2}", text)
        self.assertIn("assert 'TOP:R1' in tav02_metric_network['complete_chain_ids']", text)
        self.assertIn("assert tav02_metric_gate['relation_audit']['diagnostic_status'] == 'RELATION_NETWORK_DIAGNOSTIC_SUFFICIENT'", text)
        self.assertIn("assert tav02_metric_gate['gate_state'] == 'INSUFFICIENT'", text)
        self.assertIn("assert tav02_metric_gate['blockers'] == ['PRIMARY_ANCHOR_REQUIRED']", text)
        self.assertIn("assert tav02_metric_gate['next_action'] == 'PRIMARY_ANCHOR_DISCOVERY'", text)
        self.assertIn("assert metric_gate['authority']['canonical_geometry_authorized'] is False", text)
        self.assertIn("assert metric_gate['authority']['canonical_write_authorized'] is False", text)
        self.assertIn("assert metric_network['eligible_for_metric_calibration'] is False", text)


if __name__ == '__main__':
    unittest.main()
