import json
import unittest
from pathlib import Path

from experiments.cew_col03d.member_verification import REQUIRED_MEMBER_CONTRACTS


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "governance/cew-dxf01/CEW_DXF01_TOOLCHAIN_v1.json"
LOCK = ROOT / "requirements/cew-dxf01.lock.txt"


class Dxf01ContractTests(unittest.TestCase):
    def test_toolchain_contract_pins_direct_ezdxf_without_authority(self):
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "CEW_DXF01_TOOLCHAIN_v1")
        self.assertEqual(payload["successor_base_sha"], "c163c8ccea9594b31367a18d0451e232569dc534")
        self.assertEqual(payload["runtime"]["direct_dependency"], "ezdxf==1.4.5")
        self.assertFalse(payload["runtime"]["transitive_precedent_grants_qualification"])
        self.assertEqual(payload["authority"]["authority_effect"], "NONE")
        for key, value in payload["authority"].items():
            if key != "authority_effect":
                self.assertFalse(value, key)

    def test_dedicated_lock_has_one_direct_pin(self):
        pins = [
            line.strip()
            for line in LOCK.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(pins, ["ezdxf==1.4.5"])

    def test_source_scope_matches_recovered_package_contracts(self):
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        expected = {
            row["artifact_name"]: {
                "sha256": row["sha256"],
                "size_bytes": row["size_bytes"],
                "package_crc32": row["package_crc32"],
                "historical_role": row["qualified_role"],
                "evidentiary_class": row["authority"],
            }
            for row in REQUIRED_MEMBER_CONTRACTS
            if str(row["artifact_name"]).lower().endswith(".dxf")
        }
        observed = {
            row["artifact_name"]: {
                "sha256": row["sha256"],
                "size_bytes": row["size_bytes"],
                "package_crc32": row["package_crc32"],
                "historical_role": row["historical_role"],
                "evidentiary_class": row["evidentiary_class"],
            }
            for row in payload["source_scope"]
        }
        self.assertEqual(observed, expected)
        self.assertFalse(payload["authority"]["primary_source_identity_bridge"])
        self.assertIn(
            "USE_HISTORICAL_DXF_AS_COL03F_PRIMARY_IDENTITY_BRIDGE",
            payload["forbidden_actions"],
        )


if __name__ == "__main__":
    unittest.main()
