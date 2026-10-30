from __future__ import annotations

import json
import unittest
from pathlib import Path

from experiments.cew_b01.hosted_marker_occurrence_search import analyze_hosted_marker_occurrences


def line(pid: str, *, x: float, y: float, width: float, height: float, orientation: str) -> dict:
    return {
        "primitive_id": pid,
        "family": "LINE_SEGMENT",
        "geometry": {"x": x, "y": y, "width": width, "height": height},
        "feature_signature": {"orientation": orientation},
        "source": {"sha256": "source"},
        "page_index": 0,
        "frame": "RASTER_PIXEL",
    }


def rect(pid: str, *, x: float, y: float, width: float, height: float) -> dict:
    return {
        "primitive_id": pid,
        "family": "RECTILINEAR_CLOSED_SHAPE",
        "geometry": {"x": x, "y": y, "width": width, "height": height},
        "feature_signature": {"vertex_count": 4, "rectangularity": 0.95},
        "source": {"sha256": "source"},
        "page_index": 0,
        "frame": "RASTER_PIXEL",
    }


def text_block(
    pid: str,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    component_area: float | None = None,
    ink_ratio: float | None = None,
) -> dict:
    feature_signature = {}
    if component_area is not None:
        feature_signature["component_area"] = component_area
    if ink_ratio is not None:
        feature_signature["ink_ratio"] = ink_ratio
    return {
        "primitive_id": pid,
        "family": "TEXT_BLOCK",
        "geometry": {"x": x, "y": y, "width": width, "height": height},
        "feature_signature": feature_signature,
        "source": {"sha256": "source"},
        "page_index": 0,
        "frame": "RASTER_PIXEL",
    }


def blank(width: int = 1200, height: int = 500) -> list[list[bool]]:
    return [[False for _ in range(width)] for _ in range(height)]


class HostedMarkerAnnotationNoiseTests(unittest.TestCase):
    def _base(self) -> list[dict]:
        return [
            line("TOP", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("BOTTOM", x=100, y=260, width=1000, height=2, orientation="HORIZONTAL"),
            rect("R", x=420, y=208, width=154, height=46),
        ]

    def test_two_by_two_text_speck_is_preserved_as_ignored_noise_not_annotation_dominance(self):
        primitives = self._base() + [
            text_block("TINY", x=500, y=220, width=2, height=2, component_area=4, ink_ratio=1.0)
        ]
        analysis = analyze_hosted_marker_occurrences(primitives, blank())
        eligible = {item["marker_primitive_id"]: item for item in analysis["review_eligible"]}
        self.assertIn("R", eligible)
        evidence = eligible["R"]["annotation_evidence"]
        self.assertEqual(evidence["overlapping_text_block_ids"], [])
        self.assertEqual(evidence["ignored_tiny_text_block_ids"], ["TINY"])
        self.assertFalse(evidence["annotation_dominated"])

    def test_r03_like_low_ink_text_box_is_ignored_using_component_area_not_bounding_box(self):
        primitives = self._base() + [
            text_block(
                "LOW_INK",
                x=500,
                y=220,
                width=19,
                height=7,
                component_area=41,
                ink_ratio=41 / (19 * 7),
            )
        ]
        analysis = analyze_hosted_marker_occurrences(primitives, blank())
        eligible = {item["marker_primitive_id"]: item for item in analysis["review_eligible"]}
        self.assertIn("R", eligible)
        evidence = eligible["R"]["annotation_evidence"]
        self.assertEqual(evidence["overlapping_text_block_ids"], [])
        self.assertEqual(evidence["ignored_tiny_text_block_ids"], ["LOW_INK"])
        self.assertEqual(evidence["text_component_areas"]["LOW_INK"], 41.0)
        self.assertFalse(evidence["annotation_dominated"])

    def test_material_text_component_still_marks_annotation_dominated(self):
        primitives = self._base() + [
            text_block(
                "TEXT",
                x=470,
                y=218,
                width=22,
                height=18,
                component_area=88,
                ink_ratio=88 / (22 * 18),
            )
        ]
        analysis = analyze_hosted_marker_occurrences(primitives, blank())
        rejected = {item["marker_primitive_id"]: item for item in analysis["annotation_dominated"]}
        self.assertIn("R", rejected)
        evidence = rejected["R"]["annotation_evidence"]
        self.assertEqual(evidence["overlapping_text_block_ids"], ["TEXT"])
        self.assertEqual(evidence["ignored_tiny_text_block_ids"], [])
        self.assertEqual(evidence["text_component_areas"]["TEXT"], 88.0)
        self.assertTrue(evidence["annotation_dominated"])


class HostedMarkerGovernanceReceiptTests(unittest.TestCase):
    def test_receipt_matches_reworked_exact_source_result(self):
        receipt_path = Path("governance/cew-b01/HOSTED_MARKER_OCCURRENCE_SEARCH_v1.json")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        self.assertEqual(receipt["schema_id"], "CEW_B01_HOSTED_MARKER_OCCURRENCE_SEARCH_RESULT")
        self.assertEqual(receipt["schema_version"], 2)
        self.assertEqual(receipt["status"], "SEARCH_REWORK_PASS_HUMAN_GRAPHICAL_REVIEW_PENDING")

        result = receipt["search_result"]
        self.assertEqual(result["all_bound_occurrence_count"], 50)
        self.assertEqual(result["review_eligible_occurrence_count"], 46)
        self.assertEqual(result["annotation_dominated_count"], 4)
        self.assertEqual(
            result["counts_by_graphical_state"],
            {
                "RECT_ALONE_ON_CARRIER": 25,
                "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE": 21,
            },
        )
        self.assertEqual(result["additional_ranked_count"], 44)
        self.assertEqual(
            result["additional_ranked_counts_by_graphical_state"],
            {
                "RECT_ALONE_ON_CARRIER": 24,
                "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE": 20,
            },
        )
        self.assertEqual(
            result["review_eligible_occurrence_count"] + result["annotation_dominated_count"],
            result["all_bound_occurrence_count"],
        )

        self.assertEqual(
            receipt["evidence"]["replay_sha256"],
            "f68cfaccb496bd5c8d6b90ed4dbc68d4a3c242bcb9b905c5d01bfbf7ffd76459",
        )
        self.assertEqual(
            [item["marker_primitive_id"] for item in receipt["annotation_dominated"]],
            [
                "CEW-B01-GP-8b7eae9c9f25bb1d73c6f504",
                "CEW-B01-GP-cf4860204d8bb1c826d35f40",
                "CEW-B01-GP-dd6f0d8649bb8b6add8e0507",
                "CEW-B01-GP-f417c150f3a1b9a8d30c7d03",
            ],
        )
        self.assertEqual(
            receipt["regression_cases"]["R03_recovered"]["expected_role"],
            "REVIEW_ELIGIBLE",
        )
        self.assertTrue(receipt["annotation_separation"]["ignored_text_noise_preserved"])
        self.assertFalse(receipt["authority"]["semantic_classification_authorized"])
        self.assertFalse(receipt["authority"]["structural_identity_authorized"])
        self.assertFalse(receipt["authority"]["canonical_write_authorized"])
        self.assertFalse(receipt["authority"]["g2c_promotion_authorized"])
        self.assertFalse(receipt["authority"]["g3_authorized"])
        self.assertFalse(receipt["authority"]["merge_authorized"])


if __name__ == "__main__":
    unittest.main()
