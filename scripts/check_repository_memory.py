#!/usr/bin/env python3
"""Validate the N12 repository-memory layer.

The validator is intentionally dependency-free. It checks that the canonical
memory files exist, required CSV columns are present, and continuity risks are
made explicit instead of disappearing silently.
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
    ROOT / "docs" / "REPOSITORY_MEMORY_PROTOCOL.md",
]

REQUIRED_COLUMNS = {
    "SOURCE_REGISTRY.csv": {
        "source_id", "kind", "repo_path", "evidence_status", "availability", "status"
    },
    "ARTIFACT_INDEX.csv": {
        "artifact_id", "artifact_type", "repo_path_or_ref", "status",
        "evidence_status", "source_ref", "availability"
    },
    "OPEN_RESIDUALS.csv": {
        "residual_id", "scope", "description", "status", "blocking", "next_action"
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

    for name, expected in REQUIRED_COLUMNS.items():
        fields, rows = load_csv(MEM / name)
        missing = expected - set(fields)
        if missing:
            errors.append(f"{name}: missing columns {sorted(missing)}")
        if not rows:
            errors.append(f"{name}: empty register")

    _, artifacts = load_csv(MEM / "ARTIFACT_INDEX.csv")
    artifact_ids = set()
    for row in artifacts:
        aid = (row.get("artifact_id") or "").strip()
        if not aid:
            errors.append("ARTIFACT_INDEX.csv: row without artifact_id")
            continue
        if aid in artifact_ids:
            errors.append(f"ARTIFACT_INDEX.csv: duplicate artifact_id {aid}")
        artifact_ids.add(aid)
        if not (row.get("source_ref") or "").strip():
            errors.append(f"{aid}: missing source_ref")
        if (row.get("status") or "").strip() == "AT_RISK":
            warnings.append(f"AT_RISK artifact: {aid} -> {(row.get('repo_path_or_ref') or '').strip()}")

    _, sources = load_csv(MEM / "SOURCE_REGISTRY.csv")
    source_ids = set()
    for row in sources:
        sid = (row.get("source_id") or "").strip()
        if not sid:
            errors.append("SOURCE_REGISTRY.csv: row without source_id")
            continue
        if sid in source_ids:
            errors.append(f"SOURCE_REGISTRY.csv: duplicate source_id {sid}")
        source_ids.add(sid)
        availability = (row.get("availability") or "").strip()
        if availability in {"CHAT_CURRENT", "RUNTIME_ONLY"}:
            warnings.append(f"non-persistent source availability: {sid} = {availability}")

    _, residuals = load_csv(MEM / "OPEN_RESIDUALS.csv")
    for row in residuals:
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

    print(f"MEMORY VALID: {len(sources)} sources, {len(artifacts)} artifacts, {len(residuals)} residuals")
    if warnings:
        print(f"Continuity risks explicitly tracked: {len(warnings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
