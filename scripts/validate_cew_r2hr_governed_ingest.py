#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import cew_professional_gap_review as gap_review
import cew_r2hr_governed_ingest as ingest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_PWB005_R2GI_GOVERNED_REVIEW_INGEST_CONTRACT_v1.json"


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


def synthetic_receipt(region_id: str, *, unresolved_first: bool = False) -> dict:
    template = gap_review.template(region_id)
    decisions = []
    for index, gap in enumerate(template["gaps"]):
        decision = "UNRESOLVED_FROM_CURRENT_VIEW" if unresolved_first and index == 0 else "SUPPORTED_CONTINUITY_HYPOTHESIS"
        decisions.append(
            {
                "gap_hypothesis_id": gap["gap_hypothesis_id"],
                "review_tier": gap["review_tier"],
                "decision": decision,
                "rationale": "Synthetic governance validation only; no geometry acceptance is created.",
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
        "reviewer_label": "CI synthetic R2GI validator",
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


def envelope(region_id: str, *, unresolved_first: bool = False) -> dict:
    return gap_review.audit_envelope(
        f"R2GI-VALIDATOR-{region_id}",
        synthetic_receipt(region_id, unresolved_first=unresolved_first),
    )


def main() -> int:
    require(CONTRACT.is_file(), "R2GI contract missing")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["geometry_materialization_authorized"] is False, "contract must not authorize geometry")
    require(contract["canonical_write_authorized"] is False, "contract must not authorize canonical writes")
    require(contract["engineering_authority_effect"] == "NONE", "contract must not create engineering authority")

    package_state = gap_review.status()
    require(package_state.get("state") == "READY", f"R2HR review package not ready: {package_state}")
    require(package_state.get("region_coverage") == "4/4", "R2HR package coverage drift")
    require(package_state.get("gap_hypothesis_total") == 10, "R2HR gap count drift")

    empty = ingest.ingest_envelopes([])
    require(empty["schema_version"] == "1.2", "R2GI report schema must preserve dual revision provenance")
    require(empty["state"] == "BLOCKED_HUMAN_RECEIPT_REQUIRED", "empty ingest must remain blocked")
    require(empty["region_coverage"] == "0/4", "empty ingest coverage mismatch")
    require(empty["build_revision"] is None, "empty R2GI ingest must not invent a build revision")
    require(empty["geometry_materialization_authorized"] is False, "empty ingest must not authorize geometry")

    complete_envelopes = [envelope(region_id) for region_id in sorted(ingest.EXPECTED_REGIONS)]
    expected_candidate = complete_envelopes[0]["r2hr_receipt"]["candidate_head_sha"]
    expected_build = complete_envelopes[0]["r2hr_receipt"]["build_revision"]
    complete = ingest.ingest_envelopes(complete_envelopes)
    require(complete["state"] == "READY_FOR_EXPLICIT_GEOMETRY_ACCEPTANCE_REVIEW", "complete human findings should advance only to explicit geometry acceptance review")
    require(complete["next_gate"] == "R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE_REQUIRED", "wrong next gate")
    require(complete["region_coverage"] == "4/4", "complete ingest coverage mismatch")
    require(complete["candidate_head_sha"] == expected_candidate, "R2GI candidate-head provenance drift")
    require(complete["build_revision"] == expected_build, "R2GI build-revision provenance drift")
    require(len(complete["review_findings"]) == 10, "review finding count must match 10 R2HR gap hypotheses")
    require(complete["review_findings_are_geometry"] is False, "review findings must not become geometry")
    require(complete["geometry_materialization_authorized"] is False, "R2GI must never materialize geometry")
    require(complete["canonical_write_authorized"] is False, "R2GI must never authorize canonical writes")
    require(complete["engineering_authority_effect"] == "NONE", "R2GI must never create engineering authority")
    require("objects" not in complete and "geometry_primitives" not in complete, "R2GI output must not smuggle technical geometry")
    for row in complete["regions"]:
        require(row["candidate_head_sha"] == expected_candidate, "R2GI region candidate provenance drift")
        require(row["build_revision"] == expected_build, "R2GI region build provenance drift")
    for finding in complete["review_findings"]:
        require(finding["candidate_head_sha"] == expected_candidate, "finding candidate provenance drift")
        require(finding["build_revision"] == expected_build, "finding build provenance drift")
        require(finding["finding_is_geometry"] is False, "finding must remain non-geometric")
        require(finding["geometry_materialization_authorized"] is False, "finding must not authorize geometry")
        require(finding["structural_identity_authorized"] is False, "finding must not create structural identity")

    unresolved_envelopes = [
        envelope(region_id, unresolved_first=(index == 0))
        for index, region_id in enumerate(sorted(ingest.EXPECTED_REGIONS))
    ]
    unresolved = ingest.ingest_envelopes(unresolved_envelopes)
    require(unresolved["state"] == "BLOCKED_UNRESOLVED_HUMAN_REVIEW", "unresolved decision must block geometry acceptance")
    require(unresolved["next_gate"] == "R2HR_ADDITIONAL_SOURCE_OR_REVIEW_REQUIRED", "unresolved decision must route back to review")
    require(unresolved["build_revision"] == expected_build, "unresolved R2GI report must preserve build revision")
    require(unresolved["geometry_materialization_authorized"] is False, "unresolved review must not authorize geometry")

    duplicate = complete_envelopes + [deepcopy(complete_envelopes[0])]
    expect_error(lambda: ingest.ingest_envelopes(duplicate), "R2GI_DUPLICATE_REGION_RECEIPT")

    tampered = deepcopy(complete_envelopes[0])
    first_decision = tampered["r2hr_receipt"]["decisions"][0]
    first_decision["metric_snapshot"]["projected_gap_norm"] = float(first_decision["metric_snapshot"]["projected_gap_norm"]) + 0.001
    expect_error(lambda: ingest.ingest_envelopes([tampered]), "R2HR_DECISION_EVIDENCE_TAMPERED")

    build_tamper = deepcopy(complete_envelopes[0])
    build_tamper["r2hr_receipt"]["build_revision"] = "0" * 40
    expect_error(lambda: ingest.ingest_envelopes([build_tamper]), "R2HR_RECEIPT_PROVENANCE_MISMATCH:build_revision")

    authority_tamper = deepcopy(complete_envelopes[0])
    authority_tamper["r2hr_receipt"]["geometry_materialization_authorized"] = True
    expect_error(lambda: ingest.ingest_envelopes([authority_tamper]), "R2HR_RECEIPT_AUTHORITY_DRIFT")

    print("CEW_PWB005_R2GI_GOVERNED_INGEST = PASS")
    print("R2GI_EMPTY_INPUT_FAIL_CLOSED = PASS")
    print("R2GI_EXACT_PROVENANCE_VALIDATION = PASS")
    print("R2GI_CANDIDATE_AND_BUILD_REVISION_SEPARATION = PASS")
    print("R2GI_TAMPER_NEGATIVE_CONTROL = PASS")
    print("R2GI_UNRESOLVED_DECISION_BLOCKS = PASS")
    print("R2GI_REVIEW_FINDING_IS_NOT_GEOMETRY = PASS")
    print("R2GI_NEXT_GATE = R2GM_EXPLICIT_GEOMETRY_ACCEPTANCE_REQUIRED")
    print("GEOMETRY_MATERIALIZATION_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("ENGINEERING_AUTHORITY_EFFECT = NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
