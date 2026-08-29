#!/usr/bin/env python3
"""Validate the N12 repository-memory layer.

The validator is intentionally dependency-free. It checks that canonical memory
files exist and that no operational artifact depends only on a transient chat or
runtime path. Derived artifacts may remain outside Git only when a deterministic
regeneration recipe is registered.
"""

from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MEM = ROOT / "memory"

REQUIRED_FILES = [
    ROOT / "AGENTS.md",
    MEM / "PROJECT_STATE.md",
    MEM / "SOURCE_REGISTRY.csv",
    MEM / "ARTIFACT_INDEX.csv",
    MEM / "OPEN_RESIDUALS.csv",
    MEM / "REGENERATION_RECIPES.csv",
    MEM / "FILE_LIBRARY_RECOVERY.csv",
    ROOT / "docs" / "REPOSITORY_MEMORY_PROTOCOL.md",
]

REQUIRED_COLUMNS = {
    "SOURCE_REGISTRY.csv": {
        "source_id", "kind", "repo_path", "evidence_status", "availability", "status"
    },
    "ARTIFACT_INDEX.csv": {
        "artifact_id", "artifact_type", "repo_path_or_ref", "status",
        "evidence_status", "source_ref", "availability", "regeneration_or_recovery"
    },
    "OPEN_RESIDUALS.csv": {
        "residual_id", "scope", "description", "status", "blocking", "next_action"
    },
    "REGENERATION_RECIPES.csv": {
        "recipe_id", "artifact_id", "input_refs", "procedure", "verification", "status"
    },
    "FILE_LIBRARY_RECOVERY.csv": {
        "recovery_id", "title", "file_library_id", "search_query", "role", "status"
    },
}


def load_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"MISSING required memory file: {path.relative_to(ROOT)}")

    if errors:
        print("\n".join(errors))
        return 2

    tables: dict[str, list[dict[str, str]]] = {}
    for name, expected in REQUIRED_COLUMNS.items():
        fields, rows = load_csv(MEM / name)
        tables[name] = rows
        missing = expected - set(fields)
        if missing:
            errors.append(f"{name}: missing columns {sorted(missing)}")
        if not rows:
            errors.append(f"{name}: empty register")

    recipes = {
        (r.get("recipe_id") or "").strip(): r
        for r in tables["REGENERATION_RECIPES.csv"]
        if (r.get("recipe_id") or "").strip()
    }

    artifact_ids: set[str] = set()
    for row in tables["ARTIFACT_INDEX.csv"]:
        aid = (row.get("artifact_id") or "").strip()
        if not aid:
            errors.append("ARTIFACT_INDEX.csv: row without artifact_id")
            continue
        if aid in artifact_ids:
            errors.append(f"ARTIFACT_INDEX.csv: duplicate artifact_id {aid}")
        artifact_ids.add(aid)

        if not (row.get("source_ref") or "").strip():
            errors.append(f"{aid}: missing source_ref")

        status = (row.get("status") or "").strip()
        availability = (row.get("availability") or "").strip()
        recovery = (row.get("regeneration_or_recovery") or "").strip()

        if status == "AT_RISK":
            errors.append(f"AT_RISK artifact forbidden: {aid}")

        if availability == "RUNTIME_ONLY":
            errors.append(f"runtime-only artifact without persistent contract: {aid}")

        if availability == "DETERMINISTIC_REGEN":
            recipe_id = recovery.split()[0] if recovery else ""
            if recipe_id not in recipes:
                errors.append(f"{aid}: missing registered regeneration recipe {recipe_id!r}")
            elif (recipes[recipe_id].get("status") or "").strip() != "READY":
                errors.append(f"{aid}: regeneration recipe {recipe_id} not READY")

        if availability in {"CHAT_ONLY", "CHAT_CURRENT"}:
            errors.append(f"chat-only artifact forbidden: {aid}")

    source_ids: set[str] = set()
    for row in tables["SOURCE_REGISTRY.csv"]:
        sid = (row.get("source_id") or "").strip()
        if not sid:
            errors.append("SOURCE_REGISTRY.csv: row without source_id")
            continue
        if sid in source_ids:
            errors.append(f"SOURCE_REGISTRY.csv: duplicate source_id {sid}")
        source_ids.add(sid)

        availability = (row.get("availability") or "").strip()
        status = (row.get("status") or "").strip()
        if availability in {"CHAT_CURRENT", "CHAT_ONLY", "RUNTIME_ONLY"}:
            errors.append(f"non-persistent source availability: {sid} = {availability}")
        if status == "PERSISTENCE_PARTIAL":
            warnings.append(f"source preserved by pointer/trace, not pixel archive: {sid}")

    for row in tables["OPEN_RESIDUALS.csv"]:
        if (row.get("status") or "").strip() == "OPEN" and not (row.get("next_action") or "").strip():
            errors.append(f"residual {(row.get('residual_id') or '?')}: OPEN without next_action")

    if warnings:
        print("MEMORY WARNINGS")
        for item in warnings:
            print(f"- {item}")

    if errors:
        print("MEMORY ERRORS")
        for item in errors:
            print(f"- {item}")
        return 2

    print(
        "MEMORY VALID: "
        f"{len(source_ids)} sources, {len(artifact_ids)} artifacts, "
        f"{len(recipes)} regeneration recipes, "
        f"{len(tables['OPEN_RESIDUALS.csv'])} residuals"
    )
    if warnings:
        print(f"Non-blocking persistence warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
