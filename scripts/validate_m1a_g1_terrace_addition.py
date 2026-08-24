#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
MASTER = C / "PT_MASTER_CURRENT.csv"
TERRACE = C / "PT_TERRACE_GEOMETRY_CURRENT_v1.csv"
COL = C / "M1A_COLUMN_REINFORCEMENT_FAMILIES_v1.csv"
AD = C / "M1F_AD_HISTORICAL_MODEL_DELTA_AUDIT_v1.csv"
GATE = C / "M1A_G1_TERRACE_ADDITION_GATE_v1.csv"


def read(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def finish(errors: list[str], warnings: list[str], summary: dict[str, object]) -> int:
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-A G1 terrace addition validation: {status}")
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
    for path in [MASTER, TERRACE, COL, AD, GATE]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    master = read(MASTER)
    terrace = read(TERRACE)
    col = read(COL)
    ad = read(AD)
    gate = read(GATE)

    master_by = {r["entity_id"].strip(): r for r in master}
    added_ids = ["a", "b", "c", "d"]
    added = [master_by.get(i) for i in added_ids]
    if any(r is None for r in added):
        errors.append("PT_MASTER_CURRENT must contain distinct a,b,c,d rows")
    else:
        for r in added:
            if r["entity_type"].strip() != "TERRACE_ADDED_PILLAR":
                errors.append(f"{r['entity_id']}: wrong entity_type={r['entity_type']}")
            if r["section_cm"].strip() != "30x30":
                errors.append(f"{r['entity_id']}: expected section 30x30")
            if not r["metric_evidence"].strip().startswith("DOC_"):
                errors.append(f"{r['entity_id']}: metric evidence must remain documentary/current")

    terrace_by = {r["entity_id"].strip(): r for r in terrace}
    for i in added_ids:
        r = terrace_by.get(i, {})
        if r.get("geometry_status", "").strip().startswith("OPEN"):
            errors.append(f"{i}: stale OPEN terrace geometry is not allowed after PT Master reconciliation")
        if r.get("evidence_status", "").strip() != "DOC_METRIC_OR_AXIS":
            errors.append(f"{i}: terrace geometry artifact must inherit current documentary metric evidence")

    e03 = terrace_by.get("ETW-FLT-E03", {})
    relation = e03.get("parent_or_relation", "")
    if "length 1.50 m" not in relation:
        errors.append("ETW-FLT-E03 must preserve direct 1.50 m length")
    if "section and anchorage detail remain ND" not in e03.get("notes", ""):
        errors.append("ETW-FLT-E03 section/anchorage ND guard is missing")
    if "not automatically identified" not in e03.get("notes", ""):
        errors.append("ETW-FLT-E03 must stay separate from a-d subsystem")

    fam = [r for r in col if r["family_id"].strip() == "T7-I-04"]
    if len(fam) != 1:
        errors.append(f"expected exactly one T7-I-04 family, got {len(fam)}")
    else:
        f = fam[0]
        if f["section_drawn_cm"].strip() != "30x30":
            errors.append("T7-I-04 must remain 30x30")
        if f["longitudinal_long"].strip() != "4x14" or f["monconi"].strip() != "8x16":
            errors.append("T7-I-04 reinforcement transcription changed")
        if f["stirrup_diameter_mm"].strip() != "6" or f["stirrup_spacing_cm"].strip() != "15":
            errors.append("T7-I-04 stirrup transcription changed")
        if f["validation_state"].strip() != "FAMILY_ONLY":
            errors.append("T7-I-04 must remain FAMILY_ONLY; no direct a-d member assignment is proven")
        if f["explicit_support_ids"].strip():
            errors.append("T7-I-04 must not acquire explicit a-d support ids without primary source evidence")

    ad_by = {r["audit_id"].strip(): r for r in ad}
    built = ad_by.get("M1F-AD-001", {})
    if "Retain a-d" not in built.get("current_model_decision", ""):
        errors.append("M1-F as-built a-d retention rule is missing")
    omission = ad_by.get("M1F-AD-004", {})
    if "NOT_YET_DIRECTLY_PROVEN" not in omission.get("historical_model_state", ""):
        errors.append("historical a-d omission must remain not directly proven")

    gg = {r["check_id"].strip(): r for r in gate}
    expected = {
        "M1A-G1T-G01": "4",
        "M1A-G1T-G02": "4",
        "M1A-G1T-G03": "YES",
        "M1A-G1T-G04": "YES",
        "M1A-G1T-G05": "NO",
        "M1A-G1T-G06": "NO",
        "M1A-G1T-G07": "1.50",
        "M1A-G1T-G08": "NO",
        "M1A-G1T-G09": "NO",
        "M1A-G1T-G10": "NO",
        "M1A-G1T-G11": "NO",
        "M1A-G1T-GATE": "PASS_G1_ADDITION_GEOMETRY_WITH_COLUMN_AND_ANCHORAGE_REINFORCEMENT_WATCH",
    }
    for cid, exp in expected.items():
        actual = gg.get(cid, {}).get("actual", "").strip()
        if actual != exp:
            errors.append(f"{cid}: expected actual={exp!r}, got {actual!r}")

    warnings.extend([
        "TAV-07A I-order 30x30 family is documentary but remains FAMILY_ONLY and is not assigned to a-d",
        "a-d column longitudinal/stirrup reinforcement remains unbound",
        "ETW-FLT-E03 has direct 1.50 m geometry but section and anchorage reinforcement remain ND",
        "ETW-FLT-E03 and the a-d support subsystem remain separate until direct evidence binds them",
        "historical a-d omission remains conditional until primary historical calculation evidence is registered",
    ])

    return finish(errors, warnings, {
        "terrace_added_supports": sum(1 for r in added if r is not None),
        "doc_30x30_added_supports": sum(1 for r in added if r and r["section_cm"].strip() == "30x30"),
        "tav07a_i_order_30x30_family_rows": len(fam),
        "e03_direct_length_m": "1.50",
        "a_d_column_reinforcement_bound": "NO",
    })


if __name__ == "__main__":
    sys.exit(main())
