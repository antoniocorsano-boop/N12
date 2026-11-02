from pathlib import Path
import unittest


TARGETED_WORKFLOW = Path('.github/workflows/validate-cew-cal01-targeted-intersource-review.yml')


class TargetedInterSourceReviewWorkflowContractTests(unittest.TestCase):
    def test_targeted_gate_materializes_bounded_source_only_professional_review(self):
        self.assertTrue(TARGETED_WORKFLOW.exists(), 'targeted-review workflow must exist')
        text = TARGETED_WORKFLOW.read_text(encoding='utf-8')
        required = (
            'name: CEW-CAL-01 Targeted Inter-Source Human Review',
            'artifact_id: 13168600387',
            '116b00d94bf1e2c427eb7b873d531b27adcf97d9a027dc47f41076764f553def',
            'ebac21fc2cc49bff75e0cc7656ee30d219d44f14',
            'Materialize targeted inter-source human review package',
            'python -m experiments.cew_cal01.intersource_human_review',
            '--batch-size 8',
            'targeted-intersource-human-review.json',
            'targeted-intersource-human-review.html',
            "assert review['schema'] == 'CEW_CAL01_INTERSOURCE_TARGETED_HUMAN_REVIEW_v1'",
            "assert review['source_candidate_count'] == 22",
            "assert review['target_lattice_node_count'] == 21",
            "assert review['review_item_count'] == 8",
            "assert review['selection_strategy'] == 'SOURCE_ONLY_FARTHEST_POINT_COVERAGE_V1'",
            "assert review['target_geometry_used_for_selection'] is False",
            "assert review['target_node_ranking_performed'] is False",
            "assert review['automatic_homology_proposed'] is False",
            "assert review['selected_occurrence_ids'] == [",
            "'COL-OCC-0013'",
            "'COL-OCC-0016'",
            "'COL-OCC-0005'",
            "'COL-OCC-0002'",
            "'COL-OCC-0022'",
            "'COL-OCC-0020'",
            "'COL-OCC-0001'",
            "'COL-OCC-0021'",
            "assert review['target_overview_asset']['normalization_transform'] == 'ROTATE_90_COUNTERCLOCKWISE'",
            "assert review['target_overview_asset']['sha256'].startswith('sha256:')",
            "assert all(row['source_context_asset']['sha256'].startswith('sha256:') for row in review['review_items'])",
            "assert governed['governed_correspondence_count'] == 0",
            "assert split['state'] == 'INSUFFICIENT_INTERSOURCE_CORRESPONDENCES'",
            "assert split['affine_fit_performed'] is False",
            "assert split['ready_for_affine_fit'] is False",
            "assert payload['authority']['structural_identity_authorized'] is False",
            "assert payload['authority']['canonical_geometry_authorized'] is False",
            "assert payload['authority']['canonical_write_authorized'] is False",
            "assert payload['authority']['m0g_authorized'] is False",
            "assert payload['authority']['engineering_authority_effect'] == 'NONE'",
        )
        for needle in required:
            self.assertIn(needle, text)

        self.assertNotIn('BUILD_INTERSOURCE_AFFINE_REGISTRATION', text)


if __name__ == '__main__':
    unittest.main()
