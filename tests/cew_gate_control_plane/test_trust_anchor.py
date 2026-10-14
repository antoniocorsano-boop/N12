import hashlib
import json
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from cew_gate_control_plane.contracts import ControlPlaneError
from cew_gate_control_plane.trust_anchor import TrustAnchor, load_and_verify_promotion_record, verify_materialized_gate, verify_operational_commit_available

CANON_G="1f32a24f456e7db18c994096e4c8f5067222a592"; CANON_BUNDLE="b56a98461373f59bc54ad3bd88d3047cff45a7f840b862248a99cd33ed3fe766"; CANON_MANIFEST="318a38199e5d7643e654442b9d92cbf41c94dd7f"; CANON_A0_BLOB="d6f71146b5b833650f1943021d956e1a2d742563"; CANON_A0_SHA="88ab731c986cef0af474bf567a9bb19a12a43dcdbef2de6cb211107b17f92dbb"; CANON_O="d806dcca72779b5a186defe557a7a9b739575a90"

def canonical_record():
    return {"schema_id":"CEW_GATE_AUTHORITY_PROMOTION_RECORD","schema_version":1,"promotion_id":"CEW-GATE-AUTHORITY-01-G0-A0-2026-10-14","bootstrap_mode":"HUMAN_PROMOTION","decision":"PROMOTED","decision_recorded_at":"2026-10-14T01:39:00Z","decision_authority":"HUMAN_REPOSITORY_OWNER","repository":"antoniocorsano-boop/N12","pull_request":148,"promoted_gate_core":{"version":"G0","exact_reviewed_commit_sha":CANON_G,"source_bundle_sha256":CANON_BUNDLE,"manifest_git_blob_sha":CANON_MANIFEST},"promoted_authority":{"authority_id":"N12_CEW_CONTRACT_01_A0","git_blob_sha":CANON_A0_BLOB,"sha256":CANON_A0_SHA,"operational_commit":CANON_O},"assurance_evidence":{},"authority_boundary":{"solver_authorized":False,"calculation_model_ready":False,"synthetic_solver_result":False,"solver_run":False,"result_entity_created":False},"cew_fem_01_required":True,"residual_controls":{},"promotion_scope":"scope"}

def write_record(data):
    p=Path(tempfile.mkdtemp())/"record.json"; p.write_text(json.dumps(data),encoding="utf-8"); return p

