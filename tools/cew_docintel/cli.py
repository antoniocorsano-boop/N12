from __future__ import annotations
import argparse, hashlib, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB=Path('.cew/docintel.sqlite3')
SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,label TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS source_versions(id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sources(id),path TEXT NOT NULL,sha256 TEXT NOT NULL UNIQUE,size_bytes INTEGER NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS processing_generations(
 id TEXT PRIMARY KEY,
 source_version_id TEXT NOT NULL REFERENCES source_versions(id),
 generation_no INTEGER NOT NULL,
 processor TEXT NOT NULL,
 processor_version TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('RUNNING','SUCCEEDED','FAILED')),
 metadata_json TEXT NOT NULL,
 error_text TEXT,
 started_at TEXT NOT NULL,
 completed_at TEXT,
 UNIQUE(source_version_id,generation_no)
);
CREATE INDEX IF NOT EXISTS idx_generation_source_state ON processing_generations(source_version_id,state,generation_no);
CREATE TABLE IF NOT EXISTS source_version_processing(
 source_version_id TEXT PRIMARY KEY REFERENCES source_versions(id),
 current_generation_id TEXT REFERENCES processing_generations(id),
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS observations(id TEXT PRIMARY KEY,source_version_id TEXT NOT NULL REFERENCES source_versions(id),page INTEGER NOT NULL,kind TEXT NOT NULL,x0 REAL,y0 REAL,x1 REAL,y1 REAL,value_text TEXT,confidence REAL,detector TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('DETECTED','CANDIDATE','SUPPORTED','VALIDATED','REJECTED')),created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_obs_kind_value ON observations(kind,value_text);
CREATE INDEX IF NOT EXISTS idx_obs_source_page ON observations(source_version_id,page);
CREATE INDEX IF NOT EXISTS idx_obs_bbox ON observations(x0,y0,x1,y1);
CREATE TABLE IF NOT EXISTS observation_generation_bindings(
 observation_id TEXT PRIMARY KEY REFERENCES observations(id),
 generation_id TEXT NOT NULL REFERENCES processing_generations(id),
 bound_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_obs_generation ON observation_generation_bindings(generation_id);
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
def compact_json(raw): return json.dumps(json.loads(raw or '{}'),sort_keys=True,separators=(',',':'),ensure_ascii=False)

def cmd_init(a):
    with connect(a.db) as c: c.commit()
    print(json.dumps({'status':'PASS','db':str(a.db)}))
def cmd_ingest(a):
    p=Path(a.path).resolve()
    if not p.is_file(): raise SystemExit('file non trovato')
    h=digest(p)
    with connect(a.db) as c:
        c.execute('INSERT OR IGNORE INTO sources VALUES(?,?,?)',(a.source_id,a.label or a.source_id,now()))
        r=c.execute('SELECT id,source_id FROM source_versions WHERE sha256=?',(h,)).fetchone()
        if r and r['source_id']!=a.source_id: raise SystemExit('hash già registrato sotto una source diversa')
        vid=r['id'] if r else 'SV-'+uuid.uuid4().hex[:12]
        if not r: c.execute('INSERT INTO source_versions VALUES(?,?,?,?,?,?)',(vid,a.source_id,str(p),h,p.stat().st_size,now()))
        c.commit()
    print(json.dumps({'source_id':a.source_id,'source_version_id':vid,'sha256':h,'path':str(p)}))

def cmd_generation_start(a):
    metadata=compact_json(a.metadata)
    with connect(a.db) as c:
        if not c.execute('SELECT 1 FROM source_versions WHERE id=?',(a.source_version_id,)).fetchone(): raise SystemExit('source_version sconosciuta')
        n=c.execute('SELECT COALESCE(MAX(generation_no),0)+1 n FROM processing_generations WHERE source_version_id=?',(a.source_version_id,)).fetchone()['n']
        gid='GEN-'+uuid.uuid4().hex[:12]
        c.execute('INSERT INTO processing_generations(id,source_version_id,generation_no,processor,processor_version,state,metadata_json,started_at) VALUES(?,?,?,?,?,?,?,?)',(gid,a.source_version_id,n,a.processor,a.processor_version,'RUNNING',metadata,now()))
        c.commit()
    print(json.dumps({'generation_id':gid,'source_version_id':a.source_version_id,'generation_no':n,'state':'RUNNING'}))

def generation_row(c,gid):
    r=c.execute('SELECT * FROM processing_generations WHERE id=?',(gid,)).fetchone()
    if not r: raise SystemExit('generation sconosciuta')
    return r

def cmd_generation_succeed(a):
    with connect(a.db) as c:
        r=generation_row(c,a.generation_id)
        if r['state']!='RUNNING': raise SystemExit('solo una generation RUNNING può diventare SUCCEEDED')
        finished=now()
        c.execute("UPDATE processing_generations SET state='SUCCEEDED',completed_at=? WHERE id=?",(finished,a.generation_id))
        c.execute('''INSERT INTO source_version_processing(source_version_id,current_generation_id,updated_at) VALUES(?,?,?)
                     ON CONFLICT(source_version_id) DO UPDATE SET current_generation_id=excluded.current_generation_id,updated_at=excluded.updated_at''',(r['source_version_id'],a.generation_id,finished))
        c.commit()
    print(json.dumps({'generation_id':a.generation_id,'source_version_id':r['source_version_id'],'state':'SUCCEEDED','current':True}))

def cmd_generation_fail(a):
    with connect(a.db) as c:
        r=generation_row(c,a.generation_id)
        if r['state']!='RUNNING': raise SystemExit('solo una generation RUNNING può diventare FAILED')
        c.execute("UPDATE processing_generations SET state='FAILED',error_text=?,completed_at=? WHERE id=?",(a.error,now(),a.generation_id)); c.commit()
        current=c.execute('SELECT current_generation_id FROM source_version_processing WHERE source_version_id=?',(r['source_version_id'],)).fetchone()
    print(json.dumps({'generation_id':a.generation_id,'source_version_id':r['source_version_id'],'state':'FAILED','current_generation_id':current['current_generation_id'] if current else None}))

def cmd_generation_status(a):
    with connect(a.db) as c:
        current=c.execute('SELECT current_generation_id FROM source_version_processing WHERE source_version_id=?',(a.source_version_id,)).fetchone()
        rows=c.execute('SELECT id,generation_no,processor,processor_version,state,error_text,started_at,completed_at FROM processing_generations WHERE source_version_id=? ORDER BY generation_no',(a.source_version_id,)).fetchall()
    print(json.dumps({'source_version_id':a.source_version_id,'current_generation_id':current['current_generation_id'] if current else None,'generations':[dict(r) for r in rows]},indent=2,ensure_ascii=False))

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
        g=generation_row(c,a.generation_id)
        if g['source_version_id']!=a.source_version_id: raise SystemExit('generation e source_version non coincidono')
        if g['state']!='RUNNING': raise SystemExit('osservazioni ammesse solo su generation RUNNING')
        c.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(oid,a.source_version_id,a.page,a.kind,x0,y0,x1,y1,a.value,a.confidence,a.detector,a.state,now()))
        c.execute('INSERT INTO observation_generation_bindings VALUES(?,?,?)',(oid,a.generation_id,now())); c.commit()
    print(oid)
def cmd_convention(a):
    scope=json.dumps(json.loads(a.scope),sort_keys=True,separators=(',',':'),ensure_ascii=False); cid='CONV-'+uuid.uuid4().hex[:12]
    with connect(a.db) as c:
        c.execute('INSERT INTO conventions VALUES(?,?,?,?,?,?)',(cid,a.name,a.meaning,scope,'CANDIDATE',now())); c.commit()
    print(cid)
def cmd_curate(a):
    made=[]
    with connect(a.db) as c:
        rows=c.execute('''SELECT o.kind,o.value_text,COUNT(*) n,AVG(o.confidence) conf
                          FROM observations o
                          JOIN observation_generation_bindings b ON b.observation_id=o.id
                          JOIN source_version_processing sp ON sp.source_version_id=o.source_version_id AND sp.current_generation_id=b.generation_id
                          JOIN processing_generations g ON g.id=b.generation_id AND g.state='SUCCEEDED'
                          WHERE o.state IN ('CANDIDATE','SUPPORTED') AND COALESCE(TRIM(o.value_text),'')<>''
                          GROUP BY o.kind,o.value_text HAVING COUNT(*)>=?''',(a.min_occurrences,)).fetchall()
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
        out={t:c.execute(f'SELECT COUNT(*) n FROM {t}').fetchone()['n'] for t in ('sources','source_versions','processing_generations','observations','conventions','proposals')}
        out['generation_states']={r['state']:r['n'] for r in c.execute('SELECT state,COUNT(*) n FROM processing_generations GROUP BY state')}
        out['current_generations']=c.execute('SELECT COUNT(*) n FROM source_version_processing WHERE current_generation_id IS NOT NULL').fetchone()['n']
        out['observation_states']={r['state']:r['n'] for r in c.execute('SELECT state,COUNT(*) n FROM observations GROUP BY state')}
        out['proposal_states']={r['state']:r['n'] for r in c.execute('SELECT state,COUNT(*) n FROM proposals GROUP BY state')}
    print(json.dumps(out,indent=2))
def cmd_validate(a):
    with connect(a.db) as c:
        fk=c.execute('PRAGMA foreign_key_check').fetchall()
        bad_review=c.execute("SELECT COUNT(*) n FROM proposals WHERE state='VALIDATED' AND (reviewer IS NULL OR reviewed_at IS NULL)").fetchone()['n']
        unbound=c.execute('''SELECT COUNT(*) n FROM observations o LEFT JOIN observation_generation_bindings b ON b.observation_id=o.id WHERE b.observation_id IS NULL''').fetchone()['n']
        bad_binding=c.execute('''SELECT COUNT(*) n FROM observations o JOIN observation_generation_bindings b ON b.observation_id=o.id JOIN processing_generations g ON g.id=b.generation_id WHERE o.source_version_id<>g.source_version_id''').fetchone()['n']
        bad_current=c.execute('''SELECT COUNT(*) n FROM source_version_processing sp JOIN processing_generations g ON g.id=sp.current_generation_id WHERE g.state<>'SUCCEEDED' OR g.source_version_id<>sp.source_version_id''').fetchone()['n']
    ok=not fk and not bad_review and not unbound and not bad_binding and not bad_current
    print(json.dumps({'status':'PASS' if ok else 'FAIL','canonical_promotion':'DISABLED','human_review_required':True,'unbound_observations':unbound,'invalid_generation_bindings':bad_binding,'invalid_current_generations':bad_current}))
    raise SystemExit(0 if ok else 2)
def main():
    p=argparse.ArgumentParser(); p.add_argument('--db',type=Path,default=DEFAULT_DB); s=p.add_subparsers(dest='cmd',required=True)
    x=s.add_parser('init'); x.set_defaults(fn=cmd_init)
    x=s.add_parser('ingest'); x.add_argument('path'); x.add_argument('--source-id',required=True); x.add_argument('--label'); x.set_defaults(fn=cmd_ingest)
    x=s.add_parser('generation-start'); x.add_argument('--source-version-id',required=True); x.add_argument('--processor',required=True); x.add_argument('--processor-version',required=True); x.add_argument('--metadata',default='{}'); x.set_defaults(fn=cmd_generation_start)
    x=s.add_parser('generation-succeed'); x.add_argument('generation_id'); x.set_defaults(fn=cmd_generation_succeed)
    x=s.add_parser('generation-fail'); x.add_argument('generation_id'); x.add_argument('--error',required=True); x.set_defaults(fn=cmd_generation_fail)
    x=s.add_parser('generation-status'); x.add_argument('--source-version-id',required=True); x.set_defaults(fn=cmd_generation_status)
    x=s.add_parser('observe'); x.add_argument('--source-version-id',required=True); x.add_argument('--generation-id',required=True); x.add_argument('--page',type=int,default=1); x.add_argument('--kind',required=True); x.add_argument('--bbox'); x.add_argument('--value'); x.add_argument('--confidence',type=float,default=0); x.add_argument('--detector',required=True); x.add_argument('--state',default='CANDIDATE',choices=['DETECTED','CANDIDATE','SUPPORTED']); x.set_defaults(fn=cmd_observe)
    x=s.add_parser('convention-add'); x.add_argument('--name',required=True); x.add_argument('--meaning',required=True); x.add_argument('--scope',required=True); x.set_defaults(fn=cmd_convention)
    x=s.add_parser('curate'); x.add_argument('--min-occurrences',type=int,default=3); x.set_defaults(fn=cmd_curate)
    x=s.add_parser('proposals'); x.set_defaults(fn=cmd_proposals)
    x=s.add_parser('proposal-review'); x.add_argument('proposal_id'); x.add_argument('--decision',required=True); x.add_argument('--reviewer',required=True); x.set_defaults(fn=cmd_review)
    x=s.add_parser('status'); x.set_defaults(fn=cmd_status)
    x=s.add_parser('validate'); x.set_defaults(fn=cmd_validate)
    a=p.parse_args(); a.fn(a)
if __name__=='__main__': main()
