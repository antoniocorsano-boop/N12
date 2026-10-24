from __future__ import annotations

import hashlib
import os
import tempfile
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

    @staticmethod
    def _validate_kind(kind: str) -> None:
        if not kind or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in kind):
            raise ReceiptStoreError("INVALID_RECEIPT_KIND")

    def _fsync_root_directory(self) -> None:
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        try:
            directory_fd = os.open(self.root, flags)
        except OSError as exc:
            raise ReceiptStoreError("RECEIPT_DIRECTORY_SYNC_FAILED") from exc
        try:
            os.fsync(directory_fd)
        except OSError as exc:
            raise ReceiptStoreError("RECEIPT_DIRECTORY_SYNC_FAILED") from exc
        finally:
            os.close(directory_fd)

    def write(self, kind: str, value: object) -> StoredReceipt:
        self._validate_kind(kind)
        digest = sha256_json(value)
        path = self.root / f"{kind}-{digest}.json"
        content = canonical_json_bytes(value) + b"\n"

        if path.exists():
            existing = path.read_bytes()
            if existing == content:
                return StoredReceipt(kind=kind, path=path, sha256=digest)
            raise ReceiptStoreError("RECEIPT_CONTENT_CONFLICT")

        with tempfile.NamedTemporaryFile(mode="wb", dir=self.root, delete=False, prefix=f".{kind}-{digest}.", suffix=".tmp") as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        try:
            os.replace(tmp_path, path)
        except BaseException:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

        return StoredReceipt(kind=kind, path=path, sha256=digest)

    def claim_once(self, kind: str, key: str, value: object) -> StoredReceipt:
        """Atomically claim a deterministic key exactly once.

        The destination path is derived only from ``key``. Exclusive creation is
        the serialization point across processes: once the path exists, the same
        key can never be claimed again, regardless of receipt payload or timestamp.
        The parent directory is synced before success is reported so the directory
        entry itself is durable across a host crash on filesystems that require it.
        """
        self._validate_kind(kind)
        if not isinstance(key, str) or not key:
            raise ReceiptStoreError("INVALID_RECEIPT_CLAIM_KEY")

        key_digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        path = self.root / f"{kind}-{key_digest}.json"
        content = canonical_json_bytes(value) + b"\n"

        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ReceiptStoreError("RECEIPT_ALREADY_CLAIMED") from exc

        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

        self._fsync_root_directory()
        return StoredReceipt(kind=kind, path=path, sha256=sha256_json(value))
