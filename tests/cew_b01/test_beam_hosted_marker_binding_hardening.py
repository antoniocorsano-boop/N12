from __future__ import annotations

import unittest

from experiments.cew_b01.beam_hosted_markers import build_hosted_marker_candidates


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


class HostedMarkerCarrierBindingHardeningTests(unittest.TestCase):
    def test_marker_inside_overwide_parallel_pair_is_not_bound_as_local_carrier(self):
        primitives = [
            line("TOP", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("BOTTOM", x=100, y=400, width=1000, height=2, orientation="HORIZONTAL"),
            rect("R", x=420, y=280, width=60, height=40),
        ]
        # The two lines are a valid generic parallel pair (200/1000 = 0.20),
        # but their separation is 5x the marker cross-span. They must not be
        # treated as the marker's local host carrier merely because they enclose it.
        self.assertEqual(build_hosted_marker_candidates(primitives, ["R"]), [])


if __name__ == "__main__":
    unittest.main()
