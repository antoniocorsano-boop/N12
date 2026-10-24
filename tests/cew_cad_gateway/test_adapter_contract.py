from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from cew_cad_gateway.adapters.base import CADAdapter
from cew_cad_gateway.types import (
    CADStatus,
    CapabilityIdentity,
    CreatePolyline,
    DocumentIdentity,
)


class FakeAdapter:
    async def status(self) -> CADStatus:
        return CADStatus(
            session_id="session-1",
            document=DocumentIdentity(path="lab.dwg", sha256="0" * 64, document_id=1, revision=2),
            capabilities=CapabilityIdentity(cad_build="fake", capabilities_sha256="1" * 64),
            path_class=None,
        )

    async def inspect(self, request: dict[str, object]) -> dict[str, object]:
        return {"data": request}

    async def measure(self, request: dict[str, object]) -> dict[str, object]:
        return {"data": request}

    async def audit(self, target: dict[str, object]) -> dict[str, object]:
        return {"audit": target}

    async def capture(self, request: dict[str, object]) -> dict[str, object]:
        return {"capture": request}

    async def apply_operation(self, operation: CreatePolyline, *, request_id: str, expected: DocumentIdentity) -> dict[str, object]:
        return {"request_id": request_id, "changed_entities": ["A1"], "revision": expected.revision + 1}

    async def operation_status(self, request_id: str) -> dict[str, object]:
        return {"request_id": request_id, "status": "completed"}

    async def save_verified(self, path: Path, *, target_format: str, target_version: str, expected: DocumentIdentity) -> dict[str, object]:
        return {"ok": True, "path": str(path), "sha256": "2" * 64}


class AdapterContractTests(unittest.TestCase):
    def test_downstream_can_use_adapter_without_opencadstudio_types(self) -> None:
        async def exercise(adapter: CADAdapter) -> None:
            status = await adapter.status()
            self.assertEqual(status.document.document_id, 1)
            self.assertEqual((await adapter.inspect({"layer": "CEW-LAB"}))["data"], {"layer": "CEW-LAB"})
            self.assertEqual((await adapter.measure({"handle": "A1"}))["data"], {"handle": "A1"})
            self.assertIn("audit", await adapter.audit({"target_format": "dwg"}))
            self.assertIn("capture", await adapter.capture({"scope": "viewport"}))

        asyncio.run(exercise(FakeAdapter()))


if __name__ == "__main__":
    unittest.main()
