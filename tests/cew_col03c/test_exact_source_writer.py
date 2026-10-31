from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

try:
    from experiments.cew_col03c.exact_source import _build_payloads, write_col03c_artifacts
except (ImportError, ModuleNotFoundError):
    _build_payloads = None
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

    def _build_fixture(self):
        occurrences = [
            {
                "occurrence_id": f"COL-OCC-{index:04d}",
                "hypotheses": [],
                "exact_source_reconstructible": True,
                "lineage_complete": True,
            }
            for index in range(1, 23)
        ]
        tav07 = {
            "catalogue_id": "TAV-07A",
            "archive_commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
            "source_path": "archive/documentazione_originaria/tavola7.pdf",
            "sha256": "38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b",
            "materialization_state": "MATERIALIZED_VERIFIED",
            "authority": "PRIMARY_DOCUMENTARY_SOURCE",
            "identity_promotion_authorized": False,
        }
        observations = [
            {
                "observation_id": "TAV07-OBS-B",
                "normalized_text": "30",
                "binding_state": "UNBOUND",
                "identity_promotion_authorized": False,
                "page_index": 0,
                "bbox": {"x": 0.2, "y": 0.2, "width": 0.02, "height": 0.02},
            },
            {
                "observation_id": "TAV07-OBS-A",
                "normalized_text": "4",
                "binding_state": "UNBOUND",
                "identity_promotion_authorized": False,
                "page_index": 0,
                "bbox": {"x": 0.1, "y": 0.1, "width": 0.02, "height": 0.02},
            },
        ]
        observation_inventory = {
            "observation_state": "MACHINE_OBSERVATIONS_PRESENT",
            "observation_count": 2,
            "extraction_method": "TESSERACT_PSM11_300DPI",
            "extraction_version": "tesseract 5.3.4",
            "observations": observations,
            "observation_digest": "a" * 64,
            "identity_promotion_authorized": False,
        }
        historical = [
            {
                "artifact_name": "MATRICE_PILASTRI_27x5_v22.csv",
                "materialization_state": "KNOWN_INVENTORY_NOT_MATERIALIZED",
                "bytes_available": False,
                "row_level_evidence_usable": False,
                "authority": "REFERENCE_ONLY",
                "inventory_source_ref": "commit:643dc893:archive/ARTEFATTI_STORICI.md",
            },
            {
                "artifact_name": "TAV7_PILASTRI.dxf",
                "materialization_state": "KNOWN_INVENTORY_NOT_MATERIALIZED",
                "bytes_available": False,
                "row_level_evidence_usable": False,
                "authority": "REFERENCE_ONLY",
                "inventory_source_ref": "commit:643dc893:archive/ARTEFATTI_STORICI.md",
            },
        ]
        quality = {
            "schema": "CEW_COL03C_DERIVED_REFERENCE_QUALITY_v1",
            "topology_reference": {
                "identity_use_state": "DATA_QUALITY_BLOCKED",
                "identity_evidence_usable": False,
                "unresolved_endpoint_ids": ["N059", "N058"],
                "authority": "REFERENCE_ONLY",
            },
            "candidate_matrix_reference": {
                "reference_role": "CANDIDATE_HYPOTHESES_ONLY",
                "historical_27x5_matrix": False,
                "identity_evidence_usable": False,
                "authority": "REFERENCE_ONLY",
            },
        }
        descriptors = [
            {"path": "data/canonical/z.csv", "sha256": "2" * 64},
            {"path": "data/canonical/a.csv", "sha256": "1" * 64},
        ]
        historical_manifest = {
            "registration_commit": "643dc8934ec0c8ac37613ec2880cf9e02f5a9df2",
            "inventory_path": "archive/ARTEFATTI_STORICI.md",
        }
        return occurrences, tav07, observation_inventory, historical, historical_manifest, quality, descriptors

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

    def test_build_payloads_is_set_order_invariant(self):
        self.assertIsNotNone(_build_payloads, "COL-03C payload builder missing")
        occurrences, tav07, inventory, historical, manifest, quality, descriptors = self._build_fixture()
        first = _build_payloads(
            predecessor_occurrences=occurrences,
            tav07_metadata=tav07,
            observation_inventory=inventory,
            historical_artifacts=historical,
            historical_manifest=manifest,
            quality=quality,
            derived_descriptors=descriptors,
        )
        reversed_inventory = deepcopy(inventory)
        reversed_inventory["observations"] = list(reversed(reversed_inventory["observations"]))
        second = _build_payloads(
            predecessor_occurrences=list(reversed(deepcopy(occurrences))),
            tav07_metadata=deepcopy(tav07),
            observation_inventory=reversed_inventory,
            historical_artifacts=list(reversed(deepcopy(historical))),
            historical_manifest=deepcopy(manifest),
            quality=deepcopy(quality),
            derived_descriptors=list(reversed(deepcopy(descriptors))),
        )
        self.assertEqual(first, second)

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
