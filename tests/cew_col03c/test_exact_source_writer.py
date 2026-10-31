from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

try:
    from experiments.cew_col03c.exact_source import write_col03c_artifacts
except (ImportError, ModuleNotFoundError):
    write_col03c_artifacts = None


class ExactSourceWriterTests(unittest.TestCase):
    def _payloads(self):
        return {
            "source_manifest": {"schema": "SOURCE", "primary_sources": [{"catalogue_id": "TAV-07A"}]},
            "quality": {"schema": "QUALITY", "topology_reference": {"identity_use_state": "DATA_QUALITY_BLOCKED"}},
            "ledger": {"schema": "LEDGER", "occurrence_count": 22, "occurrences": []},
            "reconciliation": {"schema": "RECONCILIATION", "occurrence_count": 22},
            "closure": {
                "schema": "CLOSURE",
                "qualified_col03b_sha": "cfd9382b703d0a974daf63c23dc2b6d3d81eadad",
                "available_cross_document_evidence_evaluated": True,
                "historical_derived_artifact_recovery_complete": False,
                "all_occurrences_cross_document_resolved": False,
            },
        }

    def test_writer_emits_exactly_five_named_artifacts(self):
        self.assertIsNotNone(write_col03c_artifacts, "COL-03C exact-source writer missing")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "evidence" / "cew-col03c"
            digests = write_col03c_artifacts(output, **self._payloads())
            self.assertEqual(
                sorted(path.name for path in output.iterdir()),
                [
                    "cross-document-evidence-closure.json",
                    "cross-document-evidence-ledger.json",
                    "cross-document-reconciliation.json",
                    "derived-reference-quality.json",
                    "source-materialization-manifest.json",
                ],
            )
            self.assertEqual(set(digests), {path.name for path in output.iterdir()})
            self.assertTrue(all(len(value) == 64 for value in digests.values()))

    def test_writer_is_byte_deterministic(self):
        self.assertIsNotNone(write_col03c_artifacts, "COL-03C exact-source writer missing")
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            digests_a = write_col03c_artifacts(first, **self._payloads())
            payloads = self._payloads()
            payloads["source_manifest"] = {"primary_sources": [{"catalogue_id": "TAV-07A"}], "schema": "SOURCE"}
            digests_b = write_col03c_artifacts(second, **payloads)
            self.assertEqual(digests_a, digests_b)
            for name in digests_a:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_writer_does_not_create_predecessor_namespaces(self):
        self.assertIsNotNone(write_col03c_artifacts, "COL-03C exact-source writer missing")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "evidence"
            output = root / "cew-col03c"
            write_col03c_artifacts(output, **self._payloads())
            self.assertFalse((root / "cew-col03a").exists())
            self.assertFalse((root / "cew-col03b").exists())
            self.assertFalse((root / "cew-col02").exists())

    def test_artifacts_preserve_identity_unresolved_and_no_recovery_fabrication(self):
        self.assertIsNotNone(write_col03c_artifacts, "COL-03C exact-source writer missing")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_col03c_artifacts(output, **self._payloads())
            closure = json.loads((output / "cross-document-evidence-closure.json").read_text(encoding="utf-8"))
            self.assertTrue(closure["available_cross_document_evidence_evaluated"])
            self.assertFalse(closure["historical_derived_artifact_recovery_complete"])
            self.assertFalse(closure["all_occurrences_cross_document_resolved"])


if __name__ == "__main__":
    unittest.main()
