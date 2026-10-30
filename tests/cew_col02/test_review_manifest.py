from __future__ import annotations

import unittest

from experiments.cew_col02.review_export import build_review_manifest_entry


class ReviewManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = {
            "source_version_id": "SRC-TAV05S",
            "page_id": "PAGE-001",
            "page_transform_id": "PX-NORMALIZED",
            "sha256": "a" * 64,
        }
        self.candidate = {
            "occurrence_candidate_id": "COL02-FP-0001",
            "bbox": {"x": 0.1, "y": 0.2, "width": 0.03, "height": 0.11},
            "detector": "LONG_AXIS_SUPPRESSED",
            "score": 0.91,
            "axis_evidence_present": False,
        }
        self.binding = {
            "binding_state": "ONE_INTERNAL_TEXT",
            "internal_token_ids": ["TXT-001"],
            "preferred_internal_token_id": "TXT-001",
            "bindings": [
                {
                    "token_id": "TXT-001",
                    "raw_text": "18",
                    "bbox": {"x": 0.11, "y": 0.23, "width": 0.005, "height": 0.004},
                    "relation": "INSIDE_FOOTPRINT",
                    "intersection_area": 0.00002,
                    "text_contained_fraction": 1.0,
                    "center_in_footprint": True,
                    "normalized_center_distance": 0.10,
                    "edge_distance": 0.0,
                    "normalized_edge_distance": 0.0,
                    "preferred_internal_text": True,
                    "support_identity_authorized": False,
                    "structural_identity_authorized": False,
                    "canonical_write_authorized": False,
                }
            ],
        }

    def test_manifest_keeps_column_and_text_decisions_independent(self) -> None:
        entry = build_review_manifest_entry(
            panel_id="R01",
            candidate=self.candidate,
            text_binding=self.binding,
            source=self.source,
            source_only_crop="review/r01-source-only.png",
            overlay_crop="review/r01-overlay.png",
        )
        self.assertEqual(entry["panel_id"], "R01")
        self.assertEqual(entry["candidate_id"], "COL02-FP-0001")
        self.assertEqual(entry["footprint_bbox"], self.candidate["bbox"])
        self.assertEqual(entry["preferred_internal_token_id"], "TXT-001")
        self.assertEqual(entry["text_bindings"][0]["relation"], "INSIDE_FOOTPRINT")
        self.assertEqual(entry["column_graphic_decision"], "PENDING_HUMAN_REVIEW")
        self.assertEqual(entry["text_binding_decision"], "PENDING_HUMAN_REVIEW")
        self.assertNotEqual(entry["column_graphic_decision"], "INTERNAL_TEXT_BINDING_CONFIRMED")

    def test_manifest_preserves_target_and_source_provenance(self) -> None:
        entry = build_review_manifest_entry(
            panel_id="R02",
            candidate=self.candidate,
            text_binding=self.binding,
            source=self.source,
            source_only_crop="review/r02-source-only.png",
            overlay_crop="review/r02-overlay.png",
        )
        self.assertEqual(entry["source"], self.source)
        self.assertEqual(entry["source_only_crop"], "review/r02-source-only.png")
        self.assertEqual(entry["overlay_crop"], "review/r02-overlay.png")
        self.assertEqual(entry["footprint_detector"], "LONG_AXIS_SUPPRESSED")
        self.assertFalse(entry["axis_evidence_present"])

    def test_manifest_authority_is_fail_closed(self) -> None:
        entry = build_review_manifest_entry(
            panel_id="R03",
            candidate=self.candidate,
            text_binding=self.binding,
            source=self.source,
            source_only_crop="review/r03-source-only.png",
            overlay_crop="review/r03-overlay.png",
        )
        self.assertFalse(entry["authority"]["support_identity_authorized"])
        self.assertFalse(entry["authority"]["family_assignment_authorized"])
        self.assertFalse(entry["authority"]["section_assignment_authorized"])
        self.assertFalse(entry["authority"]["fixed_line_assignment_authorized"])
        self.assertFalse(entry["authority"]["structural_identity_authorized"])
        self.assertFalse(entry["authority"]["canonical_write_authorized"])
        self.assertFalse(entry["authority"]["g2c_promotion_authorized"])
        self.assertFalse(entry["authority"]["g3_authorized"])
        self.assertFalse(entry["authority"]["merge_authorized"])

    def test_missing_exact_target_fields_are_rejected(self) -> None:
        broken = dict(self.candidate)
        broken.pop("bbox")
        with self.assertRaises(ValueError):
            build_review_manifest_entry(
                panel_id="R04",
                candidate=broken,
                text_binding=self.binding,
                source=self.source,
                source_only_crop="review/r04-source-only.png",
                overlay_crop="review/r04-overlay.png",
            )


if __name__ == "__main__":
    unittest.main()
