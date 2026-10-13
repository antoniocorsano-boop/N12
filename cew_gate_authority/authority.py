from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_EXPECTED_INVARIANTS = tuple(f"I{i:02d}" for i in range(1, 18))
_BOUNDARY_KEYS = {"solver_authorized","calculation_model_ready","synthetic_solver_result","solver_run","result_entity_created"}

@dataclass(frozen=True)
class BuilderAuthority:
    path: str
    git_blob_sha: str

@dataclass(frozen=True)
class RegistrationAuthority:
    source_path: str
    source_git_blob_sha: str
    support_ids: tuple[str, ...]
    examples: tuple[dict[str, Any], ...]

@dataclass(frozen=True)
class OutputAuthority:
    identity: str
    generation_id_inside_artifact: str
    sha256: str
    size_bytes: int
    generated_at: str

@dataclass(frozen=True)
class CandidateLimits:
    max_blobs: int
    max_blob_bytes: int
    max_aggregate_bytes: int
    max_json_depth: int
    max_csv_rows: int

@dataclass(frozen=True)
class FrozenAuthority:
    authority_id: str
    source_sha256: str
    operational_commit: str
    canonical_snapshot_id: str
    model_generation_id: str
    builder: BuilderAuthority
    inputs: tuple[tuple[str, str], ...]
    registration: RegistrationAuthority
    output: OutputAuthority
    authority_boundary: dict[str, bool]
    invariants: tuple[str, ...]
    candidate_allowlist: tuple[str, ...]
    limits: CandidateLimits

def _required(data: dict[str, Any], key: str) -> Any:
    if key not in data: raise ValueError(f"authority missing required field: {key}")
    return data[key]

def load_authority(path: Path) -> FrozenAuthority:
    raw=path.read_bytes(); data=json.loads(raw.decode("utf-8"))
    if data.get("schema_id")!="CEW_FROZEN_QUALIFICATION_AUTHORITY" or data.get("schema_version")!=1: raise ValueError("unsupported authority schema")
    inputs_raw=_required(data,"inputs")
    if not isinstance(inputs_raw,list) or len(inputs_raw)!=6: raise ValueError("authority inputs must contain exactly six entries")
    inputs=tuple((str(_required(item,"path")),str(_required(item,"sha256"))) for item in inputs_raw)
    if len({p for p,_ in inputs})!=6: raise ValueError("authority input paths must be unique")
    boundary=dict(_required(data,"authority_boundary"))
    if set(boundary)!=_BOUNDARY_KEYS or any(v is not False for v in boundary.values()): raise ValueError("authority boundary must contain exactly five explicit false flags")
    invariants=tuple(str(v) for v in _required(data,"invariants"))
    if invariants!=_EXPECTED_INVARIANTS: raise ValueError("authority invariants must be exactly I01..I17 in order")
    allowlist=tuple(str(v) for v in _required(data,"candidate_allowlist"))
    if len(allowlist)!=len(set(allowlist)): raise ValueError("candidate allowlist contains duplicates")
    builder=_required(data,"builder"); registration=_required(data,"registration"); output=_required(data,"output"); limits=_required(data,"limits")
    examples=tuple(dict(item) for item in _required(registration,"examples"))
    if tuple(str(item.get("support_id")) for item in examples)!=tuple(str(v) for v in _required(registration,"support_ids")): raise ValueError("registration examples do not match support_ids")
    return FrozenAuthority(
        authority_id=str(_required(data,"authority_id")),source_sha256=hashlib.sha256(raw).hexdigest(),operational_commit=str(_required(data,"operational_commit")),
        canonical_snapshot_id=str(_required(data,"canonical_snapshot_id")),model_generation_id=str(_required(data,"model_generation_id")),
        builder=BuilderAuthority(str(_required(builder,"path")),str(_required(builder,"git_blob_sha"))),inputs=inputs,
        registration=RegistrationAuthority(str(_required(registration,"source_path")),str(_required(registration,"source_git_blob_sha")),tuple(str(v) for v in _required(registration,"support_ids")),examples),
        output=OutputAuthority(str(_required(output,"identity")),str(_required(output,"generation_id_inside_artifact")),str(_required(output,"sha256")),int(_required(output,"size_bytes")),str(_required(output,"generated_at"))),
        authority_boundary=boundary,invariants=invariants,candidate_allowlist=allowlist,
        limits=CandidateLimits(int(_required(limits,"max_blobs")),int(_required(limits,"max_blob_bytes")),int(_required(limits,"max_aggregate_bytes")),int(_required(limits,"max_json_depth")),int(_required(limits,"max_csv_rows"))),
    )
