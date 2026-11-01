import unittest

from experiments.cew_cal01.semantic_replay import refine_numeric_proposal


class Cal01SemanticReplayContractTests(unittest.TestCase):
    def test_dominant_local_consensus_and_dimension_ticks_confirm_linear_dimension(self):
        proposal = {
            "raw_ocr_text": "420",
            "ocr_rotation_degrees": 90,
            "bbox_px": [100.0, 160.0, 140.0, 220.0],
            "proposal_id": "P1",
        }
        result = refine_numeric_proposal(
            proposal,
            local_readings=["120", "120", "120", "420"],
            line_segments=[
                [120, 100, 120, 300],
                [100, 100, 140, 100],
                [100, 300, 140, 300],
            ],
            nearby_closed_frame=False,
        )
        self.assertEqual(result["proposal_id"], "P1")
        self.assertEqual(result["consensus"]["text"], "120")
        self.assertTrue(result["consensus"]["confirmed"])
        self.assertEqual(result["role"], "LINEAR_DIMENSION")
        self.assertEqual(result["documented_text"], "120")
        self.assertFalse(result["primary_anchor_authorized"])
        self.assertFalse(result["canonical_geometry_authorized"])
        self.assertEqual(result["engineering_authority_effect"], "NONE")

    def test_dimension_section_conflict_fails_closed(self):
        proposal = {
            "raw_ocr_text": "120",
            "ocr_rotation_degrees": 90,
            "bbox_px": [100.0, 160.0, 140.0, 220.0],
            "proposal_id": "P2",
        }
        result = refine_numeric_proposal(
            proposal,
            local_readings=["120", "120", "120"],
            line_segments=[
                [120, 100, 120, 300],
                [100, 100, 140, 100],
                [100, 300, 140, 300],
            ],
            nearby_closed_frame=True,
        )
        self.assertEqual(result["role"], "UNRESOLVED")
        self.assertEqual(result["reason"], "DIMENSION_SECTION_ROLE_CONFLICT")
        self.assertFalse(result["primary_anchor_authorized"])

    def test_low_consensus_stays_unresolved_even_with_dimension_like_geometry(self):
        proposal = {
            "raw_ocr_text": "420",
            "ocr_rotation_degrees": 90,
            "bbox_px": [100.0, 160.0, 140.0, 220.0],
            "proposal_id": "P3",
        }
        result = refine_numeric_proposal(
            proposal,
            local_readings=["120", "420", "129"],
            line_segments=[
                [120, 100, 120, 300],
                [100, 100, 140, 100],
                [100, 300, 140, 300],
            ],
            nearby_closed_frame=False,
        )
        self.assertEqual(result["role"], "UNRESOLVED")
        self.assertEqual(result["reason"], "OCR_CONSENSUS_INSUFFICIENT")
        self.assertFalse(result["primary_anchor_authorized"])

    def test_closed_frame_without_dimension_ticks_is_section_measure(self):
        proposal = {
            "raw_ocr_text": "40",
            "ocr_rotation_degrees": 0,
            "bbox_px": [200.0, 200.0, 240.0, 220.0],
            "proposal_id": "P4",
        }
        result = refine_numeric_proposal(
            proposal,
            local_readings=["40", "40", "40", "45"],
            line_segments=[],
            nearby_closed_frame=True,
        )
        self.assertEqual(result["role"], "SECTION_MEASURE")
        self.assertEqual(result["documented_text"], "40")
        self.assertFalse(result["primary_anchor_authorized"])


if __name__ == "__main__":
    unittest.main()
