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


audit = read_csv("M1A_50X20_REINFORCEMENT_PRECEDENT_AUDIT_v1.csv")
transfer_gate = read_csv("M1A_50X20_REINFORCEMENT_TRANSFER_GATE_v1.csv")
coverage = read_csv("M1A_BEAM_REINFORCEMENT_SOURCE_COVERAGE_CURRENT_v1.csv")
equivalence_gate = read_csv("M1A_BEAM_REINFORCEMENT_EQUIVALENCE_GATE_v1.csv")

# The direct-precedent set is closed and source-specific. Section equality alone is never a transfer rule.
expected_precedents = {
    "M1A-50X20-P01": ("TAV-02A", "T2A-G07"),
    "M1A-50X20-P02": ("TAV-034A", "T34-G03"),
    "M1A-50X20-P03": ("TAV-05A", "T5A-G03"),
}
precedents = {r["precedent_id"]: r for r in audit if r["precedent_id"] in expected_precedents}
require(set(precedents) == set(expected_precedents), f"50x20 precedent set changed: {sorted(precedents)}")
for pid, (source_id, source_group) in expected_precedents.items():
    row = precedents[pid]
    require(row["source_id"] == source_id, f"wrong source for {pid}: {row['source_id']}")
    require(row["source_group"] == source_group, f"wrong source group for {pid}: {row['source_group']}")
    require(row["transfer_decision"] == "DO_NOT_TRANSFER_NUMERIC_REINFORCEMENT", f"unsafe 50x20 transfer enabled for {pid}")
    require(row["evidence_status"].startswith("DOC"), f"non-documentary precedent status for {pid}")

# The recurring connector class is an omission/source-scope pattern, not an authored reinforcement family.
gap = next((r for r in audit if r["precedent_id"] == "M1A-50X20-GAP"), None)
require(gap is not None, "missing M1A-50X20-GAP row")
require(gap["evidence_status"] == "INF_STRONG_DRAFTING_CLASS_PATTERN", "50x20 gap-class provenance changed")
require(gap["transfer_decision"] == "NUMERIC_REINFORCEMENT_REMAINS_ND", "50x20 numeric reinforcement was promoted")
positions = [p.strip() for p in gap["documented_longitudinal_signature"].split(";") if p.strip()]
require(len(positions) == 13, f"expected 13 recurring 50x20 connector positions, found {len(positions)}")
require(len(set(positions)) == 13, "duplicate recurring 50x20 connector position")

# Global coverage may advance through unrelated new direct primary evidence; the 50x20 boundary itself must remain unchanged.
ordinary_total = sum(int(r["ordinary_beam_count"]) for r in coverage)
direct_total = sum(int(r["direct_group_source_covered_count"]) for r in coverage)
require(ordinary_total == 232, f"ordinary beam total changed: {ordinary_total}")
require(direct_total == 152, f"global direct ordinary-beam coverage mismatch: {direct_total}")

eq_metrics = {r["metric"]: r["value"] for r in equivalence_gate}
require(eq_metrics["effective_scheme_bound_total"] == "155", "effective scheme-bound beam count mismatch")
require(eq_metrics["50x20_numeric_reinforcement"] == "ND", "broader beam-equivalence gate resolves 50x20 numerically")

checks = {r["metric"]: r for r in transfer_gate}
expected_actuals = {
    "direct_local_precedents": "3",
    "precedents_authorizing_numeric_transfer": "0",
    "generic_transferable_primary_source_mechanism": "NO",
    "recurring_50x20_connector_positions": "13",
    "new_exact_bindings_from_precedent_transfer": "0",
    "direct_group_source_covered_ordinary_beams": "152",
    "effective_scheme_bound_ordinary_beams": "155",
    "50x20_numeric_reinforcement_status": "ND",
    "reopen_policy": "NEW_EXPLICIT_PRIMARY_GENERIC_50X20_CONNECTOR_DETAIL_OR_EXACT_MEMBER_BINDING",
    "gate_state": "PASS_50X20_PRECEDENTS_LOCAL_ONLY_WITH_13_RESIDUAL_WATCH",
}
for metric, expected in expected_actuals.items():
    require(metric in checks, f"missing transfer-gate metric {metric}")
    require(checks[metric]["actual"] == expected, f"wrong actual for {metric}: {checks[metric]['actual']} != {expected}")
    require(checks[metric]["expected"] == expected, f"wrong expected for {metric}: {checks[metric]['expected']} != {expected}")

require(checks["generic_transferable_primary_source_mechanism"]["status"] == "PASS", "generic-transfer absence not gated")
require(checks["new_exact_bindings_from_precedent_transfer"]["status"] == "PASS", "zero-transfer boundary not gated")
require(checks["gate_state"]["status"] == "PASS_WITH_WATCH", "50x20 closure gate must retain residual watch")

print("PASS M1-A 50x20 transfer closure unchanged; global beam coverage now 152 direct / 155 effective after independent TAV06A recovery")
