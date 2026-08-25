#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "knowledge" / "KNOWLEDGE_MANIFEST.json"
REQUIRED = [
    "knowledge/ARTIFACT_REGISTRY_CEW_FOUNDATION_PATCH_v1.csv",
    "knowledge/ARTIFACT_REGISTRY_CEW_SOURCE_FOUNDATION_PATCH_v1.csv",
    "knowledge/ARTIFACT_REGISTRY_CEW_EVIDENCE_FOUNDATION_PATCH_v1.csv",
    "knowledge/ARTIFACT_REGISTRY_CEW_SOURCE_VIEWER_PATCH_v1.csv",
    "knowledge/ARTIFACT_REGISTRY_CEW_AI_OBSERVATION_PATCH_v1.csv",
]


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    patches = list(data.get("artifact_registry_patches", []))
    changed = False
    for item in REQUIRED:
        if item not in patches:
            patches.append(item)
            changed = True
    data["artifact_registry_patches"] = patches
    MANIFEST.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("CEW_ARTIFACT_PATCH_REGISTRATION=" + ("UPDATED" if changed else "ALREADY_CURRENT"))
    for item in REQUIRED:
        print("REGISTERED=" + item)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
