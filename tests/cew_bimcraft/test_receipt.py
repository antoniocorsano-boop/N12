from __future__ import annotations

from pathlib import Path
import unittest

from cew_bimcraft.command_plan import compile_command_plan, load_benchmark_fixture
from cew_bimcraft.contracts import load_toolchain_contract
from cew_bimcraft.receipt import build_benchmark_receipt
from cew_bimcraft.reconcile import reconcile_fixture


FIXTURE_PATH = Path(
    "governance/cew-bimcraft-01/fixtures/STAGE_A_STRUCTURAL_FIXTURE_v1.json"
)
CONTRACT_PATH = Path("governance/cew-bimcraft-01/BIMCRAFT_TOOLCHAIN_v1.json")
CATEGORY = {
    "structural_column": "structuralcolumn",
    "beam": "beam",
    "footing": "footing",
    "floor": "floor",
}


def exact_observations(fixture):
    return [
        {
            "object_id": obj.object_id,
            "category": CATEGORY[obj.command],
            "params": dict(obj.params),
            "provenance": dict(obj.provenance),
        }
        for obj in fixture.objects
    ]


class BIMCraftBenchmarkReceiptTests(unittest.TestCase):
    def test_pass_receipt_never_escalates_authority(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        contract = load_toolchain_contract(CONTRACT_PATH)
        plan = compile_command_plan(fixture)
        reconciliation = reconcile_fixture(fixture, exact_observations(fixture))

        receipt = build_benchmark_receipt(
            contract=contract,
            fixture=fixture,
            command_plan=plan,
            reconciliation=reconciliation,
            candidate_sha="a" * 40,
            observed_capabilities=("run", "commands", "info"),
            output_digests={"model": "b" * 64, "ifc": "c" * 64},
        )

        self.assertEqual(receipt.result, "PASS")
        self.assertEqual(receipt.command_plan_sha256, plan.sha256)
        self.assertEqual(receipt.asset_name, "bimcraft-0.9.0-linux-x86_64.tar.gz")
        self.assertEqual(
            receipt.asset_sha256,
            "73ba200369b3f9afa95309ff74c1e873d80f27f2c054ddf6df9a0fdeb5cfccd8",
        )
        self.assertEqual(receipt.executable_path, "bin/bimcraft-cli")
        self.assertFalse(receipt.canonical_write_authorized)
        self.assertFalse(receipt.structural_identity_authorized)
        self.assertFalse(receipt.fem_authorized)
        self.assertFalse(receipt.master_change_authorized)
        self.assertFalse(receipt.n12_stage_b_authorized)

    def test_reconciliation_failure_cannot_yield_pass(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        contract = load_toolchain_contract(CONTRACT_PATH)
        plan = compile_command_plan(fixture)
        observations = exact_observations(fixture)[:-1]
        reconciliation = reconcile_fixture(fixture, observations)

        receipt = build_benchmark_receipt(
            contract=contract,
            fixture=fixture,
            command_plan=plan,
            reconciliation=reconciliation,
            candidate_sha="a" * 40,
            observed_capabilities=("run",),
            output_digests={},
        )
        self.assertEqual(receipt.result, "REWORK")
        self.assertGreater(receipt.difference_count, 0)

    def test_receipt_serialization_contains_required_false_flags(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        contract = load_toolchain_contract(CONTRACT_PATH)
        plan = compile_command_plan(fixture)
        reconciliation = reconcile_fixture(fixture, exact_observations(fixture))
        receipt = build_benchmark_receipt(
            contract=contract,
            fixture=fixture,
            command_plan=plan,
            reconciliation=reconciliation,
            candidate_sha="a" * 40,
            observed_capabilities=(),
            output_digests={},
        )
        payload = receipt.as_dict()
        for key in (
            "canonical_write_authorized",
            "structural_identity_authorized",
            "fem_authorized",
            "master_change_authorized",
            "n12_stage_b_authorized",
        ):
            self.assertIs(payload[key], False)
        self.assertEqual(payload["adoption_state"], "BENCHMARK")


if __name__ == "__main__":
    unittest.main()
