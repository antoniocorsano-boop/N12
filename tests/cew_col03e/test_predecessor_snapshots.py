from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

try:
    from experiments.cew_col03e.predecessor import load_qualified_predecessor_evidence
except (ImportError, ModuleNotFoundError):
    load_qualified_predecessor_evidence = None


COL03B_SHA = "cfd9382b703d0a974daf63c23dc2b6d3d81eadad"
AUTHORITY_KEYS = (
    "support_identity_authorized",
    "text_identity_binding_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
    "fixed_line_assignment_authorized",
    "structural_identity_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "g2c_promotion_authorized",
    "g3_authorized",
    "merge_authorized",
)
COL03C_AUTHORITY_KEYS = AUTHORITY_KEYS + ("vertical_chain_assignment_authorized", "canonical_node_assignment_authorized")


def _closed(keys=AUTHORITY_KEYS):
    return {key: False for key in keys}


def _valid_col03b_ledger():
    occurrences = []
    for index in range(1, 23):
        hypotheses = []
        if index == 1:
            hypotheses = [{"candidate_value": "4", "promotion_authorized": False, "state": "SINGLE_CHANNEL"}]
        elif index == 15:
            hypotheses = [{"candidate_value": "30", "promotion_authorized": False, "state": "SINGLE_CHANNEL"}]
        occurrences.append({
            "occurrence_id": f"COL-OCC-{index:04d}",
            "hypotheses": hypotheses,
            **_closed(),
        })
    return {"occurrence_count": 22, "occurrences": occurrences}


def _valid_col03b_closure():
    return {
        "occurrence_count": 22,
        "documentary_identity_evidence_collection_complete": True,
        "all_occurrences_identity_resolved": False,
        "blocking_reasons": [],
        "authority": _closed(),
    }


def _valid_col03c_ledger():
    return {
        "schema": "CEW_COL03C_CROSS_DOCUMENT_EVIDENCE_LEDGER_v1",
        "occurrence_count": 22,
        "occurrences": [
            {
                "occurrence_id": f"COL-OCC-{index:04d}",
                "tav07_match_state": "EVALUATED_NO_MATCH",
                "hypotheses": [],
                "cross_document_identity_resolved": False,
                **_closed(COL03C_AUTHORITY_KEYS),
            }
            for index in range(1, 23)
        ],
    }


def _valid_col03c_closure():
    return {
        "schema": "CEW_COL03C_CROSS_DOCUMENT_EVIDENCE_CLOSURE_v1",
        "qualified_col03b_sha": COL03B_SHA,
        "occurrence_count": 22,
        "available_cross_document_evidence_evaluated": True,
        "all_occurrences_cross_document_resolved": False,
        "blocking_reasons": [],
        "authority": _closed(COL03C_AUTHORITY_KEYS),
    }


def _valid_col03c_source():
    return {
        "schema": "CEW_COL03C_SOURCE_MATERIALIZATION_MANIFEST_v1",
        "qualified_col03b_sha": COL03B_SHA,
    }


def _write_json(root: Path, name: str, value: dict) -> None:
    (root / name).write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _fixture_roots(tmp: str) -> tuple[Path, Path]:
    root = Path(tmp)
    b = root / "cew-col03b"
    c = root / "cew-col03c"
    b.mkdir()
    c.mkdir()
    _write_json(b, "documentary-identity-evidence-ledger.json", _valid_col03b_ledger())
    _write_json(b, "documentary-identity-evidence-closure.json", _valid_col03b_closure())
    _write_json(c, "cross-document-evidence-ledger.json", _valid_col03c_ledger())
    _write_json(c, "cross-document-evidence-closure.json", _valid_col03c_closure())
    _write_json(c, "source-materialization-manifest.json", _valid_col03c_source())
    return b, c


class QualifiedPredecessorReplayTests(unittest.TestCase):
    def test_replayed_predecessors_preserve_exact_occurrence_and_candidate_contract(self):
        self.assertIsNotNone(load_qualified_predecessor_evidence, "COL-03E predecessor validator missing")
        with tempfile.TemporaryDirectory() as tmp:
            b, c = _fixture_roots(tmp)
            result = load_qualified_predecessor_evidence(b, c)
        self.assertEqual(result["occurrence_ids"], [f"COL-OCC-{i:04d}" for i in range(1, 23)])
        self.assertEqual(result["documentary_candidates"], {"COL-OCC-0001": ["4"], "COL-OCC-0015": ["30"]})
        self.assertEqual(result["cross_document_candidate_count"], 0)
        self.assertTrue(result["predecessor_evidence_validated"])

    def test_occurrence_set_drift_fails_closed(self):
        self.assertIsNotNone(load_qualified_predecessor_evidence)
        with tempfile.TemporaryDirectory() as tmp:
            b, c = _fixture_roots(tmp)
            ledger = json.loads((c / "cross-document-evidence-ledger.json").read_text(encoding="utf-8"))
            ledger["occurrences"].pop()
            ledger["occurrence_count"] = 21
            _write_json(c, "cross-document-evidence-ledger.json", ledger)
            with self.assertRaisesRegex(ValueError, "COL03E_OCCURRENCE_SET_DRIFT"):
                load_qualified_predecessor_evidence(b, c)

    def test_cross_document_resolution_or_candidate_drift_fails_closed(self):
        self.assertIsNotNone(load_qualified_predecessor_evidence)
        with tempfile.TemporaryDirectory() as tmp:
            b, c = _fixture_roots(tmp)
            ledger = json.loads((c / "cross-document-evidence-ledger.json").read_text(encoding="utf-8"))
            ledger["occurrences"][0]["cross_document_identity_resolved"] = True
            ledger["occurrences"][0]["hypotheses"] = [{"candidate_value": "4", "promotion_authorized": False}]
            _write_json(c, "cross-document-evidence-ledger.json", ledger)
            with self.assertRaisesRegex(ValueError, "COL03E_PREDECESSOR_STATE_DRIFT"):
                load_qualified_predecessor_evidence(b, c)

    def test_authority_drift_fails_closed(self):
        self.assertIsNotNone(load_qualified_predecessor_evidence)
        with tempfile.TemporaryDirectory() as tmp:
            b, c = _fixture_roots(tmp)
            ledger = json.loads((b / "documentary-identity-evidence-ledger.json").read_text(encoding="utf-8"))
            ledger["occurrences"][0]["structural_identity_authorized"] = True
            _write_json(b, "documentary-identity-evidence-ledger.json", ledger)
            with self.assertRaisesRegex(ValueError, "COL03E_AUTHORITY_DRIFT"):
                load_qualified_predecessor_evidence(b, c)

    def test_wrong_col03b_lineage_fails_closed(self):
        self.assertIsNotNone(load_qualified_predecessor_evidence)
        with tempfile.TemporaryDirectory() as tmp:
            b, c = _fixture_roots(tmp)
            source = deepcopy(_valid_col03c_source())
            source["qualified_col03b_sha"] = "wrong"
            _write_json(c, "source-materialization-manifest.json", source)
            with self.assertRaisesRegex(ValueError, "COL03E_COL03B_LINEAGE_DRIFT"):
                load_qualified_predecessor_evidence(b, c)


if __name__ == "__main__":
    unittest.main()
