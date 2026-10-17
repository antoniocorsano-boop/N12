#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAMILY_PATH = ROOT / "data/canonical/M1A_COLUMN_REINFORCEMENT_FAMILIES_v1.csv"
MATRIX_PATH = ROOT / "data/canonical/M1A_COLUMN_REINFORCEMENT_BINDING_CURRENT_v1.csv"
COVERAGE_PATH = ROOT / "data/canonical/M1A_COLUMN_REINFORCEMENT_COVERAGE_CURRENT_v1.csv"
CONFLICT_PATH = ROOT / "data/canonical/M1A_COLUMN_REINFORCEMENT_CARPENTRY_FIRST_CONFLICTS_v1.csv"
GATE_PATH = ROOT / "data/canonical/M1A_COLUMN_REINFORCEMENT_BINDING_GATE_v1.csv"

STOREY_SOURCES = {
    "G1": ROOT / "data/canonical/PT_PILLAR_SECTIONS_HIRES_CURRENT_v2.csv",
    "G2": ROOT / "data/canonical/STOREY_SUPPORT_SECTIONS_G2_v1.csv",
    "G3": ROOT / "data/canonical/STOREY_SUPPORT_SECTIONS_G3_v1.csv",
    "G4": ROOT / "data/canonical/STOREY_SUPPORT_SECTIONS_G4_v1.csv",
    "G5": ROOT / "data/canonical/STOREY_SUPPORT_SECTIONS_G5_v1.csv",
}
STOREY_ORDER = {"G1": "I", "G2": "II", "G3": "III", "G4": "IV", "G5": "V"}
BOUND_STATUSES = {"BOUND_SECTION_AND_ID", "BOUND_SECTION_UNIQUE"}
LATER_ADDED_G1 = {"a", "b", "c", "d"}
EXPECTED_GATE_STATUS = (
    "PASS_COLUMN_REINFORCEMENT_CARPENTRY_FIRST_BINDING_"
    "WITH_7_RESIDUALS_AND_5_SOURCE_CONFLICTS_WATCH"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def section_text(value: str) -> str:
    return (value or "").strip().lower().replace("×", "x").replace(" ", "")


def section_key(value: str) -> tuple[int, int] | None:
    text = section_text(value)
    m = re.fullmatch(r"(\d+)x(\d+)", text)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    return tuple(sorted((a, b)))


def split_ids(value: str) -> set[str]:
    return {token.strip() for token in (value or "").split(";") if token.strip()}


def high_level_evidence(value: str) -> str:
    v = (value or "").strip().upper()
    if v.startswith("DOC"):
        return "DOC"
    if v.startswith("MIS"):
        return "MIS"
    if v.startswith("RIF"):
        return "RIF"
    if v.startswith("INF"):
        return "INF"
    if v.startswith("INC"):
        return "INC"
    if v.startswith("ND"):
        return "ND"
    return v


def load_supports() -> dict[str, dict[str, dict[str, str]]]:
    result: dict[str, dict[str, dict[str, str]]] = {}
    for storey, path in STOREY_SOURCES.items():
        rows = read_csv(path)
        supports: dict[str, dict[str, str]] = {}
        for row in rows:
            if storey == "G1":
                sid = row["pillar_id"].strip()
                section = row["section_cm"].strip()
                orientation = (row.get("orientation_class") or section).strip()
            else:
                sid = row["support_id"].strip()
                section = row["section_cm"].strip()
                orientation = section
            if sid in supports:
                raise AssertionError(f"{storey}: duplicate support {sid} in {path}")
            supports[sid] = {
                "section": section,
                "orientation": orientation,
                "evidence": high_level_evidence(row.get("evidence_status", "")),
            }
        result[storey] = supports
    return result


def prepare_families() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    rows = read_csv(FAMILY_PATH)
    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        fid = row["family_id"].strip()
        if fid in by_id:
            raise AssertionError(f"duplicate family {fid}")
        row["_ids"] = split_ids(row.get("explicit_support_ids", ""))  # type: ignore[index]
        by_id[fid] = row
    return rows, by_id


def candidates_for(
    families: list[dict[str, str]], order_id: str, orientation: str
) -> list[dict[str, str]]:
    order_rows = [f for f in families if f["order_id"].strip() == order_id]
    exact = [f for f in order_rows if section_text(f["section_drawn_cm"]) == section_text(orientation)]
    if exact:
        return exact
    okey = section_key(orientation)
    return [f for f in order_rows if section_key(f["section_drawn_cm"]) == okey]


def expected_binding(
    storey: str,
    sid: str,
    orientation: str,
    families: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, str] | None, str]:
    order_id = STOREY_ORDER[storey]
    cands = candidates_for(families, order_id, orientation)

    if storey == "G1" and sid in LATER_ADDED_G1:
        return cands, None, "SECTION_MATCH_ONLY_LATER_ADDITION"
    if not cands:
        return cands, None, "UNBOUND_NO_SECTION_FAMILY"
    if len(cands) == 1:
        selected = cands[0]
        status = (
            "BOUND_SECTION_AND_ID"
            if sid in selected["_ids"]  # type: ignore[operator]
            else "BOUND_SECTION_UNIQUE"
        )
        return cands, selected, status

    explicit_compatible = [f for f in cands if sid in f["_ids"]]  # type: ignore[operator]
    if len(explicit_compatible) == 1:
        return cands, explicit_compatible[0], "BOUND_SECTION_AND_ID"
    return cands, None, "UNBOUND_SECTION_AMBIGUOUS"


