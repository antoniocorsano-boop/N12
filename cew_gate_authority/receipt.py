from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from enum import Enum
from typing import Any

from .types import QualificationReceipt


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def receipt_dict(receipt: QualificationReceipt) -> dict[str, Any]:
    return _jsonable(asdict(receipt))


def canonical_receipt_bytes(receipt: QualificationReceipt) -> bytes:
    """Canonical UTF-8 JSON bytes. The digest intentionally excludes a trailing newline."""
    return json.dumps(receipt_dict(receipt), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def receipt_sha256(receipt: QualificationReceipt) -> str:
    return hashlib.sha256(canonical_receipt_bytes(receipt)).hexdigest()
