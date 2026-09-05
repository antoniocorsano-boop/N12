#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / ".cew_evidence_region_content_diagnostic"
MANIFEST = ASSET_ROOT / "manifest.json"
ALLOWED = {
    "VECTOR",
    "RASTER",
    "TEXT",
    "MIXED",
    "REGION_MAPPING_ERROR",
    "EMPTY",
}
EXPECTED_EDGE_TOLERANCE_PT = 0.01


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _runtime_revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or ""
    ).strip()


def main() -> int:
    if not MANIFEST.is_file():
        raise AssertionError("PWB005_R1_DIAGNOSTIC_MANIFEST_MISSING")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "1.1"
    assert manifest["diagnostic_contract"] == "CEW_PWB005_R1_EVIDENCE_REGION_CONTENT_DIAGNOSTIC_v1"
    assert manifest["source_coverage"] == "4/4"
    assert manifest["governed_region_count"] == 4
    assert set(manifest["classification_vocabulary"]) == ALLOWED
    assert manifest["region_edge_tolerance_pt"] == EXPECTED_EDGE_TOLERANCE_PT
    assert manifest["containment_method"] == "SOURCE_PAGE_EDGE_TOLERANCE"
    assert manifest["r1a_remediation_basis"] == "FLOATING_POINT_CONTAINMENT_TOLERANCE"
    assert manifest["canonical_write_authorized"] is False
    assert manifest["engineering_authority_effect"] == "NONE"
    assert manifest["hva_execution_authorized"] is False
    assert manifest["diagnostic_state"] == "COMPLETE_WITH_FINDINGS"

    revision = _runtime_revision()
    if revision:
        assert manifest["build_revision"] == revision, (manifest["build_revision"], revision)

    results = manifest["region_results"]
    assert len(results) == 4
    ids = [row["evidence_region_id"] for row in results]
    assert len(set(ids)) == 4

    for row in results:
        assert row["classification"] in ALLOWED
        assert row["source_version_id"]
        assert row["source_sha256"] and len(row["source_sha256"]) == 64
        assert row["page_id"]
        assert row["transform_id"]
        assert row["region"]["coordinate_space"] == "NORMALIZED_0_1"
        assert row["ocr_used"] is False
        assert row["technical_identity_authorized"] is False
        assert row["canonical_write_authorized"] is False
        assert row["engineering_authority_effect"] == "NONE"

        crop = ASSET_ROOT / "regions" / row["crop"]["filename"]
        result_path = ASSET_ROOT / "regions" / row["result_filename"]
        assert crop.is_file(), crop
        assert result_path.is_file(), result_path
        assert _sha256(crop) == row["crop"]["sha256"]
        assert _sha256(result_path) == row["result_sha256"]
        assert row["crop"]["width_px"] > 0 and row["crop"]["height_px"] > 0
        assert 0.0 <= row["crop"]["ink_ratio"] <= 1.0

        if row["classification"] == "REGION_MAPPING_ERROR":
            assert row["mapping_error_reason"]
        else:
            assert row["mapping_error_reason"] is None
            assert row["page_registry"]["present"] is True
            assert row["page_registry"]["dimension_match"] is True
            assert row["region"]["normalized_valid"] is True
            assert row["region"]["clip_inside_page"] is True
            assert row["region"]["containment_method"] == "SOURCE_PAGE_EDGE_TOLERANCE"
            assert row["region"]["containment_tolerance_pt"] == EXPECTED_EDGE_TOLERANCE_PT

    counts = manifest["classification_counts"]
    assert set(counts) == ALLOWED
    assert sum(int(value) for value in counts.values()) == 4

    print("CEW_PWB005_R1_CONTENT_DIAGNOSTIC = PASS")
    print("SOURCE_COVERAGE = 4/4")
    print("GOVERNED_REGION_COVERAGE = 4/4")
    print("CONTAINMENT_METHOD = SOURCE_PAGE_EDGE_TOLERANCE")
    print(f"REGION_EDGE_TOLERANCE_PT = {EXPECTED_EDGE_TOLERANCE_PT}")
    print("CLASSIFICATION_COUNTS = " + json.dumps(counts, sort_keys=True))
    for row in sorted(results, key=lambda item: item["evidence_region_id"]):
        print(
            "REGION_CLASSIFICATION",
            row["evidence_region_id"],
            row["classification"],
            "drawings=" + str(row["drawing"]["path_count"]),
            "text_spans=" + str(row["text"]["span_count"]),
            "images=" + str(row["embedded_images"]["embedded_image_count"]),
            "ink_ratio=" + str(row["crop"]["ink_ratio"]),
        )
    print("R1A_REMEDIATION = PASS")
    print("DIAGNOSTIC_AUTHORITY = NONE")
    print("OCR_USED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("HVA_EXECUTION_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
