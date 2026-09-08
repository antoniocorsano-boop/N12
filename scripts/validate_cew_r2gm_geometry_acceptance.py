#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import shutil

import cew_professional_gap_review as gap_review
import cew_professional_workbench_api as workbench_api
import cew_r2gm_geometry_acceptance as r2gm
import cew_r2hr_governed_ingest as r2gi
import cew_runtime_audit_store as audit_store

R2HR_STORE = Path("/tmp/cew-r2gm-validator-r2hr")
R2GM_STORE = Path("/tmp/cew-r2gm-validator-r2gm")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_error(fn, marker: str) -> None:
    try:
        fn()
    except ValueError as exc:
        require(marker in str(exc), f"expected {marker}, got {exc}")
        return
    raise AssertionError(f"expected ValueError containing {marker}")


def r2hr_receipt(region_id: str) -> dict:
    template = gap_review.template(region_id)
    decisions = []
    for gap in template["gaps"]:
        decisions.append(
            {
                "gap_hypothesis_id": gap["gap_hypothesis_id"],
                "review_tier": gap["review_tier"],
                "decision": "SUPPORTED_CONTINUITY_HYPOTHESIS",
                "rationale": "Synthetic R2GM gate validation only; this is not a real project review.",
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
        "reviewer_label": "CI synthetic R2HR prerequisite",
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


def ready_r2gi_report() -> tuple[dict, list[dict]]:
    envelopes = []
    for region_id in sorted(r2gi.EXPECTED_REGIONS):
        receipt = r2hr_receipt(region_id)
        envelopes.append(gap_review.audit_envelope(f"R2GM-PREREQ-{region_id}", receipt))
    report = r2gi.ingest_envelopes(envelopes)
    require(report["schema_version"] == "1.2", "R2GI dual-revision schema required")
    require(report["state"] == "READY_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW", "synthetic R2GI prerequisite not ready")
    require(report["region_coverage"] == "4/4", "synthetic R2GI coverage mismatch")
    require(isinstance(report["candidate_head_sha"], str) and report["candidate_head_sha"], "R2GI candidate head missing")
    require(isinstance(report["build_revision"], str) and report["build_revision"], "R2GI build revision missing")
    require(report["geometry_materialization_authorized"] is False, "R2GI prerequisite must remain non-geometric")
    return report, envelopes


def r2gm_receipt(proposal: dict, decision: str = "ACCEPT_EXACT_REGION_DOCUMENT_GEOMETRY") -> dict:
    return {
        "schema_version": "1.1",
        "receipt_type": r2gm.RECEIPT_TYPE,
        "candidate_head_sha": proposal["candidate_head_sha"],
        "build_revision": proposal["build_revision"],
        "r2gi_report_sha256": proposal["r2gi_report_sha256"],
        "proposal_id": proposal["proposal_id"],
        "proposal_sha256": proposal["proposal_sha256"],
        "evidence_region_id": proposal["evidence_region_id"],
        "source_code": proposal["source_code"],
        "source_version_id": proposal["source_version_id"],
        "source_sha256": proposal["source_sha256"],
        "page_id": proposal["page_id"],
        "transform_id": proposal["transform_id"],
        "proposal_primitive_count": proposal["primitive_count"],
        "reviewer_label": "CI synthetic R2GM validator",
        "reviewer_attestation": True,
        "reviewed_at": "2026-08-30T00:05:00+00:00",
        "decision": decision,
        "rationale": "Synthetic R2GM governance validation only; no real project geometry decision is asserted.",
        "receipt_authority": "HUMAN_DOCUMENT_GEOMETRY_ACCEPTANCE_ONLY",
        "document_geometry_materialization_authorized": decision == "ACCEPT_EXACT_REGION_DOCUMENT_GEOMETRY",
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def main() -> int:
    report, r2hr_envelopes = ready_r2gi_report()

    blocked = r2gm.aggregate(r2gi.ingest_envelopes([]), [])
    require(blocked["state"] == "BLOCKED_R2GI_NOT_READY", "R2GM must block when R2GI is incomplete")
    require(blocked["r2c_scene_adapter_authorized"] is False, "blocked R2GM cannot authorize R2C")

    proposals = {region_id: r2gm.build_region_proposal(report, region_id) for region_id in sorted(r2gi.EXPECTED_REGIONS)}
    for region_id, proposal in proposals.items():
        require(proposal["candidate_head_sha"] == report["candidate_head_sha"], f"candidate head not preserved: {region_id}")
        require(proposal["build_revision"] == report["build_revision"], f"build revision not preserved: {region_id}")
        require(proposal["proposal_is_document_geometry"] is False, f"proposal must not pre-authorize document geometry: {region_id}")
        require(proposal["proposal_requires_explicit_human_acceptance"] is True, "proposal must require explicit human acceptance")
        require(proposal["primitive_count"] >= proposal["base_primitive_count"] > 0, "R2GM proposal must contain R2M base linework")
        if region_id != "CEW-N12-REG-T6A-G03":
            require(proposal["human_supported_bridge_count"] > 0, "synthetic supported gaps should contribute reviewed bridges")
        require(proposal["technical_identity_authorized"] is False, "proposal must not create technical identity")
        require(proposal["structural_identity_authorized"] is False, "proposal must not create structural identity")
        require(proposal["canonical_write_authorized"] is False, "proposal must not authorize canonical writes")

    report_row_build_mismatch = deepcopy(report)
    report_row_build_mismatch["build_revision"] = "0" * 40
    expect_error(
        lambda: r2gm.build_region_proposal(report_row_build_mismatch, sorted(proposals)[0]),
        "R2GM_R2GI_REGION_BUILD_MISMATCH",
    )

    r2m_build_mismatch = deepcopy(report)
    r2m_build_mismatch["build_revision"] = "0" * 40
    for row in r2m_build_mismatch["regions"]:
        if row.get("receipt_ingested") is True:
            row["build_revision"] = "0" * 40
    for finding in r2m_build_mismatch["review_findings"]:
        finding["build_revision"] = "0" * 40
    expect_error(
        lambda: r2gm.build_region_proposal(r2m_build_mismatch, sorted(proposals)[0]),
        "R2GM_R2M_BUILD_REVISION_MISMATCH",
    )

    candidate_mismatch = deepcopy(report)
    candidate_mismatch["candidate_head_sha"] = "1" * 40
    expect_error(
        lambda: r2gm.build_region_proposal(candidate_mismatch, sorted(proposals)[0]),
        "R2GM_R2GI_REGION_CANDIDATE_MISMATCH",
    )

    sample = proposals[sorted(proposals)[0]]
    valid_sample = r2gm_receipt(sample)
    r2gm.validate_receipt(valid_sample, sample)
    tampered_receipt = deepcopy(valid_sample)
    tampered_receipt["proposal_sha256"] = "0" * 64
    expect_error(lambda: r2gm.validate_receipt(tampered_receipt, sample), "R2GM_RECEIPT_PROVENANCE_MISMATCH:proposal_sha256")
    build_tampered_receipt = deepcopy(valid_sample)
    build_tampered_receipt["build_revision"] = "0" * 40
    expect_error(lambda: r2gm.validate_receipt(build_tampered_receipt, sample), "R2GM_RECEIPT_PROVENANCE_MISMATCH:build_revision")

    accept_envelopes = []
    for region_id in sorted(proposals):
        proposal = proposals[region_id]
        receipt = r2gm_receipt(proposal)
        accept_envelopes.append(r2gm.audit_envelope(f"R2GM-ACCEPT-{region_id}", receipt, proposal))

    one = r2gm.aggregate(report, accept_envelopes[:1])
    require(one["state"] == "BLOCKED_GEOMETRY_ACCEPTANCE_REQUIRED", "partial R2GM region coverage must remain blocked")
    require(one["region_coverage"] == "1/4", "partial R2GM coverage mismatch")
    require(one["document_geometry_materialized_region_count"] == 1, "accepted region should materialize only its exact document geometry")
    require(one["r2c_scene_adapter_authorized"] is False, "partial R2GM cannot authorize R2C")

    complete = r2gm.aggregate(report, accept_envelopes)
    require(complete["schema_version"] == "1.1", "R2GM report dual-revision schema required")
    require(complete["candidate_head_sha"] == report["candidate_head_sha"], "R2GM aggregate candidate provenance drift")
    require(complete["build_revision"] == report["build_revision"], "R2GM aggregate build provenance drift")
    require(complete["state"] == "READY_FOR_R2C_DOCUMENT_GEOMETRY_SCENE_ADAPTER", "4/4 explicit acceptance should route only to R2C")
    require(complete["next_gate"] == "R2C_DOCUMENT_GEOMETRY_SCENE_ADAPTER_REQUIRED", "R2GM next gate mismatch")
    require(complete["region_coverage"] == "4/4", "R2GM complete coverage mismatch")
    require(complete["document_geometry_materialized_region_count"] == 4, "all accepted regions must yield four document-geometry bundles")
    require(complete["r2c_scene_adapter_authorized"] is True, "R2C may be authorized only after 4/4 exact geometry acceptance")
    require(complete["technical_identity_authorized"] is False, "R2GM must not create technical identity")
    require(complete["structural_identity_authorized"] is False, "R2GM must not create structural identity")
    require(complete["canonical_write_authorized"] is False, "R2GM must not authorize canonical writes")
    require(complete["engineering_authority_effect"] == "NONE", "R2GM must not create engineering authority")
    for geometry in complete["accepted_document_geometry"]:
        require(geometry["candidate_head_sha"] == report["candidate_head_sha"], "accepted geometry candidate provenance drift")
        require(geometry["build_revision"] == report["build_revision"], "accepted geometry build provenance drift")
        require(geometry["is_document_geometry"] is True, "accepted R2GM output must be document geometry")
        require(geometry["authority"] == "HUMAN_ACCEPTED_DOCUMENT_GEOMETRY", "accepted geometry authority mismatch")
        require(geometry["technical_identity_authorized"] is False, "accepted document geometry is not technical identity")
        require(geometry["structural_identity_authorized"] is False, "accepted document geometry is not structural identity")

    rejected = deepcopy(accept_envelopes)
    region_id = sorted(proposals)[0]
    rejected[0] = r2gm.audit_envelope(
        f"R2GM-REJECT-{region_id}",
        r2gm_receipt(proposals[region_id], "REJECT_REGION_DOCUMENT_GEOMETRY"),
        proposals[region_id],
    )
    rejected_report = r2gm.aggregate(report, rejected)
    require(rejected_report["state"] == "BLOCKED_GEOMETRY_REJECTED", "one rejected region must block R2GM")
    require(rejected_report["r2c_scene_adapter_authorized"] is False, "rejected region must block R2C")

    deferred = deepcopy(accept_envelopes)
    deferred[0] = r2gm.audit_envelope(
        f"R2GM-DEFER-{region_id}",
        r2gm_receipt(proposals[region_id], "DEFER_NEEDS_ADDITIONAL_SOURCE"),
        proposals[region_id],
    )
    deferred_report = r2gm.aggregate(report, deferred)
    require(deferred_report["state"] == "BLOCKED_ADDITIONAL_SOURCE_REQUIRED", "deferred region must block R2GM")
    require(deferred_report["r2c_scene_adapter_authorized"] is False, "deferred region must block R2C")

    expect_error(lambda: r2gm.aggregate(report, accept_envelopes + [deepcopy(accept_envelopes[0])]), "R2GM_DUPLICATE_REGION_RECEIPT")
    geometry_tamper = deepcopy(accept_envelopes)
    geometry_tamper[0]["accepted_document_geometry"]["primitives"][0]["geometry_normalized"]["a"][0] += 0.001
    expect_error(lambda: r2gm.aggregate(report, geometry_tamper), "R2GM_ACCEPTED_GEOMETRY_TAMPERED")

    for key in (
        "CEW_AUDIT_NEON_DATABASE_URL",
        "CEW_AUDIT_HTTPS_URL",
        "CEW_AUDIT_SHARED_SECRET",
        "CEW_AUDIT_SUPABASE_URL",
        "CEW_AUDIT_SUPABASE_SERVICE_ROLE_KEY",
        "RENDER",
        "VERCEL",
    ):
        os.environ.pop(key, None)
    shutil.rmtree(R2HR_STORE, ignore_errors=True)
    shutil.rmtree(R2GM_STORE, ignore_errors=True)
    previous_r2hr = workbench_api.R2HR_RUNTIME_STORE
    previous_r2gm = workbench_api.R2GM_RUNTIME_STORE
    workbench_api.R2HR_RUNTIME_STORE = R2HR_STORE
    workbench_api.R2GM_RUNTIME_STORE = R2GM_STORE
    try:
        for envelope in r2hr_envelopes:
            audit_store.persist_runtime_receipt(envelope, R2HR_STORE)
        runtime_r2gi = workbench_api._runtime_r2gi_report()
        require(runtime_r2gi["state"] == "READY_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW", "runtime R2GI prerequisite must become ready from persisted audit receipts")
        require(runtime_r2gi["candidate_head_sha"] == report["candidate_head_sha"], "runtime R2GI candidate provenance drift")
        require(runtime_r2gi["build_revision"] == report["build_revision"], "runtime R2GI build provenance drift")
        initial_runtime_r2gm = workbench_api._runtime_r2gm_report()
        require(initial_runtime_r2gm["state"] == "BLOCKED_GEOMETRY_ACCEPTANCE_REQUIRED", "runtime R2GM must start 0/4 blocked")
        require(initial_runtime_r2gm["region_coverage"] == "0/4", "runtime R2GM initial coverage mismatch")
        for runtime_region_id in sorted(proposals):
            proposal = r2gm.build_region_proposal(runtime_r2gi, runtime_region_id)
            receipt = r2gm_receipt(proposal)
            envelope = r2gm.audit_envelope(f"R2GM-RUNTIME-{runtime_region_id}", receipt, proposal)
            audit_store.persist_runtime_receipt(envelope, R2GM_STORE)
        runtime_complete = workbench_api._runtime_r2gm_report()
        require(runtime_complete["state"] == "READY_FOR_R2C_DOCUMENT_GEOMETRY_SCENE_ADAPTER", "runtime persisted R2GM receipts must aggregate to R2C readiness")
        require(runtime_complete["candidate_receipt_count"] == 4, "runtime R2GM candidate receipt count mismatch")
        require(runtime_complete["build_revision"] == report["build_revision"], "runtime R2GM build provenance drift")
        require(runtime_complete["r2c_scene_adapter_authorized"] is True, "runtime R2GM 4/4 acceptance must authorize only R2C")
        require(runtime_complete["canonical_write_authorized"] is False, "runtime R2GM must preserve canonical-write block")
    finally:
        workbench_api.R2HR_RUNTIME_STORE = previous_r2hr
        workbench_api.R2GM_RUNTIME_STORE = previous_r2gm
        shutil.rmtree(R2HR_STORE, ignore_errors=True)
        shutil.rmtree(R2GM_STORE, ignore_errors=True)

    print("CEW_PWB005_R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE = PASS")
    print("R2GM_R2GI_ENTRY_GATE = FAIL_CLOSED")
    print("R2GM_CANDIDATE_AND_BUILD_REVISION_SEPARATION = PASS")
    print("R2GM_R2M_BUILD_REVISION_MATCH = PASS")
    print("R2GM_EXACT_PROPOSAL_FINGERPRINT = PASS")
    print("R2GM_DOCUMENT_GEOMETRY_MATERIALIZATION = HUMAN_ACCEPTANCE_ONLY")
    print("R2GM_PARTIAL_REGION_COVERAGE = BLOCKED")
    print("R2GM_REJECT_AND_DEFER = BLOCK_R2C")
    print("R2GM_4_OF_4_ACCEPTANCE_NEXT_GATE = R2C_DOCUMENT_GEOMETRY_SCENE_ADAPTER_REQUIRED")
    print("R2GM_TECHNICAL_IDENTITY_AUTHORIZED = false")
    print("R2GM_STRUCTURAL_IDENTITY_AUTHORIZED = false")
    print("R2GM_CANONICAL_WRITE_AUTHORIZED = false")
    print("R2GM_ENGINEERING_AUTHORITY_EFFECT = NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
