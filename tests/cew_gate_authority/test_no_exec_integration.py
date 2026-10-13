from __future__ import annotations

import csv, io, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

from cew_gate_authority.authority import load_authority
from cew_gate_authority.candidate_reader import CandidateReader
from cew_gate_authority.qualification import evaluate_qualification
from cew_gate_authority.operational import materialize_operational_authority
from cew_gate_authority.replay import run_model_generation_replay
from cew_gate_authority.types import CandidateIdentity,ControlPlaneIdentity,GateCoreIdentity

A0=Path("governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json"); O="d806dcca72779b5a186defe557a7a9b739575a90"
CASE_NAMES=["CASE_01_DOCUMENTED_PROPERTY.md","CASE_02_NO_PROMOTION_OF_ND.md","CASE_03_MIXED_EPISTEMIC_STATE.md","CASE_04_STRUCTURAL_IDENTITY.md","CASE_05_RELATIONSHIP_UNCERTAINTY.md","CASE_06_REAL_CONFLICT.md","CASE_07_NON_DESTRUCTIVE_UPDATE.md","CASE_08_SNAPSHOT_SCENARIO.md","CASE_09_END_TO_END_ASSURANCE.md","CASE_10_VERIFICATION_RECEIPT.md","CASE_11_REGISTRATION_UNCERTAINTY.md","CASE_12_MODEL_GENERATION.md","CASE_13_CORE_END_TO_END_ASSURANCE.md"]

