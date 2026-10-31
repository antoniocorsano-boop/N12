from __future__ import annotations

import unittest

import cv2
import numpy as np

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

        # R01-like geometry: a thin, light whole symbol on a large page, crossed
        # by orthogonal axes and partially cluttered by darker annotations. The
        # local geometry is recoverable at source resolution but is lost when
        # the whole page is halved before the local crop is extracted.
        x, y, width, height = 1400, 1500, 100, 113
        cv2.rectangle(image, (x, y), (x + width, y + height), 200, 1, cv2.LINE_AA)
        cv2.line(image, (x - 300, y + 49), (x + width + 300, y + 49), 200, 1, cv2.LINE_AA)
        cv2.line(image, (x + 38, y - 400), (x + 38, y + height + 400), 200, 1, cv2.LINE_AA)
        cv2.putText(image, "6", (x + 35, y + 75), cv2.FONT_HERSHEY_SIMPLEX, 1.0, 0, 1, cv2.LINE_AA)
        cv2.putText(image, "40", (x + width - 5, y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 1, cv2.LINE_AA)

        seed = {
            "x": (x + 30) / 1800,
            "y": (y - 10) / 2400,
            "width": 80 / 1800,
            "height": (height + 20) / 2400,
        }
        result = reconstruct_local_axis_envelope(image, seed)

        self.assertIsNotNone(result)
        assert result is not None
        bbox = result["bbox"]
        self.assertAlmostEqual(bbox["x"], x / 1800, delta=0.004)
        self.assertAlmostEqual(bbox["y"], y / 2400, delta=0.004)
        self.assertAlmostEqual(bbox["width"], width / 1800, delta=0.004)
        self.assertAlmostEqual(bbox["height"], height / 2400, delta=0.004)


if __name__ == "__main__":
    unittest.main()
