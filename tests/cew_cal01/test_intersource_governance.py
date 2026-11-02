import copy
import unittest

from experiments.cew_cal01.intersource_governance import (
    build_correspondence_review_packet,
    govern_correspondences,
)


TAV5_SOURCE_SHA = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
TAV5_RASTER_SHA = "474ed6c3958d8841b95b1ca9cdfb7702ec552204a30a4de6b646ec1e5f391406"
TAV02_SOURCE_SHA = "cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f"
LATTICE_DIGEST = "sha256:" + "d" * 64
AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _candidate_payload(count=5, proposal=False):
    nodes = []
    candidates = []
    for index in range(count):
        node_id = f"TAV-02S:LATTICE:X{index}:Y0"
        target_px = [1000.0 + index * 100.0, 2000.0]
        local_xy = [float(index) * 4.7, 0.0]
        nodes.append(
            {
                "lattice_node_id": node_id,
                "source_point_normalized_px": target_px,
                "local_metric_xy_m": local_xy,
                "fit_eligible": False,
                "primary_anchor_authorized": False,
            }
        )
        target_ids = [node_id] if proposal else []
        candidates.append(
            {
                "occurrence_id": f"COL-OCC-{index + 1:04d}",
                "object_candidate_id": f"OBJ-{index + 1:04d}",
                "source_candidate_id": f"SRC-{index + 1:04d}",
                "source_point_px": [120.0 + index * 100.0, 230.0],
                "source_frame": "RASTER_PIXEL",
                "source_evidence_refs": [f"EVID-{index + 1:04d}"],
                "classification": "HOMOLOGY_PROPOSAL" if proposal else "UNMATCHED",
                "target_lattice_node_ids": target_ids,
                "proposal_evidence_refs": [f"PRIMARY:proposal:{index + 1:04d}"] if proposal else [],
                "governed_correspondence": False,
                "fit_eligible": False,
                "structural_identity_authorized": False,
                "canonical_geometry_authorized": False,
                "canonical_write_authorized": False,
            }
        )
    return {
        "schema": "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_CANDIDATES_v1",
        "program": "CEW-CAL-01",
        "tav5_source": {
            "repository": "antoniocorsano-boop/N12",
            "commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
            "path": "archive/documentazione_originaria/tavola 5.pdf",
            "page_index": 0,
            "sha256": TAV5_SOURCE_SHA,
        },
        "tav5_raster": {
            "frame": "RASTER_PIXEL",
            "width_px": 7016,
            "height_px": 12530,
            "raster_sha256": TAV5_RASTER_SHA,
        },
        "tav02_source": {"source_id": "TAV-02S", "sha256": TAV02_SOURCE_SHA},
        "tav02_lattice_digest": LATTICE_DIGEST,
        "tav02_coordinate_frame": "LOCAL_RELATIVE_METRIC",
        "source_candidate_count": len(candidates),
        "target_lattice_node_count": len(nodes),
        "classification_counts": {
            "AMBIGUOUS": 0,
            "HOMOLOGY_PROPOSAL": len(candidates) if proposal else 0,
            "UNMATCHED": 0 if proposal else len(candidates),
        },
        "governed_correspondence_count": 0,
        "candidates": candidates,
        "target_lattice_nodes": nodes,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "eligible_for_registration_fit": False,
        "authority": dict(AUTHORITY_CLOSED),
        "candidate_digest": "sha256:" + "c" * 64,
    }


def _decision(index, node_index=None):
    if node_index is None:
        node_index = index
    return {
        "schema": "CEW_CAL01_INTERSOURCE_CORRESPONDENCE_DECISION_v1",
        "program": "CEW-CAL-01",
        "reviewer_role": "HUMAN_PROFESSIONAL_USER",
        "decision": "CONFIRM_PRIMARY_HOMOLOGY",
        "validation_state": "PRIMARY_HOMOLOGY_VALIDATED",
        "occurrence_id": f"COL-OCC-{index + 1:04d}",
        "tav5_source_sha256": TAV5_SOURCE_SHA,
        "tav5_raster_sha256": TAV5_RASTER_SHA,
        "tav5_source_point_px": [120.0 + index * 100.0, 230.0],
        "tav5_source_frame": "RASTER_PIXEL",
        "tav02_source_sha256": TAV02_SOURCE_SHA,
        "tav02_lattice_digest": LATTICE_DIGEST,
        "tav02_lattice_node_id": f"TAV-02S:LATTICE:X{node_index}:Y0",
        "tav02_source_point_normalized_px": [1000.0 + node_index * 100.0, 2000.0],
        "evidence_kind": "HUMAN_PROFESSIONAL_PRIMARY_HOMOLOGY",
        "evidence_refs": [f"PRIMARY:human-review:{index + 1:04d}"],
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "historical_m0g_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
    }


