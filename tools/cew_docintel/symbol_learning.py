import argparse, json, sqlite3
from pathlib import Path

SCHEMA='''
CREATE TABLE IF NOT EXISTS symbol_training(
 observation_id TEXT NOT NULL,
 meaning TEXT NOT NULL,
 verdict TEXT NOT NULL CHECK(verdict IN ('POSITIVE','NEGATIVE')),
 context_json TEXT NOT NULL,
 reviewer TEXT NOT NULL,
 PRIMARY KEY(observation_id,meaning,reviewer)
);
'''

def dbopen(path):
    c=sqlite3.connect(path); c.row_factory=sqlite3.Row; c.executescript(SCHEMA); return c

def label(db, obs, meaning, verdict, reviewer, context):
    with dbopen(db) as c:
        if not c.execute('SELECT 1 FROM observations WHERE id=?',(obs,)).fetchone(): raise SystemExit('observation sconosciuta')
        c.execute('INSERT OR REPLACE INTO symbol_training VALUES(?,?,?,?,?)',(obs,meaning,verdict,json.dumps(context,sort_keys=True),reviewer)); c.commit()

def stats(db):
    with dbopen(db) as c:
        rows=c.execute('SELECT meaning,verdict,COUNT(*) n FROM symbol_training GROUP BY meaning,verdict ORDER BY meaning,verdict').fetchall()
        return [dict(r) for r in rows]

def examples(db, meaning):
    with dbopen(db) as c:
        rows=c.execute('''SELECT t.*,o.source_version_id,o.page,o.x0,o.y0,o.x1,o.y1,o.kind,o.value_text,o.confidence,o.detector
                          FROM symbol_training t JOIN observations o ON o.id=t.observation_id
                          WHERE t.meaning=? ORDER BY t.verdict DESC,t.observation_id''',(meaning,)).fetchall()
        return [dict(r) for r in rows]

def main():
    p=argparse.ArgumentParser(description='CEW symbol meaning supervised dataset'); p.add_argument('--db',type=Path,default=Path('.cew/docintel.sqlite3'))
    s=p.add_subparsers(dest='cmd',required=True)
    x=s.add_parser('label'); x.add_argument('observation_id'); x.add_argument('--meaning',required=True); x.add_argument('--verdict',choices=['POSITIVE','NEGATIVE'],required=True); x.add_argument('--reviewer',required=True); x.add_argument('--context',default='{}')
    x=s.add_parser('stats')
    x=s.add_parser('examples'); x.add_argument('--meaning',required=True)
    a=p.parse_args()
    if a.cmd=='label': label(a.db,a.observation_id,a.meaning,a.verdict,a.reviewer,json.loads(a.context)); print('OK')
    elif a.cmd=='stats': print(json.dumps(stats(a.db),indent=2,ensure_ascii=False))
    else: print(json.dumps(examples(a.db,a.meaning),indent=2,ensure_ascii=False))
if __name__=='__main__': main()
