import copy
import unittest

from experiments.cew_cal01.intersource_split import freeze_registration_split


AUTHORITY_CLOSED = {
    "structural_identity_authorized": False,
    "canonical_geometry_authorized": False,
    "canonical_write_authorized": False,
    "m0g_authorized": False,
    "engineering_authority_effect": "NONE",
}


def _governed(points=None):
    points = points or [
        ([0.0, 0.0], [100.0, 200.0]),
        ([10.0, 0.0], [1100.0, 200.0]),
        ([0.0, 10.0], [100.0, 1200.0]),
        ([10.0, 10.0], [1100.0, 1200.0]),
        ([5.0, 14.0], [600.0, 1600.0]),
    ]
    rows = []
    for index, (source, target) in enumerate(points):
        rows.append(
            {
                "correspondence_id": f"CEW-CAL01-CORR-{index + 1:02d}",
                "occurrence_id": f"COL-OCC-{index + 1:04d}",
                "tav5_source_point_px": list(source),
                "tav5_source_frame": "RASTER_PIXEL",
                "tav02_lattice_node_id": f"TAV-02S:LATTICE:X{index}:Y0",
                "tav02_source_point_normalized_px": list(target),
                "tav02_source_frame": "NORMALIZED_RASTER_PIXEL",
                "tav02_local_metric_xy_m": [float(index), float(index % 2)],
                "validation_state": "PRIMARY_HOMOLOGY_VALIDATED",
                "validation_basis": "HUMAN_PROFESSIONAL_CONFIRMATION",
                "governed_correspondence": True,
                "fit_eligible": False,
                "authority": dict(AUTHORITY_CLOSED),
            }
        )
    count = len(rows)
    return {
        "schema": "CEW_CAL01_INTERSOURCE_GOVERNED_CORRESPONDENCES_v1",
        "program": "CEW-CAL-01",
        "candidate_digest": "sha256:" + "c" * 64,
        "tav5_source": {"sha256": "sha256:tav5-primary"},
        "tav5_raster": {"frame": "RASTER_PIXEL", "raster_sha256": "sha256:tav5-raster"},
        "tav02_source": {"source_id": "TAV-02S", "sha256": "sha256:tav02-primary"},
        "tav02_lattice_digest": "sha256:" + "d" * 64,
        "governed_correspondence_count": count,
        "correspondences": rows,
        "unconfirmed_candidate_count": 0,
        "unconfirmed_candidates": [],
        "readiness_state": "READY_FOR_REGISTRATION_SPLIT" if count >= 4 else "INSUFFICIENT_INTERSOURCE_CORRESPONDENCES",
        "missing_conditions": [] if count >= 4 else ["MINIMUM_GOVERNED_CORRESPONDENCES_4"],
        "next_action": "FREEZE_REGISTRATION_SPLIT" if count >= 4 else "TARGETED_INTERSOURCE_HUMAN_REVIEW",
        "eligible_for_registration_split": count >= 4,
        "eligible_for_registration_fit": False,
        "historical_comparator_loaded": False,
        "historical_affine_loaded": False,
        "historical_m0g_loaded": False,
        "authority": dict(AUTHORITY_CLOSED),
        "governed_digest": "sha256:" + "g" * 64,
    }


