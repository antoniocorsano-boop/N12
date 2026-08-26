import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CLI=ROOT/'cli.py'; LEARN=ROOT/'symbol_learning.py'
class SymbolLearningTests(unittest.TestCase):
    def run_prog(self,prog,*args):
        return subprocess.run([sys.executable,str(prog),*args],text=True,capture_output=True,check=True).stdout.strip()
    def test_label_dataset(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); db=d/'db.sqlite3'; src=d/'s.txt'; src.write_text('x')
            self.run_prog(CLI,'--db',str(db),'init')
            sv=json.loads(self.run_prog(CLI,'--db',str(db),'ingest',str(src),'--source-id','S'))['source_version_id']
            gid=json.loads(self.run_prog(CLI,'--db',str(db),'generation-start','--source-version-id',sv,'--processor','test','--processor-version','v1'))['generation_id']
            obs=self.run_prog(CLI,'--db',str(db),'observe','--source-version-id',sv,'--generation-id',gid,'--kind','symbol','--bbox','10,20,30,40','--value','rect','--confidence','0.9','--detector','test')
            self.run_prog(CLI,'--db',str(db),'generation-succeed',gid)
            self.run_prog(LEARN,'--db',str(db),'label',obs,'--meaning','COLUMN_PLAN_MARKER','--verdict','POSITIVE','--reviewer','human','--context','{"drawing_type":"carpenteria"}')
            s=json.loads(self.run_prog(LEARN,'--db',str(db),'stats'))
            self.assertEqual(s[0]['meaning'],'COLUMN_PLAN_MARKER'); self.assertEqual(s[0]['n'],1)
            ex=json.loads(self.run_prog(LEARN,'--db',str(db),'examples','--meaning','COLUMN_PLAN_MARKER'))
            self.assertEqual(ex[0]['observation_id'],obs); self.assertEqual(ex[0]['source_version_id'],sv)
            self.assertEqual(ex[0]['generation_id'],gid)
if __name__=='__main__': unittest.main()
