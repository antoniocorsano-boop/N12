#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cew_evidence_region_candidate as erc

MIGRATION = ROOT / "migrations/cew/004_evidence_region_candidate_audit_PROPOSED_NOT_APPLIED.sql"
CONTRACT = ROOT / "docs/PRODUCT/CEW_EVIDENCE_REGION_CANDIDATE_V1_CONTRACT.md"


def expect_error(payload, reason, errors):
    try:
        erc.build_candidate(payload)
    except ValueError as exc:
        if str(exc) != reason:
            errors.append(f"expected {reason}, got {exc}")
    else:
        errors.append(f"expected fail-closed {reason}")


def main() -> int:
    errors=[]
    base={
        "source_version_id":"CEW-N12-SRC-TAV05A-V17DEC414",
        "page_id":"CEW-N12-PAGE-TAV05A-P001",
        "geometry_type":"BBOX",
        "coordinate_space":"NORMALIZED_0_1",
        "x":0.10,"y":0.20,"width":0.30,"height":0.15,
        "author_type":"HUMAN",
        "purpose":"Review exploded reinforcement area",
        "human_note":"User-selected region for document/evidence review",
        "state":"PROPOSED"
    }
    c=erc.build_candidate(base)
    if c["state"] != "PROPOSED" or c["next_gate"] != "F2_PROMOTION_REVIEW_REQUIRED":
        errors.append("valid candidate must stop at F2 promotion review")
    for key in ["candidate_is_evidence_region","observation_created","structural_binding_created","epistemic_state_changed","f2_registry_written","canonical_write_authorized"]:
        if c.get(key) is not False:
            errors.append(f"candidate illegally sets {key}")
    if not c["candidate_id"].startswith("CEW-ER-CAND-"):
        errors.append("candidate identity missing")

    expect_error({**base,"source_version_id":"WRONG"},"SOURCEVERSION_PAGE_MISMATCH",errors)
    expect_error({**base,"page_id":"UNKNOWN"},"PAGE_NOT_REGISTERED",errors)
    expect_error({**base,"x":0.9,"width":0.2},"BBOX_OUTSIDE_NORMALIZED_PAGE",errors)
    expect_error({**base,"width":0},"BBOX_OUTSIDE_NORMALIZED_PAGE",errors)
    expect_error({**base,"coordinate_space":"VIEWER_PIXELS"},"UNSUPPORTED_COORDINATE_SPACE",errors)
    expect_error({**base,"state":"READY_FOR_F2_PROMOTION_REVIEW"},"INITIAL_STATE_NOT_ALLOWED",errors)

    sql=MIGRATION.read_text(encoding="utf-8").lower()
    for token in ["do not apply to production", "product_audit_only", "canonical_write = false", "revoke update, delete, truncate"]:
        if token not in sql:
            errors.append(f"proposed migration missing append-only boundary: {token}")
    contract=CONTRACT.read_text(encoding="utf-8").lower()
    for token in ["candidate is not evidenceregion", "viewer rotation/zoom/pan", "separate governed f2 promotion", "nearest-member automatic binding"]:
        if token not in contract:
            errors.append(f"contract missing boundary: {token}")

    if errors:
        print("CEW_EVIDENCE_REGION_CANDIDATE = FAIL")
        for e in errors: print(f"ERROR: {e}")
        return 1
    print("CEW_EVIDENCE_REGION_CANDIDATE = PASS")
    print("VALID_SELECTION_TAV05A = PASS")
    print("VIEWER_COORDINATE_STORAGE = FORBIDDEN")
    print("F2_REGISTRY_WRITTEN = false")
    print("OBSERVATION_CREATED = false")
    print("STRUCTURAL_BINDING_CREATED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    print("PRODUCTION_MIGRATION_APPLIED = false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
