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


class ExternalDimensionChainHardeningTests(unittest.TestCase):
    def test_bottom_carrier_inside_plan_envelope_is_not_external(self):
        lines = [
            (120.0, 680.0, 880.0, 680.0),
            (150.0, 660.0, 150.0, 700.0),
            (350.0, 660.0, 350.0, 700.0),
            (600.0, 660.0, 600.0, 700.0),
            (850.0, 660.0, 850.0, 700.0),
        ]
        result = detect_external_dimension_chains(
            side="BOTTOM",
            line_segments=lines,
            observations=[obs("inside", 475.0, 660.0, side="BOTTOM")],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 0)
        self.assertEqual(result["unresolved_observation_ids"], ["inside"])

    def test_dense_structural_crossings_do_not_form_external_chain(self):
        lines = [
            (120.0, 760.0, 880.0, 760.0),
            (150.0, 738.0, 150.0, 782.0),
            (180.0, 738.0, 180.0, 782.0),
            (210.0, 738.0, 210.0, 782.0),
            (500.0, 738.0, 500.0, 782.0),
            (850.0, 738.0, 850.0, 782.0),
        ]
        result = detect_external_dimension_chains(
            side="BOTTOM",
            line_segments=lines,
            observations=[obs("noise", 600.0, 730.0, side="BOTTOM")],
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 0)
        self.assertEqual(result["unresolved_observation_ids"], ["noise"])

    def test_overlapping_ocr_alternatives_count_as_one_graphic_location(self):
        lines = [
            (120.0, 760.0, 880.0, 760.0),
            (150.0, 738.0, 150.0, 782.0),
            (350.0, 738.0, 350.0, 782.0),
            (600.0, 738.0, 600.0, 782.0),
            (850.0, 738.0, 850.0, 782.0),
        ]
        observations = [
            obs("reading-1.50", 250.0, 730.0, side="BOTTOM"),
            obs("reading-4.50", 250.0, 730.0, side="BOTTOM"),
        ]
        result = detect_external_dimension_chains(
            side="BOTTOM",
            line_segments=lines,
            observations=observations,
            plan_envelope_bbox=PLAN,
        )
        self.assertEqual(result["chain_count"], 1)
        chain = result["chains"][0]
        self.assertEqual(chain["member_observation_count"], 1)
        self.assertEqual(chain["member_observation_ids"], ["reading-1.50", "reading-4.50"])
        self.assertEqual(chain["member_location_groups"], [["reading-1.50", "reading-4.50"]])
        self.assertEqual(result["member_observation_count"], 1)


if __name__ == "__main__":
    unittest.main()
