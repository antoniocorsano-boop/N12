import unittest

from experiments.cew_cal01.oriented_ocr import (
    backproject_rotated_bbox,
    deduplicate_metric_observations,
    generate_tile_windows,
)


class Cal01OrientedOcrContractTests(unittest.TestCase):
    def test_tile_windows_cover_roi_deterministically(self):
        windows = generate_tile_windows(
            page_width=1000,
            page_height=1600,
            roi_px=[0, 300, 1000, 1600],
            tile_width=400,
            tile_height=500,
            overlap=100,
        )
        self.assertEqual(windows[0], [0, 300, 400, 800])
        self.assertEqual(windows[-1], [600, 1100, 1000, 1600])
        self.assertEqual(windows, generate_tile_windows(
            page_width=1000,
            page_height=1600,
            roi_px=[0, 300, 1000, 1600],
            tile_width=400,
            tile_height=500,
            overlap=100,
        ))

    def test_backprojection_preserves_page_coordinates_for_all_quadrant_rotations(self):
        tile = [100, 200, 200, 260]  # width=100, height=60
        original_local = [10, 20, 30, 40]
        rotated_boxes = {
            0: [10, 20, 30, 40],
            90: [20, 10, 40, 30],
            180: [70, 20, 90, 40],
            270: [20, 70, 40, 90],
        }
        expected_page = [110.0, 220.0, 130.0, 240.0]
        for rotation, rotated_bbox in rotated_boxes.items():
            with self.subTest(rotation=rotation):
                self.assertEqual(
                    backproject_rotated_bbox(rotated_bbox, tile_bbox_px=tile, rotation_deg=rotation),
                    expected_page,
                )

    def test_dedup_keeps_best_confidence_and_preserves_orientation_evidence(self):
        observations = [
            {
                "normalized_metric_text": "1.20",
                "metric_value_m": 1.2,
                "bbox_px": [100.0, 200.0, 140.0, 220.0],
                "ocr_confidence": 71.0,
                "rotation_deg": 0,
                "tile_id": "T1",
            },
            {
                "normalized_metric_text": "1.20",
                "metric_value_m": 1.2,
                "bbox_px": [104.0, 202.0, 144.0, 222.0],
                "ocr_confidence": 88.0,
                "rotation_deg": 270,
                "tile_id": "T2",
            },
            {
                "normalized_metric_text": "4.70",
                "metric_value_m": 4.7,
                "bbox_px": [500.0, 800.0, 560.0, 830.0],
                "ocr_confidence": 91.0,
                "rotation_deg": 90,
                "tile_id": "T3",
            },
        ]
        result = deduplicate_metric_observations(observations, centroid_tolerance_px=16.0)
        self.assertEqual(len(result), 2)
        first = next(item for item in result if item["normalized_metric_text"] == "1.20")
        self.assertEqual(first["ocr_confidence"], 88.0)
        self.assertEqual(first["rotation_deg"], 270)
        self.assertEqual(first["supporting_observation_count"], 2)
        self.assertEqual(sorted(first["observed_rotations_deg"]), [0, 270])


if __name__ == "__main__":
    unittest.main()
