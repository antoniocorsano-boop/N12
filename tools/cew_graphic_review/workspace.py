from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.cew_docintel import graphic_conventions as gc
from tools.cew_graphic_knowledge import docintel_bridge
from tools.cew_review import decision_store

WORKSPACE_SCHEMA_VERSION = "0.2.0"

BINDING_SCHEMA = """
CREATE TABLE IF NOT EXISTS graphic_review_bindings(
  case_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  observation_id TEXT NOT NULL,
  candidate_fingerprint TEXT NOT NULL,
  source_sha256 TEXT NOT NULL,
  context_json TEXT NOT NULL,
  feature_signature TEXT NOT NULL DEFAULT '{}',
  suggestions_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_graphic_review_project ON graphic_review_bindings(project_id,candidate_fingerprint);
"""


def now() -> str: return datetime.now(timezone.utc).isoformat()
def _review_connect(path: Path) -> sqlite3.Connection:
    c=decision_store.connect(path); c.executescript(BINDING_SCHEMA)
    cols={r["name"] for r in c.execute("PRAGMA table_info(graphic_review_bindings)")}
    if "feature_signature" not in cols: c.execute("ALTER TABLE graphic_review_bindings ADD COLUMN feature_signature TEXT NOT NULL DEFAULT '{}'")
    c.commit(); return c
def _candidate_row(project_db: Path,observation_id: str)->sqlite3.Row:
    with gc.connect(project_db) as c: return gc.current_observation(c,observation_id)
def _source_fingerprint(row: sqlite3.Row)->str: return f"sha256:{row['source_sha256']}|{gc.candidate_fingerprint(row)}"

def build_case(*,project_db:Path,fabric_db:Path,review_db:Path,project_id:str,observation_id:str,context:dict[str,Any],suggestion_limit:int=5)->dict[str,Any]:
    if not project_id.strip(): raise ValueError("project_id is required")
    row=_candidate_row(project_db,observation_id); candidate_fp=gc.candidate_fingerprint(row); source_fp=_source_fingerprint(row)
    candidate_feature=gc.feature_signature(row["kind"],row["value_text"],context)
    resolved=docintel_bridge.resolve_for_project(fabric_db,project_id,context,candidate_feature=candidate_feature,limit=suggestion_limit)
    evidence=[{"evidence_id":candidate_fp,"label":"Project source region","summary":json.dumps({"page":row["page"],"bbox_native":[row["x0"],row["y0"],row["x1"],row["y1"]],"kind":row["kind"],"value_text":row["value_text"],"detector":row["detector"],"confidence":row["confidence"],"feature_signature":json.loads(candidate_feature)},sort_keys=True,ensure_ascii=False),"locator":json.dumps({"source_sha256":row["source_sha256"],"page":row["page"],"bbox_native":[row["x0"],row["y0"],row["x1"],row["y1"]]},sort_keys=True),"role":"SUPPORTING"}]
    for candidate in resolved["candidates"]:
        role="COUNTER" if candidate["negative_weight"]>candidate["positive_weight"] else "CONTEXT"
        evidence.append({"evidence_id":f"GKF::{candidate['meaning']}","label":f"Shared knowledge candidate: {candidate['meaning']}","summary":json.dumps({"score":candidate["calibrated_score"],"layers":candidate["layers"],"conflict":candidate["conflict"],"positive_weight":candidate["positive_weight"],"negative_weight":candidate["negative_weight"],"uncertain_weight":candidate["uncertain_weight"],"contributors":candidate["contributors"]},sort_keys=True,ensure_ascii=False),"locator":f"gkf://meaning/{candidate['meaning']}","role":role})
    top=resolved["candidates"][0] if resolved["candidates"] else None
    summary=f"Shared candidate {top['meaning']} score={top['calibrated_score']} layers={','.join(top['layers'])}" if top else "No transferable shared meaning; human label required"
    case_id=decision_store.create_case(review_db,title=f"Graphic meaning review — {project_id}",question="What does this graphic occurrence mean in this project?",candidate_summary=summary,source_fingerprint=source_fp,evidence=evidence)
    with _review_connect(review_db) as c:
        c.execute("INSERT INTO graphic_review_bindings(case_id,project_id,observation_id,candidate_fingerprint,source_sha256,context_json,feature_signature,suggestions_json,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(case_id,project_id,observation_id,candidate_fp,row["source_sha256"],json.dumps(context,sort_keys=True,ensure_ascii=False),candidate_feature,json.dumps(resolved,sort_keys=True,ensure_ascii=False),now())); c.commit()
    return package_case(review_db,case_id)

def package_case(review_db:Path,case_id:str)->dict[str,Any]:
    base=decision_store.package(review_db,case_id)
    with _review_connect(review_db) as c:
        b=c.execute("SELECT * FROM graphic_review_bindings WHERE case_id=?",(case_id,)).fetchone()
        if not b: raise KeyError(case_id)
    return {"schema_version":WORKSPACE_SCHEMA_VERSION,"case":base,"graphic":{"project_id":b["project_id"],"observation_id":b["observation_id"],"candidate_fingerprint":b["candidate_fingerprint"],"source_sha256":b["source_sha256"],"context":json.loads(b["context_json"]),"feature_signature":json.loads(b["feature_signature"] or "{}")},"shared_knowledge":json.loads(b["suggestions_json"]),"allowed_label_verdicts":["POSITIVE","NEGATIVE","UNCERTAIN"],"required_human_fields":["meaning","verdict","reviewer","rationale"],"semantic_authority":"PROJECT_HUMAN_REVIEW"}

def submit_label(*,project_db:Path,fabric_db:Path,review_db:Path,case_id:str,meaning:str,verdict:str,reviewer:str,rationale:str)->dict[str,Any]:
    if verdict not in {"POSITIVE","NEGATIVE","UNCERTAIN"}: raise ValueError("verdict must be POSITIVE, NEGATIVE or UNCERTAIN")
    if not meaning.strip() or not reviewer.strip() or not rationale.strip(): raise ValueError("meaning, reviewer and rationale are required")
    with _review_connect(review_db) as c:
        b=c.execute("SELECT * FROM graphic_review_bindings WHERE case_id=?",(case_id,)).fetchone()
        if not b: raise KeyError(case_id)
    row=_candidate_row(project_db,b["observation_id"]); current_fp=gc.candidate_fingerprint(row)
    if current_fp!=b["candidate_fingerprint"] or row["source_sha256"]!=b["source_sha256"]:
        decision_store.invalidate_on_source_drift(review_db,case_id,_source_fingerprint(row)); raise ValueError("project source/generation drift: review must be rebuilt")
    context=json.loads(b["context_json"])
    label_id=gc.label_example(project_db,b["observation_id"],meaning.strip(),verdict,reviewer.strip(),context)
    bridge_receipt=docintel_bridge.import_project_labels(project_db,fabric_db,b["project_id"])
    generic={"POSITIVE":"APPROVE","NEGATIVE":"REJECT","UNCERTAIN":"DEFER"}[verdict]
    decision_id=decision_store.decide(review_db,case_id,generic,reviewer,rationale,_source_fingerprint(row))
    return {"status":"PASS","case_id":case_id,"decision_id":decision_id,"project_label_id":label_id,"project_id":b["project_id"],"candidate_fingerprint":current_fp,"meaning":meaning.strip(),"verdict":verdict,"fabric_bridge":bridge_receipt,"shared_generalization_created":False,"canonical_promotion":"DISABLED","next":"Generalization may be proposed only by the separate multi-project GKF gate."}
