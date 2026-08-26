import json
import tempfile
import unittest
from pathlib import Path

from tools.cew_docintel import cli
from tools.cew_docintel import graphic_conventions as gc
from tools.cew_graphic_knowledge import docintel_bridge as bridge
from tools.cew_graphic_knowledge import fabric as gkf


class DocIntelBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.docintel = root / "project.sqlite3"
        self.fabric = root / "fabric.sqlite3"
        with cli.connect(self.docintel) as c:
            ts = cli.now()
            c.execute("INSERT INTO sources VALUES(?,?,?)", ("SRC", "source", ts))
            c.execute("INSERT INTO source_versions VALUES(?,?,?,?,?,?)", ("SV", "SRC", "/tmp/source.png", "d"*64, 1, ts))
            c.execute("""INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at,completed_at)
                         VALUES(?,?,?,?,?,?,?,?,?)""", ("GEN", "SV", 1, "test", "1", "SUCCEEDED", "{}", ts, ts))
            c.execute("INSERT INTO source_version_processing VALUES(?,?,?)", ("SV", "GEN", ts))
            c.execute("INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      ("OBS", "SV", 1, "TEXT_CANDIDATE", 10.0, 20.0, 30.0, 40.0, "T1", 0.9, "detector", "CANDIDATE", ts))
            c.execute("INSERT INTO observation_generation_bindings VALUES(?,?,?)", ("OBS", "GEN", ts))
            c.commit()
        gc.label_example(
            self.docintel,
            "OBS",
            "BEAM_TAG",
            "POSITIVE",
            "engineer",
            {"discipline": "structural", "drawing_type": "floor_framing_plan", "authoring_office": "office-x"},
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_project_labels_enter_fabric_without_copying_source_files(self):
        receipt = bridge.import_project_labels(self.docintel, self.fabric, "N12")
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["source_files_copied"], 0)
        self.assertEqual(receipt["labels_seen"], 1)
        with gkf.connect(self.fabric) as c:
            row = c.execute("SELECT * FROM gkf_examples").fetchone()
        self.assertEqual(row["project_id"], "N12")
        self.assertEqual(row["source_sha256"], "d"*64)
        self.assertTrue(row["candidate_fingerprint"].startswith("GCFP-"))

    def test_shared_resolution_returns_candidate_but_requires_project_specialization(self):
        bridge.import_project_labels(self.docintel, self.fabric, "N12")
        result = bridge.resolve_for_project(
            self.fabric,
            "NEW-PROJECT",
            {"discipline": "structural", "drawing_type": "floor_framing_plan", "authoring_office": "office-x"},
        )
        self.assertEqual(result["status"], "CANDIDATES_AVAILABLE")
        self.assertEqual(result["candidates"][0]["meaning"], "BEAM_TAG")
        self.assertTrue(result["project_specialization_required"])
        self.assertEqual(result["shared_knowledge_mutation"], "NONE")
        self.assertEqual(result["semantic_authority"], "NONE_UNTIL_PROJECT_HUMAN_VALIDATION")

    def test_bridge_is_idempotent_at_fabric_identity_level(self):
        bridge.import_project_labels(self.docintel, self.fabric, "N12")
        bridge.import_project_labels(self.docintel, self.fabric, "N12")
        with gkf.connect(self.fabric) as c:
            count = c.execute("SELECT COUNT(*) n FROM gkf_examples").fetchone()["n"]
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
