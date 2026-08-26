from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.2.0"
RESOLVER_VERSION = "GRAPHIC_CONTEXT_AFFINITY_ENSEMBLE_V2"
PACK_VERSION = "CEW-GRAPHIC-KNOWLEDGE-PACK-v2"

DIMENSION_WEIGHTS = {
    "discipline": 2.0, "document_family": 2.5, "drawing_type": 3.0,
    "structural_system": 2.0, "drafting_era": 1.5, "authoring_office": 4.0,
    "notation_family": 2.5, "country": 1.0, "language": 0.5, "source_modality": 0.5,
}
PATTERN_WEIGHTS = {
    "kind": 3.0, "text": 4.0, "symbol_family": 4.0, "shape_family": 3.0,
    "line_family": 2.0, "neighbourhood_class": 2.0, "topology_signature": 3.0,
    "visual_cluster": 4.0,
}
FAMILY_DIMENSIONS = (
    "discipline", "document_family", "drawing_type", "structural_system", "drafting_era",
    "authoring_office", "notation_family", "country", "language",
)
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS gkf_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS gkf_examples(
 id TEXT PRIMARY KEY,project_id TEXT NOT NULL,source_sha256 TEXT NOT NULL,candidate_fingerprint TEXT NOT NULL,
 meaning TEXT NOT NULL,verdict TEXT NOT NULL CHECK(verdict IN ('POSITIVE','NEGATIVE','UNCERTAIN')),
 context_json TEXT NOT NULL,feature_signature TEXT NOT NULL DEFAULT '{}',reviewer TEXT NOT NULL,reviewed_at TEXT NOT NULL,
 UNIQUE(project_id,candidate_fingerprint,meaning,reviewer));
CREATE INDEX IF NOT EXISTS idx_gkf_examples_meaning ON gkf_examples(meaning,verdict);
CREATE INDEX IF NOT EXISTS idx_gkf_examples_project ON gkf_examples(project_id);
CREATE TABLE IF NOT EXISTS gkf_generalizations(
 id TEXT PRIMARY KEY,meaning TEXT NOT NULL,tier TEXT NOT NULL CHECK(tier IN ('FAMILY','GLOBAL')),scope_json TEXT NOT NULL,
 distinct_projects INTEGER NOT NULL,family_count INTEGER NOT NULL,positive_count INTEGER NOT NULL,negative_count INTEGER NOT NULL,
 uncertain_count INTEGER NOT NULL,state TEXT NOT NULL CHECK(state IN ('PROPOSED','HUMAN_VALIDATED','HUMAN_REJECTED','IMPORTED_SUPPORTED')),
 reviewer TEXT,rationale TEXT,created_at TEXT NOT NULL,reviewed_at TEXT,UNIQUE(meaning,tier,scope_json));
