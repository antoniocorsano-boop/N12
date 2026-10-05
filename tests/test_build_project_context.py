import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_project_context.py"
spec = importlib.util.spec_from_file_location("build_project_context", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ContextPackTests(unittest.TestCase):
    def make_repo(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "knowledge").mkdir()
        (root / "docs" / "REFERENCE").mkdir(parents=True)
        (root / "data" / "canonical").mkdir(parents=True)
        (root / "knowledge" / "KNOWLEDGE_MANIFEST.json").write_text(json.dumps({
            "schema_version": "1.0",
            "project": "N12",
            "repository": "antoniocorsano-boop/N12",
            "canonical_branch": "work/m0-global-model",
            "current_domain": "STRUCTURAL_MODEL_COMPLETION",
            "default_unregistered_policy": "UNREGISTERED_NON_AUTHORITATIVE"
        }), encoding="utf-8")
        (root / "knowledge" / "CURRENT_STATE.json").write_text(json.dumps({
            "gate": "M1-F/FOUNDATION_PRIMARY_EVIDENCE",
            "status": "IN_PROGRESS",
            "objective": "Complete the calculation model",
            "automation": {"current_work_item": "M1E-CALCULATION-MODEL-HANDOFF"},
            "next_action": {"task": "Build calculation-model handoff"},
            "completion_condition": "CALCULATION_MODEL_READY",
            "anti_restart_rule": "Reuse validated checkpoints."
        }), encoding="utf-8")
        (root / "knowledge" / "ARTIFACT_REGISTRY.csv").write_text(
            "artifact_id,path,domain,artifact_type,authority,status,may_feed_canonical,validation_method,replaces_or_relates,note\n",
            encoding="utf-8"
        )
        (root / "data" / "canonical" / "CEW_PROJECT_STATE_CURRENT_v1.json").write_text(json.dumps({
            "status": "CURRENT",
            "current_product_work_item": {"id": "CEW-B1", "state": "IN_PROGRESS"},
            "next_action": "Complete B1"
        }), encoding="utf-8")
        (root / "docs" / "REFERENCE" / "BASELINE.md").write_text(
            "# CEW Open Source Baseline\n\n**Stato:** HUMAN_APPROVED\n\nBody\n",
            encoding="utf-8"
        )
        return tmp, root

    def test_builds_compact_context_with_reference_index(self):
        tmp, root = self.make_repo()
        try:
            pack = module.build_context_pack(root)
            self.assertEqual(pack["project"]["id"], "N12")
            self.assertEqual(pack["engineering"]["gate"], "M1-F/FOUNDATION_PRIMARY_EVIDENCE")
            self.assertEqual(pack["engineering"]["current_work_item"], "M1E-CALCULATION-MODEL-HANDOFF")
            self.assertEqual(pack["product"]["current_work_item"], "CEW-B1")
            self.assertEqual(pack["references"][0]["path"], "docs/REFERENCE/BASELINE.md")
            self.assertEqual(pack["references"][0]["status"], "HUMAN_APPROVED")
            self.assertIn("knowledge/CONTEXT_PACK_CURRENT.json", pack["required_reads"]["orientation"])
            self.assertIn("knowledge/CURRENT_STATE.json", pack["required_reads"]["engineering_mutation"])
        finally:
            tmp.cleanup()

    def test_context_pack_is_deterministic_and_compact(self):
        tmp, root = self.make_repo()
        try:
            first = module.build_context_pack(root)
            second = module.build_context_pack(root)
            self.assertEqual(first, second)
            encoded = json.dumps(first, ensure_ascii=False).encode("utf-8")
            self.assertLess(len(encoded), 16_384)
        finally:
            tmp.cleanup()

    def test_write_and_check_detect_staleness(self):
        tmp, root = self.make_repo()
        try:
            module.write_context_pack(root)
            self.assertTrue(module.context_pack_is_current(root))
            state_path = root / "knowledge" / "CURRENT_STATE.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["gate"] = "M1-E/NEW_GATE"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            self.assertFalse(module.context_pack_is_current(root))
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
