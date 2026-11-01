import unittest

from experiments.cew_cal01.tight_exact_source import build_tight_replay_manifest


SOURCE = {
    "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    "page_index": 0,
}


class Cal01TightExactSourceContractTests(unittest.TestCase):
    def test_manifest_counts_confirmed_clusters_and_keeps_authority_closed(self):
        rows = [
            {
                "cluster_index": 0,
                "target_bbox_px": [10.0, 20.0, 30.0, 50.0],
                "ocr_rotation_degrees": 270,
                "pass_count": 9,
                "observation_count": 5,
                "consensus": {
                    "confirmed": True,
                    "text": "120",
                    "family_count": 4,
                    "runner_up_family_count": 1,
                },
            },
            {
                "cluster_index": 1,
                "target_bbox_px": [100.0, 120.0, 130.0, 150.0],
                "ocr_rotation_degrees": 0,
                "pass_count": 9,
                "observation_count": 3,
                "consensus": {
                    "confirmed": False,
                    "text": None,
                    "family_count": 2,
                    "runner_up_family_count": 2,
                },
            },
        ]
        manifest = build_tight_replay_manifest(source=SOURCE, rows=rows)
        self.assertEqual(manifest["cluster_count"], 2)
        self.assertEqual(manifest["tight_consensus_confirmed_count"], 1)
        self.assertEqual(manifest["confirmed_text_counts"], {"120": 1})
        self.assertEqual(manifest["primary_anchor_count"], 0)
        self.assertFalse(manifest["historical_comparator_loaded"])
        self.assertFalse(manifest["historical_affine_loaded"])
        self.assertFalse(manifest["tav02s_evidence_loaded"])
        self.assertFalse(manifest["authority"]["canonical_geometry_authorized"])
        self.assertFalse(manifest["authority"]["canonical_write_authorized"])
        self.assertEqual(manifest["authority"]["engineering_authority_effect"], "NONE")

    def test_manifest_is_deterministic_for_same_rows_regardless_of_input_order(self):
        a = {
            "cluster_index": 2,
            "target_bbox_px": [20.0, 20.0, 30.0, 40.0],
            "ocr_rotation_degrees": 90,
            "pass_count": 9,
            "observation_count": 4,
            "consensus": {"confirmed": True, "text": "470", "family_count": 3, "runner_up_family_count": 0},
        }
        b = {
            "cluster_index": 1,
            "target_bbox_px": [10.0, 10.0, 20.0, 30.0],
            "ocr_rotation_degrees": 270,
            "pass_count": 9,
            "observation_count": 2,
            "consensus": {"confirmed": False, "text": None, "family_count": 1, "runner_up_family_count": 1},
        }
        first = build_tight_replay_manifest(source=SOURCE, rows=[a, b])
        second = build_tight_replay_manifest(source=SOURCE, rows=[b, a])
        self.assertEqual(first["tight_replay_digest"], second["tight_replay_digest"])
        self.assertEqual([row["cluster_index"] for row in first["rows"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
