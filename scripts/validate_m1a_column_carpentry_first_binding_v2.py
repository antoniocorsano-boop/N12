#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"

FAMILY_PATH = C / "M1A_COLUMN_REINFORCEMENT_FAMILIES_v1.csv"
MATRIX_PATH = C / "M1A_COLUMN_REINFORCEMENT_BINDING_CURRENT_v1.csv"
OVERRIDE_PATH = C / "M1A_COLUMN_REINFORCEMENT_BINDING_OVERRIDE_v1.csv"
RECON_PATH = C / "M1A_TAV07A_IV_CALLOUT_RECONCILIATION_v1.csv"
COVERAGE_PATH = C / "M1A_COLUMN_REINFORCEMENT_COVERAGE_CURRENT_v1.csv"
CONFLICT_PATH = C / "M1A_COLUMN_REINFORCEMENT_CARPENTRY_FIRST_CONFLICTS_v1.csv"
GATE_PATH = C / "M1A_COLUMN_REINFORCEMENT_BINDING_GATE_v1.csv"

STOREY_SOURCES = {
    "G1": C / "PT_PILLAR_SECTIONS_HIRES_CURRENT_v2.csv",
    "G2": C / "STOREY_SUPPORT_SECTIONS_G2_v1.csv",
    "G3": C / "STOREY_SUPPORT_SECTIONS_G3_v1.csv",
    "G4": C / "STOREY_SUPPORT_SECTIONS_G4_v1.csv",
    "G5": C / "STOREY_SUPPORT_SECTIONS_G5_v1.csv",
}
STOREY_ORDER = {"G1": "I", "G2": "II", "G3": "III", "G4": "IV", "G5": "V"}
DEFAULT_EXCLUDED_VALIDATION_STATES = {"DIRECT_DUPLICATE_ID_CALLOUT_CONFLICT"}
BASE_BOUND = {"BOUND_SECTION_AND_ID", "BOUND_SECTION_UNIQUE"}
EXPECTED_RESIDUALS = {
    ("G1", "3"), ("G1", "a"), ("G1", "b"), ("G1", "c"), ("G1", "d"),
    ("G3", "9"), ("G3", "16"),
}
EXPECTED_CONFLICTS = {
    ("G2", "32", "T7-II-01"),
    ("G4", "9", "T7-TR-01"),
    ("G4", "16", "T7-TR-01"),
    ("G4", "22", "T7-IV-01"),
    ("G5", "24", "T7-V-01"),
}
EXPECTED_GATE_STATUS = (
    "PASS_COLUMN_REINFORCEMENT_CARPENTRY_FIRST_BINDING_"
    "WITH_7_RESIDUALS_AND_5_SOURCE_CONFLICTS_WATCH"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def st(value: str) -> str:
    return (value or "").strip().lower().replace("×", "x").replace(" ", "")


def sk(value: str) -> tuple[int, int] | None:
    m = re.fullmatch(r"(\d+)x(\d+)", st(value))
    if not m:
        return None
    return tuple(sorted((int(m.group(1)), int(m.group(2)))))


def ids(value: str) -> set[str]:
    return {x.strip() for x in (value or "").split(";") if x.strip()}


def evidence(value: str) -> str:
    v = (value or "").strip().upper()
    for prefix in ["DOC", "MIS", "RIF", "INF", "INC", "ND"]:
        if v.startswith(prefix):
            return prefix
    return v


def load_supports() -> dict[tuple[str, str], dict[str, str]]:
    out: dict[tuple[str, str], dict[str, str]] = {}
    for storey, path in STOREY_SOURCES.items():
        for r in read_csv(path):
            if storey == "G1":
                sid = r["pillar_id"].strip()
                section = r["section_cm"].strip()
                orientation = (r.get("orientation_class") or section).strip()
            else:
                sid = r["support_id"].strip()
                section = r["section_cm"].strip()
                orientation = section
            key = (storey, sid)
            if key in out:
                raise AssertionError(f"duplicate support source row {key}")
            out[key] = {
                "section": section,
                "orientation": orientation,
                "evidence": evidence(r.get("evidence_status", "")),
            }
    return out


def parse_family_counts(value: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for token in ids(value):
        fid, count = token.split("=", 1)
        result[fid] = int(count)
    return result


def default_candidates(
    families: list[dict[str, str]], order_id: str, orientation: str
) -> list[dict[str, str]]:
    rows = [
        f for f in families
        if f["order_id"].strip() == order_id
        and f["validation_state"].strip() not in DEFAULT_EXCLUDED_VALIDATION_STATES
    ]
    exact = [f for f in rows if st(f["section_drawn_cm"]) == st(orientation)]
    if exact:
        return exact
    key = sk(orientation)
    return [f for f in rows if sk(f["section_drawn_cm"]) == key]


def expected_base(
    storey: str, sid: str, orientation: str, families: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, str] | None, str]:
    cands = default_candidates(families, STOREY_ORDER[storey], orientation)
    if storey == "G1" and sid in {"a", "b", "c", "d"}:
        return cands, None, "SECTION_MATCH_ONLY_LATER_ADDITION"
    if not cands:
        return cands, None, "UNBOUND_NO_SECTION_FAMILY"
    if len(cands) == 1:
        fam = cands[0]
        status = "BOUND_SECTION_AND_ID" if sid in fam["_ids"] else "BOUND_SECTION_UNIQUE"  # type: ignore[operator]
        return cands, fam, status
    direct = [f for f in cands if sid in f["_ids"]]  # type: ignore[operator]
    if len(direct) == 1:
        return cands, direct[0], "BOUND_SECTION_AND_ID"
    return cands, None, "UNBOUND_SECTION_AMBIGUOUS"


def source_conflicts(
    storey: str,
    sid: str,
    orientation: str,
    families: list[dict[str, str]],
    compatible_ids: set[str],
) -> set[str]:
    result: set[str] = set()
    order_id = STOREY_ORDER[storey]
    for fam in families:
        if fam["order_id"].strip() != order_id:
            continue
        if sid not in fam["_ids"]:  # type: ignore[operator]
            continue
        if fam["family_id"] not in compatible_ids and sk(fam["section_drawn_cm"]) != sk(orientation):
            result.add(fam["family_id"])
    return result


def main() -> int:
    required = [
        FAMILY_PATH, MATRIX_PATH, OVERRIDE_PATH, RECON_PATH, COVERAGE_PATH,
        CONFLICT_PATH, GATE_PATH, *STOREY_SOURCES.values(),
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise AssertionError(f"missing artifacts: {missing}")

    families = read_csv(FAMILY_PATH)
    fam_by: dict[str, dict[str, str]] = {}
    for f in families:
        fid = f["family_id"].strip()
        if fid in fam_by:
            raise AssertionError(f"duplicate family {fid}")
        f["_ids"] = ids(f.get("explicit_support_ids", ""))  # type: ignore[index]
        fam_by[fid] = f

    special = fam_by.get("T7-TR-01")
    if not special:
        raise AssertionError("missing T7-TR-01 special IV detail")
    if special["order_id"].strip() != "IV":
        raise AssertionError("T7-TR-01 must now be located in IV order")
    if special["section_drawn_cm"].strip() != "30x45":
        raise AssertionError("T7-TR-01 section must remain 30x45")
    if special["longitudinal_long"].strip() != "4x16" or special["monconi"].strip() != "8x14":
        raise AssertionError("T7-TR-01 reinforcement changed")
    if special["validation_state"].strip() != "DIRECT_DUPLICATE_ID_CALLOUT_CONFLICT":
        raise AssertionError("T7-TR-01 must remain quarantined from default direct binding")
    if ids(special["explicit_support_ids"]) != {"9", "16"}:
        raise AssertionError("literal T7-TR-01 source label 9-16 must be preserved")
    if "IV ordine" not in special["source_locator"]:
        raise AssertionError("T7-TR-01 source locator must record IV-order location")

    supports = load_supports()
    expected_support_counts = {"G1": 38, "G2": 34, "G3": 34, "G4": 34, "G5": 25}
    actual_support_counts = Counter(storey for storey, _ in supports)
    if dict(actual_support_counts) != expected_support_counts:
        raise AssertionError(f"support inventory changed: {dict(actual_support_counts)}")

    matrix_rows = read_csv(MATRIX_PATH)
    if len(matrix_rows) != 165:
        raise AssertionError(f"base matrix must contain 165 rows, got {len(matrix_rows)}")
    matrix: dict[tuple[str, str], dict[str, str]] = {}
    derived_current_conflicts: set[tuple[str, str, str]] = set()

    for r in matrix_rows:
        key = (r["storey_id"].strip(), r["support_id"].strip())
        if key in matrix:
            raise AssertionError(f"duplicate matrix row {key}")
        matrix[key] = r
        src = supports.get(key)
        if not src:
            raise AssertionError(f"matrix row not in current support inventory: {key}")
        if r["order_id"].strip() != STOREY_ORDER[key[0]]:
            raise AssertionError(f"{key}: wrong order")
        if st(r["carpentry_section_cm"]) != st(src["section"]):
            raise AssertionError(f"{key}: section differs from carpenteria source")
        if st(r["carpentry_orientation_cm"]) != st(src["orientation"]):
            raise AssertionError(f"{key}: orientation differs from carpenteria source")
        if r["carpentry_evidence_status"].strip() != src["evidence"]:
            raise AssertionError(f"{key}: carpenteria evidence status changed")

        cands, selected, status = expected_base(key[0], key[1], src["orientation"], families)
        cand_ids = {f["family_id"] for f in cands}
        if ids(r["candidate_family_ids"]) != cand_ids:
            raise AssertionError(f"{key}: base candidate set mismatch")
        expected_selected = selected["family_id"] if selected else ""
        if r["selected_family_id"].strip() != expected_selected:
            raise AssertionError(f"{key}: base selected family mismatch")
        if r["binding_status"].strip() != status:
            raise AssertionError(f"{key}: base binding status mismatch")

        for cfid in source_conflicts(key[0], key[1], src["orientation"], families, cand_ids):
            derived_current_conflicts.add((key[0], key[1], cfid))

        if selected:
            for mfield, ffield in [
                ("longitudinal_long", "longitudinal_long"),
                ("monconi", "monconi"),
                ("stirrup_diameter_mm", "stirrup_diameter_mm"),
                ("stirrup_spacing_cm", "stirrup_spacing_cm"),
            ]:
                if r[mfield].strip() != selected[ffield].strip():
                    raise AssertionError(f"{key}: {mfield} differs from base selected family")
        else:
            if any(r[x].strip() for x in ["longitudinal_long", "monconi", "stirrup_diameter_mm", "stirrup_spacing_cm"]):
                raise AssertionError(f"{key}: unbound base row contains reinforcement")

    # Source-only V-order IDs remain conflicts rather than current supports.
    g5_current = {sid for storey, sid in supports if storey == "G5"}
    source_only: set[tuple[str, str, str]] = set()
    for fam in families:
        if fam["order_id"].strip() != "V":
            continue
        for sid in fam["_ids"]:  # type: ignore[operator]
            if sid not in g5_current:
                source_only.add(("G5", sid, fam["family_id"]))

    if derived_current_conflicts | source_only != EXPECTED_CONFLICTS:
        raise AssertionError(
            f"derived conflicts changed: {derived_current_conflicts | source_only} != {EXPECTED_CONFLICTS}"
        )
    conflict_rows = read_csv(CONFLICT_PATH)
    actual_conflicts = {
        (r["storey_id"].strip(), r["support_id"].strip(), r["conflicting_family_id"].strip())
        for r in conflict_rows
    }
    if actual_conflicts != EXPECTED_CONFLICTS or len(conflict_rows) != 5:
        raise AssertionError("conflict register must preserve exactly the five known conflicts")

    recon = {r["claim_id"].strip(): r for r in read_csv(RECON_PATH)}
    if set(recon) != {"M1A-T7-IV-R01", "M1A-T7-IV-R02"}:
        raise AssertionError("unexpected IV reconciliation claim set")
    if recon["M1A-T7-IV-R01"]["reconciled_candidate"].strip() != "11;14":
        raise AssertionError("R01 must reconcile the duplicate special IV 30x45 family to candidate supports 11-14")
    if recon["M1A-T7-IV-R01"]["validation_state"].strip() != "SUPPORTED_CROSS_VALIDATED_NOT_DOC":
        raise AssertionError("R01 corrected identity must stay SUPPORTED, not DOC")
    if "RIF_USER_QUALIFIED" not in recon["M1A-T7-IV-R01"]["provenance"]:
        raise AssertionError("R01 must preserve the user's probable-refuso interpretation provenance")

    override_rows = read_csv(OVERRIDE_PATH)
    if len(override_rows) != 3:
        raise AssertionError("effective override must contain exactly G4 11,14,22")
    overrides: dict[tuple[str, str], dict[str, str]] = {}
    for o in override_rows:
        key = (o["storey_id"].strip(), o["support_id"].strip())
        if key in overrides:
            raise AssertionError(f"duplicate override {key}")
        overrides[key] = o
    if set(overrides) != {("G4", "11"), ("G4", "14"), ("G4", "22")}:
        raise AssertionError("override key set changed")

    for sid in ["11", "14"]:
        o = overrides[("G4", sid)]
        if o["effective_selected_family_id"].strip() != "T7-TR-01":
            raise AssertionError(f"G4 {sid}: special family override missing")
        if o["effective_binding_evidence_status"].strip() != "SUPPORTED":
            raise AssertionError(f"G4 {sid}: corrected identity must remain SUPPORTED")
        if o["reconciliation_claim_id"].strip() != "M1A-T7-IV-R01":
            raise AssertionError(f"G4 {sid}: wrong reconciliation claim")
        if sk(supports[("G4", sid)]["orientation"]) != sk(special["section_drawn_cm"]):
            raise AssertionError(f"G4 {sid}: special-family section not carpenteria-compatible")
        for ofield, ffield in [
            ("longitudinal_long", "longitudinal_long"),
            ("monconi", "monconi"),
            ("stirrup_diameter_mm", "stirrup_diameter_mm"),
            ("stirrup_spacing_cm", "stirrup_spacing_cm"),
        ]:
            if o[ofield].strip() != special[ffield].strip():
                raise AssertionError(f"G4 {sid}: override reinforcement differs from T7-TR-01")

    o22 = overrides[("G4", "22")]
    if o22["effective_selected_family_id"].strip() != "T7-IV-04":
        raise AssertionError("G4 22 must stay in ordinary IV 30x45 family")
    if o22["effective_binding_evidence_status"].strip() != "SUPPORTED":
        raise AssertionError("G4 22 conflict-resolved binding must remain SUPPORTED")
    if o22["reconciliation_claim_id"].strip() != "M1A-T7-IV-R02":
        raise AssertionError("G4 22 must cite R02")

    # Build effective family selection: base matrix plus explicit supported override.
    effective_selected: dict[tuple[str, str], str] = {}
    residuals: set[tuple[str, str]] = set()
    for key, row in matrix.items():
        selected = row["selected_family_id"].strip()
        if key in overrides:
            selected = overrides[key]["effective_selected_family_id"].strip()
        if selected:
            effective_selected[key] = selected
        else:
            residuals.add(key)
    if residuals != EXPECTED_RESIDUALS:
        raise AssertionError(f"effective residual set changed: {residuals}")
    if len(effective_selected) != 158:
        raise AssertionError(f"effective bound count {len(effective_selected)} != 158")

    # High-risk guards from the carpenteria-first rule.
    hard = {
        ("G2", "32"): "T7-II-02",
        ("G4", "9"): "T7-IV-02",
        ("G4", "16"): "T7-IV-02",
        ("G4", "11"): "T7-TR-01",
        ("G4", "14"): "T7-TR-01",
        ("G4", "22"): "T7-IV-04",
    }
    for key, fid in hard.items():
        if effective_selected.get(key) != fid:
            raise AssertionError(f"{key}: effective family {effective_selected.get(key)} != {fid}")
    for key in [("G1", "3"), ("G3", "9"), ("G3", "16")]:
        if key in effective_selected:
            raise AssertionError(f"{key}: must remain an explicit residual")
    for sid in ["a", "b", "c", "d"]:
        if ("G1", sid) in effective_selected:
            raise AssertionError(f"G1 {sid}: later addition must not receive historical TAV-07 reinforcement")
    if ("G5", "24") in effective_selected:
        raise AssertionError("G5 source-only 24 must not be created/bound")

    coverage = {r["storey_id"].strip(): r for r in read_csv(COVERAGE_PATH)}
    if set(coverage) != set(STOREY_ORDER):
        raise AssertionError("coverage storey set changed")
    for storey in STOREY_ORDER:
        keys = [k for k in supports if k[0] == storey]
        selected = {k: effective_selected[k] for k in keys if k in effective_selected}
        unbound = {sid for s, sid in keys if (s, sid) not in effective_selected}
        fam_counts = Counter(selected.values())
        row = coverage[storey]
        if int(row["current_support_count"]) != len(keys):
            raise AssertionError(f"{storey}: coverage support count mismatch")
        if int(row["bound_count"]) != len(selected):
            raise AssertionError(f"{storey}: coverage bound count mismatch")
        if int(row["unbound_count"]) != len(unbound) or ids(row["unbound_ids"]) != unbound:
            raise AssertionError(f"{storey}: coverage residual mismatch")
        if parse_family_counts(row["family_binding_counts"]) != dict(fam_counts):
            raise AssertionError(f"{storey}: effective family count mismatch")

    gate_rows = read_csv(GATE_PATH)
    if len(gate_rows) != 1:
        raise AssertionError("column binding gate must contain one row")
    gate = gate_rows[0]
    expected_metrics = {
        "total_current_support_storey_rows": 165,
        "bound_rows": 158,
        "unbound_rows": 7,
        "documented_conflict_rows": 5,
    }
    for field, value in expected_metrics.items():
        if int(gate[field]) != value:
            raise AssertionError(f"gate {field} changed")
    if gate["gate_status"].strip() != EXPECTED_GATE_STATUS:
        raise AssertionError("column binding gate status changed")

    print("M1A_COLUMN_CARPENTRY_FIRST_BINDING_V2 = PASS_WITH_WATCH")
    print("Current support-storey rows: 165")
    print("Effective bound: 158; explicit residuals: 7")
    print("Documented source/callout conflicts: 5")
    print("Supported IV reconciliations: G4 11,14 -> T7-TR-01; G4 22 -> T7-IV-04")
    print("Coverage: G1 33/38, G2 34/34, G3 32/34, G4 34/34, G5 25/25")
    print("WATCH: corrected 11-14 identity is SUPPORTED_CROSS_VALIDATED_NOT_DOC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
