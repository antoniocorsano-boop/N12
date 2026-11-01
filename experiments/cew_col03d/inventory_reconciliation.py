from __future__ import annotations

import re
from typing import Any


REQUIRED_V25_MEMBER_NAMES = (
    "TAV5_CARPENTERIA.dxf",
    "TAV6_TRAVI.dxf",
    "TAV7_PILASTRI.dxf",
    "ABACO_TOPOLOGICO_TAV5_v11.csv",
    "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
    "MATRICE_PILASTRI_27x5_v22.csv",
    "ABACO_TRAVI_TAV6_v23.csv",
    "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv",
)

_PACKAGE_HEADING = "## Pacchetto DXF strutturale v25"
_MEMBER_LINE = re.compile(r"^-\s+`([^`]+\.(?:csv|dxf))`\s*$", re.IGNORECASE)


def governed_v25_inventory_members(inventory_text: str) -> list[str]:
    if not isinstance(inventory_text, str) or not inventory_text.strip():
        raise ValueError("GOVERNED_INVENTORY_MISSING")
    in_package = False
    members: list[str] = []
    for raw_line in inventory_text.splitlines():
        line = raw_line.strip()
        if line == _PACKAGE_HEADING:
            in_package = True
            continue
        if in_package and line.startswith("## "):
            break
        if not in_package:
            continue
        match = _MEMBER_LINE.match(line)
        if match:
            members.append(match.group(1))
    if not in_package:
        raise ValueError("GOVERNED_V25_INVENTORY_SECTION_MISSING")
    return sorted(set(members))


def classify_member_request(
    artifact_name: str,
    inventory_text: str,
    zip_member_names: list[str] | tuple[str, ...] | set[str],
) -> dict[str, Any]:
    name = str(artifact_name or "").strip()
    if not name:
        raise ValueError("HISTORICAL_MEMBER_NAME_MISSING")
    governed = set(governed_v25_inventory_members(inventory_text))
    package_names = {str(value) for value in zip_member_names}
    if name not in governed:
        return {
            "artifact_name": name,
            "governed_inventory_member": False,
            "package_presence_state": "NOT_EVALUATED",
            "materialization_state": "NOT_IN_GOVERNED_INVENTORY",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
        }
    if name not in package_names:
        return {
            "artifact_name": name,
            "governed_inventory_member": True,
            "package_presence_state": "ABSENT",
            "materialization_state": "INVENTORY_PACKAGE_MISMATCH",
            "authority": "HISTORICAL_DERIVED_EVIDENCE",
            "promotion_authorized": False,
        }
    return {
        "artifact_name": name,
        "governed_inventory_member": True,
        "package_presence_state": "PRESENT",
        "materialization_state": "PACKAGE_MEMBER_DISCOVERED",
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "promotion_authorized": False,
    }


def reconcile_required_members(
    inventory_text: str,
    zip_member_names: list[str] | tuple[str, ...] | set[str],
) -> list[dict[str, Any]]:
    rows = [
        classify_member_request(name, inventory_text, zip_member_names)
        for name in REQUIRED_V25_MEMBER_NAMES
    ]
    return sorted(rows, key=lambda row: row["artifact_name"])