def git(cwd,*args): return subprocess.run(["git",*args],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout.strip()

def gate_repo():
    root=Path(tempfile.mkdtemp(prefix="task9-gate-")); repo=root/"repo"; repo.mkdir(); git(repo,"init"); git(repo,"config","user.email","cew@example.invalid"); git(repo,"config","user.name","CEW")
    a0=b'{"schema":"a0"}\n'; ap=repo/"governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json"; ap.parent.mkdir(parents=True); ap.write_bytes(a0)
    bundle="1"*64; mp=repo/"governance/cew-gate-authority/gate-core/G0_MANIFEST.json"; mp.parent.mkdir(parents=True); mp.write_text(json.dumps({"source_bundle_sha256":bundle}))
    git(repo,"add","."); git(repo,"commit","-m","g0"); head=git(repo,"rev-parse","HEAD"); mb=git(repo,"rev-parse",f"{head}:governance/cew-gate-authority/gate-core/G0_MANIFEST.json"); ab=git(repo,"rev-parse",f"{head}:governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json")
    return repo,TrustAnchor(head,bundle,mb,"N12_CEW_CONTRACT_01_A0",ab,hashlib.sha256(a0).hexdigest(),head)

class PromotionRecordTests(unittest.TestCase):
    def assert_invalid(self,path):
        with self.assertRaises(ControlPlaneError) as ctx: load_and_verify_promotion_record(path)
        self.assertEqual(ctx.exception.code,"PROMOTION_RECORD_INVALID")
    def test_valid_record_returns_canonical_anchor(self):
        a=load_and_verify_promotion_record(write_record(canonical_record())); self.assertEqual(a.g0_commit_sha,CANON_G); self.assertEqual(a.operational_commit_sha,CANON_O)
    def test_rejects_missing_record(self): self.assert_invalid(Path(tempfile.mkdtemp())/"missing.json")
    def test_rejects_duplicate_json_key(self):
        p=Path(tempfile.mkdtemp())/"r.json"; p.write_text('{"schema_id":"CEW_GATE_AUTHORITY_PROMOTION_RECORD","schema_id":"x"}'); self.assert_invalid(p)
    def test_rejects_wrong_schema_version_decision_or_repository(self):
        for key,val in (("schema_id","x"),("schema_version",2),("decision","CANDIDATE"),("repository","other/repo")):
            d=canonical_record(); d[key]=val
            with self.subTest(key=key): self.assert_invalid(write_record(d))
    def test_rejects_any_true_authority_flag(self):
        for key in canonical_record()["authority_boundary"]:
            d=canonical_record(); d["authority_boundary"][key]=True
            with self.subTest(key=key): self.assert_invalid(write_record(d))
    def test_rejects_false_cew_fem_required(self):
        d=canonical_record(); d["cew_fem_01_required"]=False; self.assert_invalid(write_record(d))
    def test_rejects_contradictory_g_a_o_identity(self):
        variants=[]
        for field in ("exact_reviewed_commit_sha","source_bundle_sha256","manifest_git_blob_sha"):
            d=canonical_record(); d["promoted_gate_core"][field]="0"*(64 if "256" in field else 40); variants.append(d)
        for field in ("authority_id","git_blob_sha","sha256","operational_commit"):
            d=canonical_record(); d["promoted_authority"][field]="X" if field=="authority_id" else "0"*(64 if field=="sha256" else 40); variants.append(d)
        for d in variants: self.assert_invalid(write_record(d))

class MaterializedGateTests(unittest.TestCase):
    def assert_code(self,code,fn):
        with self.assertRaises(ControlPlaneError) as ctx: fn()
        self.assertEqual(ctx.exception.code,code)
    def test_valid_materialized_gate(self): repo,a=gate_repo(); verify_materialized_gate(repo/".git",a)
    def test_rejects_wrong_g0_commit(self): repo,a=gate_repo(); self.assert_code("G0_IDENTITY_MISMATCH",lambda:verify_materialized_gate(repo/".git",replace(a,g0_commit_sha="f"*40)))
    def test_rejects_wrong_g0_manifest_blob(self): repo,a=gate_repo(); self.assert_code("G0_IDENTITY_MISMATCH",lambda:verify_materialized_gate(repo/".git",replace(a,g0_manifest_blob_sha="f"*40)))
    def test_rejects_wrong_source_bundle_digest(self): repo,a=gate_repo(); self.assert_code("G0_IDENTITY_MISMATCH",lambda:verify_materialized_gate(repo/".git",replace(a,g0_source_bundle_sha256="f"*64)))
    def test_rejects_wrong_a0_blob(self): repo,a=gate_repo(); self.assert_code("A0_IDENTITY_MISMATCH",lambda:verify_materialized_gate(repo/".git",replace(a,a0_blob_sha="f"*40)))
    def test_rejects_wrong_a0_sha256(self): repo,a=gate_repo(); self.assert_code("A0_IDENTITY_MISMATCH",lambda:verify_materialized_gate(repo/".git",replace(a,a0_sha256="f"*64)))
    def test_operational_commit_availability(self):
        repo,a=gate_repo(); verify_operational_commit_available(repo/".git",a); self.assert_code("OPERATIONAL_AUTHORITY_FETCH_FAILED",lambda:verify_operational_commit_available(repo/".git",replace(a,operational_commit_sha="f"*40)))

if __name__=="__main__": unittest.main()
