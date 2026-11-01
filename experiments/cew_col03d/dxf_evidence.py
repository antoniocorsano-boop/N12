from __future__ import annotations

import hashlib
from typing import Any


_TEXT_ENTITY_TYPES = {"TEXT", "MTEXT", "ATTRIB", "ATTDEF"}


def _pairs(data: bytes, artifact_name: str) -> list[tuple[str, str]]:
    try:
        text = data.decode("latin-1", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"DXF_TEXT_DECODE_FAILED:{artifact_name}") from exc
    lines = text.splitlines()
    if len(lines) % 2:
        raise ValueError(f"DXF_GROUP_PAIR_MALFORMED:{artifact_name}")
    return [(lines[index].strip(), lines[index + 1].strip()) for index in range(0, len(lines), 2)]


def audit_dxf_member(artifact_name: str, data: bytes) -> dict[str, Any]:
    pairs = _pairs(data, artifact_name)

    version: str | None = None
    for index, (code, value) in enumerate(pairs[:-1]):
        if code == "9" and value == "$ACADVER":
            next_code, next_value = pairs[index + 1]
            if next_code == "1":
                version = next_value
                break
    if version != "AC1027":
        raise ValueError(f"DXF_VERSION_NOT_AC1027:{artifact_name}:{version or 'MISSING'}")

    in_entities = False
    entity_count = 0
    entity_types: list[str] = []
    layers: set[str] = set()
    text_observation_count = 0

    index = 0
    while index < len(pairs):
        code, value = pairs[index]
        if code == "0" and value == "SECTION" and index + 1 < len(pairs):
            next_code, next_value = pairs[index + 1]
            in_entities = next_code == "2" and next_value == "ENTITIES"
            index += 2
            continue
        if in_entities and code == "0" and value == "ENDSEC":
            in_entities = False
        elif in_entities and code == "0":
            entity_count += 1
            entity_types.append(value)
            if value in _TEXT_ENTITY_TYPES:
                text_observation_count += 1
        elif in_entities and code == "8":
            layers.add(value)
        index += 1

    if entity_count <= 0:
        raise ValueError(f"DXF_ENTITIES_MISSING:{artifact_name}")

    return {
        "artifact_name": artifact_name,
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "dxf_version": version,
        "entity_count": entity_count,
        "entity_types": sorted(set(entity_types)),
        "layer_count": len(layers),
        "layers": sorted(layers),
        "text_observation_count": text_observation_count,
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "promotion_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
    }
