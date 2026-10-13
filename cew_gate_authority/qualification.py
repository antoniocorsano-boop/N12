from __future__ import annotations

import csv
import hashlib
import io
import json
from typing import Any

from .authority import FrozenAuthority
from .candidate_reader import CandidateReader
from .replay import ReplayResult
from .types import AuthorityIdentity,CandidateIdentity,ControlPlaneIdentity,GateCoreIdentity,InvariantResult,OperationalIdentity,QualificationReceipt

ROOT="qualification/cew-contract-01/n12/"
Q=ROOT+"qualification.json"; MATRIX=ROOT+"conformance-matrix.csv"; INDEX=ROOT+"evidence-index.json"; MINIMALITY=ROOT+"structural-type-minimality.csv"; SUFFICIENCY=ROOT+"source-sufficiency.md"; REG=ROOT+"registration-uncertainty.json"; MODEL=ROOT+"model-generation.json"; MODEL_RECEIPT=ROOT+"model-generation-receipt.json"
EXPECTED_IDS=tuple(f"C01-T{i:02d}" for i in range(1,12)); EXPECTED_INV=tuple(f"I{i:02d}" for i in range(1,18))
BOUNDARY_KEYS={"solver_authorized","calculation_model_ready","synthetic_solver_result","solver_run","result_entity_created"}
Q_FIELDS={"schema_id","schema_version","canonical_snapshot_id","operational_commit","verification_status","authority_boundary","epistemic_guards","cew_fem_01_required","cew_fem_chain"}

class PayloadError(ValueError):
    def __init__(self,code:str): super().__init__(code); self.code=code

def _depth(value:Any)->int:
    if isinstance(value,dict): return 1+max((_depth(v) for v in value.values()),default=0)
    if isinstance(value,list): return 1+max((_depth(v) for v in value),default=0)
    return 0

def _json(reader:CandidateReader,path:str,max_depth:int,*,closed_fields:set[str]|None=None)->dict[str,Any]:
    try: text=reader.read_text(path)
    except ValueError as exc:
        if "UTF-8" in str(exc): raise PayloadError("CANDIDATE_UTF8_INVALID") from exc
        raise
    try: value=json.loads(text)
    except json.JSONDecodeError as exc: raise PayloadError("CANDIDATE_JSON_INVALID") from exc
    if _depth(value)>max_depth: raise PayloadError("CANDIDATE_JSON_DEPTH_EXCEEDED")
    if not isinstance(value,dict): raise PayloadError("CANDIDATE_JSON_INVALID")
    if closed_fields is not None and set(value)!=closed_fields: raise PayloadError("CANDIDATE_SCHEMA_UNEXPECTED_FIELD")
    return value

def parse_csv_limited(text:str,max_rows:int)->list[dict[str,str]]:
    rows=[]
    for row in csv.DictReader(io.StringIO(text)):
        rows.append(dict(row))
        if len(rows)>max_rows: raise ValueError("CANDIDATE_CSV_ROWS_EXCEEDED")
    return rows

def _csv(reader:CandidateReader,path:str,max_rows:int)->list[dict[str,str]]:
    try: text=reader.read_text(path)
    except ValueError as exc:
        if "UTF-8" in str(exc): raise PayloadError("CANDIDATE_UTF8_INVALID") from exc
        raise
    try: return parse_csv_limited(text,max_rows)
    except ValueError as exc:
        if str(exc)=="CANDIDATE_CSV_ROWS_EXCEEDED": raise PayloadError(str(exc)) from exc
        raise

def _canonical(value:Any)->str: return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def _bundle_digest(reader:CandidateReader,paths:tuple[str,...])->str:
    reader.verify_allowlisted_surface(paths); h=hashlib.sha256()
    for path in sorted(paths):
        data=reader.read_blob(path); h.update(path.encode()); h.update(b"\0"); h.update(hashlib.sha256(data).hexdigest().encode()); h.update(b"\n")
    return h.hexdigest()
def _false_exact(value:Any,keys:set[str])->bool: return isinstance(value,dict) and set(value)==keys and all(value[k] is False for k in keys)
def _result(ok:bool,code:str,failures:list[str])->InvariantResult:
    if ok: return InvariantResult.PASS
    failures.append(code); return InvariantResult.FAIL

