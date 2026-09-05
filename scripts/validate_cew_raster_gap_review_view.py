#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R2BR_ROOT = ROOT / ".cew_raster_bridge_review"
R2BR_MANIFEST = R2BR_ROOT / "manifest.json"
R2RV_ROOT = ROOT / "artifacts" / "cew_r2rv_review"
R2RV_MANIFEST = R2RV_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2RV_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate() -> None:
    revision = _revision()
    r2br = _load(R2BR_MANIFEST)
    r2rv = _load(R2RV_MANIFEST)

    assert r2br["build_revision"] == revision, "R2RV_R2BR_REVISION_MISMATCH"
    assert r2rv["build_revision"] == revision, "R2RV_REVISION_MISMATCH"
    assert r2rv["review_view_contract"] == "CEW_PWB005_R2RV_RASTER_GAP_REVIEW_VIEW_v1"
    assert r2rv["decision_state"] == "REVIEW_PACKAGE_READY_HUMAN_INSPECTION_REQUIRED"
    assert r2rv["region_coverage"] == "4/4"
    assert r2rv["gap_hypothesis_total"] == 10
    assert r2rv["high_contrast_review_total"] == 5
    assert r2rv["standard_review_total"] == 5
    assert r2rv["control_incomplete_review_total"] == 0
    assert r2rv["artifact_role"] == "REVISION_BOUND_HUMAN_INSPECTION_PACKAGE"
    assert r2rv["runtime_dependency"] is False
    assert r2rv["review_view_authority"] == "NONE"
    assert r2rv["overlay_role"] == "HUMAN_INSPECTION_PROPOSAL_ONLY"
    assert r2rv["review_priority_is_correctness_threshold"] is False
    assert r2rv["gap_overlay_is_geometry"] is False
    assert r2rv["bridge_candidate_authorized"] is False
    assert r2rv["geometry_materialization_authorized"] is False
    assert r2rv["r2c_scene_adapter_authorized"] is False
    assert r2rv["technical_identity_authorized"] is False
    assert r2rv["structural_identity_authorized"] is False
    assert r2rv["canonical_write_authorized"] is False
    assert r2rv["engineering_authority_effect"] == "NONE"

    index_path = R2RV_ROOT / r2rv["index_filename"]
    assert index_path.is_file(), "R2RV_INDEX_MISSING"
    assert _sha256(index_path) == r2rv["index_sha256"], "R2RV_INDEX_HASH_MISMATCH"
    index_html = index_path.read_text(encoding="utf-8")
    for marker in (
        "Solo ispezione umana",
        "review_view_authority=NONE",
        "bridge_candidate_authorized=false",
        "r2c_scene_adapter_authorized=false",
        "canonical_write_authorized=false",
    ):
        assert marker in index_html, f"R2RV_INDEX_MARKER_MISSING:{marker}"

    br_entries = {row["evidence_region_id"]: row for row in r2br["regions"]}
    rv_entries = {row["evidence_region_id"]: row for row in r2rv["regions"]}
    assert set(br_entries) == EXPECTED_REGIONS
    assert set(rv_entries) == EXPECTED_REGIONS

    seen: set[str] = set()
    high = standard = incomplete = 0

    for region_id in sorted(EXPECTED_REGIONS):
        br = _load(R2BR_ROOT / br_entries[region_id]["result_filename"])
        rv_entry = rv_entries[region_id]
        review_path = R2RV_ROOT / rv_entry["metadata_filename"]
        html_path = R2RV_ROOT / rv_entry["html_filename"]
        crop_path = R2RV_ROOT / rv_entry["source_crop_300_filename"]
        assert review_path.is_file() and html_path.is_file() and crop_path.is_file(), f"R2RV_REGION_FILE_MISSING:{region_id}"
        assert _sha256(review_path) == rv_entry["metadata_sha256"]
        assert _sha256(html_path) == rv_entry["html_sha256"]
        assert _sha256(crop_path) == rv_entry["source_crop_300_sha256"]

        review = _load(review_path)
        assert review["build_revision"] == revision
        assert review["evidence_region_id"] == region_id
        for key in ("source_code", "source_version_id", "source_sha256", "page_id", "transform_id"):
            assert review[key] == br[key], f"R2RV_PROVENANCE_DRIFT:{region_id}:{key}"
        assert review["review_view_authority"] == "NONE"
        assert review["overlay_role"] == "HUMAN_INSPECTION_PROPOSAL_ONLY"
        assert review["review_priority_is_correctness_threshold"] is False
        assert review["gap_overlay_is_geometry"] is False
        assert review["bridge_candidate_authorized"] is False
        assert review["geometry_materialization_authorized"] is False
        assert review["r2c_scene_adapter_authorized"] is False
        assert review["technical_identity_authorized"] is False
        assert review["structural_identity_authorized"] is False
        assert review["canonical_write_authorized"] is False
        assert review["engineering_authority_effect"] == "NONE"

        br_rows = {row["gap_hypothesis_id"]: row for row in br["review_rows"]}
        rv_rows = {row["gap_hypothesis_id"]: row for row in review["review_rows"]}
        assert set(br_rows) == set(rv_rows), f"R2RV_GAP_RETENTION_FAILURE:{region_id}"
        for gap_id in sorted(br_rows):
            assert gap_id not in seen, f"R2RV_DUPLICATE_GAP:{gap_id}"
            seen.add(gap_id)
            assert rv_rows[gap_id] == br_rows[gap_id], f"R2RV_REVIEW_ROW_DRIFT:{gap_id}"
            tier = rv_rows[gap_id]["review_tier"]
            if tier == "HIGH_CONTRAST_REVIEW":
                high += 1
            elif tier == "STANDARD_REVIEW":
                standard += 1
            elif tier == "CONTROL_INCOMPLETE_REVIEW":
                incomplete += 1
            else:
                raise AssertionError(f"R2RV_UNKNOWN_REVIEW_TIER:{tier}")

        html_text = html_path.read_text(encoding="utf-8")
        required_html_markers = (
            "SOLO ISPEZIONE UMANA",
            "HUMAN_INSPECTION_PROPOSAL_ONLY",
            "Bridge candidate:</strong> false",
            "R2C:</strong> false",
            "Canonical write:</strong> false",
            "toggleHigh",
            "toggleStandard",
            "viewBox=\"0 0 1 1\"",
            "HIGH_CONTRAST_REVIEW",
            "STANDARD_REVIEW",
        )
        for marker in required_html_markers:
            assert marker in html_text, f"R2RV_HTML_MARKER_MISSING:{region_id}:{marker}"
        assert html_text.count('data-gap-id="') == len(br_rows), f"R2RV_OVERLAY_COUNT_MISMATCH:{region_id}"
        for gap_id in br_rows:
            assert gap_id in html_text, f"R2RV_GAP_NOT_RENDERED:{region_id}:{gap_id}"

    assert len(seen) == 10
    assert high == 5 and standard == 5 and incomplete == 0

    print("CEW_PWB005_R2RV_RASTER_GAP_REVIEW_VIEW = PASS")
    print("REGION_COVERAGE = 4/4")
    print("GAP_RETENTION = 10/10")
    print("HIGH_CONTRAST_REVIEW_TOTAL = 5")
    print("STANDARD_REVIEW_TOTAL = 5")
    print("CONTROL_INCOMPLETE_REVIEW_TOTAL = 0")
    print("ARTIFACT_ROLE = REVISION_BOUND_HUMAN_INSPECTION_PACKAGE")
    print("RUNTIME_DEPENDENCY = false")
    print("REVIEW_VIEW_AUTHORITY = NONE")
    print("OVERLAY_ROLE = HUMAN_INSPECTION_PROPOSAL_ONLY")
    print("GAP_OVERLAY_IS_GEOMETRY = false")
    print("R2_BRIDGE_CANDIDATE_AUTHORIZED = false")
    print("PWB005_R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("HUMAN_INSPECTION_REQUIRED = true")


if __name__ == "__main__":
    validate()
