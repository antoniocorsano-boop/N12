from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

try:
    from experiments.cew_col03d.member_verification import (
        HISTORICAL_MEMBER_ROOT,
        HISTORICAL_TRANSPORT_ROOT,
        REQUIRED_MEMBER_CONTRACTS,
        reconstruct_required_member_directory,
        verify_member_bytes,
        verify_required_member_directory,
    )
except (ImportError, ModuleNotFoundError):
    HISTORICAL_MEMBER_ROOT = None
    HISTORICAL_TRANSPORT_ROOT = None
    REQUIRED_MEMBER_CONTRACTS = None
    reconstruct_required_member_directory = None
    verify_member_bytes = None
    verify_required_member_directory = None


EXPECTED = {
    "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv": (4564, "3226fd19cc6a9fc7ff52d5c95d28f16f72b7b173e3b9d3a7403d5dbbb74107a6", "f5b62a8f"),
    "ABACO_TOPOLOGICO_TAV5_v11.csv": (2852, "186345c8227945003e8ed57cdc6bc9d93a4f2c22ecfbbfe0af0e3e415cd1b442", "5d428214"),
    "ABACO_TRAVI_TAV6_v23.csv": (8240, "48d48e014718b3d951fd1c4c5669f149203e684306ebf7933c3e2a16c95182bb", "0f53d534"),
    "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv": (7279, "18ac263085b1da832346f8280d9788ad30708bb76cff99d19ee127858a38ee1e", "c1e1136e"),
    "MATRICE_PILASTRI_27x5_v22.csv": (6349, "a77de6b5f1310b8e0662f35f5381b656a134f36ffd92c24b8bbaf74b9cc89ce1", "816694d0"),
    "TAV5_CARPENTERIA.dxf": (717875, "f8daddb352ac52399f83d34995dada371ab8940d4866baa9d5acaa913b67e3ec", "02ca74cf"),
    "TAV6_TRAVI.dxf": (379309, "770eda8e5cf37f386427229aba68e414a3da3b6bda81f6cd557cf11cea1d14c1", "66e49298"),
    "TAV7_PILASTRI.dxf": (454309, "6ab095fee72db4f5163dac6cc85e04b8b47e6b54a9f4d8090a9c515512bec47d", "944223a9"),
}


class HistoricalMemberVerificationTests(unittest.TestCase):
    def test_required_member_contracts_match_recovered_package_bytes(self):
        self.assertIsNotNone(REQUIRED_MEMBER_CONTRACTS, "COL-03D member verification missing")
        actual = {
            row["artifact_name"]: (row["size_bytes"], row["sha256"], row["package_crc32"])
            for row in REQUIRED_MEMBER_CONTRACTS
        }
        self.assertEqual(actual, EXPECTED)
        self.assertTrue(all(row["transport_encoding"] == "XZ_BASE64" for row in REQUIRED_MEMBER_CONTRACTS))
        self.assertTrue(all(row["authority"] == "HISTORICAL_DERIVED_EVIDENCE" for row in REQUIRED_MEMBER_CONTRACTS))
        self.assertTrue(all(row["promotion_authorized"] is False for row in REQUIRED_MEMBER_CONTRACTS))

    def test_checkout_transport_reconstructs_all_eight_exact_members(self):
        self.assertIsNotNone(reconstruct_required_member_directory, "COL-03D lossless transport reconstruction missing")
        self.assertEqual(HISTORICAL_TRANSPORT_ROOT, "archive/historical_packages/v25/transport")
        self.assertEqual(HISTORICAL_MEMBER_ROOT, "archive/historical_packages/v25/members")
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "members"
            rows = reconstruct_required_member_directory(
                Path(HISTORICAL_TRANSPORT_ROOT), target, REQUIRED_MEMBER_CONTRACTS
            )
            self.assertEqual([row["artifact_name"] for row in rows], sorted(EXPECTED))
            self.assertTrue(all(row["materialization_state"] == "MATERIALIZED_VERIFIED" for row in rows))
            self.assertTrue(all(row["transport_reconstruction_state"] == "LOSSLESS_RECONSTRUCTED" for row in rows))
            verified = verify_required_member_directory(target, REQUIRED_MEMBER_CONTRACTS)
            self.assertEqual(rows, verified)

    def test_changed_member_bytes_fail_as_provenance_mismatch(self):
        self.assertIsNotNone(verify_member_bytes, "COL-03D member verification missing")
        contract = next(row for row in REQUIRED_MEMBER_CONTRACTS if row["artifact_name"] == "TAV7_PILASTRI.dxf")
        with self.assertRaisesRegex(ValueError, "PROVENANCE_MISMATCH"):
            verify_member_bytes(contract["artifact_name"], b"changed", contract)

    def test_missing_transport_payload_fails_closed(self):
        self.assertIsNotNone(reconstruct_required_member_directory, "COL-03D lossless transport reconstruction missing")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "REQUIRED_MEMBER_TRANSPORT_NOT_FOUND"):
                reconstruct_required_member_directory(Path(tmp), Path(tmp) / "out", REQUIRED_MEMBER_CONTRACTS)

    def test_verification_order_is_contract_order_independent(self):
        self.assertIsNotNone(reconstruct_required_member_directory, "COL-03D lossless transport reconstruction missing")
        with tempfile.TemporaryDirectory() as tmp:
            target_a = Path(tmp) / "a"
            target_b = Path(tmp) / "b"
            forward = reconstruct_required_member_directory(
                Path(HISTORICAL_TRANSPORT_ROOT), target_a, REQUIRED_MEMBER_CONTRACTS
            )
            reverse = reconstruct_required_member_directory(
                Path(HISTORICAL_TRANSPORT_ROOT), target_b, list(reversed(REQUIRED_MEMBER_CONTRACTS))
            )
            self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
