import re
import unittest
from pathlib import Path

PROD = Path('.github/workflows/cew-gate-authority.yml')
CHECKOUT='3d3c42e5aac5ba805825da76410c181273ba90b1'
SETUP='5fda3b95a4ea91299a34e894583c3862153e4b97'
UPLOAD='cf430e030ddbb5b0abf93d22962f4752f3646cd9'
DOWNLOAD='9000827ccba6bdab643e8b6fd33ac0654aef8333'

class ProductionWorkflowContractTests(unittest.TestCase):
    def text(self):
        self.assertTrue(PROD.is_file(), 'production workflow missing')
        return PROD.read_text()
    def test_only_workflow_dispatch_and_exact_inputs(self):
        t=self.text(); event=t.split('\npermissions:',1)[0]
        self.assertIn('workflow_dispatch:',event)
        for forbidden in ('pull_request:','pull_request_target:','push:','schedule:','workflow_run:','repository_dispatch:'):
            self.assertNotIn(forbidden,event)
        self.assertEqual(len(re.findall(r'^      (pr_number|candidate_sha):$',event,re.M)),2)
        self.assertIn('      pr_number:',event); self.assertIn('      candidate_sha:',event)
    def test_jobs_and_permissions_are_minimal(self):
        t=self.text(); self.assertNotIn(': write',t); self.assertNotIn('id-token:',t); self.assertNotIn('attestations:',t); self.assertNotIn('secrets.',t)
        for job in ('qualify:','verify-handoff:','decision:'): self.assertIn(f'  {job}',t)
        self.assertIn('      contents: read\n      pull-requests: read',t)
        self.assertIn('      actions: read',t)
    def test_candidate_is_never_checked_out(self):
        t=self.text()
        for m in re.finditer(r'uses: actions/checkout@[^\n]+',t):
            snippet=t[m.start():m.start()+300]; self.assertNotIn('inputs.candidate_sha',snippet); self.assertNotIn('candidate_sha }}',snippet)
        self.assertIn('python -m cew_gate_control_plane.cli fetch-candidate',t)
        self.assertIn('--destination "$RUNNER_TEMP/candidate.git"',t)
    def test_artifact_handoff_is_by_id_and_digest_error(self):
        t=self.text(); self.assertIn('artifact-ids:',t); self.assertIn('digest-mismatch: error',t); self.assertIn('overwrite: false',t); self.assertIn('if-no-files-found: error',t)
    def test_action_pins_are_exact_and_no_tag_forms(self):
        t=self.text()
        for repo,sha in [('actions/checkout',CHECKOUT),('actions/setup-python',SETUP),('actions/upload-artifact',UPLOAD),('actions/download-artifact',DOWNLOAD)]: self.assertIn(f'uses: {repo}@{sha}',t); self.assertNotRegex(t,rf'uses: {re.escape(repo)}@v\d')

if __name__=='__main__': unittest.main()
