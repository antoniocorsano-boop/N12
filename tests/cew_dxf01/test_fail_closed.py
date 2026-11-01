import tempfile
import unittest
from pathlib import Path

from experiments.cew_col03d.member_verification import (
    HISTORICAL_TRANSPORT_ROOT,
    REQUIRED_MEMBER_CONTRACTS,
    reconstruct_required_member_directory,
)

try:
    from experiments.cew_dxf01.reader import read_dxf_path
except (ImportError, ModuleNotFoundError):
    read_dxf_path = None


ROOT = Path(__file__).resolve().parents[2]
DXF_CONTRACT = next(
    row for row in REQUIRED_MEMBER_CONTRACTS if row["artifact_name"] == "TAV7_PILASTRI.dxf"
)


class Dxf01FailClosedContractTests(unittest.TestCase):
    def test_provenance_mismatch_fails_before_structured_query(self):
        self.assertIsNotNone(
            read_dxf_path,
            "CEW-DXF-01 RED: read-only exact-source guard is not implemented",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reconstruct_required_member_directory(
                ROOT / HISTORICAL_TRANSPORT_ROOT,
                root,
                contracts=(DXF_CONTRACT,),
            )
            path = root / DXF_CONTRACT["artifact_name"]
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "PROVENANCE_MISMATCH"):
                read_dxf_path(
                    path,
                    artifact_name=DXF_CONTRACT["artifact_name"],
                    expected_sha256=DXF_CONTRACT["sha256"],
                    expected_size_bytes=DXF_CONTRACT["size_bytes"],
                )

    def test_wrong_declared_artifact_name_fails_closed(self):
        self.assertIsNotNone(read_dxf_path)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reconstruct_required_member_directory(
                ROOT / HISTORICAL_TRANSPORT_ROOT,
                root,
                contracts=(DXF_CONTRACT,),
            )
            path = root / DXF_CONTRACT["artifact_name"]
            with self.assertRaisesRegex(ValueError, "ARTIFACT_NAME_MISMATCH"):
                read_dxf_path(
                    path,
                    artifact_name="WRONG.dxf",
                    expected_sha256=DXF_CONTRACT["sha256"],
                    expected_size_bytes=DXF_CONTRACT["size_bytes"],
                )


if __name__ == "__main__":
    unittest.main()
