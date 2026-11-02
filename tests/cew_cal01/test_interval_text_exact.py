import unittest

from experiments.cew_cal01.interval_text_exact import (
    build_review_crop_bbox,
    select_local_carrier_axis,
)


class IntervalTextExactContractTests(unittest.TestCase):
    def test_local_axis_selection_prefers_strongest_ink_without_changing_governed_axis(self):
        profile = [0, 1, 2, 8, 4, 3, 1]
        result = select_local_carrier_axis(
            profile,
            governed_axis_px=100.0,
            profile_origin_px=97.0,
        )
        self.assertEqual(result["governed_axis_px"], 100.0)
        self.assertEqual(result["realigned_axis_px"], 100.0)
        self.assertFalse(result["governed_geometry_changed"])

    def test_local_axis_selection_uses_nearest_peak_on_tie(self):
        profile = [1, 9, 1, 1, 9, 1]
        result = select_local_carrier_axis(
            profile,
            governed_axis_px=103.0,
            profile_origin_px=100.0,
        )
        self.assertEqual(result["realigned_axis_px"], 104.0)

    def test_top_crop_uses_outward_half_plane_with_small_inward_guard(self):
        request = {
            "side": "TOP",
            "orientation": "HORIZONTAL",
            "interval_start_px": 100.0,
            "interval_end_px": 300.0,
            "crop_policy": {
                "longitudinal_inset_px": 15,
                "outward_depth_px": 220,
                "inward_guard_px": 40,
            },
        }
        bbox = build_review_crop_bbox(
            request,
            realigned_axis_px=500.0,
            image_width=1000,
            image_height=800,
        )
        self.assertEqual(bbox, [115, 280, 285, 540])

    def test_vertical_crop_is_clipped_and_rotated_for_review(self):
        request = {
            "side": "LEFT",
            "orientation": "VERTICAL",
            "interval_start_px": 10.0,
            "interval_end_px": 150.0,
            "crop_policy": {
                "longitudinal_inset_px": 15,
                "outward_depth_px": 220,
                "inward_guard_px": 40,
            },
        }
        bbox = build_review_crop_bbox(
            request,
            realigned_axis_px=100.0,
            image_width=1000,
            image_height=800,
        )
        self.assertEqual(bbox, [0, 25, 140, 135])

    def test_invalid_interval_fails_closed(self):
        request = {
            "side": "BOTTOM",
            "orientation": "HORIZONTAL",
            "interval_start_px": 300.0,
            "interval_end_px": 200.0,
            "crop_policy": {
                "longitudinal_inset_px": 15,
                "outward_depth_px": 220,
                "inward_guard_px": 40,
            },
        }
        with self.assertRaises(ValueError):
            build_review_crop_bbox(
                request,
                realigned_axis_px=500.0,
                image_width=1000,
                image_height=800,
            )


if __name__ == "__main__":
    unittest.main()
