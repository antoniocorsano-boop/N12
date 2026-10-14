import json
import unittest
from pathlib import Path

from cew_b01.source_contract import (
    FROZEN_N12_TAV5,
    SourceContract,
    SourceContractError,
    load_source_contract,
    validate_frozen_n12_tav5,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "governance" / "cew-b01" / "N12_TAV5_SOURCE_v1.json"

EXPECTED = {
    "repository": "antoniocorsano-boop/N12",
    "commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
    "path": "archive/documentazione_originaria/tavola 5.pdf",
    "git_blob_sha": "ec32cd621877e9037cb26ebc083164140a8e3e68",
    "sha256": "2143b256511788691291cef533559306fc2988c7cb59a16d49cf86d1d7e94c7f",
    "page_index": 0,
    "source_role": "PRIMARY_IMMUTABLE_QUALIFICATION_SOURCE",
}


class SourceContractTests(unittest.TestCase):
    def test_governed_contract_contains_only_frozen_fields(self):
        raw = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(raw, EXPECTED)
        self.assertEqual(set(raw), set(EXPECTED))
        contract = load_source_contract(CONTRACT_PATH)
        validate_frozen_n12_tav5(contract)
        self.assertEqual(contract.to_mapping(), EXPECTED)
        self.assertEqual(FROZEN_N12_TAV5, EXPECTED)

    def test_rejects_mutable_branch_only_commit(self):
        bad = dict(EXPECTED, commit="main")
        with self.assertRaises(SourceContractError):
            SourceContract.from_mapping(bad)

    def test_rejects_wrong_governed_commit(self):
        bad = SourceContract.from_mapping(dict(EXPECTED, commit="0" * 40))
        with self.assertRaises(SourceContractError):
            validate_frozen_n12_tav5(bad)

    def test_rejects_wrong_governed_blob(self):
        bad = SourceContract.from_mapping(dict(EXPECTED, git_blob_sha="1" * 40))
        with self.assertRaises(SourceContractError):
            validate_frozen_n12_tav5(bad)

    def test_rejects_wrong_governed_sha256(self):
        bad = SourceContract.from_mapping(dict(EXPECTED, sha256="2" * 64))
        with self.assertRaises(SourceContractError):
            validate_frozen_n12_tav5(bad)

    def test_rejects_extra_fields(self):
        bad = dict(EXPECTED, branch="archive")
        with self.assertRaises(SourceContractError):
            SourceContract.from_mapping(bad)


if __name__ == "__main__":
    unittest.main()
