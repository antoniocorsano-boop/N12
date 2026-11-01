from __future__ import annotations

from copy import deepcopy
import re
import unittest

try:
    from experiments.cew_col03e.adjudication import (
        build_adjudication_dossiers,
        classify_review_readiness,
    )
except (ImportError, ModuleNotFoundError):
    build_adjudication_dossiers = None
    classify_review_readiness = None


PREDECESSOR_SHA = "df4a0a38d00d18dace597e9ca1cf449edfefca03"
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


def _col03b_ledger():
    rows = []
    for index in range(1, 23):
        hypotheses = []
        if index == 1:
            hypotheses = [{
                "candidate_value": "4",
                "state": "SINGLE_CHANNEL",
                "promotion_authorized": False,
                "supporting_evidence_ids": ["TXT-001"],
            }]
        elif index == 15:
            hypotheses = [{
                "candidate_value": "30",
                "state": "SINGLE_CHANNEL",
                "promotion_authorized": False,
                "supporting_evidence_ids": ["TXT-006"],
            }]
        rows.append({
            "occurrence_id": f"COL-OCC-{index:04d}",
            "hypotheses": hypotheses,
            "conflict_state": "NONE",
        })
    return {"occurrence_count": 22, "occurrences": rows}


def _col03c_ledger():
    return {
        "occurrence_count": 22,
        "occurrences": [
            {
                "occurrence_id": f"COL-OCC-{index:04d}",
                "conflict_state": "NONE",
                "tav07_match_state": "EVALUATED_NO_MATCH",
                "tav07_source_state": "MATERIALIZED_VERIFIED",
                "hypotheses": [],
                "cross_document_identity_resolved": False,
            }
            for index in range(1, 23)
        ],
    }


def _historical_quality():
    note = "armatura di tipo documentata in TAV7; associazione al singolo pilastro non ancora dimostrata"
    return {
        "status": "EVIDENCE_ONLY",
        "blocking_findings": [
            "BEAM_ASSOCIATION_GEOMETRY_ONLY",
            "COLUMN_ASSOCIATION_NOT_DEMONSTRATED",
        ],
        "historical_row_level_evidence_recovered": True,
        "csv_evidence": [
            {
                "artifact_name": "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
                "authority": "HISTORICAL_DERIVED_EVIDENCE",
                "promotion_authorized": False,
                "structural_identity_authorized": False,
                "row_count": 27,
                "source_sha256": "hist-association-sha",
                "records": [
                    {
                        "source_row_number": row_number,
                        "values": {
                            "id_predoc": f"N{row_number - 1:03d}",
                            "sigla_TAV5": "",
                            "ordine_TAV7": "",
                            "sezione_DOC": "",
                            "stato_associazione": "VER",
                            "nota": note,
                        },
                    }
                    for row_number in range(2, 29)
                ],
            },
            {
                "artifact_name": "MATRICE_PILASTRI_27x5_v22.csv",
                "authority": "HISTORICAL_DERIVED_EVIDENCE",
                "promotion_authorized": False,
                "structural_identity_authorized": False,
                "row_count": 135,
                "source_sha256": "matrix-sha",
                "records": [],
            },
        ],
    }


