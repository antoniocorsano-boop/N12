from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def normalized_number(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if number == 0.0:
        return 0
    if number.is_integer():
        return int(number)
    return number


def vector3(value: Any) -> list[int | float] | None:
    if value is None:
        return None
    try:
        values = list(value)
    except TypeError:
        return None
    if len(values) == 2:
        values.append(0.0)
    if len(values) < 3:
        return None
    result = [normalized_number(values[index]) for index in range(3)]
    if any(item is None for item in result):
        return None
    return result  # type: ignore[return-value]


def stable_entity_id(
    source_sha256: str,
    layout_name: str,
    entity_type: str,
    handle: str | None,
    ordinal: int,
) -> str:
    locator = handle if handle else f"ordinal:{ordinal}"
    raw = f"{source_sha256}|{layout_name}|{entity_type}|{locator}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
