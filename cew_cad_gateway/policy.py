from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

_REQUIRED_ZONES = (
    "SOURCE",
    "BASELINE",
    "WORKING",
    "EVIDENCE",
    "CHANGESETS",
    "AUDITS",
    "VERIFIED",
    "ISSUED",
)


@dataclass(frozen=True)
class GatewayPolicy:
    zones: Mapping[str, str]
    mutable_path_classes: tuple[str, ...]
    max_primary_operations: int
    allow_overwrite: bool
    allowed_mutating_operations: tuple[str, ...]
    allowed_property_paths: tuple[str, ...]
    required_capabilities: tuple[str, ...]

    @classmethod
    def load(cls, path: Path) -> "GatewayPolicy":
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("INVALID_POLICY") from exc
        if not isinstance(raw, dict) or raw.get("schema") != "cew.cad.policy.v1":
            raise ValueError("INVALID_POLICY_SCHEMA")
        zones = raw.get("zones")
        if not isinstance(zones, dict) or tuple(zones.keys()) != _REQUIRED_ZONES:
            raise ValueError("INVALID_POLICY_ZONES")
        if any(not isinstance(value, str) or not value for value in zones.values()):
            raise ValueError("INVALID_POLICY_ZONES")
        if len(set(zones.values())) != len(zones):
            raise ValueError("DUPLICATE_POLICY_ZONE")

        mutable = raw.get("mutable_path_classes")
        allowed_ops = raw.get("allowed_mutating_operations")
        allowed_paths = raw.get("allowed_property_paths")
        capabilities = raw.get("required_capabilities")
        if mutable != ["WORKING"]:
            raise ValueError("INVALID_MUTABLE_ZONE_POLICY")
        if raw.get("max_primary_operations") != 1:
            raise ValueError("INVALID_OPERATION_LIMIT")
        if raw.get("allow_overwrite") is not False:
            raise ValueError("OVERWRITE_MUST_BE_DISABLED")
        if allowed_ops != ["create_polyline", "undo_own_change"]:
            raise ValueError("INVALID_MUTATION_ALLOWLIST")
        if allowed_paths != []:
            raise ValueError("PROPERTY_MUTATION_NOT_AUTHORIZED")
        if not isinstance(capabilities, list) or not capabilities or any(
            not isinstance(item, str) or not item for item in capabilities
        ):
            raise ValueError("INVALID_REQUIRED_CAPABILITIES")

        return cls(
            zones=dict(zones),
            mutable_path_classes=("WORKING",),
            max_primary_operations=1,
            allow_overwrite=False,
            allowed_mutating_operations=("create_polyline", "undo_own_change"),
            allowed_property_paths=(),
            required_capabilities=tuple(capabilities),
        )
