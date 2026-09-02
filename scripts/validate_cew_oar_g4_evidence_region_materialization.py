#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_oar_g4_evidence_region_materialization as materialization
import cew_oar_g4_region_binding as binding


def expect_error(fn, reason: str, errors: list[str]) -> None:
    try:
        fn()
    except ValueError as exc:
        if str(exc) != reason:
            errors.append(f"expected {reason}, got {exc}")
    else:
        errors.append(f"expected fail-closed {reason}")


def fixtures() -> tuple[dict, dict, dict]:
    contract = binding.load_contract()
    proposal = binding.build_receipt(
        decision_id="g4-er-proposal-1",
        support_id="1",
        bbox={"x": 0.10, "y": 0.20, "w": 0.03, "h": 0.02},
        action=binding.PROPOSAL_ACTION,
        timestamp="2026-09-02T08:00:00+00:00",
        base_proposal_decision_id=binding.unbound_revision_anchor("1"),
        contract=contract,
    )
    confirmation = binding.build_receipt(
        decision_id="g4-er-confirm-1",
        support_id="1",
        bbox=proposal["bbox"],
        action=binding.CONFIRM_ACTION,
        timestamp="2026-09-02T08:01:00+00:00",
        base_proposal_decision_id=proposal["decision_id"],
        contract=contract,
    )
    return contract, proposal, confirmation


def main() -> int:
    errors: list[str] = []
    contract, proposal, confirmation = fixtures()

    proposal_only = materialization.build_export_from_receipts([proposal], contract)
    if proposal_only["records"]:
        errors.append("proposed geometry must not export EvidenceRegionCandidate")
    if proposal_only["next_gate"] != "CONFIRM_DOCUMENTARY_GEOMETRY_FIRST":
        errors.append("proposal-only export must require confirmed documentary geometry")

    exported = materialization.build_export_from_receipts([proposal, confirmation], contract)
    if exported["schema"] != materialization.EXPORT_SCHEMA:
        errors.append("export schema mismatch")
    if len(exported["records"]) != 1:
        errors.append("exactly one confirmed support must export exactly one candidate")
    if exported["summary"]["geometry_confirmed"] != 1:
        errors.append("confirmed geometry count mismatch")
    if exported["summary"]["remaining_without_confirmed_geometry"] != 33:
        errors.append("remaining geometry count mismatch")
    if exported["next_gate"] != "F2_PROMOTION_REVIEW_REQUIRED":
        errors.append("confirmed geometry must stop at F2 promotion review")

    record = exported["records"][0]
    candidate = record["evidence_region_candidate"]
    expected_document = contract["document"]
    if record["support_id"] != "1" or record["evidence_object_id"] != "EOBJ-G4-SUPPORT-1":
        errors.append("support/evidence object binding mismatch")
    if record["oar_family_context"] != "COL-G4-40X40":
        errors.append("OAR family context not preserved")
    if record["oar_classification_confirmed"] is not False:
        errors.append("materialization illegally confirms OAR classification")
    if record["geometry_confirmation_receipt_id"] != confirmation["decision_id"]:
        errors.append("human localization receipt is not preserved")
    provenance = record["provenance"]
    for key in ["source_version_id", "page_id", "derived_asset_id", "page_transform_id", "coordinate_system"]:
        if provenance.get(key) != expected_document[key]:
            errors.append(f"provenance mismatch: {key}")
    if provenance.get("displayed_render_sha256") != expected_document["render_sha256"]:
        errors.append("displayed render hash missing from provenance")
    if candidate["source_version_id"] != expected_document["source_version_id"] or candidate["page_id"] != expected_document["page_id"]:
        errors.append("EvidenceRegionCandidate source/page mismatch")
    if candidate["state"] != "PROPOSED" or candidate["next_gate"] != "F2_PROMOTION_REVIEW_REQUIRED":
        errors.append("EvidenceRegionCandidate bypassed F2 promotion review")
    for key in [
        "candidate_is_evidence_region",
        "observation_created",
        "structural_binding_created",
        "epistemic_state_changed",
        "f2_registry_written",
        "canonical_write_authorized",
    ]:
        if candidate.get(key) is not False:
            errors.append(f"candidate illegally sets {key}")
    for key in [
        "candidate_is_evidence_region",
        "f2_registry_written",
        "observation_created",
        "structural_binding_created",
        "oar_human_confirmation",
        "structural_identity_authorized",
        "canonical_write_authorized",
    ]:
        if exported.get(key) is not False:
            errors.append(f"export illegally sets {key}")
    if exported["engineering_authority_effect"] != "NONE":
        errors.append("export illegally grants engineering authority")

    report = binding.aggregate([proposal, confirmation], contract)
    tampered_document = copy.deepcopy(report)
    tampered_document["document"]["page_transform_id"] = "WRONG"
    expect_error(
        lambda: materialization.build_export(tampered_document, contract),
        "OAR_G4_ER_MATERIALIZATION_DOCUMENT_MISMATCH",
        errors,
    )

    tampered_authority = copy.deepcopy(report)
    tampered_authority["canonical_write_authorized"] = True
    expect_error(
        lambda: materialization.build_export(tampered_authority, contract),
        "OAR_G4_ER_MATERIALIZATION_CANONICAL_WRITE_REJECTED",
        errors,
    )

    missing_receipt = copy.deepcopy(report)
    row = next(item for item in missing_receipt["objects"] if item["support_id"] == "1")
    row["geometry_confirmation_receipt_id"] = None
    expect_error(
        lambda: materialization.build_export(missing_receipt, contract),
        "OAR_G4_ER_MATERIALIZATION_CONFIRMATION_RECEIPT_REQUIRED",
        errors,
    )

    family_divergence = copy.deepcopy(report)
    row = next(item for item in family_divergence["objects"] if item["support_id"] == "1")
    row["family_id"] = "COL-G4-45X30"
    expect_error(
        lambda: materialization.build_export(family_divergence, contract),
        "OAR_G4_ER_MATERIALIZATION_FAMILY_CONTEXT_MISMATCH",
        errors,
    )

    if errors:
        print("CEW_OAR_G4_EVIDENCE_REGION_MATERIALIZATION = FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("CEW_OAR_G4_EVIDENCE_REGION_MATERIALIZATION = PASS")
    print("GEOMETRY_CONFIRMED_REQUIRED = true")
    print("EVIDENCE_REGION_CANDIDATE_MODEL_REUSED = true")
    print("SOURCE_PAGE_DERIVED_ASSET_PAGE_TRANSFORM_RECEIPT_BOUND = true")
    print("OAR_CLASSIFICATION_CONFIRMED = false")
    print("F2_REGISTRY_WRITTEN = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("STRUCTURAL_IDENTITY_AUTHORIZED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
