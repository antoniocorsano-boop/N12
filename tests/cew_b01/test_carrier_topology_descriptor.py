from __future__ import annotations

import unittest

from experiments.cew_b01.marker_topology_repair import describe_carrier_topology


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


def candidate(
    *,
    orientation: str,
    geometry: dict,
    overlap_start: float,
    overlap_end: float,
    carrier_track_ids: list[str],
) -> dict:
    return {
        "marker_primitive_id": "R",
        "marker_geometry": dict(geometry),
        "source_marker_geometry": dict(geometry),
        "review_marker_geometry": dict(geometry),
        "carrier_orientation": orientation,
        "carrier_track_ids": carrier_track_ids,
        "carrier_overlap_start": overlap_start,
        "carrier_overlap_end": overlap_end,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
    }


class CarrierTopologyDescriptorTests(unittest.TestCase):
    def test_horizontal_through_carrier_is_through_continuous(self):
        item = candidate(
            orientation="HORIZONTAL",
            geometry={"x": 100, "y": 90, "width": 40, "height": 20},
            overlap_start=20,
            overlap_end=220,
            carrier_track_ids=["T1", "T2"],
        )
        tracks = [
            track("T1", orientation="HORIZONTAL", centerline=90, start=20, end=220),
            track("T2", orientation="HORIZONTAL", centerline=110, start=20, end=220),
        ]
        result = describe_carrier_topology(item, tracks)
        self.assertEqual(result["topology_state"], "THROUGH_CONTINUOUS")
        self.assertGreater(result["continuation_before_px"], 40)
        self.assertGreater(result["continuation_after_px"], 40)

    def test_vertical_through_carrier_is_not_rejected_by_orientation(self):
        item = candidate(
            orientation="VERTICAL",
            geometry={"x": 90, "y": 100, "width": 20, "height": 40},
            overlap_start=20,
            overlap_end=220,
            carrier_track_ids=["T1", "T2"],
        )
        tracks = [
            track("T1", orientation="VERTICAL", centerline=90, start=20, end=220),
            track("T2", orientation="VERTICAL", centerline=110, start=20, end=220),
        ]
        result = describe_carrier_topology(item, tracks)
        self.assertEqual(result["topology_state"], "THROUGH_CONTINUOUS")
        self.assertEqual(result["carrier_orientation"], "VERTICAL")

    def test_one_sided_local_termination_is_terminal_or_stem(self):
        item = candidate(
            orientation="HORIZONTAL",
            geometry={"x": 100, "y": 90, "width": 40, "height": 20},
            overlap_start=96,
            overlap_end=240,
            carrier_track_ids=["T1", "T2"],
        )
        tracks = [
            track("T1", orientation="HORIZONTAL", centerline=90, start=96, end=240),
            track("T2", orientation="HORIZONTAL", centerline=110, start=96, end=240),
        ]
        result = describe_carrier_topology(item, tracks)
        self.assertEqual(result["topology_state"], "TERMINAL_OR_STEM")
        self.assertLess(result["continuation_before_px"], 10)
        self.assertGreater(result["continuation_after_px"], 40)

    def test_material_end_junction_is_junction_complex(self):
        item = candidate(
            orientation="HORIZONTAL",
            geometry={"x": 100, "y": 90, "width": 40, "height": 20},
            overlap_start=20,
            overlap_end=220,
            carrier_track_ids=["T1", "T2"],
        )
        tracks = [
            track("T1", orientation="HORIZONTAL", centerline=90, start=20, end=220),
            track("T2", orientation="HORIZONTAL", centerline=110, start=20, end=220),
            track("J1", orientation="VERTICAL", centerline=98, start=70, end=130),
            track("J2", orientation="VERTICAL", centerline=102, start=70, end=130),
        ]
        result = describe_carrier_topology(item, tracks)
        self.assertEqual(result["topology_state"], "JUNCTION_COMPLEX")
        self.assertGreaterEqual(len(result["end_junction_track_ids"]), 2)

    def test_insufficient_continuation_without_terminal_asymmetry_is_ambiguous(self):
        item = candidate(
            orientation="HORIZONTAL",
            geometry={"x": 100, "y": 90, "width": 40, "height": 20},
            overlap_start=85,
            overlap_end=155,
            carrier_track_ids=["T1", "T2"],
        )
        tracks = [
            track("T1", orientation="HORIZONTAL", centerline=90, start=85, end=155),
            track("T2", orientation="HORIZONTAL", centerline=110, start=85, end=155),
        ]
        result = describe_carrier_topology(item, tracks)
        self.assertEqual(result["topology_state"], "AMBIGUOUS")

    def test_reversed_track_input_is_byte_deterministic(self):
        item = candidate(
            orientation="HORIZONTAL",
            geometry={"x": 100, "y": 90, "width": 40, "height": 20},
            overlap_start=20,
            overlap_end=220,
            carrier_track_ids=["T1", "T2"],
        )
        tracks = [
            track("T1", orientation="HORIZONTAL", centerline=90, start=20, end=220),
            track("T2", orientation="HORIZONTAL", centerline=110, start=20, end=220),
            track("J1", orientation="VERTICAL", centerline=98, start=70, end=130),
            track("J2", orientation="VERTICAL", centerline=102, start=70, end=130),
        ]
        self.assertEqual(describe_carrier_topology(item, tracks), describe_carrier_topology(item, list(reversed(tracks))))


if __name__ == "__main__":
    unittest.main()
