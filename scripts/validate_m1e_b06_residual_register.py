#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
REGISTER = C / "M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_RESIDUAL_REGISTER_v1.csv"
GATE = C / "M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_GATE_v1.csv"
HANDOFF = C / "M1E_CALCULATION_MODEL_HANDOFF_v1.json"

EXPECTED_IDS = {
    "B06-COL-G1-003",
    "B06-COL-G1-A",
    "B06-COL-G1-B",
    "B06-COL-G1-C",
    "B06-COL-G1-D",
    "B06-COL-G3-009",
    "B06-COL-G3-016",
    "B06-T5-G01-R06",
    "B06-T5-G07-R07",
    "B06-T5-G05-R04",
    "B06-STAIR-G23-20-21",
    "B06-STAIR-G4-20-21",
    "B06-TORRINO-COLUMNS",
    "B06-G5-B017",
    "B06-G5-PER-001",
    "B06-G5-PER-002",
    "B06-G5-PER-003",
    "B06-G5-B036-DIAGONALS",
    "B06-G4-CORNICIONE",
    "B06-BALCONY-SLABS",
    "B06-G1-E03",
}

LANE_EXISTING = "EXISTING_GOVERNED_SOURCE_TARGETED"
LANE_NEW = "NEW_EVIDENCE_OR_SCOPE_EXCLUSION"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def finish(errors: list[str], warnings: list[str], summary: dict[str, object]) -> int:
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1E-B06 residual-register validation: {status}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in [REGISTER, GATE, HANDOFF]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    rows = read(REGISTER)
    gate = read(GATE)
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))

    required = {
        "residual_id", "scope_type", "object_ids", "source_authority", "evidence_state",
        "current_state", "resolution_lane", "verification_effect", "closure_class", "closure_action",
        "forbidden_inference", "canonical_evidence",
    }
    if rows and not required.issubset(rows[0].keys()):
        errors.append(f"register missing columns: {sorted(required - set(rows[0].keys()))}")

    ids = [r.get("residual_id", "").strip() for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate residual_id in B06 register")
    if set(ids) != EXPECTED_IDS:
        errors.append(
            "B06 residual identity set changed without gate update: "
            f"missing={sorted(EXPECTED_IDS - set(ids))}, extra={sorted(set(ids) - EXPECTED_IDS)}"
        )

    for r in rows:
        rid = r.get("residual_id", "").strip() or "<missing-id>"
        for field in [
            "scope_type", "object_ids", "source_authority", "evidence_state", "current_state",
            "resolution_lane", "verification_effect", "closure_class", "closure_action", "forbidden_inference",
            "canonical_evidence",
        ]:
            if not r.get(field, "").strip():
                errors.append(f"{rid}: empty {field}")

        if r.get("resolution_lane", "") not in {LANE_EXISTING, LANE_NEW}:
            errors.append(f"{rid}: invalid resolution_lane={r.get('resolution_lane', '')!r}")
        if "OR_SCOPE_EXCLUSION" not in r.get("closure_class", ""):
            errors.append(f"{rid}: closure_class must preserve explicit scope-exclusion path")
        if not r.get("current_state", "").startswith("OPEN_"):
            errors.append(f"{rid}: current_state must remain OPEN_* until an evidence-backed closure is committed")

        for rel in [p.strip() for p in r.get("canonical_evidence", "").split(";") if p.strip()]:
            if not (ROOT / rel).exists():
                errors.append(f"{rid}: canonical evidence path does not exist: {rel}")

    scope_counts = {
        "columns": sum(1 for r in rows if r["residual_id"].startswith("B06-COL-")),
        "g4_bar_details": sum(1 for r in rows if r["residual_id"].startswith("B06-T5-")),
        "stair_torrino": sum(1 for r in rows if r["residual_id"].startswith("B06-STAIR-") or r["residual_id"] == "B06-TORRINO-COLUMNS"),
        "g5_roof_perimeter": sum(1 for r in rows if r["residual_id"].startswith("B06-G5-")),
        "slab_additions": sum(1 for r in rows if r["residual_id"] in {"B06-G4-CORNICIONE", "B06-BALCONY-SLABS", "B06-G1-E03"}),
        "existing_source_targeted": sum(1 for r in rows if r.get("resolution_lane") == LANE_EXISTING),
        "new_evidence_or_scope_exclusion": sum(1 for r in rows if r.get("resolution_lane") == LANE_NEW),
        "g5_eave_end_reinforcement_residuals": sum(1 for r in rows if "EAV" in r["residual_id"] or "EAVE" in r["residual_id"]),
    }
    expected_counts = {
        "columns": 7,
        "g4_bar_details": 3,
        "stair_torrino": 3,
        "g5_roof_perimeter": 5,
        "slab_additions": 3,
        "existing_source_targeted": 11,
        "new_evidence_or_scope_exclusion": 10,
        "g5_eave_end_reinforcement_residuals": 0,
    }
    for name, expected in expected_counts.items():
        if scope_counts[name] != expected:
            errors.append(f"{name}: expected {expected}, got {scope_counts[name]}")

    gg = {r.get("gate_id", "").strip(): r for r in gate}
    expected_gate = {
        "M1E-B06-G01": "21",
        "M1E-B06-G02": "7",
        "M1E-B06-G03": "3",
        "M1E-B06-G04": "3",
        "M1E-B06-G05": "5",
        "M1E-B06-G06": "3",
        "M1E-B06-G07": "YES",
        "M1E-B06-G08": "YES",
        "M1E-B06-G09": "NO",
        "M1E-B06-G10": "11",
        "M1E-B06-G11": "10",
        "M1E-B06-G12": "0",
        "M1E-B06-GATE": "RESIDUAL_SCOPE_BOUND_21_OPEN",
    }
    for gid, expected in expected_gate.items():
        observed = gg.get(gid, {}).get("observed", "").strip()
        if observed != expected:
            errors.append(f"{gid}: expected observed={expected!r}, got {observed!r}")

    forbidden_text = " ".join(r.get("forbidden_inference", "") for r in rows).lower()
    for concept in ["analogy", "symmetry"]:
        if concept not in forbidden_text:
            errors.append(f"B06 guard text no longer contains explicit {concept} prohibition")

    authoritative = handoff.get("authoritative_inputs", {})
    if authoritative.get("reinforcement_residual_register") != "data/canonical/M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_RESIDUAL_REGISTER_v1.csv":
        errors.append("M1E handoff must reference the canonical B06 residual register")
    if authoritative.get("reinforcement_residual_gate") != "data/canonical/M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_GATE_v1.csv":
        errors.append("M1E handoff must reference the canonical B06 residual gate")
    b06 = next((b for b in handoff.get("blocking_domains", []) if b.get("id") == "M1E-B06"), None)
    if not b06:
        errors.append("M1E handoff is missing blocking domain M1E-B06")
    else:
        if b06.get("blocking") is not True:
            errors.append("M1E-B06 must remain blocking until evidence-backed closure")
        if b06.get("state") != "RESIDUAL_SCOPE_BOUND_21_OPEN":
            errors.append(f"M1E-B06 handoff state drifted: {b06.get('state')!r}")
        if b06.get("residual_register") != "data/canonical/M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_RESIDUAL_REGISTER_v1.csv":
            errors.append("M1E-B06 handoff residual_register mismatch")
        if b06.get("residual_gate") != "data/canonical/M1E_B06_SUPERSTRUCTURE_REINFORCEMENT_GATE_v1.csv":
            errors.append("M1E-B06 handoff residual_gate mismatch")
    if handoff.get("calculation_model_ready") is not False:
        errors.append("M1E handoff must keep calculation_model_ready=false while B06 is open")
    if handoff.get("status") != "RESIDUAL_NOT_CALCULATION_MODEL_READY":
        errors.append("M1E handoff status must remain RESIDUAL_NOT_CALCULATION_MODEL_READY while B06 is open")

    warnings.append(
        "M1E-B06 remains open by design: process the 11 existing-source-targeted residuals only; the other 10 require new evidence or explicit scope exclusion."
    )

    return finish(errors, warnings, {
        "residual_rows": len(rows),
        **scope_counts,
        "b06_closed": "NO",
        "calculation_model_ready": "NO",
    })


if __name__ == "__main__":
    sys.exit(main())
