#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict, Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
CONNECTIVITY = C / "M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
COVERAGE = C / "M1A_BEAM_REINFORCEMENT_SOURCE_COVERAGE_CURRENT_v1.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ids(value: str) -> set[str]:
    return {x.strip() for x in (value or "").split(";") if x.strip()}


def pair_key(a: str, b: str) -> str:
    return "--".join(sorted([a.strip(), b.strip()]))


def main() -> int:
    beams = [r for r in read(CONNECTIVITY) if r["member_class"].strip() == "ORDINARY_BEAM"]
    cov = {r["storey_id"].strip(): ids(r["uncovered_source_member_ids"]) for r in read(COVERAGE)}
    uncovered = [r for r in beams if r["source_member_id"].strip() in cov.get(r["storey_id"].strip(), set())]
    if len(uncovered) != 84:
        raise AssertionError(f"uncovered inventory changed: {len(uncovered)} != 84")

    by_pair: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_section = Counter()
    for r in uncovered:
        by_pair[pair_key(r["support_i"], r["support_j"])].append(r)
        by_section[(r["storey_id"].strip(), r["section_cm"].strip())] += 1

    recurring = {k: v for k, v in by_pair.items() if len(v) >= 2}
    isolated = {k: v for k, v in by_pair.items() if len(v) == 1}

    print("M1-A BEAM GAP FAMILY AUDIT")
    print(f"uncovered_beams={len(uncovered)} unique_support_pairs={len(by_pair)} recurring_pairs={len(recurring)} isolated_pairs={len(isolated)}")
    print("SECTION_COUNTS")
    for (storey, section), count in sorted(by_section.items()):
        print(f"  {storey} {section}: {count}")
    print("RECURRING_SUPPORT_PAIRS")
    for pair, rows in sorted(recurring.items()):
        levels = ",".join(sorted(r["storey_id"].strip() for r in rows))
        members = ";".join(sorted(r["source_member_id"].strip() for r in rows))
        sections = ";".join(sorted({r["section_cm"].strip() for r in rows}))
        print(f"  {pair}: levels={levels} sections={sections} members={members}")
    print("ISOLATED_SUPPORT_PAIRS")
    for pair, rows in sorted(isolated.items()):
        r = rows[0]
        print(f"  {pair}: level={r['storey_id'].strip()} section={r['section_cm'].strip()} member={r['source_member_id'].strip()}")
    print("Interpretation: repeated geometry across storeys is only a gap-classification signal; it is not reinforcement evidence and must not be used for automatic armature transfer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
