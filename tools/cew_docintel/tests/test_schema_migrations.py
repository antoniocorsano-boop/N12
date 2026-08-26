import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.cew_docintel import cli
from tools.cew_docintel import graphic_conventions as gc
from tools.cew_docintel import schema_migrations as sm

LEGACY_GRAPHIC_SCHEMA = '''
CREATE TABLE graphic_training_examples(
 id TEXT PRIMARY KEY,
 observation_id TEXT NOT NULL,
 source_version_id TEXT NOT NULL,
 generation_id TEXT NOT NULL,
 page INTEGER NOT NULL,
 x0 REAL,y0 REAL,x1 REAL,y1 REAL,
 observation_kind TEXT NOT NULL,
 value_text TEXT,
 meaning TEXT NOT NULL,
 verdict TEXT NOT NULL CHECK(verdict IN ('POSITIVE','NEGATIVE','UNCERTAIN')),
 feature_signature TEXT NOT NULL,
 context_json TEXT NOT NULL,
 reviewer TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(observation_id,meaning,reviewer)
);
CREATE TABLE graphic_meaning_proposals(
 id TEXT PRIMARY KEY,
 observation_id TEXT NOT NULL,
 meaning TEXT NOT NULL,
 calibrated_score REAL NOT NULL,
 decisive_support REAL NOT NULL,
 positive_weight REAL NOT NULL,
 negative_weight REAL NOT NULL,
 uncertain_weight REAL NOT NULL,
 calibration_method TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('PROPOSED','HUMAN_VALIDATED','HUMAN_REJECTED')),
 reviewer TEXT,
 rationale TEXT,
 created_at TEXT NOT NULL,
 reviewed_at TEXT
);
'''


class SchemaMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'legacy.sqlite3'
        with cli.connect(self.db) as c:
            ts = cli.now()
            c.execute('INSERT INTO sources VALUES(?,?,?)', ('SRC-L', 'legacy', ts))
            c.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?)', ('SV-L', 'SRC-L', '/tmp/source.png', 'b'*64, 99, ts))
            c.execute('''INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at,completed_at)
                         VALUES(?,?,?,?,?,?,?,?,?)''', ('GEN-L', 'SV-L', 1, 'legacy', '1', 'SUCCEEDED', '{}', ts, ts))
            c.execute('INSERT INTO source_version_processing VALUES(?,?,?)', ('SV-L', 'GEN-L', ts))
            c.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                      ('OBS-L', 'SV-L', 1, 'TEXT_CANDIDATE', 10.0, 20.0, 30.0, 40.0, 'T1', 0.8, 'legacy-detector', 'CANDIDATE', ts))
            c.execute('INSERT INTO observation_generation_bindings VALUES(?,?,?)', ('OBS-L', 'GEN-L', ts))
            c.executescript(LEGACY_GRAPHIC_SCHEMA)
            c.execute('''INSERT INTO graphic_training_examples
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      ('GT-L', 'OBS-L', 'SV-L', 'GEN-L', 1, 10.0, 20.0, 30.0, 40.0,
                       'TEXT_CANDIDATE', 'T1', 'BEAM_TAG', 'POSITIVE', '{}', '{}', 'reviewer', ts))
            c.execute('''INSERT INTO graphic_meaning_proposals
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      ('GP-L', 'OBS-L', 'BEAM_TAG', 0.75, 2.0, 2.0, 0.0, 0.0,
                       'legacy-score', 'PROPOSED', None, None, ts, None))
            c.commit()

    def tearDown(self):
        self.tmp.cleanup()

    def test_legacy_rows_are_backfilled_without_loss(self):
        with gc.connect(self.db) as c:
            training = c.execute('SELECT * FROM graphic_training_examples WHERE id=?', ('GT-L',)).fetchone()
            proposal = c.execute('SELECT * FROM graphic_meaning_proposals WHERE id=?', ('GP-L',)).fetchone()
            version = sm.current_version(c, sm.GRAPHIC_SCOPE)
            training_count = c.execute('SELECT COUNT(*) FROM graphic_training_examples').fetchone()[0]
            proposal_count = c.execute('SELECT COUNT(*) FROM graphic_meaning_proposals').fetchone()[0]
        self.assertEqual(version, sm.GRAPHIC_VERSION)
        self.assertEqual(training_count, 1)
        self.assertEqual(proposal_count, 1)
        self.assertEqual(training['source_sha256'], 'b'*64)
        self.assertEqual(proposal['source_sha256'], 'b'*64)
        self.assertTrue(training['candidate_fingerprint'].startswith('GCFP-'))
        self.assertEqual(proposal['candidate_fingerprint'], training['candidate_fingerprint'])

    def test_migrated_database_accepts_new_stable_labels(self):
        gc.connect(self.db).close()
        gc.label_example(
            self.db,
            'OBS-L',
            'COLUMN_TAG',
            'UNCERTAIN',
            'reviewer-2',
            {'drawing_type': 'structural_plan'},
        )
        with gc.connect(self.db) as c:
            rows = c.execute('SELECT meaning,verdict,candidate_fingerprint FROM graphic_training_examples ORDER BY meaning').fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual({r['verdict'] for r in rows}, {'POSITIVE', 'UNCERTAIN'})
        self.assertTrue(all(r['candidate_fingerprint'] for r in rows))

    def test_incomplete_legacy_lineage_fails_closed(self):
        bad = Path(self.tmp.name) / 'bad.sqlite3'
        with cli.connect(bad) as c:
            ts = cli.now()
            c.execute('INSERT INTO sources VALUES(?,?,?)', ('SRC-X', 'bad', ts))
            c.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?)', ('SV-X', 'SRC-X', '/tmp/x.png', 'c'*64, 1, ts))
            c.executescript(LEGACY_GRAPHIC_SCHEMA)
            c.execute('''INSERT INTO graphic_training_examples
                         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      ('GT-X', 'OBS-MISSING', 'SV-X', 'GEN-MISSING', 1, 0.0, 0.0, 1.0, 1.0,
                       'TEXT_CANDIDATE', 'X', 'UNKNOWN', 'UNCERTAIN', '{}', '{}', 'reviewer', ts))
            c.commit()
        with self.assertRaises(RuntimeError):
            gc.connect(bad)
        with sqlite3.connect(bad) as c:
            count = c.execute('SELECT COUNT(*) FROM graphic_training_examples').fetchone()[0]
            migrated = c.execute(
                "SELECT COUNT(*) FROM cew_schema_migrations WHERE scope=? AND version=?",
                (sm.GRAPHIC_SCOPE, sm.GRAPHIC_VERSION),
            ).fetchone()[0]
        self.assertEqual(count, 1)
        self.assertEqual(migrated, 0)


if __name__ == '__main__':
    unittest.main()
