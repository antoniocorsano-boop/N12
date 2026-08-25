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
        raise AssertionError("ERW initial source set changed")

    allowed_states = {
        "BLOCKED_SOURCE_ASSET_BINDING",
        "READY_FOR_DEEP_ZOOM",
        "READY_FOR_F3_VIEWER_BUILD",
        "F3_VIEWER_BUILD_PROVEN",
    }
    blocked_tokens = {"", "ND", "NOT_PERSISTED_IN_ERW", "NOT_BUILT", "NOT_REGISTERED"}

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
        if state not in allowed_states:
            raise AssertionError(f"{source}: unexpected ERW source state {state}")

        if state != "BLOCKED_SOURCE_ASSET_BINDING":
            required = [
                row["erw_primary_source_path"].strip(),
                row["erw_source_hash_binding"].strip(),
                row["viewer_asset_state"].strip(),
                row["tile_pyramid_state"].strip(),
                row["native_pixel_registration"].strip(),
            ]
            if any(v in blocked_tokens for v in required):
                raise AssertionError(f"{source}: {state} without reproducible source/navigation chain")
            if row["native_pixel_registration"].strip() != "NORMALIZED_0_1_REGION_READY":
                raise AssertionError(f"{source}: F2 region registration is not READY")

        if state == "READY_FOR_F3_VIEWER_BUILD":
            if row["tile_pyramid_state"].strip() != "REPRODUCIBLE_BUILD_DEFINED":
                raise AssertionError(f"{source}: F3 build-ready state requires deterministic pyramid build definition")
            if row["viewer_asset_state"].strip() != "REPRODUCIBLE_TECHNICAL_RENDER_READY":
                raise AssertionError(f"{source}: F3 build-ready state requires reproducible technical render")

        if state == "F3_VIEWER_BUILD_PROVEN":
            if row["tile_pyramid_state"].strip() != "DZI_BUILD_PROVEN_REPRODUCIBLE":
                raise AssertionError(f"{source}: proven F3 state requires proven DZI build")
            if row["viewer_asset_state"].strip() != "SELF_CONTAINED_VIEWER_BUILD_PROVEN":
                raise AssertionError(f"{source}: proven F3 state requires proven viewer build")

    print("CEW ERW SOURCE READINESS = PASS")
    for row in sources:
        print(f"{row['source_id']}: {row['current_state']}")
    print("Interpretation: source identity, evidence regions and viewer-build readiness are tracked as progressive states; primary PDFs remain authority throughout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
