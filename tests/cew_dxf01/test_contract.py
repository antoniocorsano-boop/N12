import json
import unittest
from pathlib import Path


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

    def test_source_scope_is_exact_and_historical_only(self):
        payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
        observed = {
            row["artifact_name"]: (row["sha256"], row["size_bytes"], row["evidentiary_class"])
            for row in payload["source_scope"]
        }
        self.assertEqual(
            observed,
            {
                "N12_TAV7_PILASTRI.dxf": (
                    "c61731902df0d42266487ca77954af75dc2f0912f3bce94f3e81e2b48cecbd57",
                    454818,
                    "HISTORICAL_DERIVED_REFERENCE",
                ),
                "N12_TAV6_TIPO.dxf": (
                    "78d0a7a58785edd586e1115b7d8ae820436c22e24dfc7d7f2cbd81914de78afb",
                    493006,
                    "HISTORICAL_DERIVED_REFERENCE",
                ),
                "N12_TAV5A_QUARTO.dxf": (
                    "f3c525ccb6926d80157db5b106f615dc0ff752c5d827b485f4d1e90fb8263e52",
                    470016,
                    "HISTORICAL_DERIVED_REFERENCE",
                ),
            },
        )
        self.assertFalse(payload["authority"]["primary_source_identity_bridge"])
        self.assertIn(
            "USE_HISTORICAL_DXF_AS_COL03F_PRIMARY_IDENTITY_BRIDGE",
            payload["forbidden_actions"],
        )


if __name__ == "__main__":
    unittest.main()
