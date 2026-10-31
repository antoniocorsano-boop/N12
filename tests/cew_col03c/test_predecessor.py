from __future__ import annotations

import unittest

try:
    from experiments.cew_col03c.predecessor import (
        QUALIFIED_COL03B_SHA,
        validate_col03b_predecessor,
    )
except (ImportError, ModuleNotFoundError):
    QUALIFIED_COL03B_SHA = None
    validate_col03b_predecessor = None


CLOSED_AUTHORITY_KEYS = (
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


def _fixture():
    occurrences = []
    for index in range(1, 23):
        row = {
            "occurrence_id": f"COL-OCC-{index:04d}",
            "documentary_evidence_state": "COMPLETE",
            "exact_source_reconstructible": True,
            "lineage_complete": True,
        }
        row.update({key: False for key in CLOSED_AUTHORITY_KEYS})
        occurrences.append(row)
    ledger = {"occurrence_count": 22, "occurrences": occurrences}
    reconciliation = {
        "occurrence_count": 22,
        "historical_artifacts_materialized": False,
        "historical_inventory_ref": "archive/ARTEFATTI_STORICI.md",
        "historical_gap_reason": "INVENTORY_PRESENT_HISTORICAL_DXF_CSV_NOT_MATERIALIZED_ON_QUALIFIED_BRANCH",
    }
    closure = {
        "documentary_identity_evidence_collection_complete": True,
        "all_occurrences_identity_resolved": False,
        "blocking_reasons": [],
        "authority": {key: False for key in CLOSED_AUTHORITY_KEYS},
    }
    return ledger, reconciliation, closure


class Col03CPredecessorTests(unittest.TestCase):
    def test_exact_predecessor_sha_is_frozen(self):
        self.assertIsNotNone(validate_col03b_predecessor, "COL-03C predecessor implementation missing")
        self.assertEqual(
            QUALIFIED_COL03B_SHA,
            "cfd9382b703d0a974daf63c23dc2b6d3d81eadad",
        )

    def test_valid_predecessor_returns_exact_22_occurrences(self):
        self.assertIsNotNone(validate_col03b_predecessor, "COL-03C predecessor implementation missing")
        ledger, reconciliation, closure = _fixture()
        rows = validate_col03b_predecessor(
            ledger=ledger,
            reconciliation=reconciliation,
            closure=closure,
            expected_sha=QUALIFIED_COL03B_SHA,
        )
        self.assertEqual([row["occurrence_id"] for row in rows], [f"COL-OCC-{i:04d}" for i in range(1, 23)])

    def test_sha_drift_fails_closed(self):
        self.assertIsNotNone(validate_col03b_predecessor, "COL-03C predecessor implementation missing")
        ledger, reconciliation, closure = _fixture()
        with self.assertRaisesRegex(ValueError, "COL-03B.*SHA"):
            validate_col03b_predecessor(
                ledger=ledger,
                reconciliation=reconciliation,
                closure=closure,
                expected_sha="0" * 40,
            )

    def test_occurrence_set_drift_fails_closed(self):
        self.assertIsNotNone(validate_col03b_predecessor, "COL-03C predecessor implementation missing")
        ledger, reconciliation, closure = _fixture()
        ledger["occurrences"] = ledger["occurrences"][:-1]
        ledger["occurrence_count"] = 21
        with self.assertRaisesRegex(ValueError, "occurrence"):
            validate_col03b_predecessor(
                ledger=ledger,
                reconciliation=reconciliation,
                closure=closure,
                expected_sha=QUALIFIED_COL03B_SHA,
            )

    def test_identity_or_authority_promotion_fails_closed(self):
        self.assertIsNotNone(validate_col03b_predecessor, "COL-03C predecessor implementation missing")
        ledger, reconciliation, closure = _fixture()
        closure["all_occurrences_identity_resolved"] = True
        with self.assertRaisesRegex(ValueError, "identity"):
            validate_col03b_predecessor(
                ledger=ledger,
                reconciliation=reconciliation,
                closure=closure,
                expected_sha=QUALIFIED_COL03B_SHA,
            )

    def test_historical_gap_semantics_are_required(self):
        self.assertIsNotNone(validate_col03b_predecessor, "COL-03C predecessor implementation missing")
        ledger, reconciliation, closure = _fixture()
        reconciliation["historical_artifacts_materialized"] = True
        with self.assertRaisesRegex(ValueError, "historical"):
            validate_col03b_predecessor(
                ledger=ledger,
                reconciliation=reconciliation,
                closure=closure,
                expected_sha=QUALIFIED_COL03B_SHA,
            )


if __name__ == "__main__":
    unittest.main()