def git(repo,*args): return subprocess.run(["git","-C",str(repo),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout.decode().strip()
def payload(a):
    ev=[f"qualification/cew-contract-01/n12/evidence/{n}" for n in CASE_NAMES]; m=io.StringIO(); w=csv.writer(m,lineterminator="\n"); w.writerow(["test_id","status","evidence_id"]); [w.writerow([f"C01-T{i:02d}","PASS",f"C01-T{i:02d}"]) for i in range(1,12)]
    q={"schema_id":"CEW_CONTRACT_01_QUALIFICATION","schema_version":1,"canonical_snapshot_id":a.canonical_snapshot_id,"operational_commit":O,"verification_status":"PASS","authority_boundary":{"solver_authorized":False,"calculation_model_ready":False,"synthetic_solver_result":False,"solver_run":False,"result_entity_created":False},"epistemic_guards":{"new_measurement_allowed":False,"nd_promotion_allowed":False,"derived_promotable_to_doc":False,"unsourced_interval_allowed":False},"cew_fem_01_required":True,"cew_fem_chain":"ModelGeneration → SolverRun → Result → Verification → Receipt"}
    reg={"schema_version":"1.0","fixture_id":"N12_REGISTRATION_UNCERTAINTY_v1","uncertainty_type":"REGISTRATION_UNCERTAINTY","source_repository":"antoniocorsano-boop/N12","source_commit":O,"source_path":a.registration.source_path,"source_git_blob_sha":a.registration.source_git_blob_sha,"examples":list(a.registration.examples),"epistemic_guard":{"residual_is_new_measurement":False,"residual_promotable_to_DOC":False,"residual_promotable_to_MIS":False,"unsourced_plus_minus_interval_allowed":False}}
    model={"schema_version":"1.0","model_generation_id":a.model_generation_id,"canonical_snapshot_id":a.canonical_snapshot_id,"generation_profile":"CEW_CANONICAL_STRUCTURAL_GRAPH_v0","builder":{"path":a.builder.path,"source_commit":O,"git_blob_sha":a.builder.git_blob_sha,"declared_builder":"CEW_STRUCTURAL_MODEL_BUILDER_v0"},"inputs":[{"path":p,"sha256":d} for p,d in a.inputs],"output":{"identity":a.output.identity,"generation_id_inside_artifact":a.output.generation_id_inside_artifact,"sha256":a.output.sha256,"size_bytes":a.output.size_bytes},"generated_at":a.output.generated_at,"verification":{"status":"PASS"},"solver_authorized":False,"calculation_model_ready":False,"synthetic_solver_result":False}
    mr={"schema_version":"1.0","receipt_id":"N12-CEW-MG-001-RECEIPT","model_generation_id":a.model_generation_id,"generation_id_inside_artifact":a.output.generation_id_inside_artifact,"engineering_result":False,"solver_run":False,"result_entity_created":False,"source_repository":"antoniocorsano-boop/N12","source_commit":O,"builder_path":a.builder.path,"output_file":a.output.identity,"output_sha256":a.output.sha256,"output_size_bytes":a.output.size_bytes,"input_sha256":dict(a.inputs),"verification":{"status":"PASS"},"generated_artifact_timestamp":a.output.generated_at}
    out={"qualification/cew-contract-01/n12/qualification.json":json.dumps(q).encode(),"qualification/cew-contract-01/n12/conformance-matrix.csv":m.getvalue().encode(),"qualification/cew-contract-01/n12/evidence-index.json":json.dumps({"schema_id":"CEW_EVIDENCE_INDEX","schema_version":1,"evidence":{f"C01-T{i:02d}":ev[i-1] for i in range(1,12)}}).encode(),"qualification/cew-contract-01/n12/structural-type-minimality.csv":b"structural_type,status\nCEW_CORE,MINIMAL\n","qualification/cew-contract-01/n12/source-sufficiency.md":b"# Source Sufficiency\nPASS_WITH_WATCH\n","qualification/cew-contract-01/n12/registration-uncertainty.json":json.dumps(reg).encode(),"qualification/cew-contract-01/n12/model-generation.json":json.dumps(model).encode(),"qualification/cew-contract-01/n12/model-generation-receipt.json":json.dumps(mr).encode()}
    out.update({p:f"# {Path(p).stem}\nEvidence.\n".encode() for p in ev}); return out

def candidate_repo(a,marker):
    repo=Path(tempfile.mkdtemp(prefix="cew-no-exec-")); git(repo.parent,"init",str(repo)); git(repo,"config","user.email","cew@example.invalid"); git(repo,"config","user.name","CEW Tests")
    for rel,data in payload(a).items(): p=repo/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
    evil=f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"; (repo/"evil.py").write_text(evil); (repo/"evil.sh").write_text(f"#!/bin/sh\necho executed > {marker}\n"); os.chmod(repo/"evil.sh",0o755)
    (repo/"package.json").write_text(json.dumps({"scripts":{"preinstall":f"echo executed > {marker}"}})); (repo/".github/actions/evil").mkdir(parents=True); (repo/".github/actions/evil/action.yml").write_text(f"runs:\n  using: composite\n  steps:\n    - shell: bash\n      run: echo executed > {marker}\n"); (repo/".github/workflows").mkdir(parents=True,exist_ok=True); (repo/".github/workflows/evil.yml").write_text("name: evil\non: push\njobs: {}\n")
    git(repo,"add","."); git(repo,"commit","-m","candidate with tripwires"); h1=git(repo,"rev-parse","HEAD")
    hook=repo/".git/hooks/post-checkout"; hook.write_text(f"#!/bin/sh\necho hook > {marker}\n"); os.chmod(hook,0o755)
    return repo,h1

class NoExecIntegrationTests(unittest.TestCase):
    def test_candidate_executables_hooks_actions_packages_and_workflow_never_run(self):
        a=load_authority(A0)
        with tempfile.TemporaryDirectory() as td:
            marker=Path(td)/"TRIPWIRE"; repo,h1=candidate_repo(a,marker); reader=CandidateReader(repo/".git",h1,a.limits,allowlist=a.candidate_allowlist)
            # Move the branch after binding H1; the reader/receipt must remain on H1.
            (repo/"later.txt").write_text("H2"); git(repo,"add","later.txt"); git(repo,"commit","-m","move head"); self.assertNotEqual(h1,git(repo,"rev-parse","HEAD"))
            materialized=materialize_operational_authority(Path("."),a,Path(td)/"operational"); replay=run_model_generation_replay(materialized,a,Path(td)/a.output.identity)
            c=CandidateIdentity("antoniocorsano-boop/N12",148,"antoniocorsano-boop/N12",h1); r=evaluate_qualification(reader,a,replay,ControlPlaneIdentity("a"*40),GateCoreIdentity("antoniocorsano-boop/N12","b"*40,"G0"),c,qualified_at="2026-10-13T00:00:00+00:00")
            self.assertTrue(r.qualified,r.failure_codes); self.assertEqual(r.candidate.head_sha,h1); self.assertFalse(marker.exists())

    def test_cli_writes_canonical_receipt_and_exits_zero_for_current_dispatch_head(self):
        a=load_authority(A0)
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); marker=td/"TRIPWIRE"; repo,h=candidate_repo(a,marker); metadata={"number":148,"base":{"sha":"a"*40,"repo":{"full_name":"antoniocorsano-boop/N12"}},"head":{"sha":h,"repo":{"full_name":"antoniocorsano-boop/N12"}}}; meta=td/"pr.json"; meta.write_text(json.dumps(metadata)); out=td/"receipt.json"
            proc=subprocess.run([sys.executable,"-m","cew_gate_authority.cli","qualify","--candidate-git-dir",str(repo/".git"),"--operational-repo",".","--authority",str(A0),"--pr-metadata",str(meta),"--requested-sha",h,"--base-commit","a"*40,"--gate-core-commit","b"*40,"--qualified-at","2026-10-13T00:00:00+00:00","--output",str(out)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            self.assertEqual(proc.returncode,0,proc.stderr.decode()); data=json.loads(out.read_text()); self.assertTrue(data["qualified"]); self.assertEqual(data["candidate"]["head_sha"],h); self.assertFalse(marker.exists())

if __name__=="__main__": unittest.main()
