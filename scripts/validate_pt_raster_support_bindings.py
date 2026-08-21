#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data/canonical/PT_RASTER_SUPPORT_BINDINGS_WORKING_v1.csv"

REQUIRED = {
    "binding_id","tile_id","support_id","candidate_id",
    "u_local_px","v_local_px","u_global_px","v_global_px",
    "bbox_x","bbox_y","bbox_w","bbox_h",
    "binding_state","evidence_class","source_observation",
    "visual_discriminator","may_promote_to_pixel_registry","note"
}
ALLOWED_STATES = {"CONFIRMED_VISUAL","CROSS_VALIDATED","CANDIDATE","REJECTED_SYMBOL","UNRESOLVED","CONFLICT"}
PROMOTABLE = {"CONFIRMED_VISUAL","CROSS_VALIDATED"}


def main() -> int:
    errors: list[str] = []
    if not LEDGER.exists():
        print("PT_RASTER_SUPPORT_BINDINGS_VALIDATION = OPEN")
        print("ledger missing")
        return 0

    with LEDGER.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        errors.append("ledger empty")
    else:
        missing = REQUIRED - set(rows[0].keys())
        if missing:
            errors.append("missing columns: " + ",".join(sorted(missing)))

    binding_ids: set[str] = set()
    candidate_keys: set[tuple[str,str]] = set()
    confirmed = 0

    for i, row in enumerate(rows, start=2):
        bid = (row.get("binding_id") or "").strip()
        state = (row.get("binding_state") or "").strip()
        promote = (row.get("may_promote_to_pixel_registry") or "").strip().upper()
        tile = (row.get("tile_id") or "").strip()
        candidate = (row.get("candidate_id") or "").strip()
        support = (row.get("support_id") or "").strip()

        if not bid:
            errors.append(f"line {i}: missing binding_id")
        elif bid in binding_ids:
            errors.append(f"line {i}: duplicate binding_id={bid}")
        binding_ids.add(bid)

        if state not in ALLOWED_STATES:
            errors.append(f"line {i}: invalid binding_state={state}")

        if promote == "YES" and state not in PROMOTABLE:
            errors.append(f"line {i}: non-promotable state marked YES: {state}")

        if state in PROMOTABLE:
            confirmed += 1
            if not support or not candidate or not tile:
                errors.append(f"line {i}: confirmed binding missing support/candidate/tile")
            key = (tile, candidate)
            if key in candidate_keys:
                errors.append(f"line {i}: candidate bound more than once in same tile: {key}")
            candidate_keys.add(key)
            for field in ("u_local_px","v_local_px","u_global_px","v_global_px","bbox_x","bbox_y","bbox_w","bbox_h"):
                try:
                    float(row.get(field, ""))
                except ValueError:
                    errors.append(f"line {i}: invalid numeric field {field}={row.get(field)}")

    if errors:
        print("PT_RASTER_SUPPORT_BINDINGS_VALIDATION = FAIL")
        for err in errors:
            print("-", err)
        return 1

    print("PT_RASTER_SUPPORT_BINDINGS_VALIDATION = PASS")
    print(f"rows={len(rows)} confirmed_or_cross_validated={confirmed}")
    print("Pixel registry promotion remains a separate semantic gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
