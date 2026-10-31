from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from experiments.cew_col03b.exact_source import (
    build_documentary_closure,
    build_documentary_reconciliation,
    finalize_evidence_bundle,
    write_col03b_artifacts,
)


QUALIFIED_SHA = "0d4a43cf02eadd2ab6f4b2641888395586c08a98"
CHANNELS = (
    "internal_text_evidence",
    "intersecting_text_evidence",
    "nearby_text_evidence",
    "high_resolution_read_evidence",
    "callout_evidence",
    "local_topology_evidence",
    "cross_document_evidence",
)


def _bundle(index: int) -> dict:
    row = {
        "occurrence_id": f"COL-OCC-{index:04d}",
        "col03a_ledger_digest": "ledger-digest",
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "source_path": "archive/documentazione_originaria/tavola 5.pdf",
        "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "page_index": 0,
        "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
        "primary_graphical_representation": {"kind": "FROZEN_PROPOSAL", "bbox": {"x": 0.1, "y": 0.1, "width": 0.01, "height": 0.01}},
        "hypotheses": [],
        "documentary_evidence_state": "NOT_EVALUATED",
        "documentary_identity_resolution_state": "UNRESOLVED",
        "conflict_state": "NONE",
        "missing_channels": list(CHANNELS),
        "exact_source_reconstructible": True,
        "lineage_complete": True,
        "support_identity_authorized": False,
        "text_identity_binding_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
        "notes": [],
    }
    for channel in CHANNELS:
        row[channel] = [{"evidence_id": f"NONE-{index}-{channel}", "evidence_class": "NO_EVIDENCE", "status": "NO_EVIDENCE"}]
    return row


def _predecessor_closure() -> dict:
    return {"occurrence_ledger_complete": True}


class DocumentaryClosureTests(unittest.TestCase):
    def test_finalize_marks_all_explicit_channels_complete_while_identity_unresolved(self) -> None:
        bundle = finalize_evidence_bundle(_bundle(1))
        self.assertEqual(bundle["missing_channels"], [])
        self.assertEqual(bundle["documentary_evidence_state"], "COMPLETE")
        self.assertEqual(bundle["documentary_identity_resolution_state"], "UNRESOLVED")

    def test_finalize_rejects_omitted_channel(self) -> None:
        bundle = _bundle(1)
        bundle["nearby_text_evidence"] = []
        finalized = finalize_evidence_bundle(bundle)
        self.assertEqual(finalized["documentary_evidence_state"], "PARTIAL")
        self.assertIn("nearby_text_evidence", finalized["missing_channels"])

    def test_closure_allows_unresolved_identity_but_requires_complete_collection(self) -> None:
        bundles = [finalize_evidence_bundle(_bundle(index)) for index in range(1, 23)]
        reconciliation = build_documentary_reconciliation(
            bundles,
            historical_manifest={"artifacts": [{"artifact_id": "TAV7", "path": "archive/TAV7_PILASTRI.dxf", "version": "v25", "sha256": "a" * 64}]},
        )
        closure = build_documentary_closure(
            bundles=bundles,
            reconciliation=reconciliation,
            predecessor_closure=_predecessor_closure(),
            qualified_base_sha=QUALIFIED_SHA,
        )
        self.assertTrue(closure["documentary_identity_evidence_collection_complete"])
        self.assertFalse(closure["all_occurrences_identity_resolved"])
        self.assertEqual(closure["blocking_reasons"], [])

    def test_authority_promotion_blocks_closure(self) -> None:
        bundles = [finalize_evidence_bundle(_bundle(index)) for index in range(1, 23)]
        bundles[0]["support_identity_authorized"] = True
        reconciliation = build_documentary_reconciliation(bundles, historical_manifest={"artifacts": []})
        closure = build_documentary_closure(
            bundles=bundles,
            reconciliation=reconciliation,
            predecessor_closure=_predecessor_closure(),
            qualified_base_sha=QUALIFIED_SHA,
        )
        self.assertFalse(closure["documentary_identity_evidence_collection_complete"])
        self.assertIn("AUTHORITY_DRIFT", closure["blocking_reasons"])

    def test_source_reconstruction_failure_blocks_closure(self) -> None:
        bundles = [finalize_evidence_bundle(_bundle(index)) for index in range(1, 23)]
        bundles[3]["exact_source_reconstructible"] = False
        reconciliation = build_documentary_reconciliation(bundles, historical_manifest={"artifacts": []})
        closure = build_documentary_closure(
            bundles=bundles,
            reconciliation=reconciliation,
            predecessor_closure=_predecessor_closure(),
            qualified_base_sha=QUALIFIED_SHA,
        )
        self.assertFalse(closure["documentary_identity_evidence_collection_complete"])
        self.assertIn("SOURCE_RECONSTRUCTION_FAILED", closure["blocking_reasons"])

    def test_writer_is_deterministic_for_shuffled_bundle_order(self) -> None:
        bundles = [finalize_evidence_bundle(_bundle(index)) for index in range(1, 23)]
        historical = {"artifacts": [{"artifact_id": "TAV7", "path": "archive/TAV7_PILASTRI.dxf", "version": "v25", "sha256": "a" * 64}]}
        reconciliation = build_documentary_reconciliation(bundles, historical_manifest=historical)
        closure = build_documentary_closure(
            bundles=bundles,
            reconciliation=reconciliation,
            predecessor_closure=_predecessor_closure(),
            qualified_base_sha=QUALIFIED_SHA,
        )
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = write_col03b_artifacts(Path(first_dir), bundles=bundles, reconciliation=reconciliation, closure=closure)
            second = write_col03b_artifacts(Path(second_dir), bundles=list(reversed(bundles)), reconciliation=reconciliation, closure=closure)
            self.assertEqual(first, second)
            for filename in (
                "documentary-identity-evidence-ledger.json",
                "documentary-identity-hypotheses.json",
                "documentary-identity-reconciliation.json",
                "documentary-identity-evidence-closure.json",
            ):
                self.assertEqual((Path(first_dir) / filename).read_bytes(), (Path(second_dir) / filename).read_bytes())
                json.loads((Path(first_dir) / filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
