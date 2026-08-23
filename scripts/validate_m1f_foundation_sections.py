#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"

TOPOLOGY = C / "M1F_FOUNDATION_TOPOLOGY_CURRENT_v1.csv"
CATALOG = C / "M1F_FOUNDATION_SECTION_CATALOG_CURRENT_v1.csv"
TRANSITIONS = C / "M1F_FOUNDATION_SECTION_TRANSITIONS_TAV01A_v1.csv"
PATCH = C / "M1F_FOUNDATION_SECTION_BINDING_PATCH_v1.csv"
SOURCE_AUDIT = C / "M1F_FOUNDATION_SOURCE_ROLE_AUDIT_v1.csv"
GATE = C / "M1F_FOUNDATION_SECTION_BINDING_GATE_v1.csv"

EXPECTED_GEOMETRY = {
    "FND-SEC-A": {
        "rib_top_width_cm": "45",
        "rib_bottom_width_cm": "90",
        "rib_height_cm": "90",
        "base_width_cm": "120",
        "base_thickness_cm": "20",
        "overall_depth_cm": "110",
        "stirrup_diameter_mm": "10",
        "stirrup_spacing_cm": "15",
    },
    "FND-SEC-B": {
        "rib_top_width_cm": "35",
        "rib_bottom_width_cm": "70",
        "rib_height_cm": "70",
        "base_width_cm": "100",
        "base_thickness_cm": "20",
        "overall_depth_cm": "90",
        "stirrup_diameter_mm": "10",
        "stirrup_spacing_cm": "15",
    },
}


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for path in [TOPOLOGY, CATALOG, TRANSITIONS, PATCH, SOURCE_AUDIT, GATE]:
        if not path.exists():
            fail(errors, f"missing required M1-F section artifact: {path.relative_to(ROOT)}")
    if errors:
        return report(errors, warnings, {})

    topology = rows(TOPOLOGY)
    catalog = rows(CATALOG)
    transitions = rows(TRANSITIONS)
    patch = rows(PATCH)
    source_audit = rows(SOURCE_AUDIT)
    gate = rows(GATE)

    # 1. Frozen M1-F foundation topology contract.
    if len(topology) != 58:
        fail(errors, f"foundation topology must contain 58 members, got {len(topology)}")
    by_member = {r["foundation_member_id"].strip(): r for r in topology}
    if len(by_member) != len(topology):
        fail(errors, "duplicate foundation_member_id in topology")

    # 2. Documentary section-family geometry.
    by_family = {r["section_family_id"].strip(): r for r in catalog}
    if set(by_family) != set(EXPECTED_GEOMETRY):
        fail(errors, f"section catalog families mismatch: {sorted(by_family)}")
    for family, expected in EXPECTED_GEOMETRY.items():
        row = by_family.get(family, {})
        for key, value in expected.items():
            if row.get(key, "").strip() != value:
                fail(errors, f"{family}: {key} expected {value}, got {row.get(key)!r}")
        if row.get("evidence_status", "").strip() != "DOC_PRIMARY_VISUAL_READ":
            fail(errors, f"{family}: evidence_status must remain DOC_PRIMARY_VISUAL_READ")

    # 3. Two explicit section transitions, no inferred station.
    transition_ids = {r["transition_id"].strip() for r in transitions}
    if transition_ids != {"M1F-SEC-TR01", "M1F-SEC-TR02"}:
        fail(errors, f"unexpected section transition set: {sorted(transition_ids)}")
    tr_by_id = {r["transition_id"].strip(): r for r in transitions}
    if tr_by_id.get("M1F-SEC-TR01", {}).get("transition_supports", "").strip() != "17|18":
        fail(errors, "TR01 must remain located at stacked supports 17|18")
    if tr_by_id.get("M1F-SEC-TR02", {}).get("transition_supports", "").strip() != "25|28|31":
        fail(errors, "TR02 must remain located at stacked supports 25|28|31")

    # 4. Apply the explicit 10-row patch only when its previous state still matches topology.
    if len(patch) != 10:
        fail(errors, f"section binding patch must contain 10 promotions, got {len(patch)}")
    patched_ids: set[str] = set()
    effective_state = {mid: r["section_family_state"].strip() for mid, r in by_member.items()}
    for p in patch:
        mid = p["foundation_member_id"].strip()
        if mid in patched_ids:
            fail(errors, f"duplicate section patch target {mid}")
            continue
        patched_ids.add(mid)
        if mid not in by_member:
            fail(errors, f"section patch references unknown member {mid}")
            continue
        previous = p["previous_section_family_state"].strip()
        if effective_state[mid] != previous:
            fail(errors, f"{mid}: patch previous state {previous!r} != topology {effective_state[mid]!r}")
        new = p["new_section_family_state"].strip()
        if new not in EXPECTED_GEOMETRY:
            fail(errors, f"{mid}: patched section family {new!r} is not in catalog")
        if p.get("evidence_status", "").strip() != "DOC_PRIMARY_VISUAL_READ":
            fail(errors, f"{mid}: patch must remain documentary visual-read evidence")
        effective_state[mid] = new

    exact = sum(1 for state in effective_state.values() if state in EXPECTED_GEOMETRY)
    supported = sum(1 for state in effective_state.values() if state == "FND-SEC-A_SUPPORTED")
    documentary_nd = sum(1 for state in effective_state.values() if state == "ND_DOCUMENTARY_COVERAGE")
    open_binding = sum(1 for state in effective_state.values() if state == "OPEN_SECTION_BINDING")
    residual_watch = [
        (mid, state)
        for mid, state in effective_state.items()
        if "TO_VERIFY" in state or "TRANSITION_WATCH" in state
    ]

    if exact != 42:
        fail(errors, f"effective exact section-family count must be 42, got {exact}")
    if supported != 1:
        fail(errors, f"supported exact section-family count must be 1, got {supported}")
    if documentary_nd != 15:
        fail(errors, f"ND documentary-coverage section count must be 15, got {documentary_nd}")
    if open_binding != 0:
        fail(errors, f"open section-binding count must be zero after source-role audit, got {open_binding}")
    if residual_watch:
        fail(errors, f"section extent/transition watches must be zero after patch: {residual_watch}")
    if exact + supported + documentary_nd != 58:
        fail(errors, "effective section-state partition does not cover all 58 members")

    # 5. Registered Tavola 1 source roles must demonstrate that the 15 ND rows are
    # documentary coverage gaps, not unresolved source-search tasks.
    source_rows = {r["source_file"].strip(): r for r in source_audit if r["source_file"].strip() != "AUDIT-SUMMARY"}
    expected_roles = {
        "tavola1.pdf": ("ARCHITECTURAL_SOURCE", "NO"),
        "tavola1-2.pdf": ("FOUNDATION_CARPENTRY", "NO"),
        "tavola1-3.pdf": ("FOUNDATION_REINFORCEMENT", "YES"),
    }
    if set(source_rows) != set(expected_roles):
        fail(errors, f"Tavola 1 source-role audit mismatch: {sorted(source_rows)}")
    for source_file, (role, provides_reinf) in expected_roles.items():
        row = source_rows.get(source_file, {})
        if row.get("canonical_role", "").strip() != role:
            fail(errors, f"{source_file}: canonical_role must be {role}")
        if row.get("provides_foundation_reinforcement", "").strip() != provides_reinf:
            fail(errors, f"{source_file}: reinforcement-source flag must be {provides_reinf}")
    summary_rows = [r for r in source_audit if r["source_file"].strip() == "AUDIT-SUMMARY"]
    if len(summary_rows) != 1:
        fail(errors, "source-role audit must contain exactly one AUDIT-SUMMARY row")
    else:
        s = summary_rows[0]
        if s.get("canonical_role", "").strip() != "REGISTERED_SECOND_INDEPENDENT_FOUNDATION_REINFORCEMENT_SOURCE":
            fail(errors, "source-role audit summary role mismatch")
        if s.get("provides_foundation_reinforcement", "").strip() != "NO":
            fail(errors, "source-role audit must confirm no second independent reinforcement source")
        if s.get("audit_state", "").strip() != "CLOSED_NO_SECOND_SOURCE":
            fail(errors, "source-role audit must be CLOSED_NO_SECOND_SOURCE")

    # 6. Gate must advertise the same post-audit contract.
    gate_by_id = {r["check_id"].strip(): r for r in gate}
    expected_gate_actuals = {
        "M1F-SEC-005": "58",
        "M1F-SEC-006": "42",
        "M1F-SEC-007": "1",
        "M1F-SEC-008": "0",
        "M1F-SEC-009": "15",
        "M1F-SEC-010": "0",
        "M1F-SEC-GATE": "PASS_SECTION_FAMILY_BINDING_WITH_15_DOCUMENTARY_GAPS",
    }
    for check_id, expected_actual in expected_gate_actuals.items():
        actual = gate_by_id.get(check_id, {}).get("actual", "").strip()
        if actual != expected_actual:
            fail(errors, f"{check_id}: gate actual expected {expected_actual!r}, got {actual!r}")

    summary = {
        "foundation_members": len(topology),
        "documented_section_families": len(catalog),
        "documented_transitions": len(transitions),
        "section_promotions": len(patch),
        "exact_section_members": exact,
        "supported_section_members": supported,
        "nd_documentary_coverage_members": documentary_nd,
        "open_section_members": open_binding,
        "transition_watch_members": len(residual_watch),
    }
    return report(errors, warnings, summary)


def report(errors: list[str], warnings: list[str], summary: dict) -> int:
    state = "PASS" if not errors else "FAIL"
    print(f"M1F_FOUNDATION_SECTION_VALIDATION={state}")
    for key, value in summary.items():
        print(f"{key}={value}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
