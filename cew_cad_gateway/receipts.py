from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .canonical import canonical_json_bytes, sha256_json


class ReceiptStoreError(ValueError):
    pass


@dataclass(frozen=True)
class StoredReceipt:
    kind: str
    path: Path
    sha256: str


class ReceiptStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        if not self.root.exists() or not self.root.is_dir():
            raise ReceiptStoreError("RECEIPT_ROOT_MISSING")

    def write(self, kind: str, value: object) -> StoredReceipt:
        if not kind or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in kind):
            raise ReceiptStoreError("INVALID_RECEIPT_KIND")
        digest = sha256_json(value)
        path = self.root / f"{kind}-{digest}.json"
        try:
            with path.open("xb") as handle:
                handle.write(canonical_json_bytes(value))
                handle.write(b"\n")
        except FileExistsError as exc:
            raise ReceiptStoreError("RECEIPT_ALREADY_EXISTS") from exc
        return StoredReceipt(kind=kind, path=path, sha256=digest)
