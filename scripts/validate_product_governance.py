#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json"
AGENT_OPERATING = ROOT / "automation/AI_NATIVE_AGENT_OPERATING_CONTRACT_v1.json"
DECISION_REGISTER = ROOT / "automation/PRODUCT_DECISION_REGISTER_v1.json"
CEW_STATE = ROOT / "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"
CEW_QUEUE = ROOT / "automation/CEW_PRODUCT_TRANSFORMATION_QUEUE_v1.json"
CEW_B1_PLAN = ROOT / "automation/CEW_B1_DOCUMENT_DRAWING_AGENT_PLAN_v1.json"
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
    agents = load(AGENT_OPERATING)
    decisions = load(DECISION_REGISTER)
    cew = load(CEW_STATE)
    cew_queue = load(CEW_QUEUE)
    b1_plan = load(CEW_B1_PLAN)
    b1 = load(B1_HUMAN)
    etw_status = load(ETW_STATUS)
    etw_manifest = load(ETW_MANIFEST)

    assert manifest["status"] == "CANONICAL"

    for path_str in sorted(set(iter_repo_paths(manifest))):
        assert_path(path_str)

    governance = manifest["repository_governance"]
    assert governance["agent_operating_contract"] == "automation/AI_NATIVE_AGENT_OPERATING_CONTRACT_v1.json"
    assert governance["product_decision_register"] == "automation/PRODUCT_DECISION_REGISTER_v1.json"
    assert governance["product_family_capability_map"].endswith("CEW_ETWIN_PRODUCT_FAMILY_CAPABILITY_MAP_v1.md")

    current_state = manifest["current_state"]
    assert current_state["cew_product_queue"] == "automation/CEW_PRODUCT_TRANSFORMATION_QUEUE_v1.json"
    assert current_state["cew_b1_execution_plan"] == "automation/CEW_B1_DOCUMENT_DRAWING_AGENT_PLAN_v1.json"

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

    assert agents["status"] == "REQUIRED_CROSS_PRODUCT_CONTRACT"
    principles = agents["principles"]
    assert principles["least_authority"] is True
    assert principles["read_does_not_imply_write"] is True
    assert principles["proposal_does_not_imply_approval"] is True
    assert principles["implementation_does_not_imply_promotion"] is True
    assert principles["agent_output_is_professional_authority"] is False
    assert principles["one_promotion_owner_per_slice"] is True
    assert principles["support_agent_can_promote"] is False
    assert principles["human_professional_gate_may_be_bypassed"] is False

    by_id = {row["decision_id"]: row for row in decisions.get("decisions", [])}
    assert "PRODUCT-HF-001" in by_id
    hf_decision = by_id["PRODUCT-HF-001"]
    assert hf_decision["state"] == "ACCEPTED"
    assert hf_decision["record"] == "docs/DECISIONI/PRODUCT_HF_001_PARTICIPANT_REVIEWER_SEPARATION_v1.md"
    assert_path(hf_decision["record"])

    program = cew["program"]
    assert program["governance_manifest"] == "automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json"
    assert program["code_development_model"] == models["cew_development_model"]
    assert program["human_centred_model"] == models["cew_human_centred_model"]
    assert program["current_b1_human_acceptance_contract"] == "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json"

    current = cew["current_product_work_item"]
    assert current["current_slice"] == "B1.8"
    assert current["state"] == "IN_PROGRESS_IMPLEMENTED_CANDIDATE_HVA_PENDING"
    assert "HUMAN_ACCEPTANCE_V2_NOT_EXECUTED" in current["promotion_blockers"]
    assert "B1_8_ACCESSIBILITY_GATE_NOT_SATISFIED" in current["promotion_blockers"]
    assert "EXTENDED_B1_SAME_REVISION_PRODUCTION_SMOKE_NOT_SATISFIED" in current["promotion_blockers"]
    assert cew["governance"]["participant_and_reviewer_separated"] is True
    assert cew["governance"]["telemetry_hidden_from_participant_by_default"] is True
    assert cew["governance"]["ci_implies_human_acceptance"] is False
    assert cew["governance"]["deployment_implies_promotion"] is False

    queue_b1 = next(row for row in cew_queue["items"] if row["id"] == "CEW-B1-SOURCE-EVIDENCE-JOURNEY")
    assert queue_b1["state"] == "IN_PROGRESS"
    assert queue_b1["current_slice"] == "B1.8"
    assert queue_b1["current_slice_state"] == "IMPLEMENTED_CANDIDATE_HVA_PENDING"
    assert queue_b1["human_acceptance_contract"] == "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json"
    assert queue_b1["current_validation"]["HUMAN_ACCEPTANCE_V2"] == "REQUIRED_NOT_EXECUTED"
    assert "B1_8_HUMAN_ACCEPTANCE_V2_NOT_EXECUTED" in queue_b1["promotion_blockers"]
    assert current["id"] == queue_b1["id"]
    assert current["current_slice"] == queue_b1["current_slice"]

    plan_by_id = {row["id"]: row for row in b1_plan["slices"]}
    assert b1_plan["development_model"] == models["cew_development_model"]
    assert b1_plan["human_centred_model"] == models["cew_human_centred_model"]
    assert b1_plan["human_acceptance_contract"] == "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json"
    assert plan_by_id["B1.7"]["state"] == "HISTORICAL_INSTRUMENT_VALIDATED_INTERACTION_REWORK_REQUIRED"
    assert plan_by_id["B1.7"]["promotion_effect"] == "NONE"
    assert plan_by_id["B1.8"]["state"] == "IMPLEMENTED_CANDIDATE_HVA_PENDING"
    assert plan_by_id["B1.8"]["contract"] == "automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json"
    assert plan_by_id["B1.8"]["gate_state"]["HVA_GATE"] == "REQUIRED_NOT_SATISFIED"
    assert plan_by_id["B1.8"]["gate_state"]["ACCESSIBILITY_GATE"] == "REQUIRED_NOT_SATISFIED"

    assert b1["status"] == "IMPLEMENTED_CANDIDATE_HVA_PENDING"
    assert b1["human_hva_state"] == "REQUIRED_NOT_SATISFIED"
    assert b1["accessibility_gate_state"] == "REQUIRED_NOT_SATISFIED"
    assert b1["production_smoke_state"] == "REQUIRED_AFTER_HVA_ON_ACCEPTED_REVISION"
    layers = b1["layers"]
    assert layers["participant_surface"]["show_internal_task_ids"] is False
    assert layers["participant_surface"]["show_runtime_sha"] is False
    assert layers["participant_surface"]["show_live_test_counters"] is False
    assert layers["participant_surface"]["show_release_decision"] is False
    assert layers["participant_surface"]["show_receipt_export"] is False
    assert layers["participant_surface"]["professional_language_first"] is True
    assert layers["reviewer_surface"]["separate_from_participant_surface"] is True
    assert layers["reviewer_surface"]["owns_hva_decision"] is True
    assert layers["receipt_layer"]["canonical_write_authorized"] is False
    assert layers["receipt_layer"]["promotion_authorized"] is False
    assert b1["production_promotion_authorized"] is False

    observed = etw_status["observed_external_preparation"]
    assert observed["state"] == "PREPARED_BLOCKED_PROMOTION"
    assert observed["prepared_head_sha"] == "36b101ed32cb61263609c84f17b740c2446be9c1"
    assert "CEW_PROMOTED_BASELINE" in etw_status["promotion_blockers"]
    assert "A0_HUMAN_FACTORS_V2_REVALIDATION" in etw_status["promotion_blockers"]
    assert etw_status["production_promotion_authorized"] is False

    assert etw_manifest["schema_version"] == "1.0"
    assert etw_manifest["status"] == "CANONICAL"
    assert etw_manifest["plan"].endswith("ETWIN_PLATFORM_EXTENSION_OVER_CEW_v1.md")
    assert etw_manifest["orchestration_model"].endswith("ETW_AGENTIC_DEVELOPMENT_ORCHESTRATION_v1.md")
    assert etw_manifest["current_promotion_plan"] == models["etwin_platform_promotion_program"]
    assert etw_manifest["current_promotion_orchestration_model"] == models["etwin_agentic_promotion_orchestration"]
    assert etw_manifest["a0_revalidation_required_before_promotion"] is True
    assert etw_manifest["cew_promoted_baseline_sha"] is None
    assert etw_manifest["engineering_authority_unchanged"] is True

    print("PRODUCT_GOVERNANCE_CONSISTENCY_PASS")
    print("CEW_B18_IMPLEMENTATION = CANDIDATE_HVA_PENDING")
    print("ETW_A0 = PREPARED_BLOCKED_PROMOTION")


if __name__ == "__main__":
    main()
