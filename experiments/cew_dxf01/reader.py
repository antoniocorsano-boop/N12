from __future__ import annotations

from collections import Counter
import hashlib
from importlib.metadata import version as distribution_version
from pathlib import Path
from typing import Any

import ezdxf

from experiments.cew_col03d.dxf_evidence import audit_dxf_member
from experiments.cew_dxf01.normalize import (
    canonical_sha256,
    normalized_number,
    stable_entity_id,
    vector3,
)


_REQUIRED_EZDXF_VERSION = "1.4.5"


def _dxf_value(entity: Any, name: str, default: Any = None) -> Any:
    try:
        if entity.dxf.hasattr(name):
            return entity.dxf.get(name)
    except (AttributeError, TypeError, ValueError):
        pass
    return default


def _entity_base(entity: Any, *, source_sha256: str, layout_name: str, ordinal: int) -> dict[str, Any]:
    kind = str(entity.dxftype())
    handle_value = _dxf_value(entity, "handle")
    handle = str(handle_value) if handle_value not in (None, "") else None
    return {
        "stable_id": stable_entity_id(source_sha256, layout_name, kind, handle, ordinal),
        "entity_type": kind,
        "handle": handle,
        "layout": layout_name,
        "layer": str(_dxf_value(entity, "layer", "")),
    }


def _text_observation(entity: Any, *, base: dict[str, Any]) -> dict[str, Any]:
    kind = base["entity_type"]
    if kind == "TEXT":
        text = str(_dxf_value(entity, "text", ""))
        insert = vector3(_dxf_value(entity, "insert"))
    else:
        text = str(getattr(entity, "text", ""))
        insert = vector3(_dxf_value(entity, "insert"))
    return {
        **base,
        "text": text,
        "insert": insert,
        "rotation": normalized_number(_dxf_value(entity, "rotation", 0.0)),
        "height": normalized_number(_dxf_value(entity, "height", _dxf_value(entity, "char_height"))),
    }


def _insert_observation(entity: Any, *, base: dict[str, Any]) -> dict[str, Any]:
    attributes: list[dict[str, Any]] = []
    for attrib in sorted(
        list(getattr(entity, "attribs", ()) or ()),
        key=lambda row: (str(_dxf_value(row, "tag", "")), str(_dxf_value(row, "handle", ""))),
    ):
        attributes.append(
            {
                "tag": str(_dxf_value(attrib, "tag", "")),
                "text": str(_dxf_value(attrib, "text", "")),
                "insert": vector3(_dxf_value(attrib, "insert")),
                "handle": str(_dxf_value(attrib, "handle", "")) or None,
            }
        )
    return {
        **base,
        "block_name": str(_dxf_value(entity, "name", "")),
        "insert": vector3(_dxf_value(entity, "insert")),
        "rotation": normalized_number(_dxf_value(entity, "rotation", 0.0)),
        "scale": [
            normalized_number(_dxf_value(entity, "xscale", 1.0)),
            normalized_number(_dxf_value(entity, "yscale", 1.0)),
            normalized_number(_dxf_value(entity, "zscale", 1.0)),
        ],
        "attributes": attributes,
    }


def _dimension_observation(entity: Any, *, base: dict[str, Any]) -> dict[str, Any]:
    return {
        **base,
        "dimension_type": normalized_number(_dxf_value(entity, "dimtype")),
        "text_override": str(_dxf_value(entity, "text", "")),
        "defpoint": vector3(_dxf_value(entity, "defpoint")),
        "defpoint2": vector3(_dxf_value(entity, "defpoint2")),
        "defpoint3": vector3(_dxf_value(entity, "defpoint3")),
        "angle": normalized_number(_dxf_value(entity, "angle")),
    }


def _header_extents(doc: Any) -> dict[str, Any]:
    def header_vector(name: str) -> list[int | float] | None:
        try:
            return vector3(doc.header.get(name))
        except (AttributeError, KeyError, TypeError, ValueError):
            return None

    extmin = header_vector("$EXTMIN")
    extmax = header_vector("$EXTMAX")
    limmin = header_vector("$LIMMIN")
    limmax = header_vector("$LIMMAX")
    return {
        "method": "SOURCE_HEADER",
        "state": "DECLARED" if extmin is not None and extmax is not None else "NOT_DECLARED",
        "extmin": extmin,
        "extmax": extmax,
        "limmin": limmin,
        "limmax": limmax,
    }