def current_conflicting_callouts(
    storey: str,
    sid: str,
    orientation: str,
    families: list[dict[str, str]],
    candidate_ids: set[str],
) -> list[str]:
    order_id = STOREY_ORDER[storey]
    conflicts: list[str] = []
    for fam in families:
        if fam["order_id"].strip() != order_id:
            continue
        if sid in fam["_ids"] and fam["family_id"] not in candidate_ids:  # type: ignore[operator]
            conflicts.append(fam["family_id"])
    if storey == "G4":
        for fam in families:
            if fam["order_id"].strip() != "IV_to_V_transition":
                continue
            if sid in fam["_ids"] and section_key(fam["section_drawn_cm"]) != section_key(orientation):  # type: ignore[operator]
                conflicts.append(fam["family_id"])
    return sorted(conflicts)


def main() -> int:
    required = [
        FAMILY_PATH, MATRIX_PATH, COVERAGE_PATH, CONFLICT_PATH, GATE_PATH, *STOREY_SOURCES.values()
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise AssertionError(f"missing required files: {missing}")

    families, _fam_by_id = prepare_families()
    supports = load_supports()

    expected_counts = {"G1": 38, "G2": 34, "G3": 34, "G4": 34, "G5": 25}
    actual_counts = {s: len(v) for s, v in supports.items()}
    if actual_counts != expected_counts:
        raise AssertionError(f"support inventory changed: {actual_counts} != {expected_counts}")

    matrix_rows = read_csv(MATRIX_PATH)
    if len(matrix_rows) != 165:
        raise AssertionError(f"matrix row count {len(matrix_rows)} != 165")
    matrix: dict[tuple[str, str], dict[str, str]] = {}
    for row in matrix_rows:
        key = (row["storey_id"].strip(), row["support_id"].strip())
        if key in matrix:
            raise AssertionError(f"duplicate matrix row {key}")
        matrix[key] = row

    expected_current_conflicts: set[tuple[str, str, str]] = set()

    for storey in ["G1", "G2", "G3", "G4", "G5"]:
        order_id = STOREY_ORDER[storey]
        for sid, src in supports[storey].items():
            key = (storey, sid)
            if key not in matrix:
                raise AssertionError(f"missing matrix row {key}")
            row = matrix[key]

            if row["order_id"].strip() != order_id:
                raise AssertionError(f"{key}: wrong order {row['order_id']} != {order_id}")
            if section_text(row["carpentry_section_cm"]) != section_text(src["section"]):
                raise AssertionError(f"{key}: section differs from source")
            if section_text(row["carpentry_orientation_cm"]) != section_text(src["orientation"]):
                raise AssertionError(f"{key}: orientation differs from source")
            if row["carpentry_evidence_status"].strip() != src["evidence"]:
                raise AssertionError(f"{key}: evidence {row['carpentry_evidence_status']} != {src['evidence']}")

            cands, selected, expected_status = expected_binding(
                storey, sid, src["orientation"], families
            )
            cand_ids = [f["family_id"] for f in cands]
            if split_ids(row["candidate_family_ids"]) != set(cand_ids):
                raise AssertionError(
                    f"{key}: candidate families {row['candidate_family_ids']} != {cand_ids}"
                )
            selected_id = selected["family_id"] if selected else ""
            if row["selected_family_id"].strip() != selected_id:
                raise AssertionError(
                    f"{key}: selected family {row['selected_family_id']} != {selected_id}"
                )
            if row["binding_status"].strip() != expected_status:
                raise AssertionError(
                    f"{key}: binding status {row['binding_status']} != {expected_status}"
                )

            candidate_id_set = set(cand_ids)
            conflicts = current_conflicting_callouts(
                storey, sid, src["orientation"], families, candidate_id_set
            )
            for fid in conflicts:
                expected_current_conflicts.add((storey, sid, fid))
            if split_ids(row["conflicting_callout_family_ids"]) != set(conflicts):
                raise AssertionError(
                    f"{key}: conflicts {row['conflicting_callout_family_ids']} != {conflicts}"
                )

            if conflicts:
                if selected and sid in selected["_ids"]:  # type: ignore[operator]
                    expected_numeric = "MATCH_PLUS_CONFLICTING_ADDITIONAL_CALLOUT"
                else:
                    expected_numeric = "CONFLICTING_NUMERIC_CALLOUT_IGNORED_BY_SECTION_FIRST_RULE"
            else:
                if selected and sid in selected["_ids"]:  # type: ignore[operator]
                    expected_numeric = "MATCH"
                elif any(
                    f["order_id"].strip() == order_id and sid in f["_ids"]  # type: ignore[operator]
                    for f in families
                ):
                    expected_numeric = "COMPATIBLE_ID_UNRESOLVED"
                else:
                    expected_numeric = "NONE"
            if row["numeric_callout_state"].strip() != expected_numeric:
                raise AssertionError(
                    f"{key}: numeric state {row['numeric_callout_state']} != {expected_numeric}"
                )

            if selected:
                expected_relation = (
                    "DIRECT"
                    if section_text(src["orientation"]) == section_text(selected["section_drawn_cm"])
                    else "ROTATED_ORIENTATION_EQUIVALENT"
                )
                if row["orientation_relation"].strip() != expected_relation:
                    raise AssertionError(f"{key}: wrong orientation relation")
                for matrix_field, family_field in [
                    ("longitudinal_long", "longitudinal_long"),
                    ("monconi", "monconi"),
                    ("stirrup_diameter_mm", "stirrup_diameter_mm"),
                    ("stirrup_spacing_cm", "stirrup_spacing_cm"),
                ]:
                    if row[matrix_field].strip() != selected[family_field].strip():
                        raise AssertionError(
                            f"{key}: {matrix_field} differs from {selected_id}"
                        )
            else:
                if any(
                    row[field].strip()
                    for field in [
                        "longitudinal_long", "monconi",
                        "stirrup_diameter_mm", "stirrup_spacing_cm"
                    ]
                ):
                    raise AssertionError(f"{key}: unbound row contains reinforcement values")

    g5_current = set(supports["G5"])
    g5_source_only: set[tuple[str, str, str]] = set()
    for fam in families:
        if fam["order_id"].strip() != "V":
            continue
        for sid in fam["_ids"]:  # type: ignore[operator]
            if sid not in g5_current:
                g5_source_only.add(("G5", sid, fam["family_id"]))

    expected_conflict_keys = expected_current_conflicts | g5_source_only
    actual_conflict_rows = read_csv(CONFLICT_PATH)
    actual_conflict_keys = {
        (
            r["storey_id"].strip(),
            r["support_id"].strip(),
            r["conflicting_family_id"].strip(),
        )
        for r in actual_conflict_rows
    }
    if actual_conflict_keys != expected_conflict_keys:
        raise AssertionError(
            f"conflict register mismatch: {actual_conflict_keys} != {expected_conflict_keys}"
        )
    if len(actual_conflict_rows) != 5:
        raise AssertionError(f"conflict row count {len(actual_conflict_rows)} != 5")

    coverage_rows = read_csv(COVERAGE_PATH)
    coverage = {r["storey_id"].strip(): r for r in coverage_rows}
    if set(coverage) != set(STOREY_ORDER):
        raise AssertionError("coverage storey set mismatch")

    total_bound = 0
    total_unbound = 0
    for storey in STOREY_ORDER:
        rs = [r for r in matrix_rows if r["storey_id"].strip() == storey]
        bound = [r for r in rs if r["binding_status"].strip() in BOUND_STATUSES]
        unbound = [r for r in rs if r["binding_status"].strip() not in BOUND_STATUSES]
        current_conflict_ids = sorted(
            {
                sid
                for s, sid, _ in expected_current_conflicts
                if s == storey
            }
        )
        source_only_ids = sorted(
            {
                sid
                for s, sid, _ in g5_source_only
                if s == storey
            }
        )
        row = coverage[storey]
        checks = {
            "current_support_count": len(rs),
            "bound_count": len(bound),
            "unbound_count": len(unbound),
            "current_numeric_conflict_count": len(current_conflict_ids),
            "source_only_conflict_count": len(source_only_ids),
        }
        for field, expected in checks.items():
            if int(row[field]) != expected:
                raise AssertionError(f"{storey}: {field} {row[field]} != {expected}")
        if split_ids(row["unbound_ids"]) != {r["support_id"].strip() for r in unbound}:
            raise AssertionError(f"{storey}: unbound ID set mismatch")
        if split_ids(row["current_numeric_conflict_ids"]) != set(current_conflict_ids):
            raise AssertionError(f"{storey}: current conflict ID set mismatch")
        if split_ids(row["source_only_conflict_ids"]) != set(source_only_ids):
            raise AssertionError(f"{storey}: source-only conflict ID set mismatch")

        family_counts = Counter(
            r["selected_family_id"].strip()
            for r in bound
            if r["selected_family_id"].strip()
        )
        encoded = {}
        for token in split_ids(row["family_binding_counts"]):
            fid, count = token.split("=", 1)
            encoded[fid] = int(count)
        if encoded != dict(family_counts):
            raise AssertionError(f"{storey}: family binding counts mismatch")
        total_bound += len(bound)
        total_unbound += len(unbound)

    if total_bound != 158 or total_unbound != 7:
        raise AssertionError(f"totals changed: bound={total_bound}, unbound={total_unbound}")

    gate_rows = read_csv(GATE_PATH)
    if len(gate_rows) != 1:
        raise AssertionError("binding gate must contain exactly one row")
    gate = gate_rows[0]
    numeric_checks = {
        "total_current_support_storey_rows": 165,
        "bound_rows": 158,
        "unbound_rows": 7,
        "documented_conflict_rows": 5,
    }
    for field, expected in numeric_checks.items():
        if int(gate[field]) != expected:
            raise AssertionError(f"gate {field} {gate[field]} != {expected}")
    if gate["gate_status"].strip() != EXPECTED_GATE_STATUS:
        raise AssertionError(f"unexpected gate status: {gate['gate_status']}")
    rule = gate["binding_rule"].upper()
    for required_phrase in ["SECTION", "ORDER", "NUMERIC CALLOUTS NEVER OVERRIDE"]:
        if required_phrase not in rule:
            raise AssertionError(f"binding rule missing phrase: {required_phrase}")

    hard_expected = {
        ("G2", "32"): "T7-II-02",
        ("G4", "22"): "T7-IV-04",
        ("G4", "9"): "T7-IV-02",
        ("G4", "16"): "T7-IV-02",
        ("G3", "9"): "",
        ("G3", "16"): "",
        ("G1", "3"): "",
    }
    for key, expected in hard_expected.items():
        if matrix[key]["selected_family_id"].strip() != expected:
            raise AssertionError(f"{key}: hard binding guard failed")
    for sid in LATER_ADDED_G1:
        if matrix[("G1", sid)]["selected_family_id"].strip():
            raise AssertionError(f"G1 {sid}: later addition must remain unbound to historical TAV-07 family")

    print("M1A_COLUMN_CARPENTRY_FIRST_BINDING = PASS")
    print("Current support-storey rows: 165")
    print("Bound: 158; explicit residuals: 7")
    print("Documented source/callout conflicts: 5")
    print("Coverage: G1 33/38, G2 34/34, G3 32/34, G4 34/34, G5 25/25")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
