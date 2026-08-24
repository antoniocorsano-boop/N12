#!/usr/bin/env python3
from __future__ import annotations

# v3 keeps the full v2 gate and replaces only the source-conflict predicate.
# Reason: in the same order, 40x45 and 45x40 are not interchangeable when
# both exact-orientation families exist.  A numeric callout to the wrong one
# must remain a documentary conflict even though the unordered dimensions
# have the same section key.

import validate_m1a_column_carpentry_first_binding_v2 as v2


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

        # Always conflicting when the physical section dimensions differ.
        if not same_unordered_section:
            result.add(fam["family_id"])
            continue

        # If an exact-orientation family exists in the same order, a support
        # number written against the rotated alternative conflicts with the
        # carpenteria orientation.  This is the G2 support-32 case.
        if exact_orientation_family_exists and not same_exact_orientation:
            result.add(fam["family_id"])

    return result


v2.source_conflicts = source_conflicts

if __name__ == "__main__":
    raise SystemExit(v2.main())
