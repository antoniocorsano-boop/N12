import json, sqlite3, subprocess, sys, tempfile, unittest
from pathlib import Path

CLI=Path(__file__).resolve().parents[1]/'cli.py'
class DocIntelTests(unittest.TestCase):
    def run_cli(self,*args):
        r=subprocess.run([sys.executable,str(CLI),*args],text=True,capture_output=True,check=True)
        return r.stdout.strip()
    def run_cli_fail(self,*args):
        r=subprocess.run([sys.executable,str(CLI),*args],text=True,capture_output=True)
        self.assertNotEqual(r.returncode,0)
        return (r.stdout+r.stderr).strip()
    def start_generation(self,db,sv,version='v1'):
        return json.loads(self.run_cli('--db',str(db),'generation-start','--source-version-id',sv,'--processor','test','--processor-version',version))['generation_id']
    def observe(self,db,sv,gid,value):
        return self.run_cli('--db',str(db),'observe','--source-version-id',sv,'--generation-id',gid,'--kind','text','--value',value,'--confidence','0.9','--detector','test')
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); db=root/'db.sqlite3'; src=root/'sample.txt'; src.write_text('25/70')
            self.run_cli('--db',str(db),'init')
            out=json.loads(self.run_cli('--db',str(db),'ingest',str(src),'--source-id','S1'))
            sv=out['source_version_id']; gid=self.start_generation(db,sv)
            for _ in range(3): self.observe(db,sv,gid,'25/70')
            self.run_cli('--db',str(db),'generation-succeed',gid)
            cur=json.loads(self.run_cli('--db',str(db),'curate','--min-occurrences','3'))
            self.assertEqual(cur['count'],1)
            status=json.loads(self.run_cli('--db',str(db),'generation-status','--source-version-id',sv))
            self.assertEqual(status['current_generation_id'],gid)
            val=json.loads(self.run_cli('--db',str(db),'validate'))
            self.assertEqual(val['status'],'PASS'); self.assertEqual(val['canonical_promotion'],'DISABLED')
    def test_failed_reprocessing_never_replaces_current_generation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); db=root/'db.sqlite3'; src=root/'sample.txt'; src.write_text('source')
            self.run_cli('--db',str(db),'init')
            sv=json.loads(self.run_cli('--db',str(db),'ingest',str(src),'--source-id','S1'))['source_version_id']
            with sqlite3.connect(db) as c:
                original=c.execute('SELECT source_id,path,sha256,size_bytes,created_at FROM source_versions WHERE id=?',(sv,)).fetchone()
            g1=self.start_generation(db,sv,'v1')
            for _ in range(3): self.observe(db,sv,g1,'OLD')
            self.run_cli('--db',str(db),'generation-succeed',g1)
            g2=self.start_generation(db,sv,'v2')
            for _ in range(3): self.observe(db,sv,g2,'FAILED_NEW')
            self.run_cli('--db',str(db),'generation-fail',g2,'--error','synthetic failure')
            status=json.loads(self.run_cli('--db',str(db),'generation-status','--source-version-id',sv))
            self.assertEqual(status['current_generation_id'],g1)
            cur=json.loads(self.run_cli('--db',str(db),'curate','--min-occurrences','3'))
            self.assertEqual(cur['count'],1)
            proposals=[json.loads(x) for x in self.run_cli('--db',str(db),'proposals').splitlines() if x.strip()]
            self.assertEqual(proposals[0]['key_text'],'text::OLD')
            self.assertNotIn('FAILED_NEW',[p['key_text'] for p in proposals])
            with sqlite3.connect(db) as c:
                after=c.execute('SELECT source_id,path,sha256,size_bytes,created_at FROM source_versions WHERE id=?',(sv,)).fetchone()
            self.assertEqual(original,after)
            self.run_cli_fail('--db',str(db),'observe','--source-version-id',sv,'--generation-id',g1,'--kind','text','--value','late','--confidence','0.9','--detector','test')
            val=json.loads(self.run_cli('--db',str(db),'validate'))
            self.assertEqual(val['status'],'PASS')
    def test_new_successful_generation_atomically_becomes_current(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); db=root/'db.sqlite3'; src=root/'sample.txt'; src.write_text('source')
            self.run_cli('--db',str(db),'init')
            sv=json.loads(self.run_cli('--db',str(db),'ingest',str(src),'--source-id','S1'))['source_version_id']
            g1=self.start_generation(db,sv,'v1'); self.observe(db,sv,g1,'A'); self.run_cli('--db',str(db),'generation-succeed',g1)
            g2=self.start_generation(db,sv,'v2'); self.observe(db,sv,g2,'B'); self.run_cli('--db',str(db),'generation-succeed',g2)
            status=json.loads(self.run_cli('--db',str(db),'generation-status','--source-version-id',sv))
            self.assertEqual(status['current_generation_id'],g2)
            self.assertEqual([g['state'] for g in status['generations']],['SUCCEEDED','SUCCEEDED'])
            val=json.loads(self.run_cli('--db',str(db),'validate'))
            self.assertEqual(val['status'],'PASS')
if __name__=='__main__': unittest.main()
