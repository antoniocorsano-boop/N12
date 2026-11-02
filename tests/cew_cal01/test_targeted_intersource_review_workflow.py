from pathlib import Path
import unittest


EXTERNAL_WORKFLOW = Path('.github/workflows/validate-cew-cal01-external-chain.yml')


class TargetedInterSourceReviewWorkflowContractTests(unittest.TestCase):
    def test_external_chain_materializes_bounded_source_only_professional_review(self):
        self.assertTrue(EXTERNAL_WORKFLOW.exists(), 'external-chain workflow must exist')
        text = EXTERNAL_WORKFLOW.read_text(encoding='utf-8')
        required = (
            'Materialize targeted inter-source human review package',
            'python -m experiments.cew_cal01.intersource_human_review',
            '--batch-size 8',
            "targeted-intersource-human-review.json",
            "targeted-intersource-human-review.html",
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
        )
        for needle in required:
            self.assertIn(needle, text)

        self.assertNotIn('BUILD_INTERSOURCE_AFFINE_REGISTRATION', text)


if __name__ == '__main__':
    unittest.main()
