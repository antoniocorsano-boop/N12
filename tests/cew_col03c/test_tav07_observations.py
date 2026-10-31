from __future__ import annotations

import unittest

try:
    from experiments.cew_col03c.tav07_observations import (
        build_tav07_observation_inventory,
        normalize_tav07_text_observations,
    )
except (ImportError, ModuleNotFoundError):
    build_tav07_observation_inventory = None
    normalize_tav07_text_observations = None


SOURCE = {
    "catalogue_id": "TAV-07A",
    "archive_commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
    "source_path": "archive/documentazione_originaria/tavola7.pdf",
    "sha256": "38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b",
    "page_count": 1,
    "materialization_state": "MATERIALIZED_VERIFIED",
    "authority": "PRIMARY_DOCUMENTARY_SOURCE",
}

OBSERVATIONS = [
    {
        "page_index": 0,
        "raw_text": "  P4  ",
        "bbox": {"x": 0.20, "y": 0.10, "width": 0.04, "height": 0.02},
        "confidence": 92.0,
    },
    {
        "page_index": 0,
        "raw_text": "P4",
        "bbox": {"x": 0.70, "y": 0.60, "width": 0.04, "height": 0.02},
        "confidence": 88.0,
    },
    {
        "page_index": 0,
        "raw_text": " 30 ",
        "bbox": {"x": 0.40, "y": 0.30, "width": 0.03, "height": 0.02},
        "confidence": 75.0,
    },
]


class Tav07ObservationTests(unittest.TestCase):
    def test_normalization_is_order_invariant_with_stable_ids(self):
        self.assertIsNotNone(normalize_tav07_text_observations, "TAV.7 observation implementation missing")
        first = normalize_tav07_text_observations(OBSERVATIONS, source_metadata=SOURCE)
        second = normalize_tav07_text_observations(list(reversed(OBSERVATIONS)), source_metadata=SOURCE)
        self.assertEqual(first, second)
        self.assertEqual(len({row["observation_id"] for row in first}), 3)

    def test_same_text_at_different_regions_remains_distinct(self):
        self.assertIsNotNone(normalize_tav07_text_observations, "TAV.7 observation implementation missing")
        rows = normalize_tav07_text_observations(OBSERVATIONS, source_metadata=SOURCE)
        p4 = [row for row in rows if row["normalized_text"] == "P4"]
        self.assertEqual(len(p4), 2)
        self.assertNotEqual(p4[0]["observation_id"], p4[1]["observation_id"])
        self.assertNotEqual(p4[0]["bbox"], p4[1]["bbox"])

    def test_observations_keep_source_page_region_and_are_unbound(self):
        self.assertIsNotNone(normalize_tav07_text_observations, "TAV.7 observation implementation missing")
        rows = normalize_tav07_text_observations(OBSERVATIONS, source_metadata=SOURCE)
        for row in rows:
            self.assertEqual(row["source_catalogue_id"], "TAV-07A")
            self.assertEqual(row["source_sha256"], SOURCE["sha256"])
            self.assertEqual(row["archive_commit"], SOURCE["archive_commit"])
            self.assertEqual(row["page_index"], 0)
            self.assertIsInstance(row["bbox"], dict)
            self.assertEqual(row["binding_state"], "UNBOUND")
            self.assertFalse(row["identity_promotion_authorized"])
            self.assertNotIn("support_identity", row)
            self.assertNotIn("structural_identity", row)

    def test_empty_text_is_not_invented(self):
        self.assertIsNotNone(normalize_tav07_text_observations, "TAV.7 observation implementation missing")
        rows = normalize_tav07_text_observations(
            [{"page_index": 0, "raw_text": "   ", "bbox": {"x": 0.1, "y": 0.1, "width": 0.1, "height": 0.1}}],
            source_metadata=SOURCE,
        )
        self.assertEqual(rows, [])
        inventory = build_tav07_observation_inventory(
            rows,
            extraction_method="TESSERACT_PSM11",
            extraction_version="tesseract 5.3.4",
        )
        self.assertEqual(inventory["observation_state"], "NO_MACHINE_TEXT_OBSERVED")
        self.assertEqual(inventory["observation_count"], 0)
        self.assertEqual(inventory["observations"], [])

    def test_inventory_records_actual_extractor_and_digest(self):
        self.assertIsNotNone(build_tav07_observation_inventory, "TAV.7 observation implementation missing")
        rows = normalize_tav07_text_observations(OBSERVATIONS, source_metadata=SOURCE)
        inventory = build_tav07_observation_inventory(
            rows,
            extraction_method="TESSERACT_PSM11",
            extraction_version="tesseract 5.3.4",
        )
        self.assertEqual(inventory["observation_state"], "MACHINE_OBSERVATIONS_PRESENT")
        self.assertEqual(inventory["observation_count"], 3)
        self.assertEqual(inventory["extraction_method"], "TESSERACT_PSM11")
        self.assertEqual(inventory["extraction_version"], "tesseract 5.3.4")
        self.assertEqual(len(inventory["observation_digest"]), 64)
        self.assertFalse(inventory["identity_promotion_authorized"])

    def test_invalid_page_or_bbox_fails_closed(self):
        self.assertIsNotNone(normalize_tav07_text_observations, "TAV.7 observation implementation missing")
        bad_page = [{"page_index": 2, "raw_text": "P4", "bbox": {"x": 0.1, "y": 0.1, "width": 0.1, "height": 0.1}}]
        with self.assertRaisesRegex(ValueError, "page"):
            normalize_tav07_text_observations(bad_page, source_metadata=SOURCE)
        bad_box = [{"page_index": 0, "raw_text": "P4", "bbox": {"x": -0.1, "y": 0.1, "width": 0.1, "height": 0.1}}]
        with self.assertRaisesRegex(ValueError, "bbox"):
            normalize_tav07_text_observations(bad_box, source_metadata=SOURCE)


if __name__ == "__main__":
    unittest.main()
