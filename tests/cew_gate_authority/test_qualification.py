from __future__ import annotations

import csv
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from cew_gate_authority.authority import load_authority
from cew_gate_authority.candidate_reader import CandidateReader
from cew_gate_authority.qualification import evaluate_qualification
from cew_gate_authority.replay import ReplayResult
from cew_gate_authority.types import CandidateIdentity, ControlPlaneIdentity, GateCoreIdentity, InvariantResult

A0 = Path("governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json")
O = "d806dcca72779b5a186defe557a7a9b739575a90"
OUTPUT_SHA = "4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2"
OUTPUT_SIZE = 1068121
STAMP = "2026-08-26T09:54:00.472520+00:00"

CASE_NAMES = [
    "CASE_01_DOCUMENTED_PROPERTY.md", "CASE_02_NO_PROMOTION_OF_ND.md", "CASE_03_MIXED_EPISTEMIC_STATE.md",
    "CASE_04_STRUCTURAL_IDENTITY.md", "CASE_05_RELATIONSHIP_UNCERTAINTY.md", "CASE_06_REAL_CONFLICT.md",
    "CASE_07_NON_DESTRUCTIVE_UPDATE.md", "CASE_08_SNAPSHOT_SCENARIO.md", "CASE_09_END_TO_END_ASSURANCE.md",
    "CASE_10_VERIFICATION_RECEIPT.md", "CASE_11_REGISTRATION_UNCERTAINTY.md", "CASE_12_MODEL_GENERATION.md",
    "CASE_13_CORE_END_TO_END_ASSURANCE.md",
]


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout.decode().strip()


def valid_registration() -> dict:
    return {
        "schema_version": "1.0", "fixture_id": "N12_REGISTRATION_UNCERTAINTY_v1", "uncertainty_type": "REGISTRATION_UNCERTAINTY",
        "source_repository": "antoniocorsano-boop/N12", "source_commit": O,
        "source_path": "data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv", "source_git_blob_sha": "fa28cf034a03d98aaa8e8ac1deb1549ddef6d64a",
        "examples": [
            {"support_id":"1","property_ref":"PT support registration coordinate","unit":"px","observed":{"u":4096.63,"v":2823.61},"predicted":{"u":4100.03,"v":2822.89},"residual":{"du":3.40,"dv":-0.72,"scalar":3.47},"diagnostic_status":"PASS_DIAGNOSTIC","evidence_class":"DOC_METRIC_OR_AXIS","derived_bound":None},
            {"support_id":"19","property_ref":"PT support registration coordinate","unit":"px","observed":{"u":2458.56,"v":4200.73},"predicted":{"u":2462.23,"v":4224.46},"residual":{"du":3.67,"dv":23.73,"scalar":24.01},"diagnostic_status":"WATCH","evidence_class":"MIS_AFFINE_WATCH","derived_bound":None},
        ],
        "epistemic_guard": {"residual_is_new_measurement":False,"residual_promotable_to_DOC":False,"residual_promotable_to_MIS":False,"unsourced_plus_minus_interval_allowed":False},
    }


def valid_model(authority) -> dict:
    return {
        "schema_version":"1.0", "model_generation_id":authority.model_generation_id, "canonical_snapshot_id":authority.canonical_snapshot_id,
        "generation_profile":"CEW_CANONICAL_STRUCTURAL_GRAPH_v0",
        "builder":{"path":authority.builder.path,"source_commit":O,"git_blob_sha":authority.builder.git_blob_sha,"declared_builder":"CEW_STRUCTURAL_MODEL_BUILDER_v0"},
        "inputs":[{"path":p,"sha256":d} for p,d in authority.inputs],
        "output":{"identity":authority.output.identity,"generation_id_inside_artifact":authority.output.generation_id_inside_artifact,"sha256":authority.output.sha256,"size_bytes":authority.output.size_bytes},
        "generated_at":authority.output.generated_at,
        "verification":{"status":"PASS"},
        "solver_authorized":False,"calculation_model_ready":False,"synthetic_solver_result":False,
    }


