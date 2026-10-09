#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
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
    "NEW_PRIMARY_SOURCE_ACQUISITION_OR_SCOPE_EXCLUSION",
    "EXPLICIT_MODEL_PARAMETER_OR_EVIDENCE",
    "USE_CLASSIFICATION_AND_ADOPTED_ASSESSMENT_RULE",
    "EVIDENCE_BINDING_OR_SCOPE_EXCLUSION",
    "NEW_EVIDENCE_OR_SCOPE_EXCLUSION",
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
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))

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
            "M1L-LM-002", "M1L-LM-005", "M1L-LM-014", "M1L-LM-015", "M1L-LM-016"
        }:
            errors.append(f"{lid}: evidence/binding residual must preserve explicit scope-exclusion path")
        if r.get("canonical_source", "").strip() != "data/canonical/M1L_LOAD_MODEL_CURRENT_v1.csv":
            errors.append(f"{lid}: canonical_source must remain the M1-L current load model")

        for forbidden_field in ["numeric_value", "numeric_unit", "Gk", "Qk", "mass", "psi"]:
            if forbidden_field in r and r.get(forbidden_field, "").strip():
                errors.append(f"{lid}: B02 register must not assign {forbidden_field}")

    by = {r.get("load_id", "").strip(): r for r in rows}
    if by.get("M1L-LM-001", {}).get("resolution_lane") != "NEW_PRIMARY_SOURCE_ACQUISITION_OR_SCOPE_EXCLUSION":
        errors.append("M1L-LM-001 must require new primary-source acquisition or historical-scope exclusion; RC-P13 is not materialized in the current repository/archive tree")
    if by.get("M1L-LM-002", {}).get("resolution_lane") != "EXPLICIT_MODEL_PARAMETER_OR_EVIDENCE":
        errors.append("M1L-LM-002 must remain an explicit model-parameter/evidence task")
    if by.get("M1L-LM-005", {}).get("resolution_lane") != "USE_CLASSIFICATION_AND_ADOPTED_ASSESSMENT_RULE":
        errors.append("M1L-LM-005 must remain a use-classification/adopted-rule task")
    if by.get("M1L-LM-006", {}).get("resolution_lane") != "NEW_EVIDENCE_OR_SCOPE_EXCLUSION":
        errors.append("M1L-LM-006 must require new evidence or scope exclusion because the canonical delta register closes the current repository search until new evidence enters")
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
        "NEW_PRIMARY_SOURCE_ACQUISITION_OR_SCOPE_EXCLUSION": 1,
        "EXPLICIT_MODEL_PARAMETER_OR_EVIDENCE": 1,
        "USE_CLASSIFICATION_AND_ADOPTED_ASSESSMENT_RULE": 1,
        "EVIDENCE_BINDING_OR_SCOPE_EXCLUSION": 9,
        "NEW_EVIDENCE_OR_SCOPE_EXCLUSION": 1,
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
        "M1E-B02-G09": "0",
        "M1E-B02-G10": "1",
        "M1E-B02-G11": "1",
        "M1E-B02-G12": "9",
        "M1E-B02-GATE": "RESIDUAL_SCOPE_BOUND_16_OPEN",
    }
    for gid, expected in expected_gate.items():
        observed = gg.get(gid, {}).get("observed", "").strip()
        if observed != expected:
            errors.append(f"{gid}: expected observed={expected!r}, got {observed!r}")

    forbidden_text = " ".join(r.get("forbidden_inference", "") for r in rows).lower()
    for concept in ["historical", "unsourced"]:
        if concept not in forbidden_text:
            errors.append(f"B02 guard text no longer contains explicit {concept} prohibition")

    authoritative = handoff.get("authoritative_inputs", {})
    if authoritative.get("load_residual_register") != "data/canonical/M1E_B02_LOAD_RESIDUAL_REGISTER_v1.csv":
        errors.append("M1E handoff must reference the canonical B02 residual register")
    if authoritative.get("load_residual_gate") != "data/canonical/M1E_B02_LOAD_GATE_v1.csv":
        errors.append("M1E handoff must reference the canonical B02 residual gate")
    b02 = next((b for b in handoff.get("blocking_domains", []) if b.get("id") == "M1E-B02"), None)
    if not b02:
        errors.append("M1E handoff is missing blocking domain M1E-B02")
    else:
        if b02.get("blocking") is not True:
            errors.append("M1E-B02 must remain blocking until evidence-backed closure")
        if b02.get("state") != "RESIDUAL_SCOPE_BOUND_16_OPEN":
            errors.append(f"M1E-B02 handoff state drifted: {b02.get('state')!r}")
        if b02.get("residual_register") != "data/canonical/M1E_B02_LOAD_RESIDUAL_REGISTER_v1.csv":
            errors.append("M1E-B02 handoff residual_register mismatch")
        if b02.get("residual_gate") != "data/canonical/M1E_B02_LOAD_GATE_v1.csv":
            errors.append("M1E-B02 handoff residual_gate mismatch")
    if handoff.get("calculation_model_ready") is not False:
        errors.append("M1E handoff must keep calculation_model_ready=false while B02 is open")
    if handoff.get("status") != "RESIDUAL_NOT_CALCULATION_MODEL_READY":
        errors.append("M1E handoff status must remain RESIDUAL_NOT_CALCULATION_MODEL_READY while B02 is open")

    warnings.append(
        "M1E-B02 remains open by design: RC-P13 requires new primary-source acquisition, PT numeric build-up requires new evidence, and zero current numerical load rows, masses or assessment combinations are authorized."
    )

    return finish(errors, warnings, {
        "residual_rows": len(rows),
        "doc_rows": provenance_counts["DOC"],
        "rif_rows": provenance_counts["RIF"],
        "nd_rows": provenance_counts["ND"],
        "new_primary_source_rows": lane_counts["NEW_PRIMARY_SOURCE_ACQUISITION_OR_SCOPE_EXCLUSION"],
        "new_evidence_rows": lane_counts["NEW_EVIDENCE_OR_SCOPE_EXCLUSION"],
        "existing_binding_rows": lane_counts["EVIDENCE_BINDING_OR_SCOPE_EXCLUSION"],
        "downstream_dependent_rows": lane_counts["DEPENDENT_DOWNSTREAM_AFTER_UPSTREAM_CLOSURE"],
        "numeric_load_rows_ready": 0,
        "b02_closed": "NO",
        "calculation_model_ready": "NO",
    })


if __name__ == "__main__":
    sys.exit(main())
