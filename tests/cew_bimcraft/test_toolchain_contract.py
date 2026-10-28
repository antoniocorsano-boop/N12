from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from cew_bimcraft.contracts import (
    BIMCraftContractError,
    load_toolchain_contract,
    verify_asset_identity,
)


CONTRACT_PATH = Path("governance/cew-bimcraft-01/BIMCRAFT_TOOLCHAIN_v1.json")


class BIMCraftToolchainContractTests(unittest.TestCase):
    def test_frozen_upstream_identity_and_authority_boundary(self) -> None:
        contract = load_toolchain_contract(CONTRACT_PATH)

        self.assertEqual(contract.release, "v0.9.0")
        self.assertEqual(
            contract.upstream_commit_sha,
            "c7ba8e2db8d7cc9fbf0847f23c8a56c8e02193f5",
        )
        self.assertEqual(
            contract.asset_sha256,
            "69aef919a17f7916d3d3b5ab278cb16e27875669bf6b11c0815387d769b57c6f",
        )
        self.assertEqual(contract.adoption_state, "BENCHMARK")
        self.assertFalse(contract.canonical_write_authorized)
        self.assertFalse(contract.structural_identity_authorized)
        self.assertFalse(contract.fem_authorized)
        self.assertFalse(contract.master_change_authorized)
        self.assertFalse(contract.n12_stage_b_authorized)

    def test_wrong_asset_bytes_fail_closed(self) -> None:
        contract = load_toolchain_contract(CONTRACT_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / contract.asset_name
            candidate.write_bytes(b"not-the-frozen-bimcraft-asset")
            with self.assertRaisesRegex(
                BIMCraftContractError,
                "BIMCRAFT_ASSET_SHA256_MISMATCH",
            ):
                verify_asset_identity(contract, candidate)

    def test_contract_file_is_stable_json_and_contains_no_adoption_authority(self) -> None:
        raw = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(raw["adoption_state"], "BENCHMARK")
        self.assertEqual(raw["project_file_policy"]["canonical_authority"], False)
        self.assertTrue(raw["project_file_policy"]["regenerable_projection_only"])
        self.assertEqual(set(raw["authority"].values()), {False})
        self.assertEqual(len(hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()), 64)

    def test_cli_execution_asset_is_exact_release_tarball(self) -> None:
        raw = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cli = raw["cli_asset"]
        self.assertEqual(cli["platform"], "linux-x86_64")
        self.assertEqual(cli["name"], "bimcraft-0.9.0-linux-x86_64.tar.gz")
        self.assertEqual(
            cli["sha256"],
            "73ba200369b3f9afa95309ff74c1e873d80f27f2c054ddf6df9a0fdeb5cfccd8",
        )
        self.assertEqual(cli["binary"], "bin/bimcraft-cli")

    def test_ifc_validator_is_pinned(self) -> None:
        raw = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        validator = raw["ifc_validator"]
        self.assertEqual(validator["package"], "ifcopenshell")
        self.assertEqual(validator["version"], "0.9.0.post1")
        self.assertEqual(validator["role"], "READ_QUERY_VALIDATE_IFC")


if __name__ == "__main__":
    unittest.main()
