#!/usr/bin/env python3
"""Validate the OA1 acquisition-first group-review Workbench contract."""
from __future__ import annotations

import json
from pathlib import Path

import cew_acquisition_group_review as group_review
import cew_acquisition_human_workbench as workbench

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_OA1_GROUP_REVIEW_WORKBENCH_CONTRACT_v1.json"
COMPOSITION = ROOT / "scripts" / "cew_professional_workbench_api.py"


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schema"] == "CEW_OA1_GROUP_REVIEW_WORKBENCH_CONTRACT_v1"
    assert contract["status"] == "IMPLEMENTED_CANDIDATE_NOT_PROMOTED"
    assert contract["route"] == "/workbench/acquisition"
    assert contract["group_review"]["one_human_action_may_cover_many_candidates"] is True
    assert contract["group_review"]["stale_proposal_rejected"] is True
    assert contract["triage"]["automatic_classification"] is False
    assert contract["governance_boundaries"]["r2hr_r2gi_r2gm_bypassed"] is False
    assert contract["governance_boundaries"]["group_review_satisfies_oa_g4"] is False
    assert contract["governance_boundaries"]["evidence_region_materialization_required_before_oa_g4"] is True
    assert contract["authority"]["canonical_write_authorized"] is False
    assert contract["authority"]["structural_identity_authorized"] is False

    assert group_review.ACTION_TO_ROLE == {
        "CONFIRM_GROUP": "POSITIVE",
        "REJECT_GROUP": "NEGATIVE",
        "MARK_AMBIGUOUS": "AMBIGUOUS",
    }
    assert group_review._bucket(0.95) == "LIKELY_MATCH"
    assert group_review._bucket(0.80) == "REVIEW"
    assert group_review._bucket(0.50) == "OUTLIER"
    assert group_review.AUTHORITY["oa_g4_human_verified"] is False
    assert group_review.AUTHORITY["evidence_region_materialized"] is False
    assert group_review.AUTHORITY["canonical_write_authorized"] is False
    assert group_review.AUTHORITY["structural_identity_authorized"] is False

    html = workbench._page()
    for marker in (
        "Acquisizione assistita",
        "Questo è un…",
        "Trova simili",
        "Revisione del gruppo",
        "Seleziona probabili",
        "Conferma selezionati",
        "Rifiuta selezionati",
        "Segna come ambigui",
        "Le eccezioni restano visibili",
        "triage, non classificazione automatica",
    ):
        assert marker in html, marker

    source = COMPOSITION.read_text(encoding="utf-8")
    assert "import cew_acquisition_human_workbench as _acquisition" in source
    assert "router.include_router(_acquisition.build_router(source_workspace))" in source

    group_source = (ROOT / "scripts" / "cew_acquisition_group_review.py").read_text(encoding="utf-8")
    for forbidden in (
        "canonical_write_authorized\": True",
        "structural_identity_authorized\": True",
        "group_action_satisfies_oa_g4\": True",
    ):
        assert forbidden not in group_source
    for required in (
        "OA1_GROUP_REVIEW_STALE_PROPOSAL",
        "OA1_GROUP_REVIEW_DUPLICATE_CANDIDATE",
        "OA1_GROUP_REVIEW_CANDIDATE_ALREADY_REVIEWED",
        "EVIDENCE_REGION_MATERIALIZATION_REQUIRED_BEFORE_OA_G4",
    ):
        assert required in group_source

    print("CEW_OA1_GROUP_REVIEW_WORKBENCH_PASS")


if __name__ == "__main__":
    main()
