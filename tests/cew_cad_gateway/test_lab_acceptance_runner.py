from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cew_cad_gateway.canonical import sha256_file
from cew_cad_gateway.policy import GatewayPolicy
from cew_cad_gateway.workspace import Workspace, WorkspaceError
from scripts.cew_cad_lab_acceptance import build_parser, create_evidence_dir, validate_lab_target


class LabAcceptanceRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "CivilExisting"
        self.root.mkdir()
        zones = {
            "SOURCE": "00_sources",
            "BASELINE": "01_baseline",
            "WORKING": "02_working",
            "EVIDENCE": "03_evidence",
            "CHANGESETS": "04_changesets",
            "AUDITS": "05_audits",
            "VERIFIED": "06_verified",
            "ISSUED": "07_issued",
        }
        for zone in zones.values():
            (self.root / zone).mkdir()
        self.policy = GatewayPolicy(
            zones=zones,
            mutable_path_classes=("WORKING",),
            max_primary_operations=1,
            allow_overwrite=False,
            allowed_mutating_operations=("create_polyline", "undo_own_change"),
            allowed_property_paths=(),
            required_capabilities=("query", "audit", "capture", "save_verified"),
        )
        self.workspace = Workspace(self.root, self.policy)
        self.lab = self.root / "02_working" / "cew-cad-lab.dwg"
        self.lab.write_bytes(b"disposable-lab-drawing")
        self.lab_hash = sha256_file(self.lab)

    def test_prepare_and_execute_parsers_never_accept_private_key_or_output_path(self) -> None:
        parser = build_parser()
        common = [
            "--workspace-root", str(self.root),
            "--policy", "governance/cew-cad/CEW_CAD_POLICY_v1.json",
            "--ocs-executable", "C:/OpenCADStudio/OpenCADStudio.exe",
            "--ocs-sha256", "a" * 64,
            "--approval-public-key", "C:/keys/cew-cad-public.pem",
            "--lab-dwg-ref", "02_working/cew-cad-lab.dwg",
            "--expected-source-sha256", self.lab_hash,
            "--target-version", "2018",
        ]
        prepare = parser.parse_args(["prepare", *common, "--changeset-id", "CS-LAB-1"])
        execute = parser.parse_args(["execute", *common, "--changeset-id", "CS-LAB-1", "--approval-id", "APP-LAB-1"])
        self.assertEqual(prepare.command, "prepare")
        self.assertEqual(execute.command, "execute")
        self.assertFalse(hasattr(prepare, "private_key"))
        self.assertFalse(hasattr(execute, "private_key"))
        self.assertFalse(hasattr(prepare, "output_path"))
        self.assertFalse(hasattr(execute, "output_path"))
        with self.assertRaises(SystemExit):
            parser.parse_args(["execute", *common, "--changeset-id", "CS-LAB-1", "--approval-id", "APP-LAB-1", "--private-key", "secret.pem"])

    def test_validate_lab_target_requires_exact_working_ref_and_hash(self) -> None:
        resolved = validate_lab_target(self.workspace, "02_working/cew-cad-lab.dwg", self.lab_hash)
        self.assertEqual(resolved, self.lab.resolve())

        baseline = self.root / "01_baseline" / "canonical.dwg"
        baseline.write_bytes(b"canonical")
        with self.assertRaises(WorkspaceError):
            validate_lab_target(self.workspace, "01_baseline/canonical.dwg", sha256_file(baseline))
        with self.assertRaises(ValueError):
            validate_lab_target(self.workspace, "02_working/cew-cad-lab.dwg", "f" * 64)
        with self.assertRaises(WorkspaceError):
            validate_lab_target(self.workspace, str(self.lab.resolve()), self.lab_hash)

    def test_evidence_directory_is_confined_below_target_root_and_collision_fails(self) -> None:
        repo_root = Path(self.tmp.name) / "repo"
        repo_root.mkdir()
        target = create_evidence_dir(repo_root, "20261022T053500Z")
        self.assertEqual(target, (repo_root / "target" / "cew-cad-01" / "20261022T053500Z").resolve())
        self.assertTrue(target.is_dir())
        with self.assertRaises(FileExistsError):
            create_evidence_dir(repo_root, "20261022T053500Z")


if __name__ == "__main__":
    unittest.main()
