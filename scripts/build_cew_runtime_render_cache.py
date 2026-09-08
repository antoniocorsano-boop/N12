#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import cew_runtime_render_budget as budget
import cew_runtime_render_cache as cache
import cew_source_evidence_workspace as source_workspace

SCALES = ("MICRO", "MESO", "MACRO")
DRAWING_DPI = 90


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or "UNRESOLVED_BUILD_REVISION"
    )


def _write_png(name: str, payload: bytes) -> tuple[str, str, int]:
    target = cache.CACHE_ROOT / name
    target.write_bytes(payload)
    return name, _sha256(payload), len(payload)


def main() -> int:
    if cache.CACHE_ROOT.exists():
        shutil.rmtree(cache.CACHE_ROOT)
    cache.CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    maps = source_workspace.maps()
    task_ids = sorted(maps["bindings"].keys())
    source_ids = sorted({maps["tasks"][task_id]["source_id"] for task_id in task_ids})
    entries: dict[str, dict] = {}

    for task_id in task_ids:
        ctx = source_workspace.task_context(task_id)
        for scale in SCALES:
            png, render_ctx = budget.render_task_source_bounded(task_id, scale)
            filename, digest, size = _write_png(f"evidence-{task_id}-{scale}.png", png)
            key = f"EVIDENCE_SOURCE:{task_id}:{scale}"
            entries[key] = {
                "kind": "EVIDENCE_SOURCE",
                "task_id": task_id,
                "scale": scale,
                "source_id": ctx["task"]["source_id"],
                "source_version_id": ctx["binding"]["source_version_id"],
                "page_id": ctx["page"]["page_id"],
                "evidence_region_id": ctx["region"]["evidence_region_id"],
                "source_sha256": render_ctx["verified_sha256"],
                "requested_dpi": render_ctx["requested_dpi"],
                "effective_dpi": render_ctx["effective_dpi"],
                "render_pixels": render_ctx["render_pixels"],
                "render_pixel_budget": render_ctx["render_pixel_budget"],
                "file": filename,
                "file_sha256": digest,
                "file_bytes": size,
                "authority": "READING_AID_ONLY",
                "canonical_write_authorized": False,
            }

    for source_id in source_ids:
        png, render_ctx = budget.render_full_page_bounded(source_id, DRAWING_DPI)
        filename, digest, size = _write_png(f"drawing-{source_id}-{DRAWING_DPI}.png", png)
        key = f"DRAWING_FULL_PAGE:{source_id}:{DRAWING_DPI}"
        entries[key] = {
            "kind": "DRAWING_FULL_PAGE",
            "source_id": source_id,
            "page_id": render_ctx["page"]["page_id"],
            "source_sha256": render_ctx["verified_sha256"],
            "requested_dpi": render_ctx["requested_dpi"],
            "effective_dpi": render_ctx["effective_dpi"],
            "render_pixels": render_ctx["render_pixels"],
            "render_pixel_budget": render_ctx["render_pixel_budget"],
            "file": filename,
            "file_sha256": digest,
            "file_bytes": size,
            "authority": "READING_AID_ONLY",
            "canonical_write_authorized": False,
        }

    manifest = {
        "schema_version": cache.MANIFEST_SCHEMA_VERSION,
        "build_revision": _revision(),
        "archive_commit": source_workspace.ARCHIVE_COMMIT,
        "generator": "build_cew_runtime_render_cache.py",
        "entry_count": len(entries),
        "entries": entries,
        "authority": "READING_AID_ONLY",
        "canonical_write_authorized": False,
    }
    cache.MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print("CEW_RUNTIME_RENDER_CACHE_BUILD = PASS")
    print(f"BUILD_REVISION = {manifest['build_revision']}")
    print(f"ENTRY_COUNT = {len(entries)}")
    print(f"CACHE_ROOT = {cache.CACHE_ROOT}")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
