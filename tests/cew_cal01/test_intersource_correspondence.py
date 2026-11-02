import copy
import unittest

from experiments.cew_cal01.intersource_correspondence import discover_correspondence_candidates


TAV5_SOURCE_SHA = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
TAV5_RASTER_SHA = "474ed6c3958d8841b95b1ca9cdfb7702ec552204a30a4de6b646ec1e5f391406"
TAV02_SOURCE_SHA = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _bridge(count=22):
    rows = []
    for index in range(count):
        x = 100.0 + index * 17.0
        y = 200.0 + index * 23.0
        rows.append(
            {
                "occurrence_id": f"COL-OCC-{index + 1:04d}",
                "object_candidate_id": f"OBJ-{index + 1:04d}",
                "source_candidate_id": f"SRC-{index + 1:04d}",
                "pixel_geometry": {
                    "frame": "RASTER_PIXEL",
                    "x": x,
                    "y": y,
                    "width": 40.0,
                    "height": 60.0,
                },
                "source_evidence_ids": [f"EVID-{index + 1:04d}"],
                "human_review_receipts": ["governance/review.json"],
                "support_identifier": None,
                "structural_identity_authorized": False,
                "canonical_write_authorized": False,
            }
        )
    return {
        "schema": "CEW_SPIRAL_EXACT_SOURCE_STRUCTURAL_CANDIDATE_BRIDGE_v1",
        "bridge": {
            "schema": "CEW_SPIRAL_STRUCTURAL_CANDIDATE_BRIDGE_v1",
            "source": {
                "repository": "antoniocorsano-boop/N12",
                "commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
                "path": "archive/documentazione_originaria/tavola 5.pdf",
                "page_index": 0,
                "sha256": TAV5_SOURCE_SHA,
            },
            "governed_raster": {
                "frame": "RASTER_PIXEL",
                "width_px": 7016,
                "height_px": 12530,
                "raster_sha256": TAV5_RASTER_SHA,
                "renderer_tool_id": "pypdfium2",
                "renderer_tool_version": "5.14.0",
            },
            "occurrence_count": count,
            "structural_candidate_count": count,
            "occurrence_bridge": rows,
            "historical_comparator_loaded": False,
            "historical_support_identifier_required": False,
            "authority": dict(AUTHORITY_CLOSED),
        },
    }


