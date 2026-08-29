#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "knowledge" / "KNOWLEDGE_MANIFEST.json"
STATE_PATH = ROOT / "knowledge" / "CURRENT_STATE.json"
REGISTRY_PATH = ROOT / "knowledge" / "ARTIFACT_REGISTRY.csv"

ALLOWED_AUTHORITIES = {
    "SOURCE_PRIMARY", "SOURCE_REFERENCE", "OBSERVATION", "CLAIM_LEDGER",
    "CANONICAL", "DERIVED", "PROCEDURE", "SKILL", "HISTORICAL"
}
ALLOWED_STATUSES = {
    "UNREVIEWED", "OBSERVED", "SUPPORTED", "CROSS_VALIDATED", "CURRENT",
    "RESIDUAL", "CONFLICT", "REOPENED", "SUPERSEDED", "TOMBSTONE",
    "HISTORICAL_ONLY", "SUSPENDED"
}
ALLOWED_FEED = {"YES", "NO", "CONDITIONAL"}
BLOCKED_FEED_STATUSES = {
    "CONFLICT", "REOPENED", "SUPERSEDED", "TOMBSTONE", "HISTORICAL_ONLY", "SUSPENDED"
}


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_registry(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def exists_rel(rel: str) -> bool:
    return (ROOT / rel).exists()


def registry_patch_rels(manifest: dict) -> list[str]:
    rels: list[str] = []
    legacy = manifest.get("artifact_registry_patch")
    if legacy:
        rels.append(legacy)
    for rel in manifest.get("artifact_registry_patches", []) or []:
        if rel and rel not in rels:
            rels.append(rel)
    return rels


def validate_registry_rows(rows, label: str, *, allow_override_paths: bool = False):
    errors: list[str] = []
    required_cols = {
        "artifact_id", "path", "domain", "artifact_type", "authority", "status",
        "may_feed_canonical", "validation_method", "replaces_or_relates", "note"
    }
    if not rows:
        errors.append(f"{label} is empty")
        return errors
    if not required_cols.issubset(rows[0].keys()):
        errors.append(f"{label} missing columns: {sorted(required_cols - set(rows[0].keys()))}")
        return errors

    ids = [r.get("artifact_id", "").strip() for r in rows]
    paths = [r.get("path", "").strip() for r in rows]
    if len(ids) != len(set(ids)):
        errors.append(f"duplicate artifact_id in {label}")
    if not allow_override_paths and len(paths) != len(set(paths)):
        errors.append(f"duplicate path in {label}")

    for i, r in enumerate(rows, start=2):
        aid = r.get("artifact_id", "").strip() or f"line-{i}"
        rel = r.get("path", "").strip()
        authority = r.get("authority", "").strip()
        status = r.get("status", "").strip()
        feed = r.get("may_feed_canonical", "").strip()

        if not rel:
            errors.append(f"{label} {aid}: empty path")
            continue
        if not exists_rel(rel):
            errors.append(f"{label} {aid}: registered path does not exist: {rel}")
        if authority not in ALLOWED_AUTHORITIES:
            errors.append(f"{label} {aid}: invalid authority={authority}")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{label} {aid}: invalid status={status}")
        if feed not in ALLOWED_FEED:
            errors.append(f"{label} {aid}: invalid may_feed_canonical={feed}")
        if status in BLOCKED_FEED_STATUSES and feed != "NO":
            errors.append(f"{label} {aid}: blocked status {status} must have may_feed_canonical=NO")
        if authority == "HISTORICAL" and feed != "NO":
            errors.append(f"{label} {aid}: HISTORICAL authority must not feed canonical")
    return errors


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for p in [ROOT / "AGENTS.md", MANIFEST_PATH, STATE_PATH, REGISTRY_PATH]:
        if not p.exists():
            errors.append(f"missing core file: {p.relative_to(ROOT)}")
    if errors:
        return errors, warnings

    try:
        manifest = load_json(MANIFEST_PATH)
    except Exception as exc:
        errors.append(f"invalid manifest JSON: {exc}")
        return errors, warnings

    try:
        state = load_json(STATE_PATH)
    except Exception as exc:
        errors.append(f"invalid current state JSON: {exc}")
        return errors, warnings

    try:
        rows = load_registry(REGISTRY_PATH)
    except Exception as exc:
        errors.append(f"invalid artifact registry CSV: {exc}")
        return errors, warnings

    errors.extend(validate_registry_rows(rows, "artifact registry"))

    all_patch_rows: list[dict] = []
    seen_patch_ids: set[str] = set()
    for patch_rel in registry_patch_rels(manifest):
        patch_path = ROOT / patch_rel
        if not patch_path.exists():
            errors.append(f"artifact registry patch missing: {patch_rel}")
            continue
        try:
            patch_rows = load_registry(patch_path)
            errors.extend(
                validate_registry_rows(
                    patch_rows, f"artifact registry patch {patch_rel}", allow_override_paths=True
                )
            )
        except Exception as exc:
            errors.append(f"invalid artifact registry patch CSV {patch_rel}: {exc}")
            continue
        for row in patch_rows:
            aid = row.get("artifact_id", "").strip()
            if aid in seen_patch_ids:
                errors.append(f"artifact registry patches reuse artifact_id: {aid}")
            seen_patch_ids.add(aid)
        all_patch_rows.extend(patch_rows)

    base_ids = {r.get("artifact_id", "").strip() for r in rows}
    patch_ids = {r.get("artifact_id", "").strip() for r in all_patch_rows}
    if base_ids & patch_ids:
        errors.append(
            "artifact registry patch reuses base artifact_id(s): "
            + ", ".join(sorted(base_ids & patch_ids))
        )

    # Patch rows intentionally override base rows by path while preserving the base registry as history.
    by_path = {r.get("path", "").strip(): r for r in rows}
    for r in all_patch_rows:
        by_path[r.get("path", "").strip()] = r

    if manifest.get("entrypoint") != "AGENTS.md":
        errors.append("manifest entrypoint must be AGENTS.md")
    for key, expected in [
        ("state_file", "knowledge/CURRENT_STATE.json"),
        ("artifact_registry", "knowledge/ARTIFACT_REGISTRY.csv")
    ]:
        if manifest.get(key) != expected:
            errors.append(f"manifest {key} must be {expected}")

    if manifest.get("current_gate") != state.get("gate"):
        errors.append(
            f"gate mismatch manifest={manifest.get('current_gate')} state={state.get('gate')}"
        )

    for skill in manifest.get("active_skills", []):
        for key in ["path", "runner"]:
            rel = skill.get(key)
            if not rel or not exists_rel(rel):
                errors.append(f"active skill {skill.get('id')} missing {key}: {rel}")
            elif rel not in by_path:
                errors.append(f"active skill {skill.get('id')} {key} not registered: {rel}")

    for rel in manifest.get("active_procedures", []):
        if not exists_rel(rel):
            errors.append(f"active procedure missing: {rel}")
        elif rel not in by_path:
            errors.append(f"active procedure not registered: {rel}")

    automation = manifest.get("automation", {})
    if automation.get("enabled"):
        for key in ["contract", "queue", "runner", "procedure", "workflow"]:
            rel = automation.get(key)
            if not rel or not exists_rel(rel):
                errors.append(f"automation {key} missing: {rel}")
            elif rel not in by_path:
                errors.append(f"automation {key} not registered: {rel}")

    pt = manifest.get("pt_geometry", {})
    current_master = pt.get("current_master")
    old_master = pt.get("old_master")

    if current_master:
        r = by_path.get(current_master)
        if not r:
            errors.append(f"current PT master not registered: {current_master}")
        else:
            if r.get("authority") != "CANONICAL":
                errors.append("PT current master must have CANONICAL authority")
            if r.get("status") != "CURRENT":
                errors.append("PT current master must have CURRENT status")
            if r.get("may_feed_canonical") != "YES":
                errors.append("PT current master must be allowed to feed canonical")
        if state.get("geometry_master_status") != "CURRENT":
            errors.append("CURRENT_STATE geometry_master_status must be CURRENT after Master promotion")
    elif old_master:
        r = by_path.get(old_master)
        if not r:
            errors.append(f"old PT master not registered: {old_master}")
        else:
            if r.get("status") != "SUSPENDED":
                errors.append("PT old master must be SUSPENDED while raster reconstruction gate is open")
            if r.get("may_feed_canonical") != "NO":
                errors.append("PT old master must not feed canonical while suspended")
        if state.get("geometry_master_status") != "SUSPENDED":
            errors.append("CURRENT_STATE geometry_master_status must be SUSPENDED while historical Master is blocked")
    else:
        errors.append("pt_geometry must declare either old_master or current_master")

    gate_path = state.get("blocking_gate")
    if gate_path:
        if not exists_rel(gate_path):
            errors.append(f"blocking gate missing: {gate_path}")
        elif gate_path not in by_path:
            errors.append(f"blocking gate is not registered: {gate_path}")
    elif state.get("status") not in {"COMPLETE", "COMPLETE_WITH_PROVENANCE_WATCHES"}:
        errors.append("blocking_gate may be omitted only for a completed state")

    output = state.get("next_action", {}).get("output")
    if output and exists_rel(output):
        warnings.append(f"next_action output already exists; CURRENT_STATE may need advancement: {output}")

    required_pipeline = pt.get("required_pipeline", [])
    missing_pipeline = [name for name in required_pipeline if not (ROOT / "data" / "canonical" / name).exists()]
    if missing_pipeline:
        warnings.append(
            "PT geometry pipeline incomplete; missing artifacts: " + ", ".join(missing_pipeline)
        )

    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for token in ["knowledge/KNOWLEDGE_MANIFEST.json", "knowledge/CURRENT_STATE.json", "knowledge/ARTIFACT_REGISTRY.csv"]:
        if token not in agents_text:
            errors.append(f"AGENTS.md does not reference required entry: {token}")
    if automation.get("enabled") and "scripts/n12_orchestrator.py" not in agents_text:
        errors.append("AGENTS.md does not reference the enabled N12 orchestrator")

    return errors, warnings


def main() -> int:
    errors, warnings = validate()
    if errors:
        print("KNOWLEDGE_SYSTEM_VALIDATION = FAIL")
        for e in errors:
            print(f"ERROR: {e}")
        for w in warnings:
            print(f"WARN: {w}")
        return 1

    print("KNOWLEDGE_SYSTEM_VALIDATION = PASS")
    for w in warnings:
        print(f"WARN: {w}")
    print("Architecture and authority contracts are coherent.")
    print("Open domain gates are reported as warnings and remain subject to specialist semantic QA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
