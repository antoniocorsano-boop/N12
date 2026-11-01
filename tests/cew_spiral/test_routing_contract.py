from __future__ import annotations

import unittest

from cew_spiral.router import route_next_residual


class SpiralRoutingContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authority = {
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "m0g_authorized": False,
        }

    def test_source_native_route_precedes_ocr_for_same_residual(self) -> None:
        decision = route_next_residual(
            [
                {
                    "residual_id": "R-001",
                    "blocker_class": "MODEL_RELATION",
                    "model_impact": 8,
                    "acquisition_cost_class": "LOW",
                    "evidence": {
                        "qualified_source_native_available": True,
                        "governed_raster_available": True,
                        "historical_only": False,
                    },
                }
            ],
            authority=self.authority,
        )
        self.assertEqual(decision["selected_residual_id"], "R-001")
        self.assertEqual(decision["route"], "QUALIFIED_SOURCE_NATIVE")

    def test_missing_vector_falls_back_to_governed_raster(self) -> None:
        decision = route_next_residual(
            [
                {
                    "residual_id": "R-002",
                    "blocker_class": "MODEL_RELATION",
                    "model_impact": 7,
                    "acquisition_cost_class": "MEDIUM",
                    "evidence": {
                        "qualified_source_native_available": False,
                        "governed_raster_available": True,
                        "historical_only": False,
                    },
                }
            ],
            authority=self.authority,
        )
        self.assertEqual(decision["route"], "GOVERNED_RASTER_OCR")

    def test_historical_only_primary_identity_claim_remains_blocked(self) -> None:
        decision = route_next_residual(
            [
                {
                    "residual_id": "R-ID",
                    "blocker_class": "MODEL_RELATION",
                    "model_impact": 10,
                    "acquisition_cost_class": "LOW",
                    "primary_identity_required": True,
                    "evidence": {
                        "qualified_source_native_available": True,
                        "governed_raster_available": True,
                        "historical_only": True,
                    },
                }
            ],
            authority=self.authority,
        )
        self.assertEqual(decision["state"], "BLOCKED_NEEDS_PRIMARY_OR_MANUAL_EVIDENCE")
        self.assertEqual(decision["route"], "MANUAL_OR_NEW_PRIMARY_EVIDENCE")
        self.assertFalse(decision["promotion_authorized"])

    def test_priority_is_model_relation_then_impact_then_evidence_then_cost_then_id(self) -> None:
        residuals = [
            {
                "residual_id": "R-PROP-HIGH",
                "blocker_class": "PROPERTY",
                "model_impact": 100,
                "acquisition_cost_class": "LOW",
                "evidence": {"qualified_source_native_available": True, "governed_raster_available": True, "historical_only": False},
            },
            {
                "residual_id": "R-REL-LOW",
                "blocker_class": "MODEL_RELATION",
                "model_impact": 5,
                "acquisition_cost_class": "LOW",
                "evidence": {"qualified_source_native_available": True, "governed_raster_available": True, "historical_only": False},
            },
            {
                "residual_id": "R-REL-HIGH-B",
                "blocker_class": "MODEL_RELATION",
                "model_impact": 9,
                "acquisition_cost_class": "LOW",
                "evidence": {"qualified_source_native_available": False, "governed_raster_available": True, "historical_only": False},
            },
            {
                "residual_id": "R-REL-HIGH-A",
                "blocker_class": "MODEL_RELATION",
                "model_impact": 9,
                "acquisition_cost_class": "HIGH",
                "evidence": {"qualified_source_native_available": True, "governed_raster_available": True, "historical_only": False},
            },
        ]
        decision = route_next_residual(residuals, authority=self.authority)
        self.assertEqual(decision["selected_residual_id"], "R-REL-HIGH-A")
        self.assertEqual(decision["route"], "QUALIFIED_SOURCE_NATIVE")


if __name__ == "__main__":
    unittest.main()
