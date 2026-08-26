import tempfile
import unittest
from pathlib import Path

from tools.cew_docintel import cli
from tools.cew_docintel import graphic_conventions as gc
from tools.cew_graphic_knowledge import fabric as gkf
from tools.cew_graphic_review import workspace


CTX = {
    "discipline": "structural",
    "document_family": "reinforced_concrete_drawings",
    "drawing_type": "floor_framing_plan",
    "structural_system": "rc_frame",
    "authoring_office": "office-x",
    "country": "IT",
}


class GraphicReviewWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.project = root / "project.sqlite3"
        self.fabric = root / "fabric.sqlite3"
        self.review = root / "review.sqlite3"
        with cli.connect(self.project) as c:
            ts = cli.now()
            c.execute("INSERT INTO sources VALUES(?,?,?)", ("SRC", "source", ts))
            c.execute("INSERT INTO source_versions VALUES(?,?,?,?,?,?)", ("SV", "SRC", "/tmp/source.png", "a"*64, 1, ts))
            c.execute("""INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at,completed_at)
                         VALUES(?,?,?,?,?,?,?,?,?)""", ("GEN", "SV", 1, "test", "1", "SUCCEEDED", "{}", ts, ts))
            c.execute("INSERT INTO source_version_processing VALUES(?,?,?)", ("SV", "GEN", ts))
            c.execute("INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      ("OBS", "SV", 1, "line", 10.0, 20.0, 30.0, 40.0, "vertical", 0.9, "detector", "CANDIDATE", ts))
            c.execute("INSERT INTO observation_generation_bindings VALUES(?,?,?)", ("OBS", "GEN", ts))
            c.commit()
        gkf.connect(self.fabric).close()

    def tearDown(self):
        self.tmp.cleanup()

    def seed_affine_knowledge(self):
        gkf.add_example(
            self.fabric,
            project_id="OTHER",
            source_sha256="b"*64,
            candidate_fingerprint="GCFP-" + "b"*64,
            meaning="COLUMN_MARKER",
            verdict="POSITIVE",
            context=CTX,
            reviewer="other-engineer",
        )

    def test_case_without_shared_knowledge_requires_human_label(self):
        package = workspace.build_case(
            project_db=self.project,
            fabric_db=self.fabric,
            review_db=self.review,
            project_id="N12",
            observation_id="OBS",
            context=CTX,
        )
        self.assertEqual(package["shared_knowledge"]["status"], "NO_TRANSFERABLE_MEANING")
        self.assertEqual(package["semantic_authority"], "PROJECT_HUMAN_REVIEW")
        self.assertTrue(package["graphic"]["candidate_fingerprint"].startswith("GCFP-"))

    def test_affine_shared_candidate_is_explained_not_auto_accepted(self):
        self.seed_affine_knowledge()
        package = workspace.build_case(
            project_db=self.project,
            fabric_db=self.fabric,
            review_db=self.review,
            project_id="N12",
            observation_id="OBS",
            context=CTX,
        )
        suggestion = package["shared_knowledge"]["candidates"][0]
        self.assertEqual(suggestion["meaning"], "COLUMN_MARKER")
        self.assertEqual(suggestion["layers"], ["AFFINE"])
        self.assertTrue(suggestion["contributors"])
        self.assertEqual(package["case"]["state"], "PENDING")

    def test_positive_human_label_specializes_project_then_contributes_example(self):
        self.seed_affine_knowledge()
        package = workspace.build_case(
            project_db=self.project,
            fabric_db=self.fabric,
            review_db=self.review,
            project_id="N12",
            observation_id="OBS",
            context=CTX,
        )
        result = workspace.submit_label(
            project_db=self.project,
            fabric_db=self.fabric,
            review_db=self.review,
            case_id=package["case"]["provenance"]["case_id"],
            meaning="COLUMN_MARKER",
            verdict="POSITIVE",
            reviewer="engineer-n12",
            rationale="confirmed on the original drawing",
        )
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["shared_generalization_created"])
        with gc.connect(self.project) as c:
            labels = c.execute("SELECT meaning,verdict FROM graphic_training_examples").fetchall()
        self.assertEqual([(r["meaning"], r["verdict"]) for r in labels], [("COLUMN_MARKER", "POSITIVE")])
        with gkf.connect(self.fabric) as c:
            projects = {r["project_id"] for r in c.execute("SELECT project_id FROM gkf_examples")}
            generalizations = c.execute("SELECT COUNT(*) n FROM gkf_generalizations").fetchone()["n"]
        self.assertEqual(projects, {"OTHER", "N12"})
        self.assertEqual(generalizations, 0)

    def test_negative_and_uncertain_are_first_class_project_specializations(self):
        for verdict in ("NEGATIVE", "UNCERTAIN"):
            review_db = Path(self.tmp.name) / f"review-{verdict}.sqlite3"
            package = workspace.build_case(
                project_db=self.project,
                fabric_db=self.fabric,
                review_db=review_db,
                project_id="N12",
                observation_id="OBS",
                context=CTX,
            )
            workspace.submit_label(
                project_db=self.project,
                fabric_db=self.fabric,
                review_db=review_db,
                case_id=package["case"]["provenance"]["case_id"],
                meaning=f"MEANING_{verdict}",
                verdict=verdict,
                reviewer=f"reviewer-{verdict}",
                rationale="human classification",
            )
        with gc.connect(self.project) as c:
            verdicts = {r["verdict"] for r in c.execute("SELECT verdict FROM graphic_training_examples")}
        self.assertEqual(verdicts, {"NEGATIVE", "UNCERTAIN"})

    def test_generation_drift_blocks_old_review(self):
        package = workspace.build_case(
            project_db=self.project,
            fabric_db=self.fabric,
            review_db=self.review,
            project_id="N12",
            observation_id="OBS",
            context=CTX,
        )
        with cli.connect(self.project) as c:
            ts = cli.now()
            c.execute("""INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at,completed_at)
                         VALUES(?,?,?,?,?,?,?,?,?)""", ("GEN2", "SV", 2, "test", "2", "SUCCEEDED", "{}", ts, ts))
            c.execute("UPDATE source_version_processing SET current_generation_id=?,updated_at=? WHERE source_version_id=?", ("GEN2", ts, "SV"))
            c.commit()
        with self.assertRaises(ValueError):
            workspace.submit_label(
                project_db=self.project,
                fabric_db=self.fabric,
                review_db=self.review,
                case_id=package["case"]["provenance"]["case_id"],
                meaning="COLUMN_MARKER",
                verdict="POSITIVE",
                reviewer="engineer",
                rationale="old review",
            )


if __name__ == "__main__":
    unittest.main()
