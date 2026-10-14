import json
import tempfile
import unittest
from pathlib import Path

from cew_gate_control_plane.cli import main
from cew_gate_control_plane.decision import FinalDecision, reduce_decision

H="a"*40

class DecisionReducerTests(unittest.TestCase):
    def test_exit_0_and_verified_handoff_is_success(self):
        self.assertEqual(reduce_decision(qualify_job_result="success",qualification_exit_code=0,receipt_emitted=True,handoff_job_result="success"),FinalDecision("QUALIFIED",True,None))
    def test_exit_1_and_verified_handoff_is_not_qualified(self):
        self.assertEqual(reduce_decision(qualify_job_result="success",qualification_exit_code=1,receipt_emitted=True,handoff_job_result="success").failure_code,"NOT_QUALIFIED")
    def test_exit_2_is_control_plane_error(self):
        self.assertEqual(reduce_decision(qualify_job_result="success",qualification_exit_code=2,receipt_emitted=False,handoff_job_result="skipped").failure_code,"CONTROL_PLANE_OR_INVOCATION_ERROR")
    def test_missing_expected_receipt_fails(self):
        self.assertEqual(reduce_decision(qualify_job_result="success",qualification_exit_code=0,receipt_emitted=False,handoff_job_result="success").failure_code,"RECEIPT_NOT_EMITTED")
    def test_failed_or_skipped_handoff_fails(self):
        for result in ("failure","skipped","cancelled"):
            with self.subTest(result=result): self.assertFalse(reduce_decision(qualify_job_result="success",qualification_exit_code=0,receipt_emitted=True,handoff_job_result=result).success)
    def test_unknown_or_failed_qualify_state_fails(self):
        for result in ("failure","cancelled","mystery"):
            with self.subTest(result=result): self.assertEqual(reduce_decision(qualify_job_result=result,qualification_exit_code=None,receipt_emitted=False,handoff_job_result="skipped").failure_code,"CONTROL_PLANE_OR_INVOCATION_ERROR")
    def test_type_confused_exit_code_or_receipt_flag_fails_closed(self):
        for exit_code in (True, False, "0", 1.0):
            with self.subTest(exit_code=exit_code):
                decision=reduce_decision(qualify_job_result="success",qualification_exit_code=exit_code,receipt_emitted=True,handoff_job_result="success")
                self.assertFalse(decision.success)
                self.assertEqual(decision.failure_code,"CONTROL_PLANE_OR_INVOCATION_ERROR")
        for emitted in (1, 0, "true", None):
            with self.subTest(receipt_emitted=emitted):
                decision=reduce_decision(qualify_job_result="success",qualification_exit_code=0,receipt_emitted=emitted,handoff_job_result="success")
                self.assertFalse(decision.success)
                self.assertEqual(decision.failure_code,"CONTROL_PLANE_OR_INVOCATION_ERROR")

class CliIntegrationTests(unittest.TestCase):
    def out(self): return Path(tempfile.mkdtemp())/"out.json"
    def test_preflight_writes_normalized_json(self):
        out=self.out(); rc=main(["preflight","--repository","antoniocorsano-boop/N12","--ref","refs/heads/main","--ref-type","branch","--pr-number","148","--candidate-sha",H,"--output-json",str(out)])
        self.assertEqual(rc,0); data=json.loads(out.read_text()); self.assertEqual(data["pr_number"],148); self.assertEqual(data["candidate_sha"],H)
    def test_preflight_failure_writes_stable_code(self):
        out=self.out(); rc=main(["preflight","--repository","antoniocorsano-boop/N12","--ref","refs/heads/dev","--ref-type","branch","--pr-number","148","--candidate-sha",H,"--output-json",str(out)])
        self.assertEqual(rc,2); self.assertEqual(json.loads(out.read_text())["failure_code"],"NON_CANONICAL_CONTROL_PLANE_REF")
    def test_malformed_provided_integer_writes_stable_json_failure(self):
        out=self.out(); rc=main(["preflight","--repository","antoniocorsano-boop/N12","--ref","refs/heads/main","--ref-type","branch","--pr-number","1.5","--candidate-sha",H,"--output-json",str(out)])
        self.assertEqual(rc,2); self.assertEqual(json.loads(out.read_text())["failure_code"],"INVALID_DISPATCH_INPUT")
    def test_decision_cli_returns_zero_only_for_qualified(self):
        out=self.out(); rc=main(["decision","--qualify-job-result","success","--qualification-exit-code","0","--receipt-emitted","true","--handoff-job-result","success","--output-json",str(out)])
        self.assertEqual(rc,0); self.assertTrue(json.loads(out.read_text())["success"])
        out=self.out(); rc=main(["decision","--qualify-job-result","success","--qualification-exit-code","1","--receipt-emitted","true","--handoff-job-result","success","--output-json",str(out)])
        self.assertEqual(rc,1); self.assertEqual(json.loads(out.read_text())["failure_code"],"NOT_QUALIFIED")
    def test_all_required_subcommands_are_present(self):
        for command in ("preflight","fetch-candidate","verify-trust","build-handoff","verify-handoff","decision"):
            with self.subTest(command=command):
                with self.assertRaises(SystemExit) as ctx: main([command,"--help"])
                self.assertEqual(ctx.exception.code,0)

if __name__=="__main__": unittest.main()
