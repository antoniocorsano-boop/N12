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


coverage = read_csv("M1A_BEAM_REINFORCEMENT_SOURCE_COVERAGE_CURRENT_v1.csv")
inferred = read_csv("M1A_BEAM_REINFORCEMENT_INFERRED_BINDINGS_CURRENT_v1.csv")
audit50 = read_csv("M1A_50X20_REINFORCEMENT_PRECEDENT_AUDIT_v1.csv")
gate = read_csv("M1A_BEAM_REINFORCEMENT_EQUIVALENCE_GATE_v1.csv")
connectivity = read_csv("M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv")
t34 = read_csv("M1A_TAV034A_BEAM_GROUP_INDEX_v1.csv")
t5 = read_csv("M1A_TAV05A_BEAM_GROUP_INDEX_v1.csv")

# Frozen direct-coverage baseline must not be silently rewritten by equivalence inference.
ordinary_total = sum(int(r["ordinary_beam_count"]) for r in coverage)
direct_total = sum(int(r["direct_group_source_covered_count"]) for r in coverage)
direct_uncovered = sum(int(r["uncovered_count"]) for r in coverage)
require(ordinary_total == 232, f"ordinary beam total changed: {ordinary_total}")
require(direct_total == 148, f"direct source coverage changed: {direct_total}")
require(direct_uncovered == 84, f"direct uncovered total changed: {direct_uncovered}")

g4_cov = next(r for r in coverage if r["storey_id"] == "G4")
require(int(g4_cov["direct_group_source_covered_count"]) == 31, "G4 direct coverage must remain 31")
require(int(g4_cov["uncovered_count"]) == 17, "G4 direct uncovered count must remain 17")

# Only the three omitted companion spans are admitted by this gate.
expected = {"G4-B036", "G4-B041", "G4-B046"}
actual = {r["member_id"] for r in inferred}
require(actual == expected, f"unexpected inferred member set: {sorted(actual)}")
for r in inferred:
    require(r["storey_id"] == "G4", f"non-G4 inferred binding: {r['member_id']}")
    require(r["section_cm"] == "25x70", f"wrong section for {r['member_id']}")
    require(r["same_level_source_group"] == "T5A-G07", f"wrong same-level source group for {r['member_id']}")
    require(r["evidence_status"] == "INF_STRONG_DRAFTING_RULE", f"wrong provenance for {r['member_id']}")
    require(r["binding_scope"] == "FAMILY_TOPOLOGY_COUNT_DIAMETER_ONLY", f"binding scope too broad for {r['member_id']}")
    require(r["numeric_bar_length_status"].startswith("ND_"), f"numeric lengths were improperly promoted for {r['member_id']}")
    require(r["direct_source_coverage_status"] == "NO", f"inferred binding incorrectly marked direct for {r['member_id']}")

# Source-authored precedent: lower shared sheet explicitly pairs the two runs; G4 sheet draws only the base run.
t34_g07 = next(r for r in t34 if r["group_id"] == "T34-G07")
require(t34_g07["drawn_sequence_a"] == "19-25-28-31", "T34-G07 base run changed")
require(t34_g07["drawn_sequence_b"] == "22'-27-30-33", "T34-G07 companion run changed")
require(t34_g07["evidence_status"] == "DOC", "T34-G07 pairing must remain documentary")

t5_g07 = next(r for r in t5 if r["group_id"] == "T5A-G07")
require(t5_g07["drawn_sequence_a"] == "19-25-28-31", "T5A-G07 base run changed")
require(not t5_g07["drawn_sequence_b"].strip(), "T5A-G07 must not be rewritten as direct paired coverage")

# Cross-storey geometry and section check. Tiny G2/G4 face-length difference on B036 is allowed; topology is unchanged.
conn = {r["source_member_id"]: r for r in connectivity}
expected_lengths = {
    "G4-B030": 3.7818,
    "G4-B039": 3.0500,
    "G4-B044": 4.3000,
    "G4-B036": 1.7000,
    "G4-B041": 2.7232,
    "G4-B046": 3.9655,
    "G2-B036": 1.6750,
    "G2-B041": 2.7232,
    "G2-B046": 3.9655,
}
for member_id, target in expected_lengths.items():
    require(member_id in conn, f"missing connectivity member {member_id}")
    row = conn[member_id]
    require(row["section_cm"] == "25x70", f"section mismatch for {member_id}: {row['section_cm']}")
    length = float(row["geometric_length_m"])
    require(abs(length - target) < 1e-4, f"length mismatch for {member_id}: {length} != {target}")

# The 50x20 search class is explicitly kept numeric-ND because current direct precedents have role/topology mismatch.
gap = next(r for r in audit50 if r["precedent_id"] == "M1A-50X20-GAP")
require(gap["evidence_status"] == "INF_STRONG_DRAFTING_CLASS_PATTERN", "50x20 class provenance changed")
require(gap["transfer_decision"] == "NUMERIC_REINFORCEMENT_REMAINS_ND", "50x20 numeric reinforcement was improperly promoted")
for pid in ("M1A-50X20-P01", "M1A-50X20-P02", "M1A-50X20-P03"):
    row = next(r for r in audit50 if r["precedent_id"] == pid)
    require(row["transfer_decision"] == "DO_NOT_TRANSFER_NUMERIC_REINFORCEMENT", f"unsafe 50x20 transfer enabled for {pid}")

metrics = {r["metric"]: r["value"] for r in gate}
require(metrics["ordinary_beams_total"] == "232", "gate ordinary total mismatch")
require(metrics["direct_group_source_covered_total"] == "148", "gate direct coverage mismatch")
require(metrics["g4_inferred_companion_members"] == "3", "gate inferred count mismatch")
require(metrics["effective_scheme_bound_total"] == "151", "gate effective count mismatch")
require(metrics["remaining_unbound_total"] == "81", "gate remaining count mismatch")
require(metrics["g4_effective_bound"] == "34", "gate G4 effective count mismatch")
require(metrics["g4_remaining_unbound"] == "14", "gate G4 remaining count mismatch")
require(metrics["50x20_numeric_reinforcement"] == "ND", "gate improperly resolves 50x20 numeric reinforcement")
require(
    metrics["gate_status"] == "PASS_G4_COMPANION_FAMILY_BINDING_WITH_50X20_NUMERIC_WATCH",
    "gate status mismatch",
)

print("PASS M1-A beam equivalence: 148 direct + 3 INF_STRONG = 151/232; G4 residuals harmonized to 14; 50x20 numeric reinforcement remains ND")
