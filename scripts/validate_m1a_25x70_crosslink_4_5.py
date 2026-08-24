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


audit = read_csv("M1A_25X70_CROSSLINK_4_5_AUDIT_v1.csv")
gate = read_csv("M1A_25X70_CROSSLINK_4_5_GATE_v1.csv")
logic = read_csv("M1A_BEAM_REINFORCEMENT_DRAFTING_LOGIC_CURRENT_v1.csv")
t34 = read_csv("M1A_TAV034A_BEAM_GROUP_INDEX_v1.csv")
t5 = read_csv("M1A_TAV05A_BEAM_GROUP_INDEX_v1.csv")
t2 = read_csv("M1A_TAV02A_BEAM_GROUP_INDEX_v1.csv")
conn = read_csv("M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv")
coverage = read_csv("M1A_BEAM_REINFORCEMENT_SOURCE_COVERAGE_CURRENT_v1.csv")
eq_gate = read_csv("M1A_BEAM_REINFORCEMENT_EQUIVALENCE_GATE_v1.csv")

# The qualified semantic rule must remain separate from DOC source facts.
sem = next((r for r in logic if r["rule_id"] == "M1A-BDL-010"), None)
require(sem is not None, "missing homologous-travate semantic rule M1A-BDL-010")
require(sem["rule_type"] == "HOMOLOGOUS_TRAVATE_LABEL_SEMANTICS", "wrong M1A-BDL-010 rule type")
require(sem["evidence_status"] == "RIF_USER_QUALIFIED_CROSSCHECKED", "qualified semantics improperly promoted or weakened")
require("not an implicit transverse beam 4-5" in sem["observed_drafting_behavior"], "4-5 semantic exclusion missing")

# Source schedules show homologous longitudinal sequences and do not directly bind cross-link 4-5.
t34_g01 = next(r for r in t34 if r["group_id"] == "T34-G01")
require(t34_g01["drawn_sequence_a"] == "4-3-2-1", "T34-G01 sequence A changed")
require(t34_g01["drawn_sequence_b"] == "5-6-7-8", "T34-G01 sequence B changed")
require("G2-B004" not in t34_g01["g2_member_ids"], "G2 4-5 cross-link incorrectly absorbed into T34-G01")
require("G3-B004" not in t34_g01["g3_member_ids"], "G3 4-5 cross-link incorrectly absorbed into T34-G01")

t5_g01 = next(r for r in t5 if r["group_id"] == "T5A-G01")
require(t5_g01["drawn_sequence_a"] == "4-3-2-1", "T5A-G01 sequence A changed")
require(t5_g01["drawn_sequence_b"] == "5-6-7-8", "T5A-G01 sequence B changed")
require("G4-B004" not in t5_g01["g4_member_ids"], "G4 4-5 cross-link incorrectly absorbed into T5A-G01")

t2_g01 = next(r for r in t2 if r["group_id"] == "T2A-G01")
require(t2_g01["drawn_sequence_a"] == "4-3-2-1", "T2A-G01 sequence A changed")
require(t2_g01["drawn_sequence_b"] == "5-6-7-8", "T2A-G01 sequence B changed")
require("B-013" not in t2_g01["canonical_member_ids"], "G1 4-5 cross-link incorrectly absorbed into T2A-G01")

# Frozen physical geometry: three repeated 4-5 cross-links are all 25x70 and 1.50 m.
by_source = {r["source_member_id"]: r for r in conn}
expected_members = {
    "G2-B004": "G2",
    "G3-B004": "G3",
    "G4-B004": "G4",
}
for member_id, storey in expected_members.items():
    require(member_id in by_source, f"missing frozen member {member_id}")
    row = by_source[member_id]
    require(row["storey_id"] == storey, f"wrong storey for {member_id}")
    require(row["support_i"] == "4" and row["support_j"] == "5", f"wrong supports for {member_id}")
    require(row["section_cm"] == "25x70", f"wrong section for {member_id}: {row['section_cm']}")
    require(abs(float(row["geometric_length_m"]) - 1.5) < 1e-6, f"wrong length for {member_id}")

# Audit must retain exactly three rows and zero numeric transfer.
require({r["member_id"] for r in audit} == set(expected_members), "unexpected 4-5 audit member set")
for r in audit:
    require(r["direct_group_binding"] == "NO", f"direct binding created for {r['member_id']}")
    require(r["transfer_decision"] == "NUMERIC_REINFORCEMENT_REMAINS_ND", f"numeric transfer enabled for {r['member_id']}")
    require("RIF_USER_QUALIFIED_SEMANTICS" in r["evidence_status"], f"semantic provenance missing for {r['member_id']}")

# Broader coverage is frozen: this closure must not increase direct/effective counts.
ordinary_total = sum(int(r["ordinary_beam_count"]) for r in coverage)
direct_total = sum(int(r["direct_group_source_covered_count"]) for r in coverage)
require(ordinary_total == 232, f"ordinary beam total changed: {ordinary_total}")
require(direct_total == 148, f"direct beam coverage changed: {direct_total}")
eq_metrics = {r["metric"]: r["value"] for r in eq_gate}
require(eq_metrics["effective_scheme_bound_total"] == "151", "effective scheme-bound count changed")

metrics = {r["metric"]: r for r in gate}
expected_actuals = {
    "current_g2_g3_g4_crosslinks_4_5": "3",
    "crosslinks_section_25x70_and_length_1_50": "3",
    "direct_armature_group_bindings": "0",
    "independent_lower_level_same_drafting_behavior": "YES",
    "new_exact_bindings_from_longitudinal_scheme_transfer": "0",
    "numeric_reinforcement_status": "ND",
    "direct_group_source_covered_ordinary_beams": "148",
    "effective_scheme_bound_ordinary_beams": "151",
    "reopen_policy": "NEW_EXPLICIT_PRIMARY_4_5_CROSSLINK_DETAIL_OR_EXACT_MEMBER_BINDING",
    "gate_state": "PASS_25X70_CROSSLINK_4_5_SOURCE_OMISSION_WITH_3_LEVEL_ND_WATCH",
}
for metric, expected in expected_actuals.items():
    require(metric in metrics, f"missing gate metric {metric}")
    require(metrics[metric]["expected"] == expected, f"wrong expected for {metric}")
    require(metrics[metric]["actual"] == expected, f"wrong actual for {metric}")

require(metrics["gate_state"]["status"] == "PASS_WITH_WATCH", "4-5 closure gate must retain ND watch")

print(
    "PASS M1-A 25x70 cross-link 4-5: homologous-travate semantics preserved as RIF_USER_QUALIFIED; "
    "3 physical 4-5 members remain outside longitudinal G01 schedules and numerically ND"
)
