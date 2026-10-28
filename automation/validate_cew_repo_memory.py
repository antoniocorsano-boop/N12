#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

REGISTRY_RELATIVE_PATH = Path("governance/repo-memory/CEW_CAPABILITY_REGISTRY_v1.json")
LEGACY_ASSESSMENTS_RELATIVE_PATH = Path(
    "governance/repo-memory/CEW_LEGACY_PLAN_REUSE_ASSESSMENTS_v1.json"
)
REUSE_DECISION_GLOB = "*_REUSE_DECISION_v1.json"
PLAN_GLOB = "*cew*.md"
MEMORY_HEADING = "## Repository Memory / Reuse Assessment"


def _load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing required repository-memory file: {path}")
        return None
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"repository-memory JSON root must be an object: {path}")
        return None
    return payload


def _validate_registry(root: Path, errors: list[str]) -> tuple[set[str], set[str]]:
    path = root / REGISTRY_RELATIVE_PATH
    registry = _load_json(path, errors)
    if registry is None:
        return set(), set()
    if registry.get("schema_version") != "CEW_CAPABILITY_REGISTRY_v1":
        errors.append(f"unexpected capability-registry schema in {path}")

    vocabulary_raw = registry.get("reuse_vocabulary")
    if not isinstance(vocabulary_raw, list) or not vocabulary_raw:
        errors.append(f"reuse_vocabulary must be a non-empty list in {path}")
        vocabulary: set[str] = set()
    else:
        vocabulary = {str(item) for item in vocabulary_raw if str(item).strip()}

    capabilities_raw = registry.get("capabilities")
    if not isinstance(capabilities_raw, list):
        errors.append(f"capabilities must be a list in {path}")
        return set(), vocabulary

    capability_ids: set[str] = set()
    for index, capability in enumerate(capabilities_raw):
        if not isinstance(capability, dict):
            errors.append(f"capabilities[{index}] must be an object in {path}")
            continue
        capability_id = str(capability.get("capability_id") or "").strip()
        if not capability_id:
            errors.append(f"capabilities[{index}] is missing capability_id in {path}")
            continue
        if capability_id in capability_ids:
            errors.append(f"duplicate capability_id {capability_id} in {path}")
        capability_ids.add(capability_id)
        disposition = capability.get("reuse_disposition")
        if disposition is not None and str(disposition) not in vocabulary:
            errors.append(
                f"invalid reuse disposition {disposition!s} for {capability_id}; allowed={sorted(vocabulary)}"
            )
    return capability_ids, vocabulary


def _validate_reuse_decisions(
    root: Path,
    capability_ids: set[str],
    vocabulary: set[str],
    errors: list[str],
) -> None:
    directory = root / "governance" / "repo-memory"
    if not directory.exists():
        errors.append(f"missing repository-memory directory: {directory}")
        return
    for path in sorted(directory.glob(REUSE_DECISION_GLOB)):
        payload = _load_json(path, errors)
        if payload is None:
            continue
        decision_id = str(payload.get("decision_id") or path.name)
        consulted = payload.get("consulted_capabilities")
        if not isinstance(consulted, list) or not consulted:
            errors.append(f"{decision_id}: consulted_capabilities must be a non-empty list")
            consulted = []
        for capability_id in consulted:
            capability_id = str(capability_id)
            if capability_id not in capability_ids:
                errors.append(f"{decision_id}: unknown capability reference {capability_id}")
        decisions = payload.get("decisions")
        if not isinstance(decisions, list) or not decisions:
            errors.append(f"{decision_id}: decisions must be a non-empty list")
            continue
        for index, row in enumerate(decisions):
            if not isinstance(row, dict):
                errors.append(f"{decision_id}: decisions[{index}] must be an object")
                continue
            capability_id = str(row.get("source_capability") or "").strip()
            if capability_id and capability_id not in capability_ids:
                errors.append(
                    f"{decision_id}: decisions[{index}] references unknown capability {capability_id}"
                )
            disposition = row.get("reuse_disposition")
            if disposition is not None and str(disposition) not in vocabulary:
                errors.append(
                    f"{decision_id}: invalid reuse disposition {disposition!s}; allowed={sorted(vocabulary)}"
                )


def _validate_legacy_assessments(
    root: Path,
    capability_ids: set[str],
    errors: list[str],
) -> set[str]:
    path = root / LEGACY_ASSESSMENTS_RELATIVE_PATH
    if not path.exists():
        return set()
    payload = _load_json(path, errors)
    if payload is None:
        return set()
    if payload.get("schema_version") != "CEW_LEGACY_PLAN_REUSE_ASSESSMENTS_v1":
        errors.append(f"unexpected legacy-plan assessment schema in {path}")
        return set()
    rows = payload.get("plans")
    if not isinstance(rows, list) or not rows:
        errors.append(f"legacy-plan assessments must contain a non-empty plans list in {path}")
        return set()

    governed_paths: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"legacy plans[{index}] must be an object in {path}")
            continue
        relative = str(row.get("path") or "").strip()
        if not relative.startswith("docs/superpowers/plans/") or not relative.endswith(".md"):
            errors.append(f"legacy plans[{index}] has invalid plan path {relative!r}")
            continue
        if relative in governed_paths:
            errors.append(f"duplicate legacy plan assessment for {relative}")
            continue
        governed_paths.add(relative)
        if not (root / relative).is_file():
            errors.append(f"legacy plan assessment points to missing plan: {relative}")
        if row.get("status") != "HISTORICAL_PLAN_PREDATES_REPO_MEMORY":
            errors.append(f"legacy plan {relative} has invalid status")
        if row.get("assessment") != "REUSE_FIRST_REVIEW_RECORDED_EXTERNALLY":
            errors.append(f"legacy plan {relative} has invalid assessment state")
        consulted = row.get("consulted_capabilities")
        if not isinstance(consulted, list) or not consulted:
            errors.append(f"legacy plan {relative} requires consulted_capabilities")
            continue
        for capability_id in consulted:
            capability_id = str(capability_id)
            if capability_id not in capability_ids:
                errors.append(
                    f"legacy plan {relative} references unknown capability {capability_id}"
                )
    return governed_paths


def _validate_plans(root: Path, errors: list[str], legacy_paths: set[str]) -> None:
    directory = root / "docs" / "superpowers" / "plans"
    if not directory.exists():
        return
    for path in sorted(directory.glob(PLAN_GLOB)):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        upper = text.upper()
        if "SUPERSEDED" in upper or "DO NOT CONTINUE" in upper:
            continue
        if not path.name.startswith("2026-10-28-"):
            continue
        if MEMORY_HEADING in text:
            continue
        if relative in legacy_paths:
            continue
        errors.append(f"{path}: active CEW plan must contain '{MEMORY_HEADING}'")


def validate_repository_memory(root: Path) -> list[str]:
    root = Path(root)
    errors: list[str] = []
    capability_ids, vocabulary = _validate_registry(root, errors)
    if capability_ids and vocabulary:
        _validate_reuse_decisions(root, capability_ids, vocabulary, errors)
    legacy_paths = _validate_legacy_assessments(root, capability_ids, errors)
    _validate_plans(root, errors, legacy_paths)
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository_memory(root)
    if errors:
        for error in errors:
            print(f"CEW_REPO_MEMORY_FAIL: {error}")
        return 1
    print("CEW_REPO_MEMORY_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
