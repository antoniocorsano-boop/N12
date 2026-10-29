from __future__ import annotations

import unittest

import numpy as np

from cew_b01 import document_zoning


class DocumentZoningRefinementTests(unittest.TestCase):
    def test_refinement_recovers_dense_title_edge_without_absorbing_page_margin(self) -> None:
        ink = np.zeros((400, 640), dtype=np.uint8)
        # Synthetic document-function region begins inside the coarse grid cell.
        # The coarse proposal intentionally starts too low at y=75.
        ink[52:151, 5:251] = 255
        refined = document_zoning._refine_title_block_bbox(
            ink,
            (0, 75, 280, 100),
        )
        x, y, width, height = refined
        self.assertGreater(y, 0)
        self.assertLessEqual(y, 52)
        self.assertGreaterEqual(y + height, 151)
        self.assertLessEqual(x, 5)
        self.assertGreaterEqual(x + width, 251)


if __name__ == "__main__":
    unittest.main()
