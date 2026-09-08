#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_runtime_render_cache as cache

EXPECTED_TASKS = {"ERW-N12-001", "ERW-N12-002", "ERW-N12-003", "ERW-N12-004"}
EXPECTED_SCALES = {"MICRO", "MESO", "MACRO"}
EXPECTED_DRAWINGS = {"TAV-05A", "TAV-06A"}


def fail(message: str) -> None:
    raise AssertionError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not cache.MANIFEST_PATH.is_file():
        fail("runtime render cache manifest missing")
    manifest = json.loads(cache.MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != cache.MANIFEST_SCHEMA_VERSION:
        fail("runtime render cache schema mismatch")
    if manifest.get("authority") != "READING_AID_ONLY":
        fail("runtime render cache authority mismatch")
    if manifest.get("canonical_write_authorized") is not False:
        fail("runtime render cache must not authorize canonical writes")

    expected_revision = os.getenv("GITHUB_SHA") or os.getenv("RENDER_GIT_COMMIT")
    if expected_revision and manifest.get("build_revision") != expected_revision:
        fail("runtime render cache build revision mismatch")

    entries = manifest.get("entries") or {}
    expected_count = len(EXPECTED_TASKS) * len(EXPECTED_SCALES) + len(EXPECTED_DRAWINGS)
    if len(entries) != expected_count:
        fail(f"unexpected runtime cache entry count: {len(entries)} != {expected_count}")

    for task_id in EXPECTED_TASKS:
        for scale in EXPECTED_SCALES:
            key = f"EVIDENCE_SOURCE:{task_id}:{scale}"
            if key not in entries:
                fail(f"missing cache entry {key}")
    for source_id in EXPECTED_DRAWINGS:
        key = f"DRAWING_FULL_PAGE:{source_id}:90"
        if key not in entries:
            fail(f"missing cache entry {key}")

    for key, entry in entries.items():
        if entry.get("authority") != "READING_AID_ONLY":
            fail(f"invalid authority for {key}")
        if entry.get("canonical_write_authorized") is not False:
            fail(f"canonical write unexpectedly authorized for {key}")
        target = cache.CACHE_ROOT / entry["file"]
        if not target.is_file():
            fail(f"cache file missing for {key}")
        if digest(target) != entry.get("file_sha256"):
            fail(f"cache sha mismatch for {key}")
        if not target.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            fail(f"cache file is not png for {key}")

    # Simulate the managed runtime. install() must select the cache-backed
    # functions and the exact app route must return PNG bytes without invoking
    # PyMuPDF on demand.
    os.environ["RENDER"] = "true"
    os.environ["RENDER_GIT_COMMIT"] = manifest["build_revision"]

    import cew_runtime_render_budget as budget
    import cew_source_evidence_workspace as source_workspace
    import cew_drawing_viewer as drawing_viewer

    budget.install()
    if source_workspace.render_task_source.__module__ != "cew_runtime_render_cache":
        fail("managed source renderer is not cache-backed")
    if drawing_viewer.render_full_page.__module__ != "cew_runtime_render_cache":
        fail("managed drawing renderer is not cache-backed")

    evidence_png, evidence_ctx = source_workspace.render_task_source("ERW-N12-001", "MICRO")
    if not evidence_png.startswith(b"\x89PNG"):
        fail("managed evidence cache did not return PNG")
    if evidence_ctx.get("runtime_render_source") != "BUILD_TIME_VERIFIED_CACHE":
        fail("managed evidence cache provenance missing")

    drawing_png, drawing_ctx = drawing_viewer.render_full_page("TAV-05A", 90)
    if not drawing_png.startswith(b"\x89PNG"):
        fail("managed drawing cache did not return PNG")
    if drawing_ctx.get("runtime_render_source") != "BUILD_TIME_VERIFIED_CACHE":
        fail("managed drawing cache provenance missing")

    status = cache.cache_status()
    if status.get("state") != "READY":
        fail(f"runtime cache not ready: {status}")

    print("CEW_RUNTIME_RENDER_CACHE = PASS")
    print(f"BUILD_REVISION = {manifest['build_revision']}")
    print(f"ENTRY_COUNT = {len(entries)}")
    print("MANAGED_RENDER_SOURCE = BUILD_TIME_VERIFIED_CACHE")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
