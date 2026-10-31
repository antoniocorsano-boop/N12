import hashlib
import unittest
from pathlib import Path

from experiments.cew_col02.residual_occurrence_reconciliation import (
    RESIDUAL_CANDIDATE_IDS,
    build_reconciliation_manifest,
    select_residual_occurrences,
)


SOURCE_SHA = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
PRODUCER_SHA = "5664614d813cd11cf357bed40d7cdfaa843720f2"
SEARCH_REPLAY = "11dc8a03789628c6167a8c7cc10fe41d318c5fa22535065598e1c36aa56fd1ac"
SWEEP_REPLAY = "bdf6dbdb6a071312727a3ca8146159d4f47514a7bcaec5225235987b0ccb1070"
REVIEW_SHA = "896036dd048bac77555b383eb7af8329118dedc7f6dd4b5b7373e489f406a0d7"


def bundle():
    actions = {candidate_id: "NON_PILASTRO" for candidate_id in RESIDUAL_CANDIDATE_IDS}
    actions["COL02-FP-0252"] = "INQUADRATO_MALE"
    actions["COL02-FP-0106"] = "INQUADRATO_MALE"
    actions["COL02-FP-0581"] = "PILASTRO"
    actions["COL02-FP-0605"] = "PILASTRO"
    events = []
    for index, candidate_id in enumerate(RESIDUAL_CANDIDATE_IDS, start=1):
        events.append(
            {
                "schema_version": "cew-mobile-review-event-v1",
                "event_id": f"D{index:02d}",
                "timestamp": "2026-10-31T05:40:00Z",
                "event_type": "CANDIDATE_DECISION",
                "candidate_id": candidate_id,
                "action": actions[candidate_id],
                "reason": None,
                "terminal": True,
            }
        )
    for index, (candidate_id, point) in enumerate(
        [
            ("COL02-FP-0605", {"x": 0.48, "y": 0.49}),
            ("COL02-FP-0572", {"x": 0.63, "y": 0.92}),
            ("COL02-FP-0572", {"x": 0.17, "y": 0.91}),
            ("COL02-FP-0572", {"x": 0.59, "y": 0.42}),
        ],
        start=1,
    ):
        events.append(
            {
                "schema_version": "cew-mobile-review-event-v1",
                "event_id": f"P{index:02d}",
                "timestamp": "2026-10-31T05:41:00Z",
                "event_type": "ADDITIONAL_OCCURRENCE",
                "candidate_id": candidate_id,
                "action": "ALTRO_PILASTRO",
                "point": point,
                "terminal": False,
            }
        )
    return {
        "schema_version": "cew-mobile-review-bundle-v1",
        "review_id": "CEW-COL02-VISIBLE-SIBLING-RESIDUAL-MOBILE-v1",
        "source": {
            "authority": "EXACT_SOURCE_DERIVED_HUMAN_GRAPHICAL_REVIEW_ONLY",
            "occurrence_sweep_replay_sha256": SWEEP_REPLAY,
            "producer_exact_sha": PRODUCER_SHA,
            "prototype_guided_replay_sha256": SEARCH_REPLAY,
            "source_sha256": SOURCE_SHA,
        },
        "candidate_ids": list(RESIDUAL_CANDIDATE_IDS),
        "events": events,
        "authority": {
            "support_identity_authorized": False,
            "text_identity_binding_authorized": False,
            "family_assignment_authorized": False,
            "section_assignment_authorized": False,
            "fixed_line_assignment_authorized": False,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "g2c_promotion_authorized": False,
            "g3_authorized": False,
            "merge_authorized": False,
        },
        "canonical_write_authorized": False,
        "canonical_write_performed": False,
    }


