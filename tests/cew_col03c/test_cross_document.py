from __future__ import annotations

from copy import deepcopy
import unittest

try:
    from experiments.cew_col03c.cross_document import (
        CLOSED_AUTHORITY_KEYS,
        build_cross_document_bundles,
        build_cross_document_closure,
        build_cross_document_reconciliation,
    )
except (ImportError, ModuleNotFoundError):
    CLOSED_AUTHORITY_KEYS = ()
    build_cross_document_bundles = None
    build_cross_document_closure = None
    build_cross_document_reconciliation = None


QUALIFIED_SHA = "cfd9382b703d0a974daf63c23dc2b6d3d81eadad"


def _occurrences():
    rows = []
    for index in range(1, 23):
        row = {
            "occurrence_id": f"COL-OCC-{index:04d}",
            "hypotheses": [],
            "exact_source_reconstructible": True,
            "lineage_complete": True,
        }
        if index == 1:
            row["hypotheses"] = [{
                "hypothesis_id": "COL03B-HYP-0001",
                "hypothesis_kind": "DOCUMENTARY_LABEL_CANDIDATE",
                "candidate_value": "4",
                "state": "SINGLE_CHANNEL",
                "promotion_authorized": False,
            }]
        if index == 15:
            row["hypotheses"] = [{
                "hypothesis_id": "COL03B-HYP-0015",
                "hypothesis_kind": "DOCUMENTARY_LABEL_CANDIDATE",
                "candidate_value": "30",
                "state": "SINGLE_CHANNEL",
                "promotion_authorized": False,
            }]
        rows.append(row)
    return rows


def _source():
    return {
        "catalogue_id": "TAV-07A",
        "archive_commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
        "source_path": "archive/documentazione_originaria/tavola7.pdf",
        "sha256": "38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b",
        "materialization_state": "MATERIALIZED_VERIFIED",
        "authority": "PRIMARY_DOCUMENTARY_SOURCE",
        "identity_promotion_authorized": False,
    }


def _observations(*, duplicate_30: bool = False):
    rows = [
        {
            "observation_id": "TAV07-OBS-A",
            "normalized_text": "4",
            "binding_state": "UNBOUND",
            "identity_promotion_authorized": False,
            "page_index": 0,
            "bbox": {"x": 0.1, "y": 0.1, "width": 0.02, "height": 0.02},
        },
        {
            "observation_id": "TAV07-OBS-B",
            "normalized_text": "30",
            "binding_state": "UNBOUND",
            "identity_promotion_authorized": False,
            "page_index": 0,
            "bbox": {"x": 0.2, "y": 0.2, "width": 0.02, "height": 0.02},
        },
        {
            "observation_id": "TAV07-OBS-X",
            "normalized_text": "SEZIONE A-A",
            "binding_state": "UNBOUND",
            "identity_promotion_authorized": False,
            "page_index": 0,
            "bbox": {"x": 0.7, "y": 0.7, "width": 0.1, "height": 0.02},
        },
    ]
    if duplicate_30:
        rows.append({
            "observation_id": "TAV07-OBS-C",
            "normalized_text": "30",
            "binding_state": "UNBOUND",
            "identity_promotion_authorized": False,
            "page_index": 0,
            "bbox": {"x": 0.8, "y": 0.4, "width": 0.02, "height": 0.02},
        })
    return rows


def _historical():
    names = [
        "TAV7_PILASTRI.dxf",
        "ABACO_TOPOLOGICO_TAV5_v11.csv",
        "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
        "MATRICE_PILASTRI_27x5_v22.csv",
    ]
    return [
        {
            "artifact_name": name,
            "materialization_state": "KNOWN_INVENTORY_NOT_MATERIALIZED",
            "bytes_available": False,
            "row_level_evidence_usable": False,
            "authority": "REFERENCE_ONLY",
            "inventory_source_ref": "commit:643dc893:archive/ARTEFATTI_STORICI.md",
        }
        for name in names
    ]


