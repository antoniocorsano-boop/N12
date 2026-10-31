from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import unittest

import cv2
import numpy as np


MODULE_NAME = "experiments.cew_col02.review_directed_outer_envelope"
REVIEW_RECEIPT = Path("governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v1.json")
SUPPORTED_FINDING = "TOP_TRUNCATED_INTERNAL_LINE_SELECTED"


class ReviewDirectedOuterEnvelopeTests(unittest.TestCase):
    def _module(self):
        spec = importlib.util.find_spec(MODULE_NAME)
        self.assertIsNotNone(spec, "review-directed outer-envelope module is missing")
        return importlib.import_module(MODULE_NAME)

    @staticmethod
    def _base_result(*, x: int, y: int, width: int, height: int, image_w: int, image_h: int) -> dict:
        return {
            "schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_v1",
            "bbox": {
                "x": x / image_w,
                "y": y / image_h,
                "width": width / image_w,
                "height": height / image_h,
            },
            "axis_cross": {"x": (x + width / 2) / image_w, "y": (y + 10) / image_h},
            "axis_thickness_px": {"horizontal": 3, "vertical": 3},
            "boundary_side_count": 4,
            "boundary_coverage": {"left": 1.0, "right": 1.0, "top": 0.52, "bottom": 1.0},
            "detector": "LOCAL_AXIS_AWARE_FOUR_SIDE_ENVELOPE_REPAIR_HALF_SCALE_FALLBACK",
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
        }

    def test_top_truncation_extends_only_top_to_outer_boundary(self) -> None:
        module = self._module()
        image = np.full((400, 500), 255, dtype=np.uint8)
        cv2.rectangle(image, (150, 80), (350, 260), 0, 3)
        cv2.line(image, (150, 150), (350, 150), 0, 3)
        base = self._base_result(x=150, y=150, width=201, height=111, image_w=500, image_h=400)
        original_bottom = base["bbox"]["y"] + base["bbox"]["height"]

        result = module.complete_review_directed_outer_envelope(
            image,
            base,
            finding=SUPPORTED_FINDING,
        )

        self.assertIsNotNone(result)
        assert result is not None
        bbox = result["bbox"]
        self.assertAlmostEqual(bbox["x"], base["bbox"]["x"], places=12)
        self.assertAlmostEqual(bbox["width"], base["bbox"]["width"], places=12)
        self.assertAlmostEqual(bbox["y"], 80 / 400, delta=0.015)
        self.assertAlmostEqual(bbox["y"] + bbox["height"], original_bottom, places=12)
        self.assertEqual(result["detector"], "REVIEW_DIRECTED_OUTER_ENVELOPE_COMPLETION")
        self.assertEqual(result["review_directed_completion"]["finding"], SUPPORTED_FINDING)
        self.assertFalse(result["canonical_geometry_authorized"])
        self.assertFalse(result["canonical_write_authorized"])

    def test_ambiguous_outer_top_candidates_fail_closed(self) -> None:
        module = self._module()
        image = np.full((400, 500), 255, dtype=np.uint8)
        cv2.line(image, (150, 70), (150, 260), 0, 3)
        cv2.line(image, (350, 70), (350, 260), 0, 3)
        cv2.line(image, (150, 70), (350, 70), 0, 3)
        cv2.line(image, (150, 105), (350, 105), 0, 3)
        cv2.line(image, (150, 260), (350, 260), 0, 3)
        cv2.line(image, (150, 150), (350, 150), 0, 3)
        base = self._base_result(x=150, y=150, width=201, height=111, image_w=500, image_h=400)

        result = module.complete_review_directed_outer_envelope(
            image,
            base,
            finding=SUPPORTED_FINDING,
        )

        self.assertIsNone(result)

    def test_weak_frozen_side_evidence_fails_closed(self) -> None:
        module = self._module()
        image = np.full((400, 500), 255, dtype=np.uint8)
        cv2.line(image, (150, 80), (350, 80), 0, 3)
        cv2.line(image, (150, 150), (350, 150), 0, 3)
        cv2.line(image, (150, 260), (350, 260), 0, 3)
        base = self._base_result(x=150, y=150, width=201, height=111, image_w=500, image_h=400)

        result = module.complete_review_directed_outer_envelope(
            image,
            base,
            finding=SUPPORTED_FINDING,
        )

        self.assertIsNone(result)

    def test_governed_receipt_authorizes_only_wsr003_source_candidate(self) -> None:
        module = self._module()
        receipt = json.loads(REVIEW_RECEIPT.read_text(encoding="utf-8"))

        authorized = module.authorized_completion_requests(receipt)

        self.assertEqual(authorized, {"COL02-FP-0241": SUPPORTED_FINDING})


if __name__ == "__main__":
    unittest.main()
