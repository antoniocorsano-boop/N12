from __future__ import annotations

import unittest

from experiments.cew_b01.marker_topology_repair import describe_transverse_band


def blank(width: int = 260, height: int = 180) -> list[list[bool]]:
    return [[False for _ in range(width)] for _ in range(height)]


def draw_vertical(binary: list[list[bool]], x: int, y0: int, y1: int, width: int = 1) -> None:
    for px in range(x, x + width):
        for y in range(y0, y1 + 1):
            binary[y][px] = True


def draw_horizontal(binary: list[list[bool]], y: int, x0: int, x1: int, width: int = 1) -> None:
    for py in range(y, y + width):
        for x in range(x0, x1 + 1):
            binary[py][x] = True


def track(tid: str, *, orientation: str, centerline: float, start: float, end: float) -> dict:
    return {
        "track_id": tid,
        "orientation": orientation,
        "centerline": centerline,
        "start": start,
        "end": end,
        "length": end - start,
        "member_primitive_ids": [tid + "-P"],
    }


def horizontal_candidate() -> dict:
    geometry = {"x": 100.0, "y": 90.0, "width": 40.0, "height": 20.0}
    return {
        "marker_primitive_id": "R-H",
        "marker_geometry": dict(geometry),
        "source_marker_geometry": dict(geometry),
        "review_marker_geometry": dict(geometry),
        "carrier_orientation": "HORIZONTAL",
        "carrier_track_ids": ["HC1", "HC2"],
        "carrier_overlap_start": 20.0,
        "carrier_overlap_end": 220.0,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def horizontal_carrier_tracks() -> list[dict]:
    return [
        track("HC1", orientation="HORIZONTAL", centerline=90, start=20, end=220),
        track("HC2", orientation="HORIZONTAL", centerline=110, start=20, end=220),
    ]


def vertical_candidate() -> dict:
    geometry = {"x": 100.0, "y": 70.0, "width": 20.0, "height": 40.0}
    return {
        "marker_primitive_id": "R-V",
        "marker_geometry": dict(geometry),
        "source_marker_geometry": dict(geometry),
        "review_marker_geometry": dict(geometry),
        "carrier_orientation": "VERTICAL",
        "carrier_track_ids": ["VC1", "VC2"],
        "carrier_overlap_start": 20.0,
        "carrier_overlap_end": 160.0,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def vertical_carrier_tracks() -> list[dict]:
    return [
        track("VC1", orientation="VERTICAL", centerline=100, start=20, end=160),
        track("VC2", orientation="VERTICAL", centerline=120, start=20, end=160),
    ]


class TransverseBandSignatureTests(unittest.TestCase):
    def test_no_material_cross_side_traces_is_alone(self):
        result = describe_transverse_band(
            horizontal_candidate(), horizontal_carrier_tracks(), blank()
        )
        self.assertEqual(result["graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertEqual(result.get("side_reference"), "CARRIER_CROSS_AXIS")
        self.assertEqual(result["negative_side_count"], 0)
        self.assertEqual(result["positive_side_count"], 0)

    def test_two_above_and_two_below_primitive_traces_is_complete_double_band(self):
        tracks = horizontal_carrier_tracks() + [
            track("U1", orientation="VERTICAL", centerline=112, start=50, end=88),
            track("U2", orientation="VERTICAL", centerline=128, start=50, end=88),
            track("D1", orientation="VERTICAL", centerline=112, start=112, end=150),
            track("D2", orientation="VERTICAL", centerline=128, start=112, end=150),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_PLUS_DOUBLE_TRANSVERSE_BAND")
        self.assertEqual(result["negative_side_label"], "ABOVE")
        self.assertEqual(result["positive_side_label"], "BELOW")
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (2, 2))
        self.assertEqual(result["primitive_negative_track_ids"], ["U1", "U2"])
        self.assertEqual(result["primitive_positive_track_ids"], ["D1", "D2"])
        self.assertEqual(result["matched_cross_side_pair_count"], 2)

    def test_two_full_height_orthogonal_tracks_contribute_to_both_cross_sides(self):
        tracks = horizontal_carrier_tracks() + [
            track("X1", orientation="VERTICAL", centerline=112, start=50, end=150),
            track("X2", orientation="VERTICAL", centerline=128, start=50, end=150),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_PLUS_DOUBLE_TRANSVERSE_BAND")
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (2, 2))
        self.assertEqual(result["primitive_negative_track_ids"], ["X1", "X2"])
        self.assertEqual(result["primitive_positive_track_ids"], ["X1", "X2"])
        self.assertEqual(result["matched_cross_side_pair_count"], 2)

    def test_two_above_and_one_below_is_partial(self):
        tracks = horizontal_carrier_tracks() + [
            track("U1", orientation="VERTICAL", centerline=112, start=50, end=88),
            track("U2", orientation="VERTICAL", centerline=128, start=50, end=88),
            track("D1", orientation="VERTICAL", centerline=112, start=112, end=150),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_PLUS_PARTIAL_TRANSVERSE_TRACES")
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (2, 1))
        self.assertEqual(result["matched_cross_side_pair_count"], 1)

    def test_four_before_after_tracks_along_carrier_axis_do_not_qualify_cross_side_2_plus_2(self):
        tracks = horizontal_carrier_tracks() + [
            track("L1", orientation="VERTICAL", centerline=76, start=80, end=120),
            track("L2", orientation="VERTICAL", centerline=86, start=80, end=120),
            track("R1", orientation="VERTICAL", centerline=154, start=80, end=120),
            track("R2", orientation="VERTICAL", centerline=164, start=80, end=120),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertNotEqual(result["graphical_state"], "RECT_PLUS_DOUBLE_TRANSVERSE_BAND")
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (0, 0))

    def test_remote_cross_side_traces_outside_marker_longitudinal_neighborhood_are_ignored(self):
        tracks = horizontal_carrier_tracks() + [
            track("U_REMOTE", orientation="VERTICAL", centerline=45, start=50, end=88),
            track("D_REMOTE", orientation="VERTICAL", centerline=195, start=112, end=150),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertEqual(result["primitive_negative_track_ids"], [])
        self.assertEqual(result["primitive_positive_track_ids"], [])

    def test_duplicate_near_coincident_tracks_do_not_inflate_cross_side_count(self):
        tracks = horizontal_carrier_tracks() + [
            track("U1", orientation="VERTICAL", centerline=112.0, start=50, end=88),
            track("U1_DUP", orientation="VERTICAL", centerline=113.5, start=50, end=88),
            track("D1", orientation="VERTICAL", centerline=112.0, start=112, end=150),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (1, 1))
        self.assertEqual(result["graphical_state"], "RECT_PLUS_PARTIAL_TRANSVERSE_TRACES")

    def test_raster_two_above_and_two_below_is_preserved_separately_from_primitive_evidence(self):
        binary = blank()
        for x in (112, 128):
            draw_vertical(binary, x, 50, 88, width=2)
            draw_vertical(binary, x, 112, 150, width=2)
        result = describe_transverse_band(
            horizontal_candidate(), horizontal_carrier_tracks(), binary
        )
        self.assertEqual(result["graphical_state"], "RECT_PLUS_DOUBLE_TRANSVERSE_BAND")
        self.assertEqual(result["primitive_negative_track_ids"], [])
        self.assertEqual(result["primitive_positive_track_ids"], [])
        self.assertEqual(len(result["raster_negative_strokes"]), 2)
        self.assertEqual(len(result["raster_positive_strokes"]), 2)
        self.assertEqual(result["matched_cross_side_pair_count"], 2)
        self.assertEqual(result["evidence_sources"], ["RASTER_LOCAL_PROFILE"])

    def test_orthogonal_traces_confined_inside_carrier_band_do_not_count(self):
        tracks = horizontal_carrier_tracks() + [
            track("I1", orientation="VERTICAL", centerline=112, start=94, end=106),
            track("I2", orientation="VERTICAL", centerline=128, start=94, end=106),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (0, 0))

    def test_vertical_carrier_rotates_cross_side_labels_to_left_and_right(self):
        tracks = vertical_carrier_tracks() + [
            track("L1", orientation="HORIZONTAL", centerline=82, start=60, end=98),
            track("L2", orientation="HORIZONTAL", centerline=98, start=60, end=98),
            track("R1", orientation="HORIZONTAL", centerline=82, start=122, end=160),
            track("R2", orientation="HORIZONTAL", centerline=98, start=122, end=160),
        ]
        result = describe_transverse_band(vertical_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_PLUS_DOUBLE_TRANSVERSE_BAND")
        self.assertEqual(result["negative_side_label"], "LEFT")
        self.assertEqual(result["positive_side_label"], "RIGHT")
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (2, 2))
        self.assertEqual(result["matched_cross_side_pair_count"], 2)

    def test_reversed_tracks_are_byte_deterministic(self):
        tracks = horizontal_carrier_tracks() + [
            track("U1", orientation="VERTICAL", centerline=112, start=50, end=88),
            track("U2", orientation="VERTICAL", centerline=128, start=50, end=88),
            track("D1", orientation="VERTICAL", centerline=112, start=112, end=150),
            track("D2", orientation="VERTICAL", centerline=128, start=112, end=150),
        ]
        forward = describe_transverse_band(horizontal_candidate(), tracks, blank())
        reverse = describe_transverse_band(horizontal_candidate(), list(reversed(tracks)), blank())
        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