def _derived():
    return {
        "topology_reference": {
            "identity_use_state": "DATA_QUALITY_BLOCKED",
            "identity_evidence_usable": False,
            "unresolved_endpoint_ids": ["N058", "N059"],
            "authority": "REFERENCE_ONLY",
        },
        "candidate_matrix_reference": {
            "reference_role": "CANDIDATE_HYPOTHESES_ONLY",
            "historical_27x5_matrix": False,
            "identity_evidence_usable": False,
            "authority": "REFERENCE_ONLY",
        },
    }


def _bundles(*, duplicate_30: bool = False):
    return build_cross_document_bundles(
        predecessor_occurrences=_occurrences(),
        tav07_source=_source(),
        tav07_observations=_observations(duplicate_30=duplicate_30),
        historical_artifacts=_historical(),
        derived_reference_quality=_derived(),
    )


class CrossDocumentTests(unittest.TestCase):
    def test_exactly_22_governed_subjects_are_preserved(self):
        self.assertIsNotNone(build_cross_document_bundles, "cross-document implementation missing")
        bundles = _bundles()
        self.assertEqual(len(bundles), 22)
        self.assertEqual([row["occurrence_id"] for row in bundles], [f"COL-OCC-{i:04d}" for i in range(1, 23)])

    def test_primary_source_availability_is_recorded_independently_of_match(self):
        self.assertIsNotNone(build_cross_document_bundles, "cross-document implementation missing")
        bundles = _bundles()
        row = next(item for item in bundles if item["occurrence_id"] == "COL-OCC-0002")
        self.assertEqual(row["tav07_source_state"], "MATERIALIZED_VERIFIED")
        self.assertEqual(row["tav07_match_state"], "EVALUATED_NO_MATCH")
        self.assertEqual(row["hypotheses"], [])

    def test_inventory_only_history_is_recovery_gap_not_negative_evidence(self):
        self.assertIsNotNone(build_cross_document_bundles, "cross-document implementation missing")
        row = _bundles()[0]
        self.assertEqual(len(row["historical_recovery_gaps"]), 4)
        for gap in row["historical_recovery_gaps"]:
            self.assertEqual(gap["materialization_state"], "KNOWN_INVENTORY_NOT_MATERIALIZED")
            self.assertNotEqual(gap.get("evidence_class"), "NO_EVIDENCE")
            self.assertFalse(gap["row_level_evidence_usable"])

    def test_blocked_topology_cannot_support_identity_hypothesis(self):
        self.assertIsNotNone(build_cross_document_bundles, "cross-document implementation missing")
        row = _bundles()[0]
        self.assertEqual(row["derived_reference_state"]["topology_reference"]["identity_use_state"], "DATA_QUALITY_BLOCKED")
        for hypothesis in row["hypotheses"]:
            self.assertNotIn("topology_reference", hypothesis["supporting_channels"])

    def test_exact_label_match_creates_candidate_only(self):
        self.assertIsNotNone(build_cross_document_bundles, "cross-document implementation missing")
        row = next(item for item in _bundles() if item["occurrence_id"] == "COL-OCC-0001")
        self.assertEqual(row["tav07_match_state"], "SINGLE_CANDIDATE")
        self.assertEqual(len(row["hypotheses"]), 1)
        hypothesis = row["hypotheses"][0]
        self.assertEqual(hypothesis["hypothesis_kind"], "CROSS_DOCUMENT_LABEL_CANDIDATE")
        self.assertEqual(hypothesis["candidate_value"], "4")
        self.assertEqual(hypothesis["supporting_evidence_ids"], ["COL03B-HYP-0001", "TAV07-OBS-A"])
        self.assertEqual(hypothesis["supporting_channels"], ["COL03B_DOCUMENTARY_LABEL", "TAV07_EXACT_LABEL"])
        self.assertFalse(hypothesis["promotion_authorized"])
        self.assertFalse(row["cross_document_identity_resolved"])

    def test_duplicate_tav07_label_is_ambiguous_not_auto_selected(self):
        self.assertIsNotNone(build_cross_document_bundles, "cross-document implementation missing")
        row = next(item for item in _bundles(duplicate_30=True) if item["occurrence_id"] == "COL-OCC-0015")
        self.assertEqual(row["tav07_match_state"], "AMBIGUOUS")
        self.assertEqual(row["conflict_state"], "AMBIGUOUS_CROSS_DOCUMENT_MATCH")
        self.assertEqual(len(row["hypotheses"]), 1)
        self.assertEqual(row["hypotheses"][0]["state"], "AMBIGUOUS")
        self.assertEqual(row["hypotheses"][0]["supporting_evidence_ids"], ["COL03B-HYP-0015", "TAV07-OBS-B", "TAV07-OBS-C"])
        self.assertFalse(row["cross_document_identity_resolved"])

    def test_bundle_output_is_input_order_invariant(self):
        self.assertIsNotNone(build_cross_document_bundles, "cross-document implementation missing")
        first = build_cross_document_bundles(
            predecessor_occurrences=_occurrences(),
            tav07_source=_source(),
            tav07_observations=_observations(),
            historical_artifacts=_historical(),
            derived_reference_quality=_derived(),
        )
        second = build_cross_document_bundles(
            predecessor_occurrences=list(reversed(_occurrences())),
            tav07_source=deepcopy(_source()),
            tav07_observations=list(reversed(_observations())),
            historical_artifacts=list(reversed(_historical())),
            derived_reference_quality=deepcopy(_derived()),
        )
        self.assertEqual(first, second)

    def test_reconciliation_separates_recovery_from_evaluation_and_review(self):
        self.assertIsNotNone(build_cross_document_reconciliation, "cross-document implementation missing")
        bundles = _bundles(duplicate_30=True)
        result = build_cross_document_reconciliation(
            bundles=bundles,
            historical_artifacts=_historical(),
            derived_reference_quality=_derived(),
            tav07_source=_source(),
        )
        self.assertEqual(result["occurrence_count"], 22)
        self.assertEqual(result["tav07_source_state"], "MATERIALIZED_VERIFIED")
        self.assertFalse(result["historical_derived_artifact_recovery_complete"])
        self.assertIn("COL-OCC-0015", result["ambiguous_occurrence_ids"])
        self.assertTrue(result["human_review_required"])
        self.assertEqual(len(result["bundle_digest"]), 64)

    def test_closure_can_complete_available_evaluation_while_identity_and_recovery_remain_open(self):
        self.assertIsNotNone(build_cross_document_closure, "cross-document implementation missing")
        bundles = _bundles()
        reconciliation = build_cross_document_reconciliation(
            bundles=bundles,
            historical_artifacts=_historical(),
            derived_reference_quality=_derived(),
            tav07_source=_source(),
        )
        closure = build_cross_document_closure(
            bundles=bundles,
            reconciliation=reconciliation,
            qualified_col03b_sha=QUALIFIED_SHA,
        )
        self.assertTrue(closure["available_cross_document_evidence_evaluated"])
        self.assertFalse(closure["historical_derived_artifact_recovery_complete"])
        self.assertFalse(closure["all_occurrences_cross_document_resolved"])
        self.assertEqual(closure["blocking_reasons"], [])
        for key in CLOSED_AUTHORITY_KEYS:
            self.assertFalse(closure["authority"][key], key)

    def test_wrong_predecessor_or_authority_drift_blocks_closure(self):
        self.assertIsNotNone(build_cross_document_closure, "cross-document implementation missing")
        bundles = _bundles()
        reconciliation = build_cross_document_reconciliation(
            bundles=bundles,
            historical_artifacts=_historical(),
            derived_reference_quality=_derived(),
            tav07_source=_source(),
        )
        wrong_sha = build_cross_document_closure(
            bundles=bundles,
            reconciliation=reconciliation,
            qualified_col03b_sha="0" * 40,
        )
        self.assertFalse(wrong_sha["available_cross_document_evidence_evaluated"])
        self.assertIn("QUALIFIED_BASE_SHA_DRIFT", wrong_sha["blocking_reasons"])

        drifted = deepcopy(bundles)
        drifted[0]["structural_identity_authorized"] = True
        drift = build_cross_document_closure(
            bundles=drifted,
            reconciliation=reconciliation,
            qualified_col03b_sha=QUALIFIED_SHA,
        )
        self.assertFalse(drift["available_cross_document_evidence_evaluated"])
        self.assertIn("AUTHORITY_DRIFT", drift["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
