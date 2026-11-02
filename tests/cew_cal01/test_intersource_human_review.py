import copy
import unittest

from experiments.cew_cal01.intersource_human_review import (
    build_targeted_review_manifest,
    select_targeted_review_batch,
)


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}

CENTERS_AND_EVIDENCE_COUNTS = [
    ("COL-OCC-0001", [4693.0, 4070.0], 2),
    ("COL-OCC-0002", [6042.0, 4074.0], 2),
    ("COL-OCC-0003", [5952.0, 5158.0], 2),
    ("COL-OCC-0004", [4726.0, 5198.0], 2),
    ("COL-OCC-0005", [3488.5, 5199.0], 2),
    ("COL-OCC-0006", [3341.0, 5355.0], 2),
    ("COL-OCC-0007", [2607.5, 6165.5], 2),
    ("COL-OCC-0008", [3604.0, 6160.5], 2),
    ("COL-OCC-0009", [3694.0, 6376.0], 2),
    ("COL-OCC-0010", [4732.0, 6414.0], 2),
    ("COL-OCC-0011", [4737.0, 7188.0], 2),
    ("COL-OCC-0012", [6043.0, 7309.0], 2),
    ("COL-OCC-0013", [5608.5, 7385.0], 5),
    ("COL-OCC-0014", [2606.0, 7656.0], 2),
    ("COL-OCC-0015", [4491.0, 7678.0], 2),
    ("COL-OCC-0016", [1792.0, 7666.0], 2),
    ("COL-OCC-0017", [3120.0, 7691.0], 4),
    ("COL-OCC-0018", [4493.0, 8390.0], 2),
    ("COL-OCC-0019", [5612.0, 8366.0], 2),
    ("COL-OCC-0020", [3125.0, 8381.0], 2),
    ("COL-OCC-0021", [4515.0, 9642.0], 2),
    ("COL-OCC-0022", [5643.0, 10738.0], 2),
]

EXPECTED_BATCH = [
    "COL-OCC-0013",
    "COL-OCC-0016",
    "COL-OCC-0005",
    "COL-OCC-0002",
    "COL-OCC-0022",
    "COL-OCC-0020",
    "COL-OCC-0001",
    "COL-OCC-0021",
]


