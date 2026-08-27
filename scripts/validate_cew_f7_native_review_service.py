#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import cew_f7_native_review_service as service

ROOT = Path(__file__).resolve().parents[1]


def receipt(decision_id: str, observation: str) -> dict:
    schema = json.loads(service.RECEIPT_SCHEMA.read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0",
        "decision_id": decision_id,
        "task_id": "ERW-N12-001",
        "residual_id": "M1E-B06-R08",
        "review_mode": "HUMAN_REVIEW",
        "reviewer": "synthetic-native-ui-conformance",
        "timestamp": "2000-01-01T00:00:00Z",
        "outcome": "CONFIRMED",
        "human_observation": observation,
        "evidence_regions": ["CEW-N12-REG-G01-R06"],
        "source_versions": ["CEW-N12-SRC-TAV05A-V17DEC414"],
        "direct_primary_evidence_observed": True,
        "requested_epistemic_state": "DOC",
        "target_id": "CEW-TARGET-REINFORCEMENT-OBSERVATION",
        "reopen_approval_id": "",
        "authority_acknowledgement": schema["authority_acknowledgement_exact"],
    }


def main() -> int:
    contract = json.loads(service.SERVICE_CONTRACT.read_text(encoding="utf-8"))
    ui = contract["ui_invariants"]
    auth = contract["authority_invariants"]
    if not all(ui[k] is True for k in (
        "prefilled_outcome_forbidden",
        "prefilled_human_observation_forbidden",
        "prefilled_direct_primary_claim_forbidden",
        "prefilled_promotion_target_forbidden",
        "prefilled_epistemic_promotion_forbidden",
        "human_authority_acknowledgement_requires_explicit_checkbox",
        "receipt_is_submitted_by_cew_without_manual_json_download",
    )):
        raise AssertionError("native review UI invariant weakened")
    for k in (
        "ui_state_is_engineering_authority",
        "service_may_impersonate_human_reviewer",
        "service_may_create_human_observation",
        "service_may_infer_structural_payload_from_unconstrained_free_text",
        "service_may_write_canonical_directly",
        "service_may_modify_f2_geometry",
        "service_may_reopen_m0g",
        "fixture_fields_accepted_from_interactive_api",
        "runtime_audit_may_feed_canonical",
    ):
        if auth[k] is not False:
            raise AssertionError(f"native review authority invariant weakened: {k}")

    task_rows = service.rows(service.TASKS)
    root_html = service.control_room.build(service.load_json(service.STATE), service.load_json(service.ISSUES), task_rows)
    if "/review/f7?task=ERW-N12-001" not in root_html or "Revisione umana evidenze F7" not in root_html:
        raise AssertionError("Control Room does not expose native F7 review")
    review_html = service.render_review("ERW-N12-001")
    if "Invia a CEW" not in review_html or "/api/f7/receipt" not in review_html:
        raise AssertionError("native review submit UI missing")
    if "2 Φ12 superiori + 2 Φ12 inferiori" in review_html:
        raise AssertionError("real/synthetic reinforcement observation was prefilled in UI")
    if "selected" in review_html.lower():
        raise AssertionError("human review select field was preselected")

    with tempfile.TemporaryDirectory() as td:
        store = service.ensure_runtime_store(Path(td) / "receipts")

        positive = service.process_receipt(receipt("NATIVE-POSITIVE", "2 Φ12 superiori + 2 Φ12 inferiori"), store)
        if positive["state"] != "PATCH_CANDIDATE_READY_NO_WRITE":
            raise AssertionError(f"directional receipt did not reach governed candidate: {positive}")
        candidate = positive["patch_candidate"]
        sem = candidate["semantic_payload"]
        if sem["upper"] != {"count": 2, "diameter_mm": 12} or sem["lower"] != {"count": 2, "diameter_mm": 12}:
            raise AssertionError("directional reinforcement semantics collapsed or drifted")
        if sem["raw_human_observation"] != "2 Φ12 superiori + 2 Φ12 inferiori":
            raise AssertionError("raw human observation not preserved verbatim")
        if candidate["canonical_write_authorized"] is not False or candidate["canonical_write_performed"] is not False:
            raise AssertionError("native candidate gained canonical write authority")

        aggregate = service.process_receipt(receipt("NATIVE-AGGREGATE", "4 Φ12"), store)
        if aggregate["state"] != "SEMANTIC_BLOCKED" or "SEMANTIC_DIRECTIONAL_GRAMMAR_REQUIRED" not in aggregate["reason_codes"]:
            raise AssertionError("aggregate reinforcement was not fail-closed")

        bad_ack = receipt("NATIVE-BAD-ACK", "2 Φ12 superiori + 2 Φ12 inferiori")
        bad_ack["authority_acknowledgement"] = "true"
        rejected = service.process_receipt(bad_ack, store)
        if rejected["state"] != "RECEIPT_REJECTED":
            raise AssertionError("invalid authority acknowledgement was accepted")

        injected = receipt("NATIVE-FIXTURE-INJECTION", "2 Φ12 superiori + 2 Φ12 inferiori")
        injected["fixture_only"] = True
        rejected_fixture = service.process_receipt(injected, store)
        if rejected_fixture["state"] != "RECEIPT_REJECTED" or "UNEXPECTED_FIELDS_FORBIDDEN" not in rejected_fixture["reason_codes"]:
            raise AssertionError("interactive fixture field injection was accepted")

        persisted = list(store.glob("*.json"))
        if len(persisted) != 2:
            raise AssertionError(f"runtime audit persistence count drift: {len(persisted)}")

    print("CEW_F7_NATIVE_REVIEW_SERVICE_PASS")
    print("CONTROL_ROOM_NATIVE_REVIEW=PASS")
    print("HUMAN_FIELDS_PREFILLED=0")
    print("DIRECTIONAL_R08_TO_PATCH_CANDIDATE=PASS")
    print("AGGREGATE_4PHI12=SEMANTIC_BLOCKED")
    print("INVALID_AUTHORITY_ACK=REJECTED")
    print("INTERACTIVE_FIXTURE_INJECTION=REJECTED")
    print("RUNTIME_RECEIPT_AUDIT=APPEND_ONLY_NONCANONICAL")
    print("CANONICAL_WRITE_EXECUTED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
