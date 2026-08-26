from __future__ import annotations
import argparse, hashlib, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB=Path('.cew/docintel.sqlite3')
SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,label TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS source_versions(id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(id),path TEXT NOT NULL,sha256 TEXT NOT NULL UNIQUE,size_bytes INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY,source_version_id TEXT NOT NULL REFERENCES source_versions(id),page INTEGER NOT NULL,kind TEXT NOT NULL,x0 REAL,y0 REAL,x1 REAL,y1 REAL,value_text TEXT,confidence REAL,detector TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('DETECTED','CANDIDATE','SUPPORTED','VALIDATED','REJECTED')),created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_obs_kind_value ON observations(kind,value_text);
CREATE INDEX IF NOT EXISTS idx_obs_source_page ON observations(source_version_id,page);
CREATE INDEX IF NOT EXISTS idx_obs_bbox ON observations(x0,y0,x1,y1);
CREATE TABLE IF NOT EXISTS conventions(id TEXT PRIMARY KEY,name TEXT NOT NULL,meaning TEXT NOT NULL,scope_json TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('CANDIDATE','SUPPORTED','VALIDATED','REJECTED')),created_at TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS idx_conv_name_scope ON conventions(name,scope_json);
CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY,proposal_type TEXT NOT NULL,key_text TEXT NOT NULL,payload_json TEXT NOT NULL,evidence_count INTEGER NOT NULL,state TEXT NOT NULL CHECK(state IN ('PROPOSED','VALIDATED','REJECTED')),reviewer TEXT,reviewed_at TEXT,created_at TEXT NOT NULL);
'''

def now(): return datetime.now(timezone.utc).isoformat()
def connect(p):
    p.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(p); c.row_factory=sqlite3.Row; c.executescript(SCHEMA); return c
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def cmd_init(a):
    with connect(a.db) as c: c.commit()
    print(json.dumps({'status':'PASS','db':str(a.db)}))
def cmd_ingest(a):
    p=Path(a.path).resolve()
    if not p.is_file(): raise SystemExit('file non trovato')
    h=digest(p)
    with connect(a.db) as c:
        c.execute('INSERT OR IGNORE INTO sources VALUES(?,?,?)',(a.source_id,a.label or a.source_id,now()))
        r=c.execute('SELECT id FROM source_versions WHERE sha256=?',(h,)).fetchone()
        vid=r['id'] if r else 'SV-'+uuid.uuid4().hex[:12]
        if not r: c.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?)',(vid,a.source_id,str(p),h,p.stat().st_size,now()))
        c.commit()
    print(json.dumps({'source_id':a.source_id,'source_version_id':vid,'sha256':h,'path':str(p)}))
def bbox(s):
    if not s: return (None,None,None,None)
    v=[float(x) for x in s.split(',')]
    if len(v)!=4: raise SystemExit('bbox: x0,y0,x1,y1')
    return tuple(v)
def cmd_observe(a):
    if a.state not in {'DETECTED','CANDIDATE','SUPPORTED'}: raise SystemExit('promozione diretta vietata')
    if not 0<=a.confidence<=1: raise SystemExit('confidence 0..1')
    x0,y0,x1,y1=bbox(a.bbox); oid='OBS-'+uuid.uuid4().hex[:12]
    with connect(a.db) as c:
        if not c.execute('SELECT 1 FROM source_versions WHERE id=?',(a.source_version_id,)).fetchone(): raise SystemExit('source_version sconosciuta')
        c.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(oid,a.source_version_id,a.page,a.kind,x0,y0,x1,y1,a.value,a.confidence,a.detector,a.state,now())); c.commit()
    print(oid)
def cmd_convention(a):
    scope=json.dumps(json.loads(a.scope),sort_keys=True,separators=(',',':'),ensure_ascii=False); cid='CONV-'+uuid.uuid4().hex[:12]
    with connect(a.db) as c:
        c.execute('INSERT INTO conventions VALUES(?,?,?,?,?,?)',(cid,a.name,a.meaning,scope,'CANDIDATE',now())); c.commit()
    print(cid)
def cmd_curate(a):
    made=[]
    with connect(a.db) as c:
        rows=c.execute("SELECT kind,value_text,COUNT(*) n,AVG(confidence) conf FROM observations WHERE state IN ('CANDIDATE','SUPPORTED') AND COALESCE(TRIM(value_text),'')<>'' GROUP BY kind,value_text HAVING COUNT(*)>=?",(a.min_occurrences,)).fetchall()
        for r in rows:
            key=f"{r['kind']}::{r['value_text']}"; ex=c.execute("SELECT 1 FROM proposals WHERE key_text=? AND state='PROPOSED'",(key,)).fetchone()
            if ex: continue
            pid='PROP-'+uuid.uuid4().hex[:12]; payload=json.dumps({'kind':r['kind'],'value':r['value_text'],'mean_confidence':round(r['conf'] or 0,4)},ensure_ascii=False)
            c.execute('INSERT INTO proposals(id,proposal_type,key_text,payload_json,evidence_count,state,created_at) VALUES(?,?,?,?,?,?,?)',(pid,'RECURRING_GRAPHIC_PATTERN',key,payload,r['n'],'PROPOSED',now())); made.append(pid)
        c.commit()
    print(json.dumps({'created':made,'count':len(made)}))
def cmd_proposals(a):
    with connect(a.db) as c:
        for r in c.execute('SELECT * FROM proposals ORDER BY created_at DESC'): print(json.dumps(dict(r),ensure_ascii=False))
def cmd_review(a):
    if a.decision not in {'VALIDATED','REJECTED'}: raise SystemExit('decision non valida')
    with connect(a.db) as c:
        cur=c.execute("UPDATE proposals SET state=?,reviewer=?,reviewed_at=? WHERE id=? AND state='PROPOSED'",(a.decision,a.reviewer,now(),a.proposal_id))
        if cur.rowcount!=1: raise SystemExit('proposta non disponibile')
        c.commit()
    print('OK')
def cmd_status(a):
    with connect(a.db) as c:
        out={t:c.execute(f'SELECT COUNT(*) n FROM {t}').fetchone()['n'] for t in ('sources','source_versions','observations','conventions','proposals')}
        out['observation_states']={r['state']:r['n'] for r in c.execute('SELECT state,COUNT(*) n FROM observations GROUP BY state')}
        out['proposal_states']={r['state']:r['n'] for r in c.execute('SELECT state,COUNT(*) n FROM proposals GROUP BY state')}
    print(json.dumps(out,indent=2))
def cmd_validate(a):
    with connect(a.db) as c:
        fk=c.execute('PRAGMA foreign_key_check').fetchall(); bad=c.execute("SELECT COUNT(*) n FROM proposals WHERE state='VALIDATED' AND (reviewer IS NULL OR reviewed_at IS NULL)").fetchone()['n']
    ok=not fk and not bad; print(json.dumps({'status':'PASS' if ok else 'FAIL','canonical_promotion':'DISABLED','human_review_required':True})); raise SystemExit(0 if ok else 2)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--db',type=Path,default=DEFAULT_DB); s=p.add_subparsers(dest='cmd',required=True)
    x=s.add_parser('init'); x.set_defaults(fn=cmd_init)
    x=s.add_parser('ingest'); x.add_argument('path'); x.add_argument('--source-id',required=True); x.add_argument('--label'); x.set_defaults(fn=cmd_ingest)
    x=s.add_parser('observe'); x.add_argument('--source-version-id',required=True); x.add_argument('--page',type=int,default=1); x.add_argument('--kind',required=True); x.add_argument('--bbox'); x.add_argument('--value'); x.add_argument('--confidence',type=float,default=0); x.add_argument('--detector',required=True); x.add_argument('--state',default='CANDIDATE',choices=['DETECTED','CANDIDATE','SUPPORTED']); x.set_defaults(fn=cmd_observe)
    x=s.add_parser('convention-add'); x.add_argument('--name',required=True); x.add_argument('--meaning',required=True); x.add_argument('--scope',required=True); x.set_defaults(fn=cmd_convention)
    x=s.add_parser('curate'); x.add_argument('--min-occurrences',type=int,default=3); x.set_defaults(fn=cmd_curate)
    x=s.add_parser('proposals'); x.set_defaults(fn=cmd_proposals)
    x=s.add_parser('proposal-review'); x.add_argument('proposal_id'); x.add_argument('--decision',required=True); x.add_argument('--reviewer',required=True); x.set_defaults(fn=cmd_review)
    x=s.add_parser('status'); x.set_defaults(fn=cmd_status)
    x=s.add_parser('validate'); x.set_defaults(fn=cmd_validate)
    a=p.parse_args(); a.fn(a)
if __name__=='__main__': main()
