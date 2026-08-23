#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
GROUPS = C / "M1F_TAV01A_GROUP_INDEX_v1.csv"
REINF = C / "M1F_TAV01A_GROUP_REINFORCEMENT_v1.csv"
PATCH = C / "M1F_TAV01A_REINFORCEMENT_CORRECTION_PATCH_v1.csv"
QUEUE = C / "M1F_REINFORCEMENT_EXTRACTION_QUEUE_v1.csv"
TOPOLOGY = C / "M1F_FOUNDATION_TOPOLOGY_CURRENT_v1.csv"
CROSSCHECK = C / "M1F_TAV01A_TAV01S_CROSSCHECK_v1.csv"
GATE = C / "M1F_FOUNDATION_REINFORCEMENT_GATE_v1.csv"

EXPECTED_GROUPS = {f"F1A-G0{i}" for i in range(1, 8)}
EXPECTED_PATCH_IDS = {f"M1F-REINF-P{i:03d}" for i in range(1, 32)}
EXPECTED_GATE_STATE = "PASS_GROUP_TRANSCRIPTION_COMPLETE_WITH_DOCUMENTARY_GAPS"


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def apply_patch(base, patch, errors):
    rows = [dict(r) for r in base]
    by_id = {r["row_id"].strip(): r for r in rows}
    patch_ids = {r["patch_id"].strip() for r in patch}
    if len(patch) != 31 or patch_ids != EXPECTED_PATCH_IDS:
        errors.append("HiRes correction/partition patch must contain exactly P001-P031")
        return rows

    for p in patch:
        op = p["operation"].strip()
        target = p["target_row_id"].strip()
        new_id = p["new_row_id"].strip()
        values = {
            "group_id": p["group_id"].strip(),
            "source_id": "TAV-01A",
            "source_locator": p["source_locator"].strip(),
            "bar_role": p["bar_role"].strip(),
            "bar_quantity": p["bar_quantity"].strip(),
            "bar_diameter_mm": p["bar_diameter_mm"].strip(),
            "shape_or_length": p["shape_or_length"].strip(),
            "segment_dimensions_cm": p.get("segment_dimensions_cm", "").strip(),
            "evidence_status": p["evidence_status"].strip(),
            "binding_state": p["binding_state"].strip(),
            "note": p["reason"].strip(),
        }
        if op == "REPLACE":
            if target not in by_id or new_id != target:
                errors.append(f"invalid REPLACE {p['patch_id']}: target={target} new={new_id}")
                continue
            by_id[target].update(values)
        elif op == "ADD":
            if not new_id or new_id in by_id:
                errors.append(f"invalid ADD {p['patch_id']}: new_row_id={new_id}")
                continue
            row = {k: "" for k in base[0].keys()}
            row["row_id"] = new_id
            row.update(values)
            rows.append(row)
            by_id[new_id] = row
        else:
            errors.append(f"unknown patch operation {op!r}")
    return rows