class InterSourceRegistrationSplitTests(unittest.TestCase):
    def test_five_governed_pairs_freeze_four_fit_and_one_holdout(self):
        result = freeze_registration_split(_governed())
        self.assertEqual(result["schema"], "CEW_CAL01_INTERSOURCE_REGISTRATION_SPLIT_v1")
        self.assertEqual(result["state"], "REGISTRATION_SPLIT_FROZEN")
        self.assertEqual(result["governed_correspondence_count"], 5)
        self.assertEqual(result["fit_count"], 4)
        self.assertEqual(result["holdout_count"], 1)
        self.assertTrue(result["ready_for_affine_fit"])
        self.assertFalse(result["affine_fit_performed"])
        self.assertFalse(result["eligible_for_metric_anchor_promotion"])
        self.assertEqual(result["next_action"], "BUILD_INTERSOURCE_AFFINE_REGISTRATION")
        self.assertEqual(result["authority"], AUTHORITY_CLOSED)

        fit_ids = set(result["fit_correspondence_ids"])
        holdout_ids = set(result["holdout_correspondence_ids"])
        all_ids = {row["correspondence_id"] for row in _governed()["correspondences"]}
        self.assertFalse(fit_ids & holdout_ids)
        self.assertEqual(fit_ids | holdout_ids, all_ids)
        self.assertEqual(len(fit_ids), 4)
        self.assertEqual(len(holdout_ids), 1)

    def test_minimum_four_pairs_freeze_three_fit_and_one_holdout(self):
        payload = _governed()
        payload["correspondences"] = payload["correspondences"][:4]
        payload["governed_correspondence_count"] = 4
        result = freeze_registration_split(payload)
        self.assertEqual(result["fit_count"], 3)
        self.assertEqual(result["holdout_count"], 1)
        self.assertTrue(result["source_fit_geometry_noncollinear"])
        self.assertTrue(result["target_fit_geometry_noncollinear"])

    def test_fewer_than_four_pairs_fail_closed_before_fit(self):
        payload = _governed(points=[
            ([0.0, 0.0], [0.0, 0.0]),
            ([10.0, 0.0], [10.0, 0.0]),
            ([0.0, 10.0], [0.0, 10.0]),
        ])
        result = freeze_registration_split(payload)
        self.assertEqual(result["state"], "INSUFFICIENT_INTERSOURCE_CORRESPONDENCES")
        self.assertEqual(result["missing_conditions"], ["MINIMUM_GOVERNED_CORRESPONDENCES_4"])
        self.assertEqual(result["fit_count"], 0)
        self.assertEqual(result["holdout_count"], 0)
        self.assertFalse(result["ready_for_affine_fit"])
        self.assertFalse(result["affine_fit_performed"])

    def test_collinear_fit_geometry_fails_closed_in_source_or_target_frame(self):
        source_collinear = _governed(points=[
            ([0.0, 0.0], [0.0, 0.0]),
            ([10.0, 0.0], [10.0, 0.0]),
            ([20.0, 0.0], [0.0, 10.0]),
            ([30.0, 0.0], [10.0, 10.0]),
        ])
        result = freeze_registration_split(source_collinear)
        self.assertEqual(result["state"], "INSUFFICIENT_INTERSOURCE_CORRESPONDENCES")
        self.assertIn("NONCOLLINEAR_SOURCE_FIT_GEOMETRY_REQUIRED", result["missing_conditions"])

        target_collinear = _governed(points=[
            ([0.0, 0.0], [0.0, 0.0]),
            ([10.0, 0.0], [10.0, 0.0]),
            ([0.0, 10.0], [20.0, 0.0]),
            ([10.0, 10.0], [30.0, 0.0]),
        ])
        result = freeze_registration_split(target_collinear)
        self.assertEqual(result["state"], "INSUFFICIENT_INTERSOURCE_CORRESPONDENCES")
        self.assertIn("NONCOLLINEAR_TARGET_FIT_GEOMETRY_REQUIRED", result["missing_conditions"])

    def test_input_order_and_residual_fields_cannot_change_frozen_split(self):
        baseline = _governed()
        altered = copy.deepcopy(baseline)
        altered["correspondences"] = list(reversed(altered["correspondences"]))
        for index, row in enumerate(altered["correspondences"]):
            row["residual_px"] = 10000.0 - index * 777.0
            row["residual_m"] = index * 99.0
        first = freeze_registration_split(baseline)
        second = freeze_registration_split(altered)
        self.assertEqual(first["fit_correspondence_ids"], second["fit_correspondence_ids"])
        self.assertEqual(first["holdout_correspondence_ids"], second["holdout_correspondence_ids"])
        self.assertEqual(first["split_digest"], second["split_digest"])

    def test_split_rejects_authority_or_historical_input_escalation(self):
        historical = _governed()
        historical["historical_affine_loaded"] = True
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_SPLIT_HISTORICAL_INPUT_FORBIDDEN"):
            freeze_registration_split(historical)

        elevated = _governed()
        elevated["authority"]["canonical_geometry_authorized"] = True
        with self.assertRaisesRegex(ValueError, "CAL01_INTERSOURCE_SPLIT_AUTHORITY_ESCALATION"):
            freeze_registration_split(elevated)

    def test_split_is_bound_to_exact_governed_points_and_preserves_frames(self):
        result = freeze_registration_split(_governed())
        rows = {row["correspondence_id"]: row for row in result["frozen_correspondences"]}
        original = {row["correspondence_id"]: row for row in _governed()["correspondences"]}
        for correspondence_id, row in rows.items():
            source = original[correspondence_id]
            self.assertEqual(row["tav5_source_point_px"], source["tav5_source_point_px"])
            self.assertEqual(row["tav5_source_frame"], "RASTER_PIXEL")
            self.assertEqual(row["tav02_source_point_normalized_px"], source["tav02_source_point_normalized_px"])
            self.assertEqual(row["tav02_source_frame"], "NORMALIZED_RASTER_PIXEL")
            self.assertIn(row["split_role"], {"FIT", "HOLDOUT"})


if __name__ == "__main__":
    unittest.main()
