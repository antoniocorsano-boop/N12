import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from tools.cew_dossier import engine


BINDING = {"kind": "model_generation", "id": "MODEL", "generation_id": "GEN-1", "fingerprint": "sha256:" + "a" * 64}


class DossierEngineTests(unittest.TestCase):
    def spec(self):
        return {
            "project_id": "N12",
            "global_bindings": [{"kind": "source_index", "id": "SRC", "generation_id": "SRCGEN-1", "fingerprint": "sha256:" + "b" * 64}],
            "sections": [
                {"section_id": "S1", "title": "Structural model", "state": "AVAILABLE", "bindings": [BINDING], "artifact_refs": ["model.json"]},
                {"section_id": "S2", "title": "FEM results", "state": "UNAVAILABLE_BLOCKED", "blockers": ["FEM-001 BLOCKED_EVIDENCE"]},
            ],
        }

    def test_manifest_identity_is_content_deterministic_and_generation_bound(self):
        a = engine.build_manifest(self.spec())
        b = engine.build_manifest(self.spec())
        self.assertEqual(a["generation_id"], b["generation_id"])
        self.assertEqual(a["content_fingerprint"], b["content_fingerprint"])
        self.assertTrue(a["content_fingerprint"].startswith("sha256:"))
        self.assertEqual(a["canonical_promotion"], "DISABLED")

    def test_available_section_requires_exact_generation_binding(self):
        bad = self.spec()
        bad["sections"][0]["bindings"] = []
        with self.assertRaises(ValueError):
            engine.build_manifest(bad)

    def test_blocked_section_requires_explicit_blocker(self):
        bad = self.spec()
        bad["sections"][1]["blockers"] = []
        with self.assertRaises(ValueError):
            engine.build_manifest(bad)

    def test_fingerprint_tampering_fails_closed(self):
        manifest = engine.build_manifest(self.spec())
        manifest["sections"][0]["title"] = "tampered"
        ok, errors = engine.validate_manifest(manifest)
        self.assertFalse(ok)
        self.assertIn("dossier content fingerprint mismatch", errors)

    def test_immutable_write_is_idempotent_and_rejects_different_generation(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "dossier.json"
            manifest = engine.build_manifest(self.spec())
            self.assertEqual(engine.write_immutable(path, manifest), "WRITTEN")
            self.assertEqual(engine.write_immutable(path, manifest), "ALREADY_PRESENT_IDENTICAL")
            other_spec = self.spec()
            other_spec["sections"][1]["blockers"].append("NEW")
            with self.assertRaises(FileExistsError):
                engine.write_immutable(path, engine.build_manifest(other_spec))

    def test_supersession_changes_generation_without_mutating_previous(self):
        first = engine.build_manifest(self.spec())
        spec2 = self.spec()
        spec2["supersedes"] = first["generation_id"]
        second = engine.build_manifest(spec2)
        self.assertNotEqual(first["generation_id"], second["generation_id"])
        self.assertEqual(second["supersedes"], first["generation_id"])

    def test_renderer_is_projection_and_keeps_blocked_sections_visible(self):
        manifest = engine.build_manifest(self.spec())
        html = engine.render_html(manifest)
        self.assertIn("NOT ENGINEERING AUTHORITY", html)
        self.assertIn("UNAVAILABLE_BLOCKED", html)
        self.assertIn("FEM-001 BLOCKED_EVIDENCE", html)
        self.assertIn("GEN-1", html)


if __name__ == "__main__":
    unittest.main()