def valid_model_receipt(authority) -> dict:
    return {
        "schema_version":"1.0","receipt_id":"N12-CEW-MG-001-RECEIPT","model_generation_id":authority.model_generation_id,
        "generation_id_inside_artifact":authority.output.generation_id_inside_artifact,"engineering_result":False,"solver_run":False,"result_entity_created":False,
        "source_repository":"antoniocorsano-boop/N12","source_commit":O,"builder_path":authority.builder.path,
        "output_file":authority.output.identity,"output_sha256":authority.output.sha256,"output_size_bytes":authority.output.size_bytes,
        "input_sha256":dict(authority.inputs),"verification":{"status":"PASS"},"generated_artifact_timestamp":authority.output.generated_at,
    }


def valid_payload(authority) -> dict[str, bytes]:
    evidence_paths = [f"qualification/cew-contract-01/n12/evidence/{name}" for name in CASE_NAMES]
    evidence_map = {f"C01-T{i:02d}": evidence_paths[i-1] for i in range(1,12)}
    matrix = io.StringIO(); writer = csv.writer(matrix, lineterminator="\n"); writer.writerow(["test_id","status","evidence_id"])
    for i in range(1,12): writer.writerow([f"C01-T{i:02d}","PASS",f"C01-T{i:02d}"])
    qualification = {
        "schema_id":"CEW_CONTRACT_01_QUALIFICATION","schema_version":1,"canonical_snapshot_id":authority.canonical_snapshot_id,"operational_commit":O,
        "verification_status":"PASS",
        "authority_boundary":{"solver_authorized":False,"calculation_model_ready":False,"synthetic_solver_result":False,"solver_run":False,"result_entity_created":False},
        "epistemic_guards":{"new_measurement_allowed":False,"nd_promotion_allowed":False,"derived_promotable_to_doc":False,"unsourced_interval_allowed":False},
        "cew_fem_01_required":True,"cew_fem_chain":"ModelGeneration → SolverRun → Result → Verification → Receipt",
    }
    payload = {
        "qualification/cew-contract-01/n12/qualification.json": json.dumps(qualification, ensure_ascii=False).encode(),
        "qualification/cew-contract-01/n12/conformance-matrix.csv": matrix.getvalue().encode(),
        "qualification/cew-contract-01/n12/evidence-index.json": json.dumps({"schema_id":"CEW_EVIDENCE_INDEX","schema_version":1,"evidence":evidence_map}).encode(),
        "qualification/cew-contract-01/n12/structural-type-minimality.csv": b"structural_type,status\nCEW_CORE,MINIMAL\n",
        "qualification/cew-contract-01/n12/source-sufficiency.md": b"# N12 Source Sufficiency\nPASS_WITH_WATCH\n",
        "qualification/cew-contract-01/n12/registration-uncertainty.json": json.dumps(valid_registration()).encode(),
        "qualification/cew-contract-01/n12/model-generation.json": json.dumps(valid_model(authority)).encode(),
        "qualification/cew-contract-01/n12/model-generation-receipt.json": json.dumps(valid_model_receipt(authority)).encode(),
    }
    for path in evidence_paths: payload[path] = f"# {Path(path).stem}\nEvidence preserved from CEW audit trail.\n".encode()
    return payload


def write_candidate(payload: dict[str, bytes]) -> tuple[Path, str]:
    repo = Path(tempfile.mkdtemp(prefix="cew-qualification-")); run_git(repo.parent,"init",str(repo)); run_git(repo,"config","user.email","cew@example.invalid"); run_git(repo,"config","user.name","CEW Tests")
    for rel,data in payload.items():
        path=repo/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    run_git(repo,"add","qualification"); run_git(repo,"commit","-m","candidate")
    return repo, run_git(repo,"rev-parse","HEAD")


