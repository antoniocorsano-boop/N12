from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from ..types import CADOperation, CADStatus, DocumentIdentity


@runtime_checkable
class CADAdapter(Protocol):
    async def status(self) -> CADStatus: ...

    async def inspect(self, request: dict[str, object]) -> dict[str, object]: ...

    async def measure(self, request: dict[str, object]) -> dict[str, object]: ...

    async def audit(self, target: dict[str, object]) -> dict[str, object]: ...

    async def capture(self, request: dict[str, object]) -> dict[str, object]: ...

    async def apply_operation(
        self,
        operation: CADOperation,
        *,
        request_id: str,
        expected: DocumentIdentity,
    ) -> dict[str, object]: ...

    async def operation_status(self, request_id: str) -> dict[str, object]: ...

    async def save_verified(
        self,
        path: Path,
        *,
        target_format: str,
        target_version: str,
        expected: DocumentIdentity,
    ) -> dict[str, object]: ...
