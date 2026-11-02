import unittest

from experiments.cew_cal01.external_dimension_chain import detect_external_dimension_chains


PLAN = [100.0, 100.0, 900.0, 700.0]


def obs(observation_id, cx, cy, *, side, width=40.0, height=24.0):
    return {
        "observation_id": observation_id,
        "search_band": side,
        "bbox_normalized_px": [
            cx - width / 2.0,
            cy - height / 2.0,
            cx + width / 2.0,
            cy + height / 2.0,
        ],
    }


class ExternalDimensionChainContractTests(unittest.TestCase):
    def test_horizontal_long_carrier_builds_four_interval_chain(self):
        lines = [
            (120.0, 760.0, 880.0, 760.0),
            (150.0, 738.0, 150.0, 782.0),
            (300.0, 738.0, 300.0, 782.0),
            (470.0, 738.0, 470.0, 782.0),
            (650.0, 738.0, 650.0, 782.0),
            (850.0, 738.0, 850.0, 782.0),
        ]
        observations = [
            obs("d1", 225.0, 730.0, side="BOTTOM"),
            obs("d2", 385.0, 730.0, side="BOTTOM"),
            obs("d3", 560.0, 730.0, side="BOTTOM"),
            obs("d4", 750.0, 730.0, side="BOTTOM"),
        ]

        result = detect_external_dimension_chains(
            side="BOTTOM",
            line_segments=lines,
            observations=observations,
            plan_envelope_bbox=PLAN,
        )

        self.assertEqual(result["chain_count"], 1)
        chain = result["chains"][0]
        self.assertEqual(chain["orientation"], "HORIZONTAL")
        self.assertEqual(chain["tick_positions_px"], [150.0, 300.0, 470.0, 650.0, 850.0])
        self.assertEqual(len(chain["intervals"]), 4)
        self.assertEqual(chain["member_observation_ids"], ["d1", "d2", "d3", "d4"])
        self.assertEqual(result["member_observation_count"], 4)
        self.assertEqual(result["unresolved_observation_ids"], [])
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertFalse(result["authority"]["canonical_geometry_authorized"])

    def test_long_structural_edge_without_repeated_ticks_is_rejected(self):
        result = detect_external_dimension_chains(
            side="BOTTOM",
            line_segments=[(120.0, 760.0, 880.0, 760.0)],
            observations=[obs("d1", 400.0, 730.0, side="BOTTOM")],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 0)
        self.assertEqual(result["member_observation_count"], 0)
        self.assertEqual(result["unresolved_observation_ids"], ["d1"])

    def test_short_local_dimension_is_not_external_chain(self):
        lines = [
            (400.0, 760.0, 520.0, 760.0),
            (400.0, 740.0, 400.0, 780.0),
            (460.0, 740.0, 460.0, 780.0),
            (520.0, 740.0, 520.0, 780.0),
        ]
        result = detect_external_dimension_chains(
            side="BOTTOM",
            line_segments=lines,
            observations=[obs("local", 460.0, 730.0, side="BOTTOM")],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 0)
        self.assertEqual(result["unresolved_observation_ids"], ["local"])

    def test_nested_right_carriers_remain_distinct(self):
        lines = [
            (960.0, 120.0, 960.0, 680.0),
            (940.0, 150.0, 980.0, 150.0),
            (940.0, 300.0, 980.0, 300.0),
            (940.0, 500.0, 980.0, 500.0),
            (940.0, 650.0, 980.0, 650.0),
            (1040.0, 150.0, 1040.0, 680.0),
            (1020.0, 180.0, 1060.0, 180.0),
            (1020.0, 420.0, 1060.0, 420.0),
            (1020.0, 650.0, 1060.0, 650.0),
        ]
        observations = [
            obs("inner-a", 935.0, 225.0, side="RIGHT"),
            obs("inner-b", 935.0, 400.0, side="RIGHT"),
            obs("outer-a", 1015.0, 300.0, side="RIGHT"),
            obs("outer-b", 1015.0, 535.0, side="RIGHT"),
        ]
        result = detect_external_dimension_chains(
            side="RIGHT",
            line_segments=lines,
            observations=observations,
            plan_envelope_bbox=PLAN,
        )

        self.assertEqual(result["chain_count"], 2)
        members = [chain["member_observation_ids"] for chain in result["chains"]]
        self.assertEqual(members, [["inner-a", "inner-b"], ["outer-a", "outer-b"]])

    def test_equidistant_token_between_two_valid_carriers_fails_closed(self):
        lines = [
            (120.0, 760.0, 880.0, 760.0),
            (150.0, 740.0, 150.0, 780.0),
            (400.0, 740.0, 400.0, 780.0),
            (850.0, 740.0, 850.0, 780.0),
            (120.0, 800.0, 880.0, 800.0),
            (150.0, 780.0, 150.0, 820.0),
            (400.0, 780.0, 400.0, 820.0),
            (850.0, 780.0, 850.0, 820.0),
        ]
        result = detect_external_dimension_chains(
            side="BOTTOM",
            line_segments=lines,
            observations=[obs("ambiguous", 275.0, 780.0, side="BOTTOM")],
            plan_envelope_bbox=PLAN,
        )

        self.assertEqual(result["chain_count"], 2)
        self.assertEqual(result["member_observation_count"], 0)
        self.assertEqual(result["unresolved_observation_ids"], ["ambiguous"])

    def test_zero_chain_result_is_valid_and_closed(self):
        result = detect_external_dimension_chains(
            side="TOP",
            line_segments=[],
            observations=[],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 0)
        self.assertEqual(result["chains"], [])
        self.assertEqual(result["primary_anchor_count"], 0)
        self.assertFalse(result["authority"]["canonical_write_authorized"])


if __name__ == "__main__":
    unittest.main()
