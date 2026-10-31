from __future__ import annotations

import unittest

from experiments.cew_col03b.historical_correspondence import (
    build_cross_document_candidate,
    validate_historical_artifact_manifest,
)


class HistoricalCorrespondenceTests(unittest.TestCase):
    def test_manifest_requires_explicit_artifact_provenance(self) -> None:
        manifest = {
            "artifacts": [
                {
                    "artifact_id": "TAV7",
                    "path": "archive/TAV7_PILASTRI.dxf",
                    "version": "v25",
                    "sha256": "a" * 64,
                }
            ]
        }
        normalized = validate_historical_artifact_manifest(manifest)
        self.assertEqual(normalized["artifacts"][0]["artifact_id"], "TAV7")
        with self.assertRaisesRegex(ValueError, "provenance"):
            validate_historical_artifact_manifest(
                {"artifacts": [{"artifact_id": "TAV7", "path": "archive/TAV7_PILASTRI.dxf"}]}
            )

    def test_missing_transform_cannot_produce_supported_match(self) -> None:
        candidate = build_cross_document_candidate(
            occurrence_id="COL-OCC-0001",
            artifact_ref={"artifact_id": "TAV7", "path": "archive/TAV7_PILASTRI.dxf", "version": "v25", "sha256": "a" * 64},
            candidate_id="N012",
            matching_discriminants=["LOCAL_ORDER", "GEOMETRIC_POSITION"],
            conflicting_discriminants=[],
            transform_ref=None,
        )
        self.assertEqual(candidate["status"], "CANDIDATE")
        self.assertFalse(candidate["support_identity_authorized"])

    def test_independent_match_with_transform_is_only_cross_document_supported(self) -> None:
        candidate = build_cross_document_candidate(
            occurrence_id="COL-OCC-0001",
            artifact_ref={"artifact_id": "TAV7", "path": "archive/TAV7_PILASTRI.dxf", "version": "v25", "sha256": "a" * 64},
            candidate_id="N012",
            matching_discriminants=["LOCAL_ORDER", "GEOMETRIC_POSITION"],
            conflicting_discriminants=[],
            transform_ref={"transform_id": "HIST-TAV7-TO-TAV5-1", "method": "AFFINE_GOVERNED"},
        )
        self.assertEqual(candidate["status"], "SUPPORTED")
        self.assertEqual(candidate["evidence_class"], "INDEPENDENT_DOCUMENTARY_CORRESPONDENCE")
        self.assertEqual(candidate["candidate_id"], "N012")
        self.assertFalse(candidate["support_identity_authorized"])
        self.assertFalse(candidate["canonical_geometry_authorized"])

    def test_conflicting_discriminant_forces_contradicted(self) -> None:
        candidate = build_cross_document_candidate(
            occurrence_id="COL-OCC-0001",
            artifact_ref={"artifact_id": "M27X5", "path": "archive/MATRICE_PILASTRI_27x5_v22.csv", "version": "v22", "sha256": "b" * 64},
            candidate_id="CHAIN-04",
            matching_discriminants=["LOCAL_ORDER"],
            conflicting_discriminants=["SPAN_SIGNATURE"],
            transform_ref={"transform_id": "MATRIX-RECON-1", "method": "DOCUMENTARY_RECONCILIATION"},
        )
        self.assertEqual(candidate["status"], "CONTRADICTED")
        self.assertEqual(candidate["conflicting_discriminants"], ["SPAN_SIGNATURE"])

    def test_ambiguous_historical_target_never_promotes_identity(self) -> None:
        candidate = build_cross_document_candidate(
            occurrence_id="COL-OCC-0001",
            artifact_ref={
                "artifact_id": "TOPO",
                "path": "archive/ABACO_TOPOLOGICO_TAV5_v11.csv",
                "version": "v11",
                "sha256": "c" * 64,
                "competing_candidate_ids": ["N012", "N058"],
            },
            candidate_id="N012",
            matching_discriminants=["GEOMETRIC_POSITION"],
            conflicting_discriminants=[],
            transform_ref={"transform_id": "TOPO-TO-TAV5-1", "method": "AFFINE_GOVERNED"},
        )
        self.assertEqual(candidate["status"], "CANDIDATE")
        self.assertTrue(candidate["ambiguous"])
        self.assertFalse(candidate["support_identity_authorized"])


if __name__ == "__main__":
    unittest.main()
