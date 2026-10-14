import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from cew_gate_control_plane.contracts import ControlPlaneError
from cew_gate_control_plane.handoff import HandoffContext, build_handoff_envelope, validate_artifact_id, verify_handoff_directory
from cew_gate_control_plane.trust_anchor import TrustAnchor

G="1"*40; BUNDLE="2"*64; M="3"*40; AID="A0"; AB="4"*40; AS="5"*64; O="6"*40; B="7"*40; H="8"*40
ANCHOR=TrustAnchor(G,BUNDLE,M,AID,AB,AS,O); CTX=HandoffContext(101,2,B,148,"fork/N12",H)

def receipt(qualified=True):
    return {"schema_id":"CEW_QUALIFICATION_RECEIPT","schema_version":1,"qualified_at":"2026-10-14T00:00:00Z","control_plane":{"base_commit_sha":B},"gate_core":{"repository":"antoniocorsano-boop/N12","commit_sha":G,"version":"G0"},"authority":{"authority_id":AID,"authority_sha256":AS},"candidate":{"base_repository":"antoniocorsano-boop/N12","pr_number":148,"head_repository":"fork/N12","head_sha":H},"operational_authority":{"commit_sha":O},"qualification_bundle_sha256":"9"*64,"replay":{},"invariants":{},"failure_codes":[] if qualified else ["X"],"authority_boundary":{},"cew_fem_01_required":True,"qualified":qualified}
def write_artifact(*,qualified=True,exit_code=0,context=CTX):
    d=Path(tempfile.mkdtemp()); rp=d/"qualification-receipt.json"; rp.write_bytes(json.dumps(receipt(qualified),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()+b"\n"); env=build_handoff_envelope(rp,context,ANCHOR,exit_code); (d/"handoff-envelope.json").write_text(json.dumps(env,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8"); return d,env

class HandoffHappyAndFailReceiptTests(unittest.TestCase):
    def test_pass_receipt_survives_handoff(self): d,_=write_artifact(); self.assertTrue(verify_handoff_directory(d,CTX,ANCHOR)["qualified"])
    def test_fail_receipt_survives_handoff(self): d,_=write_artifact(qualified=False,exit_code=1); self.assertFalse(verify_handoff_directory(d,CTX,ANCHOR)["qualified"])
    def test_exit_2_without_receipt_is_rejected(self):
        d=Path(tempfile.mkdtemp()); (d/"handoff-envelope.json").write_text("{}")
        with self.assertRaises(ControlPlaneError) as c: verify_handoff_directory(d,CTX,ANCHOR)
        self.assertEqual(c.exception.code,"RECEIPT_NOT_EMITTED")
class HandoffTamperTests(unittest.TestCase):
    def assert_code(self,code,fn):
        with self.assertRaises(ControlPlaneError) as c: fn()
        self.assertEqual(c.exception.code,code)
    def test_receipt_transport_byte_mutation_fails(self): d,_=write_artifact(); p=d/"qualification-receipt.json"; p.write_bytes(p.read_bytes().replace(b'"qualified":true',b'"qualified":false')); self.assert_code("HANDOFF_RECEIPT_DIGEST_MISMATCH",lambda:verify_handoff_directory(d,CTX,ANCHOR))
    def test_receipt_newline_mutation_fails(self): d,_=write_artifact(); p=d/"qualification-receipt.json"; p.write_bytes(p.read_bytes().rstrip(b"\n")); self.assert_code("HANDOFF_RECEIPT_DIGEST_MISMATCH",lambda:verify_handoff_directory(d,CTX,ANCHOR))
    def test_correct_canonical_but_wrong_transport_digest_fails(self):
        d,e=write_artifact(); e["receipt_transport_sha256"]="0"*64; (d/"handoff-envelope.json").write_text(json.dumps(e,separators=(",",":"),sort_keys=True)); self.assert_code("HANDOFF_RECEIPT_DIGEST_MISMATCH",lambda:verify_handoff_directory(d,CTX,ANCHOR))
    def test_wrong_run_id_fails(self): d,_=write_artifact(); self.assert_code("HANDOFF_RUN_ID_MISMATCH",lambda:verify_handoff_directory(d,replace(CTX,run_id=102),ANCHOR))
    def test_wrong_run_attempt_fails(self): d,_=write_artifact(); self.assert_code("HANDOFF_RUN_ID_MISMATCH",lambda:verify_handoff_directory(d,replace(CTX,run_attempt=3),ANCHOR))
    def test_incoherent_b_g_a_h_o_fails(self):
        for key,val in [("control_plane_base_sha","0"*40),("gate_core_commit_sha","0"*40),("authority_sha256","0"*64),("candidate_head_sha","0"*40),("operational_commit_sha","0"*40)]:
            d,e=write_artifact(); e[key]=val; (d/"handoff-envelope.json").write_text(json.dumps(e,separators=(",",":"),sort_keys=True));
            with self.subTest(key=key): self.assert_code("HANDOFF_ENVELOPE_INVALID",lambda d=d:verify_handoff_directory(d,CTX,ANCHOR))
    def test_run_identity_type_confusion_fails(self):
        for bad in (True,"101",0,-1):
            with self.subTest(bad=bad):
                with self.assertRaises(ControlPlaneError): HandoffContext(bad,2,B,148,"fork/N12",H)
class ArtifactShapeTests(unittest.TestCase):
    def assert_code(self,code,fn):
        with self.assertRaises(ControlPlaneError) as c: fn()
        self.assertEqual(c.exception.code,code)
    def test_missing_or_extra_artifact_file_fails(self):
        d,_=write_artifact(); (d/"qualification-receipt.json").unlink(); self.assert_code("RECEIPT_NOT_EMITTED",lambda:verify_handoff_directory(d,CTX,ANCHOR)); d,_=write_artifact(); (d/"handoff-envelope.json").unlink(); self.assert_code("HANDOFF_ENVELOPE_INVALID",lambda:verify_handoff_directory(d,CTX,ANCHOR)); d,_=write_artifact(); (d/"extra.txt").write_text("x"); self.assert_code("HANDOFF_ENVELOPE_INVALID",lambda:verify_handoff_directory(d,CTX,ANCHOR))
    def test_artifact_id_must_be_positive_integer_not_name(self):
        self.assertEqual(validate_artifact_id(42),42)
        for bad in (None,"artifact-name",0,-1,True):
            with self.subTest(bad=bad): self.assert_code("ARTIFACT_HANDOFF_FAILED",lambda bad=bad:validate_artifact_id(bad))
    def test_duplicate_json_keys_in_envelope_fail(self): d,_=write_artifact(); (d/"handoff-envelope.json").write_text('{"schema_id":"CEW_GATE_AUTHORITY_HANDOFF_ENVELOPE","schema_id":"X"}'); self.assert_code("HANDOFF_ENVELOPE_INVALID",lambda:verify_handoff_directory(d,CTX,ANCHOR))
    def test_duplicate_json_keys_in_receipt_fail(self):
        d=Path(tempfile.mkdtemp()); rp=d/"qualification-receipt.json"
        rp.write_text('{"schema_id":"CEW_QUALIFICATION_RECEIPT","schema_id":"X"}',encoding="utf-8")
        self.assert_code("HANDOFF_RECEIPT_DIGEST_MISMATCH",lambda:build_handoff_envelope(rp,CTX,ANCHOR,0))
if __name__=="__main__": unittest.main()
