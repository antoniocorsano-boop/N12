import unittest

from experiments.cew_cal01.oriented_refinement import (
    backproject_rotated_bbox,
    cluster_numeric_observations_by_location,
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

    def test_location_cluster_preserves_conflicting_readings_before_consensus(self):
        observations = [
            {
                "raw_ocr_text": "120",
                "normalized_metric_text": "1.20",
                "bbox_px": [100.0, 200.0, 140.0, 220.0],
                "ocr_confidence": 88.0,
                "ocr_rotation_degrees": 270,
                "tile_index": 1,
            },
            {
                "raw_ocr_text": "420",
                "normalized_metric_text": "4.20",
                "bbox_px": [104.0, 202.0, 144.0, 222.0],
                "ocr_confidence": 61.0,
                "ocr_rotation_degrees": 270,
                "tile_index": 2,
            },
            {
                "raw_ocr_text": "120",
                "normalized_metric_text": "1.20",
                "bbox_px": [98.0, 198.0, 138.0, 218.0],
                "ocr_confidence": 92.0,
                "ocr_rotation_degrees": 90,
                "tile_index": 3,
            },
            {
                "raw_ocr_text": "470",
                "normalized_metric_text": "4.70",
                "bbox_px": [500.0, 800.0, 560.0, 830.0],
                "ocr_confidence": 91.0,
                "ocr_rotation_degrees": 90,
                "tile_index": 4,
            },
        ]
        clusters = cluster_numeric_observations_by_location(observations, centroid_tolerance_px=16.0)
        self.assertEqual(len(clusters), 2)
        first = clusters[0]
        self.assertEqual(first["observation_count"], 3)
        self.assertEqual(first["readings"], ["120", "120", "420"])
        self.assertEqual(first["observed_rotations_deg"], [90, 270])
        self.assertEqual(first["supporting_tile_ids"], ["1", "2", "3"])
        self.assertEqual(first["representative"]["raw_ocr_text"], "120")
        self.assertEqual(first["representative"]["ocr_confidence"], 92.0)


if __name__ == "__main__":
    unittest.main()
