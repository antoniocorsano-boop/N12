#!/usr/bin/env python3
"""Regression: legacy revision-head recovery must replay governed transitions."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import cew_oar_g4_region_binding as binding
import cew_oar_g4_revision_head as revision_head

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql"
ATOMIC = ROOT / "scripts/cew_oar_g4_atomic_store.py"
NETLIFY = ROOT / "netlify/functions/cew-audit.mjs"
NETLIFY_REPLAY = ROOT / "netlify/functions/cew-oar-replay.mjs"


def _node_outcome(receipts: list[dict], binding_id: str, support_id: str) -> dict:
    program = r"""
import { replayOarHead } from './netlify/functions/cew-oar-replay.mjs';
let raw = '';
for await (const chunk of process.stdin) raw += chunk;
const payload = JSON.parse(raw);
try {
  const result = replayOarHead(payload.receipts, payload.binding_id, payload.support_id);
  process.stdout.write(JSON.stringify({ok: true, result}));
} catch (err) {
  process.stdout.write(JSON.stringify({ok: false, marker: String(err?.code || err?.message || err)}));
}
"""
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", program],
        cwd=ROOT,
        input=json.dumps({"receipts": receipts, "binding_id": binding_id, "support_id": support_id}),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(proc.stdout)


def _node_head(receipts: list[dict], binding_id: str, support_id: str) -> dict:
    outcome = _node_outcome(receipts, binding_id, support_id)
    assert outcome["ok"] is True, outcome
    return outcome["result"]


def _head_from_report(receipts: list[dict], support_id: str) -> tuple[str, str]:
    report = binding.aggregate(receipts)
    row = next(item for item in report["objects"] if str(item["support_id"]) == str(support_id))
    current = row.get("geometry_proposal_receipt_id") or binding.unbound_revision_anchor(support_id)
    return str(current), str(row["state"])


def _assert_python_rejects(receipts: list[dict], marker: str) -> None:
    try:
        binding.aggregate(receipts)
    except ValueError as exc:
        assert marker in str(exc), (marker, str(exc))
    else:
        raise AssertionError(f"canonical aggregate accepted divergent history: {marker}")


def main() -> None:
    contract = binding.load_contract()
    support_id = "1"
    binding_id = contract["binding_id"]
    unbound = binding.unbound_revision_anchor(support_id)

    p0 = binding.build_receipt(
        decision_id="legacy-p0",
        support_id=support_id,
        bbox={"x": 0.10, "y": 0.20, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        base_proposal_decision_id=unbound,
        timestamp="2026-09-01T10:00:00.000001+00:00",
        contract=contract,
    )
    p1 = binding.build_receipt(
        decision_id="legacy-p1",
        support_id=support_id,
        bbox={"x": 0.11, "y": 0.20, "w": 0.02, "h": 0.03},
        action=binding.PROPOSAL_ACTION,
        base_proposal_decision_id=p0["decision_id"],
        timestamp="2026-09-01T10:00:00.000002+00:00",
        contract=contract,
    )
    delayed_p0_confirm = binding.build_receipt(
        decision_id="legacy-confirm-p0-delayed",
        support_id=support_id,
        bbox=p0["bbox"],
        action=binding.CONFIRM_ACTION,
        base_proposal_decision_id=p0["decision_id"],
        timestamp="2026-09-01T10:00:00.000003+00:00",
        contract=contract,
    )
    legacy = [p0, p1, delayed_p0_confirm]

    expected_id, expected_state = _head_from_report(legacy, support_id)
    assert expected_id == p1["decision_id"]
    assert expected_state == "PROPOSED"

    py_head = revision_head.derive_revision_head(legacy, support_id, contract)
    assert py_head["current_proposal_decision_id"] == expected_id
    assert py_head["state"] == expected_state
    assert py_head["canonical_write_authorized"] is False
    assert py_head["engineering_authority_effect"] == "NONE"

    js_head = _node_head(legacy, binding_id, support_id)
    assert js_head["current_proposal_decision_id"] == expected_id
    assert js_head["state"] == expected_state
    assert js_head["stale_transition_count"] == 1
    assert js_head["snapshot_receipt_count"] == len(legacy)
    assert js_head["canonical_write_authorized"] is False
    assert js_head["engineering_authority_effect"] == "NONE"

    # Ordinary confirmation remains terminal and must agree across replay paths.
    confirmed = binding.build_receipt(
        decision_id="legacy-confirm-p1",
        support_id=support_id,
        bbox=p1["bbox"],
        action=binding.CONFIRM_ACTION,
        base_proposal_decision_id=p1["decision_id"],
        timestamp="2026-09-01T10:00:00.000004+00:00",
        contract=contract,
    )
    terminal = [p0, p1, delayed_p0_confirm, confirmed]
    expected_id, expected_state = _head_from_report(terminal, support_id)
    assert (expected_id, expected_state) == (p1["decision_id"], "GEOMETRY_CONFIRMED")
    assert revision_head.derive_revision_head(terminal, support_id, contract)["state"] == "GEOMETRY_CONFIRMED"
    js_terminal = _node_head(terminal, binding_id, support_id)
    assert (js_terminal["current_proposal_decision_id"], js_terminal["state"]) == (expected_id, expected_state)

    # Full governed-field parity: backend replay must reject every field that
    # canonical _validate_receipt_governance() rejects before deriving a head.
    field_mutations = {
        "task_id": "WRONG-TASK",
        "residual_id": "WRONG-RESIDUAL",
        "pilot_id": "WRONG-PILOT",
        "evidence_object_id": "WRONG-EVIDENCE",
        "family_id": "COL-G4-WRONG",
        "source_version_id": "WRONG-SOURCE",
        "page_id": "WRONG-PAGE",
        "derived_asset_id": "WRONG-ASSET",
        "page_transform_id": "WRONG-XFORM",
        "coordinate_system": "WRONG-COORDINATES",
    }
    for index, (field, value) in enumerate(field_mutations.items(), start=1):
        tampered = dict(p0)
        tampered["decision_id"] = f"tampered-{index:02d}"
        tampered["timestamp"] = f"2026-09-01T11:00:00.{index:06d}+00:00"
        tampered[field] = value
        fixture = [tampered]
        marker = f"OAR_REGION_GOVERNED_FIELD_MISMATCH_{field.upper()}"
        _assert_python_rejects(fixture, marker)
        outcome = _node_outcome(fixture, binding_id, support_id)
        assert outcome == {"ok": False, "marker": marker}, (field, outcome)

    # The complete OAR snapshot must be validated before requested-support
    # scoping. A divergent row outside that scope must poison both canonical
    # aggregate and Netlify replay instead of being silently filtered away.
    bad_binding = dict(p0)
    bad_binding["decision_id"] = "legacy-divergent-binding"
    bad_binding["timestamp"] = "2026-09-01T12:00:00.000001+00:00"
    bad_binding["binding_id"] = "WRONG-BINDING"
    binding_fixture = [p0, bad_binding]
    _assert_python_rejects(binding_fixture, "OAR_REGION_GOVERNED_FIELD_MISMATCH_BINDING_ID")
    outcome = _node_outcome(binding_fixture, binding_id, support_id)
    assert outcome == {"ok": False, "marker": "OAR_REGION_GOVERNED_FIELD_MISMATCH_BINDING_ID"}, outcome

    bad_support = dict(p0)
    bad_support["decision_id"] = "legacy-divergent-support"
    bad_support["timestamp"] = "2026-09-01T12:00:00.000002+00:00"
    bad_support["support_id"] = "999"
    support_fixture = [p0, bad_support]
    _assert_python_rejects(support_fixture, "OAR_REGION_SUPPORT_NOT_IN_PILOT")
    outcome = _node_outcome(support_fixture, binding_id, support_id)
    assert outcome == {"ok": False, "marker": "OAR_REGION_SUPPORT_NOT_IN_PILOT"}, outcome

    sql = SQL.read_text(encoding="utf-8").lower()
    atomic = ATOMIC.read_text(encoding="utf-8")
    netlify = NETLIFY.read_text(encoding="utf-8")
    replay_js = NETLIFY_REPLAY.read_text(encoding="utf-8")

    # Supabase: replay function drives both migration backfill and missing-head
    # recovery under the advisory-lock CAS boundary. Timestamp-only confirmed
    # head selection is forbidden.
    assert "cew_oar_replay_region_head_v1" in sql
    assert "cross join lateral public.cew_oar_replay_region_head_v1" in sql
    assert "from public.cew_oar_replay_region_head_v1(v_binding_id, v_support_id)" in sql
    assert "confirmed_heads as (" not in sql
    assert "oar_region_base_proposal_mismatch" in sql
    assert "v_stale := v_stale + 1" in sql
    assert "on conflict (binding_id, support_id) do nothing" in sql

    # Neon: no missing row may default directly to UNBOUND when legacy history
    # exists; it must derive through the canonical Python aggregate first.
    assert "revision_head.derive_revision_head(existing, support_id)" in atomic
    assert "OAR_REGION_LEGACY_HEAD_BACKFILL_FAILED" in atomic

    # Netlify: the legacy query reads all OAR receipts before replay scoping.
    legacy_query_start = netlify.index("const legacyResult = await db.sql`")
    legacy_query_end = netlify.index("const allOarReceipts", legacy_query_start)
    legacy_query = netlify[legacy_query_start:legacy_query_end]
    assert "receipt_json->>'binding_id'" not in legacy_query
    assert "receipt_json->>'support_id'" not in legacy_query
    assert "legacyHead = replayOarHead(allOarReceipts, bindingId, supportId)" in netlify
    assert "snapshot_receipt_count" in replay_js
    assert "globallySeenDecisions" in replay_js
    assert "validateOarReceiptGovernance(receipt, receiptBinding, receiptSupport)" in replay_js

    # Netlify legacy seed and CAS transition must not depend on sibling CTE
    # visibility. A missing PROPOSED head is inserted directly in its final
    # post-transition state and its RETURNING row drives receipt commit.
    assert "WITH seeded AS (" not in netlify
    assert "seeded_transition AS (" in netlify
    assert "updated_existing AS (" in netlify
    assert "SELECT binding_id FROM seeded_transition" in netlify
    assert "(SELECT count(*) FROM seeded)" not in netlify
    assert "globalReceiptCount = legacyHead.snapshot_receipt_count" in netlify
    assert "legacyHead.current_proposal_decision_id" in netlify
    assert "CASE WHEN ${action} = 'PROPOSE_GEOMETRY' THEN ${decisionId} ELSE ${legacyHead.current_proposal_decision_id} END" in netlify

    print("CEW_OAR_G4_REVISION_HEAD_REPLAY_PASS")
    print("legacy_p0_p1_delayed_confirm_p0=P1_PROPOSED")
    print("python_aggregate_projection=PASS netlify_replay_parity=PASS")
    print("netlify_full_oar_snapshot_validation=PASS netlify_seeded_transition_cas=PASS")
    print("supabase_replay_backfill=PASS neon_replay_backfill=PASS netlify_replay_backfill=PASS")
    print("canonical_write_authorized=false structural_identity_authorized=false engineering_authority_effect=NONE")


if __name__ == "__main__":
    main()