class AdjudicationDossierTests(unittest.TestCase):
    def test_current_real_evidence_yields_22_insufficient_dossiers_without_identity_promotion(self):
        self.assertIsNotNone(build_adjudication_dossiers, "COL-03E dossier builder missing")
        dossiers = build_adjudication_dossiers(
            col03b_ledger=_col03b_ledger(),
            col03c_ledger=_col03c_ledger(),
            historical_quality=_historical_quality(),
            predecessor_sha=PREDECESSOR_SHA,
        )
        self.assertEqual(len(dossiers), 22)
        self.assertEqual([row["occurrence_id"] for row in dossiers], [f"COL-OCC-{i:04d}" for i in range(1, 23)])
        self.assertEqual({row["review_readiness_state"] for row in dossiers}, {"INSUFFICIENT_EVIDENCE"})
        self.assertEqual(dossiers[0]["documentary_candidates"], ["4"])
        self.assertEqual(dossiers[14]["documentary_candidates"], ["30"])
        self.assertEqual(dossiers[1]["documentary_candidates"], [])
        self.assertTrue(all(row["cross_document_candidates"] == [] for row in dossiers))
        for row in dossiers:
            self.assertRegex(row["dossier_digest"], re.compile(r"^[0-9a-f]{64}$"))
            self.assertFalse(row["identity_promoted"])
            for key in AUTHORITY_KEYS:
                self.assertFalse(row[key], (row["occurrence_id"], key))

    def test_unbound_historical_rows_remain_context_and_do_not_create_occurrence_identity(self):
        self.assertIsNotNone(build_adjudication_dossiers)
        dossiers = build_adjudication_dossiers(
            col03b_ledger=_col03b_ledger(),
            col03c_ledger=_col03c_ledger(),
            historical_quality=_historical_quality(),
            predecessor_sha=PREDECESSOR_SHA,
        )
        first = dossiers[0]
        context = first["unbound_historical_context"]
        self.assertEqual(context["bridge_state"], "UNBOUND")
        self.assertEqual(context["column_association_row_count"], 27)
        self.assertEqual(context["historical_matrix_row_count"], 135)
        self.assertEqual(context["association_not_demonstrated_row_count"], 27)
        self.assertIn("COLUMN_ASSOCIATION_NOT_DEMONSTRATED", context["blocking_findings"])
        self.assertNotIn("N001", first.get("occurrence_specific_historical_ids", []))
        self.assertIn("NO_TAV07_CROSS_DOCUMENT_MATCH", first["missing_evidence"])

    def test_dossier_build_is_input_order_invariant(self):
        self.assertIsNotNone(build_adjudication_dossiers)
        b = _col03b_ledger()
        c = _col03c_ledger()
        q = _historical_quality()
        first = build_adjudication_dossiers(
            col03b_ledger=b,
            col03c_ledger=c,
            historical_quality=q,
            predecessor_sha=PREDECESSOR_SHA,
        )
        b2, c2, q2 = deepcopy(b), deepcopy(c), deepcopy(q)
        b2["occurrences"].reverse()
        c2["occurrences"].reverse()
        q2["csv_evidence"].reverse()
        q2["blocking_findings"].reverse()
        q2["csv_evidence"][-1]["records"].reverse()
        second = build_adjudication_dossiers(
            col03b_ledger=b2,
            col03c_ledger=c2,
            historical_quality=q2,
            predecessor_sha=PREDECESSOR_SHA,
        )
        self.assertEqual(first, second)

    def test_review_readiness_precedence_is_fail_closed(self):
        self.assertIsNotNone(classify_review_readiness, "COL-03E readiness classifier missing")
        self.assertEqual(
            classify_review_readiness(
                conflict_state="CONTRADICTED",
                candidate_count=2,
                match_state="AMBIGUOUS",
                provenance_complete=True,
                historical_semantic_blocked=True,
            ),
            "CONTRADICTED",
        )
        self.assertEqual(
            classify_review_readiness(
                conflict_state="NONE",
                candidate_count=2,
                match_state="AMBIGUOUS",
                provenance_complete=True,
                historical_semantic_blocked=True,
            ),
            "AMBIGUOUS",
        )
        self.assertEqual(
            classify_review_readiness(
                conflict_state="NONE",
                candidate_count=1,
                match_state="SINGLE_CANDIDATE",
                provenance_complete=True,
                historical_semantic_blocked=True,
            ),
            "BLOCKED_BY_HISTORICAL_SEMANTICS",
        )
        self.assertEqual(
            classify_review_readiness(
                conflict_state="NONE",
                candidate_count=1,
                match_state="SINGLE_CANDIDATE",
                provenance_complete=False,
                historical_semantic_blocked=False,
            ),
            "INSUFFICIENT_EVIDENCE",
        )
        self.assertEqual(
            classify_review_readiness(
                conflict_state="NONE",
                candidate_count=1,
                match_state="SINGLE_CANDIDATE",
                provenance_complete=True,
                historical_semantic_blocked=False,
            ),
            "READY_FOR_HUMAN_REVIEW",
        )


if __name__ == "__main__":
    unittest.main()
