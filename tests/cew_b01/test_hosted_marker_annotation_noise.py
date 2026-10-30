from __future__ import annotations

import unittest

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


def text_block(pid: str, *, x: float, y: float, width: float, height: float) -> dict:
    return {
        "primitive_id": pid,
        "family": "TEXT_BLOCK",
        "geometry": {"x": x, "y": y, "width": width, "height": height},
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
        primitives = self._base() + [text_block("TINY", x=500, y=220, width=2, height=2)]
        analysis = analyze_hosted_marker_occurrences(primitives, blank())
        eligible = {item["marker_primitive_id"]: item for item in analysis["review_eligible"]}
        self.assertIn("R", eligible)
        evidence = eligible["R"]["annotation_evidence"]
        self.assertEqual(evidence["overlapping_text_block_ids"], [])
        self.assertEqual(evidence["ignored_tiny_text_block_ids"], ["TINY"])
        self.assertFalse(evidence["annotation_dominated"])

    def test_material_text_block_still_marks_annotation_dominated(self):
        primitives = self._base() + [text_block("TEXT", x=470, y=218, width=22, height=18)]
        analysis = analyze_hosted_marker_occurrences(primitives, blank())
        rejected = {item["marker_primitive_id"]: item for item in analysis["annotation_dominated"]}
        self.assertIn("R", rejected)
        evidence = rejected["R"]["annotation_evidence"]
        self.assertEqual(evidence["overlapping_text_block_ids"], ["TEXT"])
        self.assertEqual(evidence["ignored_tiny_text_block_ids"], [])
        self.assertTrue(evidence["annotation_dominated"])


if __name__ == "__main__":
    unittest.main()
