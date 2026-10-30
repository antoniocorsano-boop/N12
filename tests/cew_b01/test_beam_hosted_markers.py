from __future__ import annotations

import unittest

from experiments.cew_b01.beam_hosted_markers import (
    build_hosted_marker_candidates,
    build_line_tracks,
    build_linear_carriers,
)


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


class BeamHostedMarkerSignatureTests(unittest.TestCase):
    def _base_horizontal(self) -> list[dict]:
        return [
            line("TOP", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("BOTTOM", x=100, y=260, width=1000, height=2, orientation="HORIZONTAL"),
            rect("R", x=420, y=208, width=60, height=46),
        ]

    def test_hosted_rectangle_without_two_transverse_tracks_is_alone_state(self):
        candidates = build_hosted_marker_candidates(self._base_horizontal(), ["R"])
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertEqual(candidates[0]["transverse_track_ids"], [])

    def test_two_distinct_orthogonal_tracks_crossing_carrier_form_transverse_pair_state(self):
        primitives = self._base_horizontal() + [
            line("V1", x=410, y=170, width=2, height=130, orientation="VERTICAL"),
            line("V2", x=490, y=170, width=2, height=130, orientation="VERTICAL"),
        ]
        candidates = build_hosted_marker_candidates(primitives, ["R"])
        self.assertEqual(candidates[0]["graphical_state"], "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE")
        self.assertEqual(len(candidates[0]["transverse_pair_track_ids"]), 2)
        self.assertEqual(set(candidates[0]["transverse_primitive_ids"]), {"V1", "V2"})

    def test_single_orthogonal_track_is_not_a_pair(self):
        primitives = self._base_horizontal() + [
            line("V1", x=450, y=170, width=2, height=130, orientation="VERTICAL"),
        ]
        candidates = build_hosted_marker_candidates(primitives, ["R"])
        self.assertEqual(candidates[0]["graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertEqual(len(candidates[0]["transverse_track_ids"]), 1)

    def test_marker_outside_carrier_band_is_not_bound(self):
        primitives = [
            line("TOP", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("BOTTOM", x=100, y=260, width=1000, height=2, orientation="HORIZONTAL"),
            rect("R", x=420, y=300, width=60, height=46),
        ]
        self.assertEqual(build_hosted_marker_candidates(primitives, ["R"]), [])

    def test_multiple_plausible_carriers_resolve_deterministically(self):
        primitives = self._base_horizontal() + [
            line("OUTER_TOP", x=90, y=190, width=1020, height=2, orientation="HORIZONTAL"),
            line("OUTER_BOTTOM", x=90, y=270, width=1020, height=2, orientation="HORIZONTAL"),
        ]
        forward = build_hosted_marker_candidates(primitives, ["R"])
        reverse = build_hosted_marker_candidates(list(reversed(primitives)), ["R"])
        self.assertEqual(forward, reverse)
        self.assertEqual(len(forward), 1)

    def test_authority_flags_remain_false_and_semantics_absent(self):
        candidate = build_hosted_marker_candidates(self._base_horizontal(), ["R"])[0]
        self.assertIsNone(candidate["semantic_meaning"])
        self.assertFalse(candidate["structural_identity_authorized"])
        self.assertFalse(candidate["canonical_write_authorized"])
        self.assertFalse(candidate["g3_authorized"])
        self.assertFalse(candidate["merge_authorized"])


if __name__ == "__main__":
    unittest.main()
