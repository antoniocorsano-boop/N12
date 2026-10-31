from __future__ import annotations

import json
import unittest
from pathlib import Path


RECEIPT = Path("governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json")


class AxisAwareWholeSymbolManifestTests(unittest.TestCase):
    def test_manifest_preserves_v1_ids_and_keeps_repair_authority_bounded(self) -> None:
        try:
            from experiments.cew_col02.axis_aware_whole_symbol_exact_source import build_axis_aware_repair_manifest
        except ModuleNotFoundError:
            self.fail("axis-aware exact-source repair manifest builder is missing")

        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        repair_ids = ["COL02-FP-0252", "COL02-FP-0073", "COL02-FP-0241", "COL02-FP-0261", "COL02-FP-0071"]
        proposals = [
            {
                "candidate_id": candidate_id,
                "bbox": {"x": 0.1 + index * 0.1, "y": 0.2, "width": 0.03, "height": 0.04},
            }
            for index, candidate_id in enumerate(repair_ids)
        ] + [
            {
                "candidate_id": "COL02-FP-0106",
                "bbox": {"x": 0.7, "y": 0.2, "width": 0.03, "height": 0.04},
            }
        ]
        repairs = {
            candidate_id: {
                "bbox": {"x": proposal["bbox"]["x"] - 0.01, "y": 0.19, "width": 0.05, "height": 0.06},
                "axis_cross": {"x": proposal["bbox"]["x"] + 0.01, "y": 0.22},
                "axis_thickness_px": {"horizontal": 5, "vertical": 5},
                "boundary_side_count": 4,
            }
            for candidate_id, proposal in zip(repair_ids, proposals[:5])
        }
        repairs["COL02-FP-0241"] = None

        manifest = build_axis_aware_repair_manifest(
            receipt=receipt,
            proposals=proposals,
            repair_results=repairs,
            source_replay_sha256="source-replay",
        )

        self.assertEqual(manifest["schema"], "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_MANIFEST_v1")
        self.assertEqual(manifest["proposal_count"], 6)
        self.assertEqual(manifest["rejected_candidates"], [
            {"candidate_id": "COL02-FP-0106", "reason": "MISLOCALIZED_NOT_COLUMN"}
        ])
        self.assertEqual(len(manifest["repairs"]), 5)
        self.assertEqual([row["repair_id"] for row in manifest["repairs"]], [
            "COL02-WSR-001", "COL02-WSR-002", "COL02-WSR-003", "COL02-WSR-004", "COL02-WSR-005"
        ])
        self.assertEqual([row["source_candidate_id"] for row in manifest["repairs"]], repair_ids)
        self.assertEqual(manifest["repairs"][2]["status"], "UNRESOLVED_GEOMETRY_REPAIR")
        self.assertIsNone(manifest["repairs"][2]["reconstructed_bbox"])
        self.assertTrue(all(not row["repair_id"].startswith("COL02-FP-") for row in manifest["repairs"]))
        self.assertFalse(manifest["occurrence_coverage_complete"])

        authority = manifest["authority"]
        self.assertTrue(authority["graphical_whole_symbol_repair_authorized"])
        for key in (
            "support_identity_authorized",
            "text_identity_binding_authorized",
            "family_assignment_authorized",
            "section_assignment_authorized",
            "fixed_line_assignment_authorized",
            "structural_identity_authorized",
            "canonical_geometry_authorized",
            "canonical_write_authorized",
            "g2c_promotion_authorized",
            "g3_authorized",
            "merge_authorized",
        ):
            self.assertFalse(authority[key], key)

    def test_missing_repair_seed_proposal_fails_closed(self) -> None:
        try:
            from experiments.cew_col02.axis_aware_whole_symbol_exact_source import build_axis_aware_repair_manifest
        except ModuleNotFoundError:
            self.fail("axis-aware exact-source repair manifest builder is missing")

        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "missing repair seed proposal"):
            build_axis_aware_repair_manifest(
                receipt=receipt,
                proposals=[],
                repair_results={},
                source_replay_sha256="source-replay",
            )


if __name__ == "__main__":
    unittest.main()
