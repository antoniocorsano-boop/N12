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
    required = [CONNECTIVITY, T2, T34, T5, T6]
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
        total_covered += len(cov)
        total_uncovered += len(uncov)
        print(
            f"{storey}: ordinary={len(rows)} group_source_covered={len(cov)} "
            f"uncovered={len(uncov)} schedule_ids_not_in_frozen_beams={len(orphan_schedule_ids)}"
        )
        print(f"  uncovered_ids={';'.join(uncov) if uncov else 'NONE'}")
        if orphan_schedule_ids:
            print(f"  schedule_ids_not_in_frozen_beams={';'.join(orphan_schedule_ids)}")
        print(
            "  group_counts=" + ";".join(
                f"{gid}:{len(member_ids & source_ids)}"
                for gid, member_ids in sorted(groups.get(storey, {}).items())
            )
        )

    print(f"TOTAL: covered={total_covered} uncovered={total_uncovered}")
    print("Interpretation: coverage means a member ID is present in a directly indexed source schedule; it does not by itself imply bar-by-bar member/station projection is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