def replay(*, passed=True, sha=OUTPUT_SHA, size=OUTPUT_SIZE, stamp=STAMP, codes=()):
    return ReplayResult(passed=passed,failure_codes=tuple(codes),output_identity="N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json",output_sha256=sha,output_size_bytes=size,generated_at=stamp)


class QualificationEngineTests(unittest.TestCase):
    def setUp(self):
        self.authority=load_authority(A0); self.b=ControlPlaneIdentity("a"*40); self.g=GateCoreIdentity("antoniocorsano-boop/N12","b"*40,"G0")

    def evaluate(self, payload=None, *, replay_result=None, candidate_sha_override=None):
        repo,h=write_candidate(payload or valid_payload(self.authority)); candidate=CandidateIdentity("antoniocorsano-boop/N12",148,"antoniocorsano-boop/N12",candidate_sha_override or h)
        reader=CandidateReader(repo/".git",h,self.authority.limits,allowlist=self.authority.candidate_allowlist)
        return evaluate_qualification(reader,self.authority,replay_result or replay(),self.b,self.g,candidate,qualified_at="2026-10-13T00:00:00+00:00")

    def mutate_json(self, path, fn):
        payload=valid_payload(self.authority); obj=json.loads(payload[path]); fn(obj); payload[path]=json.dumps(obj,ensure_ascii=False).encode(); return payload

    def assert_failure(self, receipt, invariant, code):
        self.assertFalse(receipt.qualified); self.assertEqual(receipt.invariants[invariant],InvariantResult.FAIL); self.assertIn(code,receipt.failure_codes)

    def test_happy_path_passes_all_i01_to_i17(self):
        receipt=self.evaluate(); self.assertTrue(receipt.qualified); self.assertTrue(all(v is InvariantResult.PASS for v in receipt.invariants.values())); self.assertEqual(receipt.failure_codes,())

    def test_i01_exact_candidate_head(self): self.assert_failure(self.evaluate(candidate_sha_override="f"*40),"I01","I01_CANDIDATE_HEAD_MISMATCH")
    def test_i02_trusted_invocation_requires_g0_identity(self):
        repo,h=write_candidate(valid_payload(self.authority)); r=CandidateReader(repo/".git",h,self.authority.limits,allowlist=self.authority.candidate_allowlist); c=CandidateIdentity("antoniocorsano-boop/N12",148,"antoniocorsano-boop/N12",h)
        receipt=evaluate_qualification(r,self.authority,replay(),self.b,GateCoreIdentity("antoniocorsano-boop/N12","b"*40,"G1"),c,qualified_at="2026-10-13T00:00:00+00:00"); self.assert_failure(receipt,"I02","I02_TRUSTED_INVOCATION_INVALID")
    def test_i03_operational_authority(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/qualification.json",lambda o:o.update(operational_commit="0"*40))),"I03","I03_OPERATIONAL_AUTHORITY_MISMATCH")
    def test_i04_exact_input_set(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/model-generation.json",lambda o:o["inputs"].pop())),"I04","I04_INPUT_SET_MISMATCH")
    def test_i05_input_byte_identity_claims(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/model-generation.json",lambda o:o["inputs"][0].update(sha256="0"*64))),"I05","I05_INPUT_DIGEST_MISMATCH")
    def test_i06_builder_identity(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/model-generation.json",lambda o:o["builder"].update(git_blob_sha="0"*40))),"I06","I06_BUILDER_IDENTITY_MISMATCH")
    def test_i07_snapshot_identity(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/qualification.json",lambda o:o.update(canonical_snapshot_id="wrong"))),"I07","I07_SNAPSHOT_IDENTITY_MISMATCH")
    def test_i08_durable_replay(self): self.assert_failure(self.evaluate(replay_result=replay(passed=False,codes=("REPLAY_BUILD_FAILED",))),"I08","I08_REPLAY_FAILED")
    def test_i09_output_integrity(self): self.assert_failure(self.evaluate(replay_result=replay(sha="0"*64)),"I09","I09_OUTPUT_INTEGRITY_MISMATCH")
    def test_i10_manifest_receipt_coherence(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/model-generation-receipt.json",lambda o:o.update(output_sha256="0"*64))),"I10","I10_MANIFEST_RECEIPT_INCOHERENT")
    def test_i11_registration_source_provenance(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/registration-uncertainty.json",lambda o:o.update(source_git_blob_sha="0"*40))),"I11","I11_REGISTRATION_SOURCE_MISMATCH")
    def test_i12_exact_registration_examples(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/registration-uncertainty.json",lambda o:o["examples"][1]["residual"].update(scalar=24.02))),"I12","I12_REGISTRATION_EXAMPLES_MISMATCH")
    def test_i13_epistemic_guards(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/registration-uncertainty.json",lambda o:o["epistemic_guard"].update(residual_promotable_to_DOC=True))),"I13","I13_EPISTEMIC_GUARD_VIOLATION")
    def test_i14_gate_matrix_exact_unique_pass_set(self):
        payload=valid_payload(self.authority); payload["qualification/cew-contract-01/n12/conformance-matrix.csv"]=payload["qualification/cew-contract-01/n12/conformance-matrix.csv"].replace(b"C01-T11,PASS,C01-T11",b"C01-T10,PASS,C01-T11"); self.assert_failure(self.evaluate(payload),"I14","I14_GATE_MATRIX_INVALID")
    def test_i15_every_pass_has_existing_indexed_evidence(self):
        payload=valid_payload(self.authority); index=json.loads(payload["qualification/cew-contract-01/n12/evidence-index.json"]); index["evidence"]["C01-T01"]="qualification/cew-contract-01/n12/evidence/MISSING.md"; payload["qualification/cew-contract-01/n12/evidence-index.json"]=json.dumps(index).encode(); self.assert_failure(self.evaluate(payload),"I15","I15_EVIDENCE_INVALID")
    def test_i16_authority_boundary(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/qualification.json",lambda o:o["authority_boundary"].update(solver_authorized=True))),"I16","I16_AUTHORITY_BOUNDARY_VIOLATION")
    def test_i17_cew_fem_separation(self): self.assert_failure(self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/qualification.json",lambda o:o.update(cew_fem_01_required=False))),"I17","I17_CEW_FEM_SEPARATION_VIOLATION")

    def test_unexpected_closed_schema_field_fails_before_qualification(self):
        receipt=self.evaluate(self.mutate_json("qualification/cew-contract-01/n12/qualification.json",lambda o:o.update(unexpected="x"))); self.assertFalse(receipt.qualified); self.assertIn("CANDIDATE_SCHEMA_UNEXPECTED_FIELD",receipt.failure_codes)
    def test_json_depth_over_64_fails_before_qualification(self):
        payload=valid_payload(self.authority); deep={}; cursor=deep
        for _ in range(65): cursor["x"]={}; cursor=cursor["x"]
        q=json.loads(payload["qualification/cew-contract-01/n12/qualification.json"]); q["epistemic_guards"]=deep; payload["qualification/cew-contract-01/n12/qualification.json"]=json.dumps(q).encode(); receipt=self.evaluate(payload); self.assertFalse(receipt.qualified); self.assertIn("CANDIDATE_JSON_DEPTH_EXCEEDED",receipt.failure_codes)
    def test_malformed_utf8_text_fails_before_qualification(self):
        payload=valid_payload(self.authority); payload["qualification/cew-contract-01/n12/evidence/CASE_01_DOCUMENTED_PROPERTY.md"]=b"\xff\xfe"; receipt=self.evaluate(payload); self.assertFalse(receipt.qualified); self.assertIn("CANDIDATE_UTF8_INVALID",receipt.failure_codes)


if __name__ == "__main__": unittest.main()
