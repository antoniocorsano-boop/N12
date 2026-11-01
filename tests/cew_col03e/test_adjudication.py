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
        occurrence_id = f"COL-OCC-{index:04d}"
        hypotheses = []
        internal_text_evidence = []
        if index == 1:
            evidence_id = "COL-OCC-0001-TXT-001"
            hypotheses = [{
                "candidate_value": "4",
                "hypothesis_id": "HYP-COL-OCC-0001-DOCUMENTARY_LABEL_CANDIDATE-4",
                "state": "SINGLE_CHANNEL",
                "promotion_authorized": False,
                "supporting_evidence_ids": [evidence_id],
            }]
            internal_text_evidence = [{
                "evidence_id": evidence_id,
                "provenance_ref": "CEW-N12-XFORM-TAV05S-P001:TXT-001",
                "exact_source_reconstructible": True,
            }]
        elif index == 15:
            evidence_id = "COL-OCC-0015-TXT-006"
            hypotheses = [{
                "candidate_value": "30",
                "hypothesis_id": "HYP-COL-OCC-0015-DOCUMENTARY_LABEL_CANDIDATE-30",
                "state": "SINGLE_CHANNEL",
                "promotion_authorized": False,
                "supporting_evidence_ids": [evidence_id],
            }]
            internal_text_evidence = [{
                "evidence_id": evidence_id,
                "provenance_ref": "CEW-N12-XFORM-TAV05S-P001:TXT-006",
                "exact_source_reconstructible": True,
            }]
        rows.append({
            "occurrence_id": occurrence_id,
            "hypotheses": hypotheses,
            "internal_text_evidence": internal_text_evidence,
            "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
            "page_id": "CEW-N12-PAGE-TAV05S-P001",
            "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
            "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
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
                "tav07_source_ref": {
                    "catalogue_id": "TAV-07A",
                    "archive_commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
                    "source_path": "archive/documentazione_originaria/tavola7.pdf",
                    "sha256": "38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b",
                },
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

    def test_candidate_dossier_exposes_replayable_documentary_and_primary_source_provenance(self):
        self.assertIsNotNone(build_adjudication_dossiers)
        first = build_adjudication_dossiers(
            col03b_ledger=_col03b_ledger(),
            col03c_ledger=_col03c_ledger(),
            historical_quality=_historical_quality(),
            predecessor_sha=PREDECESSOR_SHA,
        )[0]

        channels = first["evidence_channels"]
        documentary = channels["documentary"]
        self.assertEqual(len(documentary), 1)
        self.assertEqual(documentary[0]["candidate_value"], "4")
        self.assertEqual(documentary[0]["hypothesis_state"], "SINGLE_CHANNEL")
        self.assertEqual(documentary[0]["supporting_evidence_ids"], ["COL-OCC-0001-TXT-001"])
        self.assertEqual(
            documentary[0]["provenance"],
            [{
                "evidence_id": "COL-OCC-0001-TXT-001",
                "provenance_ref": "CEW-N12-XFORM-TAV05S-P001:TXT-001",
                "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
                "page_id": "CEW-N12-PAGE-TAV05S-P001",
                "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
                "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
                "exact_source_reconstructible": True,
            }],
        )
        cross_document = channels["cross_document"]
        self.assertEqual(cross_document["source_state"], "MATERIALIZED_VERIFIED")
        self.assertEqual(cross_document["match_state"], "EVALUATED_NO_MATCH")
        self.assertEqual(cross_document["source_ref"]["catalogue_id"], "TAV-07A")
        self.assertEqual(
            cross_document["source_ref"]["sha256"],
            "38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b",
        )
        self.assertEqual(channels["historical"]["bridge_state"], "UNBOUND")

    def test_candidate_without_replayable_supporting_provenance_fails_closed(self):
        self.assertIsNotNone(build_adjudication_dossiers)
        col03b = _col03b_ledger()
        col03b["occurrences"][0]["internal_text_evidence"] = []
        with self.assertRaisesRegex(ValueError, "COL03E_DOCUMENTARY_PROVENANCE_INCOMPLETE"):
            build_adjudication_dossiers(
                col03b_ledger=col03b,
                col03c_ledger=_col03c_ledger(),
                historical_quality=_historical_quality(),
                predecessor_sha=PREDECESSOR_SHA,
            )

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
