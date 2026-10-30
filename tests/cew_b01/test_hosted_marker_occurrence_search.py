from __future__ import annotations

import json
import unittest

from experiments.cew_b01.hosted_marker_occurrence_search import (
    analyze_hosted_marker_occurrences,
    discover_hosted_marker_occurrences,
    hosted_marker_signature,
    pair_evidence_overlay_spec,
    prototype_distance,
    rank_occurrences_for_review,
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


def vertical_stroke(binary: list[list[bool]], x0: int, x1: int, y0: int, y1: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            binary[y][x] = True


def ink_box(binary: list[list[bool]], x0: int, x1: int, y0: int, y1: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            binary[y][x] = True


def payload_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def review_candidate(
    pid: str,
    *,
    state: str = "RECT_ALONE_ON_CARRIER",
    x: float = 100.0,
    y: float = 200.0,
    width: float = 60.0,
    height: float = 40.0,
    carrier_orientation: str = "HORIZONTAL",
    carrier_separation: float = 50.0,
    carrier_overlap_length: float = 600.0,
    pair_centers: tuple[float, float] | None = None,
    transverse_pair_track_ids: list[str] | None = None,
) -> dict:
    raster = {
        "pair_detected": pair_centers is not None,
        "pair_strokes": (
            [{"center": pair_centers[0], "width": 4}, {"center": pair_centers[1], "width": 4}]
            if pair_centers is not None
            else []
        ),
        "cross_search_start": 150.0,
        "cross_search_end": 300.0,
    }
    primitive_pair_ids = list(transverse_pair_track_ids or [])
    sources = []
    if len(primitive_pair_ids) == 2:
        sources.append("PRIMITIVE_LOCAL_TRACK_PAIR")
    if pair_centers is not None:
        sources.append("RASTER_LOCAL_PROFILE")
    return {
        "hosted_marker_id": f"HM-{pid}",
        "marker_primitive_id": pid,
        "marker_geometry": {"x": x, "y": y, "width": width, "height": height},
        "carrier_id": f"LC-{pid}",
        "carrier_orientation": carrier_orientation,
        "carrier_separation": carrier_separation,
        "carrier_overlap_start": 0.0,
        "carrier_overlap_end": carrier_overlap_length,
        "transverse_pair_track_ids": primitive_pair_ids,
        "primitive_graphical_state": (
            "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE"
            if len(primitive_pair_ids) == 2
            else "RECT_ALONE_ON_CARRIER"
        ),
        "raster_transverse_evidence": raster,
        "pair_evidence_sources": sources,
        "graphical_state": state,
        "semantic_meaning": None,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
        "review_state": "UNREVIEWED",
    }


class HostedMarkerOccurrenceDiscoveryTests(unittest.TestCase):
    def _primitives(self) -> list[dict]:
        return [
            line("TOP", x=100, y=200, width=1000, height=2, orientation="HORIZONTAL"),
            line("BOTTOM", x=100, y=260, width=1000, height=2, orientation="HORIZONTAL"),
            rect("R_ALONE", x=420, y=208, width=60, height=46),
            rect("R_PAIR", x=620, y=208, width=60, height=46),
            rect("R_OUTSIDE", x=420, y=320, width=60, height=46),
            text_block("TEXT", x=500, y=210, width=50, height=20),
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
        forward = analyze_hosted_marker_occurrences(self._primitives(), self._binary())
        reverse = analyze_hosted_marker_occurrences(list(reversed(self._primitives())), self._binary())
        self.assertEqual(payload_bytes(forward), payload_bytes(reverse))

    def test_text_block_overlapping_marker_is_preserved_but_excluded_from_review_eligible(self):
        primitives = self._primitives() + [
            rect("R_TEXT", x=760, y=208, width=60, height=46),
            text_block("T_INSIDE", x=778, y=220, width=20, height=12),
        ]
        analysis = analyze_hosted_marker_occurrences(primitives, self._binary())
        self.assertNotIn("R_TEXT", [item["marker_primitive_id"] for item in analysis["review_eligible"]])
        rejected = {item["marker_primitive_id"]: item for item in analysis["annotation_dominated"]}
        self.assertIn("R_TEXT", rejected)
        self.assertEqual(rejected["R_TEXT"]["candidate_role"], "ANNOTATION_DOMINATED")
        self.assertEqual(rejected["R_TEXT"]["annotation_evidence"]["overlapping_text_block_ids"], ["T_INSIDE"])

    def test_enclosed_internal_ink_without_text_block_excludes_annotation_like_box(self):
        primitives = self._primitives() + [rect("R_INK", x=760, y=208, width=60, height=46)]
        binary = self._binary()
        # Two compact components fully enclosed in the marker mimic a numeric annotation.
        ink_box(binary, 775, 780, 222, 235)
        ink_box(binary, 790, 797, 220, 236)
        analysis = analyze_hosted_marker_occurrences(primitives, binary)
        self.assertNotIn("R_INK", [item["marker_primitive_id"] for item in analysis["review_eligible"]])
        rejected = {item["marker_primitive_id"]: item for item in analysis["annotation_dominated"]}
        self.assertGreaterEqual(rejected["R_INK"]["annotation_evidence"]["enclosed_component_count"], 2)
        self.assertGreater(rejected["R_INK"]["annotation_evidence"]["enclosed_component_area"], 0)

    def test_border_crossing_pair_strokes_do_not_count_as_enclosed_annotation_ink(self):
        primitives = self._primitives()
        analysis = analyze_hosted_marker_occurrences(primitives, self._binary())
        pair = {item["marker_primitive_id"]: item for item in analysis["review_eligible"]}["R_PAIR"]
        self.assertEqual(pair["annotation_evidence"]["enclosed_component_count"], 0)
        self.assertEqual(pair["candidate_role"], "REVIEW_ELIGIBLE")


class HostedMarkerOccurrenceOverlayTests(unittest.TestCase):
    def test_primitive_only_pair_emits_two_overlay_tracks_even_without_raster_pair(self):
        candidate = review_candidate(
            "P",
            state="RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE",
            pair_centers=None,
            transverse_pair_track_ids=["T1", "T2"],
        )
        tracks = [
            {"track_id": "T1", "orientation": "VERTICAL", "centerline": 125.0, "start": 150.0, "end": 300.0},
            {"track_id": "T2", "orientation": "VERTICAL", "centerline": 150.0, "start": 150.0, "end": 300.0},
        ]
        overlays = pair_evidence_overlay_spec(candidate, tracks)
        primitive = [item for item in overlays if item["source"] == "PRIMITIVE_LOCAL_TRACK_PAIR"]
        raster = [item for item in overlays if item["source"] == "RASTER_LOCAL_PROFILE"]
        self.assertEqual(len(primitive), 2)
        self.assertEqual(raster, [])

    def test_mixed_pair_preserves_primitive_and_raster_provenance_separately(self):
        candidate = review_candidate(
            "P",
            state="RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE",
            pair_centers=(130.0, 160.0),
            transverse_pair_track_ids=["T1", "T2"],
        )
        tracks = [
            {"track_id": "T1", "orientation": "VERTICAL", "centerline": 125.0, "start": 150.0, "end": 300.0},
            {"track_id": "T2", "orientation": "VERTICAL", "centerline": 150.0, "start": 150.0, "end": 300.0},
        ]
        overlays = pair_evidence_overlay_spec(candidate, tracks)
        self.assertEqual([item["source"] for item in overlays].count("PRIMITIVE_LOCAL_TRACK_PAIR"), 2)
        self.assertEqual([item["source"] for item in overlays].count("RASTER_LOCAL_PROFILE"), 2)


class HostedMarkerOccurrenceRankingTests(unittest.TestCase):
    def test_scale_equivalent_geometry_has_zero_prototype_distance(self):
        prototype = review_candidate(
            "P",
            width=60,
            height=40,
            carrier_separation=50,
            carrier_overlap_length=600,
        )
        scaled = review_candidate(
            "S",
            width=120,
            height=80,
            carrier_separation=100,
            carrier_overlap_length=1200,
        )
        self.assertAlmostEqual(
            prototype_distance(hosted_marker_signature(scaled), hosted_marker_signature(prototype)),
            0.0,
            places=9,
        )

    def test_distorted_carrier_separation_ranks_farther_than_scale_equivalent_copy(self):
        prototype = review_candidate("P", carrier_separation=50)
        equivalent = review_candidate("E", carrier_separation=50)
        distorted = review_candidate("D", carrier_separation=100)
        p_sig = hosted_marker_signature(prototype)
        self.assertLess(
            prototype_distance(hosted_marker_signature(equivalent), p_sig),
            prototype_distance(hosted_marker_signature(distorted), p_sig),
        )

    def test_pair_separation_metric_is_optional_and_compared_only_when_shared(self):
        pair_state = "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE"
        prototype = review_candidate("P", state=pair_state, pair_centers=(120.0, 150.0))
        primitive_only_pair = review_candidate("G1", state=pair_state, pair_centers=None)
        signature = hosted_marker_signature(primitive_only_pair)
        self.assertNotIn("raster_pair_separation_to_marker_long_span", signature)
        self.assertGreaterEqual(
            prototype_distance(signature, hosted_marker_signature(prototype)),
            0.0,
        )

    def test_ranking_uses_same_state_prototype_and_excludes_prototype_ids(self):
        alone = review_candidate("C5", state="RECT_ALONE_ON_CARRIER")
        pair = review_candidate(
            "C7",
            state="RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE",
            pair_centers=(120.0, 150.0),
        )
        a1 = review_candidate("A1", state="RECT_ALONE_ON_CARRIER")
        p1 = review_candidate(
            "P1",
            state="RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE",
            pair_centers=(120.0, 150.0),
        )
        ranked = rank_occurrences_for_review(
            [pair, a1, alone, p1],
            {
                "RECT_ALONE_ON_CARRIER": alone,
                "RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE": pair,
            },
        )
        self.assertEqual({item["marker_primitive_id"] for item in ranked}, {"A1", "P1"})
        by_id = {item["marker_primitive_id"]: item for item in ranked}
        self.assertEqual(by_id["A1"]["prototype_marker_primitive_id"], "C5")
        self.assertEqual(by_id["P1"]["prototype_marker_primitive_id"], "C7")
        self.assertEqual(by_id["A1"]["review_state"], "UNREVIEWED")
        self.assertEqual(by_id["P1"]["review_state"], "UNREVIEWED")

    def test_equal_distance_order_is_deterministic_by_geometry_then_primitive_id(self):
        prototype = review_candidate("C5")
        b = review_candidate("B", x=200)
        a = review_candidate("A", x=100)
        c = review_candidate("C", x=100)
        forward = rank_occurrences_for_review(
            [b, c, a, prototype],
            {"RECT_ALONE_ON_CARRIER": prototype},
        )
        reverse = rank_occurrences_for_review(
            [prototype, a, c, b],
            {"RECT_ALONE_ON_CARRIER": prototype},
        )
        self.assertEqual(payload_bytes(forward), payload_bytes(reverse))
        self.assertEqual([item["marker_primitive_id"] for item in forward], ["A", "C", "B"])


if __name__ == "__main__":
    unittest.main()
