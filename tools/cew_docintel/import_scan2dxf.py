import argparse, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def add(c,sv,generation_id,page,kind,bbox,value,confidence,detector):
    oid='OBS-'+uuid.uuid4().hex[:12]
    c.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(oid,sv,page,kind,*bbox,value,float(confidence),detector,'CANDIDATE',now()))
    c.execute('INSERT INTO observation_generation_bindings VALUES(?,?,?)',(oid,generation_id,now()))
    return oid

def main():
    p=argparse.ArgumentParser(); p.add_argument('--db',type=Path,required=True); p.add_argument('--source-version-id',required=True); p.add_argument('--generation-id',required=True); p.add_argument('--page',type=int,default=1); p.add_argument('--geometry'); p.add_argument('--text'); p.add_argument('--detector',default='scan2dxf-v0.2'); a=p.parse_args()
    c=sqlite3.connect(a.db); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
    if not c.execute('SELECT 1 FROM source_versions WHERE id=?',(a.source_version_id,)).fetchone(): raise SystemExit('source_version sconosciuta')
    g=c.execute('SELECT source_version_id,state FROM processing_generations WHERE id=?',(a.generation_id,)).fetchone()
    if not g: raise SystemExit('generation sconosciuta')
    if g['source_version_id']!=a.source_version_id: raise SystemExit('generation e source_version non coincidono')
    if g['state']!='RUNNING': raise SystemExit('import ammesso solo su generation RUNNING')
    ids=[]
    if a.geometry:
        for gline in json.loads(Path(a.geometry).read_text(encoding='utf-8')):
            x1,y1,x2,y2=map(float,(gline['x1'],gline['y1'],gline['x2'],gline['y2']))
            ids.append(add(c,a.source_version_id,a.generation_id,a.page,'line',(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)),gline.get('family'),gline.get('confidence',0),a.detector))
    if a.text:
        for t in json.loads(Path(a.text).read_text(encoding='utf-8')):
            x,y,w,h=map(float,(t['x'],t['y'],t['w'],t['h']))
            ids.append(add(c,a.source_version_id,a.generation_id,a.page,'text',(x,y,x+w,y+h),t.get('text'),t.get('confidence',0),t.get('engine',a.detector)))
    c.commit(); c.close(); print(json.dumps({'generation_id':a.generation_id,'imported':len(ids),'observation_ids':ids}))
if __name__=='__main__': main()
