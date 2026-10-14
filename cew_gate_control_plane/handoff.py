from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from .contracts import ControlPlaneError, load_strict_json_bytes
from .trust_anchor import TrustAnchor

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_EXPECTED_FILES = {"qualification-receipt.json", "handoff-envelope.json"}
_ENVELOPE_KEYS = {"schema_id","schema_version","run_id","run_attempt","control_plane_base_sha","gate_core_commit_sha","gate_core_source_bundle_sha256","authority_id","authority_sha256","candidate_pr_number","candidate_head_repository","candidate_head_sha","operational_commit_sha","qualification_exit_code","receipt_canonical_sha256","receipt_transport_sha256"}

@dataclass(frozen=True)
class HandoffContext:
    run_id:int; run_attempt:int; control_plane_base_sha:str; candidate_pr_number:int; candidate_head_repository:str; candidate_head_sha:str
    def __post_init__(self)->None:
        for value in (self.run_id,self.run_attempt,self.candidate_pr_number):
            if not isinstance(value,int) or isinstance(value,bool) or value<1: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")
        if _SHA40.fullmatch(self.control_plane_base_sha) is None or _SHA40.fullmatch(self.candidate_head_sha) is None: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")
        if not isinstance(self.candidate_head_repository,str) or "/" not in self.candidate_head_repository: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")

def _strict_receipt(data:bytes)->dict[str,object]: return load_strict_json_bytes(data,label="HANDOFF_RECEIPT_DIGEST_MISMATCH")
def canonical_json_sha256(data:bytes)->str:
    obj=_strict_receipt(data); canonical=json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8"); return hashlib.sha256(canonical).hexdigest()
def transport_sha256(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def validate_artifact_id(value:object)->int:
    if not isinstance(value,int) or isinstance(value,bool) or value<1: raise ControlPlaneError("ARTIFACT_HANDOFF_FAILED")
    return value

def build_handoff_envelope(receipt_path:Path,context:HandoffContext,anchor:TrustAnchor,qualification_exit_code:int)->dict[str,object]:
    if not isinstance(qualification_exit_code,int) or isinstance(qualification_exit_code,bool) or qualification_exit_code not in {0,1,2}: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")
    try: data=Path(receipt_path).read_bytes()
    except OSError as exc: raise ControlPlaneError("RECEIPT_NOT_EMITTED") from exc
    _strict_receipt(data)
    return {"schema_id":"CEW_GATE_AUTHORITY_HANDOFF_ENVELOPE","schema_version":1,"run_id":context.run_id,"run_attempt":context.run_attempt,"control_plane_base_sha":context.control_plane_base_sha,"gate_core_commit_sha":anchor.g0_commit_sha,"gate_core_source_bundle_sha256":anchor.g0_source_bundle_sha256,"authority_id":anchor.authority_id,"authority_sha256":anchor.a0_sha256,"candidate_pr_number":context.candidate_pr_number,"candidate_head_repository":context.candidate_head_repository,"candidate_head_sha":context.candidate_head_sha,"operational_commit_sha":anchor.operational_commit_sha,"qualification_exit_code":qualification_exit_code,"receipt_canonical_sha256":canonical_json_sha256(data),"receipt_transport_sha256":transport_sha256(data)}

def _require_receipt_binding(receipt:dict[str,object],context:HandoffContext,anchor:TrustAnchor)->None:
    try:
        cp=receipt["control_plane"]; gate=receipt["gate_core"]; auth=receipt["authority"]; candidate=receipt["candidate"]; op=receipt["operational_authority"]
        if not all(isinstance(x,dict) for x in (cp,gate,auth,candidate,op)): raise KeyError
        valid=(cp.get("base_commit_sha")==context.control_plane_base_sha and gate.get("commit_sha")==anchor.g0_commit_sha and auth.get("authority_id")==anchor.authority_id and auth.get("authority_sha256")==anchor.a0_sha256 and candidate.get("pr_number")==context.candidate_pr_number and candidate.get("head_repository")==context.candidate_head_repository and candidate.get("head_sha")==context.candidate_head_sha and op.get("commit_sha")==anchor.operational_commit_sha)
    except (KeyError,TypeError): valid=False
    if not valid: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")

def verify_handoff_directory(directory:Path,envelope_context:HandoffContext,anchor:TrustAnchor)->dict[str,object]:
    directory=Path(directory); receipt_path=directory/"qualification-receipt.json"; envelope_path=directory/"handoff-envelope.json"
    if not receipt_path.is_file(): raise ControlPlaneError("RECEIPT_NOT_EMITTED")
    if not envelope_path.is_file(): raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")
    try: names={p.name for p in directory.iterdir() if p.is_file()}
    except OSError as exc: raise ControlPlaneError("ARTIFACT_HANDOFF_FAILED") from exc
    if names!=_EXPECTED_FILES: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")
    try: envelope=load_strict_json_bytes(envelope_path.read_bytes(),label="HANDOFF_ENVELOPE_INVALID")
    except OSError as exc: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID") from exc
    if set(envelope)!=_ENVELOPE_KEYS or envelope.get("schema_id")!="CEW_GATE_AUTHORITY_HANDOFF_ENVELOPE" or envelope.get("schema_version")!=1: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")
    if envelope.get("run_id")!=envelope_context.run_id or envelope.get("run_attempt")!=envelope_context.run_attempt: raise ControlPlaneError("HANDOFF_RUN_ID_MISMATCH")
    trusted={"control_plane_base_sha":envelope_context.control_plane_base_sha,"gate_core_commit_sha":anchor.g0_commit_sha,"gate_core_source_bundle_sha256":anchor.g0_source_bundle_sha256,"authority_id":anchor.authority_id,"authority_sha256":anchor.a0_sha256,"candidate_pr_number":envelope_context.candidate_pr_number,"candidate_head_repository":envelope_context.candidate_head_repository,"candidate_head_sha":envelope_context.candidate_head_sha,"operational_commit_sha":anchor.operational_commit_sha}
    if any(envelope.get(k)!=v for k,v in trusted.items()): raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")
    qec=envelope.get("qualification_exit_code")
    if not isinstance(qec,int) or isinstance(qec,bool) or qec not in {0,1,2}: raise ControlPlaneError("HANDOFF_ENVELOPE_INVALID")
    data=receipt_path.read_bytes()
    if envelope.get("receipt_transport_sha256")!=transport_sha256(data): raise ControlPlaneError("HANDOFF_RECEIPT_DIGEST_MISMATCH")
    if envelope.get("receipt_canonical_sha256")!=canonical_json_sha256(data): raise ControlPlaneError("HANDOFF_RECEIPT_DIGEST_MISMATCH")
    receipt=_strict_receipt(data); _require_receipt_binding(receipt,envelope_context,anchor); return receipt
