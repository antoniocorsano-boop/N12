import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cew_platform_orchestrator", ROOT / "scripts" / "cew_platform_orchestrator.py")
ORCH = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ORCH)


class CEWPlatformOrchestratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queue, cls.policy, cls.registry, cls.contract, cls.checkpoint_contract = ORCH.load_state()
        cls.work_state = ORCH.load_work_state()

    def test_repository_contracts_validate(self):
        ok, errors = ORCH.validate()
        self.assertTrue(ok, errors)

    def test_runtime_state_is_separate_from_queue_definition(self):
        queue_pos2 = next(x for x in self.queue["items"] if x["id"] == "POS-002")
        self.assertEqual(queue_pos2["status"], "READY")
        self.assertEqual(self.work_state["items"]["POS-002"]["status"], "COMPLETE")
        effective = ORCH.apply_work_state(self.queue, self.work_state)
        effective_pos2 = next(x for x in effective["items"] if x["id"] == "POS-002")
        self.assertEqual(effective_pos2["status"], "COMPLETE")

    def test_serial_work_is_exclusive_when_runtime_marks_it_ready(self):
        state = copy.deepcopy(self.work_state)
        state["items"]["POS-002"]["status"] = "READY"
        for wid, value in state["items"].items():
            if wid not in {"POS-001", "POS-002"} and value["status"] == "READY":
                value["status"] = "WAITING"
        plan = ORCH.build_plan(self.queue, self.policy, self.registry, work_state=state)
        self.assertEqual([x["id"] for x in plan], ["POS-002"])
        self.assertEqual(plan[0]["execution"]["mode"], "SERIAL")

    def test_current_plan_is_lock_safe_dependency_complete_and_priority_ordered(self):
        plan = ORCH.build_plan(self.queue, self.policy, self.registry, work_state=self.work_state)
        self.assertTrue(plan)
        effective = ORCH.apply_work_state(self.queue, self.work_state)
        by_id = {x["id"]: x for x in effective["items"]}
        locks = []
        priorities = []
        for item in plan:
            source = by_id[item["id"]]
            self.assertEqual(source["status"], "READY")
            self.assertTrue(all(by_id[d]["status"] == "COMPLETE" for d in source.get("depends_on", [])))
            locks.extend(item["execution"]["locks"])
            priorities.append(item["priority"])
        self.assertEqual(len(locks), len(set(locks)))
        self.assertEqual(priorities, sorted(priorities))

    def test_lock_collision_prevents_unsafe_parallel_execution(self):
        queue = copy.deepcopy(self.queue)
        state = copy.deepcopy(self.work_state)
        by_id = {x["id"]: x for x in queue["items"]}
        for wid, value in state["items"].items():
            if wid in {"DOC-001", "ENT-001"}:
                value["status"] = "READY"
            elif value["status"] == "READY":
                value["status"] = "WAITING"
        state["items"]["POS-002"]["status"] = "COMPLETE"
        by_id["ENT-001"]["execution"]["locks"] = list(by_id["DOC-001"]["execution"]["locks"])
        plan = ORCH.build_plan(queue, self.policy, self.registry, work_state=state)
        ids = [x["id"] for x in plan]
        self.assertIn("DOC-001", ids)
        self.assertNotIn("ENT-001", ids)

    def test_cycle_detection_is_fail_closed(self):
        items = [
            {"id": "A", "depends_on": ["B"]},
            {"id": "B", "depends_on": ["C"]},
            {"id": "C", "depends_on": ["A"]},
        ]
        cycle = ORCH.dependency_cycle(items)
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle[0], cycle[-1])

    def test_runtime_completion_receipts_validate(self):
        errors = ORCH.validate_runtime_receipts(
            self.queue, self.work_state, self.policy, self.registry, self.contract
        )
        self.assertEqual(errors, [])

    def test_result_contract_accepts_registered_provider_selection(self):
        item = next(x for x in self.queue["items"] if x["id"] == "DOC-001")
        result = ORCH.result_template(item, self.registry)
        result.update({
            "outcome": "COMPLETE_PASS",
            "branch": "exp/test",
            "head_sha": "a" * 40,
            "input_generations": ["GEN-1"],
            "input_fingerprints": ["sha256:test"],
            "outputs": ["artifact.json"],
            "gates": [{"name": "unit", "status": "PASS"}],
            "next_eligible_action": "DOC-002",
        })
        errors = ORCH.validate_result_payload(result, self.queue, self.policy, self.registry, self.contract)
        self.assertEqual(errors, [])

    def test_result_contract_rejects_unregistered_provider(self):
        item = next(x for x in self.queue["items"] if x["id"] == "DOC-001")
        result = ORCH.result_template(item, self.registry)
        result.update({
            "outcome": "COMPLETE_PASS",
            "branch": "exp/test",
            "head_sha": "b" * 40,
            "input_generations": [],
            "input_fingerprints": [],
            "outputs": ["artifact.json"],
            "gates": [{"name": "unit", "status": "PASS"}],
        })
        result["selected_providers"]["source.identity"] = "invented-provider"
        errors = ORCH.validate_result_payload(result, self.queue, self.policy, self.registry, self.contract)
        self.assertTrue(any("source.identity" in error for error in errors), errors)

    def test_checkpoint_contract_supports_resume_without_becoming_completion(self):
        item = next(x for x in self.queue["items"] if x["id"] == "DOC-001")
        checkpoint = ORCH.checkpoint_template(item)
        checkpoint.update({
            "checkpoint_id": "CHK-DOC-001-1",
            "branch": "exp/test",
            "head_sha": "c" * 40,
            "input_fingerprints": ["sha256:test"],
            "completed_steps": ["DISCOVER"],
            "outputs_so_far": ["candidate.json"],
            "next_step": "EXECUTE generation migration",
        })
        errors = ORCH.validate_checkpoint_payload(checkpoint, self.queue, self.policy, self.checkpoint_contract)
        self.assertEqual(errors, [])
        self.assertNotIn("outcome", checkpoint)

    def test_capability_registry_has_alternative_specialist_providers(self):
        self.assertGreaterEqual(len(self.registry["capabilities"]["document.ocr_htr"]["providers"]), 2)
        self.assertGreaterEqual(len(self.registry["capabilities"]["analysis.fem"]["providers"]), 2)


if __name__ == "__main__":
    unittest.main()
