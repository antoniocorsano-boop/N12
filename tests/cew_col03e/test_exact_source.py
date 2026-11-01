from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

try:
    from experiments.cew_col03e.exact_source import (
        build_exact_source_artifacts,
        write_col03e_artifacts,
    )
except (ImportError, ModuleNotFoundError):
    build_exact_source_artifacts = None
    write_col03e_artifacts = None


PREDECESSOR_SHA = "df4a0a38d00d18dace597e9ca1cf449edfefca03"
EXPECTED_OUTPUTS = {
    "identity-adjudication-dossiers.json",
    "identity-adjudication-readiness.json",
    "identity-adjudication-closure.json",
}
AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "vertical_chain_assignment_authorized",
    "structural_identity_authorized",
    "canonical_node_assignment_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)


def _inputs():
    b_rows = []
    c_rows = []
    for index in range(1, 23):
        b_hypotheses = []
        if index == 1:
            b_hypotheses = [{"candidate_value": "4", "state": "SINGLE_CHANNEL", "promotion_authorized": False}]
        elif index == 15:
            b_hypotheses = [{"candidate_value": "30", "state": "SINGLE_CHANNEL", "promotion_authorized": False}]
        b_rows.append({"occurrence_id": f"COL-OCC-{index:04d}", "hypotheses": b_hypotheses, "conflict_state": "NONE"})
        c_rows.append({
            "occurrence_id": f"COL-OCC-{index:04d}",
            "hypotheses": [],
            "conflict_state": "NONE",
            "tav07_match_state": "EVALUATED_NO_MATCH",
            "tav07_source_state": "MATERIALIZED_VERIFIED",
            "cross_document_identity_resolved": False,
        })
    note = "armatura di tipo documentata in TAV7; associazione al singolo pilastro non ancora dimostrata"
    quality = {
        "status": "EVIDENCE_ONLY",
        "blocking_findings": ["COLUMN_ASSOCIATION_NOT_DEMONSTRATED"],
        "historical_row_level_evidence_recovered": True,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "csv_evidence": [
            {
                "artifact_name": "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
                "row_count": 27,
                "source_sha256": "association-sha",
                "records": [
                    {"source_row_number": n, "values": {"id_predoc": f"N{n - 1:03d}", "nota": note}}
                    for n in range(2, 29)
                ],
            },
            {
                "artifact_name": "MATRICE_PILASTRI_27x5_v22.csv",
                "row_count": 135,
                "source_sha256": "matrix-sha",
                "records": [],
            },
        ],
    }
    return {"occurrence_count": 22, "occurrences": b_rows}, {"occurrence_count": 22, "occurrences": c_rows}, quality


class ExactSourceArtifactTests(unittest.TestCase):
    def test_exact_source_emits_three_governed_artifacts_and_no_identity_promotion(self):
        self.assertIsNotNone(build_exact_source_artifacts, "COL-03E exact-source builder missing")
        b, c, q = _inputs()
        artifacts = build_exact_source_artifacts(
            col03b_ledger=b,
            col03c_ledger=c,
            historical_quality=q,
            predecessor_sha=PREDECESSOR_SHA,
        )
        self.assertEqual(set(artifacts), EXPECTED_OUTPUTS)

        dossiers = artifacts["identity-adjudication-dossiers.json"]
        readiness = artifacts["identity-adjudication-readiness.json"]
        closure = artifacts["identity-adjudication-closure.json"]

        self.assertEqual(dossiers["occurrence_count"], 22)
        self.assertEqual(len(dossiers["dossiers"]), 22)
        self.assertEqual(readiness["state_counts"], {"INSUFFICIENT_EVIDENCE": 22})
        self.assertEqual(readiness["ready_for_human_review_count"], 0)
        self.assertEqual(readiness["documentary_candidate_occurrence_ids"], ["COL-OCC-0001", "COL-OCC-0015"])
        self.assertTrue(closure["adjudication_dossiers_complete"])
        self.assertFalse(closure["any_identity_resolved"])
        self.assertEqual(closure["qualification_blockers"], [])
        self.assertEqual(
            closure["identity_resolution_blockers"],
            ["NO_GOVERNED_HISTORICAL_BRIDGE", "NO_TAV07_CROSS_DOCUMENT_MATCH"],
        )
        self.assertEqual(closure["next_required_action"], "ACQUIRE_NEW_IDENTITY_BRIDGE_EVIDENCE")
        for key in AUTHORITY_KEYS:
            self.assertFalse(closure[key], key)

    def test_writer_is_byte_deterministic_and_limits_output_surface(self):
        self.assertIsNotNone(build_exact_source_artifacts)
        self.assertIsNotNone(write_col03e_artifacts, "COL-03E exact-source writer missing")
        b, c, q = _inputs()
        first = build_exact_source_artifacts(
            col03b_ledger=b,
            col03c_ledger=c,
            historical_quality=q,
            predecessor_sha=PREDECESSOR_SHA,
        )
        second = build_exact_source_artifacts(
            col03b_ledger=b,
            col03c_ledger=c,
            historical_quality=q,
            predecessor_sha=PREDECESSOR_SHA,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "evidence" / "cew-col03e"
            first_written = write_col03e_artifacts(root, first)
            first_digests = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first_written}
            second_written = write_col03e_artifacts(root, second)
            second_digests = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in second_written}
            self.assertEqual(first_digests, second_digests)
            self.assertEqual({p.name for p in root.iterdir()}, EXPECTED_OUTPUTS)

    def test_wrong_predecessor_sha_fails_closed(self):
        self.assertIsNotNone(build_exact_source_artifacts)
        b, c, q = _inputs()
        with self.assertRaisesRegex(ValueError, "COL03E_PREDECESSOR_SHA_DRIFT"):
            build_exact_source_artifacts(
                col03b_ledger=b,
                col03c_ledger=c,
                historical_quality=q,
                predecessor_sha="wrong",
            )


if __name__ == "__main__":
    unittest.main()
