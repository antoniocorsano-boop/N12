from __future__ import annotations

import unittest

from experiments.cew_b01.beam_hosted_markers import build_line_tracks, build_linear_carriers


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


class BeamHostedMarkerLineTrackTests(unittest.TestCase):
    def test_duplicate_horizontal_hough_segments_collapse_to_one_track_with_full_provenance(self):
        primitives = [
            line("L1", x=100, y=200, width=500, height=2, orientation="HORIZONTAL"),
            line("L2", x=102, y=201, width=496, height=2, orientation="HORIZONTAL"),
            line("L3", x=98, y=203, width=505, height=2, orientation="HORIZONTAL"),
        ]
        tracks = build_line_tracks(primitives)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0]["orientation"], "HORIZONTAL")
        self.assertEqual(tracks[0]["member_primitive_ids"], ["L1", "L2", "L3"])
        self.assertLessEqual(abs(tracks[0]["centerline"] - 202.0), 2.0)

    def test_horizontal_and_vertical_segments_never_coalesce(self):
        primitives = [
            line("H", x=100, y=200, width=500, height=2, orientation="HORIZONTAL"),
            line("V", x=300, y=50, width=2, height=500, orientation="VERTICAL"),
        ]
        tracks = build_line_tracks(primitives)
        self.assertEqual([track["orientation"] for track in tracks], ["HORIZONTAL", "VERTICAL"])

    def test_reversed_input_is_deterministic(self):
        primitives = [
            line("L1", x=100, y=200, width=500, height=2, orientation="HORIZONTAL"),
            line("L2", x=102, y=201, width=496, height=2, orientation="HORIZONTAL"),
            line("V1", x=900, y=100, width=2, height=400, orientation="VERTICAL"),
        ]
        self.assertEqual(build_line_tracks(primitives), build_line_tracks(list(reversed(primitives))))

    def test_no_first_220_cap_late_segments_remain_available(self):
        primitives = [
            line(f"D{i:03d}", x=0, y=float(i * 20), width=100, height=2, orientation="HORIZONTAL")
            for i in range(300)
        ]
        primitives.append(line("LATE", x=1000, y=9000, width=900, height=2, orientation="HORIZONTAL"))
        tracks = build_line_tracks(primitives)
        self.assertTrue(any("LATE" in track["member_primitive_ids"] for track in tracks))


class BeamHostedMarkerCarrierTests(unittest.TestCase):
    def test_two_distinct_long_parallel_tracks_form_one_carrier_with_provenance(self):
        primitives = [
            line("TOP", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("BOTTOM", x=120, y=260, width=960, height=2, orientation="HORIZONTAL"),
        ]
        carriers = build_linear_carriers(build_line_tracks(primitives))
        self.assertEqual(len(carriers), 1)
        carrier = carriers[0]
        self.assertEqual(carrier["orientation"], "HORIZONTAL")
        self.assertAlmostEqual(carrier["separation"], 60.0, delta=2.0)
        self.assertEqual(carrier["member_primitive_ids"], ["BOTTOM", "TOP"])

    def test_near_coincident_duplicate_edges_do_not_form_carrier(self):
        primitives = [
            line("A", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("B", x=100, y=204, width=1000, height=2, orientation="HORIZONTAL"),
        ]
        self.assertEqual(build_linear_carriers(build_line_tracks(primitives)), [])

    def test_orthogonal_tracks_do_not_form_carrier(self):
        primitives = [
            line("H", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("V", x=300, y=50, width=2, height=1000, orientation="VERTICAL"),
        ]
        self.assertEqual(build_linear_carriers(build_line_tracks(primitives)), [])

    def test_carrier_after_more_than_220_unrelated_tracks_is_still_found(self):
        primitives = [
            line(f"D{i:03d}", x=0, y=float(i * 30), width=100, height=2, orientation="HORIZONTAL")
            for i in range(300)
        ]
        primitives.extend([
            line("LATE_A", x=2000, y=10000, width=1200, height=2, orientation="HORIZONTAL"),
            line("LATE_B", x=2020, y=10070, width=1160, height=2, orientation="HORIZONTAL"),
        ])
        carriers = build_linear_carriers(build_line_tracks(primitives))
        self.assertTrue(any(set(carrier["member_primitive_ids"]) == {"LATE_A", "LATE_B"} for carrier in carriers))

    def test_carrier_output_is_deterministic_under_reversed_track_input(self):
        primitives = [
            line("A", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("B", x=120, y=260, width=960, height=2, orientation="HORIZONTAL"),
            line("C", x=2000, y=500, width=2, height=900, orientation="VERTICAL"),
            line("D", x=2070, y=520, width=2, height=860, orientation="VERTICAL"),
        ]
        tracks = build_line_tracks(primitives)
        self.assertEqual(build_linear_carriers(tracks), build_linear_carriers(list(reversed(tracks))))


if __name__ == "__main__":
    unittest.main()
