#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
EVID = C / "M1F_FOUNDATION_ELEVATION_CONTINUITY_v1.csv"
GATE = C / "M1F_FOUNDATION_ELEVATION_GATE_v1.csv"
WORK = C / "M1F_FOUNDATION_WORK_REGISTER_v1.csv"
TOPO = C / "M1F_FOUNDATION_TOPOLOGY_CURRENT_v1.csv"
MASTER = C / "PT_MASTER_CURRENT.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for p in [EVID, GATE, WORK, TOPO, MASTER]:
        if not p.exists():
            errors.append(f"missing artifact: {p.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    evid, gate, work, topo, master = map(read, [EVID, GATE, WORK, TOPO, MASTER])
    eby = {r["evidence_id"].strip(): r for r in evid}
    gby = {r["check_id"].strip(): r for r in gate}
    wby = {r["item_id"].strip(): r for r in work}

    if len(master) != 38:
        errors.append(f"expected 38 PT/foundation support identities, got {len(master)}")
    if len(topo) != 58:
        errors.append(f"expected frozen 58-member foundation topology, got {len(topo)}")

    e1 = eby.get("M1F-ELEV-001", {})
    if e1.get("evidence_state", "").strip() != "DOC_DIRECT_SECTION":
        errors.append("main foundation common-plane evidence must remain DOC_DIRECT_SECTION")
    if "COMMON_STRUCTURAL_FOUNDATION_PLANE" not in e1.get("model_decision", ""):
        errors.append("main foundation plane decision lost")

    e2 = eby.get("M1F-ELEV-002", {})
    if "raised" not in e2.get("observed_fact", "").lower() or "separately" not in e2.get("model_decision", "").lower():
        errors.append("raised fill/floor must remain distinct from foundation elevation")

    e4 = eby.get("M1F-ELEV-004", {})
    if "1.00" not in e4.get("observed_fact", "") or e4.get("residual_state", "").strip() != "ABSOLUTE_FOUNDATION_Z_ND":
        errors.append("historical 1.00 m bearing depth must remain relative with absolute foundation Z ND")
    if "G1" not in e4.get("model_decision", ""):
        errors.append("validator requires explicit protection against using 1.00 m as G1-relative model Z")

    e5 = eby.get("M1F-ELEV-005", {})
    if "ZF_COMMON" not in e5.get("model_decision", "") or e5.get("residual_state", "").strip() != "ZF_COMMON_NUMERIC_ND":
        errors.append("38 supports must be bound symbolically to ZF_COMMON while numeric Z stays ND")

    e6 = eby.get("M1F-ELEV-006", {})
    if "Exclude" not in e6.get("model_decision", ""):
        errors.append("ancillary/peripheral lines must remain excluded from common-plane proof")

    expected_gate = {
        "M1F-ELEV-G01": "COMMON_PLANE_DOC",
        "M1F-ELEV-G02": "YES",
        "M1F-ELEV-G03": "38",
        "M1F-ELEV-G04": "1.00",
        "M1F-ELEV-G05": "NO",
        "M1F-ELEV-G06": "0",
        "M1F-ELEV-GATE": "PASS_COMMON_FOUNDATION_PLANE_WITH_NUMERIC_Z_WATCH",
    }
    for cid, expected in expected_gate.items():
        actual = gby.get(cid, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{cid}: expected {expected!r}, got {actual!r}")

    w7 = wby.get("M1F-007", {})
    if w7.get("current_status", "").strip() != "COMMON_STRUCTURAL_FOUNDATION_PLANE_CONFIRMED":
        errors.append("M1F-007 work-register status is not promoted to common structural plane confirmed")
    w9 = wby.get("M1F-009", {})
    if "SYMBOLIC_PLANE_BINDING_COMPLETE_NUMERIC_Z_OPEN" not in w9.get("current_status", ""):
        errors.append("M1F-009 must keep symbolic-plane binding complete and numeric Z open")

    forbidden_text = "ZF_COMMON=-1.00"
    combined = "\n".join(",".join(r.values()) for r in evid + work)
    if forbidden_text in combined:
        errors.append("forbidden silent conversion found: ZF_COMMON=-1.00 relative to G1")

    if gby.get("M1F-ELEV-G05", {}).get("status", "").strip() == "PASS_WITH_WATCH":
        warnings.append("common plane is closed but numeric ZF_COMMON remains ND pending G1/piano-di-campagna datum registration")

    return finish(errors, warnings, {
        "supports": len(master),
        "foundation_members": len(topo),
        "common_plane": "DOC",
        "symbolic_plane": "ZF_COMMON",
        "numeric_ZF_COMMON": "ND",
        "historical_bearing_depth_below_ground_m": "1.00",
    })


def finish(errors, warnings, summary):
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-F foundation elevation validation: {status}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
