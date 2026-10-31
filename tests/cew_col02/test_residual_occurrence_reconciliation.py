import unittest

from experiments.cew_col02.residual_occurrence_reconciliation import (
    project_crop_point,
    reconcile_human_points,
    replay_mobile_review,
)


RESIDUAL_IDS = [
    "COL02-FP-0515",
    "COL02-FP-0252",
    "COL02-FP-0028",
    "COL02-FP-0581",
    "COL02-FP-0577",
    "COL02-FP-0605",
    "COL02-FP-0490",
    "COL02-FP-0106",
    "COL02-FP-0572",
    "COL02-FP-0243",
]


def event(event_id, event_type, candidate_id, **extra):
    return {
        "schema_version": "cew-mobile-review-event-v1",
        "event_id": event_id,
        "timestamp": "2026-10-31T05:40:00Z",
        "event_type": event_type,
        "candidate_id": candidate_id,
        **extra,
    }


def sample_bundle():
    events = [
        event("E01", "CANDIDATE_DECISION", "COL02-FP-0515", action="NON_PILASTRO", terminal=True),
        event("E02", "CANDIDATE_DECISION", "COL02-FP-0252", action="INQUADRATO_MALE", terminal=True),
        event("E03", "CANDIDATE_DECISION", "COL02-FP-0028", action="NON_PILASTRO", terminal=True),
        event("E04", "CANDIDATE_DECISION", "COL02-FP-0581", action="PILASTRO", terminal=True),
        event("E05", "CANDIDATE_DECISION", "COL02-FP-0577", action="NON_PILASTRO", terminal=True),
        event("E06", "CANDIDATE_DECISION", "COL02-FP-0605", action="PILASTRO", terminal=True),
        event("E07", "UNDO_LAST", "COL02-FP-0605", undoes_event_id="E06", terminal=False),
        event("E08", "ADDITIONAL_OCCURRENCE", "COL02-FP-0605", action="ALTRO_PILASTRO", point={"x": 0.48, "y": 0.49}, terminal=False),
        event("E09", "CANDIDATE_DECISION", "COL02-FP-0605", action="PILASTRO", terminal=True),
        event("E10", "CANDIDATE_DECISION", "COL02-FP-0490", action="NON_PILASTRO", terminal=True),
        event("E11", "CANDIDATE_DECISION", "COL02-FP-0106", action="INQUADRATO_MALE", terminal=True),
        event("E12", "CANDIDATE_DECISION", "COL02-FP-0572", action="NON_PILASTRO", terminal=True),
        event("E13", "CANDIDATE_DECISION", "COL02-FP-0243", action="NON_PILASTRO", terminal=True),
        event("E14", "CANDIDATE_DECISION", "COL02-FP-0243", action="NON_PILASTRO", terminal=True),
        event("E15", "UNDO_LAST", "COL02-FP-0243", undoes_event_id="E14", terminal=False),
        event("E16", "ADDITIONAL_OCCURRENCE", "COL02-FP-0572", action="ALTRO_PILASTRO", point={"x": 0.63, "y": 0.92}, terminal=False),
        event("E17", "ADDITIONAL_OCCURRENCE", "COL02-FP-0572", action="ALTRO_PILASTRO", point={"x": 0.17, "y": 0.91}, terminal=False),
        event("E18", "ADDITIONAL_OCCURRENCE", "COL02-FP-0572", action="ALTRO_PILASTRO", point={"x": 0.59, "y": 0.42}, terminal=False),
    ]
    return {
        "schema_version": "cew-mobile-review-bundle-v1",
        "review_id": "CEW-COL02-VISIBLE-SIBLING-RESIDUAL-MOBILE-v1",
        "source": {
            "authority": "EXACT_SOURCE_DERIVED_HUMAN_GRAPHICAL_REVIEW_ONLY",
            "occurrence_sweep_replay_sha256": "bdf6dbdb6a071312727a3ca8146159d4f47514a7bcaec5225235987b0ccb1070",
            "producer_exact_sha": "5664614d813cd11cf357bed40d7cdfaa843720f2",
            "prototype_guided_replay_sha256": "11dc8a03789628c6167a8c7cc10fe41d318c5fa22535065598e1c36aa56fd1ac",
            "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
        },
        "candidate_ids": list(RESIDUAL_IDS),
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


class ResidualOccurrenceReplayTests(unittest.TestCase):
    def test_replay_resolves_undo_and_preserves_exact_effective_review(self):
        result = replay_mobile_review(sample_bundle())
        self.assertEqual(len(result["decisions"]), 10)
        self.assertEqual(len(result["additional_occurrences"]), 4)
        self.assertEqual(
            {item["candidate_id"]: item["action"] for item in result["decisions"]},
            {
                "COL02-FP-0515": "NON_PILASTRO",
                "COL02-FP-0252": "INQUADRATO_MALE",
                "COL02-FP-0028": "NON_PILASTRO",
                "COL02-FP-0581": "PILASTRO",
                "COL02-FP-0577": "NON_PILASTRO",
                "COL02-FP-0605": "PILASTRO",
                "COL02-FP-0490": "NON_PILASTRO",
                "COL02-FP-0106": "INQUADRATO_MALE",
                "COL02-FP-0572": "NON_PILASTRO",
                "COL02-FP-0243": "NON_PILASTRO",
            },
        )
        self.assertEqual(result["misframed_candidate_ids"], ["COL02-FP-0252", "COL02-FP-0106"])

    def test_replay_rejects_lineage_drift(self):
        bundle = sample_bundle()
        bundle["source"]["producer_exact_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "producer_exact_sha"):
            replay_mobile_review(bundle)

    def test_replay_rejects_missing_terminal_candidate_decision(self):
        bundle = sample_bundle()
        bundle["events"] = [e for e in bundle["events"] if e.get("candidate_id") != "COL02-FP-0243"]
        with self.assertRaisesRegex(ValueError, "exactly one effective terminal decision"):
            replay_mobile_review(bundle)


class HumanPointReconciliationTests(unittest.TestCase):
    def test_project_crop_point_maps_mobile_coordinates_to_source_coordinates(self):
        source_point = project_crop_point(
            {"x": 0.5, "y": 0.25},
            {"x": 0.10, "y": 0.20, "width": 0.20, "height": 0.40},
        )
        self.assertAlmostEqual(source_point["x"], 0.20)
        self.assertAlmostEqual(source_point["y"], 0.30)

    def test_point_inside_unique_proposal_binds_to_existing_candidate(self):
        points = [{"event_id": "P1", "source_point": {"x": 0.15, "y": 0.15}}]
        proposals = [
            {"candidate_id": "A", "bbox": {"x": 0.10, "y": 0.10, "width": 0.10, "height": 0.10}},
            {"candidate_id": "B", "bbox": {"x": 0.40, "y": 0.40, "width": 0.10, "height": 0.10}},
        ]
        result = reconcile_human_points(points, proposals, reviewed_ids=set())
        self.assertEqual(result[0]["status"], "REVIEW_REQUIRED_EXISTING_PROPOSAL")
        self.assertEqual(result[0]["proposal_candidate_id"], "A")

    def test_point_resolving_to_reviewed_candidate_is_duplicate_not_review_task(self):
        points = [{"event_id": "P1", "source_point": {"x": 0.15, "y": 0.15}}]
        proposals = [{"candidate_id": "A", "bbox": {"x": 0.10, "y": 0.10, "width": 0.10, "height": 0.10}}]
        result = reconcile_human_points(points, proposals, reviewed_ids={"A"})
        self.assertEqual(result[0]["status"], "DUPLICATE_EXISTING_OCCURRENCE")
        self.assertEqual(result[0]["proposal_candidate_id"], "A")

    def test_two_points_resolving_to_same_new_proposal_create_one_review_task(self):
        points = [
            {"event_id": "P1", "source_point": {"x": 0.14, "y": 0.14}},
            {"event_id": "P2", "source_point": {"x": 0.16, "y": 0.16}},
        ]
        proposals = [{"candidate_id": "A", "bbox": {"x": 0.10, "y": 0.10, "width": 0.10, "height": 0.10}}]
        result = reconcile_human_points(points, proposals, reviewed_ids=set())
        self.assertEqual(result[0]["status"], "REVIEW_REQUIRED_EXISTING_PROPOSAL")
        self.assertEqual(result[1]["status"], "DUPLICATE_POINT_RESOLUTION")
        self.assertEqual(result[1]["duplicate_of_event_id"], "P1")

    def test_equal_geometric_candidates_fail_closed_as_unbound(self):
        points = [{"event_id": "P1", "source_point": {"x": 0.15, "y": 0.15}}]
        proposals = [
            {"candidate_id": "B", "bbox": {"x": 0.10, "y": 0.10, "width": 0.10, "height": 0.10}},
            {"candidate_id": "A", "bbox": {"x": 0.10, "y": 0.10, "width": 0.10, "height": 0.10}},
        ]
        result = reconcile_human_points(points, proposals, reviewed_ids=set())
        self.assertEqual(result[0]["status"], "HUMAN_POINT_UNBOUND")
        self.assertEqual(result[0]["ambiguous_candidate_ids"], ["A", "B"])
        self.assertNotIn("proposal_candidate_id", result[0])


if __name__ == "__main__":
    unittest.main()
