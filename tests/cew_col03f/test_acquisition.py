from __future__ import annotations

import unittest

try:
    from experiments.cew_col03f.acquisition import (
        build_primary_bridge_ledger,
        classify_acquisition_state,
        inspection_priority,
    )
except (ImportError, ModuleNotFoundError):
    build_primary_bridge_ledger = None
    classify_acquisition_state = None
    inspection_priority = None


def _obs(value: str, *, psm: str, relation: str = "INTERNAL", region: str = "FOOTPRINT") -> dict:
    return {
        "normalized_text": value,
        "raw_text": value,
        "ocr_configuration": psm,
        "relation": relation,
        "region_class": region,
        "exact_source_reconstructible": True,
        "provenance_ref": f"TEST:{region}:{psm}:{value}",
    }


def _occurrence_ledger() -> dict:
    rows = []
    for index in range(1, 23):
        rows.append(
            {
                "occurrence_id": f"COL-OCC-{index:04d}",
                "primary_graphical_representation": {
                    "bbox": {"x": 0.1, "y": 0.2, "width": 0.03, "height": 0.04}
                },
                "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
                "page_id": "CEW-N12-PAGE-TAV05S-P001",
                "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
            }
        )
    return {"occurrence_count": 22, "occurrences": rows}


def _documentary_ledger() -> dict:
    rows = []
    for index in range(1, 23):
        occurrence_id = f"COL-OCC-{index:04d}"
        hypotheses = []
        if index == 1:
            hypotheses = [{"candidate_value": "4"}]
        if index == 15:
            hypotheses = [{"candidate_value": "30"}]
        rows.append({"occurrence_id": occurrence_id, "hypotheses": hypotheses})
    return {"occurrence_count": 22, "occurrences": rows}


def _col03e_dossiers() -> dict:
    return {
        "occurrence_count": 22,
        "dossiers": [
            {
                "occurrence_id": f"COL-OCC-{index:04d}",
                "dossier_digest": f"digest-{index:04d}",
                "identity_promoted": False,
            }
            for index in range(1, 23)
        ],
    }


def _crop_manifests() -> dict:
    return {
        f"COL-OCC-{index:04d}": {
            "FOOTPRINT": {"bounds_px": [1, 2, 30, 40]},
            "LOCAL": {"bounds_px": [0, 0, 60, 80]},
            "CONTEXT": {"bounds_px": [0, 0, 100, 120]},
            "source_only_path": f"review/COL-OCC-{index:04d}-source-only.png",
            "source_only_sha256": "a" * 64,
            "target_overlay_path": f"review/COL-OCC-{index:04d}-target-overlay.png",
            "target_overlay_sha256": "b" * 64,
        }
        for index in range(1, 23)
    }


class AcquisitionClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(classify_acquisition_state, "COL-03F acquisition module missing")

    def test_existing_candidate_is_corroborated_only_by_matching_direct_observation(self):
        result = classify_acquisition_state(["4"], [_obs("4", psm="PSM6")])
        self.assertEqual(result["state"], "CORROBORATED_EXISTING_LABEL_CANDIDATE")
        self.assertEqual(result["candidate_values"], ["4"])

    def test_existing_candidate_without_direct_reobservation_stays_unresolved(self):
        result = classify_acquisition_state(["4"], [_obs("4", psm="PSM6", relation="NEARBY")])
        self.assertEqual(result["state"], "NO_DIRECT_LABEL_OBSERVED")
        self.assertEqual(result["candidate_values"], [])

    def test_different_direct_value_contradicts_existing_candidate(self):
        result = classify_acquisition_state(["30"], [_obs("31", psm="PSM6")])
        self.assertEqual(result["state"], "CONTRADICTS_EXISTING_DOCUMENTARY_CANDIDATE")
        self.assertEqual(result["candidate_values"], [])

    def test_new_value_requires_both_fixed_ocr_configurations(self):
        result = classify_acquisition_state(
            [],
            [_obs("12", psm="PSM6"), _obs("12", psm="PSM11", region="LOCAL")],
        )
        self.assertEqual(result["state"], "NEW_MULTI_CONFIG_LABEL_CANDIDATE")
        self.assertEqual(result["candidate_values"], ["12"])

    def test_single_configuration_direct_value_is_not_candidate(self):
        result = classify_acquisition_state([], [_obs("12", psm="PSM6")])
        self.assertEqual(result["state"], "SINGLE_CONFIG_DIRECT_OBSERVATION")
        self.assertEqual(result["candidate_values"], [])

    def test_multiple_direct_values_are_ambiguous(self):
        result = classify_acquisition_state(
            [],
            [_obs("12", psm="PSM6"), _obs("13", psm="PSM11")],
        )
        self.assertEqual(result["state"], "AMBIGUOUS_DIRECT_LABELS")
        self.assertEqual(result["candidate_values"], [])

    def test_historical_style_identifier_is_excluded_from_positive_candidate_surface(self):
        result = classify_acquisition_state(
            [],
            [_obs("N001", psm="PSM6"), _obs("N001", psm="PSM11")],
        )
        self.assertEqual(result["state"], "NO_DIRECT_LABEL_OBSERVED")
        self.assertEqual(result["candidate_values"], [])


class AcquisitionLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(inspection_priority, "COL-03F inspection priority missing")
        self.assertIsNotNone(build_primary_bridge_ledger, "COL-03F ledger builder missing")

    def test_priority_places_two_existing_documentary_candidates_first(self):
        occurrence_ids = [f"COL-OCC-{index:04d}" for index in range(1, 23)]
        result = inspection_priority(
            list(reversed(occurrence_ids)),
            {"COL-OCC-0015": ["30"], "COL-OCC-0001": ["4"]},
        )
        self.assertEqual(result[:2], ["COL-OCC-0001", "COL-OCC-0015"])
        self.assertEqual(result[2:], [oid for oid in occurrence_ids if oid not in {"COL-OCC-0001", "COL-OCC-0015"}])

    def test_ledger_preserves_22_occurrences_and_keeps_all_authority_closed(self):
        focused = {f"COL-OCC-{index:04d}": [] for index in range(1, 23)}
        focused["COL-OCC-0001"] = [_obs("4", psm="PSM6")]
        focused["COL-OCC-0015"] = [_obs("30", psm="PSM6")]
        ledger = build_primary_bridge_ledger(
            occurrence_ledger=_occurrence_ledger(),
            documentary_ledger=_documentary_ledger(),
            col03e_dossiers=_col03e_dossiers(),
            focused_observations=focused,
            source_ref={
                "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
                "page_id": "CEW-N12-PAGE-TAV05S-P001",
                "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
                "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
                "raster_sha256": "c" * 64,
                "raster_width_px": 7016,
                "raster_height_px": 12530,
            },
            crop_manifests=_crop_manifests(),
        )
        self.assertEqual(ledger["occurrence_count"], 22)
        self.assertEqual([row["occurrence_id"] for row in ledger["occurrences"]][:2], ["COL-OCC-0001", "COL-OCC-0015"])
        for row in ledger["occurrences"]:
            self.assertFalse(row["identity_promoted"])
            self.assertFalse(row["structural_identity_authorized"])
            self.assertFalse(row["canonical_geometry_authorized"])
            self.assertFalse(row["canonical_write_authorized"])
            self.assertNotIn("N001", row.get("candidate_values", []))


if __name__ == "__main__":
    unittest.main()
