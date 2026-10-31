import unittest

from experiments.cew_col02.residual_occurrence_reconciliation import build_reframe_tasks


def decision(candidate_id, action):
    return {
        "event_id": f"DEC-{candidate_id}",
        "event_type": "CANDIDATE_DECISION",
        "candidate_id": candidate_id,
        "action": action,
        "terminal": True,
    }


class ResidualOccurrenceReframeTests(unittest.TestCase):
    def test_only_misframed_candidates_receive_expanded_context(self):
        search = {
            "review_panels": [
                {
                    "panel_id": "S01",
                    "candidate_id": "COL02-FP-0252",
                    "bbox": {"x": 0.20, "y": 0.30, "width": 0.04, "height": 0.05},
                },
                {
                    "panel_id": "S02",
                    "candidate_id": "COL02-FP-0106",
                    "bbox": {"x": 0.70, "y": 0.60, "width": 0.03, "height": 0.04},
                },
                {
                    "panel_id": "S03",
                    "candidate_id": "COL02-FP-0581",
                    "bbox": {"x": 0.50, "y": 0.40, "width": 0.03, "height": 0.03},
                },
            ]
        }
        decisions = [
            decision("COL02-FP-0252", "INQUADRATO_MALE"),
            decision("COL02-FP-0106", "INQUADRATO_MALE"),
            decision("COL02-FP-0581", "PILASTRO"),
        ]

        tasks = build_reframe_tasks(search, decisions, source_width=1000, source_height=800)
        self.assertEqual([task["candidate_id"] for task in tasks], ["COL02-FP-0252", "COL02-FP-0106"])

        panels = {panel["candidate_id"]: panel for panel in search["review_panels"]}
        for task in tasks:
            original = panels[task["candidate_id"]]["bbox"]
            self.assertEqual(task["target_bbox"], original)
            context = task["context_bbox"]
            self.assertLessEqual(context["x"], original["x"])
            self.assertLessEqual(context["y"], original["y"])
            self.assertGreaterEqual(context["x"] + context["width"], original["x"] + original["width"])
            self.assertGreaterEqual(context["y"] + context["height"], original["y"] + original["height"])
            self.assertGreater(context["width"], original["width"])
            self.assertGreater(context["height"], original["height"])
            self.assertEqual(task["task_type"], "REFRAME_CONFIRMATION")

    def test_reframe_clips_context_at_source_bounds_without_moving_target(self):
        search = {
            "review_panels": [
                {
                    "panel_id": "S_EDGE",
                    "candidate_id": "COL02-FP-0252",
                    "bbox": {"x": 0.0, "y": 0.0, "width": 0.02, "height": 0.03},
                }
            ]
        }
        tasks = build_reframe_tasks(
            search,
            [decision("COL02-FP-0252", "INQUADRATO_MALE")],
            source_width=1000,
            source_height=800,
        )
        self.assertEqual(tasks[0]["target_bbox"], search["review_panels"][0]["bbox"])
        self.assertEqual(tasks[0]["context_bbox"]["x"], 0.0)
        self.assertEqual(tasks[0]["context_bbox"]["y"], 0.0)
        self.assertLessEqual(tasks[0]["context_bbox"]["x"] + tasks[0]["context_bbox"]["width"], 1.0)
        self.assertLessEqual(tasks[0]["context_bbox"]["y"] + tasks[0]["context_bbox"]["height"], 1.0)

    def test_missing_panel_for_misframed_candidate_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "missing review panel"):
            build_reframe_tasks(
                {"review_panels": []},
                [decision("COL02-FP-0252", "INQUADRATO_MALE")],
                source_width=1000,
                source_height=800,
            )


if __name__ == "__main__":
    unittest.main()
