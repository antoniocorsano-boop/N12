import tempfile
import unittest
from pathlib import Path

from tools.cew_docintel import cli
from tools.cew_docintel import graphic_conventions as gc
from tools.cew_graphic_knowledge import fabric as gkf
from tools.cew_graphic_review import browser_shell


CTX = {
    "discipline": "structural",
    "document_family": "reinforced_concrete_drawings",
    "drawing_type": "UNKNOWN_REQUIRES_REVIEW",
    "country": "IT",
    "source_modality": "scan",
}


class GraphicReviewBrowserShellTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.project = root / "project.sqlite3"
        self.fabric = root / "fabric.sqlite3"
        self.review = root / "review.sqlite3"
        with cli.connect(self.project) as c:
            ts = cli.now()
            c.execute("INSERT INTO sources VALUES(?,?,?)", ("SRC", "source", ts))
            c.execute("INSERT INTO source_versions VALUES(?,?,?,?,?,?)", ("SV", "SRC", "/tmp/source.png", "a" * 64, 1, ts))
            c.execute(
                """INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at,completed_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                ("GEN", "SV", 1, "test", "1", "SUCCEEDED", "{}", ts, ts),
            )
            c.execute("INSERT INTO source_version_processing VALUES(?,?,?)", ("SV", "GEN", ts))
            c.execute(
                "INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("OBS", "SV", 1, "line", 10.0, 20.0, 30.0, 40.0, "vertical", 0.9, "detector", "CANDIDATE", ts),
            )
            c.execute("INSERT INTO observation_generation_bindings VALUES(?,?,?)", ("OBS", "GEN", ts))
            c.commit()
        gkf.connect(self.fabric).close()
        self.package = {
            "schema_version": "0.2.0",
            "work_item_id": "DOC-003",
            "review_package_fingerprint": "sha256:" + "f" * 64,
            "candidates": [{"observation_id": "OBS"}],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def build(self):
        return browser_shell.build_browser_manifest(
            project_db=self.project,
            fabric_db=self.fabric,
            review_db=self.review,
            project_id="N12",
            candidate_package=self.package,
            context=CTX,
            image_map={"a" * 64: "assets/source.png"},
        )

    def test_browser_manifest_renders_real_region_binding_and_human_controls(self):
        manifest = self.build()
        self.assertEqual(manifest["candidate_count"], 1)
        self.assertEqual(manifest["semantic_authority"], "PROJECT_HUMAN_REVIEW")
        self.assertEqual(manifest["automatic_generalization"], "DISABLED")
        case = manifest["cases"][0]
        self.assertEqual(case["image_path"], "assets/source.png")
        self.assertEqual(case["bbox_native"], [10.0, 20.0, 30.0, 40.0])
        html = browser_shell.render_html(manifest)
        self.assertIn("Esporta decisioni JSON", html)
        self.assertIn(browser_shell.DECISION_SCHEMA, html)
        self.assertIn("assets/source.png", html)
        self.assertIn("POSITIVE", html)
        self.assertIn("NEGATIVE", html)
        self.assertIn("UNCERTAIN", html)

    def test_exported_decision_batch_rechecks_workspace_and_contributes_without_generalizing(self):
        manifest = self.build()
        case_id = manifest["cases"][0]["case_id"]
        result = browser_shell.apply_decision_batch(
            project_db=self.project,
            fabric_db=self.fabric,
            review_db=self.review,
            decision_batch={
                "schema_version": browser_shell.DECISION_SCHEMA,
                "project_id": "N12",
                "decisions": [{
                    "case_id": case_id,
                    "meaning": "COLUMN_PLAN_MARKER",
                    "verdict": "POSITIVE",
                    "reviewer": "engineer-n12",
                    "rationale": "confirmed against the project source region",
                }],
            },
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["decision_count"], 1)
        self.assertEqual(result["automatic_generalization"], "DISABLED")
        with gc.connect(self.project) as c:
            labels = c.execute("SELECT meaning,verdict FROM graphic_training_examples").fetchall()
        self.assertEqual([(r["meaning"], r["verdict"]) for r in labels], [("COLUMN_PLAN_MARKER", "POSITIVE")])
        with gkf.connect(self.fabric) as c:
            examples = c.execute("SELECT project_id,meaning,verdict FROM gkf_examples").fetchall()
            generalizations = c.execute("SELECT COUNT(*) n FROM gkf_generalizations").fetchone()["n"]
        self.assertEqual([(r["project_id"], r["meaning"], r["verdict"]) for r in examples], [("N12", "COLUMN_PLAN_MARKER", "POSITIVE")])
        self.assertEqual(generalizations, 0)

    def test_decision_apply_fails_closed_after_generation_drift(self):
        manifest = self.build()
        case_id = manifest["cases"][0]["case_id"]
        with cli.connect(self.project) as c:
            ts = cli.now()
            c.execute(
                """INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at,completed_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                ("GEN2", "SV", 2, "test", "2", "SUCCEEDED", "{}", ts, ts),
            )
            c.execute("UPDATE source_version_processing SET current_generation_id=?,updated_at=? WHERE source_version_id=?", ("GEN2", ts, "SV"))
            c.commit()
        with self.assertRaises(ValueError):
            browser_shell.apply_decision_batch(
                project_db=self.project,
                fabric_db=self.fabric,
                review_db=self.review,
                decision_batch={
                    "schema_version": browser_shell.DECISION_SCHEMA,
                    "decisions": [{
                        "case_id": case_id,
                        "meaning": "COLUMN_PLAN_MARKER",
                        "verdict": "POSITIVE",
                        "reviewer": "engineer-n12",
                        "rationale": "stale decision",
                    }],
                },
            )


if __name__ == "__main__":
    unittest.main()
