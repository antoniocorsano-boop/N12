from __future__ import annotations

import unittest

from experiments.cew_b01.beam_hosted_marker_hybrid import build_hybrid_hosted_marker_candidates


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


def blank(width: int = 1200, height: int = 500) -> list[list[bool]]:
    return [[False for _ in range(width)] for _ in range(height)]


def vertical_stroke(binary: list[list[bool]], x0: int, x1: int, y0: int, y1: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            binary[y][x] = True


class HybridHostedMarkerTests(unittest.TestCase):
    def _base(self) -> list[dict]:
        return [
            line("TOP", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("BOTTOM", x=100, y=260, width=1000, height=2, orientation="HORIZONTAL"),
            rect("R", x=420, y=208, width=100, height=46),
            line("ONE_HOUGH", x=520, y=70, width=2, height=190, orientation="VERTICAL"),
        ]

    def test_raster_pair_can_recover_pair_when_primitive_state_has_only_one_local_track(self):
        binary = blank()
        vertical_stroke(binary, 485, 488, 70, 198)
        vertical_stroke(binary, 515, 518, 70, 198)
        candidate = build_hybrid_hosted_marker_candidates(self._base(), ["R"], binary)[0]
        self.assertEqual(candidate["primitive_graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertTrue(candidate["raster_transverse_evidence"]["pair_detected"])
        self.assertEqual(candidate["graphical_state"], "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE")
        self.assertEqual(candidate["pair_evidence_sources"], ["RASTER_LOCAL_PROFILE"])

    def test_blank_raster_keeps_alone_state_when_primitive_pair_is_absent(self):
        candidate = build_hybrid_hosted_marker_candidates(self._base(), ["R"], blank())[0]
        self.assertEqual(candidate["primitive_graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertFalse(candidate["raster_transverse_evidence"]["pair_detected"])
        self.assertEqual(candidate["graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertEqual(candidate["pair_evidence_sources"], [])

    def test_hybrid_output_remains_nonsemantic_and_nonpromoting(self):
        candidate = build_hybrid_hosted_marker_candidates(self._base(), ["R"], blank())[0]
        self.assertIsNone(candidate["semantic_meaning"])
        self.assertFalse(candidate["structural_identity_authorized"])
        self.assertFalse(candidate["canonical_write_authorized"])
        self.assertFalse(candidate["g3_authorized"])
        self.assertFalse(candidate["merge_authorized"])


if __name__ == "__main__":
    unittest.main()
