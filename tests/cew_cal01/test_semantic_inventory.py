import unittest

from experiments.cew_cal01.semantic_inventory import build_semantic_inventory


class Cal01SemanticInventoryContractTests(unittest.TestCase):
    def test_inventory_classifies_roles_and_keeps_authority_closed(self):
        proposals = [
            {
                "proposal_id": "P1",
                "raw_ocr_text": "420",
                "ocr_rotation_degrees": 90,
                "bbox_px": [100.0, 160.0, 140.0, 220.0],
            },
            {
                "proposal_id": "P2",
                "raw_ocr_text": "40",
                "ocr_rotation_degrees": 0,
                "bbox_px": [200.0, 200.0, 240.0, 220.0],
            },
            {
                "proposal_id": "P3",
                "raw_ocr_text": "129",
                "ocr_rotation_degrees": 90,
                "bbox_px": [300.0, 160.0, 340.0, 220.0],
            },
        ]
        local_contexts = {
            "P1": {
                "local_readings": ["120", "120", "120", "420"],
                "line_segments": [
                    [120, 100, 120, 300],
                    [100, 100, 140, 100],
                    [100, 300, 140, 300],
                ],
                "nearby_closed_frame": False,
            },
            "P2": {
                "local_readings": ["40", "40", "40", "45"],
                "line_segments": [],
                "nearby_closed_frame": True,
            },
            "P3": {
                "local_readings": ["129", "120", "129"],
                "line_segments": [
                    [320, 100, 320, 300],
                    [300, 100, 340, 100],
                    [300, 300, 340, 300],
                ],
                "nearby_closed_frame": False,
            },
        }
        result = build_semantic_inventory(proposals, local_contexts)
        self.assertEqual(result["proposal_count"], 3)
        self.assertEqual(result["role_counts"]["LINEAR_DIMENSION"], 1)
        self.assertEqual(result["role_counts"]["SECTION_MEASURE"], 1)
        self.assertEqual(result["role_counts"]["UNRESOLVED"], 1)
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertFalse(result["authority"]["primary_anchor_authorized"])
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])
        self.assertFalse(result["authority"]["canonical_write_authorized"])
        self.assertFalse(result["authority"]["m0g_authorized"])
        self.assertTrue(result["semantic_inventory_digest"].startswith("sha256:"))

    def test_inventory_rejects_missing_local_context(self):
        proposals = [{
            "proposal_id": "P1",
            "raw_ocr_text": "120",
            "ocr_rotation_degrees": 90,
            "bbox_px": [100.0, 160.0, 140.0, 220.0],
        }]
        with self.assertRaisesRegex(ValueError, "CAL01_SEMANTIC_CONTEXT_MISSING"):
            build_semantic_inventory(proposals, {})

    def test_inventory_is_deterministic_for_same_inputs(self):
        proposals = [{
            "proposal_id": "P1",
            "raw_ocr_text": "40",
            "ocr_rotation_degrees": 0,
            "bbox_px": [200.0, 200.0, 240.0, 220.0],
        }]
        contexts = {
            "P1": {
                "local_readings": ["40", "40", "40"],
                "line_segments": [],
                "nearby_closed_frame": True,
            }
        }
        self.assertEqual(
            build_semantic_inventory(proposals, contexts),
            build_semantic_inventory(proposals, contexts),
        )


if __name__ == "__main__":
    unittest.main()