def _lattice():
    nodes = []
    for x_index, x_m in enumerate((0.0, 4.7, 9.8)):
        for y_index, y_m in enumerate((0.0, 2.1)):
            nodes.append(
                {
                    "lattice_node_id": f"TAV-02S:LATTICE:X{x_index}:Y{y_index}",
                    "source_point_normalized_px": [1000.0 + x_index * 100.0, 2000.0 + y_index * 100.0],
                    "local_metric_xy_m": [x_m, y_m],
                    "fit_eligible": False,
                    "primary_anchor_authorized": False,
                }
            )
    return {
        "schema": "CEW_CAL01_TAV02_REFERENCE_LATTICE_v1",
        "source": {"source_id": "TAV-02S", "sha256": TAV02_SOURCE_SHA},
        "coordinate_frame": "LOCAL_RELATIVE_METRIC",
        "lattice_digest": "sha256:" + "d" * 64,
        "lattice_node_count": len(nodes),
        "lattice_nodes": nodes,
        "absolute_origin_authorized": False,
        "eligible_for_metric_calibration": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


class InterSourceCorrespondenceProposalTests(unittest.TestCase):
    def test_exact_tav5_occurrences_remain_unmatched_without_primary_homology_evidence(self):
        result = discover_correspondence_candidates(_bridge(), _lattice())
        self.assertEqual(result["schema"], "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_CANDIDATES_v1")
        self.assertEqual(result["source_candidate_count"], 22)
        self.assertEqual(result["classification_counts"], {"AMBIGUOUS": 0, "HOMOLOGY_PROPOSAL": 0, "UNMATCHED": 22})
        self.assertEqual(result["governed_correspondence_count"], 0)
        self.assertTrue(all(row["classification"] == "UNMATCHED" for row in result["candidates"]))
        self.assertTrue(all(row["target_lattice_node_ids"] == [] for row in result["candidates"]))
        self.assertTrue(all(row["fit_eligible"] is False for row in result["candidates"]))
        self.assertTrue(all(row["governed_correspondence"] is False for row in result["candidates"]))
        self.assertEqual(result["authority"], AUTHORITY_CLOSED)

    def test_tav5_centers_are_derived_only_from_governed_raster_geometry(self):
        result = discover_correspondence_candidates(_bridge(count=1), _lattice())
        row = result["candidates"][0]
        self.assertEqual(row["occurrence_id"], "COL-OCC-0001")
        self.assertEqual(row["source_point_px"], [120.0, 230.0])
        self.assertEqual(row["source_frame"], "RASTER_PIXEL")
        self.assertEqual(result["tav5_source"]["sha256"], TAV5_SOURCE_SHA)
        self.assertEqual(result["tav5_raster"]["raster_sha256"], TAV5_RASTER_SHA)
        self.assertEqual(result["tav5_raster"]["width_px"], 7016)
        self.assertEqual(result["tav5_raster"]["height_px"], 12530)

    def test_explicit_primary_binding_creates_proposal_not_governed_correspondence(self):
        binding = {
            "occurrence_id": "COL-OCC-0001",
            "lattice_node_id": "TAV-02S:LATTICE:X1:Y1",
            "evidence_kind": "PRIMARY_SOURCE_HOMOLOGY",
            "evidence_refs": ["PRIMARY:visual-review:001"],
        }
        result = discover_correspondence_candidates(_bridge(count=2), _lattice(), [binding])
        first = result["candidates"][0]
        second = result["candidates"][1]
        self.assertEqual(first["classification"], "HOMOLOGY_PROPOSAL")
        self.assertEqual(first["target_lattice_node_ids"], ["TAV-02S:LATTICE:X1:Y1"])
        self.assertEqual(first["proposal_evidence_refs"], ["PRIMARY:visual-review:001"])
        self.assertFalse(first["governed_correspondence"])
        self.assertFalse(first["fit_eligible"])
        self.assertEqual(second["classification"], "UNMATCHED")
        self.assertEqual(result["governed_correspondence_count"], 0)

    def test_conflicting_explicit_bindings_are_ambiguous_not_auto_selected(self):
        bindings = [
            {
                "occurrence_id": "COL-OCC-0001",
                "lattice_node_id": "TAV-02S:LATTICE:X0:Y0",
                "evidence_kind": "PRIMARY_SOURCE_HOMOLOGY",
                "evidence_refs": ["PRIMARY:A"],
            },
            {
                "occurrence_id": "COL-OCC-0001",
                "lattice_node_id": "TAV-02S:LATTICE:X1:Y1",
                "evidence_kind": "PRIMARY_SOURCE_HOMOLOGY",
                "evidence_refs": ["PRIMARY:B"],
            },
        ]
        result = discover_correspondence_candidates(_bridge(count=1), _lattice(), bindings)
        row = result["candidates"][0]
        self.assertEqual(row["classification"], "AMBIGUOUS")
        self.assertEqual(row["target_lattice_node_ids"], ["TAV-02S:LATTICE:X0:Y0", "TAV-02S:LATTICE:X1:Y1"])
        self.assertFalse(row["governed_correspondence"])
        self.assertFalse(row["fit_eligible"])

    def test_no_historical_identity_or_nearest_distance_is_emitted(self):
        bridge = _bridge(count=1)
        bridge["bridge"]["occurrence_bridge"][0]["support_identifier"] = "N999"
        result = discover_correspondence_candidates(bridge, _lattice())
        serialized = repr(result)
        self.assertNotIn("N999", serialized)
        self.assertNotIn("support_identifier", serialized)
        self.assertNotIn("nearest", serialized.lower())
        self.assertNotIn("historical_m0g", serialized.lower())
        self.assertNotIn("historical_affine", serialized.lower())

    def test_binding_order_does_not_change_digest(self):
        bindings = [
            {
                "occurrence_id": "COL-OCC-0001",
                "lattice_node_id": "TAV-02S:LATTICE:X0:Y0",
                "evidence_kind": "PRIMARY_SOURCE_HOMOLOGY",
                "evidence_refs": ["PRIMARY:A"],
            },
            {
                "occurrence_id": "COL-OCC-0002",
                "lattice_node_id": "TAV-02S:LATTICE:X1:Y1",
                "evidence_kind": "PRIMARY_SOURCE_HOMOLOGY",
                "evidence_refs": ["PRIMARY:B"],
            },
        ]
        forward = discover_correspondence_candidates(_bridge(count=2), _lattice(), bindings)
        reverse = discover_correspondence_candidates(_bridge(count=2), _lattice(), list(reversed(bindings)))
        self.assertEqual(forward["candidate_digest"], reverse["candidate_digest"])
        self.assertEqual(forward["candidates"], reverse["candidates"])

    def test_unknown_or_unproven_binding_fails_closed(self):
        bad_occurrence = {
            "occurrence_id": "COL-OCC-9999",
            "lattice_node_id": "TAV-02S:LATTICE:X0:Y0",
            "evidence_kind": "PRIMARY_SOURCE_HOMOLOGY",
            "evidence_refs": ["PRIMARY:A"],
        }
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_OCCURRENCE_UNKNOWN"):
            discover_correspondence_candidates(_bridge(count=1), _lattice(), [bad_occurrence])

        bad_evidence = copy.deepcopy(bad_occurrence)
        bad_evidence["occurrence_id"] = "COL-OCC-0001"
        bad_evidence["evidence_kind"] = "NEAREST_GEOMETRY"
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_EVIDENCE_KIND_INVALID"):
            discover_correspondence_candidates(_bridge(count=1), _lattice(), [bad_evidence])


if __name__ == "__main__":
    unittest.main()
