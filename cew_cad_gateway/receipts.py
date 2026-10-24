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
        content = canonical_json_bytes(value) + b"\n"
        
        if path.exists():
            existing = path.read_bytes()
            if existing == content:
                # Idempotent: same content, return existing
                return StoredReceipt(kind=kind, path=path, sha256=digest)
            else:
                # Conflict: same path but different content
                raise ReceiptStoreError("RECEIPT_CONTENT_CONFLICT")
        
        # Atomic write: temp file + rename
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode="wb", dir=self.root, delete=False, prefix=f".{kind}-{digest}.", suffix=".tmp") as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        try:
            os.replace(tmp_path, path)
        except BaseException:
            # Cleanup temp file on error
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        
        return StoredReceipt(kind=kind, path=path, sha256=digest)