def assert_row(by_id, row_id, expected, errors):
    r = by_id.get(row_id, {})
    actual = (
        r.get("bar_quantity", "").strip(),
        r.get("bar_diameter_mm", "").strip(),
        r.get("shape_or_length", "").strip(),
        r.get("segment_dimensions_cm", "").strip(),
        r.get("binding_state", "").strip(),
    )
    if actual != expected:
        errors.append(f"{row_id}: direct partition mismatch expected {expected}, got {actual}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [GROUPS, REINF, PATCH, QUEUE, TOPOLOGY, CROSSCHECK, GATE]
    for path in required:
        if not path.exists():
            errors.append(f"missing required artifact: {path.relative_to(ROOT)}")
    if errors:
        return report(errors, warnings, {})

    groups, base, patch, queue, topology, cross, gate = map(read_csv, required)
    reinf = apply_patch(base, patch, errors)

    group_ids = [r["group_id"].strip() for r in groups]
    if len(groups) != 7 or set(group_ids) != EXPECTED_GROUPS or len(set(group_ids)) != 7:
        errors.append("group index must contain exactly unique G01-G07")
    if len(base) != 47:
        errors.append(f"base rows must remain 47, got {len(base)}")
    if len(reinf) != 69:
        errors.append(f"effective rows must be 69, got {len(reinf)}")
    row_ids = [r["row_id"].strip() for r in reinf]
    if len(row_ids) != len(set(row_ids)):
        errors.append("duplicate effective reinforcement row_id")
    if {r["group_id"].strip() for r in reinf} != EXPECTED_GROUPS:
        errors.append("effective reinforcement rows must cover exactly G01-G07")

    queue_by_group = {r["group_id"].strip(): r for r in queue}
    complete = sum(r["reinforcement_transcription_state"].strip() == "COMPLETE_DIRECT" for r in queue)
    partial = sum(r["reinforcement_transcription_state"].strip() == "PARTIAL_DIRECT" for r in queue)
    pending = sum(r["reinforcement_transcription_state"].strip() == "PENDING" for r in queue)
    if set(queue_by_group) != EXPECTED_GROUPS or len(queue) != 7:
        errors.append("queue must contain G01-G07 exactly once")
    if (complete, partial, pending) != (7, 0, 0):
        errors.append(f"queue partition expected 7/0/0, got {(complete, partial, pending)}")

    open_rows = [r for r in reinf if r["binding_state"].strip().startswith("OPEN_")]
    if open_rows:
        errors.append(f"zero OPEN_TRANSCRIPTION rows expected, got {[r.get('row_id','') for r in open_rows]}")

    for group in ["F1A-G05", "F1A-G06"]:
        states = {r["binding_state"].strip() for r in reinf if r["group_id"].strip() == group}
        if not any(s.endswith("B_SIDE") for s in states) or not any(s.endswith("A_SIDE") for s in states):
            errors.append(f"{group}: B/A regimes must remain explicit")
    g05_transition = [r for r in reinf if r["group_id"].strip() == "F1A-G05" and r["binding_state"].strip() == "GROUP_BOUND_TRANSITION_17_18"]
    if len(g05_transition) != 2:
        errors.append(f"G05 must preserve exactly two direct transition-spanning bars, got {len(g05_transition)}")

    by_id = {r["row_id"].strip(): r for r in reinf}
    exact = {
        "F1A-G07-R04": ("2","12","BENT_PARTIAL","70+70=140;right_diag122;left_inclined_segment_unlabelled","GROUP_BOUND"),
        "F1A-G07-R04B": ("2","12","BENT_PARTIAL","left_diag122;70+30=100;right_diag_unlabelled","GROUP_BOUND"),
        "F1A-G07-R04C": ("2","14","BENT_PARTIAL","left_diag122;30+70=100;right_end_segment_unlabelled","GROUP_BOUND"),
        "F1A-G04-R04": ("2","18","BENT_PARTIAL","left_end_segment_unlabelled;70+100=170;right_diag122;continuation_unlabelled","GROUP_BOUND"),
        "F1A-G04-R04B": ("2","14","BENT_PARTIAL","left_diag122;100+40=140;ascending_diag_unlabelled;top210;right_diag122;40+70=110","GROUP_BOUND"),
        "F1A-G06-R09A": ("2","14","BENT","left_diag122;100+45=145;ascending_diag122;top200;right_diag122;45+105=150","GROUP_BOUND_A_SIDE"),
        "F1A-G05-R04B": ("2","12","BENT","60+70=130;right_diag93","GROUP_BOUND_B_SIDE"),
        "F1A-G05-R04C": ("2","14","BENT","left_diag93;70+35=105;ascending_diag93;top140;descending_diag93;35+95=130;right_diag122","GROUP_BOUND_TRANSITION_17_18"),
        "F1A-G05-R09A": ("2","18","BENT","left_diag93;70+50=120;ascending_diag122;top280;descending_diag122;50+95=145;right_diag122","GROUP_BOUND_TRANSITION_17_18"),
        "F1A-G05-R09B": ("2","14","BENT_PARTIAL","left_diag122;95+70=165","GROUP_BOUND_A_SIDE"),
        "F1A-G03-R04": ("2","18","BENT_PARTIAL","70+50=120;ascending_diag122;top300;descending_diag_unlabelled;50+30=80;right_diag122","GROUP_BOUND_WITH_22_PRIME_CORRECTION"),
        "F1A-G03-R04B": ("2","12","BENT_PARTIAL","left_diag_unlabelled;30+40=70;ascending_diag122;top100;descending_diag_unlabelled;40+85=125;right_diag122","GROUP_BOUND_WITH_22_PRIME_CORRECTION"),
        "F1A-G03-R04C": ("2","16","BENT_PARTIAL","left_diag122;85+70=155","GROUP_BOUND_WITH_22_PRIME_CORRECTION"),
        "F1A-G03-R04D": ("2","18","BENT_PARTIAL","70+100=170;right_diag122","GROUP_BOUND_WITH_22_PRIME_CORRECTION"),
        "F1A-G03-R04E": ("2","14","BENT_PARTIAL","left_diag122;100+60=160","GROUP_BOUND_WITH_22_PRIME_CORRECTION"),
        "F1A-G03-R04F": ("2","14","BENT_PARTIAL","60+75=135;right_diag122","GROUP_BOUND_WITH_22_PRIME_CORRECTION"),
        "F1A-G03-R04G": ("2","16","BENT","left_diag122;75+45=120;ascending_diag122;top210;descending_diag122;45+70=115","GROUP_BOUND_WITH_22_PRIME_CORRECTION"),
        "F1A-G02-R04": ("2","16","BENT","70+45=115;ascending_diag122;top210;descending_diag122;45+90=135;right_diag122","GROUP_BOUND"),
        "F1A-G02-R04B": ("2","14","BENT_PARTIAL","left_diag_unlabelled;90+30=120;ascending_diag122;top95;descending_diag122;30+30=60;right_diag122","GROUP_BOUND"),
        "F1A-G02-R04C": ("2","12","BENT_PARTIAL","left_diag_unlabelled;30+50=80;right_diag122","GROUP_BOUND"),
        "F1A-G02-R04D": ("2","16","BENT_PARTIAL","left_diag_unlabelled;50+45=95;ascending_diag122;top260;descending_diag_unlabelled;45+90=135;right_diag122","GROUP_BOUND"),
        "F1A-G02-R04E": ("2","14","BENT_PARTIAL","left_diag122;90+70=160;right_vertical_end_unlabelled;right_inclined_segment_unlabelled","GROUP_BOUND"),
        "F1A-G02-R04F": ("2","14","BENT_PARTIAL","left_vertical_end_unlabelled;70+85=155;right_diag122","GROUP_BOUND"),
        "F1A-G02-R04G": ("2","16","BENT_PARTIAL","left_diag_unlabelled;85+50=135;ascending_diag122;top240;descending_diag_unlabelled;50+55=105;right_diag122","GROUP_BOUND"),
        "F1A-G02-R04H": ("2","12","BENT_PARTIAL","left_diag_unlabelled;55+80=135","GROUP_BOUND"),
        "F1A-G02-R04I": ("2","14","BENT_PARTIAL","80+30=110;ascending_diag122;top60;descending_diag_unlabelled;30+90=120;right_diag_unlabelled","GROUP_BOUND"),
        "F1A-G02-R04J": ("2","16","BENT_PARTIAL","left_diag_unlabelled;90+45=135;ascending_diag122;top240;descending_diag_unlabelled;45+70=115","GROUP_BOUND"),
    }
    for row_id, expected in exact.items():
        assert_row(by_id, row_id, expected, errors)

    g02 = [r for r in reinf if r["group_id"].strip() == "F1A-G02"]
    g02_bent = [r for r in g02 if "BENT_BAR" in r["bar_role"].strip()]
    if len(g02_bent) != 10 or any(r["binding_state"].strip() != "GROUP_BOUND" for r in g02_bent):
        errors.append("G02 must contain exactly ten bound bent bars after P022-P031")

    for row_id, expected in {
        "F1A-G02-R02": ("2","14","L=1080|L=990"),
        "F1A-G02-R02B": ("3","16","L=1100"),
        "F1A-G02-R03": ("3","14","L=1120|L=1010"),
        "F1A-G02-R03B": ("3","16","L=1120"),
    }.items():
        r = by_id.get(row_id, {})
        actual = (r.get("bar_quantity", "").strip(), r.get("bar_diameter_mm", "").strip(), r.get("shape_or_length", "").strip())
        if actual != expected:
            errors.append(f"{row_id}: G02 straight-bar correction mismatch")

    g03 = [r for r in reinf if r["group_id"].strip() == "F1A-G03"]
    expected_g03_straight = {
        ("UPPER_STRAIGHT_BAR","3","16","L=880"),
        ("UPPER_STRAIGHT_BAR","2","14","L=910"),
        ("LOWER_STRAIGHT_BAR","3","18","L=920"),
        ("LOWER_STRAIGHT_BAR","3","14","L=960"),
    }
    actual_g03_straight = {
        (r["bar_role"].strip(), r["bar_quantity"].strip(), r["bar_diameter_mm"].strip(), r["shape_or_length"].strip())
        for r in g03 if r["bar_role"].strip() in {"UPPER_STRAIGHT_BAR", "LOWER_STRAIGHT_BAR"}
    }
    if actual_g03_straight != expected_g03_straight:
        errors.append("G03 direct straight-bar mismatch")
    g03_bent = [r for r in g03 if "BENT_BAR" in r["bar_role"].strip()]
    if len(g03_bent) != 7 or any(r["binding_state"].strip() != "GROUP_BOUND_WITH_22_PRIME_CORRECTION" for r in g03_bent):
        errors.append("G03 must contain exactly seven bent bars with 22-prime correction binding")

    cross_by_id = {r["candidate_id"].strip(): r for r in cross}
    if cross_by_id.get("FND-C015", {}).get("promotion_state", "").strip() != "REJECTED_AS_PHYSICAL_EDGE":
        errors.append("FND-C015 must remain rejected")
    if cross_by_id.get("FND-C016", {}).get("promotion_state", "").strip() != "TRANSFORMED_TO_PHYSICAL_PATH":
        errors.append("FND-C016 must remain transformed through 22-prime")

    if len(topology) != 58:
        errors.append(f"topology expected 58, got {len(topology)}")
    direct = sum(r["reinforcement_binding_state"].strip() == "DIRECT_GROUP_BOUND" for r in topology)
    supported = sum(r["reinforcement_binding_state"].strip() == "SCHEMATIC_22_27_SPLIT_AT_22_PRIME" for r in topology)
    no_autonomous = len(topology) - direct - supported
    if (direct, supported, no_autonomous) != (42, 1, 15):
        errors.append(f"member binding partition mismatch {(direct, supported, no_autonomous)}")

    gate_by_id = {r["check_id"].strip(): r for r in gate}
    expected_gate_actuals = {
        "M1F-REINF-001": "7",
        "M1F-REINF-002": "7",
        "M1F-REINF-003": "69",
        "M1F-REINF-004": "7",
        "M1F-REINF-005": "0",
        "M1F-REINF-006": "0",
        "M1F-REINF-007": "0",
        "M1F-REINF-008": "2",
        "M1F-REINF-009": "1",
        "M1F-REINF-010": "42",
        "M1F-REINF-011": "1",
        "M1F-REINF-012": "15",
        "M1F-REINF-013": "4",
        "M1F-REINF-014": "3",
        "M1F-REINF-015": "2",
        "M1F-REINF-016": "1",
        "M1F-REINF-017": "4",
        "M1F-REINF-018": "7",
        "M1F-REINF-019": "10",
        "M1F-REINF-GATE": EXPECTED_GATE_STATE,
    }
    for check_id, expected in expected_gate_actuals.items():
        actual = gate_by_id.get(check_id, {}).get("actual", "").strip()
        if actual != expected:
            errors.append(f"{check_id}: expected {expected}, got {actual}")

    if no_autonomous:
        warnings.append(f"group transcription complete; {no_autonomous} physical members retain ND documentary exact-section/longitudinal-reinforcement coverage")
    unlabeled_rows = sum("UNLABELLED_SEGMENT_WATCH" in r["evidence_status"].strip() for r in reinf)
    if unlabeled_rows:
        warnings.append(f"source-unlabelled segment watches retained in {unlabeled_rows} effective reinforcement rows; no dimensions inferred")

    summary = {
        "groups": len(groups),
        "base_reinforcement_rows": len(base),
        "effective_reinforcement_rows": len(reinf),
        "correction_patch_rows": len(patch),
        "groups_complete": complete,
        "groups_partial": partial,
        "groups_pending": pending,
        "open_transcription_rows": len(open_rows),
        "g02_bent_rows": len(g02_bent),
        "members_direct_group_bound": direct,
        "members_supported_group_bound": supported,
        "members_without_autonomous_group": no_autonomous,
    }
    return report(errors, warnings, summary)


def report(errors, warnings, summary) -> int:
    state = "PASS" if not errors else "FAIL"
    print(f"M1F_FOUNDATION_REINFORCEMENT_VALIDATION={state}")
    for key, value in summary.items():
        print(f"{key}={value}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
