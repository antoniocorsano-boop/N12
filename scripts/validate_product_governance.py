#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json"
CEW_STATE = ROOT / "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"
B1_HUMAN = ROOT / "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json"
ETW_STATUS = ROOT / "automation/ETW_PROGRAM_STATUS_v1.json"
ETW_MANIFEST = ROOT / "automation/ETW_PROGRAM_MANIFEST_v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_path(path_str: str) -> None:
    path = ROOT / path_str
    assert path.exists(), f"Missing governed path: {path_str}"


def iter_repo_paths(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from iter_repo_paths(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_repo_paths(item)
    elif isinstance(value, str) and value.startswith(("docs/", "automation/", "data/", "knowledge/")):
        if value.endswith((".md", ".json", ".py")):
            yield value


def main() -> None:
    manifest = load(MANIFEST)
    cew = load(CEW_STATE)
    b1 = load(B1_HUMAN)
    etw_status = load(ETW_STATUS)
    etw_manifest = load(ETW_MANIFEST)

    assert manifest["status"] == "CANONICAL"

    # Every concrete governed path in the cross-product manifest must exist.
    for path_str in sorted(set(iter_repo_paths(manifest))):
        assert_path(path_str)

    models = manifest["current_models"]
    assert models["cew_development_model"].endswith("CEW_CODE_DEVELOPMENT_MODEL_v2.md")
    assert models["cew_human_centred_model"].endswith("CEW_HUMAN_CENTRED_GOVUK_MODEL_v2.md")
    assert models["etwin_platform_promotion_program"].endswith("ETWIN_PLATFORM_EXTENSION_OVER_CEW_v2.md")
    assert models["etwin_agentic_promotion_orchestration"].endswith("ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v2.md")

    boundaries = manifest["authority_boundaries"]
    assert boundaries["product_state_is_engineering_authority"] is False
    assert boundaries["ui_state_is_engineering_authority"] is False
    assert boundaries["agent_output_is_engineering_authority"] is False
    assert boundaries["deployment_implies_promotion"] is False
    assert boundaries["ci_implies_human_acceptance"] is False
    assert boundaries["production_implies_canonical_authority"] is False
    assert boundaries["human_observation_may_be_lossily_normalized"] is False
    assert boundaries["participant_may_self_approve_release"] is False

    # CEW current state must consume current governance rather than reconstruct it.
    program = cew["program"]
    assert program["governance_manifest"] == "automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json"
    assert program["code_development_model"] == models["cew_development_model"]
    assert program["human_centred_model"] == models["cew_human_centred_model"]
    assert program["current_b1_human_acceptance_contract"] == "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json"

    current = cew["current_product_work_item"]
    assert current["current_slice"] == "B1.8"
    assert current["state"] == "IN_PROGRESS_BLOCKED_HUMAN_ACCEPTANCE_V2_AND_PROMOTION"
    assert "HUMAN_ACCEPTANCE_V2_NOT_IMPLEMENTED_OR_EXECUTED" in current["promotion_blockers"]
    assert cew["governance"]["participant_and_reviewer_separated"] is True
    assert cew["governance"]["telemetry_hidden_from_participant_by_default"] is True
    assert cew["governance"]["ci_implies_human_acceptance"] is False
    assert cew["governance"]["deployment_implies_promotion"] is False

    # B1 v2 must encode the human separation discovered through real use.
    assert b1["status"] == "DESIGN_REQUIRED_NOT_IMPLEMENTED"
    layers = b1["layers"]
    assert layers["participant_surface"]["show_internal_task_ids"] is False
    assert layers["participant_surface"]["show_runtime_sha"] is False
    assert layers["participant_surface"]["show_live_test_counters"] is False
    assert layers["participant_surface"]["show_release_decision"] is False
    assert layers["participant_surface"]["show_receipt_export"] is False
    assert layers["reviewer_surface"]["separate_from_participant_surface"] is True
    assert layers["reviewer_surface"]["owns_hva_decision"] is True
    assert layers["receipt_layer"]["canonical_write_authorized"] is False
    assert b1["production_promotion_authorized"] is False

    # eTwin preparation evidence is preserved, but current promotion follows v2.
    observed = etw_status["observed_external_preparation"]
    assert observed["state"] == "PREPARED_BLOCKED_PROMOTION"
    assert observed["prepared_head_sha"] == "36b101ed32cb61263609c84f17b740c2446be9c1"
    assert "CEW_PROMOTED_BASELINE" in etw_status["promotion_blockers"]
    assert "A0_HUMAN_FACTORS_V2_REVALIDATION" in etw_status["promotion_blockers"]
    assert etw_status["production_promotion_authorized"] is False

    assert etw_manifest["current_promotion_plan"] == models["etwin_platform_promotion_program"]
    assert etw_manifest["current_promotion_orchestration_model"] == models["etwin_agentic_promotion_orchestration"]
    assert etw_manifest["a0_revalidation_required_before_promotion"] is True
    assert etw_manifest["cew_promoted_baseline_sha"] is None
    assert etw_manifest["engineering_authority_unchanged"] is True

    print("PRODUCT_GOVERNANCE_CONSISTENCY_PASS")


if __name__ == "__main__":
    main()
