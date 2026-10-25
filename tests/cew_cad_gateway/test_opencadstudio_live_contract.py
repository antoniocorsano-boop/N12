from __future__ import annotations

import unittest

from cew_cad_gateway.adapters.opencadstudio import (
    _build_typed_polyline_request,
    _mapping,
    _normalize_ocs_mutation_response,
)
from cew_cad_gateway.types import CreatePolyline


class _CallToolResultLike:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def model_dump(self) -> dict[str, object]:
        return self._payload


class OpenCADStudioLiveContractTests(unittest.TestCase):
    def test_entities_create_uses_live_ocs_vertex_arrays(self) -> None:
        operation = CreatePolyline(
            layer="CEW-LAB",
            points=((0.0, 0.0), (4000.0, 0.0), (4000.0, 3000.0)),
            closed=True,
        )

        request = _build_typed_polyline_request(operation)

        self.assertEqual(
            request["vertices"],
            [[0.0, 0.0], [4000.0, 0.0], [4000.0, 3000.0]],
        )

    def test_mutation_normalization_accepts_live_result_handles(self) -> None:
        response = {
            "ok": True,
            "status": "completed",
            "request_id": "cew-cad-live-contract",
            "result": {
                "created": 1,
                "handles": ["87"],
                "layers_created": ["CEW-LAB"],
            },
            "state": {
                "revision": 2,
                "geometry_revision": 32,
                "document_id": 3,
                "dirty": True,
            },
        }

        normalized = _normalize_ocs_mutation_response(response)

        self.assertEqual(normalized["status"], "completed")
        self.assertEqual(normalized["revision"], 2)
        self.assertEqual(normalized["changed_entities"], ["87"])

    def test_mapping_accepts_call_tool_result_model_dump(self) -> None:
        payload = {
            "ok": True,
            "status": "completed",
            "result": {"handles": ["87"]},
            "state": {"revision": 2},
        }

        mapped = _mapping(_CallToolResultLike(payload))

        self.assertEqual(mapped, payload)


if __name__ == "__main__":
    unittest.main()
