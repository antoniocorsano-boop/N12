import json, subprocess, sys, tempfile, unittest
from pathlib import Path

CLI=Path(__file__).resolve().parents[1]/'cli.py'
class DocIntelTests(unittest.TestCase):
    def run_cli(self,*args):
        r=subprocess.run([sys.executable,str(CLI),*args],text=True,capture_output=True,check=True)
        return r.stdout.strip()
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); db=root/'db.sqlite3'; src=root/'sample.txt'; src.write_text('25/70')
            self.run_cli('--db',str(db),'init')
            out=json.loads(self.run_cli('--db',str(db),'ingest',str(src),'--source-id','S1'))
            sv=out['source_version_id']
            for _ in range(3):
                self.run_cli('--db',str(db),'observe','--source-version-id',sv,'--kind','text','--value','25/70','--confidence','0.9','--detector','test')
            cur=json.loads(self.run_cli('--db',str(db),'curate','--min-occurrences','3'))
            self.assertEqual(cur['count'],1)
            val=json.loads(self.run_cli('--db',str(db),'validate'))
            self.assertEqual(val['status'],'PASS'); self.assertEqual(val['canonical_promotion'],'DISABLED')
if __name__=='__main__': unittest.main()
