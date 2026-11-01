from __future__ import annotations

import unittest

from cew_spiral.grammar_adapter import (
    ALLOWED_KNOWLEDGE_PROVENANCE,
    GRAMMAR_INVARIANTS,
    interpret_observation,
)


class GrammarAdapterContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = {
            "source_version_id": "CEW-N12-DXF01-TAV5",
            "sha256": "a" * 64,
            "evidence_region_id": "DXF01-OBS-0001",
            "stable_id": "DXF01-ENTITY-0001",
            "evidentiary_class": "HISTORICAL_DERIVED_EVIDENCE",
        }

    def authority_is_closed(self, result: dict) -> None:
        authority = result["authority"]
        self.assertEqual(authority["engineering_authority_effect"], "NONE")
        self.assertFalse(authority["structural_identity_authorized"])
        self.assertFalse(authority["canonical_geometry_authorized"])
        self.assertFalse(authority["canonical_write_authorized"])
        self.assertTrue(authority["human_review_required"])

    def test_ported_contract_preserves_invariants_and_provenance_classes(self) -> None:
        self.assertEqual(
            ALLOWED_KNOWLEDGE_PROVENANCE,
            {
                "PROJECT_LEARNED",
                "VERIFIED_REFERENCE",
                "METHOD_RULE",
                "HUMAN_TAUGHT_PROJECT_RULE",
            },
        )
        for invariant in {
            "RECTANGLE_DOES_NOT_IMPLY_COLUMN",
            "DIMENSION_REQUIRES_RELATION",
            "TOPOLOGY_OUTRANKS_VISUAL_PROXIMITY_FOR_IDENTITY",
            "CROSS_VIEW_CONFLICT_FAILS_CLOSED",
            "OCR_CONFIDENCE_IS_NOT_ENGINEERING_CONFIDENCE",
            "SOURCE_REMAINS_EVIDENTIARY_AUTHORITY",
        }:
            self.assertIn(invariant, GRAMMAR_INVARIANTS)

    def test_rectangle_alone_never_implies_column(self) -> None:
        result = interpret_observation(
            {
                "source": self.source,
                "primitive": "RECTANGULAR_ENVELOPE",
                "knowledge_provenance": "PROJECT_LEARNED",
            }
        )
        self.assertEqual(result["hypothesis"]["state"], "AMBIGUOUS_TECHNICAL_OBJECT_CANDIDATE")
        self.assertIsNone(result["hypothesis"].get("structural_type"))
        self.authority_is_closed(result)

    def test_dimension_without_target_relation_stays_unbound(self) -> None:
        result = interpret_observation(
            {
                "source": self.source,
                "token_type": "DIMENSION",
                "token": "30",
                "target_relation": None,
                "knowledge_provenance": "VERIFIED_REFERENCE",
            }
        )
        self.assertEqual(result["relation"]["state"], "DIMENSION_NEEDS_TARGET_RELATION")
        self.assertEqual(result["hypothesis"]["state"], "TECHNICAL_TOKEN_NEEDS_CONTEXT")
        self.authority_is_closed(result)

    def test_topology_outranks_visual_proximity_for_identity_proposal(self) -> None:
        result = interpret_observation(
            {
                "source": self.source,
                "relation_type": "IDENTITY_CANDIDATE",
                "visual_target_id": "COL-OCC-0001",
                "topology_target_id": "COL-OCC-0002",
                "knowledge_provenance": "METHOD_RULE",
            }
        )
        self.assertEqual(result["relation"]["preferred_target_id"], "COL-OCC-0002")
        self.assertEqual(result["hypothesis"]["state"], "IDENTITY_HYPOTHESIS_TOPOLOGY_PREFERRED_REVIEW")
        self.authority_is_closed(result)

    def test_ocr_confidence_never_becomes_engineering_confidence(self) -> None:
        result = interpret_observation(
            {
                "source": self.source,
                "token_type": "TEXT",
                "token": "13",
                "ocr_confidence": 0.99,
                "target_relation": None,
                "knowledge_provenance": "PROJECT_LEARNED",
            }
        )
        self.assertEqual(result["observation"]["ocr_confidence"], 0.99)
        self.assertNotIn("engineering_confidence", result["hypothesis"])
        self.assertEqual(result["hypothesis"]["state"], "TECHNICAL_TOKEN_NEEDS_CONTEXT")
        self.authority_is_closed(result)

    def test_cross_source_conflict_fails_closed(self) -> None:
        result = interpret_observation(
            {
                "source": self.source,
                "relation_type": "IDENTITY_CANDIDATE",
                "visual_target_id": "COL-OCC-0001",
                "topology_target_id": "COL-OCC-0001",
                "cross_source_conflict": True,
                "knowledge_provenance": "HUMAN_TAUGHT_PROJECT_RULE",
            }
        )
        self.assertEqual(result["hypothesis"]["state"], "CROSS_SOURCE_CONFLICT_REVIEW_REQUIRED")
        self.assertIsNone(result["hypothesis"].get("candidate_target_id"))
        self.authority_is_closed(result)

    def test_historical_dxf_remains_non_primary_and_non_promoting(self) -> None:
        result = interpret_observation(
            {
                "source": self.source,
                "token_type": "TEXT",
                "token": "P13",
                "target_relation": "INSIDE_CLOSED_FRAME",
                "knowledge_provenance": "VERIFIED_REFERENCE",
            }
        )
        self.assertEqual(result["source"]["evidentiary_class"], "HISTORICAL_DERIVED_EVIDENCE")
        self.assertFalse(result["authority"]["primary_source_identity_bridge"])
        self.authority_is_closed(result)

    def test_source_binding_and_provenance_are_mandatory(self) -> None:
        with self.assertRaisesRegex(ValueError, "SOURCE_BINDING_REQUIRED"):
            interpret_observation({"primitive": "RECTANGULAR_ENVELOPE", "knowledge_provenance": "PROJECT_LEARNED"})
        with self.assertRaisesRegex(ValueError, "KNOWLEDGE_PROVENANCE_INVALID"):
            interpret_observation({"source": self.source, "primitive": "RECTANGULAR_ENVELOPE", "knowledge_provenance": "UNTRACKED"})


if __name__ == "__main__":
    unittest.main()