def source_fixture():
    search = {
        "replay_sha256": SEARCH_REPLAY,
        "source": {"sha256": SOURCE_SHA},
        "review_panels": [
            {
                "panel_id": "S10",
                "candidate_id": "HOST-10",
                "bbox": {"x": 0.70, "y": 0.60, "width": 0.10, "height": 0.08},
            },
            {
                "panel_id": "S15",
                "candidate_id": "HOST-15",
                "bbox": {"x": 0.75, "y": 0.50, "width": 0.10, "height": 0.08},
            },
            {
                "panel_id": "S18",
                "candidate_id": "HOST-18",
                "bbox": {"x": 0.35, "y": 0.35, "width": 0.12, "height": 0.10},
            },
        ],
    }
    sweep = {
        "replay_sha256": SWEEP_REPLAY,
        "source_search_replay_sha256": SEARCH_REPLAY,
        "panels": [
            {
                "panel_id": "S10",
                "target_candidate_id": "HOST-10",
                "visible_sibling_candidates": [
                    {
                        "candidate_id": "COL02-FP-0252",
                        "bbox": {"x": 0.79, "y": 0.66, "width": 0.02, "height": 0.02},
                        "score": 0.64,
                        "visible_fraction_in_crop": 1.0,
                    }
                ],
            },
            {
                "panel_id": "S15",
                "target_candidate_id": "HOST-15",
                "visible_sibling_candidates": [
                    {
                        "candidate_id": "COL02-FP-0605",
                        "bbox": {"x": 0.84, "y": 0.57, "width": 0.04, "height": 0.03},
                        "score": 0.58,
                        "visible_fraction_in_crop": 1.0,
                    },
                    {
                        "candidate_id": "COL02-FP-0252",
                        "bbox": {"x": 0.80, "y": 0.65, "width": 0.02, "height": 0.02},
                        "score": 0.60,
                        "visible_fraction_in_crop": 0.70,
                    },
                ],
            },
            {
                "panel_id": "S18",
                "target_candidate_id": "HOST-18",
                "visible_sibling_candidates": [
                    {
                        "candidate_id": "COL02-FP-0106",
                        "bbox": {"x": 0.38, "y": 0.49, "width": 0.02, "height": 0.02},
                        "score": 0.61,
                        "visible_fraction_in_crop": 1.0,
                    },
                    {
                        "candidate_id": "COL02-FP-0572",
                        "bbox": {"x": 0.47, "y": 0.35, "width": 0.05, "height": 0.04},
                        "score": 0.55,
                        "visible_fraction_in_crop": 1.0,
                    },
                ],
            },
        ],
    }
    audit = {"source": {"raster_width_px": 1000, "raster_height_px": 1000, "sha256": SOURCE_SHA}}
    return search, sweep, audit


class ResidualOccurrenceManifestTests(unittest.TestCase):
    def test_frozen_real_review_receipt_bytes_match_recorded_digest(self):
        path = Path("governance/cew-col02/COL02_RESIDUAL_MOBILE_HUMAN_REVIEW_v1.json")
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), REVIEW_SHA)

    def test_select_residual_occurrences_keeps_best_visible_context(self):
        search, sweep, _audit = source_fixture()
        selected = select_residual_occurrences(search, sweep)
        by_id = {item["candidate_id"]: item for item in selected}
        self.assertEqual(by_id["COL02-FP-0252"]["source_panel_id"], "S10")
        self.assertEqual(by_id["COL02-FP-0252"]["visible_fraction_in_crop"], 1.0)

    def test_manifest_is_bounded_and_fail_closed(self):
        search, sweep, audit = source_fixture()
        manifest = build_reconciliation_manifest(
            bundle(),
            search=search,
            sweep=sweep,
            audit=audit,
            proposals=[],
            human_review_bundle_sha256=REVIEW_SHA,
        )
        self.assertEqual(len(manifest["reframe_tasks"]), 2)
        self.assertEqual(
            [task["candidate_id"] for task in manifest["reframe_tasks"]],
            ["COL02-FP-0252", "COL02-FP-0106"],
        )
        self.assertEqual(len(manifest["point_reconciliation"]), 4)
        self.assertEqual(len(manifest["review_tasks"]), 6)
        self.assertTrue(manifest["residual_candidate_review_complete"])
        self.assertFalse(manifest["occurrence_coverage_complete"])
        self.assertTrue(manifest["authority"]["graphical_reconciliation_review_authorized"])
        forbidden = [
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
        ]
        self.assertTrue(all(manifest["authority"][key] is False for key in forbidden))
        self.assertEqual(manifest["human_review_bundle_sha256"], REVIEW_SHA)


if __name__ == "__main__":
    unittest.main()
