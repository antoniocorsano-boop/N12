from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

try:
    from experiments.cew_col03f.exact_source import (
        build_inspection_queue,
        build_primary_bridge_closure,
        write_col03f_json,
    )
except (ImportError, ModuleNotFoundError):
    build_inspection_queue = None
    build_primary_bridge_closure = None
    write_col03f_json = None


PREDECESSOR_SHA = "cbf57e9261228a7376df826baadc79abe2da254c"


def _row(index: int, *, state: str = "NO_DIRECT_LABEL_OBSERVED", candidate_values: list[str] | None = None) -> dict:
    occurrence_id = f"COL-OCC-{index:04d}"
    return {
        "queue_index": index,
        "occurrence_id": occurrence_id,
        "acquisition_state": state,
        "candidate_values": list(candidate_values or []),
        "identity_promoted": False,
        "historical_identity_positive_evidence_used": False,
        "support_identity_authorized": False,
        "text_identity_binding_authorized": False,
        "family_assignment_authorized": False,
        "section_assignment_authorized": False,
        "fixed_line_assignment_authorized": False,
        "vertical_chain_assignment_authorized": False,
        "structural_identity_authorized": False,
        "canonical_node_assignment_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
        "g2c_promotion_authorized": False,
        "g3_authorized": False,
        "merge_authorized": False,
        "crop_manifest": {
            "source_only_path": f"review/{occurrence_id}-source-only.png",
            "source_only_sha256": "a" * 64,
            "target_overlay_path": f"review/{occurrence_id}-target-overlay.png",
            "target_overlay_sha256": "b" * 64,
        },
    }


def _ledger(*, with_candidate: bool = True) -> dict:
    order = ["COL-OCC-0001", "COL-OCC-0015"] + [
        f"COL-OCC-{index:04d}" for index in range(1, 23) if index not in {1, 15}
    ]
    rows_by_id = {f"COL-OCC-{index:04d}": _row(index) for index in range(1, 23)}
    if with_candidate:
        rows_by_id["COL-OCC-0001"] = _row(
            1,
            state="CORROBORATED_EXISTING_LABEL_CANDIDATE",
            candidate_values=["4"],
        )
    rows = []
    for queue_index, occurrence_id in enumerate(order, start=1):
        row = dict(rows_by_id[occurrence_id])
        row["queue_index"] = queue_index
        rows.append(row)
    return {
        "schema": "CEW_COL03F_PRIMARY_BRIDGE_EVIDENCE_LEDGER_v1",
        "occurrence_count": 22,
        "inspection_order": order,
        "occurrences": rows,
        "candidate_occurrence_ids": ["COL-OCC-0001"] if with_candidate else [],
        "identity_promotion_authorized": False,
        "source_ref": {
            "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
            "source_sha256": "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580",
            "raster_sha256": "c" * 64,
        },
    }


class ClosureContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(build_inspection_queue, "COL-03F inspection queue builder missing")
        self.assertIsNotNone(build_primary_bridge_closure, "COL-03F closure builder missing")
        self.assertIsNotNone(write_col03f_json, "COL-03F deterministic writer missing")

    def test_queue_is_candidate_first_and_complete(self):
        queue = build_inspection_queue(_ledger(), predecessor_sha=PREDECESSOR_SHA)
        self.assertEqual(queue["occurrence_count"], 22)
        self.assertEqual(queue["inspection_order"][:2], ["COL-OCC-0001", "COL-OCC-0015"])
        self.assertEqual(len(queue["entries"]), 22)
        self.assertTrue(queue["all_authority_closed"])
        self.assertFalse(queue["any_identity_resolved"])
        self.assertEqual(queue["entries"][0]["candidate_values"], ["4"])

    def test_closure_exposes_candidates_and_unresolved_without_resolving_identity(self):
        ledger = _ledger(with_candidate=True)
        queue = build_inspection_queue(ledger, predecessor_sha=PREDECESSOR_SHA)
        closure = build_primary_bridge_closure(ledger, queue, PREDECESSOR_SHA)
        self.assertEqual(closure["occurrence_count"], 22)
        self.assertEqual(closure["candidate_occurrence_ids"], ["COL-OCC-0001"])
        self.assertEqual(len(closure["unresolved_occurrence_ids"]), 21)
        self.assertEqual(closure["candidate_probe_results"]["COL-OCC-0001"]["candidate_values"], ["4"])
        self.assertIn("COL-OCC-0015", closure["candidate_probe_results"])
        self.assertFalse(closure["any_identity_resolved"])
        self.assertTrue(closure["all_authority_closed"])
        self.assertEqual(
            closure["next_required_action"],
            "HUMAN_ADJUDICATE_PRIMARY_LABEL_BRIDGE_CANDIDATES",
        )

    def test_closure_routes_to_external_primary_evidence_when_no_candidate_exists(self):
        ledger = _ledger(with_candidate=False)
        queue = build_inspection_queue(ledger, predecessor_sha=PREDECESSOR_SHA)
        closure = build_primary_bridge_closure(ledger, queue, PREDECESSOR_SHA)
        self.assertEqual(closure["candidate_occurrence_ids"], [])
        self.assertEqual(len(closure["unresolved_occurrence_ids"]), 22)
        self.assertEqual(
            closure["next_required_action"],
            "ACQUIRE_EXTERNAL_OR_MANUAL_PRIMARY_IDENTITY_EVIDENCE",
        )

    def test_writer_emits_exactly_three_canonical_json_files(self):
        ledger = _ledger(with_candidate=False)
        queue = build_inspection_queue(ledger, predecessor_sha=PREDECESSOR_SHA)
        closure = build_primary_bridge_closure(ledger, queue, PREDECESSOR_SHA)
        artifacts = {
            "primary-bridge-evidence-ledger.json": ledger,
            "primary-bridge-inspection-queue.json": queue,
            "primary-bridge-closure.json": closure,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = write_col03f_json(root, artifacts)
            self.assertEqual(
                [path.name for path in written],
                [
                    "primary-bridge-closure.json",
                    "primary-bridge-evidence-ledger.json",
                    "primary-bridge-inspection-queue.json",
                ],
            )
            self.assertEqual(len(list(root.glob("*.json"))), 3)
            for path in written:
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(payload, dict)
                self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))


if __name__ == "__main__":
    unittest.main()
