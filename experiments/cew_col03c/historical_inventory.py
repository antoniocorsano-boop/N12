from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


_HEADING = re.compile(r"^#{2,6}\s+(.+?)\s*$")
_PACKAGE_REF = re.compile(r"\bv\d+\b", re.IGNORECASE)


def parse_historical_inventory(text: str, *, source_ref: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = _HEADING.match(line)
        if match:
            if current is not None:
                current["historical_package_refs"] = sorted(set(current["historical_package_refs"]), key=lambda value: (int(value[1:]), value))
                records.append(current)
            title = match.group(1).strip().strip("`")
            current = {
                "artifact_name": title,
                "inventory_source_ref": source_ref,
                "historical_package_refs": [],
                "inventory_notes": [],
                "authority": "REFERENCE_ONLY",
            }
            continue
        if current is None or not line:
            continue
        current["inventory_notes"].append(line)
        current["historical_package_refs"].extend(ref.lower() for ref in _PACKAGE_REF.findall(line))
    if current is not None:
        current["historical_package_refs"] = sorted(set(current["historical_package_refs"]), key=lambda value: (int(value[1:]), value))
        records.append(current)
    return records


def classify_historical_artifact(
    record: dict[str, Any],
    *,
    materialized_path: str | None,
    sha256: str | None,
) -> dict[str, Any]:
    result = deepcopy(record)
    result["authority"] = "REFERENCE_ONLY"
    expected_sha256 = result.get("expected_sha256")
    if materialized_path is None or sha256 is None:
        result.update(
            {
                "materialized_path": None,
                "sha256": None,
                "materialization_state": "KNOWN_INVENTORY_NOT_MATERIALIZED",
                "bytes_available": False,
                "row_level_evidence_usable": False,
            }
        )
        return result

    normalized_sha = str(sha256).lower()
    result["materialized_path"] = materialized_path
    result["sha256"] = normalized_sha
    result["bytes_available"] = True
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or expected_sha256.lower() != normalized_sha:
        result["materialization_state"] = "PROVENANCE_MISMATCH"
        result["row_level_evidence_usable"] = False
        return result

    result["materialization_state"] = "MATERIALIZED_VERIFIED"
    result["row_level_evidence_usable"] = True
    return result


def require_row_level_evidence_usable(record: dict[str, Any]) -> None:
    if record.get("materialization_state") != "MATERIALIZED_VERIFIED" or record.get("row_level_evidence_usable") is not True:
        raise ValueError(f"historical artifact not materialized for row-level evidence: {record.get('artifact_name')}")
