from __future__ import annotations

import copy
import unittest

from cew_spiral.router import route_next_residual


class SpiralAuthorityBoundaryTests(unittest.TestCase):
    def test_router_preserves_authority_snapshot_exactly(self) -> None:
        authority = {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
            "engineering_authority_effect": "NONE",
        }
        before = copy.deepcopy(authority)
        decision = route_next_residual(
            [
                {
                    "residual_id": "R-001",
                    "blocker_class": "PROPERTY",
                    "model_impact": 1,
                    "acquisition_cost_class": "LOW",
                    "evidence": {"qualified_source_native_available": True, "governed_raster_available": False, "historical_only": False},
                }
            ],
            authority=authority,
        )
        self.assertEqual(authority, before)
        self.assertEqual(decision["authority_before"], before)
        self.assertEqual(decision["authority_after"], before)
        self.assertFalse(decision["promotion_authorized"])

    def test_router_rejects_pre_authorized_mutation_request(self) -> None:
        with self.assertRaisesRegex(ValueError, "ROUTER_AUTHORITY_ESCALATION_FORBIDDEN"):
            route_next_residual(
                [
                    {
                        "residual_id": "R-001",
                        "blocker_class": "PROPERTY",
                        "model_impact": 1,
                        "acquisition_cost_class": "LOW",
                        "evidence": {"qualified_source_native_available": True, "governed_raster_available": False, "historical_only": False},
                    }
                ],
                authority={"canonical_write_authorized": True},
            )


if __name__ == "__main__":
    unittest.main()
