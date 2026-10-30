from __future__ import annotations

import json
import unittest

from experiments.cew_b01.hosted_marker_occurrence_search import discover_hosted_marker_occurrences


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


def payload_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class HostedMarkerOccurrenceDiscoveryTests(unittest.TestCase):
    def _primitives(self) -> list[dict]:
        return [
            line("TOP", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("BOTTOM", x=100, y=260, width=1000, height=2, orientation="HORIZONTAL"),
            rect("R_ALONE", x=420, y=208, width=60, height=46),
            rect("R_PAIR", x=620, y=208, width=60, height=46),
            rect("R_OUTSIDE", x=420, y=320, width=60, height=46),
            {
                "primitive_id": "TEXT",
                "family": "TEXT_BLOCK",
                "geometry": {"x": 500, "y": 210, "width": 50, "height": 20},
                "source": {"sha256": "source"},
                "page_index": 0,
                "frame": "RASTER_PIXEL",
            },
        ]

    def _binary(self) -> list[list[bool]]:
        binary = blank()
        vertical_stroke(binary, 635, 638, 70, 198)
        vertical_stroke(binary, 660, 663, 70, 198)
        return binary

    def test_discovers_all_and_only_rectilinear_markers_that_bind_to_local_carrier(self):
        result = discover_hosted_marker_occurrences(self._primitives(), self._binary())
        self.assertEqual([item["marker_primitive_id"] for item in result], ["R_ALONE", "R_PAIR"])

    def test_raster_pair_recovery_preserves_primitive_state_separately(self):
        by_id = {
            item["marker_primitive_id"]: item
            for item in discover_hosted_marker_occurrences(self._primitives(), self._binary())
        }
        self.assertEqual(by_id["R_PAIR"]["primitive_graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertTrue(by_id["R_PAIR"]["raster_transverse_evidence"]["pair_detected"])
        self.assertEqual(by_id["R_PAIR"]["graphical_state"], "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE")
        self.assertEqual(by_id["R_PAIR"]["pair_evidence_sources"], ["RASTER_LOCAL_PROFILE"])
        self.assertEqual(by_id["R_ALONE"]["graphical_state"], "RECT_ALONE_ON_CARRIER")

    def test_occurrences_remain_nonsemantic_and_nonpromoting(self):
        for item in discover_hosted_marker_occurrences(self._primitives(), self._binary()):
            self.assertIsNone(item["semantic_meaning"])
            self.assertFalse(item["structural_identity_authorized"])
            self.assertFalse(item["canonical_write_authorized"])
            self.assertFalse(item["g3_authorized"])
            self.assertFalse(item["merge_authorized"])

    def test_reversed_primitive_input_is_byte_deterministic(self):
        forward = discover_hosted_marker_occurrences(self._primitives(), self._binary())
        reverse = discover_hosted_marker_occurrences(list(reversed(self._primitives())), self._binary())
        self.assertEqual(payload_bytes(forward), payload_bytes(reverse))


if __name__ == "__main__":
    unittest.main()
