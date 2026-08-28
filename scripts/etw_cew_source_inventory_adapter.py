#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "canonical" / "tavole_originali_remote_index_v1.csv"
SCOPE_MODEL = ROOT / "automation" / "ETW_PLATFORM_SCOPE_MODEL_v1.json"

REQUIRED_REGISTRY_FIELDS = {
    "id",
    "canonical_filename",
    "git_blob_sha",
    "sha256",
    "classe",
    "livello_uso",
    "ruolo",
    "status",
}


class ScopeInventoryError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_source_registry(path: Path = REGISTRY) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED_REGISTRY_FIELDS - fields
        if missing:
            raise ValueError(f"CEW source registry missing fields: {sorted(missing)}")
        rows = [dict(row) for row in reader]
    if not rows:
        raise ValueError("CEW source registry is empty")
    return rows


def load_scope_model(path: Path = SCOPE_MODEL) -> dict[str, Any]:
    return _read_json(path)


def resolve_scope(project_id: str, discipline_id: str, model: dict[str, Any] | None = None) -> dict[str, Any]:
    if not project_id:
        raise ScopeInventoryError("MISSING_PROJECT")
    if not discipline_id:
        raise ScopeInventoryError("MISSING_DISCIPLINE")
    model = model or load_scope_model()
    projects = {p["project_id"] for p in model.get("projects", [])}
    disciplines = {d["discipline_id"] for d in model.get("disciplines", [])}
    if project_id not in projects:
        raise ScopeInventoryError("UNKNOWN_PROJECT")
    if discipline_id not in disciplines:
        raise ScopeInventoryError("UNKNOWN_DISCIPLINE")
    for scope in model.get("project_discipline_scopes", []):
        if scope.get("project_id") == project_id and scope.get("discipline_id") == discipline_id:
            return scope
    raise ScopeInventoryError("SCOPE_NOT_DECLARED")


def _public_source_identity(row: dict[str, str]) -> dict[str, Any]:
    return {
        "source_id": row["id"],
        "canonical_filename": row["canonical_filename"],
        "git_blob_sha": row["git_blob_sha"],
        "sha256": row["sha256"],
        "registry_class": row["classe"],
        "level_use": row["livello_uso"],
        "role": row["ruolo"],
        "source_status": row["status"],
    }


def scope_inventory_projection(
    project_id: str,
    discipline_id: str,
    *,
    registry_path: Path = REGISTRY,
    scope_model_path: Path = SCOPE_MODEL,
) -> dict[str, Any]:
    model = load_scope_model(scope_model_path)
    scope = resolve_scope(project_id, discipline_id, model)
    mode = scope.get("source_inventory_mode")

    base = {
        "schema_version": "1.0",
        "projection_type": "ScopeInventoryProjection",
        "authority": "READ_MODEL_ONLY",
        "project_id": project_id,
        "discipline_id": discipline_id,
        "scope_state": scope.get("scope_state"),
        "module_state": scope.get("module_state"),
        "source_inventory_mode": mode,
        "project_source_binding_created": False,
        "canonical_write_authorized": False,
    }

    if mode == "EMPTY_TEST_FIXTURE":
        return {
            **base,
            "sources": [],
            "source_count": 0,
            "engineering_data_present": False,
            "test_only": True,
        }

    if mode == "CEW_DELEGATED":
        return {
            **base,
            "sources": [],
            "source_count": None,
            "delegated_to": "CEW",
            "rule": "A0 does not reclassify CEW source ownership for Structures.",
        }

    if mode == "READ_ONLY_EXPLICIT_REGISTRY_CLASSIFICATION":
        class_filter = scope.get("source_registry_class_filter")
        if not class_filter:
            raise ValueError("explicit registry classification mode requires source_registry_class_filter")
        rows = load_source_registry(registry_path)
        selected = [row for row in rows if row.get("classe") == class_filter]
        sources = [_public_source_identity(row) for row in selected]
        return {
            **base,
            "registry_class_filter": class_filter,
            "sources": sources,
            "source_count": len(sources),
            "domain_contract_released": False,
            "domain_entity_count": 0,
            "domain_property_count": 0,
            "synthetic_engineering_data": False,
            "rule": "Source availability is projected from CEW classification only; no Architecture domain entity is inferred.",
        }

    raise ValueError(f"unsupported source_inventory_mode={mode!r}")


def validate_adapter() -> list[str]:
    errors: list[str] = []
    rows = load_source_registry()
    architecture = scope_inventory_projection("N12", "ARCHITECTURE")
    expected_ids = {row["id"] for row in rows if row.get("classe") == "architettonica"}
    actual_ids = {row["source_id"] for row in architecture["sources"]}
    if actual_ids != expected_ids:
        errors.append("Architecture projection does not exactly match registry classe=architettonica")
    if architecture.get("source_count") != len(expected_ids):
        errors.append("Architecture source count is not derived from registry")
    if architecture.get("domain_entity_count") != 0 or architecture.get("domain_property_count") != 0:
        errors.append("A0 Architecture projection must contain zero domain entities/properties")
    test_scope = scope_inventory_projection("TEST_PROJECT", "STRUCTURES")
    if test_scope.get("source_count") != 0 or test_scope.get("engineering_data_present") is not False:
        errors.append("TEST_PROJECT must contain zero engineering source data")
    structures = scope_inventory_projection("N12", "STRUCTURES")
    if structures.get("source_inventory_mode") != "CEW_DELEGATED" or structures.get("sources"):
        errors.append("A0 Structures source inventory must remain delegated to CEW")
    for project_id, discipline_id, expected in [
        ("", "STRUCTURES", "MISSING_PROJECT"),
        ("UNKNOWN", "STRUCTURES", "UNKNOWN_PROJECT"),
        ("N12", "", "MISSING_DISCIPLINE"),
        ("N12", "UNKNOWN", "UNKNOWN_DISCIPLINE"),
    ]:
        try:
            scope_inventory_projection(project_id, discipline_id)
            errors.append(f"invalid context {project_id}/{discipline_id} did not fail closed")
        except ScopeInventoryError as exc:
            if str(exc) != expected:
                errors.append(f"invalid context expected {expected}, got {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only eTwin A0 adapter over the CEW source registry")
    parser.add_argument("--project", default="N12")
    parser.add_argument("--discipline", default="ARCHITECTURE")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.validate:
        errors = validate_adapter()
        if errors:
            print("ETW_CEW_SOURCE_INVENTORY_ADAPTER = FAIL")
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("ETW_CEW_SOURCE_INVENTORY_ADAPTER = PASS")
        return 0

    try:
        projection = scope_inventory_projection(args.project, args.discipline)
    except ScopeInventoryError as exc:
        print(json.dumps({"state": "SCOPE_REJECTED", "reason": str(exc)}, indent=2))
        return 2
    print(json.dumps(projection, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