CREATE INDEX IF NOT EXISTS idx_gkf_generalizations_state ON gkf_generalizations(state,tier,meaning);
CREATE TABLE IF NOT EXISTS gkf_imports(pack_fingerprint TEXT PRIMARY KEY,imported_at TEXT NOT NULL,source_namespace TEXT,item_count INTEGER NOT NULL);
"""

def now() -> str: return datetime.now(timezone.utc).isoformat()
def canonical_json(value: dict[str, Any]) -> str: return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def normalize_value(value: Any) -> str:
    if value is None: return ""
    if isinstance(value,(list,tuple,set)): return "|".join(sorted(normalize_value(v) for v in value))
    return " ".join(str(value).strip().upper().split())
def normalize_context(context: dict[str, Any]) -> dict[str,str]:
    return {k:normalize_value(context.get(k)) for k in DIMENSION_WEIGHTS if normalize_value(context.get(k))}
def _table_columns(c: sqlite3.Connection, table: str) -> set[str]: return {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}
def connect(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(db); c.row_factory=sqlite3.Row; c.executescript(SCHEMA)
    if "feature_signature" not in _table_columns(c,"gkf_examples"):
        c.execute("ALTER TABLE gkf_examples ADD COLUMN feature_signature TEXT NOT NULL DEFAULT '{}'")
    current=c.execute("SELECT value FROM gkf_meta WHERE key='schema_version'").fetchone()
    if current and current["value"]>SCHEMA_VERSION:
        c.close(); raise RuntimeError(f"future Graphic Knowledge schema {current['value']} is not supported by {SCHEMA_VERSION}")
    c.execute("INSERT INTO gkf_meta(key,value) VALUES('schema_version',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(SCHEMA_VERSION,)); c.commit(); return c

def context_affinity(target: dict[str,Any],source: dict[str,Any]) -> dict[str,Any]:
    t=normalize_context(target); s=normalize_context(source); denominator=sum(DIMENSION_WEIGHTS[k] for k in t)
    if denominator==0: return {"score":0.0,"matched":[],"mismatched":[],"missing":list(DIMENSION_WEIGHTS)}
    matched=[]; mismatched=[]; missing=[]; score=0.0
    for k,v in t.items():
        sv=s.get(k)
        if not sv: missing.append(k)
        elif sv==v: matched.append(k); score+=DIMENSION_WEIGHTS[k]
        else: mismatched.append(k)
    return {"score":round(score/denominator,6),"matched":matched,"mismatched":mismatched,"missing":missing}

def _feature_object(feature: str|dict[str,Any]|None) -> dict[str,Any]:
    if feature is None: return {}
    if isinstance(feature,dict): return feature
    text=feature.strip()
    if not text: return {}
    try:
        value=json.loads(text); return value if isinstance(value,dict) else {"raw":text}
    except json.JSONDecodeError: return {"raw":text}
def pattern_core(feature: str|dict[str,Any]|None) -> dict[str,str]:
    obj=_feature_object(feature); ctx=obj.get("context") if isinstance(obj.get("context"),dict) else {}
    merged={
      "kind":obj.get("kind"),"text":obj.get("text"),"symbol_family":obj.get("symbol_family") or ctx.get("symbol_family"),
      "shape_family":obj.get("shape_family") or ctx.get("shape_family"),"line_family":obj.get("line_family") or ctx.get("line_family"),
      "neighbourhood_class":obj.get("neighbourhood_class") or ctx.get("neighbourhood_class"),
      "topology_signature":obj.get("topology_signature") or ctx.get("topology_signature"),"visual_cluster":obj.get("visual_cluster") or ctx.get("visual_cluster")}
    return {k:normalize_value(v) for k,v in merged.items() if normalize_value(v)}
def feature_signature(feature: str|dict[str,Any]|None) -> str: return canonical_json(_feature_object(feature))
def pattern_affinity(target: str|dict[str,Any]|None,source: str|dict[str,Any]|None) -> dict[str,Any]:
    t=pattern_core(target); s=pattern_core(source)
    if not t: return {"score":1.0,"matched":[],"mismatched":[],"missing":[],"mode":"UNSPECIFIED_TARGET"}
    denominator=sum(PATTERN_WEIGHTS[k] for k in t)
    if denominator==0: return {"score":0.0,"matched":[],"mismatched":[],"missing":list(t),"mode":"NO_USABLE_PATTERN"}
    if t.get("kind") and s.get("kind") and t["kind"]!=s["kind"]:
        return {"score":0.0,"matched":[],"mismatched":["kind"],"missing":[],"mode":"KIND_CONFLICT"}
    matched=[]; mismatched=[]; missing=[]; score=0.0
    for k,v in t.items():
        sv=s.get(k)
        if not sv: missing.append(k)
        elif sv==v: matched.append(k); score+=PATTERN_WEIGHTS[k]
        else: mismatched.append(k)
    return {"score":round(score/denominator,6),"matched":matched,"mismatched":mismatched,"missing":missing,"mode":"STRUCTURED_PATTERN"}
def combined_affinity(context_score: float,pattern_score: float) -> float:
    return 0.0 if pattern_score<=0 else round(pattern_score*(0.4+0.6*context_score),6)
def family_scope(context: dict[str,Any]) -> dict[str,str]:
    n=normalize_context(context); return {k:n[k] for k in FAMILY_DIMENSIONS if k in n}
def family_signature(context: dict[str,Any],pattern: str|dict[str,Any]|None=None) -> str:
    scope:dict[str,Any]=family_scope(context); p=pattern_core(pattern)
    if p: scope["_pattern"]=p
    return canonical_json(scope)
def stable_id(prefix: str,payload: dict[str,Any]) -> str: return prefix+hashlib.sha256(canonical_json(payload).encode()).hexdigest()

def add_example(db: Path,*,project_id: str,source_sha256: str,candidate_fingerprint: str,meaning: str,verdict: str,context: dict[str,Any],reviewer: str,reviewed_at: str|None=None,feature: str|dict[str,Any]|None=None) -> str:
    if verdict not in {"POSITIVE","NEGATIVE","UNCERTAIN"}: raise ValueError("verdict must be POSITIVE, NEGATIVE or UNCERTAIN")
    if not all(x.strip() for x in (project_id,source_sha256,candidate_fingerprint,meaning,reviewer)): raise ValueError("project_id, source_sha256, candidate_fingerprint, meaning and reviewer are required")
    if len(source_sha256)!=64: raise ValueError("source_sha256 must be a SHA-256 hex digest")
    if not candidate_fingerprint.startswith("GCFP-"): raise ValueError("candidate_fingerprint must use the GCFP stable identity")
    context_json=canonical_json(normalize_context(context)); feature_json=feature_signature(feature)
    eid=stable_id("GKE-",{"project_id":project_id,"source_sha256":source_sha256,"candidate_fingerprint":candidate_fingerprint,"meaning":meaning.strip(),"reviewer":reviewer.strip()})
    with connect(db) as c:
        c.execute("""INSERT INTO gkf_examples(id,project_id,source_sha256,candidate_fingerprint,meaning,verdict,context_json,feature_signature,reviewer,reviewed_at)
        VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(project_id,candidate_fingerprint,meaning,reviewer) DO UPDATE SET verdict=excluded.verdict,context_json=excluded.context_json,feature_signature=excluded.feature_signature,reviewed_at=excluded.reviewed_at""",
        (eid,project_id.strip(),source_sha256.lower(),candidate_fingerprint,meaning.strip(),verdict,context_json,feature_json,reviewer.strip(),reviewed_at or now())); c.commit()
    return eid

def _example_weight(project_id: str,target_project: str,affinity: float,pattern_score: float) -> float:
    if pattern_score<0.25: return 0.0
    if project_id==target_project: return 3.0*pattern_score
    return 0.0 if affinity<0.25 else 0.5+1.5*affinity
def _validated_generalization_weight(tier: str,state: str,affinity: float,pattern_score: float) -> float:
    if pattern_score<0.25: return 0.0
    trust=1.0 if state=="HUMAN_VALIDATED" else 0.45
    if tier=="GLOBAL": return (0.75+0.75*pattern_score)*trust
    return 0.0 if affinity<0.25 else (1.0+2.0*affinity)*trust

def resolve(db: Path,*,project_id: str,context: dict[str,Any],candidate_feature: str|dict[str,Any]|None=None,min_affinity: float=0.25,limit: int=5) -> dict[str,Any]:
    target_context=normalize_context(context); target_pattern=pattern_core(candidate_feature)
    support=defaultdict(lambda:{"positive":0.0,"negative":0.0,"uncertain":0.0,"local_positive":0.0,"local_negative":0.0,"contributors":[],"layers":set()})
    with connect(db) as c:
        examples=c.execute("SELECT * FROM gkf_examples ORDER BY reviewed_at,id").fetchall()
        generalizations=c.execute("SELECT * FROM gkf_generalizations WHERE state IN ('HUMAN_VALIDATED','IMPORTED_SUPPORTED') ORDER BY tier,meaning,id").fetchall()
    for row in examples:
        ci=context_affinity(target_context,json.loads(row["context_json"])); pi=pattern_affinity(candidate_feature,row["feature_signature"]); affinity=combined_affinity(ci["score"],pi["score"])
        weight=_example_weight(row["project_id"],project_id,affinity,pi["score"])
        if row["project_id"]!=project_id and affinity<min_affinity: continue
        if weight<=0: continue
        item=support[row["meaning"]]; layer="LOCAL" if row["project_id"]==project_id else "AFFINE"; item["layers"].add(layer)
        if row["verdict"]=="POSITIVE": item["positive"]+=weight; item["local_positive"]+=weight if layer=="LOCAL" else 0
        elif row["verdict"]=="NEGATIVE": item["negative"]+=weight; item["local_negative"]+=weight if layer=="LOCAL" else 0
        else: item["uncertain"]+=weight
        item["contributors"].append({"layer":layer,"project_id":row["project_id"],"candidate_fingerprint":row["candidate_fingerprint"],"verdict":row["verdict"],"context_affinity":ci["score"],"pattern_affinity":pi["score"],"affinity":affinity,"weight":round(weight,6)})
    for row in generalizations:
        scope=json.loads(row["scope_json"]); gp=scope.pop("_pattern",{}); cs=1.0 if row["tier"]=="GLOBAL" else context_affinity(target_context,scope)["score"]
        pi=pattern_affinity(candidate_feature,gp); affinity=combined_affinity(cs,pi["score"]); weight=_validated_generalization_weight(row["tier"],row["state"],affinity,pi["score"])
        if weight<=0: continue
        item=support[row["meaning"]]; item["positive"]+=weight; item["layers"].add(row["tier"])
        item["contributors"].append({"layer":row["tier"],"generalization_id":row["id"],"state":row["state"],"context_affinity":round(cs,6),"pattern_affinity":pi["score"],"affinity":affinity,"weight":round(weight,6)})
    ranked=[]
    for meaning,item in support.items():
        p,n,u=item["positive"],item["negative"],item["uncertain"]; decisive=p+n; raw=(1+p)/(2+decisive); certainty=decisive/(decisive+u+1) if decisive+u else 0; calibrated=0.5+(raw-0.5)*certainty
        conflict=(item["local_positive"]>0 and item["local_negative"]>0) or (p>0 and n>0 and abs(calibrated-0.5)<=0.15)
        contributors=sorted(item["contributors"],key=lambda x:(-float(x["weight"]),x.get("project_id",""),x.get("generalization_id","")))
        ranked.append({"meaning":meaning,"calibrated_score":round(calibrated,6),"decisive_support":round(decisive,6),"positive_weight":round(p,6),"negative_weight":round(n,6),"uncertain_weight":round(u,6),"layers":sorted(item["layers"]),"conflict":bool(conflict),"contributors":contributors[:8]})
    ranked.sort(key=lambda x:(-x["calibrated_score"],-x["decisive_support"],x["meaning"]))
    return {"schema_version":SCHEMA_VERSION,"resolver":RESOLVER_VERSION,"project_id":project_id,"context":target_context,"candidate_pattern":target_pattern,"status":"CANDIDATES_AVAILABLE" if ranked else "NO_TRANSFERABLE_MEANING","candidates":ranked[:limit],"semantic_authority":"NONE_UNTIL_PROJECT_HUMAN_VALIDATION","combination_policy":"GRAPHIC_PATTERN × PROJECT_CONTEXT -> LOCAL + AFFINE + FAMILY + GLOBAL"}

def _counts(rows): return (sum(r["verdict"]=="POSITIVE" for r in rows),sum(r["verdict"]=="NEGATIVE" for r in rows),sum(r["verdict"]=="UNCERTAIN" for r in rows))
def propose_generalizations(db: Path,*,min_family_projects:int=2,min_global_projects:int=3,max_negative_ratio:float=0.25)->list[str]:
    with connect(db) as c:
        rows=c.execute("SELECT * FROM gkf_examples ORDER BY meaning,project_id,id").fetchall(); groups=defaultdict(list)
        for r in rows: groups[(r["meaning"],canonical_json(pattern_core(r["feature_signature"])))].append(r)
        created=[]
        for (meaning,pkey),mrs in groups.items():
            pattern=json.loads(pkey); families=defaultdict(list)
            for r in mrs: families[family_signature(json.loads(r["context_json"]),pattern)].append(r)
            for sig,frs in families.items():
                p,n,u=_counts(frs); projects={r["project_id"] for r in frs if r["verdict"]=="POSITIVE"}; ratio=n/max(1,p+n)
                if p and len(projects)>=min_family_projects and ratio<=max_negative_ratio:
                    scope=json.loads(sig); pid=stable_id("GKG-",{"meaning":meaning,"tier":"FAMILY","scope":scope}); cur=c.execute("""INSERT INTO gkf_generalizations(id,meaning,tier,scope_json,distinct_projects,family_count,positive_count,negative_count,uncertain_count,state,created_at) VALUES(?,?,?,?,?,?,?,?,?,'PROPOSED',?) ON CONFLICT(meaning,tier,scope_json) DO NOTHING""",(pid,meaning,"FAMILY",sig,len(projects),1,p,n,u,now()));
                    if cur.rowcount==1: created.append(pid)
            pos=[r for r in mrs if r["verdict"]=="POSITIVE"]; neg=[r for r in mrs if r["verdict"]=="NEGATIVE"]; projects={r["project_id"] for r in pos}; fams={canonical_json(family_scope(json.loads(r["context_json"]))) for r in pos}; ratio=len(neg)/max(1,len(pos)+len(neg))
            if len(projects)>=min_global_projects and len(fams)>=2 and ratio<=max_negative_ratio:
                scope={"_pattern":pattern} if pattern else {}; sj=canonical_json(scope); pid=stable_id("GKG-",{"meaning":meaning,"tier":"GLOBAL","scope":scope}); cur=c.execute("""INSERT INTO gkf_generalizations(id,meaning,tier,scope_json,distinct_projects,family_count,positive_count,negative_count,uncertain_count,state,created_at) VALUES(?,?,?,?,?,?,?,?,?,'PROPOSED',?) ON CONFLICT(meaning,tier,scope_json) DO NOTHING""",(pid,meaning,"GLOBAL",sj,len(projects),len(fams),len(pos),len(neg),sum(r["verdict"]=="UNCERTAIN" for r in mrs),now()));
                if cur.rowcount==1: created.append(pid)
        c.commit(); return sorted(set(created))
def review_generalization(db:Path,proposal_id:str,decision:str,reviewer:str,rationale:str)->None:
    if decision not in {"APPROVE","REJECT"}: raise ValueError("decision must be APPROVE or REJECT")
    if not reviewer.strip() or not rationale.strip(): raise ValueError("reviewer and rationale are required")
    target="HUMAN_VALIDATED" if decision=="APPROVE" else "HUMAN_REJECTED"
    with connect(db) as c:
        cur=c.execute("UPDATE gkf_generalizations SET state=?,reviewer=?,rationale=?,reviewed_at=? WHERE id=? AND state IN ('PROPOSED','IMPORTED_SUPPORTED')",(target,reviewer.strip(),rationale.strip(),now(),proposal_id))
        if cur.rowcount!=1: raise ValueError("generalization is unknown or already locally reviewed")
        c.commit()
def _pack_body(c,namespace): return {"pack_version":PACK_VERSION,"source_namespace":namespace,"examples":[dict(r) for r in c.execute("SELECT * FROM gkf_examples ORDER BY id")],"validated_generalizations":[dict(r) for r in c.execute("SELECT * FROM gkf_generalizations WHERE state='HUMAN_VALIDATED' ORDER BY tier,meaning,id")]}
def export_pack(db:Path,namespace:str)->dict[str,Any]:
    with connect(db) as c: body=_pack_body(c,namespace)
    return {**body,"pack_fingerprint":"sha256:"+hashlib.sha256(canonical_json(body).encode()).hexdigest()}
def import_pack(db:Path,pack:dict[str,Any])->dict[str,Any]:
    if pack.get("pack_version")!=PACK_VERSION: raise ValueError("unsupported knowledge pack version")
    body={k:pack[k] for k in ("pack_version","source_namespace","examples","validated_generalizations")}; expected="sha256:"+hashlib.sha256(canonical_json(body).encode()).hexdigest()
    if pack.get("pack_fingerprint")!=expected: raise ValueError("knowledge pack fingerprint mismatch")
    with connect(db) as c:
        if c.execute("SELECT 1 FROM gkf_imports WHERE pack_fingerprint=?",(expected,)).fetchone(): return {"status":"ALREADY_IMPORTED","pack_fingerprint":expected,"imported":0}
        imported=0
        for r in pack["examples"]:
            c.execute("INSERT OR IGNORE INTO gkf_examples(id,project_id,source_sha256,candidate_fingerprint,meaning,verdict,context_json,feature_signature,reviewer,reviewed_at) VALUES(?,?,?,?,?,?,?,?,?,?)",tuple(r[k] for k in ("id","project_id","source_sha256","candidate_fingerprint","meaning","verdict","context_json","feature_signature","reviewer","reviewed_at"))); imported+=c.execute("SELECT changes()").fetchone()[0]
        for r in pack["validated_generalizations"]:
            c.execute("""INSERT INTO gkf_generalizations(id,meaning,tier,scope_json,distinct_projects,family_count,positive_count,negative_count,uncertain_count,state,reviewer,rationale,created_at,reviewed_at) VALUES(?,?,?,?,?,?,?,?,?,'IMPORTED_SUPPORTED',?,?,?,?) ON CONFLICT(meaning,tier,scope_json) DO NOTHING""",(r["id"],r["meaning"],r["tier"],r["scope_json"],r["distinct_projects"],r["family_count"],r["positive_count"],r["negative_count"],r["uncertain_count"],r.get("reviewer"),r.get("rationale"),r["created_at"],r.get("reviewed_at"))); imported+=c.execute("SELECT changes()").fetchone()[0]
        c.execute("INSERT INTO gkf_imports VALUES(?,?,?,?)",(expected,now(),pack.get("source_namespace"),imported)); c.commit()
    return {"status":"IMPORTED_SUPPORTED","pack_fingerprint":expected,"imported":imported}
def status(db:Path)->dict[str,Any]:
    with connect(db) as c:
        return {"schema_version":SCHEMA_VERSION,"examples":c.execute("SELECT COUNT(*) n FROM gkf_examples").fetchone()["n"],"projects":c.execute("SELECT COUNT(DISTINCT project_id) n FROM gkf_examples").fetchone()["n"],"generalization_states":{r["state"]:r["n"] for r in c.execute("SELECT state,COUNT(*) n FROM gkf_generalizations GROUP BY state")},"imports":c.execute("SELECT COUNT(*) n FROM gkf_imports").fetchone()["n"],"semantic_authority":"HUMAN_REVIEW_REQUIRED"}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--db",type=Path,required=True); s=p.add_subparsers(dest="cmd",required=True); s.add_parser("init")
    x=s.add_parser("resolve"); x.add_argument("--project-id",required=True); x.add_argument("--context",required=True); x.add_argument("--candidate-feature",default="{}"); x.add_argument("--limit",type=int,default=5)
    x=s.add_parser("generalize"); x.add_argument("--min-family-projects",type=int,default=2); x.add_argument("--min-global-projects",type=int,default=3)
    x=s.add_parser("review-generalization"); x.add_argument("proposal_id"); x.add_argument("--decision",choices=["APPROVE","REJECT"],required=True); x.add_argument("--reviewer",required=True); x.add_argument("--rationale",required=True)
    x=s.add_parser("export-pack"); x.add_argument("--namespace",required=True); x.add_argument("--output",type=Path,required=True); x=s.add_parser("import-pack"); x.add_argument("path",type=Path); s.add_parser("status"); a=p.parse_args()
    if a.cmd=="init": connect(a.db).close(); print(json.dumps({"status":"PASS","schema_version":SCHEMA_VERSION}))
    elif a.cmd=="resolve": print(json.dumps(resolve(a.db,project_id=a.project_id,context=json.loads(a.context),candidate_feature=a.candidate_feature,limit=a.limit),indent=2))
    elif a.cmd=="generalize": print(json.dumps({"created":propose_generalizations(a.db,min_family_projects=a.min_family_projects,min_global_projects=a.min_global_projects)}))
    elif a.cmd=="review-generalization": review_generalization(a.db,a.proposal_id,a.decision,a.reviewer,a.rationale); print("OK")
    elif a.cmd=="export-pack":
        payload=export_pack(a.db,a.namespace); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); print(payload["pack_fingerprint"])
    elif a.cmd=="import-pack": print(json.dumps(import_pack(a.db,json.loads(a.path.read_text(encoding="utf-8"))),indent=2))
    else: print(json.dumps(status(a.db),indent=2))
if __name__=="__main__": main()
