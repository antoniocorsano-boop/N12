import unittest

from experiments.cew_cal01.external_chain_postprocess import build_external_chain_result


class ExternalChainPostprocessContractTests(unittest.TestCase):
    def test_postprocess_preserves_legacy_inventory_and_adds_chain_evidence(self):
        discovery = {
            "source": {"source_id": "TAV-02S", "sha256": "c" * 64},
            "discovery_digest": "sha256:legacy",
            "candidate_count": 2,
            "numeric_observation_count": 3,
            "candidates": [
                {
                    "observation_id": "a",
                    "search_band": "BOTTOM",
                    "bbox_normalized_px": [200.0, 720.0, 250.0, 744.0],
                }
            ],
            "rejected_observations": [
                {
                    "observation_id": "b",
                    "search_band": "BOTTOM",
                    "bbox_normalized_px": [360.0, 720.0, 410.0, 744.0],
                },
                {
                    "observation_id": "c",
                    "search_band": "TOP",
                    "bbox_normalized_px": [360.0, 40.0, 410.0, 64.0],
                },
            ],
            "bands": [
                {"side": "TOP", "bbox_px": [100, 0, 900, 100]},
                {"side": "RIGHT", "bbox_px": [900, 100, 1100, 700]},
                {"side": "BOTTOM", "bbox_px": [100, 700, 900, 820]},
                {"side": "LEFT", "bbox_px": [0, 100, 100, 700]},
            ],
            "plan_envelope": {"envelope_bbox_normalized_px": [100, 100, 900, 700]},
            "primary_anchor_count": 0,
            "authority": {
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "canonical_write_authorized": False,
                "m0g_authorized": False,
                "engineering_authority_effect": "NONE",
            },
        }
        line_segments_by_side = {
            "TOP": [],
            "RIGHT": [],
            "LEFT": [],
            "BOTTOM": [
                (120.0, 760.0, 880.0, 760.0),
                (150.0, 738.0, 150.0, 782.0),
                (300.0, 738.0, 300.0, 782.0),
                (470.0, 738.0, 470.0, 782.0),
                (650.0, 738.0, 650.0, 782.0),
                (850.0, 738.0, 850.0, 782.0),
            ],
        }

        result = build_external_chain_result(
            discovery=discovery,
            line_segments_by_side=line_segments_by_side,
        )

        self.assertEqual(result["source"]["source_id"], "TAV-02S")
        self.assertEqual(result["legacy_discovery_digest"], "sha256:legacy")
        self.assertEqual(result["legacy_candidate_count"], 2)
        self.assertEqual(result["legacy_numeric_observation_count"], 3)
        self.assertEqual(result["side_order"], ["TOP", "RIGHT", "BOTTOM", "LEFT"])
        self.assertEqual(result["external_chain_count"], 1)
        self.assertEqual(result["external_chain_member_count"], 2)
        bottom = next(row for row in result["sides"] if row["side"] == "BOTTOM")
        self.assertEqual(bottom["chains"][0]["member_observation_ids"], ["a", "b"])
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])
        self.assertFalse(result["eligible_for_metric_calibration"])

    def test_postprocess_is_deterministic_for_observation_input_order(self):
        base = {
            "source": {"source_id": "TAV-01S", "sha256": "a" * 64},
            "discovery_digest": "sha256:legacy",
            "candidate_count": 0,
            "numeric_observation_count": 2,
            "candidates": [],
            "rejected_observations": [
                {"observation_id": "z", "search_band": "BOTTOM", "bbox_normalized_px": [500.0, 720.0, 540.0, 744.0]},
                {"observation_id": "a", "search_band": "BOTTOM", "bbox_normalized_px": [200.0, 720.0, 240.0, 744.0]},
            ],
            "bands": [{"side": side, "bbox_px": [0, 0, 1, 1]} for side in ["TOP", "RIGHT", "BOTTOM", "LEFT"]],
            "plan_envelope": {"envelope_bbox_normalized_px": [100, 100, 900, 700]},
            "primary_anchor_count": 0,
            "authority": {"canonical_geometry_authorized": False, "canonical_write_authorized": False},
        }
        lines = {
            "TOP": [], "RIGHT": [], "LEFT": [],
            "BOTTOM": [
                (120.0, 760.0, 880.0, 760.0),
                (150.0, 738.0, 150.0, 782.0),
                (300.0, 738.0, 300.0, 782.0),
                (470.0, 738.0, 470.0, 782.0),
                (650.0, 738.0, 650.0, 782.0),
                (850.0, 738.0, 850.0, 782.0),
            ],
        }
        left = build_external_chain_result(discovery=base, line_segments_by_side=lines)
        reversed_discovery = dict(base)
        reversed_discovery["rejected_observations"] = list(reversed(base["rejected_observations"]))
        right = build_external_chain_result(discovery=reversed_discovery, line_segments_by_side=lines)
        self.assertEqual(left["external_chain_digest"], right["external_chain_digest"])
        self.assertEqual(left["sides"], right["sides"])


if __name__ == "__main__":
    unittest.main()
