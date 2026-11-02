import unittest

from experiments.cew_cal01.external_chain_refinement import build_refined_external_chains


PLAN = [3845.0, 992.0, 11094.0, 6357.0]


def obs(observation_id, side, cx, cy):
    return {
        "observation_id": observation_id,
        "search_band": side,
        "bbox_normalized_px": [cx - 20.0, cy - 12.0, cx + 20.0, cy + 12.0],
    }


class ExternalChainRefinementContractTests(unittest.TestCase):
    def test_fragmented_top_carrier_uses_crossing_tick_strength_and_drops_text_strokes(self):
        axis = [
            (4208.0, 555.0, 7510.0, 555.0),
            (7480.0, 558.0, 10887.0, 558.0),
        ]
        ticks = [
            (4233.0, 547.0, 4233.0, 591.0),
            (5346.0, 530.0, 5346.0, 595.0),
            (5946.0, 523.0, 5946.0, 564.0),  # text-like weak stroke
            (6543.0, 532.0, 6543.0, 585.0),
            (7064.0, 522.0, 7064.0, 564.0),  # text-like weak stroke
            (7518.0, 534.0, 7518.0, 596.0),
            (8020.0, 523.0, 8020.0, 569.0),  # text-like weak stroke
            (8494.0, 528.0, 8494.0, 593.0),
            (9744.0, 512.0, 9744.0, 587.0),
            (10857.0, 510.0, 10857.0, 586.0),
        ]
        result = build_refined_external_chains(
            side="TOP",
            axis_segments=axis,
            tick_segments=ticks,
            observations=[obs("top-token", "TOP", 9090.0, 568.0)],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 1)
        self.assertEqual(
            result["chains"][0]["tick_positions_px"],
            [4233.0, 5346.0, 6543.0, 7518.0, 8494.0, 9744.0, 10857.0],
        )
        self.assertEqual(len(result["chains"][0]["intervals"]), 6)

    def test_bottom_rejects_long_structural_crossing_as_tick(self):
        axis = [(4213.0, 6517.0, 9031.0, 6517.0)]
        ticks = [
            (4231.0, 6498.0, 4231.0, 6563.0),
            (5349.0, 6506.0, 5349.0, 6568.0),
            (6309.0, 6496.0, 6309.0, 6552.0),
            (7807.0, 6491.0, 7807.0, 6550.0),
            (8551.0, 6468.0, 8551.0, 6612.0),  # structural crossing, too long
            (8977.0, 6494.0, 8977.0, 6545.0),
        ]
        result = build_refined_external_chains(
            side="BOTTOM",
            axis_segments=axis,
            tick_segments=ticks,
            observations=[obs("bottom-token", "BOTTOM", 7000.0, 6505.0)],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chains"][0]["tick_positions_px"], [4231.0, 5349.0, 6309.0, 7807.0, 8977.0])
        self.assertEqual(len(result["chains"][0]["intervals"]), 4)

    def test_left_chain_accepts_five_morphological_ticks_after_longitudinal_recovery(self):
        axis = [
            (3943.0, 822.0, 3943.0, 4635.0),
            (3941.0, 4550.0, 3941.0, 5144.0),
        ]
        ticks = [
            (3934.0, 865.0, 3980.0, 865.0),
            (3924.0, 2187.0, 3971.0, 2187.0),
            (3914.0, 3493.0, 3966.0, 3493.0),
            (3913.0, 4304.0, 3968.0, 4304.0),
            (3913.0, 5119.0, 3975.0, 5119.0),
        ]
        result = build_refined_external_chains(
            side="LEFT",
            axis_segments=axis,
            tick_segments=ticks,
            observations=[obs("left-token", "LEFT", 3988.0, 1610.0)],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 1)
        self.assertEqual(result["chains"][0]["tick_positions_px"], [865.0, 2187.0, 3493.0, 4304.0, 5119.0])
        self.assertEqual(len(result["chains"][0]["intervals"]), 4)

    def test_right_recovers_weak_endpoint_tick_but_rejects_inside_unsupported_carrier(self):
        axis = [
            (11146.0, 3769.0, 11146.0, 6247.0),
            (11061.0, 1832.0, 11061.0, 4516.0),
        ]
        ticks = [
            (11120.0, 3805.0, 11181.0, 3805.0),
            (11117.0, 4291.0, 11188.0, 4291.0),
            (11125.0, 5107.0, 11195.0, 5107.0),
            (11128.0, 6218.0, 11147.0, 6218.0),  # weak but near carrier endpoint
            (11022.0, 1874.0, 11101.0, 1874.0),
        ]
        result = build_refined_external_chains(
            side="RIGHT",
            axis_segments=axis,
            tick_segments=ticks,
            observations=[
                obs("right-good", "RIGHT", 11124.0, 4700.0),
                obs("right-local", "RIGHT", 11052.0, 1850.0),
            ],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 1)
        self.assertEqual(result["chains"][0]["tick_positions_px"], [3805.0, 4291.0, 5107.0, 6218.0])
        self.assertEqual(result["chains"][0]["member_observation_ids"], ["right-good"])

    def test_authority_remains_closed(self):
        result = build_refined_external_chains(
            side="TOP",
            axis_segments=[],
            tick_segments=[],
            observations=[],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 0)
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertFalse(result["eligible_for_metric_calibration"])
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])


if __name__ == "__main__":
    unittest.main()
