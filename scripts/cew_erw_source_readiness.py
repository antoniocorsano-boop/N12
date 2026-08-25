#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "data" / "canonical" / "CEW_ERW_SOURCE_ASSET_STATUS_v1.csv"
TASKS = ROOT / "data" / "canonical" / "CEW_ERW_RESOLUTION_TASKS_v1.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def ids(value: str) -> set[str]:
    return {x.strip() for x in (value or "").split(";") if x.strip()}


def main() -> int:
    sources = read(STATUS)
    tasks = {r["task_id"].strip(): r for r in read(TASKS)}
    if {r["source_id"].strip() for r in sources} != {"TAV-05A", "TAV-06A"}:
        raise AssertionError("ERW-0 initial source set changed")

    for row in sources:
        source = row["source_id"].strip()
        linked = ids(row["linked_task_ids"])
        if not linked:
            raise AssertionError(f"{source}: no linked ERW task")
        missing = sorted(linked - set(tasks))
        if missing:
            raise AssertionError(f"{source}: unknown task ids {missing}")
        for task_id in linked:
            if tasks[task_id]["source_id"].strip() != source:
                raise AssertionError(f"{source}: task {task_id} source mismatch")

        state = row["current_state"].strip()
        if state == "READY_FOR_DEEP_ZOOM":
            required = [
                row["erw_primary_source_path"].strip(),
                row["erw_source_hash_binding"].strip(),
                row["viewer_asset_state"].strip(),
                row["tile_pyramid_state"].strip(),
                row["native_pixel_registration"].strip(),
            ]
            if any(v in {"", "ND", "NOT_PERSISTED_IN_ERW", "NOT_BUILT", "NOT_REGISTERED"} for v in required):
                raise AssertionError(f"{source}: READY_FOR_DEEP_ZOOM without reproducible source/navigation chain")
        elif state != "BLOCKED_SOURCE_ASSET_BINDING":
            raise AssertionError(f"{source}: unexpected ERW-0 state {state}")

    print("CEW ERW SOURCE READINESS = PASS_WITH_WATCH")
    for row in sources:
        print(f"{row['source_id']}: {row['current_state']}")
    print("Interpretation: semantic task locators exist; primary source/path/hash/native-pixel viewer chain must be made reproducible before deep-zoom adjudication is declared ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
