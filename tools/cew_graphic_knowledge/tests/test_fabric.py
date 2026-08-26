import json
import tempfile
import unittest
from pathlib import Path

from tools.cew_graphic_knowledge import fabric as gkf


CTX_A = {
    "discipline": "structural",
    "document_family": "reinforced_concrete_drawings",
    "drawing_type": "floor_framing_plan",
    "structural_system": "rc_frame",
    "drafting_era": "1970s-1980s",
    "authoring_office": "office-x",
    "notation_family": "hand_drafted_rc",
    "country": "IT",
    "language": "it",
    "source_modality": "scan",
}
CTX_B = dict(CTX_A, authoring_office="office-y")
CTX_C = dict(CTX_A, drawing_type="beam_schedule", authoring_office="office-z")
CTX_UNRELATED = {
    "discipline": "architecture",
    "document_family": "architectural_plan",
    "drawing_type": "floor_plan",
    "source_modality": "cad_pdf",
}


def fp(char: str) -> str:
    return "GCFP-" + char * 64


class GraphicKnowledgeFabricTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "shared.sqlite3"
        gkf.connect(self.db).close()

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, project, meaning, verdict, fingerprint, context, reviewer="engineer"):
        return gkf.add_example(
            self.db,
            project_id=project,
            source_sha256=(project[-1].lower() if project[-1].isalnum() else "a") * 64,
            candidate_fingerprint=fingerprint,
            meaning=meaning,
            verdict=verdict,
            context=context,
            reviewer=reviewer,
        )

    def test_affinity_rewards_similar_project_context(self):
        close = gkf.context_affinity(CTX_A, CTX_B)["score"]
        far = gkf.context_affinity(CTX_A, CTX_UNRELATED)["score"]
        self.assertGreater(close, 0.7)
        self.assertGreater(close, far)

    def test_local_specialization_has_stronger_weight_than_external_example(self):
        self.add("P1", "COLUMN_MARKER", "POSITIVE", fp("1"), CTX_A)
        self.add("P2", "COLUMN_MARKER", "NEGATIVE", fp("2"), CTX_A)
        result = gkf.resolve(self.db, project_id="P2", context=CTX_A)
        candidate = result["candidates"][0]
        self.assertIn("LOCAL", candidate["layers"])
        self.assertIn("AFFINE", candidate["layers"])
        self.assertGreater(candidate["negative_weight"], 0)
        self.assertLess(candidate["calibrated_score"], 0.5)
        self.assertTrue(candidate["conflict"])
        self.assertEqual(result["semantic_authority"], "NONE_UNTIL_PROJECT_HUMAN_VALIDATION")

    def test_affine_projects_can_be_combined(self):
        self.add("P1", "BEAM_TAG", "POSITIVE", fp("1"), CTX_A)
        self.add("P2", "BEAM_TAG", "POSITIVE", fp("2"), CTX_B)
        result = gkf.resolve(self.db, project_id="P3", context=CTX_A)
        candidate = result["candidates"][0]
        self.assertGreater(candidate["calibrated_score"], 0.5)
        self.assertEqual(candidate["layers"], ["AFFINE"])
        projects = {c["project_id"] for c in candidate["contributors"]}
        self.assertEqual(projects, {"P1", "P2"})

    def test_unrelated_projects_do_not_transfer(self):
        self.add("P1", "ROOM_LABEL", "POSITIVE", fp("1"), CTX_UNRELATED)
        result = gkf.resolve(self.db, project_id="N12", context=CTX_A)
        self.assertEqual(result["status"], "NO_TRANSFERABLE_MEANING")

    def test_family_and_global_generalization_require_multiple_projects_and_human_review(self):
        self.add("P1", "BEAM_TAG", "POSITIVE", fp("1"), CTX_A)
        self.add("P2", "BEAM_TAG", "POSITIVE", fp("2"), CTX_A)
        self.add("P3", "BEAM_TAG", "POSITIVE", fp("3"), CTX_C)
        created = gkf.propose_generalizations(self.db)
        self.assertGreaterEqual(len(created), 2)
        with gkf.connect(self.db) as c:
            rows = c.execute("SELECT * FROM gkf_generalizations ORDER BY tier").fetchall()
        self.assertEqual({r["tier"] for r in rows}, {"FAMILY", "GLOBAL"})
        self.assertTrue(all(r["state"] == "PROPOSED" for r in rows))
        global_row = next(r for r in rows if r["tier"] == "GLOBAL")
        gkf.review_generalization(self.db, global_row["id"], "APPROVE", "review-board", "validated across project families")
        with gkf.connect(self.db) as c:
            state = c.execute("SELECT state FROM gkf_generalizations WHERE id=?", (global_row["id"],)).fetchone()["state"]
        self.assertEqual(state, "HUMAN_VALIDATED")

    def test_negative_counterevidence_blocks_unsafe_family_generalization(self):
        self.add("P1", "COLUMN_MARKER", "POSITIVE", fp("1"), CTX_A)
        self.add("P2", "COLUMN_MARKER", "POSITIVE", fp("2"), CTX_A)
        self.add("P3", "COLUMN_MARKER", "NEGATIVE", fp("3"), CTX_A)
        created = gkf.propose_generalizations(self.db, max_negative_ratio=0.2)
        with gkf.connect(self.db) as c:
            family_count = c.execute("SELECT COUNT(*) n FROM gkf_generalizations WHERE tier='FAMILY'").fetchone()["n"]
        self.assertEqual(family_count, 0)
        self.assertEqual(created, [])

    def test_validated_shared_pack_imports_as_supported_not_local_authority(self):
        self.add("P1", "BEAM_TAG", "POSITIVE", fp("1"), CTX_A)
        self.add("P2", "BEAM_TAG", "POSITIVE", fp("2"), CTX_A)
        created = gkf.propose_generalizations(self.db)
        with gkf.connect(self.db) as c:
            family = c.execute("SELECT id FROM gkf_generalizations WHERE tier='FAMILY'").fetchone()
        self.assertIsNotNone(family)
        gkf.review_generalization(self.db, family["id"], "APPROVE", "board", "cross-project validation")
        pack = gkf.export_pack(self.db, "CEW-LAB-A")
        self.assertTrue(pack["pack_fingerprint"].startswith("sha256:"))

        db2 = Path(self.tmp.name) / "receiver.sqlite3"
        result = gkf.import_pack(db2, pack)
        self.assertEqual(result["status"], "IMPORTED_SUPPORTED")
        with gkf.connect(db2) as c:
            states = {r["state"] for r in c.execute("SELECT state FROM gkf_generalizations")}
        self.assertEqual(states, {"IMPORTED_SUPPORTED"})
        resolved = gkf.resolve(db2, project_id="NEW", context=CTX_A)
        self.assertEqual(resolved["semantic_authority"], "NONE_UNTIL_PROJECT_HUMAN_VALIDATION")

    def test_pack_fingerprint_detects_tampering_and_import_is_idempotent(self):
        self.add("P1", "BEAM_TAG", "POSITIVE", fp("1"), CTX_A)
        pack = gkf.export_pack(self.db, "CEW-LAB-A")
        receiver = Path(self.tmp.name) / "receiver.sqlite3"
        first = gkf.import_pack(receiver, pack)
        second = gkf.import_pack(receiver, pack)
        self.assertEqual(first["status"], "IMPORTED_SUPPORTED")
        self.assertEqual(second["status"], "ALREADY_IMPORTED")
        tampered = json.loads(json.dumps(pack))
        tampered["examples"][0]["meaning"] = "OTHER"
        with self.assertRaises(ValueError):
            gkf.import_pack(Path(self.tmp.name) / "bad.sqlite3", tampered)


if __name__ == "__main__":
    unittest.main()
