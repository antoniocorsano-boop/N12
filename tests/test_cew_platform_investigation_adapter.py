import unittest
from copy import deepcopy

from scripts import cew_platform_investigation_adapter as adapter


class InvestigationPlatformAdapterTests(unittest.TestCase):
    def setUp(self):
        self.contract = adapter.load(adapter.CONTRACT_PATH)
        self.plan = {
            "project_id": "TEST",
            "status": "ADVISORY_PLAN_NOT_EVIDENCE",
            "value_of_information_ready": False,
            "blocker_count": 1,
            "covered_blocker_count": 1,
            "uncovered_blockers": [],
            "candidates": [{
                "investigation_id": "INV-A",
                "target_domain": "MATERIAL",
                "candidate_class": "LABORATORY_TEST",
                "method": "test",
                "expected_uncertainty_reduction": "HIGH",
                "invasiveness": "MEDIUM",
                "relative_cost": "MEDIUM",
                "dependency_ids": [],
                "potentially_closes": ["B-1"],
                "unlocks": ["assessment"],
                "decision_state": "CANDIDATE",
                "ranking_status": "ADVISORY_NOT_VALUE_OF_INFORMATION",
            }],
        }

    def test_advisory_plan_is_adoptable_without_becoming_evidence(self):
        package = adapter.adoption_package(self.plan, self.contract)
        self.assertEqual(package["status"], "PASS")
        self.assertFalse(package["planner_creates_evidence"])
        self.assertFalse(package["planner_assigns_engineering_values"])
        self.assertTrue(package["human_selection_required_before_project_execution"])

    def test_voi_gate_is_closed_without_declared_decision_model(self):
        gate = adapter.voi_gate(self.contract)
        self.assertEqual(gate["status"], "NOT_READY")
        self.assertIn("decision_variable", gate["missing"])
        self.assertIn("test_likelihood_model", gate["missing"])

    def test_voi_gate_opens_only_when_all_contract_fields_exist(self):
        required = self.contract["future_voi_gate"]["required_before_activation"]
        gate = adapter.voi_gate(self.contract, {field: {"declared": True} for field in required})
        self.assertEqual(gate["status"], "READY")
        self.assertEqual(gate["missing"], [])
        self.assertEqual(gate["activation_authority"], "HUMAN_ENGINEERING_REVIEW_REQUIRED")

    def test_accidental_voi_claim_fails_closed(self):
        bad = deepcopy(self.plan)
        bad["value_of_information_ready"] = True
        ok, errors = adapter.validate_advisory_plan(bad, self.contract)
        self.assertFalse(ok)
        self.assertTrue(any("must not claim Value of Information" in e for e in errors))

    def test_candidate_without_blocker_binding_fails_closed(self):
        bad = deepcopy(self.plan)
        bad["candidates"][0]["potentially_closes"] = []
        ok, errors = adapter.validate_advisory_plan(bad, self.contract)
        self.assertFalse(ok)
        self.assertTrue(any("not bound to an unresolved blocker" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
