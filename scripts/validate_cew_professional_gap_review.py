#!/usr/bin/env python3
from __future__ import annotations

import copy
import os
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "scripts/cew_professional_gap_review.py"
API = ROOT / "scripts/cew_professional_workbench_api.py"
RENDER_BUILD = ROOT / "scripts/render_build_candidate.sh"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    py_compile.compile(str(SERVICE), doraise=True)
    py_compile.compile(str(API), doraise=True)

    os.environ["CEW_RUNTIME_REVISION"] = "a" * 40
    import cew_professional_gap_review as gap

    base_gap = {
        "gap_hypothesis_id": "RGH-" + "1" * 20,
        "review_tier": "HIGH_CONTRAST_REVIEW",
        "candidate_ids": ["RGM-a", "RGM-b"],
        "bridge_endpoints_normalized": {"a": [0.1, 0.2], "b": [0.3, 0.4]},
        "metric_snapshot": {
            "projected_gap_norm": 0.2,
            "nearest_endpoint_distance_norm": 0.2,
            "r2s_cross_scale_min_support_fraction": 1.0,
            "r2s_cross_scale_min_longest_run_fraction": 0.8,
            "cross_scale_min_support_contrast": 0.7,
            "cross_scale_min_run_contrast": 0.6,
        },
    }
    template = {
        "candidate_head_sha": "a" * 40,
        "build_revision": "b" * 40,
        "evidence_region_id": "CEW-N12-REG-G01-R06",
        "source_code": "TAV-05A",
        "source_version_id": "CEW-N12-SRC-TAV05A-V17DEC414",
        "source_sha256": "c" * 64,
        "page_id": "CEW-N12-PAGE-TAV05A-P001",
        "transform_id": "CEW-N12-XFORM-TAV05A-P001",
        "gaps": [base_gap],
    }
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
        "reviewer_label": "CI reviewer fixture",
        "reviewer_attestation": True,
        "reviewed_at": "2026-08-30T03:30:00+00:00",
        "decisions": [
            {
                **base_gap,
                "decision": "SUPPORTED_CONTINUITY_HYPOTHESIS",
                "rationale": "Synthetic policy fixture; no human or geometry authority.",
                "decision_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
                "decision_is_geometry_acceptance": False,
            }
        ],
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

    gap.validate_receipt(receipt, template)
    envelope = gap.audit_envelope("ERW-N12-001", receipt)
    require(envelope["authority"] == "RUNTIME_AUDIT_ONLY", "runtime audit authority drift")
    require(envelope["canonical_write"] is False, "runtime audit must not write canonical data")
    require(envelope["engineering_authority_effect"] == "NONE", "engineering authority drift")
    require(envelope["next_gate"] == "R2HR_GOVERNED_REVIEW_INGEST_REQUIRED", "separate ingest gate missing")
    require(envelope["decision_id"].startswith("R2HR-CEW-N12-REG-G01-R06-"), "safe deterministic receipt id missing")

    tampered = copy.deepcopy(receipt)
    tampered["decisions"][0]["candidate_ids"] = ["RGM-a", "RGM-z"]
    try:
        gap.validate_receipt(tampered, template)
        raise AssertionError("tampered candidate evidence accepted")
    except ValueError as exc:
        require("EVIDENCE_TAMPERED" in str(exc), "wrong tamper rejection reason")

    promoted = copy.deepcopy(receipt)
    promoted["canonical_write_authorized"] = True
    try:
        gap.validate_receipt(promoted, template)
        raise AssertionError("canonical-write R2HR receipt accepted")
    except ValueError as exc:
        require("AUTHORITY_DRIFT" in str(exc), "wrong authority rejection reason")

    geometry_accept = copy.deepcopy(receipt)
    geometry_accept["decisions"][0]["decision_is_geometry_acceptance"] = True
    try:
        gap.validate_receipt(geometry_accept, template)
        raise AssertionError("geometry acceptance smuggled through human review")
    except ValueError as exc:
        require("GEOMETRY_ACCEPTANCE_FORBIDDEN" in str(exc), "wrong geometry rejection reason")

    service = SERVICE.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    render_build = RENDER_BUILD.read_text(encoding="utf-8")
    for marker in (
        "HUMAN_REVIEW_EVIDENCE_ONLY",
        "R2HR_GOVERNED_REVIEW_INGEST_REQUIRED",
        "geometry_materialization_authorized",
        "canonical_write_authorized",
        "Registra revisione in CEW",
    ):
        require(marker in service, f"gap-review service marker missing: {marker}")
    require("new Blob" not in service and "download=" not in service, "runtime review must not require JSON download/export")
    for marker in (
        '@router.get("/workbench/gap-review"',
        '@router.post("/api/workbench/gap-review/receipt")',
        'audit_store.persist_runtime_receipt',
        'R2HR_RECEIPT_PERSISTED_AUDIT_ONLY',
        'Verifica continuità raster',
    ):
        require(marker in api, f"gap-review API integration marker missing: {marker}")
    require('CEW_REVIEW_HEAD_SHA="$RENDER_GIT_COMMIT" python scripts/build_cew_human_gap_review_receipts.py' in render_build, "Render exact-revision R2HR build missing")
    require("CEW_RENDER_R2HR_REGION_COVERAGE = 4/4" in render_build, "Render R2HR coverage guard missing")
    require("CEW_RENDER_R2HR_GAP_TOTAL = 10" in render_build, "Render R2HR gap guard missing")

    print("CEW_PROFESSIONAL_GAP_REVIEW_RUNTIME = PASS")
    print("R2HR_REVIEW_IN_SYSTEM = PASS")
    print("R2HR_JSON_DOWNLOAD_REQUIRED = false")
    print("R2HR_RECEIPT_PERSISTENCE = APPEND_ONLY_RUNTIME_AUDIT")
    print("R2HR_RECEIPT_IS_GEOMETRY_ACCEPTANCE = false")
    print("R2HR_GOVERNED_REVIEW_INGEST = SEPARATE_REQUIRED_GATE")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("ENGINEERING_AUTHORITY_EFFECT = NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
