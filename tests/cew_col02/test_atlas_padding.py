from __future__ import annotations

import unittest

import numpy as np

from experiments.cew_col02.exact_source_audit import _pad_panel_to_width


class AtlasPaddingTests(unittest.TestCase):
    def test_colour_panel_padding_is_white_in_all_channels(self) -> None:
        panel = np.zeros((2, 2, 3), dtype=np.uint8)
        padded = _pad_panel_to_width(panel, 4)
        self.assertEqual(padded.shape, (2, 4, 3))
        self.assertTrue(np.all(padded[:, 2:, :] == 255))

    def test_panel_already_at_width_is_unchanged(self) -> None:
        panel = np.zeros((2, 4, 3), dtype=np.uint8)
        padded = _pad_panel_to_width(panel, 4)
        self.assertTrue(np.array_equal(padded, panel))


if __name__ == "__main__":
    unittest.main()
