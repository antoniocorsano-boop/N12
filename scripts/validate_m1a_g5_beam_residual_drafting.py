from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data" / "canonical"


def read_csv(name: str):
    with (CANON / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


roof = read_csv("M1A_TAV06A_ROOF_GROUP_INDEX_v1.csv")
coverage = read_csv("M1A_BEAM_REINFORCEMENT_SOURCE_COVERAGE_CURRENT_v1.csv")
audit = read_csv("M1A_G5_BEAM_RESIDUAL_DRAFTING_AUDIT_v1.csv")
gate = read_csv("M1A_G5_BEAM_RESIDUAL_DRAFTING_GATE_v1.csv")
sections = read_csv("M1S_G5_BEAM_SECTIONS_CURRENT_v1.csv")
eq_gate = read_csv("M1A_BEAM_REINFORCEMENT_EQUIVALENCE_GATE_v1.csv")
logic = read_csv("M1A_BEAM_REINFORCEMENT_DRAFTING_LOGIC_CURRENT_v1.csv")

require(len(roof) == 6, f"expected six indexed TAV06A groups, got {len(roof)}")
by_group = {r["group_id"]: r for r in roof}
require(set(by_group) == {"T6A-G01","T6A-G02","T6A-G03","T6A-G04","T6A-G05","T6A-G06"}, f"unexpected TAV06A group set: {sorted(by_group)}")

g06 = by_group["T6A-G06"]
require(g06["evidence_status"] == "DOC", "T6A-G06 must remain DOC")
require(g06["binding_status"] == "DIRECT_TOPOLOGY_MATCH", "T6A-G06 must remain direct")
require(g06["section_cm"] == "30x50", "T6A-G06 section changed")
require(g06["stirrups"] == "phi6/15", "T6A-G06 stirrups changed")
require({s.strip() for s in g06["drawn_sequences"].split(";")} == {"25-26-27", "28-29-30"}, "T6A-G06 sequences changed")
require({s.strip() for s in g06["canonical_member_ids"].split(";")} == {"G5-B029","G5-B030","G5-B034","G5-B035"}, "T6A-G06 direct members changed")

cov = next(r for r in coverage if r["storey_id"] == "G5")
require(int(cov["ordinary_beam_count"]) == 36, "G5 beam population changed")
require(int(cov["direct_group_source_covered_count"]) == 19, "G5 direct coverage must be 19")
require(int(cov["uncovered_count"]) == 17, "G5 residual count must be 17")
expected_residuals = {x.strip() for x in cov["uncovered_source_member_ids"].split(";") if x.strip()}
require(len(expected_residuals) == 17, "G5 coverage residual list must contain 17 unique ids")
require({r["member_id"] for r in audit} == expected_residuals, "G5 residual audit must exactly match coverage residual set")

sec = {r["beam_id"]: r for r in sections}
for r in audit:
    mid = r["member_id"]
    require(mid in sec, f"missing M1-S section for {mid}")
    require(r["section_cm"] == sec[mid]["section_cm"], f"audit section mismatch for {mid}")
    require(r["numeric_reinforcement_status"] == "ND", f"residual numerical reinforcement promoted for {mid}")
    require(r["binding_decision"] in {"KEEP_RESIDUAL", "DO_NOT_ABSORB_INTO_PAIRED_RUN"}, f"unexpected binding decision for {mid}")

# Critical semantic exclusions.
for mid in ("G5-B031", "G5-B032", "G5-B033"):
    row = next(r for r in audit if r["member_id"] == mid)
    require(row["residual_class"] == "TRANSVERSE_CONNECTOR_BETWEEN_HOMOLOGOUS_T6A_G06_RUNS", f"wrong G06 crosslink class for {mid}")
    require(row["binding_decision"] == "DO_NOT_ABSORB_INTO_PAIRED_RUN", f"G06 transverse connector absorbed for {mid}")

for mid in ("G5-B008", "G5-B020"):
    row = next(r for r in audit if r["member_id"] == mid)
    require("CANDIDATE" in row["residual_class"], f"5-13-21 candidate semantics missing for {mid}")
    require(row["binding_decision"] == "KEEP_RESIDUAL", f"5-13-21 candidate improperly bound for {mid}")

b017 = next(r for r in audit if r["member_id"] == "G5-B017")
require(b017["residual_class"] == "IMPLUVIO_SPECIAL_UNBOUND", "B017 impluvio class changed")
require(b017["binding_decision"] == "KEEP_RESIDUAL", "B017 was improperly bound")
require(by_group["T6A-G03"]["binding_status"] == "UNBOUND_TO_CANONICAL_MEMBER", "T6A-G03 unexpectedly bound")

sem = next(r for r in logic if r["rule_id"] == "M1A-BDL-010")
require(sem["evidence_status"] == "RIF_USER_QUALIFIED_CROSSCHECKED", "homologous-travate semantics provenance changed")
rec = next(r for r in logic if r["rule_id"] == "M1A-BDL-011")
require(rec["evidence_status"] == "DOC", "direct T6A-G06 recovery rule must remain DOC")

metrics = {r["metric"]: r["actual"] for r in gate}
expected = {
    "tav06a_indexed_groups":"6",
    "g5_ordinary_beams":"36",
    "g5_direct_source_covered":"19",
    "g5_direct_source_residuals":"17",
    "recovered_t6a_g06_direct_members":"4",
    "g5_residual_numeric_reinforcement_promoted":"0",
    "candidate_5_13_21_bound_members":"0",
    "t6a_g06_transverse_connectors_absorbed":"0",
    "b017_bound_to_t6a_g03":"NO",
    "global_direct_beam_coverage":"152",
    "global_effective_scheme_coverage":"155",
    "gate_state":"PASS_G5_DIRECT_19_OF_36_WITH_17_CLASSIFIED_RESIDUALS",
}
for key, val in expected.items():
    require(metrics.get(key) == val, f"gate metric {key}: {metrics.get(key)!r} != {val!r}")

eq = {r["metric"]: r["value"] for r in eq_gate}
require(eq["direct_group_source_covered_total"] == "152", "global direct coverage mismatch")
require(eq["effective_scheme_bound_total"] == "155", "global effective coverage mismatch")
require(eq["remaining_unbound_total"] == "77", "global unbound count mismatch")

print("PASS M1-A G5 residual drafting: 6 TAV06A groups, 19/36 direct, 17 residuals classified, zero unsafe numeric promotions")
