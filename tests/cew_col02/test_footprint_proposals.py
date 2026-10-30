from __future__ import annotations

import unittest

import cv2
import numpy as np

from experiments.cew_col02.footprint_proposals import (
    _suppress_nested_raw_candidates,
    extract_footprint_proposals,
)


class FootprintProposalTests(unittest.TestCase):
    def test_long_crossing_axes_do_not_prevent_elongated_envelope_proposal(self) -> None:
        image = np.full((1000, 1000), 255, dtype=np.uint8)
        # Small elongated footprint crossed by page-scale axes.
        cv2.rectangle(image, (491, 470), (509, 525), 0, 2)
        cv2.line(image, (100, 497), (900, 497), 0, 2)
        cv2.line(image, (500, 100), (500, 900), 0, 2)

        payload = extract_footprint_proposals(image, max_candidates=200)
        envelopes = [row for row in payload["candidates"] if row["detector"] == "LONG_AXIS_SUPPRESSED"]
        self.assertGreater(len(envelopes), 0)
        self.assertTrue(
            any(
                row["bbox"]["x"] < 0.52
                and row["bbox"]["x"] + row["bbox"]["width"] > 0.48
                and row["bbox"]["y"] < 0.54
                and row["bbox"]["y"] + row["bbox"]["height"] > 0.46
                for row in envelopes
            )
        )
        self.assertTrue(all("best_family_prior" not in row for row in payload["candidates"]))
        self.assertFalse(payload["authority"]["support_identity_authorized"])

    def test_nested_raw_subcontour_is_suppressed_by_geometry_only(self) -> None:
        rows = [
            {
                "candidate_id": "OUTER",
                "bbox": {"x": 0.40, "y": 0.40, "width": 0.08, "height": 0.08},
                "rectangularity": 0.80,
                "detector": "LONG_AXIS_SUPPRESSED",
            },
            {
                "candidate_id": "INNER",
                "bbox": {"x": 0.42, "y": 0.42, "width": 0.04, "height": 0.04},
                "rectangularity": 0.90,
                "detector": "RAW_CONTOUR",
            },
            {
                "candidate_id": "SEPARATE",
                "bbox": {"x": 0.70, "y": 0.70, "width": 0.04, "height": 0.04},
                "rectangularity": 0.90,
                "detector": "RAW_CONTOUR",
            },
        ]
        filtered, suppressed = _suppress_nested_raw_candidates(rows)
        ids = [row["candidate_id"] for row in filtered]
        self.assertEqual(suppressed, 1)
        self.assertIn("OUTER", ids)
        self.assertNotIn("INNER", ids)
        self.assertIn("SEPARATE", ids)

    def test_proposal_generation_has_no_support_or_family_identity(self) -> None:
        image = np.full((500, 500), 255, dtype=np.uint8)
        cv2.rectangle(image, (230, 230), (250, 250), 0, 2)
        payload = extract_footprint_proposals(image, max_candidates=50)
        for row in payload["candidates"]:
            self.assertIsNone(row["support_identity"])
            self.assertIsNone(row["family_id"])
        self.assertFalse(payload["authority"]["family_assignment_authorized"])
        self.assertFalse(payload["authority"]["structural_identity_authorized"])
        self.assertFalse(payload["authority"]["canonical_write_authorized"])


if __name__ == "__main__":
    unittest.main()
