#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"

CONNECTIVITY = C / "M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
T2 = C / "M1A_TAV02A_BEAM_GROUP_INDEX_v1.csv"
T34 = C / "M1A_TAV034A_BEAM_GROUP_INDEX_v1.csv"
T5 = C / "M1A_TAV05A_BEAM_GROUP_INDEX_v1.csv"
T6 = C / "M1A_TAV06A_ROOF_GROUP_INDEX_v1.csv"
COVERAGE = C / "M1A_BEAM_REINFORCEMENT_SOURCE_COVERAGE_CURRENT_v1.csv"
GATE = C / "M1A_BEAM_REINFORCEMENT_SOURCE_COVERAGE_GATE_v1.csv"
EXPECTED_GATE = "PASS_BEAM_REINFORCEMENT_SOURCE_COVERAGE_CLASSIFIED_WITH_84_DOCUMENTARY_GAPS"


def read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ids(value: str) -> set[str]:
    out: set[str] = set()
    for raw in (value or "").split(";"):
        token = raw.strip()
        if not token or token.startswith("MISSING_") or token.startswith("SPECIAL_"):
            continue
        out.add(token)
    return out


def main() -> int:
    required = [CONNECTIVITY, T2, T34, T5, T6, COVERAGE, GATE]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise AssertionError(f"missing source files: {missing}")

    beams = [r for r in read(CONNECTIVITY) if r["member_class"].strip() == "ORDINARY_BEAM"]
    if len(beams) != 232:
        raise AssertionError(f"frozen ordinary-beam inventory changed: {len(beams)} != 232")

    covered: dict[str, set[str]] = defaultdict(set)
    groups: dict[str, dict[str, set[str]]] = defaultdict(dict)

    for r in read(T2):
        s = ids(r["canonical_member_ids"])
        covered["G1"].update(s)
        groups["G1"][r["group_id"].strip()] = s

    for r in read(T34):
        g2 = ids(r["g2_member_ids"])
        g3 = ids(r["g3_member_ids"])
        covered["G2"].update(g2)
        covered["G3"].update(g3)
        groups["G2"][r["group_id"].strip()] = g2
        groups["G3"][r["group_id"].strip()] = g3

    for r in read(T5):
        s = ids(r["g4_member_ids"])
        covered["G4"].update(s)
        groups["G4"][r["group_id"].strip()] = s

    for r in read(T6):
        s = ids(r["canonical_member_ids"])
        covered["G5"].update(s)
        groups["G5"][r["group_id"].strip()] = s

    by_storey: dict[str, list[dict[str, str]]] = defaultdict(list)
    for b in beams:
        by_storey[b["storey_id"].strip()].append(b)

    persisted = {r["storey_id"].strip(): r for r in read(COVERAGE)}
    if set(persisted) != {"G1", "G2", "G3", "G4", "G5"}:
        raise AssertionError("persisted beam coverage storey set changed")

    total_covered = 0
    total_uncovered = 0
    print("M1-A BEAM REINFORCEMENT SOURCE-COVERAGE AUDIT")
    print(f"ordinary_beams={len(beams)}")

    for storey in ["G1", "G2", "G3", "G4", "G5"]:
        rows = by_storey.get(storey, [])
        source_ids = {r["source_member_id"].strip() for r in rows}
        cov = source_ids & covered.get(storey, set())
        uncov = sorted(source_ids - covered.get(storey, set()))
        orphan_schedule_ids = sorted(covered.get(storey, set()) - source_ids)
        if orphan_schedule_ids:
            raise AssertionError(f"{storey}: schedule IDs outside frozen ordinary-beam inventory: {orphan_schedule_ids}")

        p = persisted[storey]
        checks = {
            "ordinary_beam_count": len(rows),
            "direct_group_source_covered_count": len(cov),
            "uncovered_count": len(uncov),
        }
        for field, expected in checks.items():
            if int(p[field]) != expected:
                raise AssertionError(f"{storey}: persisted {field}={p[field]} != {expected}")
        if ids(p["uncovered_source_member_ids"]) != set(uncov):
            raise AssertionError(f"{storey}: persisted uncovered member set changed")
        if p["coverage_state"].strip() != "SOURCE_COVERAGE_CLASSIFIED_WITH_DOCUMENTARY_GAPS":
            raise AssertionError(f"{storey}: coverage state changed")

        total_covered += len(cov)
        total_uncovered += len(uncov)
        print(f"{storey}: ordinary={len(rows)} group_source_covered={len(cov)} uncovered={len(uncov)}")
        print(f"  uncovered_ids={';'.join(uncov) if uncov else 'NONE'}")
        print(
            "  group_counts=" + ";".join(
                f"{gid}:{len(member_ids & source_ids)}"
                for gid, member_ids in sorted(groups.get(storey, {}).items())
            )
        )

    if (total_covered, total_uncovered) != (148, 84):
        raise AssertionError(f"beam source-coverage totals changed: {(total_covered, total_uncovered)}")

    gate_rows = {r["check_id"].strip(): r for r in read(GATE)}
    if gate_rows.get("M1A-BRC-GATE", {}).get("actual", "").strip() != EXPECTED_GATE:
        raise AssertionError("beam coverage gate state changed")
    if gate_rows.get("M1A-BRC-G02", {}).get("actual", "").strip() != "148":
        raise AssertionError("beam covered total gate value changed")
    if gate_rows.get("M1A-BRC-G03", {}).get("actual", "").strip() != "84":
        raise AssertionError("beam uncovered total gate value changed")

    print(f"TOTAL: covered={total_covered} uncovered={total_uncovered}")
    print("M1A_BEAM_REINFORCEMENT_SOURCE_COVERAGE_GATE = PASS_WITH_WATCH")
    print("Interpretation: coverage means direct presence in an indexed source schedule; it does not imply detailed member/station projection is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
