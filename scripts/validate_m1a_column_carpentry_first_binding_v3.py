#!/usr/bin/env python3
from __future__ import annotations

# v3 keeps the full v2 gate, replaces the source-conflict predicate, and
# guards the seven explicitly closed-to-current-source column residuals.

import validate_m1a_column_carpentry_first_binding_v2 as v2

RESIDUAL_PATH = v2.ROOT / "data/canonical/M1A_COLUMN_REINFORCEMENT_RESIDUALS_CURRENT_v1.csv"
EXPECTED_RESIDUALS = {
    ("G1", "3"): "UNBOUND_NO_SECTION_FAMILY",
    ("G1", "a"): "SECTION_MATCH_ONLY_NOT_MEMBER_BOUND",
    ("G1", "b"): "SECTION_MATCH_ONLY_NOT_MEMBER_BOUND",
    ("G1", "c"): "SECTION_MATCH_ONLY_NOT_MEMBER_BOUND",
    ("G1", "d"): "SECTION_MATCH_ONLY_NOT_MEMBER_BOUND",
    ("G3", "9"): "UNBOUND_AMBIGUOUS_TWO_40x40_FAMILIES",
    ("G3", "16"): "UNBOUND_AMBIGUOUS_TWO_40x40_FAMILIES",
}


def source_conflicts(
    storey: str,
    sid: str,
    orientation: str,
    families: list[dict[str, str]],
    compatible_ids: set[str],
) -> set[str]:
    result: set[str] = set()
    order_id = v2.STOREY_ORDER[storey]

    eligible_order_families = [
        fam for fam in families
        if fam["order_id"].strip() == order_id
        and fam["validation_state"].strip() not in v2.DEFAULT_EXCLUDED_VALIDATION_STATES
    ]
    exact_orientation_family_exists = any(
        v2.st(fam["section_drawn_cm"]) == v2.st(orientation)
        for fam in eligible_order_families
    )

    for fam in families:
        if fam["order_id"].strip() != order_id:
            continue
        if sid not in fam["_ids"]:  # type: ignore[operator]
            continue
        if fam["family_id"] in compatible_ids:
            continue

        same_unordered_section = v2.sk(fam["section_drawn_cm"]) == v2.sk(orientation)
        same_exact_orientation = v2.st(fam["section_drawn_cm"]) == v2.st(orientation)

        if not same_unordered_section:
            result.add(fam["family_id"])
            continue
        if exact_orientation_family_exists and not same_exact_orientation:
            result.add(fam["family_id"])

    return result


def validate_residuals() -> None:
    if not RESIDUAL_PATH.exists():
        raise AssertionError("missing M1A column residual register")
    rows = v2.read_csv(RESIDUAL_PATH)
    if len(rows) != 7:
        raise AssertionError(f"column residual register must contain exactly 7 rows, got {len(rows)}")
    actual = {
        (r["storey_id"].strip(), r["support_id"].strip()): r
        for r in rows
    }
    if set(actual) != set(EXPECTED_RESIDUALS):
        raise AssertionError(f"column residual identities changed: {set(actual)}")
    for key, expected_binding in EXPECTED_RESIDUALS.items():
        row = actual[key]
        if row["current_member_binding"].strip() != expected_binding:
            raise AssertionError(f"{key}: residual binding state changed")
        if row["current_search_state"].strip() != "CURRENT_PRIMARY_SOURCE_SEARCH_CLOSED":
            raise AssertionError(f"{key}: current-source search must stay closed until new evidence")
        if not row["reopen_rule"].strip():
            raise AssertionError(f"{key}: residual must retain an explicit reopen rule")
    for key in [("G3", "9"), ("G3", "16")]:
        row = actual[key]
        if set(x for x in row["candidate_tav07_families"].split(";") if x) != {"T7-III-01", "T7-III-02"}:
            raise AssertionError(f"{key}: G3 ambiguity candidates changed")
        if row["direct_tav07_member_numbering"].strip() != "NONE":
            raise AssertionError(f"{key}: TAV-07 III-order direct numbering must remain absent")


def main() -> int:
    rc = v2.main()
    if rc != 0:
        return rc
    validate_residuals()
    print("M1A_COLUMN_RESIDUAL_REGISTER = PASS")
    print("Closed-to-current-source residuals: G1 3,a,b,c,d; G3 9,16")
    return 0


v2.source_conflicts = source_conflicts

if __name__ == "__main__":
    raise SystemExit(main())
