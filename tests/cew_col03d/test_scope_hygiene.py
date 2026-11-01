from __future__ import annotations

from pathlib import Path
import unittest


class Col03DScopeHygieneTests(unittest.TestCase):
    def test_temporary_raster_diagnostic_workflow_is_not_part_of_checkpoint(self):
        self.assertFalse(
            Path('.github/workflows/diagnose-cew-col03d-raster-source.yml').exists(),
            'temporary COL-03D raster diagnostic workflow must not ship in the recovery checkpoint',
        )


if __name__ == '__main__':
    unittest.main()
