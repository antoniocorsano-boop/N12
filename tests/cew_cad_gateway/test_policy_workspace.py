from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cew_cad_gateway.policy import GatewayPolicy
from cew_cad_gateway.types import PathClass
from cew_cad_gateway.workspace import Workspace, WorkspaceError


ZONES = {
    "SOURCE": "00_sources",
    "BASELINE": "01_baseline",
    "WORKING": "02_working",
    "EVIDENCE": "03_evidence",
    "CHANGESETS": "04_changesets",
    "AUDITS": "05_audits",
    "VERIFIED": "06_verified",
    "ISSUED": "07_issued",
}


def write_policy(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "cew.cad.policy.v1",
                "zones": ZONES,
                "mutable_path_classes": ["WORKING"],
                "max_primary_operations": 1,
                "allow_overwrite": False,
                "allowed_mutating_operations": ["create_polyline", "undo_own_change"],
                "allowed_property_paths": [],
                "required_capabilities": ["query", "audit", "capture", "save_verified"],
            }
        ),
        encoding="utf-8",
    )


class WorkspacePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "CivilExisting"
        self.root.mkdir()
        for directory in ZONES.values():
            (self.root / directory).mkdir()
        self.policy_path = self.root / "policy.json"
        write_policy(self.policy_path)
        self.policy = GatewayPolicy.load(self.policy_path)
        self.workspace = Workspace(self.root, self.policy)

    def test_policy_pins_single_operation_no_overwrite_and_no_property_paths(self) -> None:
        self.assertEqual(self.policy.max_primary_operations, 1)
        self.assertFalse(self.policy.allow_overwrite)
        self.assertEqual(self.policy.allowed_mutating_operations, ("create_polyline", "undo_own_change"))
        self.assertEqual(self.policy.allowed_property_paths, ())

    def test_only_working_zone_resolves_as_mutable(self) -> None:
        working = self.root / "02_working" / "lab.dwg"
        working.write_bytes(b"lab")
        self.assertEqual(self.workspace.classify(working), PathClass.WORKING)
        self.assertEqual(self.workspace.resolve_ref("02_working/lab.dwg", PathClass.WORKING), working.resolve())

        for ref, expected in (
            ("00_sources/source.dwg", PathClass.SOURCE),
            ("01_baseline/base.dwg", PathClass.BASELINE),
            ("06_verified/out.dwg", PathClass.VERIFIED),
            ("07_issued/issued.dwg", PathClass.ISSUED),
        ):
            path = self.root / ref
            path.write_bytes(b"x")
            self.assertEqual(self.workspace.classify(path), expected)
            with self.assertRaises(WorkspaceError):
                self.workspace.resolve_ref(ref, PathClass.WORKING)

    def test_rejects_traversal_absolute_unc_drive_case_and_unicode_aliases(self) -> None:
        bad_refs = (
            "02_working/../01_baseline/base.dwg",
            "/tmp/escape.dwg",
            "C:\\temp\\escape.dwg",
            "\\\\server\\share\\escape.dwg",
            "02_WORKING/lab.dwg",
            "02_working/cafe\u0301.dwg",
        )
        for ref in bad_refs:
            with self.subTest(ref=ref):
                with self.assertRaises(WorkspaceError):
                    self.workspace.resolve_ref(ref, PathClass.WORKING)

    def test_rejects_symlink_escape_even_when_link_is_inside_working(self) -> None:
        outside = Path(self.tmp.name) / "outside.dwg"
        outside.write_bytes(b"outside")
        link = self.root / "02_working" / "link.dwg"
        try:
            link.symlink_to(outside)
            with self.assertRaises(WorkspaceError):
                self.workspace.resolve_ref("02_working/link.dwg", PathClass.WORKING)
            return
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                self.skipTest("symlink creation requires privilege on this Windows host; containment verified by realpath check")
            raise

    def test_missing_workspace_root_is_rejected(self) -> None:
        missing = Path(self.tmp.name) / "missing"
        with self.assertRaises(WorkspaceError):
            Workspace(missing, self.policy)

    def test_verified_output_is_server_generated_and_collision_fails(self) -> None:
        source = self.root / "02_working" / "lab.dwg"
        source.write_bytes(b"lab")
        output = self.workspace.verified_output("02_working/lab.dwg", "CEW-CAD-CS-000001", ".dwg")
        self.assertEqual(output.parent, (self.root / "06_verified").resolve())
        self.assertIn("CEW-CAD-CS-000001", output.name)
        output.write_bytes(b"verified")
        with self.assertRaises(WorkspaceError):
            self.workspace.verified_output("02_working/lab.dwg", "CEW-CAD-CS-000001", ".dwg")


if __name__ == "__main__":
    unittest.main()
