from pathlib import Path
import unittest


PRIMARY_WORKFLOW = Path('.github/workflows/validate-cew-cal01.yml')
EXTERNAL_WORKFLOW = Path('.github/workflows/validate-cew-cal01-external-chain.yml')


class AnchorConnectivityWorkflowContractTests(unittest.TestCase):
    def test_primary_metric_gate_tracks_anchor_connectivity_inputs_on_exact_head(self):
        self.assertTrue(PRIMARY_WORKFLOW.exists(), 'primary metric workflow must exist')
        text = PRIMARY_WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('ref: ${{ github.event.pull_request.head.sha || github.sha }}', text)
        self.assertIn("'experiments/cew_cal01/intersource_correspondence.py'", text)
        self.assertIn("'experiments/cew_cal01/intersource_governance.py'", text)
        self.assertIn("'experiments/cew_cal01/intersource_split.py'", text)
        self.assertIn("'tests/cew_cal01/test_anchor_connectivity_workflow.py'", text)

    def test_external_gate_replays_canonical_tav5_bridge_and_stops_fail_closed(self):
        self.assertTrue(EXTERNAL_WORKFLOW.exists(), 'external-chain workflow must exist')
        text = EXTERNAL_WORKFLOW.read_text(encoding='utf-8')
        required = (
            'ref: ${{ github.event.pull_request.head.sha || github.sha }}',
            'python -m experiments.cew_col02.exact_source_audit',
            'python -m experiments.cew_col03a.exact_source',
            'python -m cew_spiral.exact_source_structural_candidate_bridge',
            'discover_correspondence_candidates',
            'govern_correspondences',
            'freeze_registration_split',
            "assert bridge['qualification']['occurrence_count'] == 22",
            "assert bridge['qualification']['structural_candidate_count'] == 22",
            "assert candidates['source_candidate_count'] == 22",
            "assert candidates['classification_counts'] == {'AMBIGUOUS': 0, 'HOMOLOGY_PROPOSAL': 0, 'UNMATCHED': 22}",
            "assert governed['governed_correspondence_count'] == 0",
            "assert governed['readiness_state'] == 'INSUFFICIENT_INTERSOURCE_CORRESPONDENCES'",
            "assert governed['next_action'] == 'TARGETED_INTERSOURCE_HUMAN_REVIEW'",
            "assert split['state'] == 'INSUFFICIENT_INTERSOURCE_CORRESPONDENCES'",
            "assert split['next_action'] == 'TARGETED_INTERSOURCE_HUMAN_REVIEW'",
            "assert split['affine_fit_performed'] is False",
            "assert split['ready_for_affine_fit'] is False",
            "assert lattice['lattice_node_count'] == 21",
            "assert lattice['lattice_digest'].startswith('sha256:')",
            "assert payload['authority']['structural_identity_authorized'] is False",
            "assert payload['authority']['canonical_geometry_authorized'] is False",
            "assert payload['authority']['canonical_write_authorized'] is False",
            "assert payload['authority']['m0g_authorized'] is False",
            "assert payload['authority']['engineering_authority_effect'] == 'NONE'",
        )
        for needle in required:
            self.assertIn(needle, text)

        self.assertIn("assert candidates['historical_comparator_loaded'] is False", text)
        self.assertIn("assert candidates['historical_affine_loaded'] is False", text)
        self.assertIn("assert split['historical_m0g_loaded'] is False", text)
        self.assertNotIn('BUILD_INTERSOURCE_AFFINE_REGISTRATION', text)


if __name__ == '__main__':
    unittest.main()
