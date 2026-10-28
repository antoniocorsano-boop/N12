from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from cew_bimcraft.command_plan import (
    BIMCraftFixtureError,
    compile_command_plan,
    load_benchmark_fixture,
)


FIXTURE_PATH = Path(
    "governance/cew-bimcraft-01/fixtures/STAGE_A_STRUCTURAL_FIXTURE_v1.json"
)
REQUIRED_PROVENANCE = {
    "CEW_OBJECT_ID",
    "CEW_EVIDENCE_ID",
    "CEW_SOURCE_SHA256",
    "CEW_EPISTEMIC_STATE",
    "CEW_REVISION",
    "CEW_AUTHORITY",
}
ALLOWED_COMMANDS = {
    "parameter",
    "level",
    "type",
    "structural_column",
    "beam",
    "footing",
    "floor",
    "modify",
}


class BIMCraftCommandPlanTests(unittest.TestCase):
    def test_stage_a_fixture_is_explicitly_noncanonical(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        self.assertEqual(fixture.project, "CEW-BIMCRAFT-01-STAGE-A")
        self.assertEqual(fixture.authority, "BENCHMARK_ONLY")
        self.assertFalse(fixture.canonical)
        self.assertFalse(fixture.structural_identity_authorized)
        self.assertEqual(fixture.units, "mm")
        self.assertNotIn("N12", fixture.project)

        for obj in fixture.objects:
            self.assertEqual(set(obj.provenance), REQUIRED_PROVENANCE)
            self.assertEqual(obj.provenance["CEW_AUTHORITY"], "BENCHMARK_ONLY")
            self.assertEqual(obj.provenance["CEW_OBJECT_ID"], obj.object_id)

    def test_authority_escalation_fails_closed(self) -> None:
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        raw["authority"] = "CANONICAL"
        raw["canonical"] = True
        raw["structural_identity_authorized"] = True

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "fixture.json"
            bad.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(BIMCraftFixtureError, "FIXTURE_AUTHORITY_FORBIDDEN"):
                load_benchmark_fixture(bad)

    def test_doc_without_real_source_binding_is_rejected(self) -> None:
        raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        raw["objects"][0]["provenance"]["CEW_EPISTEMIC_STATE"] = "DOC"

        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "fixture.json"
            bad.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaisesRegex(BIMCraftFixtureError, "SYNTHETIC_DOC_FORBIDDEN"):
                load_benchmark_fixture(bad)

    def test_command_plan_is_deterministic_and_contains_no_shell_escape(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        first = compile_command_plan(fixture)
        second = compile_command_plan(fixture)

        self.assertEqual(first.canonical_json, second.canonical_json)
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(len(first.sha256), 64)
        self.assertTrue(first.commands)

        for command in first.commands:
            self.assertIn(command.command, ALLOWED_COMMANDS)
            self.assertNotIn(command.command, {"shell", "exec", "system"})
            self.assertNotIn("shell", command.params)
            self.assertNotIn("command_line", command.params)

    def test_plan_preserves_explicit_geometry_and_uses_symbolic_refs_for_provenance(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        plan = compile_command_plan(fixture)

        create_by_bind = {
            command.bind: command
            for command in plan.commands
            if command.bind is not None
        }
        self.assertEqual(
            create_by_bind["element:SYN-BEAM-001"].params["points"],
            [[0, 0], [5000, 0]],
        )
        self.assertEqual(
            create_by_bind["element:SYN-COL-001"].params["at"],
            [0, 0],
        )
        self.assertEqual(
            create_by_bind["element:SYN-FOOT-001"].params["thickness"],
            500,
        )
        self.assertTrue(
            create_by_bind["element:SYN-SLAB-001"].params["structural"]
        )

        provenance_updates = [
            command
            for command in plan.commands
            if command.command == "modify" and command.ref is not None
        ]
        self.assertEqual(len(provenance_updates), len(fixture.objects))
        self.assertEqual(
            {command.ref for command in provenance_updates},
            {f"element:{obj.object_id}" for obj in fixture.objects},
        )
        for update in provenance_updates:
            self.assertEqual(set(update.params["params"]), REQUIRED_PROVENANCE)

    def test_project_parameter_declarations_cover_structural_categories(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        plan = compile_command_plan(fixture)
        declarations = [c for c in plan.commands if c.command == "parameter"]
        self.assertEqual({c.params["name"] for c in declarations}, REQUIRED_PROVENANCE)
        for declaration in declarations:
            self.assertEqual(
                declaration.params["categories"],
                ["structuralcolumn", "beam", "footing", "floor"],
            )


if __name__ == "__main__":
    unittest.main()
