from __future__ import annotations

import unittest

from experiments.cew_b01.marker_topology_repair import describe_transverse_band


def blank(width: int = 260, height: int = 180) -> list[list[bool]]:
    return [[False for _ in range(width)] for _ in range(height)]


def draw_vertical(binary: list[list[bool]], x: int, y0: int, y1: int, width: int = 1) -> None:
    for px in range(x, x + width):
        for y in range(y0, y1 + 1):
            binary[y][px] = True


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
        "marker_primitive_id": "R",
        "marker_geometry": dict(geometry),
        "source_marker_geometry": dict(geometry),
        "review_marker_geometry": dict(geometry),
        "carrier_orientation": "HORIZONTAL",
        "carrier_track_ids": ["C1", "C2"],
        "carrier_overlap_start": 20.0,
        "carrier_overlap_end": 220.0,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


def carrier_tracks() -> list[dict]:
    return [
        track("C1", orientation="HORIZONTAL", centerline=90, start=20, end=220),
        track("C2", orientation="HORIZONTAL", centerline=110, start=20, end=220),
    ]


class TransverseBandSignatureTests(unittest.TestCase):
    def test_no_material_transverse_traces_is_alone(self):
        result = describe_transverse_band(horizontal_candidate(), carrier_tracks(), blank())
        self.assertEqual(result["graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertEqual(result["negative_side_count"], 0)
        self.assertEqual(result["positive_side_count"], 0)

    def test_two_plus_two_primitive_traces_is_complete_double_band(self):
        tracks = carrier_tracks() + [
            track("N1", orientation="VERTICAL", centerline=76, start=80, end=120),
            track("N2", orientation="VERTICAL", centerline=86, start=80, end=120),
            track("P1", orientation="VERTICAL", centerline=154, start=80, end=120),
            track("P2", orientation="VERTICAL", centerline=164, start=80, end=120),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_PLUS_DOUBLE_TRANSVERSE_BAND")
        self.assertEqual(result["negative_side_count"], 2)
        self.assertEqual(result["positive_side_count"], 2)
        self.assertEqual(result["primitive_negative_track_ids"], ["N1", "N2"])
        self.assertEqual(result["primitive_positive_track_ids"], ["P1", "P2"])

    def test_one_plus_one_is_partial_not_complete(self):
        tracks = carrier_tracks() + [
            track("N1", orientation="VERTICAL", centerline=82, start=80, end=120),
            track("P1", orientation="VERTICAL", centerline=158, start=80, end=120),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_PLUS_PARTIAL_TRANSVERSE_TRACES")
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (1, 1))

    def test_two_plus_one_is_partial(self):
        tracks = carrier_tracks() + [
            track("N1", orientation="VERTICAL", centerline=76, start=80, end=120),
            track("N2", orientation="VERTICAL", centerline=86, start=80, end=120),
            track("P1", orientation="VERTICAL", centerline=158, start=80, end=120),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_PLUS_PARTIAL_TRANSVERSE_TRACES")
        self.assertEqual((result["negative_side_count"], result["positive_side_count"]), (2, 1))

    def test_remote_traces_are_not_counted_as_local_band(self):
        tracks = carrier_tracks() + [
            track("REMOTE_N", orientation="VERTICAL", centerline=10, start=80, end=120),
            track("REMOTE_P", orientation="VERTICAL", centerline=235, start=80, end=120),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["graphical_state"], "RECT_ALONE_ON_CARRIER")
        self.assertEqual(result["primitive_negative_track_ids"], [])
        self.assertEqual(result["primitive_positive_track_ids"], [])

    def test_duplicate_near_coincident_tracks_do_not_inflate_side_count(self):
        tracks = carrier_tracks() + [
            track("N1", orientation="VERTICAL", centerline=80.0, start=80, end=120),
            track("N1_DUP", orientation="VERTICAL", centerline=81.5, start=80, end=120),
            track("P1", orientation="VERTICAL", centerline=158.0, start=80, end=120),
        ]
        result = describe_transverse_band(horizontal_candidate(), tracks, blank())
        self.assertEqual(result["negative_side_count"], 1)
        self.assertEqual(result["positive_side_count"], 1)
        self.assertEqual(result["graphical_state"], "RECT_PLUS_PARTIAL_TRANSVERSE_TRACES")

    def test_raster_two_plus_two_is_preserved_separately_from_primitive_evidence(self):
        binary = blank()
        for x in (76, 86, 154, 164):
            draw_vertical(binary, x, 84, 116, width=2)
        result = describe_transverse_band(horizontal_candidate(), carrier_tracks(), binary)
        self.assertEqual(result["graphical_state"], "RECT_PLUS_DOUBLE_TRANSVERSE_BAND")
        self.assertEqual(result["primitive_negative_track_ids"], [])
        self.assertEqual(result["primitive_positive_track_ids"], [])
        self.assertEqual(len(result["raster_negative_strokes"]), 2)
        self.assertEqual(len(result["raster_positive_strokes"]), 2)
        self.assertEqual(result["evidence_sources"], ["RASTER_LOCAL_PROFILE"])

    def test_reversed_tracks_are_byte_deterministic(self):
        tracks = carrier_tracks() + [
            track("N1", orientation="VERTICAL", centerline=76, start=80, end=120),
            track("N2", orientation="VERTICAL", centerline=86, start=80, end=120),
            track("P1", orientation="VERTICAL", centerline=154, start=80, end=120),
            track("P2", orientation="VERTICAL", centerline=164, start=80, end=120),
        ]
        forward = describe_transverse_band(horizontal_candidate(), tracks, blank())
        reverse = describe_transverse_band(horizontal_candidate(), list(reversed(tracks)), blank())
        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
