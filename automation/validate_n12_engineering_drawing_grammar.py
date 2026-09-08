#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation" / "N12_ENGINEERING_DRAWING_GRAMMAR_CONTRACT_v1.json"
CORPUS = ROOT / "data" / "benchmark" / "n12_engineering_grammar_regression_v1.json"

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

ALLOWED_PROVENANCE = {
    "PROJECT_LEARNED",
    "VERIFIED_REFERENCE",
    "METHOD_RULE",
    "HUMAN_TAUGHT_PROJECT_RULE",
}

REQUIRED_GATES = {
    "KG-G1_EVIDENCE_SEMANTICS_PASS",
    "KG-G2_TECHNICAL_GRAMMAR_PASS",
    "KG-G3_STRUCTURAL_RELATION_PASS",
    "KG-G4_KNOWLEDGE_PROVENANCE_PASS",
    "KG-G5_HELD_OUT_N12_INTERPRETATION_PASS",
}


def fail(message: str) -> None:
    print(f"N12_ENGINEERING_DRAWING_GRAMMAR_FAIL: {message}")
    raise SystemExit(1)


def load(path: Path):
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def validate_contract(contract):
    authority = contract.get("authority", {})
    if authority.get("grammar_output") != "STRUCTURAL_HYPOTHESIS_CANDIDATE":
        fail("grammar output authority changed")
    for key in (
        "human_review_required",
        "structural_identity_authorized",
        "canonical_geometry_authorized",
        "canonical_write_authorized",
    ):
        if key not in authority:
            fail(f"missing authority field: {key}")
    if authority["human_review_required"] is not True:
        fail("human review must remain required")
    if authority["structural_identity_authorized"] is not False:
        fail("automatic structural identity must remain forbidden")
    if authority["canonical_geometry_authorized"] is not False:
        fail("automatic canonical geometry must remain forbidden")
    if authority["canonical_write_authorized"] is not False:
        fail("canonical write must remain forbidden")
    if authority.get("engineering_authority_effect") != "NONE":
        fail("engineering authority escalation detected")

    invariants = set(contract.get("invariants", []))
    missing = EXPECTED_INVARIANTS - invariants
    if missing:
        fail(f"missing invariants: {sorted(missing)}")

    provenance = set(contract.get("knowledge_provenance_classes", []))
    if provenance != ALLOWED_PROVENANCE:
        fail(f"knowledge provenance classes diverged: {sorted(provenance)}")

    gates = set(contract.get("readiness_gates", []))
    if gates != REQUIRED_GATES:
        fail(f"readiness gates diverged: {sorted(gates)}")


def validate_case_shape(case, group):
    required = {"case_id", "name", "rule_refs", "input", "forbidden_outputs", "required_output", "source_binding_state"}
    missing = required - set(case)
    if missing:
        fail(f"{group} {case.get('case_id', '<unknown>')} missing fields: {sorted(missing)}")
    if not case["rule_refs"]:
        fail(f"{case['case_id']} has no rule refs")
    if not case["forbidden_outputs"]:
        fail(f"{case['case_id']} has no forbidden outputs")
    dangerous = {"STRUCTURAL_IDENTITY", "CANONICAL_WRITE", "CANONICAL_SECTION_ASSIGNMENT", "CANONICAL_ARMATURE"}
    if case["required_output"] in dangerous:
        fail(f"{case['case_id']} requires a promoting output")


def evaluate_training_case(case):
    cid = case["case_id"]
    inp = case["input"]
    expected = case["required_output"]

    if cid == "TR-RC-001":
        actual = "AMBIGUOUS_TECHNICAL_OBJECT_CANDIDATE" if inp.get("primitive") == "RECTANGULAR_ENVELOPE" else "UNHANDLED"
    elif cid == "TR-RC-002":
        actual = "REBAR_CALLOUT_CANDIDATE" if inp.get("target_relation") is None else "REBAR_TARGET_RELATION_CANDIDATE"
    elif cid == "TR-RC-003":
        same_metric = inp.get("metric_signature_a") == inp.get("metric_signature_b")
        actual = "IDENTITY_HYPOTHESIS_NEEDS_SECOND_DISCRIMINANT" if same_metric and not inp.get("independent_discriminant") else "IDENTITY_REVIEW_CANDIDATE"
    else:
        fail(f"training evaluator missing for {cid}")

    if actual != expected:
        fail(f"training case {cid}: expected {expected}, got {actual}")
    return actual


def evaluate_held_out_governance(case):
    state = case["source_binding_state"]
    if state == "SOURCE_BINDING_REQUIRED":
        return "NOT_EXECUTABLE"
    return "BOUND_READY_FOR_INTERPRETATION_TEST"


def validate_corpus(corpus):
    training = corpus.get("training_cases", [])
    held_out = corpus.get("held_out_cases", [])
    if not training or not held_out:
        fail("training and held-out corpora must both be non-empty")

    ids = set()
    for group_name, cases in (("training", training), ("held_out", held_out)):
        for case in cases:
            validate_case_shape(case, group_name)
            if case["case_id"] in ids:
                fail(f"duplicate case id: {case['case_id']}")
            ids.add(case["case_id"])

    training_results = {case["case_id"]: evaluate_training_case(case) for case in training}
    held_out_results = {case["case_id"]: evaluate_held_out_governance(case) for case in held_out}

    policy = corpus.get("gate_policy", {})
    if policy.get("automatic_structural_identity") is not False:
        fail("corpus policy permits automatic structural identity")
    if policy.get("canonical_write_authorized") is not False:
        fail("corpus policy permits canonical write")
    if policy.get("kg_g5_pass_requires_all_held_out_bound_and_passed") is not True:
        fail("KG-G5 must require all held-out cases bound and passed")

    all_held_out_bound = all(v != "NOT_EXECUTABLE" for v in held_out_results.values())
    kg_g5 = "PASS" if all_held_out_bound else "BLOCKED_SOURCE_BINDING_REQUIRED"

    return training_results, held_out_results, kg_g5


def main():
    contract = load(CONTRACT)
    corpus = load(CORPUS)
    validate_contract(contract)
    training_results, held_out_results, kg_g5 = validate_corpus(corpus)

    print("N12_ENGINEERING_DRAWING_GRAMMAR_CONTRACT_PASS")
    for cid, result in training_results.items():
        print(f"TRAINING_CASE_PASS {cid} {result}")
    for cid, result in held_out_results.items():
        print(f"HELD_OUT_CASE {cid} {result}")
    print(f"KG_G5_STATE {kg_g5}")
    print("N12_ENGINEERING_DRAWING_GRAMMAR_FOUNDATION_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
