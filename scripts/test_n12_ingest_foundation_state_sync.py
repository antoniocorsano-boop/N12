#!/usr/bin/env python3
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import n12_ingest_agent_result as ingestor


class FoundationStateSyncTest(unittest.TestCase):
    def test_foundation_model_counts_and_status_come_from_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            gate_path = Path(td) / "M1F_FOUNDATION_GATE_v1.csv"
            with gate_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["check_id", "metric", "expected", "actual", "status", "severity", "note"],
                )
                writer.writeheader()
                writer.writerows([
                    {"check_id": "M1F-MODEL-G01", "metric": "support_identities", "expected": "41", "actual": "41", "status": "PASS", "severity": "HARD", "note": "test"},
                    {"check_id": "M1F-MODEL-G02", "metric": "foundation_members_primary", "expected": "60", "actual": "60", "status": "PASS", "severity": "HARD", "note": "test"},
                    {"check_id": "M1F-MODEL-G03", "metric": "connected_components", "expected": "2", "actual": "2", "status": "PASS", "severity": "HARD", "note": "test"},
                    {"check_id": "M1F-MODEL-FINAL", "metric": "gate_state", "expected": "TEST_GATE_COMPLETE", "actual": "TEST_GATE_COMPLETE", "status": "PASS_WITH_WATCH", "severity": "GATE", "note": "test"},
                ])

            previous = getattr(ingestor, "FOUNDATION_MODEL_GATE", None)
            ingestor.FOUNDATION_MODEL_GATE = gate_path
            try:
                state: dict = {}
                ingestor.sync_domain_state_after_result(
                    state,
                    {"decision": "PASS_WITH_WATCH", "work_item_id": ingestor.FOUNDATION_MODEL_ID},
                )
            finally:
                if previous is None:
                    delattr(ingestor, "FOUNDATION_MODEL_GATE")
                else:
                    ingestor.FOUNDATION_MODEL_GATE = previous

            progress = state["foundation_progress"]
            self.assertEqual(progress["current_supports"], 41)
            self.assertEqual(progress["current_foundation_members"], 60)
            self.assertEqual(progress["current_connected_components"], 2)
            self.assertEqual(progress["current_model_status"], "TEST_GATE_COMPLETE")


if __name__ == "__main__":
    unittest.main()
