import argparse, json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def add(c,sv,page,kind,bbox,value,confidence,detector):
    oid='OBS-'+uuid.uuid4().hex[:12]
    c.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(oid,sv,page,kind,*bbox,value,float(confidence),detector,'CANDIDATE',now()))
    return oid

def main():
    p=argparse.ArgumentParser(); p.add_argument('--db',type=Path,required=True); p.add_argument('--source-version-id',required=True); p.add_argument('--page',type=int,default=1); p.add_argument('--geometry'); p.add_argument('--text'); p.add_argument('--detector',default='scan2dxf-v0.2'); a=p.parse_args()
    c=sqlite3.connect(a.db)
    if not c.execute('SELECT 1 FROM source_versions WHERE id=?',(a.source_version_id,)).fetchone(): raise SystemExit('source_version sconosciuta')
    ids=[]
    if a.geometry:
        for g in json.loads(Path(a.geometry).read_text(encoding='utf-8')):
            x1,y1,x2,y2=map(float,(g['x1'],g['y1'],g['x2'],g['y2']))
            ids.append(add(c,a.source_version_id,a.page,'line',(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)),g.get('family'),g.get('confidence',0),a.detector))
    if a.text:
        for t in json.loads(Path(a.text).read_text(encoding='utf-8')):
            x,y,w,h=map(float,(t['x'],t['y'],t['w'],t['h']))
            ids.append(add(c,a.source_version_id,a.page,'text',(x,y,x+w,y+h),t.get('text'),t.get('confidence',0),t.get('engine',a.detector)))
    c.commit(); c.close(); print(json.dumps({'imported':len(ids),'observation_ids':ids}))
if __name__=='__main__': main()
