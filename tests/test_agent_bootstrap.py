import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "agent_bootstrap.py"
spec = importlib.util.spec_from_file_location("agent_bootstrap", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AgentBootstrapTests(unittest.TestCase):
    def make_repo(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "knowledge").mkdir()
        (root / "docs" / "REFERENCE").mkdir(parents=True)
        (root / "data" / "canonical").mkdir(parents=True)
        (root / "knowledge" / "KNOWLEDGE_MANIFEST.json").write_text(json.dumps({
            "project": "N12",
            "repository": "antoniocorsano-boop/N12",
            "artifact_registry_patches": []
        }), encoding="utf-8")
        (root / "knowledge" / "CURRENT_STATE.json").write_text(json.dumps({
            "gate": "G0",
            "objective": "Do work",
            "next_action": {"task": "Next"}
        }), encoding="utf-8")
        (root / "knowledge" / "ARTIFACT_REGISTRY.csv").write_text(
            "artifact_id,path,domain,artifact_type,authority,status,may_feed_canonical,validation_method,replaces_or_relates,note\n"
            "A,docs/a.md,SYSTEM,REFERENCE,PROCEDURE,CURRENT,YES,manual,,a\n"
            "B,docs/b.md,SYSTEM,REFERENCE,HISTORICAL,SUSPENDED,NO,manual,,b\n",
            encoding="utf-8"
        )
        return tmp, root

    def test_compact_payload_does_not_expand_registry(self):
        tmp, root = self.make_repo()
        try:
            payload = module.compact_payload(root)
            self.assertEqual(payload["project"]["id"], "N12")
            self.assertNotIn("authorized_artifacts", payload)
            self.assertEqual(payload["engineering"]["gate"], "G0")
        finally:
            tmp.cleanup()

    def test_full_payload_preserves_authority_diagnostics(self):
        tmp, root = self.make_repo()
        try:
            payload = module.full_payload(root)
            self.assertEqual(payload["authorized_artifacts"][0]["id"], "A")
            self.assertEqual(payload["blocked_artifacts"][0]["id"], "B")
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