def _candidates():
    rows = []
    for occurrence_id, point, evidence_count in CENTERS_AND_EVIDENCE_COUNTS:
        rows.append(
            {
                "occurrence_id": occurrence_id,
                "object_candidate_id": f"OBJ:{occurrence_id}",
                "source_candidate_id": f"SRC:{occurrence_id}",
                "source_point_px": list(point),
                "source_frame": "RASTER_PIXEL",
                "source_evidence_refs": [
                    f"PRIMARY:{occurrence_id}:E{index + 1}" for index in range(evidence_count)
                ],
                "classification": "UNMATCHED",
                "target_lattice_node_ids": [],
                "proposal_evidence_refs": [],
                "governed_correspondence": False,
                "fit_eligible": False,
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "canonical_write_authorized": False,
            }
        )
    nodes = [
        {
            "lattice_node_id": f"TAV-02S:LATTICE:X{x}:Y{y}",
            "source_point_normalized_px": [1000.0 + x * 100.0, 2000.0 + y * 100.0],
            "local_metric_xy_m": [float(x), float(y)],
            "fit_eligible": False,
            "primary_anchor_authorized": False,
        }
        for x in range(7)
        for y in range(3)
    ]
    return {
        "schema": "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_CANDIDATES_v1",
        "program": "CEW-CAL-01",
        "candidate_digest": "sha256:" + "c" * 64,
        "tav5_source": {
            "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
        },
        "tav5_raster": {
            "frame": "RASTER_PIXEL",
            "width_px": 7016,
            "height_px": 12530,
            "raster_sha256": "474ed6c3958d8841b95b1ca9cdfb7702ec552204a30a4de6b646ec1e5f391406",
        },
        "tav02_source": {
            "source_id": "TAV-02S",
            "sha256": "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f",
        },
        "tav02_lattice_digest": "sha256:" + "d" * 64,
        "tav02_coordinate_frame": "LOCAL_RELATIVE_METRIC",
        "source_candidate_count": len(rows),
        "target_lattice_node_count": len(nodes),
        "classification_counts": {"AMBIGUOUS": 0, "HOMOLOGY_PROPOSAL": 0, "UNMATCHED": len(rows)},
        "governed_correspondence_count": 0,
        "candidates": rows,
        "target_lattice_nodes": nodes,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "eligible_for_registration_fit": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


class TargetedInterSourceHumanReviewTests(unittest.TestCase):
    def test_qualified_source_fixture_selects_expected_eight_occurrences(self):
        self.assertEqual(select_targeted_review_batch(_candidates(), 8), EXPECTED_BATCH)

    def test_selection_is_stable_under_candidate_input_order(self):
        payload = _candidates()
        reversed_payload = copy.deepcopy(payload)
        reversed_payload["candidates"].reverse()
        self.assertEqual(
            select_targeted_review_batch(payload, 8),
            select_targeted_review_batch(reversed_payload, 8),
        )

    def test_target_geometry_cannot_influence_selection(self):
        baseline = _candidates()
        drifted_target = copy.deepcopy(baseline)
        drifted_target["target_lattice_nodes"].reverse()
        for index, row in enumerate(drifted_target["target_lattice_nodes"]):
            row["source_point_normalized_px"] = [9000.0 - index * 321.0, 100.0 + index * 777.0]
            row["local_metric_xy_m"] = [float(index * 1000), float(-index * 1000)]
        self.assertEqual(
            select_targeted_review_batch(baseline, 8),
            select_targeted_review_batch(drifted_target, 8),
        )

    def test_invalid_batch_size_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_REVIEW_BATCH_SIZE_INVALID"):
            select_targeted_review_batch(_candidates(), 0)
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_REVIEW_BATCH_SIZE_INVALID"):
            select_targeted_review_batch(_candidates(), 23)

    def test_manifest_is_review_only_and_contains_no_target_suggestion(self):
        payload = _candidates()
        selected = select_targeted_review_batch(payload, 8)
        source_assets = {
            occurrence_id: {
                "file": f"tav5-{occurrence_id.lower()}-context.png",
                "sha256": "sha256:" + f"{index + 1:064x}",
                "crop_bbox_px": [0, 0, 100, 100],
            }
            for index, occurrence_id in enumerate(selected)
        }
        target_overview = {
            "file": "tav02-lattice-overview.png",
            "sha256": "sha256:" + "a" * 64,
            "normalization_transform": "ROTATE_90_COUNTERCLOCKWISE",
            "normalized_width_px": 12914,
            "normalized_height_px": 7016,
        }
        result = build_targeted_review_manifest(payload, selected, source_assets, target_overview)
        self.assertEqual(result["schema"], "CEW_CAL01_INTERSOURCE_TARGETED_HUMAN_REVIEW_v1")
        self.assertEqual(result["selection_strategy"], "SOURCE_ONLY_FARTHEST_POINT_COVERAGE_V1")
        self.assertEqual(result["selected_occurrence_ids"], EXPECTED_BATCH)
        self.assertEqual(result["review_item_count"], 8)
        self.assertEqual(result["target_lattice_node_count"], 21)
        self.assertFalse(result["target_geometry_used_for_selection"])
        self.assertFalse(result["target_node_ranking_performed"])
        self.assertFalse(result["automatic_homology_proposed"])
        self.assertEqual(result["decision_required"], "IDENTIFY_PRIMARY_HOMOLOGOUS_LATTICE_NODE_OR_REJECT")
        self.assertEqual(result["authority"], AUTHORITY_CLOSED)
        self.assertFalse(result["historical_comparator_loaded"])
        self.assertFalse(result["historical_affine_loaded"])
        self.assertFalse(result["historical_m0g_loaded"])
        serialized = repr(result).lower()
        for forbidden in ("nearest", "suggested_identity", "suggested_target", "similarity_score", "confidence_score"):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
