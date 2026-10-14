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
        t=self.text();
        for m in re.finditer(r'uses: actions/checkout@[^\n]+',t):
            snippet=t[m.start():m.start()+300]; self.assertNotIn('inputs.candidate_sha',snippet); self.assertNotIn('candidate_sha }}',snippet)
        self.assertIn('python -m cew_gate_control_plane.cli fetch-candidate',t)
        self.assertIn('--destination "$RUNNER_TEMP/candidate.git"',t)
    def test_verify_handoff_job_never_reads_or_fetches_candidate(self):
        t=self.text()
        verify=t.split('\n  verify-handoff:\n',1)[1].split('\n  decision:\n',1)[0]
        for forbidden in ('fetch-candidate','candidate.git','refs/pull/','cew_gate_authority.cli qualify','--candidate-git-dir'):
            self.assertNotIn(forbidden,verify)

    def test_promoted_g0_executes_from_exact_materialized_directory(self):
        t=self.text()
        self.assertIn('cd "$RUNNER_TEMP/g0"', t)
        self.assertNotIn('PYTHONPATH="$RUNNER_TEMP/g0" python -m cew_gate_authority.cli qualify', t)

    def test_b_layer_executes_from_exact_materialized_base(self):
        t=self.text()
        self.assertGreaterEqual(t.count('cd "$RUNNER_TEMP/control-plane"'), 2)
        self.assertNotIn('PYTHONPATH="$RUNNER_TEMP/control-plane"', t)

    def test_artifact_handoff_is_by_id_and_digest_error(self):
        t=self.text(); self.assertIn('artifact-ids:',t); self.assertIn('digest-mismatch: error',t); self.assertIn('overwrite: false',t); self.assertIn('if-no-files-found: error',t)
    def test_action_pins_are_exact_and_no_tag_forms(self):
        t=self.text()
        for repo,sha in [('actions/checkout',CHECKOUT),('actions/setup-python',SETUP),('actions/upload-artifact',UPLOAD),('actions/download-artifact',DOWNLOAD)]: self.assertIn(f'uses: {repo}@{sha}',t); self.assertNotRegex(t,rf'uses: {re.escape(repo)}@v\d')

if __name__=='__main__': unittest.main()

VALIDATE = Path('.github/workflows/validate-cew-gate-authority-task9.yml')

class ValidationWorkflowContractTests(unittest.TestCase):
    def text(self):
        self.assertTrue(VALIDATE.is_file(), 'validation workflow missing')
        return VALIDATE.read_text()

    def test_validation_is_pr_only_and_read_only(self):
        t=self.text(); event=t.split('\npermissions:',1)[0]
        self.assertIn('pull_request:', event)
        self.assertNotIn('workflow_dispatch:', event)
        self.assertNotIn(': write', t)
        self.assertNotIn('secrets.', t)
        self.assertIn('permissions:\n  contents: read', t)

    def test_validation_checks_out_exact_pr_head(self):
        t=self.text()
        self.assertIn(f'uses: actions/checkout@{CHECKOUT}', t)
        self.assertIn('ref: ${{ github.event.pull_request.head.sha }}', t)
        self.assertIn('persist-credentials: false', t)

    def test_validation_fetches_operational_commit_before_g0_suite(self):
        t=self.text()
        fetch='git fetch --no-tags --depth=1 origin d806dcca72779b5a186defe557a7a9b739575a90'
        suite="python -m unittest discover -s tests/cew_gate_authority -p 'test_*.py' -v"
        self.assertIn(fetch, t)
        self.assertLess(t.index(fetch), t.index(suite))

    def test_validation_does_not_invoke_production_qualification(self):
        t=self.text()
        self.assertNotIn('gh workflow run', t)
        self.assertNotIn('/dispatches', t)
        self.assertNotIn('fetch-candidate', t)
        self.assertNotIn('cew_gate_authority.cli qualify', t)

    def test_codeql_is_analysis_only_without_upload(self):
        t=self.text()
        self.assertIn('github/codeql-action/analyze@24c54180a607b1449ed407dd24f251e4e9147c8d', t)
        self.assertIn('upload: never', t)
        self.assertIn('upload-database: false', t)
