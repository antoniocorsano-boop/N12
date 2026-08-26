import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('decision_store',ROOT/'decision_store.py')
M=importlib.util.module_from_spec(SPEC); assert SPEC.loader is not None; SPEC.loader.exec_module(M)

class DecisionStoreTests(unittest.TestCase):
    def evidence(self):
        return [
            {'evidence_id':'EV-1','label':'Tavola originale','summary':'Dettaglio candidato leggibile','locator':'TAV07:R1','role':'SUPPORTING'},
            {'evidence_id':'EV-2','label':'Controevidenza','summary':'Seconda regione non coerente','locator':'TAV07:R2','role':'COUNTER'}
        ]
    def test_package_is_human_first_and_keeps_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'review.sqlite3'
            cid=M.create_case(db,'Sezione trave','Quale sezione è documentata?','Candidato 25x70','sha256:a',self.evidence())
            p=M.package(db,cid)
            self.assertEqual(p['title'],'Sezione trave')
            self.assertEqual(p['question'],'Quale sezione è documentata?')
            self.assertIn('provenance',p); self.assertEqual(p['provenance']['case_id'],cid)
            self.assertEqual(len(p['evidence']),2)
    def test_approve_persists_decision_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'review.sqlite3'
            cid=M.create_case(db,'Caso','Confermare?','Candidato','sha256:a',self.evidence())
            rid=M.decide(db,cid,'APPROVE','engineer','coerente con evidenza','sha256:a')
            p=M.package(db,cid)
            self.assertTrue(rid.startswith('DEC-')); self.assertEqual(p['state'],'APPROVED'); self.assertEqual(p['decision_history'][0]['decision'],'APPROVE')
            self.assertEqual(M.validate_store(db)['status'],'PASS')
    def test_correction_requires_explicit_payload(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'review.sqlite3'; cid=M.create_case(db,'Caso','Correggere?','Candidato','sha256:a',self.evidence())
            with self.assertRaises(ValueError): M.decide(db,cid,'CORRECT','engineer','serve correzione','sha256:a')
            M.decide(db,cid,'CORRECT','engineer','correzione verificata','sha256:a',{'section':'30x70'})
            self.assertEqual(M.package(db,cid)['state'],'CORRECTED')
    def test_source_drift_invalidates_review_without_rewriting_history(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'review.sqlite3'; cid=M.create_case(db,'Caso','Confermare?','Candidato','sha256:a',self.evidence())
            M.decide(db,cid,'APPROVE','engineer','ok','sha256:a')
            self.assertTrue(M.invalidate_on_source_drift(db,cid,'sha256:b'))
            p=M.package(db,cid); self.assertEqual(p['state'],'STALE_REVIEW'); self.assertEqual(len(p['decision_history']),1); self.assertEqual(p['decision_history'][0]['source_fingerprint'],'sha256:a')
    def test_decision_with_drift_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'review.sqlite3'; cid=M.create_case(db,'Caso','Confermare?','Candidato','sha256:a',self.evidence())
            with self.assertRaises(ValueError): M.decide(db,cid,'APPROVE','engineer','ok','sha256:b')
            self.assertEqual(M.package(db,cid)['state'],'STALE_REVIEW')

if __name__=='__main__': unittest.main()
