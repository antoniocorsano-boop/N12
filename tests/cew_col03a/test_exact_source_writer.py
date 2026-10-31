from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest


SOURCE = {
    "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
    "source_path": "archive/documentazione_originaria/tavola 5.pdf",
    "sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
    "page_id": "CEW-N12-PAGE-TAV05S-P001",
    "page_index": 0,
    "page_transform_id": "CEW-N12-XFORM-TAV05S-P001",
}

CLOSED_AUTHORITY = {
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
}


def _proposal_payload(*, overlap: bool = False) -> dict:
    candidates = []
    for index in range(1, 612):
        candidates.append(
            {
                "candidate_id": f"COL02-FP-{index:04d}",
                "bbox": {
                    "x": ((index - 1) % 50) * 0.015,
                    "y": ((index - 1) // 50) * 0.02,
                    "width": 0.01,
                    "height": 0.012,
                },
                "detector": "TEST",
            }
        )
    candidates[0]["bbox"] = {"x": 0.10, "y": 0.10, "width": 0.10, "height": 0.10}
    candidates[1]["bbox"] = (
        {"x": 0.105, "y": 0.105, "width": 0.095, "height": 0.095}
        if overlap
        else {"x": 0.30, "y": 0.10, "width": 0.04, "height": 0.05}
    )
    return {"candidate_count": 611, "candidates": candidates}


def _evidence(candidate_id: str, evidence_id: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "candidate_id": candidate_id,
        "evidence_class": "PROTOTYPE_CONFIRMED",
        "graphical_decision": "COLUMN_FOOTPRINT_CONFIRMED",
        "discovery_path": "HUMAN_PROTOTYPE_REVIEW",
        "human_review_receipt": "fixture.json",
        "repair_id": None,
        "human_added_point_event_ids": [],
        "lineage": {"fixture": evidence_id},
    }


def _closure() -> dict:
    return {
        "schema_id": "CEW_COL02_OCCURRENCE_COVERAGE_CLOSURE",
        "schema_version": 1,
        "occurrence_coverage_complete": True,
        "proposal_count": 611,
        "original_proposal_id_space_immutable": True,
        "authority": dict(CLOSED_AUTHORITY),
    }


def _write(path: Path, payload) -> bytes:
    raw = (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path.write_bytes(raw)
    return raw


class ExactSourceWriterTests(unittest.TestCase):
    @staticmethod
    def _module():
        from experiments.cew_col03a import exact_source

        return exact_source

    def _paths(self, root: Path, *, reverse: bool = False, overlap: bool = False):
        evidence = [_evidence("COL02-FP-0001", "E1"), _evidence("COL02-FP-0002", "E2")]
        if reverse:
            evidence.reverse()
        payloads = {
            "evidence": evidence,
            "proposals": _proposal_payload(overlap=overlap),
            "repair": {"schema": "CEW_COL02_AXIS_AWARE_WHOLE_SYMBOL_REPAIR_MANIFEST_v1", "repairs": []},
            "closure": _closure(),
            "source": SOURCE,
        }
        paths = {}
        originals = {}
        for name, payload in payloads.items():
            path = root / f"{name}.json"
            originals[name] = _write(path, payload)
            paths[name] = path
        return paths, originals

    def test_writer_emits_three_canonical_json_files_without_mutating_inputs(self):
        module = self._module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, originals = self._paths(root)
            output = root / "out"
            summary = module.write_col03a_artifacts(
                evidence_items_path=paths["evidence"],
                proposals_path=paths["proposals"],
                repair_manifest_path=paths["repair"],
                col02_closure_path=paths["closure"],
                source_path=paths["source"],
                output_root=output,
            )

            expected = {
                "column-occurrence-ledger.json",
                "column-occurrence-reconciliation.json",
                "column-occurrence-ledger-closure.json",
            }
            self.assertEqual({path.name for path in output.iterdir()}, expected)
            for path in output.iterdir():
                raw = path.read_bytes()
                self.assertTrue(raw.endswith(b"\n"))
                payload = json.loads(raw.decode("utf-8"))
                self.assertEqual(raw, (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8"))
            for name, path in paths.items():
                self.assertEqual(path.read_bytes(), originals[name])

            closure = json.loads((output / "column-occurrence-ledger-closure.json").read_text(encoding="utf-8"))
            self.assertTrue(closure["occurrence_ledger_complete"])
            self.assertEqual(closure["authority"], CLOSED_AUTHORITY)
            self.assertEqual(summary["occurrence_count"], 2)

    def test_summary_digests_match_emitted_ledger_reconciliation_and_closure(self):
        module = self._module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, _ = self._paths(root)
            output = root / "out"
            summary = module.write_col03a_artifacts(
                evidence_items_path=paths["evidence"],
                proposals_path=paths["proposals"],
                repair_manifest_path=paths["repair"],
                col02_closure_path=paths["closure"],
                source_path=paths["source"],
                output_root=output,
            )
            for key, filename in [
                ("ledger_sha256", "column-occurrence-ledger.json"),
                ("reconciliation_sha256", "column-occurrence-reconciliation.json"),
                ("closure_sha256", "column-occurrence-ledger-closure.json"),
            ]:
                self.assertEqual(summary[key], hashlib.sha256((output / filename).read_bytes()).hexdigest())

            closure = json.loads((output / "column-occurrence-ledger-closure.json").read_text(encoding="utf-8"))
            ledger = json.loads((output / "column-occurrence-ledger.json").read_text(encoding="utf-8"))
            reconciliation = json.loads((output / "column-occurrence-reconciliation.json").read_text(encoding="utf-8"))
            canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            self.assertEqual(closure["ledger_sha256"], hashlib.sha256(canonical(ledger)).hexdigest())
            self.assertEqual(closure["reconciliation_sha256"], hashlib.sha256(canonical(reconciliation)).hexdigest())

    def test_ambiguity_is_emitted_fail_closed_not_silently_merged(self):
        module = self._module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths, _ = self._paths(root, overlap=True)
            output = root / "out"
            module.write_col03a_artifacts(
                evidence_items_path=paths["evidence"],
                proposals_path=paths["proposals"],
                repair_manifest_path=paths["repair"],
                col02_closure_path=paths["closure"],
                source_path=paths["source"],
                output_root=output,
            )
            ledger = json.loads((output / "column-occurrence-ledger.json").read_text(encoding="utf-8"))
            closure = json.loads((output / "column-occurrence-ledger-closure.json").read_text(encoding="utf-8"))
            self.assertEqual(ledger["occurrence_count"], 2)
            self.assertEqual(ledger["conflict_count"], 1)
            self.assertEqual(ledger["conflicts"][0]["conflict_state"], "AMBIGUOUS_DUPLICATE")
            self.assertFalse(closure["occurrence_ledger_complete"])
            self.assertIn("UNRESOLVED_CONFLICTS", closure["blocking_reasons"])

    def test_reversing_normalized_evidence_order_produces_byte_identical_outputs(self):
        module = self._module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_root = root / "first"
            second_root = root / "second"
            first_root.mkdir()
            second_root.mkdir()
            first_paths, _ = self._paths(first_root, reverse=False)
            second_paths, _ = self._paths(second_root, reverse=True)
            first_out = first_root / "out"
            second_out = second_root / "out"
            module.write_col03a_artifacts(
                evidence_items_path=first_paths["evidence"],
                proposals_path=first_paths["proposals"],
                repair_manifest_path=first_paths["repair"],
                col02_closure_path=first_paths["closure"],
                source_path=first_paths["source"],
                output_root=first_out,
            )
            module.write_col03a_artifacts(
                evidence_items_path=second_paths["evidence"],
                proposals_path=second_paths["proposals"],
                repair_manifest_path=second_paths["repair"],
                col02_closure_path=second_paths["closure"],
                source_path=second_paths["source"],
                output_root=second_out,
            )
            for filename in [
                "column-occurrence-ledger.json",
                "column-occurrence-reconciliation.json",
                "column-occurrence-ledger-closure.json",
            ]:
                self.assertEqual((first_out / filename).read_bytes(), (second_out / filename).read_bytes())


if __name__ == "__main__":
    unittest.main()