def _block_inventory(doc: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for block in sorted(list(doc.blocks), key=lambda item: str(item.name)):
        counts = Counter(str(entity.dxftype()) for entity in block)
        attdefs = []
        for entity in block:
            if str(entity.dxftype()) == "ATTDEF":
                attdefs.append(
                    {
                        "tag": str(_dxf_value(entity, "tag", "")),
                        "text": str(_dxf_value(entity, "text", "")),
                        "insert": vector3(_dxf_value(entity, "insert")),
                    }
                )
        rows.append(
            {
                "name": str(block.name),
                "entity_counts": dict(sorted(counts.items())),
                "attribute_definitions": sorted(attdefs, key=lambda row: (row["tag"], row["text"])),
            }
        )
    return rows


def read_dxf_path(
    path: str | Path,
    *,
    artifact_name: str,
    expected_sha256: str,
    expected_size_bytes: int,
) -> dict[str, Any]:
    source_path = Path(path)
    if source_path.name != artifact_name:
        raise ValueError(f"ARTIFACT_NAME_MISMATCH:{artifact_name}:{source_path.name}")
    if not source_path.is_file():
        raise ValueError(f"SOURCE_NOT_FOUND:{artifact_name}")

    before_bytes = source_path.read_bytes()
    source_sha256 = hashlib.sha256(before_bytes).hexdigest()
    if len(before_bytes) != int(expected_size_bytes) or source_sha256 != str(expected_sha256):
        raise ValueError(f"PROVENANCE_MISMATCH:{artifact_name}")

    raw_audit = audit_dxf_member(artifact_name, before_bytes)
    actual_ezdxf_version = distribution_version("ezdxf")
    if actual_ezdxf_version != _REQUIRED_EZDXF_VERSION:
        raise ValueError(
            f"TOOLCHAIN_VERSION_MISMATCH:ezdxf:{actual_ezdxf_version}:{_REQUIRED_EZDXF_VERSION}"
        )

    try:
        doc = ezdxf.readfile(str(source_path))
    except Exception as exc:  # ezdxf exposes several parser-specific exception classes
        raise ValueError(f"DXF_STRUCTURED_READ_FAILED:{artifact_name}") from exc

    layers = sorted(str(layer.dxf.name) for layer in doc.layers)
    entity_counts: Counter[str] = Counter()
    text_entities: list[dict[str, Any]] = []
    inserts: list[dict[str, Any]] = []
    dimensions: list[dict[str, Any]] = []

    for layout in sorted(list(doc.layouts), key=lambda item: str(item.name)):
        layout_name = str(layout.name)
        for ordinal, entity in enumerate(layout):
            kind = str(entity.dxftype())
            entity_counts[kind] += 1
            base = _entity_base(
                entity,
                source_sha256=source_sha256,
                layout_name=layout_name,
                ordinal=ordinal,
            )
            if kind in {"TEXT", "MTEXT"}:
                text_entities.append(_text_observation(entity, base=base))
            elif kind == "INSERT":
                inserts.append(_insert_observation(entity, base=base))
            elif kind == "DIMENSION":
                dimensions.append(_dimension_observation(entity, base=base))

    text_entities.sort(key=lambda row: row["stable_id"])
    inserts.sort(key=lambda row: row["stable_id"])
    dimensions.sort(key=lambda row: row["stable_id"])

    try:
        units = doc.header.get("$INSUNITS")
    except (AttributeError, KeyError, TypeError, ValueError):
        units = None

    payload: dict[str, Any] = {
        "schema": "CEW_DXF01_OBSERVATION_v1",
        "source": {
            "artifact_name": artifact_name,
            "sha256": source_sha256,
            "size_bytes": len(before_bytes),
            "dxf_version": raw_audit["dxf_version"],
            "insertion_units_code": normalized_number(units),
            "evidentiary_class": "HISTORICAL_DERIVED_EVIDENCE",
        },
        "toolchain": {
            "ezdxf_version": actual_ezdxf_version,
            "independent_raw_verifier": "experiments.cew_col03d.dxf_evidence.audit_dxf_member",
        },
        "raw_audit": raw_audit,
        "inventories": {
            "layers": layers,
            "entity_counts": dict(sorted(entity_counts.items())),
            "text_entities": text_entities,
            "inserts": inserts,
            "blocks": _block_inventory(doc),
            "dimensions": dimensions,
            "extents": _header_extents(doc),
        },
        "authority": {
            "authority_effect": "NONE",
            "primary_source_identity_bridge": False,
            "structural_identity_authorized": False,
            "canonical_geometry_authorized": False,
            "canonical_write_authorized": False,
            "family_assignment_authorized": False,
            "section_assignment_authorized": False,
            "m0g_authorized": False,
        },
        "source_bytes_unchanged": True,
    }

    after_bytes = source_path.read_bytes()
    if hashlib.sha256(after_bytes).hexdigest() != source_sha256 or len(after_bytes) != len(before_bytes):
        raise ValueError(f"SOURCE_MUTATED_DURING_READ:{artifact_name}")

    payload["normalized_sha256"] = canonical_sha256(payload)
    return payload
