from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


class RepositoryMemoryGateTests(unittest.TestCase):
    def _load_validator(self):
        try:
            spec = importlib.util.find_spec("automation.validate_cew_repo_memory")
        except ModuleNotFoundError:
            spec = None
        self.assertIsNotNone(spec, "repository-memory validator module must exist")
        return importlib.import_module("automation.validate_cew_repo_memory")

    def _write_minimal_repo(self, root: Path) -> None:
        governance = root / "governance" / "repo-memory"
        governance.mkdir(parents=True)
        plans = root / "docs" / "superpowers" / "plans"
        plans.mkdir(parents=True)
        (governance / "CEW_CAPABILITY_REGISTRY_v1.json").write_text(
            json.dumps(
                {
                    "schema_version": "CEW_CAPABILITY_REGISTRY_v1",
                    "reuse_vocabulary": ["REUSE", "ADAPT", "PORT", "REFERENCE_ONLY", "DO_NOT_REUSE"],
                    "capabilities": [
                        {
                            "capability_id": "CEW-CAP-TEST",
                            "reuse_disposition": "REUSE",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (governance / "CEW_TEST_REUSE_DECISION_v1.json").write_text(
            json.dumps(
                {
                    "decision_id": "CEW-TEST-REUSE-v1",
                    "consulted_capabilities": ["CEW-CAP-TEST"],
                    "decisions": [
                        {
                            "responsibility": "test",
                            "source_capability": "CEW-CAP-TEST",
                            "reuse_disposition": "REUSE",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (plans / "2026-10-28-cew-test.md").write_text(
            "# CEW test plan\n\n## Repository Memory / Reuse Assessment\n\n- `CEW-CAP-TEST` -> REUSE.\n",
            encoding="utf-8",
        )

    def test_current_repository_memory_is_consistent(self):
        validator = self._load_validator()
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(validator.validate_repository_memory(root), [])

    def test_unknown_capability_reference_fails_closed(self):
        validator = self._load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_repo(root)
            decision = root / "governance" / "repo-memory" / "CEW_TEST_REUSE_DECISION_v1.json"
            payload = json.loads(decision.read_text(encoding="utf-8"))
            payload["consulted_capabilities"].append("CEW-CAP-MISSING")
            decision.write_text(json.dumps(payload), encoding="utf-8")
            errors = validator.validate_repository_memory(root)
            self.assertTrue(any("CEW-CAP-MISSING" in error for error in errors), errors)

    def test_invalid_reuse_disposition_fails_closed(self):
        validator = self._load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_repo(root)
            decision = root / "governance" / "repo-memory" / "CEW_TEST_REUSE_DECISION_v1.json"
            payload = json.loads(decision.read_text(encoding="utf-8"))
            payload["decisions"][0]["reuse_disposition"] = "INVENT_AGAIN"
            decision.write_text(json.dumps(payload), encoding="utf-8")
            errors = validator.validate_repository_memory(root)
            self.assertTrue(any("INVENT_AGAIN" in error for error in errors), errors)

    def test_cew_plan_without_memory_assessment_fails_closed(self):
        validator = self._load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_minimal_repo(root)
            plan = root / "docs" / "superpowers" / "plans" / "2026-10-28-cew-test.md"
            plan.write_text("# CEW test plan\n\nNo reuse section.\n", encoding="utf-8")
            errors = validator.validate_repository_memory(root)
            self.assertTrue(any("Repository Memory / Reuse Assessment" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
