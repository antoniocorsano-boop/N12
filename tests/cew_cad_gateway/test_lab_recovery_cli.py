from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cew_cad_gateway.canonical import sha256_file
from scripts.cew_cad_lab_acceptance import build_parser


class LabRecoveryCLITests(unittest.TestCase):
    def test_recover_requires_refs_but_no_mutation_confirmation_or_private_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lab = root / "lab.dwg"
            lab.write_bytes(b"lab")
            common = [
                "--workspace-root", str(root),
                "--policy", "governance/cew-cad/CEW_CAD_POLICY_v1.json",
                "--ocs-executable", "C:/OpenCADStudio/OpenCADStudio.exe",
                "--ocs-sha256", "a" * 64,
                "--approval-public-key", "C:/keys/cew-cad-public.pem",
                "--lab-dwg-ref", "02_working/cew-cad-lab.dwg",
                "--expected-source-sha256", sha256_file(lab),
                "--target-version", "2018",
            ]
            parser = build_parser()
            args = parser.parse_args([
                "recover", *common,
                "--changeset-id", "CEW-CAD-LAB-004C",
                "--approval-id", "CEW-CAD-APP-LAB-004G",
            ])
            self.assertEqual(args.command, "recover")
            self.assertFalse(hasattr(args, "confirm_lab_mutation"))
            self.assertFalse(hasattr(args, "private_key"))
            self.assertFalse(hasattr(args, "output_path"))


if __name__ == "__main__":
    unittest.main()
