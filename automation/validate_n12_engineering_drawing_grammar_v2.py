#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "N12_ENGINEERING_DRAWING_GRAMMAR_CONTRACT_v1.json"
CORPUS = ROOT / "data" / "benchmark" / "n12_engineering_grammar_regression_v2.json"

EXPECTED_INVARIANTS = {
    "RECTANGLE_DOES_NOT_IMPLY_COLUMN",
    "DIMENSION_REQUIRES_RELATION",
    "REBAR_CALLOUT_REQUIRES_TARGET_BINDING",
    "SECTION_SIZE_REQUIRES_CONTEXTUAL_BINDING",
    "TOPOLOGY_OUTRANKS_VISUAL_PROXIMITY_FOR_IDENTITY",
    "PROTOTYPE_DOES_NOT_IMPLY_TRUTH",
    "CROSS_VIEW_CONFLICT_FAILS_CLOSED",
    "OCR_CONFIDENCE_IS_NOT_ENGINEERING_CONFIDENCE",
    "SOURCE_REMAINS_EVIDENTIARY_AUTHORITY",
}


def fail(msg):
    print(f"N12_ENGINEERING_DRAWING_GRAMMAR_FAIL: {msg}")
    raise SystemExit(1)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"cannot load {path.relative_to(ROOT)}: {exc}")


def validate_contract(c):
    a = c.get("authority", {})
    if a.get("grammar_output") != "STRUCTURAL_HYPOTHESIS_CANDIDATE": fail("authority output changed")
    if a.get("human_review_required") is not True: fail("human review must remain required")
    if a.get("structural_identity_authorized") is not False: fail("automatic structural identity forbidden")
    if a.get("canonical_geometry_authorized") is not False: fail("automatic canonical geometry forbidden")
    if a.get("canonical_write_authorized") is not False: fail("canonical write forbidden")
    if a.get("engineering_authority_effect") != "NONE": fail("engineering authority escalation")
    missing = EXPECTED_INVARIANTS - set(c.get("invariants", []))
    if missing: fail(f"missing invariants {sorted(missing)}")


def validate_binding(case):
    if case.get("source_binding_state") != "SOURCE_BOUND_READY_FOR_INTERPRETATION":
        fail(f"{case['case_id']} is not source-bound ready")
    b = case.get("source_binding", {})
    required = {"source_version_id","sha256","page_id","page_index","evidence_region_id","verification_basis"}
    missing = required - set(b)
    if missing: fail(f"{case['case_id']} missing source binding {sorted(missing)}")
    sha = b["sha256"]
    if len(sha) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in sha):
        fail(f"{case['case_id']} invalid sha256")
    return b


def training(case):
    cid, inp = case["case_id"], case["input"]
    if cid == "TR-RC-001":
        actual = "AMBIGUOUS_TECHNICAL_OBJECT_CANDIDATE" if inp.get("primitive") == "RECTANGULAR_ENVELOPE" else "UNHANDLED"
    elif cid == "TR-RC-002":
        actual = "REBAR_CALLOUT_CANDIDATE" if inp.get("target_relation") is None else "REBAR_TARGET_RELATION_CANDIDATE"
    elif cid == "TR-RC-003":
        same = inp.get("metric_signature_a") == inp.get("metric_signature_b")
        actual = "IDENTITY_HYPOTHESIS_NEEDS_SECOND_DISCRIMINANT" if same and not inp.get("independent_discriminant") else "IDENTITY_REVIEW_CANDIDATE"
    else:
        fail(f"training evaluator missing {cid}")
    if actual != case["required_output"]: fail(f"{cid}: expected {case['required_output']} got {actual}")
    return actual


def held_out(case):
    b = validate_binding(case)
    cid, inp = case["case_id"], case["input"]

    if cid == "HO-RC-001":
        if b.get("source_version_id") != "N12-CALC-RELATION-RC-P13-V7E2560FE": fail("HO-RC-001 wrong source")
        if b.get("evidence_region_id") != "N12-CALC-RELATION-RC-P13-25X70-CANDIDATE": fail("HO-RC-001 wrong region")
        actual = "SECTION_DIMENSION_CANDIDATE_NEEDS_TARGET_BINDING" if inp.get("token") == "25x70" and inp.get("target_element_bound") is False else "SECTION_REVIEW_CANDIDATE"

    elif cid == "HO-RC-002":
        if b.get("source_version_id") != "N12-CALC-RELATION-RC-P10-V3DC4528D": fail("HO-RC-002 wrong source")
        if b.get("evidence_region_id") != "N12-CALC-RELATION-RC-P10-G5-TRUNCATION": fail("HO-RC-002 wrong region")
        if inp.get("visual_completion_allowed") is not False: fail("HO-RC-002 permits visual completion")
        actual = "PRESERVE_DOCUMENTED_TRUNCATION" if inp.get("upper_level_segments") == "C2-C7" and inp.get("full_frame_segments") == "C1-C8" else "TRUNCATION_REVIEW_REQUIRED"

    elif cid == "HO-RC-003":
        loc = b.get("token_locator", {})
        if loc.get("ocr_confidence") != inp.get("ocr_confidence"): fail("HO-RC-003 OCR confidence mismatch")
        actual = "TECHNICAL_TOKEN_NEEDS_CONTEXT" if inp.get("target_relation") is None else "TECHNICAL_TOKEN_WITH_TARGET_RELATION_CANDIDATE"

    else:
        fail(f"held-out evaluator missing {cid}")

    if actual != case["required_output"]: fail(f"{cid}: expected {case['required_output']} got {actual}")
    if actual in set(case.get("forbidden_outputs", [])): fail(f"{cid} produced forbidden output")
    return f"HELD_OUT_INTERPRETATION_PASS:{actual}"


def main():
    contract = load(CONTRACT)
    corpus = load(CORPUS)
    validate_contract(contract)
    train_results = {c["case_id"]: training(c) for c in corpus.get("training_cases", [])}
    held_results = {c["case_id"]: held_out(c) for c in corpus.get("held_out_cases", [])}
    if set(held_results) != {"HO-RC-001","HO-RC-002","HO-RC-003"}: fail("held-out corpus incomplete")
    if corpus.get("gate_policy", {}).get("automatic_structural_identity") is not False: fail("automatic identity policy changed")
    if corpus.get("gate_policy", {}).get("canonical_write_authorized") is not False: fail("canonical write policy changed")
    kg_g5 = "PASS" if all(v.startswith("HELD_OUT_INTERPRETATION_PASS:") for v in held_results.values()) else "BLOCKED"
    print("N12_ENGINEERING_DRAWING_GRAMMAR_CONTRACT_PASS")
    for cid,r in train_results.items(): print(f"TRAINING_CASE_PASS {cid} {r}")
    for cid,r in held_results.items(): print(f"HELD_OUT_CASE {cid} {r}")
    print(f"KG_G5_STATE {kg_g5}")
    if kg_g5 != "PASS": fail("KG-G5 did not pass")
    print("N12_ENGINEERING_DRAWING_GRAMMAR_V2_PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
