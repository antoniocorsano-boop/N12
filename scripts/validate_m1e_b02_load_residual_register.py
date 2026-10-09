#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
SOURCE = C / "M1L_LOAD_MODEL_CURRENT_v1.csv"
REGISTER = C / "M1E_B02_LOAD_RESIDUAL_REGISTER_v1.csv"
GATE = C / "M1E_B02_LOAD_GATE_v1.csv"
HANDOFF = C / "M1E_CALCULATION_MODEL_HANDOFF_v1.json"

EXPECTED_IDS = {f"M1L-LM-{i:03d}" for i in range(1, 17)}
ALLOWED_PROVENANCE = {"DOC", "RIF", "ND"}
ALLOWED_LANES = {
    "EXISTING_PRIMARY_SOURCE_RECOVERY",
    "EXPLICIT_MODEL_PARAMETER_OR_EVIDENCE",
    "USE_CLASSIFICATION_AND_ADOPTED_ASSESSMENT_RULE",
    "EVIDENCE_BINDING_OR_SCOPE_EXCLUSION",
    "DEPENDENT_DOWNSTREAM_AFTER_UPSTREAM_CLOSURE",
}


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def finish(errors: list[str], warnings: list[str], summary: dict[str, object]) -> int:
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1E-B02 load-residual validation: {status}")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in [SOURCE, REGISTER, GATE, HANDOFF]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    source = read(SOURCE)
    rows = read(REGISTER)
    gate = read(GATE)

    source_by = {r.get("load_id", "").strip(): r for r in source}
    if set(source_by) != EXPECTED_IDS:
        errors.append(
            "M1-L source identity set changed: "
            f"missing={sorted(EXPECTED_IDS - set(source_by))}, extra={sorted(set(source_by) - EXPECTED_IDS)}"
        )

    required = {
        "residual_id", "load_id", "model_view", "domain", "provenance", "numeric_status",
        "current_model_status", "source_residual", "resolution_lane", "closure_class",
        "closure_action", "forbidden_inference", "canonical_source",
    }
    if rows and not required.issubset(rows[0].keys()):
        errors.append(f"register missing columns: {sorted(required - set(rows[0].keys()))}")

    ids = [r.get("load_id", "").strip() for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate load_id in B02 register")
    if set(ids) != EXPECTED_IDS:
        errors.append(
            "B02 load identity set changed without gate update: "
            f"missing={sorted(EXPECTED_IDS - set(ids))}, extra={sorted(set(ids) - EXPECTED_IDS)}"
        )

    for r in rows:
        lid = r.get("load_id", "").strip() or "<missing-id>"
        rid = r.get("residual_id", "").strip()
        if rid != f"B02-{lid}":
            errors.append(f"{lid}: residual_id must be B02-{lid}, got {rid!r}")
        for field in required - {"residual_id", "load_id"}:
            if not r.get(field, "").strip():
                errors.append(f"{lid}: empty {field}")

        src = source_by.get(lid, {})
        for field in ["model_view", "domain", "provenance", "numeric_status", "current_model_status"]:
            if r.get(field, "").strip() != src.get(field, "").strip():
                errors.append(f"{lid}: {field} diverges from M1-L source")
        if r.get("source_residual", "").strip() != src.get("residual", "").strip():
            errors.append(f"{lid}: source_residual diverges from M1-L source")
        if r.get("provenance", "").strip() not in ALLOWED_PROVENANCE:
            errors.append(f"{lid}: unsupported provenance={r.get('provenance', '')!r}")
        if r.get("resolution_lane", "").strip() not in ALLOWED_LANES:
            errors.append(f"{lid}: invalid resolution_lane={r.get('resolution_lane', '')!r}")
        if "OR_SCOPE_EXCLUSION" not in r.get("closure_class", "") and lid not in {
            "M1L-LM-001", "M1L-LM-002", "M1L-LM-005", "M1L-LM-014", "M1L-LM-015", "M1L-LM-016"
        }:
            errors.append(f"{lid}: evidence/binding residual must preserve explicit scope-exclusion path")
        if r.get("canonical_source", "").strip() != "data/canonical/M1L_LOAD_MODEL_CURRENT_v1.csv":
            errors.append(f"{lid}: canonical_source must remain the M1-L current load model")

        # B02 is a residual inventory only. It must not introduce numerical actions.
        for forbidden_field in ["numeric_value", "numeric_unit", "Gk", "Qk", "mass", "psi"]:
            if forbidden_field in r and r.get(forbidden_field, "").strip():
                errors.append(f"{lid}: B02 register must not assign {forbidden_field}")

    # Hard dependency guards copied from the canonical M1-L model semantics.
    by = {r.get("load_id", "").strip(): r for r in rows}
    if by.get("M1L-LM-001", {}).get("resolution_lane") != "EXISTING_PRIMARY_SOURCE_RECOVERY":
        errors.append("M1L-LM-001 must remain an existing-primary-source recovery task")
    if by.get("M1L-LM-002", {}).get("resolution_lane") != "EXPLICIT_MODEL_PARAMETER_OR_EVIDENCE":
        errors.append("M1L-LM-002 must remain an explicit model-parameter/evidence task")
    if by.get("M1L-LM-005", {}).get("resolution_lane") != "USE_CLASSIFICATION_AND_ADOPTED_ASSESSMENT_RULE":
        errors.append("M1L-LM-005 must remain a use-classification/adopted-rule task")
    for lid in ["M1L-LM-014", "M1L-LM-015", "M1L-LM-016"]:
        if by.get(lid, {}).get("resolution_lane") != "DEPENDENT_DOWNSTREAM_AFTER_UPSTREAM_CLOSURE":
            errors.append(f"{lid} must remain downstream-dependent")

    provenance_counts = {
        p: sum(1 for r in rows if r.get("provenance", "").strip() == p)
        for p in ["DOC", "RIF", "ND"]
    }
    lane_counts = {
        lane: sum(1 for r in rows if r.get("resolution_lane", "").strip() == lane)
        for lane in ALLOWED_LANES
    }

    expected_counts = {
        "DOC": 6,
        "RIF": 4,
        "ND": 6,
        "EXISTING_PRIMARY_SOURCE_RECOVERY": 1,
        "EXPLICIT_MODEL_PARAMETER_OR_EVIDENCE": 1,
        "USE_CLASSIFICATION_AND_ADOPTED_ASSESSMENT_RULE": 1,
        "EVIDENCE_BINDING_OR_SCOPE_EXCLUSION": 10,
        "DEPENDENT_DOWNSTREAM_AFTER_UPSTREAM_CLOSURE": 3,
    }
    for key, expected in expected_counts.items():
        actual = provenance_counts.get(key, lane_counts.get(key, 0))
        if actual != expected:
            errors.append(f"{key}: expected {expected}, got {actual}")

    gg = {r.get("gate_id", "").strip(): r for r in gate}
    expected_gate = {
        "M1E-B02-G01": "16",
        "M1E-B02-G02": "6",
        "M1E-B02-G03": "4",
        "M1E-B02-G04": "6",
        "M1E-B02-G05": "0",
        "M1E-B02-G06": "3",
        "M1E-B02-G07": "NO",
        "M1E-B02-G08": "NO",
        "M1E-B02-GATE": "RESIDUAL_SCOPE_BOUND_16_OPEN",
    }
    for gid, expected in expected_gate.items():
        observed = gg.get(gid, {}).get("observed", "").strip()
        if observed != expected:
            errors.append(f"{gid}: expected observed={expected!r}, got {observed!r}")

    # Guard text must continue to prohibit the two most dangerous shortcuts.
    forbidden_text = " ".join(r.get("forbidden_inference", "") for r in rows).lower()
    for concept in ["historical", "unsourced"]:
        if concept not in forbidden_text:
            errors.append(f"B02 guard text no longer contains explicit {concept} prohibition")

    warnings.append(
        "M1E-B02 remains open by design: the 16 M1-L residual rows are bounded, but zero current numerical load rows, masses or assessment combinations are authorized."
    )

    return finish(errors, warnings, {
        "residual_rows": len(rows),
        "doc_rows": provenance_counts["DOC"],
        "rif_rows": provenance_counts["RIF"],
        "nd_rows": provenance_counts["ND"],
        "downstream_dependent_rows": lane_counts["DEPENDENT_DOWNSTREAM_AFTER_UPSTREAM_CLOSURE"],
        "numeric_load_rows_ready": 0,
        "b02_closed": "NO",
        "calculation_model_ready": "NO",
    })


if __name__ == "__main__":
    sys.exit(main())
