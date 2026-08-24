#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
CONT = C / "STOREY_SUPPORT_CONTINUITY_G4_G5_TAV06S_v1.json"
SECTIONS = C / "STOREY_SUPPORT_SECTIONS_G5_v1.csv"
FAMILIES = C / "M1A_COLUMN_REINFORCEMENT_FAMILIES_v1.csv"
BIND = C / "M1A_G5_COLUMN_REINFORCEMENT_BINDING_CURRENT_v1.csv"
CONFLICT = C / "M1A_G5_COLUMN_REINFORCEMENT_SOURCE_CONFLICT_v1.csv"
GATE = C / "M1A_G5_COLUMN_REINFORCEMENT_GATE_v1.csv"


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def finish(errors: list[str], warnings: list[str], summary: dict[str, object]) -> int:
    status = "FAIL" if errors else ("PASS_WITH_WATCH" if warnings else "PASS")
    print(f"M1-A G5 column reinforcement validation: {status}")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    return 1 if errors else 0


def split_ids(text: str) -> set[str]:
    return {x.strip() for x in text.split(";") if x.strip()}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    for path in [CONT, SECTIONS, FAMILIES, BIND, CONFLICT, GATE]:
        if not path.exists():
            errors.append(f"missing artifact: {path.relative_to(ROOT)}")
    if errors:
        return finish(errors, warnings, {})

    with CONT.open("r", encoding="utf-8") as f:
        cont = json.load(f)
    sections = read_csv(SECTIONS)
    families = read_csv(FAMILIES)
    bindings = read_csv(BIND)
    conflicts = read_csv(CONFLICT)
    gate = read_csv(GATE)

    current = set(cont.get("present_on_tav06s", []))
    absent = set(cont.get("not_present_on_tav06s", []))
    if len(current) != 25:
        errors.append(f"expected 25 current G5 supports, got {len(current)}")
    if "24" not in absent:
        errors.append("support 24 must remain DOC absent from G5 roof carpenteria")

    fam_by = {r["family_id"].strip(): r for r in families}
    v01 = fam_by.get("T7-V-01")
    v02 = fam_by.get("T7-V-02")
    if not v01 or not v02:
        errors.append("missing T7-V-01 or T7-V-02 family")
        return finish(errors, warnings, {})
    for fam in [v01, v02]:
        if fam["evidence_status"].strip() != "DOC":
            errors.append(f"{fam['family_id']}: V-order family must remain DOC")
        if not fam["validation_state"].strip().startswith("DIRECT_NUMBERED"):
            errors.append(f"{fam['family_id']}: V-order family must remain directly numbered")

    v01_ids = split_ids(v01["explicit_support_ids"])
    v02_ids = split_ids(v02["explicit_support_ids"])
    source_ids = v01_ids | v02_ids
    if v01_ids & v02_ids:
        errors.append(f"V-order family support lists overlap: {sorted(v01_ids & v02_ids)}")
    if len(source_ids) != 26:
        errors.append(f"expected 26 direct V-order source ids, got {len(source_ids)}")
    source_only = source_ids - current
    current_missing = current - source_ids
    if source_only != {"24"}:
        errors.append(f"expected source-only support {{'24'}}, got {sorted(source_only)}")
    if current_missing:
        errors.append(f"current G5 supports missing from V-order source families: {sorted(current_missing)}")

    if len(bindings) != 25:
        errors.append(f"expected 25 current binding rows, got {len(bindings)}")
    bind_ids = [r["support_id"].strip() for r in bindings]
    if len(bind_ids) != len(set(bind_ids)):
        errors.append("duplicate support_id in G5 reinforcement binding")
    if set(bind_ids) != current:
        errors.append(f"binding support set mismatch: missing={sorted(current-set(bind_ids))} extra={sorted(set(bind_ids)-current)}")
    if "24" in bind_ids:
        errors.append("support 24 must not appear in current G5 reinforcement binding")

    section_by = {r["support_id"].strip(): r for r in sections}
    if set(section_by) != current:
        errors.append("G5 section register support set does not match current TAV-06S set")

    c_v01 = 0
    c_v02 = 0
    section_matches = 0
    for row in bindings:
        sid = row["support_id"].strip()
        family_id = row["source_family_id"].strip()
        if row["evidence_status"].strip() != "DOC":
            errors.append(f"{sid}: reinforcement binding must remain DOC")
        if row["validation_state"].strip() != "DIRECT_CURRENT_G5_BINDING":
            errors.append(f"{sid}: invalid binding state {row['validation_state']!r}")
        if row["source_numbering"].strip() != "DIRECT_NUMBERED":
            errors.append(f"{sid}: source numbering must remain DIRECT_NUMBERED")

        expected_family = "T7-V-01" if sid in v01_ids else "T7-V-02" if sid in v02_ids else None
        if family_id != expected_family:
            errors.append(f"{sid}: expected family {expected_family}, got {family_id}")
            continue
        fam = fam_by[family_id]
        expected_fields = {
            "section_cm": fam["section_drawn_cm"].strip(),
            "longitudinal_long": fam["longitudinal_long"].strip(),
            "monconi": fam["monconi"].strip(),
            "stirrup_diameter_mm": fam["stirrup_diameter_mm"].strip(),
            "stirrup_spacing_cm": fam["stirrup_spacing_cm"].strip(),
        }
        for field, expected in expected_fields.items():
            if row[field].strip() != expected:
                errors.append(f"{sid}: {field} expected {expected!r}, got {row[field].strip()!r}")
        if family_id == "T7-V-01":
            c_v01 += 1
        else:
            c_v02 += 1

        sec = section_by.get(sid, {})
        if sec.get("section_cm", "").strip() == row["section_cm"].strip() and sec.get("evidence_status", "").strip() == "DOC":
            section_matches += 1
        else:
            errors.append(f"{sid}: reinforcement-family section does not match independent G5 section register")

    if c_v01 != 13:
        errors.append(f"expected 13 current T7-V-01 bindings, got {c_v01}")
    if c_v02 != 12:
        errors.append(f"expected 12 current T7-V-02 bindings, got {c_v02}")
    if section_matches != 25:
        errors.append(f"expected 25 independent section matches, got {section_matches}")

    if len(conflicts) != 1:
        errors.append(f"expected one G5 column source conflict row, got {len(conflicts)}")
    else:
        c = conflicts[0]
        if c["source_support_id"].strip() != "24":
            errors.append("G5 column source conflict must be support 24")
        if c["evidence_state"].strip() != "DOC_SOURCE_CONFLICT":
            errors.append("support 24 conflict must remain DOC_SOURCE_CONFLICT")
        decision = c["current_model_decision"].lower()
        if "exclude support 24" not in decision or "do not create" not in decision:
            errors.append("support 24 conflict must explicitly exclude current G5 creation")

    gg = {r["check_id"].strip(): r for r in gate}
    expected_gate = {
        "M1A-G5C-G01": "25",
        "M1A-G5C-G02": "26",
        "M1A-G5C-G03": "25",
        "M1A-G5C-G04": "0",
        "M1A-G5C-G05": "13",
        "M1A-G5C-G06": "12",
        "M1A-G5C-G07": "25",
        "M1A-G5C-G08": "1",
        "M1A-G5C-G09": "NO",
        "M1A-G5C-G10": "NO",
        "M1A-G5C-GATE": "PASS_G5_COLUMN_REINFORCEMENT_25_OF_25_WITH_SOURCE24_CONFLICT_WATCH",
    }
    for cid, expected in expected_gate.items():
        actual = gg.get(cid, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{cid}: expected actual={expected!r}, got {actual!r}")

    warnings.append("TAV-07A V order directly lists support 24, while TAV-06S documents it absent from current G5 carpenteria; the conflict is preserved without geometry reopen")

    return finish(errors, warnings, {
        "current_g5_supports": len(current),
        "direct_v_order_source_ids": len(source_ids),
        "current_g5_reinforcement_bindings": len(bindings),
        "t7_v01_current_bindings": c_v01,
        "t7_v02_current_bindings": c_v02,
        "independent_section_matches": section_matches,
        "source_only_conflicts": len(source_only),
        "current_missing_bindings": len(current_missing),
    })


if __name__ == "__main__":
    sys.exit(main())
