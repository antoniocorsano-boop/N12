#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import shutil

import cew_professional_gap_review as gap_review
import cew_professional_workbench_api as workbench_api
import cew_r2hr_governed_ingest as r2gi
import cew_runtime_audit_store as audit_store

STORE = Path("/tmp/cew-r2gi-runtime-validation")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def synthetic_receipt(region_id: str, *, rationale_suffix: str = "base") -> dict:
    template = gap_review.template(region_id)
    decisions = []
    for gap in template["gaps"]:
        decisions.append(
            {
                "gap_hypothesis_id": gap["gap_hypothesis_id"],
                "review_tier": gap["review_tier"],
                "decision": "SUPPORTED_CONTINUITY_HYPOTHESIS",
                "rationale": f"Synthetic runtime-ingest validation only ({rationale_suffix}); no geometry acceptance.",
                "candidate_ids": deepcopy(gap["candidate_ids"]),
                "bridge_endpoints_normalized": deepcopy(gap["bridge_endpoints_normalized"]),
                "metric_snapshot": deepcopy(gap["metric_snapshot"]),
                "decision_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
                "decision_is_geometry_acceptance": False,
            }
        )
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
        "reviewer_label": "CI runtime ingest validator",
        "reviewer_attestation": True,
        "reviewed_at": "2026-08-30T00:00:00+00:00",
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
    return gap_review.validate_receipt(receipt, template)


def envelope(region_id: str, *, rationale_suffix: str = "base") -> dict:
    return gap_review.audit_envelope(
        f"R2GI-RUNTIME-{region_id}",
        synthetic_receipt(region_id, rationale_suffix=rationale_suffix),
    )


def main() -> int:
    for key in (
        "CEW_AUDIT_NEON_DATABASE_URL",
        "CEW_AUDIT_HTTPS_URL",
        "CEW_AUDIT_SHARED_SECRET",
        "CEW_AUDIT_SUPABASE_URL",
        "CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY",
        "VERCEL",
        "RENDER",
    ):
        os.environ.pop(key, None)

    shutil.rmtree(STORE, ignore_errors=True)
    STORE.mkdir(parents=True)

    package = gap_review.status()
    require(package.get("state") == "READY", f"R2HR package not ready: {package}")
    require(package.get("region_coverage") == "4/4", "R2HR package coverage drift")
    require(package.get("gap_hypothesis_total") == 10, "R2HR gap count drift")

    empty = audit_store.load_runtime_receipts(r2gi.ALLOWED_AUDIT_RECEIPT_TYPE, STORE)
    require(empty["audit_backend"] == "FILESYSTEM_APPEND_ONLY", "test audit backend must be filesystem")
    require(empty["receipt_count"] == 0, "empty runtime audit store must read zero receipts")
    require(empty["canonical_write"] is False, "runtime audit read must never authorize canonical write")

    previous_store = workbench_api.R2HR_RUNTIME_STORE
    workbench_api.R2HR_RUNTIME_STORE = STORE
    try:
        regions = sorted(r2gi.EXPECTED_REGIONS)
        for index, region_id in enumerate(regions, 1):
            persisted = audit_store.persist_runtime_receipt(envelope(region_id), STORE)
            require(persisted["audit_backend"] == "FILESYSTEM_APPEND_ONLY", "runtime receipt persistence backend drift")
            loaded = audit_store.load_runtime_receipts(r2gi.ALLOWED_AUDIT_RECEIPT_TYPE, STORE)
            require(loaded["receipt_count"] == index, "runtime audit read-back count mismatch")
            report = workbench_api._runtime_r2gi_report()
            require(report["candidate_receipt_count"] == index, "candidate receipt count mismatch")
            require(report["geometry_materialization_authorized"] is False, "runtime ingest must not materialize geometry")
            require(report["canonical_write_authorized"] is False, "runtime ingest must not authorize canonical writes")
            if index < len(regions):
                require(report["state"] == "BLOCKED_HUMAN_RECEIPT_REQUIRED", "partial receipt set must remain blocked")
            else:
                require(report["state"] == "READY_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW", "complete receipt set must advance only to R2GM")
                require(report["next_gate"] == "R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE_REQUIRED", "complete receipt set must route to R2GM")
                require(report["region_coverage"] == "4/4", "runtime ingest coverage mismatch")

        stale = deepcopy(envelope(regions[0], rationale_suffix="stale"))
        stale["decision_id"] = "R2HR-STALE-REVISION-SYNTHETIC"
        stale["r2hr_receipt"]["candidate_head_sha"] = "0" * 40
        audit_store.persist_runtime_receipt(stale, STORE)
        report = workbench_api._runtime_r2gi_report()
        require(report["audit_receipt_total"] == 5, "stale audit receipt must remain visible to audit read-back")
        require(report["candidate_receipt_count"] == 4, "stale revision receipt must not enter current governed ingest")
        require(report["state"] == "READY_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW", "stale revision must not perturb current exact-revision state")

        duplicate = envelope(regions[0], rationale_suffix="second-valid-review")
        audit_store.persist_runtime_receipt(duplicate, STORE)
        try:
            workbench_api._runtime_r2gi_report()
        except ValueError as exc:
            require("R2GI_DUPLICATE_REGION_RECEIPT" in str(exc), "same-revision duplicate must fail closed as conflict")
        else:
            raise AssertionError("same-revision duplicate receipt must not be silently superseded")
    finally:
        workbench_api.R2HR_RUNTIME_STORE = previous_store
        shutil.rmtree(STORE, ignore_errors=True)

    os.environ["RENDER"] = "1"
    try:
        audit_store.load_runtime_receipts(r2gi.ALLOWED_AUDIT_RECEIPT_TYPE, STORE)
    except ValueError as exc:
        require("production audit backend is not configured" in str(exc), "production read-back must fail closed without persistent backend")
    else:
        raise AssertionError("unconfigured production audit read-back must fail closed")
    finally:
        os.environ.pop("RENDER", None)

    print("CEW_R2GI_RUNTIME_AUDIT_READ_BACK = PASS")
    print("CEW_R2GI_RUNTIME_EXACT_REVISION_FILTER = PASS")
    print("CEW_R2GI_RUNTIME_PARTIAL_RECEIPTS_FAIL_CLOSED = PASS")
    print("CEW_R2GI_RUNTIME_COMPLETE_RECEIPTS_ROUTE_TO_R2GM = PASS")
    print("CEW_R2GI_RUNTIME_DUPLICATE_REGION_CONFLICT = PASS")
    print("CEW_R2GI_RUNTIME_CANONICAL_WRITE_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
