import tempfile
import unittest
from pathlib import Path

from tools.cew_docintel import cli
from tools.cew_docintel import graphic_conventions as gc


class GraphicConventionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'docintel.sqlite3'
        with cli.connect(self.db) as c:
            ts = cli.now()
            c.execute('INSERT INTO sources VALUES(?,?,?)', ('SRC-1', 'test', ts))
            c.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?)', ('SV-1', 'SRC-1', '/tmp/source.png', 'a'*64, 123, ts))
            c.execute('''INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at,completed_at)
                         VALUES(?,?,?,?,?,?,?,?,?)''', ('GEN-1', 'SV-1', 1, 'test', '1', 'SUCCEEDED', '{}', ts, ts))
            c.execute('INSERT INTO source_version_processing VALUES(?,?,?)', ('SV-1', 'GEN-1', ts))
            for oid, kind, text, x in [
                ('OBS-1', 'TEXT_CANDIDATE', 'T1', 0.0),
                ('OBS-2', 'TEXT_CANDIDATE', 'T1', 10.0),
                ('OBS-3', 'TEXT_CANDIDATE', 'T1', 20.0),
                ('OBS-4', 'GEOMETRY_SEGMENT', None, 30.0),
            ]:
                c.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                          (oid, 'SV-1', 1, kind, x, 0.0, x+5.0, 5.0, text, 0.8, 'test-detector', 'CANDIDATE', ts))
                c.execute('INSERT INTO observation_generation_bindings VALUES(?,?,?)', (oid, 'GEN-1', ts))
            c.commit()

    def tearDown(self):
        self.tmp.cleanup()

    def test_positive_negative_uncertain_labels_are_preserved_with_lineage(self):
        ctx = {'drawing_type': 'roof_plan', 'document_family': 'structural'}
        gc.label_example(self.db, 'OBS-1', 'BEAM_TAG', 'POSITIVE', 'reviewer-a', ctx)
        gc.label_example(self.db, 'OBS-2', 'BEAM_TAG', 'NEGATIVE', 'reviewer-a', ctx)
        gc.label_example(self.db, 'OBS-3', 'BEAM_TAG', 'UNCERTAIN', 'reviewer-a', ctx)
        with gc.connect(self.db) as c:
            rows = c.execute('SELECT * FROM graphic_training_examples ORDER BY verdict').fetchall()
        self.assertEqual({r['verdict'] for r in rows}, {'POSITIVE', 'NEGATIVE', 'UNCERTAIN'})
        self.assertTrue(all(r['source_version_id'] == 'SV-1' and r['generation_id'] == 'GEN-1' for r in rows))
        self.assertTrue(all(r['x0'] is not None and r['x1'] is not None for r in rows))

    def test_counterexample_reduces_score(self):
        ctx = {'drawing_type': 'roof_plan'}
        gc.label_example(self.db, 'OBS-1', 'BEAM_TAG', 'POSITIVE', 'r1', ctx)
        before = gc.score_meaning(self.db, 'OBS-3', 'BEAM_TAG', ctx)['calibrated_score']
        gc.label_example(self.db, 'OBS-2', 'BEAM_TAG', 'NEGATIVE', 'r2', ctx)
        after = gc.score_meaning(self.db, 'OBS-3', 'BEAM_TAG', ctx)['calibrated_score']
        self.assertLess(after, before)

    def test_uncertainty_damps_semantic_score(self):
        ctx = {'drawing_type': 'roof_plan'}
        gc.label_example(self.db, 'OBS-1', 'BEAM_TAG', 'POSITIVE', 'r1', ctx)
        before = gc.score_meaning(self.db, 'OBS-3', 'BEAM_TAG', ctx)['calibrated_score']
        gc.label_example(self.db, 'OBS-2', 'BEAM_TAG', 'UNCERTAIN', 'r2', ctx)
        after = gc.score_meaning(self.db, 'OBS-3', 'BEAM_TAG', ctx)['calibrated_score']
        self.assertGreater(before, after)
        self.assertGreater(after, 0.5)

    def test_review_package_preserves_region_and_does_not_invent_meaning(self):
        package = gc.build_review_package(self.db, limit=4)
        self.assertEqual(package['status'], 'BLOCKED_HUMAN_DECISION')
        self.assertEqual(package['semantic_promotion'], 'HUMAN_ONLY')
        self.assertEqual(package['candidate_count'], 4)
        self.assertTrue(all(len(c['bbox_native']) == 4 for c in package['candidates']))
        self.assertTrue(all(c['generation_id'] == 'GEN-1' for c in package['candidates']))
        self.assertTrue(all(c['suggested_meanings'] == [] for c in package['candidates']))

    def test_human_validation_is_required_for_meaning_proposal(self):
        ctx = {'drawing_type': 'roof_plan'}
        gc.label_example(self.db, 'OBS-1', 'BEAM_TAG', 'POSITIVE', 'r1', ctx)
        scored = gc.propose_meanings(self.db, 'OBS-3', ctx)[0]
        pid = gc.persist_proposal(self.db, scored)
        with self.assertRaises(ValueError):
            gc.review_proposal(self.db, pid, 'VALIDATE', '', 'approved')
        gc.review_proposal(self.db, pid, 'VALIDATE', 'engineer', 'confirmed from original drawing')
        with gc.connect(self.db) as c:
            state = c.execute('SELECT state FROM graphic_meaning_proposals WHERE id=?', (pid,)).fetchone()['state']
        self.assertEqual(state, 'HUMAN_VALIDATED')

    def test_stale_generation_cannot_be_labeled(self):
        with cli.connect(self.db) as c:
            ts = cli.now()
            c.execute('''INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at,completed_at)
                         VALUES(?,?,?,?,?,?,?,?,?)''', ('GEN-2', 'SV-1', 2, 'test', '2', 'SUCCEEDED', '{}', ts, ts))
            c.execute('UPDATE source_version_processing SET current_generation_id=? WHERE source_version_id=?', ('GEN-2', 'SV-1'))
            c.commit()
        with self.assertRaises(ValueError):
            gc.label_example(self.db, 'OBS-1', 'BEAM_TAG', 'POSITIVE', 'reviewer', {})


if __name__ == '__main__':
    unittest.main()
