import json, tempfile, unittest
from pathlib import Path
from cew_gate_control_plane.cli import main
from cew_gate_control_plane.decision import FinalDecision, reduce_decision
H="a"*40
class DecisionReducerTests(unittest.TestCase):
    def test_exit_0_and_verified_handoff_is_success(self): self.assertEqual(reduce_decision(qualify_job_result="success",qualification_exit_code=0,receipt_emitted=True,handoff_job_result="success"),FinalDecision("QUALIFIED",True,None))
    def test_exit_1_and_verified_handoff_is_not_qualified(self): self.assertEqual(reduce_decision(qualify_job_result="success",qualification_exit_code=1,receipt_emitted=True,handoff_job_result="success").failure_code,"NOT_QUALIFIED")
    def test_exit_2_is_control_plane_error(self): self.assertEqual(reduce_decision(qualify_job_result="success",qualification_exit_code=2,receipt_emitted=False,handoff_job_result="skipped").failure_code,"CONTROL_PLANE_OR_INVOCATION_ERROR")
    def test_missing_expected_receipt_fails(self): self.assertEqual(reduce_decision(qualify_job_result="success",qualification_exit_code=0,receipt_emitted=False,handoff_job_result="success").failure_code,"RECEIPT_NOT_EMITTED")
    def test_failed_or_skipped_handoff_fails(self):
        for r in ("failure","skipped","cancelled"):
            with self.subTest(result=r): self.assertFalse(reduce_decision(qualify_job_result="success",qualification_exit_code=0,receipt_emitted=True,handoff_job_result=r).success)
    def test_unknown_or_failed_qualify_state_fails(self):
        for r in ("failure","cancelled","mystery"):
            with self.subTest(result=r): self.assertEqual(reduce_decision(qualify_job_result=r,qualification_exit_code=None,receipt_emitted=False,handoff_job_result="skipped").failure_code,"CONTROL_PLANE_OR_INVOCATION_ERROR")
class CliIntegrationTests(unittest.TestCase):
    def out(self): return Path(tempfile.mkdtemp())/"out.json"
    def test_preflight_writes_normalized_json(self):
        o=self.out(); rc=main(["preflight","--repository","antoniocorsano-boop/N12","--ref","refs/heads/main","--ref-type","branch","--pr-number","148","--candidate-sha",H,"--output-json",str(o)]); self.assertEqual(rc,0); d=json.loads(o.read_text()); self.assertEqual(d["pr_number"],148); self.assertEqual(d["candidate_sha"],H)
    def test_preflight_failure_writes_stable_code(self):
        o=self.out(); rc=main(["preflight","--repository","antoniocorsano-boop/N12","--ref","refs/heads/dev","--ref-type","branch","--pr-number","148","--candidate-sha",H,"--output-json",str(o)]); self.assertEqual(rc,2); self.assertEqual(json.loads(o.read_text())["failure_code"],"NON_CANONICAL_CONTROL_PLANE_REF")
    def test_decision_cli_returns_zero_only_for_qualified(self):
        o=self.out(); self.assertEqual(main(["decision","--qualify-job-result","success","--qualification-exit-code","0","--receipt-emitted","true","--handoff-job-result","success","--output-json",str(o)]),0); self.assertTrue(json.loads(o.read_text())["success"]); o=self.out(); self.assertEqual(main(["decision","--qualify-job-result","success","--qualification-exit-code","1","--receipt-emitted","true","--handoff-job-result","success","--output-json",str(o)]),1); self.assertEqual(json.loads(o.read_text())["failure_code"],"NOT_QUALIFIED")
    def test_all_required_subcommands_are_present(self):
        for c in ("preflight","fetch-candidate","verify-trust","build-handoff","verify-handoff","decision"):
            with self.subTest(command=c):
                with self.assertRaises(SystemExit) as x: main([c,"--help"])
                self.assertEqual(x.exception.code,0)
if __name__=="__main__": unittest.main()
