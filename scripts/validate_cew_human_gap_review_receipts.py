#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R2BR_ROOT = ROOT / ".cew_raster_bridge_review"
R2BR_MANIFEST = R2BR_ROOT / "manifest.json"
R2RV_ROOT = ROOT / "artifacts" / "cew_r2rv_review"
R2RV_MANIFEST = R2RV_ROOT / "manifest.json"
R2HR_ROOT = ROOT / "artifacts" / "cew_r2hr_review"
R2HR_MANIFEST = R2HR_ROOT / "manifest.json"
SCHEMA_PATH = ROOT / "automation" / "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_RECEIPT_SCHEMA_v1.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
GAP_ID = re.compile(r"^RGH-[0-9a-f]{20}$")
ALLOWED_DECISIONS = {
    "SUPPORTED_CONTINUITY_HYPOTHESIS",
    "REJECTED_CONTINUITY_HYPOTHESIS",
    "UNRESOLVED_FROM_CURRENT_VIEW",
}


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2HR_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _head_sha() -> str:
    value = os.getenv("CEW_REVIEW_HEAD_SHA", "").strip().lower()
    if not SHA40.fullmatch(value):
        raise AssertionError("R2HR_CANDIDATE_HEAD_SHA_REQUIRED")
    return value


def _metric_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "projected_gap_norm": row["projected_gap_norm"],
        "nearest_endpoint_distance_norm": row["nearest_endpoint_distance_norm"],
        "r2s_cross_scale_min_support_fraction": row["r2s_cross_scale_min_support_fraction"],
        "r2s_cross_scale_min_longest_run_fraction": row["r2s_cross_scale_min_longest_run_fraction"],
        "cross_scale_min_support_contrast": row["cross_scale_min_support_contrast"],
        "cross_scale_min_run_contrast": row["cross_scale_min_run_contrast"],
    }


def _validate_schema_contract(schema: dict[str, Any]) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_RECEIPT_SCHEMA_v1"
    props = schema["properties"]
    assert props["receipt_type"]["const"] == "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_v1"
    assert props["reviewer_attestation"]["const"] is True
    decision_props = props["decisions"]["items"]["properties"]
    assert set(decision_props["decision"]["enum"]) == ALLOWED_DECISIONS
    assert decision_props["rationale"]["minLength"] == 1
    assert decision_props["decision_authority"]["const"] == "HUMAN_REVIEW_EVIDENCE_ONLY"
    assert decision_props["decision_is_geometry_acceptance"]["const"] is False
    assert props["receipt_authority"]["const"] == "HUMAN_REVIEW_EVIDENCE_ONLY"
    for key in (
        "supported_continuity_hypothesis_is_geometry",
        "human_review_is_bridge_acceptance",
        "bridge_candidate_authorized",
        "geometry_materialization_authorized",
        "r2c_scene_adapter_authorized",
        "technical_identity_authorized",
        "structural_identity_authorized",
        "canonical_write_authorized",
    ):
        assert props[key]["const"] is False, f"R2HR_SCHEMA_AUTHORITY_DRIFT:{key}"
    assert props["engineering_authority_effect"]["const"] == "NONE"