def evaluate_qualification(reader:CandidateReader,authority:FrozenAuthority,replay:ReplayResult,control_plane:ControlPlaneIdentity,gate_core:GateCoreIdentity,candidate:CandidateIdentity,*,qualified_at:str)->QualificationReceipt:
    failures:list[str]=[]; inv={key:InvariantResult.NOT_APPLICABLE for key in EXPECTED_INV}
    try:
        digest=_bundle_digest(reader,authority.candidate_allowlist)
        q=_json(reader,Q,authority.limits.max_json_depth,closed_fields=Q_FIELDS)
        if q.get("schema_id")!=authority.qualification_schema_id or q.get("schema_version")!=authority.qualification_schema_version:
            raise PayloadError("CANDIDATE_QUALIFICATION_SCHEMA_UNSUPPORTED")
        reg=_json(reader,REG,authority.limits.max_json_depth); model=_json(reader,MODEL,authority.limits.max_json_depth); mr=_json(reader,MODEL_RECEIPT,authority.limits.max_json_depth); index=_json(reader,INDEX,authority.limits.max_json_depth)
        matrix=_csv(reader,MATRIX,authority.limits.max_csv_rows); _csv(reader,MINIMALITY,authority.limits.max_csv_rows)
        try: reader.read_text(SUFFICIENCY)
        except ValueError as exc:
            if "UTF-8" in str(exc): raise PayloadError("CANDIDATE_UTF8_INVALID") from exc
            raise
        for path in authority.candidate_allowlist:
            if path.endswith(".md"):
                try: reader.read_text(path)
                except ValueError as exc:
                    if "UTF-8" in str(exc): raise PayloadError("CANDIDATE_UTF8_INVALID") from exc
                    raise
    except PayloadError as exc:
        failures.append(exc.code); digest="0"*64
        return _receipt(authority,replay,control_plane,gate_core,candidate,qualified_at,digest,inv,failures)
    except ValueError:
        failures.append("CANDIDATE_SURFACE_INVALID"); digest="0"*64
        return _receipt(authority,replay,control_plane,gate_core,candidate,qualified_at,digest,inv,failures)

    inv["I01"]=_result(reader.head_sha==candidate.head_sha,"I01_CANDIDATE_HEAD_MISMATCH",failures)
    inv["I02"]=_result(gate_core.version=="G0" and bool(control_plane.base_commit_sha) and bool(authority.source_sha256),"I02_TRUSTED_INVOCATION_INVALID",failures)
    inv["I03"]=_result(q.get("operational_commit")==authority.operational_commit and model.get("builder",{}).get("source_commit")==authority.operational_commit and mr.get("source_commit")==authority.operational_commit,"I03_OPERATIONAL_AUTHORITY_MISMATCH",failures)
    model_inputs=model.get("inputs") if isinstance(model.get("inputs"),list) else []
    actual_paths=[str(item.get("path")) for item in model_inputs if isinstance(item,dict)]
    expected_paths=[p for p,_ in authority.inputs]
    inv["I04"]=_result(actual_paths==expected_paths and len(set(actual_paths))==6,"I04_INPUT_SET_MISMATCH",failures)
    actual_input_map={str(item.get("path")):str(item.get("sha256")) for item in model_inputs if isinstance(item,dict)}
    inv["I05"]=_result(actual_input_map==dict(authority.inputs),"I05_INPUT_DIGEST_MISMATCH",failures)
    b=model.get("builder") if isinstance(model.get("builder"),dict) else {}
    inv["I06"]=_result(b.get("path")==authority.builder.path and b.get("git_blob_sha")==authority.builder.git_blob_sha,"I06_BUILDER_IDENTITY_MISMATCH",failures)
    inv["I07"]=_result(q.get("canonical_snapshot_id")==authority.canonical_snapshot_id and model.get("canonical_snapshot_id")==authority.canonical_snapshot_id,"I07_SNAPSHOT_IDENTITY_MISMATCH",failures)
    inv["I08"]=_result(replay.passed is True,"I08_REPLAY_FAILED",failures)
    inv["I09"]=_result(replay.output_identity==authority.output.identity and replay.output_sha256==authority.output.sha256 and replay.output_size_bytes==authority.output.size_bytes and replay.generated_at==authority.output.generated_at,"I09_OUTPUT_INTEGRITY_MISMATCH",failures)
    mo=model.get("output") if isinstance(model.get("output"),dict) else {}; rv=mr.get("verification") if isinstance(mr.get("verification"),dict) else {}; mv=model.get("verification") if isinstance(model.get("verification"),dict) else {}
    coherent=(model.get("model_generation_id")==authority.model_generation_id==mr.get("model_generation_id") and mo.get("generation_id_inside_artifact")==authority.output.generation_id_inside_artifact==mr.get("generation_id_inside_artifact") and mo.get("identity")==mr.get("output_file")==authority.output.identity and mo.get("sha256")==mr.get("output_sha256")==authority.output.sha256 and mo.get("size_bytes")==mr.get("output_size_bytes")==authority.output.size_bytes and model.get("generated_at")==mr.get("generated_artifact_timestamp")==authority.output.generated_at and mr.get("input_sha256")==dict(authority.inputs) and mv.get("status")==rv.get("status")=="PASS")
    inv["I10"]=_result(coherent,"I10_MANIFEST_RECEIPT_INCOHERENT",failures)
    source_ok=(reg.get("source_repository")=="antoniocorsano-boop/N12" and reg.get("source_commit")==authority.operational_commit and reg.get("source_path")==authority.registration.source_path and reg.get("source_git_blob_sha")==authority.registration.source_git_blob_sha)
    inv["I11"]=_result(source_ok,"I11_REGISTRATION_SOURCE_MISMATCH",failures)
    inv["I12"]=_result(_canonical(reg.get("examples"))==_canonical(list(authority.registration.examples)),"I12_REGISTRATION_EXAMPLES_MISMATCH",failures)
    qguards=q.get("epistemic_guards"); rguards=reg.get("epistemic_guard")
    qkeys={"new_measurement_allowed","nd_promotion_allowed","derived_promotable_to_doc","unsourced_interval_allowed"}; rkeys={"residual_is_new_measurement","residual_promotable_to_DOC","residual_promotable_to_MIS","unsourced_plus_minus_interval_allowed"}
    inv["I13"]=_result(_false_exact(qguards,qkeys) and _false_exact(rguards,rkeys),"I13_EPISTEMIC_GUARD_VIOLATION",failures)
    matrix_ids=[r.get("test_id") for r in matrix]; matrix_ok=(tuple(matrix_ids)==EXPECTED_IDS and len(set(matrix_ids))==11 and all(r.get("status")=="PASS" and r.get("evidence_id")==r.get("test_id") for r in matrix))
    inv["I14"]=_result(matrix_ok,"I14_GATE_MATRIX_INVALID",failures)
    evidence=index.get("evidence") if isinstance(index.get("evidence"),dict) else {}
    expected_evidence=dict(authority.evidence_bindings)
    evidence_ok=(index.get("schema_id")=="CEW_EVIDENCE_INDEX" and index.get("schema_version")==1 and evidence==expected_evidence)
    if evidence_ok:
        for key in EXPECTED_IDS:
            path=expected_evidence[key]
            try:
                if not reader.read_text(path).strip(): evidence_ok=False; break
            except ValueError: evidence_ok=False; break
    inv["I15"]=_result(evidence_ok,"I15_EVIDENCE_INVALID",failures)
    boundary_ok=_false_exact(q.get("authority_boundary"),BOUNDARY_KEYS) and model.get("solver_authorized") is False and model.get("calculation_model_ready") is False and model.get("synthetic_solver_result") is False and mr.get("engineering_result") is False and mr.get("solver_run") is False and mr.get("result_entity_created") is False
    inv["I16"]=_result(boundary_ok,"I16_AUTHORITY_BOUNDARY_VIOLATION",failures)
    inv["I17"]=_result(q.get("cew_fem_01_required") is True and q.get("cew_fem_chain")=="ModelGeneration → SolverRun → Result → Verification → Receipt","I17_CEW_FEM_SEPARATION_VIOLATION",failures)
    if q.get("verification_status")!="PASS": failures.append("QUALIFICATION_VERIFICATION_NOT_PASS")
    return _receipt(authority,replay,control_plane,gate_core,candidate,qualified_at,digest,inv,failures)

def _receipt(authority,replay,control_plane,gate_core,candidate,qualified_at,digest,inv,failures):
    qualified=not failures and all(v is InvariantResult.PASS for v in inv.values())
    return QualificationReceipt(schema_id="CEW_QUALIFICATION_RECEIPT",schema_version=1,qualified_at=qualified_at,control_plane=control_plane,gate_core=gate_core,authority=AuthorityIdentity(authority.authority_id,authority.source_sha256),candidate=candidate,operational_authority=OperationalIdentity(authority.operational_commit),qualification_bundle_sha256=digest,replay={"output_identity":replay.output_identity,"output_sha256":replay.output_sha256,"output_size_bytes":replay.output_size_bytes,"historical_generated_at":replay.generated_at},invariants=inv,failure_codes=tuple(failures),authority_boundary=dict(authority.authority_boundary),cew_fem_01_required=True,qualified=qualified)
