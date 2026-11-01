from __future__ import annotations

import unittest

from cew_spiral.prototype_similarity_adapter import rank_from_project_memory


class PrototypeSimilarityAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scene = {
            "source": {
                "source_version_id": "CEW-N12-DXF01-TAV5",
                "page_id": "TAV5",
                "evidence_region_id": "DXF01-SCENE",
                "source_sha256": "b" * 64,
            },
            "objects": [
                {
                    "object_id": "P1",
                    "geometry": {"type": "LINE", "a": [0, 0], "b": [10, 0]},
                    "properties": {
                        "topology_hint": "FRAME_EDGE",
                        "spatial_context": "GRID_A",
                        "associated_text": "P13 30X45",
                    },
                },
                {
                    "object_id": "C1",
                    "geometry": {"type": "LINE", "a": [0, 1], "b": [9.5, 1]},
                    "properties": {
                        "topology_hint": "FRAME_EDGE",
                        "spatial_context": "GRID_A",
                        "associated_text": "P13 30X45",
                    },
                },
                {
                    "object_id": "NEG1",
                    "geometry": {"type": "LINE", "a": [0, 2], "b": [10, 2]},
                    "properties": {
                        "topology_hint": "FRAME_EDGE",
                        "spatial_context": "GRID_A",
                        "associated_text": "P13 30X45",
                    },
                },
                {
                    "object_id": "AMB1",
                    "geometry": {"type": "LINE", "a": [0, 3], "b": [10, 3]},
                    "properties": {
                        "topology_hint": "FRAME_EDGE",
                        "spatial_context": "GRID_A",
                        "associated_text": "P13 30X45",
                    },
                },
            ],
        }
        self.memory = {
            "schema": "CEW_PROTOTYPE_MEMORY_v1",
            "project_id": "N12",
            "concept_id": "COLUMN_MARKER",
            "meaning": "project-local column marker candidate",
            "scope": "PROJECT_LOCAL",
            "examples": [
                {"role": "POSITIVE", "candidate_id": "P1", "source_version_id": "CEW-N12-DXF01-TAV5"},
                {"role": "NEGATIVE", "candidate_id": "NEG1", "source_version_id": "CEW-N12-DXF01-TAV5"},
                {"role": "AMBIGUOUS", "candidate_id": "AMB1", "source_version_id": "CEW-N12-DXF01-TAV5"},
            ],
            "authority": {
                "canonical_write_authorized": False,
                "structural_identity_authorized": False,
                "engineering_authority_effect": "NONE",
                "human_project_validation_required": True,
            },
        }

    def test_positive_example_seeds_ranking_negative_penalizes_and_ambiguous_does_not_seed(self) -> None:
        result = rank_from_project_memory(self.scene, self.memory)
        self.assertEqual(result["prototype_anchor_id"], "P1")
        self.assertEqual(result["ignored_ambiguous_example_ids"], ["AMB1"])
        rows = {row["candidate_object_id"]: row for row in result["candidates"]}
        self.assertGreater(rows["C1"]["score"], rows["NEG1"]["score"])
        self.assertTrue(rows["NEG1"]["negative_example_penalty_applied"])
        self.assertIn("signal_scores", rows["C1"])
        self.assertIn("reason_codes", rows["C1"])

    def test_similarity_never_creates_semantic_or_structural_authority(self) -> None:
        result = rank_from_project_memory(self.scene, self.memory)
        self.assertFalse(result["auto_confirm_cluster_authorized"])
        self.assertFalse(result["structural_identity_created"])
        self.assertFalse(result["canonical_write_authorized"])
        self.assertEqual(result["engineering_authority_effect"], "NONE")
        for row in result["candidates"]:
            self.assertFalse(row["object_type_created"])
            self.assertFalse(row["family_membership_created"])
            self.assertFalse(row["structural_identity_created"])
            self.assertTrue(row["human_confirmation_required"])

    def test_same_inputs_are_deterministic(self) -> None:
        self.assertEqual(
            rank_from_project_memory(self.scene, self.memory),
            rank_from_project_memory(self.scene, self.memory),
        )

    def test_source_revision_mismatch_fails_closed(self) -> None:
        drifted = dict(self.memory)
        drifted["examples"] = [dict(row) for row in self.memory["examples"]]
        drifted["examples"][0]["source_version_id"] = "OTHER-SOURCE"
        with self.assertRaisesRegex(ValueError, "PROTOTYPE_SOURCE_REVISION_MISMATCH"):
            rank_from_project_memory(self.scene, drifted)

    def test_ambiguous_only_memory_cannot_seed_a_prototype(self) -> None:
        memory = dict(self.memory)
        memory["examples"] = [
            {"role": "AMBIGUOUS", "candidate_id": "AMB1", "source_version_id": "CEW-N12-DXF01-TAV5"}
        ]
        with self.assertRaisesRegex(ValueError, "HUMAN_TAUGHT_POSITIVE_REQUIRED"):
            rank_from_project_memory(self.scene, memory)

    def test_non_project_local_or_authority_drift_is_rejected(self) -> None:
        nonlocal_memory = dict(self.memory)
        nonlocal_memory["scope"] = "GLOBAL"
        with self.assertRaisesRegex(ValueError, "PROJECT_LOCAL_MEMORY_REQUIRED"):
            rank_from_project_memory(self.scene, nonlocal_memory)
        unsafe = dict(self.memory)
        unsafe["authority"] = dict(self.memory["authority"])
        unsafe["authority"]["structural_identity_authorized"] = True
        with self.assertRaisesRegex(ValueError, "PROTOTYPE_MEMORY_AUTHORITY_DRIFT"):
            rank_from_project_memory(self.scene, unsafe)


if __name__ == "__main__":
    unittest.main()
