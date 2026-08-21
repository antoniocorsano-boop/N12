#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "data" / "canonical"

CROP_REGISTER = CANON / "TAV02S_CROP_REVIEW_REGISTER_v1.csv"
OBS_REGISTER = CANON / "TAV02S_SYMBOL_OBSERVATIONS_v1.csv"
BEAM_REGISTER = CANON / "TAV02S_BEAMS_DOC_CURRENT_v1.csv"
RESIDUAL_REGISTER = CANON / "TAV02S_READING_RESIDUALS_v1.csv"

ALLOWED_OBS = {
    "DOC_DIRECT",
    "DOC_CROSS_TILE",
    "DOC_ALIGN",
    "INF_STRONG",
    "UNCERTAIN",
    "CONFLICT",
    "SUPERSEDED",
}

# PROVISIONAL_DOC is an observed/documentary candidate state. It is explicitly
# NOT equivalent to BEAM_DOC and cannot be used as a promoted canonical beam.
ALLOWED_BEAM = {
    "BEAM_DOC",
    "PROVISIONAL_DOC",
    "TO_VERIFY_BEAM",
    "CONFLICT",
    "SUPERSEDED",
}

DOCUMENTARY_BEAM_EVIDENCE = {
    "DOC_DIRECT",
    "DOC_CROSS_TILE",
    "DOC_ALIGN",
    "DOC_CONTINUITY",
    "DOC_SECTION_BOUND",
    "DOC_CONTINUITY_MIS_LENGTH",
}

CONFIRMED_CONTINUITY = {
    "YES",
    "CONFIRMED",
    "CONTINUOUS",
    "CROSS_TILE_CONFIRMED",
    "DOC_CONTINUOUS",
}

BLOCKING_SOURCE_MARKERS = {"SUPERSEDED", "CONFLICT", "REVOKED"}


def rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def status() -> int:
    crop_rows = rows(CROP_REGISTER)
    if not crop_rows:
        print("ERROR: crop register missing or empty")
        return 2

    done = [r for r in crop_rows if r.get("review_status") in {"REVIEWED", "CLOSED"}]
    pending = [r for r in crop_rows if r.get("review_status") not in {"REVIEWED", "CLOSED"}]

    print(f"crop reviewed: {len(done)}/{len(crop_rows)}")
    if pending:
        nxt = pending[0]
        print(f"next crop: {nxt.get('tile_id')}")
        print(f"raster window: ({nxt.get('u0_px')},{nxt.get('v0_px')}) -> ({nxt.get('u1_px')},{nxt.get('v1_px')})")
        print(f"cross-tile check: {nxt.get('cross_tile_check')}")
    else:
        print("next crop: NONE")

    print(f"observations: {len(rows(OBS_REGISTER))}")
    print(f"beam records: {len(rows(BEAM_REGISTER))}")
    print(f"residuals: {len(rows(RESIDUAL_REGISTER))}")
    return 0


def validate() -> int:
    errors: list[str] = []

    required = [CROP_REGISTER, OBS_REGISTER, BEAM_REGISTER, RESIDUAL_REGISTER]
    for path in required:
        if not path.exists():
            errors.append(f"missing file: {path.relative_to(ROOT)}")

    obs = rows(OBS_REGISTER)
    for i, r in enumerate(obs, start=2):
        state = (r.get("evidence_status") or "").strip()
        if state and state not in ALLOWED_OBS:
            errors.append(f"observations line {i}: invalid evidence_status={state}")

    beams = rows(BEAM_REGISTER)
    for i, r in enumerate(beams, start=2):
        status_value = (r.get("canonical_status") or "").strip()
        evidence = (r.get("evidence_status") or "").strip()
        continuity = (r.get("continuity_status") or "").strip().upper()
        node_i = (r.get("node_i") or "").strip()
        node_j = (r.get("node_j") or "").strip()
        source_primary = (r.get("source_tile_primary") or "").strip()
        source_cross = (r.get("source_tile_crosscheck") or "").strip()
        source = f"{source_primary} {source_cross}".upper()

        if status_value and status_value not in ALLOWED_BEAM:
            errors.append(f"beams line {i}: invalid canonical_status={status_value}")
            continue

        # Both documentary candidate and promoted beam records must at least be
        # traceable to endpoints, a primary source and a continuous line.
        if status_value in {"PROVISIONAL_DOC", "BEAM_DOC"}:
            if not node_i or not node_j:
                errors.append(f"beams line {i}: {status_value} without both endpoints")
            if not source_primary:
                errors.append(f"beams line {i}: {status_value} without source_tile_primary")
            if evidence not in DOCUMENTARY_BEAM_EVIDENCE:
                errors.append(f"beams line {i}: {status_value} with non-documentary evidence={evidence}")
            if continuity not in CONFIRMED_CONTINUITY:
                errors.append(f"beams line {i}: {status_value} without confirmed continuity_status={continuity}")
            if any(marker in source for marker in BLOCKING_SOURCE_MARKERS):
                errors.append(f"beams line {i}: {status_value} references blocked/superseded source")

        # BEAM_DOC is the only promoted state. PROVISIONAL_DOC remains a
        # candidate and must pass the separate cross-validation gate before
        # any downstream canonical geometry consumes it.
        if status_value == "BEAM_DOC" and not source_cross:
            errors.append(f"beams line {i}: BEAM_DOC requires independent/cross-tile evidence")

    crop_rows = rows(CROP_REGISTER)
    ids = [r.get("tile_id") for r in crop_rows]
    if len(ids) != len(set(ids)):
        errors.append("crop register contains duplicate tile_id values")
    if crop_rows and len(crop_rows) != 12:
        errors.append(f"expected 12 TAV-02S crops, found {len(crop_rows)}")

    if errors:
        print("VALIDATION: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    provisional = sum(1 for r in beams if (r.get("canonical_status") or "").strip() == "PROVISIONAL_DOC")
    promoted = sum(1 for r in beams if (r.get("canonical_status") or "").strip() == "BEAM_DOC")
    print("VALIDATION: PASS")
    print(
        f"crops={len(crop_rows)} observations={len(obs)} beams={len(beams)} "
        f"provisional={provisional} beam_doc={promoted} residuals={len(rows(RESIDUAL_REGISTER))}"
    )
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"status", "validate"}:
        print("usage: python skills/pt-carpentry-reader/runner.py {status|validate}")
        return 2
    return status() if sys.argv[1] == "status" else validate()


if __name__ == "__main__":
    raise SystemExit(main())
