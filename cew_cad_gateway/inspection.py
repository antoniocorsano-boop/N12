from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from .adapters.base import CADAdapter
from .canonical import sha256_json
from .receipts import ReceiptStore
from .types import CADStatus, InspectionReceipt
from .workspace import Workspace


class InspectionService:
    def __init__(
        self,
        adapter: CADAdapter,
        workspace: Workspace,
        receipt_store: ReceiptStore,
        *,
        now: Callable[[], str],
    ) -> None:
        self.adapter = adapter
        self.workspace = workspace
        self.receipt_store = receipt_store
        self._now = now

    async def status(self) -> CADStatus:
        status = await self.adapter.status()
        path_class = self.workspace.classify(Path(status.document.path))
        return replace(status, path_class=path_class)

    async def inspect(self, request: dict[str, object]) -> dict[str, object]:
        status = await self.status()
        data = await self.adapter.inspect(dict(request))
        return {"status": status, "data": data}

    async def measure(self, request: dict[str, object]) -> dict[str, object]:
        status = await self.status()
        data = await self.adapter.measure(dict(request))
        return {"status": status, "data": data}

    async def capture(self, request: dict[str, object]) -> dict[str, object]:
        status = await self.status()
        data = await self.adapter.capture(dict(request))
        return {"status": status, "data": data}

    async def audit(self, target: dict[str, object]) -> dict[str, object]:
        status = await self.status()
        data = await self.adapter.audit(dict(target))
        receipt = InspectionReceipt(
            schema="cew.cad.inspection.v1",
            status=status,
            audit_sha256=sha256_json(data),
            observed_at=self._now(),
        )
        stored = self.receipt_store.write("inspection", receipt)
        # Return JSON-serializable response without exposing filesystem path
        return {
            "status": status,
            "data": data,
            "receipt": receipt,
            "stored": {"kind": stored.kind, "sha256": stored.sha256},
        }
