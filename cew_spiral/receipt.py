from __future__ import annotations

import hashlib
import json
from typing import Any

from cew_spiral.contracts import ROUTE_RECEIPT_SCHEMA


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build_route_receipt(decision: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema": ROUTE_RECEIPT_SCHEMA,
        "selected_residual_id": decision["selected_residual_id"],
        "state": decision["state"],
        "route": decision["route"],
        "selection_basis": decision["selection_basis"],
        "residual_priority_order": decision["residual_priority_order"],
        "authority_before": decision["authority_before"],
        "authority_after": decision["authority_after"],
        "promotion_authorized": decision["promotion_authorized"],
    }
    payload["receipt_sha256"] = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
    return payload
