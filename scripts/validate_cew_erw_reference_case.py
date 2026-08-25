#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "CEW_ERW_CONTRACT_v1.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    args = ap.parse_args()

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    ref = contract["reference_vertical_slice"]

    if contract.get("milestone") != "CEW-F6" or contract.get("status") != "ACTIVE_IMPLEMENTATION_CONTRACT":
        raise AssertionError("ERW contract is not active for F6")
    if bundle.get("authority") != "DERIVED_REVIEW_WORKSPACE_ONLY":
        raise AssertionError("ERW authority drift")
    inv = contract["authority_invariants"]
    forbidden = (
        "workspace_may_modify_canonical_ledgers",
        "workspace_may_modify_f2_geometry",
        "workspace_may_reopen_m0g",
        "workspace_may_promote_without_direct_evidence",
        "candidate_comparison_is_primary_evidence",
    )
    if any(inv.get(k) is not False for k in forbidden):
        raise AssertionError("ERW authority boundary weakened")

    task = bundle["task"]
    residual = bundle["residual"]
    obs = bundle["source"]["observation"]
    viewer = bundle["source"]["viewer_binding"]
    member = bundle["model"]["candidate_member"]
    decision = bundle["reference_disposition_receipt"]

    if task["task_id"].strip() != ref["task_id"] or residual["residual_id"].strip() != ref["residual_id"]:
        raise AssertionError("reference task/residual drift")
    if obs["reference_item"].strip() != ref["source_scheme"]:
        raise AssertionError("reference source scheme drift")
    if obs["structural_binding"].strip():
        raise AssertionError("F2 observation binding was silently introduced")
    if "UNBOUND" not in obs["migration_note"]:
        raise AssertionError("F2 UNBOUND state not preserved")
    if viewer["binding_state"].strip() != "READY" or "UNBOUND" not in viewer["authority_note"]:
        raise AssertionError("viewer provenance/binding state drift")
    if member["source_member_id"] != "G5-B017" or member["support_i"] != "12" or member["support_j"] != "19":
        raise AssertionError("candidate member endpoint topology drift")

    candidates = {c["candidate_id"]: c for c in bundle["candidates"]}
    bad = candidates.get("ERW-N12-004-CAND-BIND-G5-B017")
    keep = candidates.get("ERW-N12-004-CAND-UNBOUND")
    if not bad or bad["status"] != "REJECTED_BY_CURRENT_EVIDENCE" or bad["selectable"] is not False:
        raise AssertionError("forbidden G5-B017 binding became selectable")
    if not keep or keep["status"] != "SUPPORTED_DISPOSITION" or keep["selectable"] is not True:
        raise AssertionError("UNBOUND disposition not available")
    if decision["outcome"] != "UNBOUND" or decision["selected_candidate"] != keep["candidate_id"]:
        raise AssertionError("reference decision must retain UNBOUND")
    if decision.get("canonical_write") is not False or bundle.get("canonical_mutation") != "FORBIDDEN":
        raise AssertionError("reference workspace attempted canonical mutation")
    if decision["requested_epistemic_state"] != "ND_MEMBER_BINDING":
        raise AssertionError("member binding epistemic state was promoted")

    print("ERW_REFERENCE_CASE_PASS")
    print("TASK=ERW-N12-004")
    print("RESIDUAL=M1E-B06-R11")
    print("SOURCE_SCHEME=T6A-G03")
    print("CANDIDATE_MEMBER=G5-B017:12-19")
    print("BIND_G5_B017=REJECTED_BY_CURRENT_EVIDENCE")
    print("DISPOSITION=UNBOUND")
    print("F2_GEOMETRY_MUTATION=FORBIDDEN")
    print("M0G_REOPEN=FORBIDDEN")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