def _validate_synthetic_receipt(template: dict[str, Any]) -> None:
    decisions = []
    for gap in template["gaps"]:
        decisions.append({
            "gap_hypothesis_id": gap["gap_hypothesis_id"],
            "review_tier": gap["review_tier"],
            "decision": "UNRESOLVED_FROM_CURRENT_VIEW",
            "rationale": "Synthetic validator rationale; no human decision is created.",
            "candidate_ids": gap["candidate_ids"],
            "bridge_endpoints_normalized": gap["bridge_endpoints_normalized"],
            "metric_snapshot": gap["metric_snapshot"],
            "decision_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
            "decision_is_geometry_acceptance": False,
        })
    receipt = {
        "schema_version": "1.0",
        "receipt_type": "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_v1",
        "candidate_head_sha": template["candidate_head_sha"],
        "build_revision": template["build_revision"],
        "evidence_region_id": template["evidence_region_id"],
        "source_code": template["source_code"],
        "source_version_id": template["source_version_id"],
        "source_sha256": template["source_sha256"],
        "page_id": template["page_id"],
        "transform_id": template["transform_id"],
        "reviewer_label": "SYNTHETIC_VALIDATOR_ONLY",
        "reviewer_attestation": True,
        "reviewed_at": "2026-08-29T00:00:00Z",
        "decisions": decisions,
        "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
        "supported_continuity_hypothesis_is_geometry": False,
        "human_review_is_bridge_acceptance": False,
        "bridge_candidate_authorized": False,
        "geometry_materialization_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }
    assert SHA40.fullmatch(receipt["candidate_head_sha"])
    assert SHA40.fullmatch(receipt["build_revision"])
    assert SHA64.fullmatch(receipt["source_sha256"])
    assert receipt["reviewer_attestation"] is True
    assert len(receipt["decisions"]) == len(template["gaps"])
    for row in receipt["decisions"]:
        assert GAP_ID.fullmatch(row["gap_hypothesis_id"])
        assert row["decision"] in ALLOWED_DECISIONS
        assert row["rationale"].strip()
        assert row["decision_authority"] == "HUMAN_REVIEW_EVIDENCE_ONLY"
        assert row["decision_is_geometry_acceptance"] is False
    for key in (
        "supported_continuity_hypothesis_is_geometry",
        "human_review_is_bridge_acceptance",
        "bridge_candidate_authorized",
        "geometry_materialization_authorized",
        "r2c_scene_adapter_authorized",
        "technical_identity_authorized",
        "structural_identity_authorized",
        "canonical_write_authorized",
    ):
        assert receipt[key] is False
    assert receipt["engineering_authority_effect"] == "NONE"


def validate() -> None:
    expected_head = _head_sha()
    schema = _load(SCHEMA_PATH)
    r2br = _load(R2BR_MANIFEST)
    r2rv = _load(R2RV_MANIFEST)
    r2hr = _load(R2HR_MANIFEST)
    _validate_schema_contract(schema)

    assert r2hr["package_contract"] == "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_RECEIPT_PACKAGE_v1"
    assert r2hr["receipt_schema_id"] == schema["$id"]
    assert r2hr["candidate_head_sha"] == expected_head
    assert SHA40.fullmatch(r2hr["build_revision"])
    assert r2hr["build_revision"] == r2rv["build_revision"] == r2br["build_revision"]
    assert r2hr["region_coverage"] == "4/4"
    assert r2hr["gap_hypothesis_total"] == 10
    assert r2hr["high_contrast_review_total"] == 5
    assert r2hr["standard_review_total"] == 5
    assert r2hr["control_incomplete_review_total"] == 0
    assert r2hr["artifact_role"] == "REVISION_BOUND_HUMAN_GAP_REVIEW_PACKAGE"
    assert r2hr["runtime_dependency"] is False
    assert r2hr["receipt_authority"] == "HUMAN_REVIEW_EVIDENCE_ONLY"
    assert r2hr["decision_state"] == "HUMAN_GAP_REVIEW_PACKAGE_READY_RECEIPT_NOT_YET_PRODUCED"
    assert r2hr["engineering_authority_effect"] == "NONE"
    for key in (
        "supported_continuity_hypothesis_is_geometry",
        "human_review_is_bridge_acceptance",
        "bridge_candidate_authorized",
        "geometry_materialization_authorized",
        "r2c_scene_adapter_authorized",
        "technical_identity_authorized",
        "structural_identity_authorized",
        "canonical_write_authorized",
    ):
        assert r2hr[key] is False, f"R2HR_PACKAGE_AUTHORITY_DRIFT:{key}"

    index_path = R2HR_ROOT / r2hr["index_filename"]
    assert index_path.is_file() and _sha256(index_path) == r2hr["index_sha256"]
    index = index_path.read_text(encoding="utf-8")
    for marker in (
        "Review evidence only",
        "receipt_authority=HUMAN_REVIEW_EVIDENCE_ONLY",
        "human_review_is_bridge_acceptance=false",
        "r2c_scene_adapter_authorized=false",
        "canonical_write_authorized=false",
        expected_head,
        r2hr["build_revision"],
    ):
        assert marker in index, f"R2HR_INDEX_MARKER_MISSING:{marker}"

    br_entries = {row["evidence_region_id"]: row for row in r2br["regions"]}
    hr_entries = {row["evidence_region_id"]: row for row in r2hr["regions"]}
    assert set(br_entries) == EXPECTED_REGIONS
    assert set(hr_entries) == EXPECTED_REGIONS

    seen: set[str] = set()
    total = high = standard = incomplete = 0
    for region_id in sorted(EXPECTED_REGIONS):
        br = _load(R2BR_ROOT / br_entries[region_id]["result_filename"])
        hr_entry = hr_entries[region_id]
        template_path = R2HR_ROOT / hr_entry["receipt_template_filename"]
        html_path = R2HR_ROOT / hr_entry["html_filename"]
        crop_path = R2HR_ROOT / hr_entry["source_crop_filename"]
        assert template_path.is_file() and html_path.is_file() and crop_path.is_file()
        assert _sha256(template_path) == hr_entry["receipt_template_sha256"]
        assert _sha256(html_path) == hr_entry["html_sha256"]
        assert _sha256(crop_path) == hr_entry["source_crop_sha256"]

        template = _load(template_path)
        assert template["template_type"] == "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_TEMPLATE_v1"
        assert template["receipt_schema_id"] == schema["$id"]
        assert template["candidate_head_sha"] == expected_head
        assert template["build_revision"] == r2hr["build_revision"]
        assert template["evidence_region_id"] == region_id
        assert template["template_state"] == "UNREVIEWED"
        assert set(template["allowed_decisions"]) == ALLOWED_DECISIONS
        for key in ("source_code", "source_version_id", "source_sha256", "page_id", "transform_id"):
            assert template[key] == br[key], f"R2HR_TEMPLATE_PROVENANCE_DRIFT:{region_id}:{key}"
        assert SHA64.fullmatch(template["source_sha256"])
        assert template["receipt_authority"] == "HUMAN_REVIEW_EVIDENCE_ONLY"
        assert template["engineering_authority_effect"] == "NONE"
        for key in (
            "supported_continuity_hypothesis_is_geometry",
            "human_review_is_bridge_acceptance",
            "bridge_candidate_authorized",
            "geometry_materialization_authorized",
            "r2c_scene_adapter_authorized",
            "technical_identity_authorized",
            "structural_identity_authorized",
            "canonical_write_authorized",
        ):
            assert template[key] is False

        br_rows = {row["gap_hypothesis_id"]: row for row in br["review_rows"]}
        template_rows = {row["gap_hypothesis_id"]: row for row in template["gaps"]}
        assert set(br_rows) == set(template_rows), f"R2HR_GAP_RETENTION_FAILURE:{region_id}"
        for gap_id in sorted(br_rows):
            assert gap_id not in seen, f"R2HR_DUPLICATE_GAP:{gap_id}"
            seen.add(gap_id)
            source = br_rows[gap_id]
            row = template_rows[gap_id]
            assert row["review_tier"] == source["review_tier"]
            assert row["candidate_ids"] == source["candidate_ids"]
            assert row["bridge_endpoints_normalized"] == source["bridge_endpoints_normalized"]
            assert row["metric_snapshot"] == _metric_snapshot(source), f"R2HR_METRIC_DRIFT:{gap_id}"
            total += 1
            if row["review_tier"] == "HIGH_CONTRAST_REVIEW":
                high += 1
            elif row["review_tier"] == "STANDARD_REVIEW":
                standard += 1
            else:
                incomplete += 1

        html_text = html_path.read_text(encoding="utf-8")
        required_markers = (
            "EVIDENZA DI REVISIONE UMANA SOLTANTO",
            "SUPPORTED_CONTINUITY_HYPOTHESIS",
            "REJECTED_CONTINUITY_HYPOTHESIS",
            "UNRESOLVED_FROM_CURRENT_VIEW",
            "reviewerLabel",
            "attestation",
            "Esporta review JSON",
            "HUMAN_REVIEW_EVIDENCE_ONLY",
            "decision_is_geometry_acceptance:false",
            "human_review_is_bridge_acceptance:false",
            "bridge_candidate_authorized:false",
            "r2c_scene_adapter_authorized:false",
            "canonical_write_authorized:false",
            "new Date().toISOString()",
            expected_head,
            r2hr["build_revision"],
        )
        for marker in required_markers:
            assert marker in html_text, f"R2HR_HTML_MARKER_MISSING:{region_id}:{marker}"
        assert html_text.count('data-gap-id="') == len(br_rows), f"R2HR_OVERLAY_COUNT_MISMATCH:{region_id}"
        assert html_text.count('class="decision-card" data-gap-id="') == len(br_rows), f"R2HR_DECISION_COUNT_MISMATCH:{region_id}"
        _validate_synthetic_receipt(template)

    assert len(seen) == total == 10
    assert (high, standard, incomplete) == (5, 5, 0)

    print("CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_PACKAGE = PASS")
    print("CANDIDATE_HEAD_SHA = " + expected_head)
    print("BUILD_REVISION = " + r2hr["build_revision"])
    print("HEAD_AND_BUILD_IDENTITY_DISTINCT_FIELDS = true")
    print("REGION_COVERAGE = 4/4")
    print("GAP_RETENTION = 10/10")
    print("HIGH_CONTRAST_REVIEW_TOTAL = 5")
    print("STANDARD_REVIEW_TOTAL = 5")
    print("RECEIPT_SCHEMA = PASS")
    print("LOCAL_EXPORT_ONLY = true")
    print("REVIEWER_ATTESTATION_REQUIRED = true")
    print("RATIONALE_REQUIRED_PER_GAP = true")
    print("RECEIPT_AUTHORITY = HUMAN_REVIEW_EVIDENCE_ONLY")
    print("SUPPORTED_CONTINUITY_HYPOTHESIS_IS_GEOMETRY = false")
    print("HUMAN_REVIEW_IS_BRIDGE_ACCEPTANCE = false")
    print("R2_BRIDGE_CANDIDATE_AUTHORIZED = false")
    print("PWB005_R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("HUMAN_GAP_REVIEW_RECEIPT_PRODUCED = false")


if __name__ == "__main__":
    validate()
