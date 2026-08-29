#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data/canonical/PT_RASTER_SUPPORT_BINDINGS_WORKING_v1.csv"
REGISTRATION = ROOT / "data/canonical/TAV02S_TILE_TO_NATIVE_REGISTRATION_v1.csv"

REQUIRED = {
    "binding_id","tile_id","support_id","candidate_or_union",
    "u_local_px","v_local_px","bbox_x","bbox_y","bbox_w","bbox_h",
    "u_native_px","v_native_px","binding_state","evidence_class","source_registration",
    "crosscheck_tile","crosscheck_delta_px","may_promote_to_pixel_registry","note"
}

ALLOWED_STATES = {
    "CONFIRMED_VISUAL",
    "CONFIRMED_VISUAL_REBOUND",
    "CONFIRMED_VISUAL_EXTENDED",
    "DIRECT_REGISTERED",
    "DIRECT_REGISTERED_EXTENDED",
    "CROSS_VALIDATED",
    "CROSS_VALIDATED_EXTENDED",
    "CANDIDATE",
    "REJECTED_SYMBOL",
    "UNRESOLVED",
    "CONFLICT",
}
PROMOTABLE = {
    "DIRECT_REGISTERED",
    "DIRECT_REGISTERED_EXTENDED",
    "CROSS_VALIDATED",
    "CROSS_VALIDATED_EXTENDED",
}
CONFIRMED = {
    "CONFIRMED_VISUAL",
    "CONFIRMED_VISUAL_REBOUND",
    "CONFIRMED_VISUAL_EXTENDED",
    "DIRECT_REGISTERED",
    "DIRECT_REGISTERED_EXTENDED",
    "CROSS_VALIDATED",
    "CROSS_VALIDATED_EXTENDED",
}


def load_registration_states() -> dict[str, str]:
    if not REGISTRATION.exists():
        return {}
    with REGISTRATION.open("r", encoding="utf-8-sig", newline="") as fh:
        return {
            (r.get("tile_id") or "").strip(): (r.get("registration_status") or "").strip()
            for r in csv.DictReader(fh)
        }


def main() -> int:
    errors: list[str] = []
    if not LEDGER.exists():
        print("PT_RASTER_SUPPORT_BINDINGS_VALIDATION = OPEN")
        print("ledger missing")
        return 0
    if not REGISTRATION.exists():
        errors.append("missing tile-to-native registration")

    registration_states = load_registration_states()

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
    cross_validated = 0
    direct_registered = 0
    confirmed_visual = 0
    extended = 0

    for i, row in enumerate(rows, start=2):
        bid = (row.get("binding_id") or "").strip()
        state = (row.get("binding_state") or "").strip()
        promote = (row.get("may_promote_to_pixel_registry") or "").strip().upper()
        tile = (row.get("tile_id") or "").strip()
        candidate = (row.get("candidate_or_union") or "").strip()
        support = (row.get("support_id") or "").strip()
        source_registration = (row.get("source_registration") or "").strip()

        if not bid:
            errors.append(f"line {i}: missing binding_id")
        elif bid in binding_ids:
            errors.append(f"line {i}: duplicate binding_id={bid}")
        binding_ids.add(bid)

        if state not in ALLOWED_STATES:
            errors.append(f"line {i}: invalid binding_state={state}")

        if promote == "YES" and state not in PROMOTABLE:
            errors.append(f"line {i}: only G1 class A/B states may be marked YES, got {state}")

        if state in CONFIRMED:
            if not support or not candidate or not tile:
                errors.append(f"line {i}: confirmed binding missing support/candidate/tile")
            if not source_registration:
                errors.append(f"line {i}: confirmed binding missing source_registration")
            for part in [p.strip() for p in candidate.split("+") if p.strip()]:
                key = (tile, part)
                if key in candidate_keys:
                    errors.append(f"line {i}: candidate fragment bound more than once in same tile: {key}")
                candidate_keys.add(key)
            for field in ("u_local_px","v_local_px","u_native_px","v_native_px","bbox_x","bbox_y","bbox_w","bbox_h"):
                try:
                    float(row.get(field, ""))
                except (ValueError, TypeError):
                    errors.append(f"line {i}: invalid numeric field {field}={row.get(field)}")

        if state.startswith("CROSS_VALIDATED"):
            cross_validated += 1
            if not (row.get("crosscheck_tile") or "").strip():
                errors.append(f"line {i}: {state} without crosscheck_tile")
            try:
                float(row.get("crosscheck_delta_px", ""))
            except (ValueError, TypeError):
                errors.append(f"line {i}: {state} without numeric crosscheck_delta_px")

        if state.startswith("DIRECT_REGISTERED"):
            direct_registered += 1
            if registration_states.get(tile) != "DIRECT_SIFT_RANSAC":
                errors.append(
                    f"line {i}: {state} requires tile with DIRECT_SIFT_RANSAC registration, "
                    f"got {registration_states.get(tile) or 'UNKNOWN'} for {tile}"
                )
            if (row.get("crosscheck_tile") or "").strip():
                errors.append(f"line {i}: {state} should not masquerade as cross-tile validation")

        if state.startswith("CONFIRMED_VISUAL"):
            confirmed_visual += 1

        if state.endswith("EXTENDED"):
            extended += 1

    if errors:
        print("PT_RASTER_SUPPORT_BINDINGS_VALIDATION = FAIL")
        for err in errors:
            print("-", err)
        return 1

    print("PT_RASTER_SUPPORT_BINDINGS_VALIDATION = PASS")
    print(
        f"rows={len(rows)} cross_validated={cross_validated} "
        f"direct_registered={direct_registered} confirmed_visual={confirmed_visual} extended={extended}"
    )
    print("G1 Class A CROSS_VALIDATED and Class B DIRECT_REGISTERED may enter the pixel registry; metric validation remains in G2-G4.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
