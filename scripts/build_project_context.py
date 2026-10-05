#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PATH = Path("knowledge/CONTEXT_PACK_CURRENT.json")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def reference_status(text: str) -> str:
    patterns = [
        r"\*\*Stato:\*\*\s*([^\n]+)",
        r"\*\*Status:\*\*\s*([^\n]+)",
        r"^Status:\s*([^\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "REFERENCE"


def discover_references(root: Path) -> list[dict[str, str]]:
    ref_dir = root / "docs" / "REFERENCE"
    if not ref_dir.exists():
        return []
    refs = []
    for path in sorted(ref_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        refs.append({
            "path": path.relative_to(root).as_posix(),
            "title": first_heading(text, path.stem),
            "status": reference_status(text),
            "sha256": sha256_file(path),
        })
    return refs


def fingerprint(root: Path, rel: str) -> str | None:
    path = root / rel
    return sha256_file(path) if path.exists() else None


def build_context_pack(root: Path = ROOT) -> dict:
    manifest = read_json(root / "knowledge" / "KNOWLEDGE_MANIFEST.json", {}) or {}
    state = read_json(root / "knowledge" / "CURRENT_STATE.json", {}) or {}
    product = read_json(root / "data" / "canonical" / "CEW_PROJECT_STATE_CURRENT_v1.json", {}) or {}

    automation = state.get("automation") or manifest.get("automation") or {}
    next_action = state.get("next_action") or {}
    if isinstance(next_action, str):
        next_task = next_action
    else:
        next_task = next_action.get("task") or next_action.get("work_item") or next_action

    product_item = product.get("current_product_work_item") or {}
    product_item_id = product_item.get("id") if isinstance(product_item, dict) else product_item
    product_item_state = product_item.get("state") if isinstance(product_item, dict) else None

    refs = discover_references(root)

    pack = {
        "schema_version": "1.0",
        "purpose": "Compact deterministic project bootstrap. Read full sources only when the active task requires them.",
        "project": {
            "id": manifest.get("project") or "N12",
            "repository": manifest.get("repository") or "antoniocorsano-boop/N12",
            "canonical_branch": manifest.get("canonical_branch"),
            "domain": manifest.get("current_domain"),
        },
        "engineering": {
            "gate": state.get("gate"),
            "status": state.get("status"),
            "objective": state.get("objective"),
            "current_work_item": automation.get("current_work_item") or (
                next_action.get("work_item") if isinstance(next_action, dict) else None
            ),
            "next_action": next_task,
            "completion_condition": state.get("completion_condition"),
        },
        "product": {
            "status": product.get("status"),
            "current_work_item": product_item_id,
            "current_work_item_state": product_item_state,
            "next_action": product.get("next_action"),
        },
        "references": refs,
        "invariants": [
            "Repository state, not chat history, is the continuity authority.",
            "Unregistered artifacts are non-authoritative by default.",
            "No UI, agent result, IFC file or solver result becomes engineering authority by itself.",
            "DOC/MIS/RIF/INF/INC/ND and derived MOD/POST states must not be silently promoted.",
            state.get("anti_restart_rule") or "Reuse validated checkpoints; reopen only the smallest conflicting claim.",
        ],
        "required_reads": {
            "orientation": [
                CONTEXT_PATH.as_posix(),
                *[ref["path"] for ref in refs],
            ],
            "engineering_mutation": [
                "knowledge/KNOWLEDGE_MANIFEST.json",
                "knowledge/CURRENT_STATE.json",
                "knowledge/ARTIFACT_REGISTRY.csv",
                "docs/PROTOCOLLO_CANONICO.md",
            ],
            "product_mutation": [
                "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json",
                "automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json",
            ],
        },
        "source_fingerprints": {
            "knowledge_manifest": fingerprint(root, "knowledge/KNOWLEDGE_MANIFEST.json"),
            "current_state": fingerprint(root, "knowledge/CURRENT_STATE.json"),
            "artifact_registry": fingerprint(root, "knowledge/ARTIFACT_REGISTRY.csv"),
            "product_state": fingerprint(root, "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"),
        },
        "rule": "Use this pack for orientation. Before any canonical/product mutation, read the relevant full sources in required_reads.",
    }
    return pack


def write_context_pack(root: Path = ROOT) -> Path:
    target = root / CONTEXT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_context_pack(root), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def context_pack_is_current(root: Path = ROOT) -> bool:
    target = root / CONTEXT_PATH
    if not target.exists():
        return False
    try:
        existing = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return existing == build_context_pack(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.write:
        path = write_context_pack(ROOT)
        print(f"CONTEXT_PACK_WRITTEN={path.relative_to(ROOT).as_posix()}")
        return 0
    if args.check:
        ok = context_pack_is_current(ROOT)
        print("CONTEXT_PACK_CURRENT=" + ("YES" if ok else "NO"))
        return 0 if ok else 1

    print(json.dumps(build_context_pack(ROOT), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
