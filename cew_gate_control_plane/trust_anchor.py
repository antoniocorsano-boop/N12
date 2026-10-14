from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .contracts import ControlPlaneError, load_strict_json_bytes

CANON_G0_COMMIT = "1f32a24f456e7db18c994096e4c8f5067222a592"
CANON_G0_BUNDLE = "b56a98461373f59bc54ad3bd88d3047cff45a7f840b862248a99cd33ed3fe766"
CANON_G0_MANIFEST_BLOB = "318a38199e5d7643e654442b9d92cbf41c94dd7f"
CANON_A0_ID = "N12_CEW_CONTRACT_01_A0"
CANON_A0_BLOB = "d6f71146b5b833650f1943021d956e1a2d742563"
CANON_A0_SHA256 = "88ab731c986cef0af474bf567a9bb19a12a43dcdbef2de6cb211107b17f92dbb"
CANON_O = "d806dcca72779b5a186defe557a7a9b739575a90"
REPOSITORY = "antoniocorsano-boop/N12"
MANIFEST_PATH = "governance/cew-gate-authority/gate-core/G0_MANIFEST.json"
A0_PATH = "governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json"
_BOUNDARY_KEYS = {"solver_authorized","calculation_model_ready","synthetic_solver_result","solver_run","result_entity_created"}

@dataclass(frozen=True)
class TrustAnchor:
    g0_commit_sha: str
    g0_source_bundle_sha256: str
    g0_manifest_blob_sha: str
    authority_id: str
    a0_blob_sha: str
    a0_sha256: str
    operational_commit_sha: str

def canonical_anchor() -> TrustAnchor:
    return TrustAnchor(CANON_G0_COMMIT,CANON_G0_BUNDLE,CANON_G0_MANIFEST_BLOB,CANON_A0_ID,CANON_A0_BLOB,CANON_A0_SHA256,CANON_O)

def load_and_verify_promotion_record(path: Path) -> TrustAnchor:
    try:
        raw = Path(path).read_bytes()
        data = load_strict_json_bytes(raw, label="PROMOTION_RECORD_INVALID")
    except (OSError, ControlPlaneError) as exc:
        if isinstance(exc, ControlPlaneError): raise
        raise ControlPlaneError("PROMOTION_RECORD_INVALID") from exc
    try:
        gate=data["promoted_gate_core"]; auth=data["promoted_authority"]; boundary=data["authority_boundary"]
        if not isinstance(gate,dict) or not isinstance(auth,dict) or not isinstance(boundary,dict): raise KeyError
        a=canonical_anchor()
        valid=(data.get("schema_id")=="CEW_GATE_AUTHORITY_PROMOTION_RECORD" and data.get("schema_version")==1 and data.get("decision")=="PROMOTED" and data.get("repository")==REPOSITORY and gate.get("version")=="G0" and gate.get("exact_reviewed_commit_sha")==a.g0_commit_sha and gate.get("source_bundle_sha256")==a.g0_source_bundle_sha256 and gate.get("manifest_git_blob_sha")==a.g0_manifest_blob_sha and auth.get("authority_id")==a.authority_id and auth.get("git_blob_sha")==a.a0_blob_sha and auth.get("sha256")==a.a0_sha256 and auth.get("operational_commit")==a.operational_commit_sha and set(boundary)==_BOUNDARY_KEYS and all(boundary[k] is False for k in _BOUNDARY_KEYS) and data.get("cew_fem_01_required") is True)
    except (KeyError,TypeError): valid=False
    if not valid: raise ControlPlaneError("PROMOTION_RECORD_INVALID")
    return canonical_anchor()

def _git(git_dir: Path,*args: str,code: str)->bytes:
    try: cp=subprocess.run(["git","--git-dir",str(git_dir),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    except (OSError,subprocess.CalledProcessError) as exc: raise ControlPlaneError(code) from exc
    return cp.stdout

def verify_materialized_gate(git_dir: Path, anchor: TrustAnchor)->None:
    git_dir=Path(git_dir)
    head=_git(git_dir,"rev-parse","HEAD",code="G0_IDENTITY_MISMATCH").decode().strip()
    if head!=anchor.g0_commit_sha: raise ControlPlaneError("G0_IDENTITY_MISMATCH")
    mb=_git(git_dir,"rev-parse",f"{anchor.g0_commit_sha}:{MANIFEST_PATH}",code="G0_IDENTITY_MISMATCH").decode().strip()
    if mb!=anchor.g0_manifest_blob_sha: raise ControlPlaneError("G0_IDENTITY_MISMATCH")
    raw=_git(git_dir,"show",f"{anchor.g0_commit_sha}:{MANIFEST_PATH}",code="G0_IDENTITY_MISMATCH")
    try: manifest=json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc: raise ControlPlaneError("G0_IDENTITY_MISMATCH") from exc
    if not isinstance(manifest,dict) or manifest.get("source_bundle_sha256")!=anchor.g0_source_bundle_sha256: raise ControlPlaneError("G0_IDENTITY_MISMATCH")
    ab=_git(git_dir,"rev-parse",f"{anchor.g0_commit_sha}:{A0_PATH}",code="A0_IDENTITY_MISMATCH").decode().strip()
    if ab!=anchor.a0_blob_sha: raise ControlPlaneError("A0_IDENTITY_MISMATCH")
    a0=_git(git_dir,"show",f"{anchor.g0_commit_sha}:{A0_PATH}",code="A0_IDENTITY_MISMATCH")
    if hashlib.sha256(a0).hexdigest()!=anchor.a0_sha256: raise ControlPlaneError("A0_IDENTITY_MISMATCH")

def verify_operational_commit_available(git_dir: Path, anchor: TrustAnchor)->None:
    _git(Path(git_dir),"cat-file","-e",f"{anchor.operational_commit_sha}^{{commit}}",code="OPERATIONAL_AUTHORITY_FETCH_FAILED")
