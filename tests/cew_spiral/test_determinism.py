from __future__ import annotations

import unittest

from cew_spiral.router import route_next_residual


class SpiralDeterminismTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
        }

    def test_same_inputs_replay_to_same_decision(self) -> None:
        residuals = [
            {
                "residual_id": "R-B",
                "blocker_class": "MODEL_RELATION",
                "model_impact": 5,
                "acquisition_cost_class": "LOW",
                "evidence": {"qualified_source_native_available": True, "governed_raster_available": True, "historical_only": False},
            },
            {
                "residual_id": "R-A",
                "blocker_class": "MODEL_RELATION",
                "model_impact": 5,
                "acquisition_cost_class": "LOW",
                "evidence": {"qualified_source_native_available": True, "governed_raster_available": True, "historical_only": False},
            },
        ]
        first = route_next_residual(residuals, authority=self.authority)
        second = route_next_residual(list(reversed(residuals)), authority=self.authority)
        self.assertEqual(first, second)
        self.assertEqual(first["selected_residual_id"], "R-A")


if __name__ == "__main__":
    unittest.main()