class InterSourceGovernanceTests(unittest.TestCase):
    def test_no_confirmation_materializes_fail_closed_insufficiency(self):
        result = govern_correspondences(_candidate_payload())
        self.assertEqual(result["schema"], "CEW_CAL01_INTERSOURCE_GOVERNED_CORRESPONDENCES_v1")
        self.assertEqual(result["governed_correspondence_count"], 0)
        self.assertEqual(result["readiness_state"], "INSUFFICIENT_INTERSOURCE_CORRESPONDENCES")
        self.assertEqual(result["missing_conditions"], ["MINIMUM_GOVERNED_CORRESPONDENCES_4"])
        self.assertEqual(result["next_action"], "TARGETED_INTERSOURCE_HUMAN_REVIEW")
        self.assertFalse(result["eligible_for_registration_fit"])
        self.assertEqual(result["authority"], AUTHORITY_CLOSED)

    def test_four_exact_human_decisions_create_governed_pairs_but_not_fit_authority(self):
        decisions = [_decision(index) for index in range(4)]
        result = govern_correspondences(_candidate_payload(), decisions)
        self.assertEqual(result["governed_correspondence_count"], 4)
        self.assertEqual(result["readiness_state"], "READY_FOR_REGISTRATION_SPLIT")
        self.assertEqual(result["missing_conditions"], [])
        self.assertTrue(result["eligible_for_registration_split"])
        self.assertFalse(result["eligible_for_registration_fit"])
        first = result["correspondences"][0]
        self.assertEqual(first["occurrence_id"], "COL-OCC-0001")
        self.assertEqual(first["tav5_source_point_px"], [120.0, 230.0])
        self.assertEqual(first["tav5_source_frame"], "RASTER_PIXEL")
        self.assertEqual(first["tav02_lattice_node_id"], "TAV-02S:LATTICE:X0:Y0")
        self.assertEqual(first["tav02_source_point_normalized_px"], [1000.0, 2000.0])
        self.assertEqual(first["tav02_source_frame"], "NORMALIZED_RASTER_PIXEL")
        self.assertEqual(first["validation_state"], "PRIMARY_HOMOLOGY_VALIDATED")
        self.assertFalse(first["fit_eligible"])
        self.assertEqual(result["authority"], AUTHORITY_CLOSED)

    def test_unconfirmed_automatic_proposals_never_become_governed(self):
        result = govern_correspondences(_candidate_payload(proposal=True))
        self.assertEqual(result["governed_correspondence_count"], 0)
        self.assertEqual(result["readiness_state"], "INSUFFICIENT_INTERSOURCE_CORRESPONDENCES")
        self.assertTrue(all(row["governed_correspondence"] is False for row in result["unconfirmed_candidates"]))

    def test_historical_affine_or_m0g_provenance_is_rejected(self):
        historical_affine = _decision(0)
        historical_affine["historical_affine_loaded"] = True
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN"):
            govern_correspondences(_candidate_payload(), [historical_affine])

        historical_m0g = _decision(0)
        historical_m0g["evidence_refs"] = ["M0-G:N001"]
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_HISTORICAL_INPUT_FORBIDDEN"):
            govern_correspondences(_candidate_payload(), [historical_m0g])

    def test_source_raster_or_exact_point_drift_fails_closed(self):
        bad_source = _decision(0)
        bad_source["tav5_source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_DECISION_SOURCE_DRIFT"):
            govern_correspondences(_candidate_payload(), [bad_source])

        bad_raster = _decision(0)
        bad_raster["tav5_raster_sha256"] = "1" * 64
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_DECISION_RASTER_DRIFT"):
            govern_correspondences(_candidate_payload(), [bad_raster])

        bad_point = _decision(0)
        bad_point["tav5_source_point_px"] = [121.0, 230.0]
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_DECISION_POINT_DRIFT"):
            govern_correspondences(_candidate_payload(), [bad_point])

    def test_duplicate_conflicting_source_or_target_partner_fails_closed(self):
        conflict_source = [_decision(0, 0), _decision(0, 1)]
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_CONFLICTING_PARTNER"):
            govern_correspondences(_candidate_payload(), conflict_source)

        conflict_target = [_decision(0, 0), _decision(1, 0)]
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_CONFLICTING_PARTNER"):
            govern_correspondences(_candidate_payload(), conflict_target)

    def test_decision_order_does_not_change_governed_digest(self):
        decisions = [_decision(index) for index in range(4)]
        forward = govern_correspondences(_candidate_payload(), decisions)
        reverse = govern_correspondences(_candidate_payload(), list(reversed(decisions)))
        self.assertEqual(forward["governed_digest"], reverse["governed_digest"])
        self.assertEqual(forward["correspondences"], reverse["correspondences"])

    def test_review_packet_is_deterministic_and_contains_no_suggested_identity(self):
        candidates = _candidate_payload(count=3)
        packet = build_correspondence_review_packet(candidates)
        self.assertEqual(packet["schema"], "CEW_CAL01_INTERSOURCE_HUMAN_REVIEW_PACKET_v1")
        self.assertEqual(packet["review_item_count"], 3)
        self.assertEqual(packet["target_lattice_node_count"], 3)
        serialized = repr(packet).lower()
        self.assertNotIn("suggested_identity", serialized)
        self.assertNotIn("support_identifier", serialized)
        self.assertNotIn("nearest", serialized)
        self.assertFalse(packet["historical_comparator_loaded"])
        self.assertFalse(packet["historical_affine_loaded"])
        self.assertEqual(packet["authority"], AUTHORITY_CLOSED)


if __name__ == "__main__":
    unittest.main()
