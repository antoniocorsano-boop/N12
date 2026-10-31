from __future__ import annotations

import unittest
from unittest import mock

import cv2
import numpy as np

import experiments.cew_col02.axis_aware_local_envelope as local_envelope
from experiments.cew_col02.axis_aware_local_envelope import reconstruct_local_axis_envelope


class LocalAxisEnvelopeTests(unittest.TestCase):
    def test_external_axis_continuation_selects_whole_symbol_over_shifted_partial_envelope(self) -> None:
        image = np.full((500, 700), 255, dtype=np.uint8)

        # True whole column symbol: 320 x 80, crossed by page-scale axes.
        cv2.rectangle(image, (200, 220), (520, 300), 0, 3)
        cv2.line(image, (30, 260), (670, 260), 0, 2)
        cv2.line(image, (360, 20), (360, 480), 0, 2)

        # Competing shifted envelope above the symbol. It is locally four-sided,
        # but its interior horizontal line at y=220 is only the finite top border
        # of the real symbol: it does not continue beyond x=200..520.
        cv2.line(image, (200, 160), (520, 160), 0, 3)
        cv2.line(image, (200, 160), (200, 260), 0, 3)
        cv2.line(image, (520, 160), (520, 260), 0, 3)

        seed = {
            "x": 360 / 700,
            "y": 220 / 500,
            "width": 160 / 700,
            "height": 40 / 500,
        }
        result = reconstruct_local_axis_envelope(image, seed)

        self.assertIsNotNone(result)
        assert result is not None
        bbox = result["bbox"]
        self.assertAlmostEqual(bbox["x"], 200 / 700, delta=0.012)
        self.assertAlmostEqual(bbox["y"], 220 / 500, delta=0.018)
        self.assertAlmostEqual(bbox["width"], 320 / 700, delta=0.018)
        self.assertAlmostEqual(bbox["height"], 80 / 500, delta=0.025)
        self.assertAlmostEqual(result["axis_cross"]["x"], 360 / 700, delta=0.012)
        self.assertAlmostEqual(result["axis_cross"]["y"], 260 / 500, delta=0.018)

    def test_finite_internal_boundary_is_not_accepted_as_horizontal_axis(self) -> None:
        image = np.full((400, 600), 255, dtype=np.uint8)
        cv2.rectangle(image, (180, 150), (420, 250), 0, 3)
        cv2.line(image, (300, 40), (300, 360), 0, 2)
        # Finite internal line, intentionally not continuing outside the box.
        cv2.line(image, (180, 200), (420, 200), 0, 2)

        seed = {
            "x": 300 / 600,
            "y": 150 / 400,
            "width": 120 / 600,
            "height": 50 / 400,
        }
        result = reconstruct_local_axis_envelope(image, seed)
        self.assertIsNone(result)

    def test_high_resolution_thin_symbol_is_localized_before_any_downsampling(self) -> None:
        image = np.full((2400, 1800), 255, dtype=np.uint8)

        # R01-like geometry: a thin whole symbol on a large page, crossed by
        # orthogonal axes and cluttered by darker annotations. The line tone is
        # deliberately distinct from the text but dark enough to make the test
        # stable across supported OpenCV threshold implementations.
        x, y, width, height = 1400, 1500, 100, 113
        cv2.rectangle(image, (x, y), (x + width, y + height), 160, 1, cv2.LINE_AA)
        cv2.line(image, (x - 300, y + 49), (x + width + 300, y + 49), 160, 1, cv2.LINE_AA)
        cv2.line(image, (x + 38, y - 400), (x + 38, y + height + 400), 160, 1, cv2.LINE_AA)
        cv2.putText(image, "6", (x + 35, y + 75), cv2.FONT_HERSHEY_SIMPLEX, 1.0, 0, 1, cv2.LINE_AA)
        cv2.putText(image, "40", (x + width - 5, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 1, cv2.LINE_AA)

        seed = {
            "x": (x + 20) / 1800,
            "y": y / 2400,
            "width": 90 / 1800,
            "height": 120 / 2400,
        }
        result = reconstruct_local_axis_envelope(image, seed)

        self.assertIsNotNone(result)
        assert result is not None
        bbox = result["bbox"]
        self.assertAlmostEqual(bbox["x"], x / 1800, delta=0.004)
        self.assertAlmostEqual(bbox["y"], y / 2400, delta=0.004)
        self.assertAlmostEqual(bbox["width"], width / 1800, delta=0.004)
        self.assertAlmostEqual(bbox["height"], height / 2400, delta=0.004)

    def test_large_source_retries_legacy_half_scale_only_after_native_failure(self) -> None:
        image = np.full((2400, 1800), 255, dtype=np.uint8)
        seed = {"x": 0.50, "y": 0.45, "width": 0.02, "height": 0.01}
        legacy_result = {
            "bbox": {"x": 0.49, "y": 0.44, "width": 0.04, "height": 0.02},
            "detector": "LOCAL_AXIS_AWARE_FOUR_SIDE_ENVELOPE_REPAIR",
        }

        single_scale = getattr(local_envelope, "_reconstruct_local_axis_envelope_single_scale", None)
        self.assertTrue(callable(single_scale), "single-scale detector seam is missing")
        with mock.patch.object(
            local_envelope,
            "_reconstruct_local_axis_envelope_single_scale",
            side_effect=[None, legacy_result],
        ) as detector:
            result = reconstruct_local_axis_envelope(image, seed)

        self.assertEqual(detector.call_count, 2)
        native_call, legacy_call = detector.call_args_list
        self.assertEqual(native_call.args[0].shape, (2400, 1800))
        self.assertEqual(native_call.kwargs["margin_floor"], 180)
        self.assertEqual(native_call.kwargs["margin_cap"], 840)
        self.assertEqual(legacy_call.args[0].shape, (1200, 900))
        self.assertEqual(legacy_call.kwargs["margin_floor"], 90)
        self.assertEqual(legacy_call.kwargs["margin_cap"], 420)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["bbox"], legacy_result["bbox"])
        self.assertEqual(result["detector"], "LOCAL_AXIS_AWARE_FOUR_SIDE_ENVELOPE_REPAIR_HALF_SCALE_FALLBACK")
        self.assertEqual(result["analysis_scale_factor"], 0.5)

    def test_nested_selection_keeps_outer_envelope_when_smaller_top_edge_is_weaker(self) -> None:
        selector = getattr(local_envelope, "_select_plausible_envelope", None)
        self.assertTrue(callable(selector), "bounded nested-envelope selector seam is missing")
        assert callable(selector)

        outer = {
            "score": 0.90,
            "box": (10, 10, 100, 80),
            "coverage": {"left": 0.98, "right": 0.97, "top": 0.96, "bottom": 0.98},
        }
        internal_top = {
            "score": 0.87,
            "box": (10, 25, 100, 65),
            "coverage": {"left": 1.0, "right": 1.0, "top": 0.52, "bottom": 1.0},
        }

        chosen = selector([internal_top, outer])
        self.assertIs(chosen, outer)

    def test_nested_selection_collapses_lower_overshoot_when_smaller_boundary_is_not_weaker(self) -> None:
        selector = getattr(local_envelope, "_select_plausible_envelope", None)
        self.assertTrue(callable(selector), "bounded nested-envelope selector seam is missing")
        assert callable(selector)

        overshoot = {
            "score": 0.90,
            "box": (10, 10, 100, 100),
            "coverage": {"left": 0.90, "right": 0.96, "top": 1.0, "bottom": 0.84},
        }
        true_envelope = {
            "score": 0.87,
            "box": (10, 10, 100, 80),
            "coverage": {"left": 0.94, "right": 0.96, "top": 1.0, "bottom": 0.92},
        }

        chosen = selector([overshoot, true_envelope])
        self.assertIs(chosen, true_envelope)

    def test_nested_selection_still_fails_closed_for_non_nested_plausible_envelopes(self) -> None:
        selector = getattr(local_envelope, "_select_plausible_envelope", None)
        self.assertTrue(callable(selector), "bounded nested-envelope selector seam is missing")
        assert callable(selector)

        first = {
            "score": 0.90,
            "box": (10, 10, 100, 80),
            "coverage": {"left": 0.95, "right": 0.95, "top": 0.95, "bottom": 0.95},
        }
        competing = {
            "score": 0.87,
            "box": (40, 10, 100, 80),
            "coverage": {"left": 0.96, "right": 0.96, "top": 0.96, "bottom": 0.96},
        }

        self.assertIsNone(selector([first, competing]))

    def test_composite_projection_band_exposes_edge_boundary_hypotheses(self) -> None:
        variants = getattr(local_envelope, "_boundary_band_variants", None)
        self.assertTrue(callable(variants), "composite boundary-band variant seam is missing")
        assert callable(variants)

        ordinary = {"position": 20, "start": 18, "end": 22, "support": 50}
        composite = {"position": 40, "start": 30, "end": 45, "support": 80}
        rows = variants([ordinary, composite], line_run=10)

        self.assertEqual([row["position"] for row in rows], [20, 30, 40, 45])
        self.assertEqual(ordinary, {"position": 20, "start": 18, "end": 22, "support": 50})
        self.assertEqual(composite, {"position": 40, "start": 30, "end": 45, "support": 80})

    def test_bilateral_external_axis_continuation_bridges_interior_axis_gap(self) -> None:
        image = np.full((500, 700), 255, dtype=np.uint8)

        # Complete rectangular symbol with a horizontal structural axis.
        cv2.rectangle(image, (200, 220), (520, 300), 0, 3)
        cv2.line(image, (30, 260), (670, 260), 0, 2)

        # The vertical structural axis is collinear above and below the symbol,
        # but deliberately interrupted inside it. This models the exact-source
        # WSR-003 failure class: bilateral continuation is the graphical evidence
        # that must permit bounded axis-gap bridging without inventing identity.
        cv2.line(image, (360, 20), (360, 216), 0, 2)
        cv2.line(image, (360, 304), (360, 480), 0, 2)

        seed = {
            "x": 360 / 700,
            "y": 220 / 500,
            "width": 160 / 700,
            "height": 40 / 500,
        }
        result = reconstruct_local_axis_envelope(image, seed)

        self.assertIsNotNone(result)
        assert result is not None
        bbox = result["bbox"]
        self.assertAlmostEqual(bbox["x"], 200 / 700, delta=0.012)
        self.assertAlmostEqual(bbox["y"], 220 / 500, delta=0.018)
        self.assertAlmostEqual(bbox["width"], 320 / 700, delta=0.018)
        self.assertAlmostEqual(bbox["height"], 80 / 500, delta=0.025)
        self.assertGreater(result["axis_external_continuation"]["vertical"]["above"], 0.20)
        self.assertGreater(result["axis_external_continuation"]["vertical"]["below"], 0.20)

    def test_boundary_edge_variant_cannot_reuse_the_selected_axis_band(self) -> None:
        guard = getattr(local_envelope, "_boundary_reuses_axis_band", None)
        self.assertTrue(callable(guard), "axis-band boundary reuse guard seam is missing")
        assert callable(guard)

        axis_band = {"position": 40, "start": 30, "end": 45, "support": 80}
        edge_variant = {
            "position": 30,
            "start": 30,
            "end": 45,
            "support": 80,
            "boundary_variant": "start",
        }
        independent_boundary = {
            "position": 18,
            "start": 16,
            "end": 20,
            "support": 70,
            "boundary_variant": "peak",
        }

        self.assertTrue(guard(edge_variant, axis_band))
        self.assertFalse(guard(independent_boundary, axis_band))

    def test_near_duplicate_prefers_stronger_boundary_then_peak_origin(self) -> None:
        deduplicate = getattr(local_envelope, "_deduplicate_envelope_candidates", None)
        self.assertTrue(callable(deduplicate), "evidence-aware candidate deduplication seam is missing")
        assert callable(deduplicate)

        edge_variant = {
            "score": 0.94,
            "box": (10, 8, 100, 82),
            "coverage": {"left": 1.0, "right": 1.0, "top": 1.0, "bottom": 1.0},
            "boundary_variant_count": 1,
        }
        peak_candidate = {
            "score": 0.90,
            "box": (10, 10, 100, 80),
            "coverage": {"left": 1.0, "right": 1.0, "top": 1.0, "bottom": 1.0},
            "boundary_variant_count": 0,
        }
        rows = deduplicate([edge_variant, peak_candidate])
        self.assertEqual(len(rows), 1)
        self.assertIs(rows[0], peak_candidate)

        weak_peak = {
            "score": 0.96,
            "box": (10, 10, 100, 84),
            "coverage": {"left": 0.90, "right": 0.96, "top": 1.0, "bottom": 0.84},
            "boundary_variant_count": 0,
        }
        strong_edge = {
            "score": 0.92,
            "box": (10, 10, 100, 80),
            "coverage": {"left": 1.0, "right": 1.0, "top": 1.0, "bottom": 1.0},
            "boundary_variant_count": 1,
        }
        rows = deduplicate([weak_peak, strong_edge])
        self.assertEqual(len(rows), 1)
        self.assertIs(rows[0], strong_edge)


if __name__ == "__main__":
    unittest.main()
