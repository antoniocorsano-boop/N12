from __future__ import annotations

import json
from pathlib import Path
import unittest

from cew_bimcraft.command_plan import compile_command_plan, load_benchmark_fixture
from cew_bimcraft.mcp_runner import (
    BIMCraftMCPError,
    execute_command_plan,
    extract_bound_id,
    parse_tool_response,
)


FIXTURE_PATH = Path(
    "governance/cew-bimcraft-01/fixtures/STAGE_A_STRUCTURAL_FIXTURE_v1.json"
)


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self._next_ids = {
            "structural_column": {"id": 210001},
            "beam": {"ids": [210002]},
            "footing": {"id": 210003},
            "floor": {"id": 210004},
        }

    def tool(self, name: str, arguments: dict | None = None):
        args = dict(arguments or {})
        self.calls.append((name, args))
        if name == "new_model":
            return {"name": args.get("name", "Project")}
        if name == "execute":
            command = args["command"]
            return self._next_ids.get(command, {})
        raise AssertionError(f"unexpected tool {name}")


class BIMCraftMCPRunnerTests(unittest.TestCase):
    def test_parse_tool_response_decodes_json_text(self) -> None:
        response = {
            "jsonrpc": "2.0",
            "id": 7,
            "result": {
                "content": [{"type": "text", "text": '{"id":210001}'}]
            },
        }
        self.assertEqual(parse_tool_response(response), {"id": 210001})

    def test_parse_tool_response_fails_on_tool_error(self) -> None:
        response = {
            "jsonrpc": "2.0",
            "id": 7,
            "result": {
                "isError": True,
                "content": [{"type": "text", "text": "bad geometry"}],
            },
        }
        with self.assertRaisesRegex(BIMCraftMCPError, "bad geometry"):
            parse_tool_response(response)

    def test_extract_bound_id_accepts_id_or_single_ids_only(self) -> None:
        self.assertEqual(extract_bound_id({"id": 210001}), 210001)
        self.assertEqual(extract_bound_id({"ids": [210002]}), 210002)
        with self.assertRaisesRegex(BIMCraftMCPError, "BIMCRAFT_BIND_ID_AMBIGUOUS"):
            extract_bound_id({"ids": [1, 2]})
        with self.assertRaisesRegex(BIMCraftMCPError, "BIMCRAFT_BIND_ID_MISSING"):
            extract_bound_id({})

    def test_execute_plan_resolves_symbolic_refs_before_modify(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        plan = compile_command_plan(fixture)
        client = FakeClient()

        result = execute_command_plan(client, plan)

        self.assertEqual(
            result.bindings,
            {
                "element:SYN-COL-001": 210001,
                "element:SYN-BEAM-001": 210002,
                "element:SYN-FOOT-001": 210003,
                "element:SYN-SLAB-001": 210004,
            },
        )
        modify_calls = [
            args for name, args in client.calls
            if name == "execute" and args.get("command") == "modify"
        ]
        self.assertEqual(len(modify_calls), 4)
        self.assertEqual(
            {call["params"]["id"] for call in modify_calls},
            {210001, 210002, 210003, 210004},
        )
        for call in modify_calls:
            self.assertNotIn("ref", call["params"])
            self.assertEqual(call["params"]["params"]["CEW_AUTHORITY"], "BENCHMARK_ONLY")

    def test_execute_plan_starts_fresh_noncanonical_model(self) -> None:
        fixture = load_benchmark_fixture(FIXTURE_PATH)
        plan = compile_command_plan(fixture)
        client = FakeClient()
        execute_command_plan(client, plan)
        self.assertEqual(
            client.calls[0],
            ("new_model", {"name": "CEW-BIMCRAFT-01-STAGE-A"}),
        )


if __name__ == "__main__":
    unittest.main()
