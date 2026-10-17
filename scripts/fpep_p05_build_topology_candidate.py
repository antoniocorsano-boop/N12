#!/usr/bin/env python3
"""Build the FPEP P05 primary-topology candidate ledger.

P05 deliberately does not create canonical foundation members. It converts
Reader-A graphical-continuity observations into traceable candidate corridors,
using only documented support identifiers from P04. Exact two-label corridors
are retained as PAIR_CANDIDATE rows but remain WITHHELD until P06 performs a
source-local cross-validation. Multi-label/jog corridors remain unresolved.

Forbidden legacy geometry, counts, M0-G, PT and TAV-01A are never read.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PIPELINE_ID = "N12_FPEP_FOUNDATION_PRIMARY_EVIDENCE_PIPELINE"
WORK_ITEM_ID = "FPEP-P05-TOPOLOGY-CANDIDATE"
AGENT_ROLE = "FOUNDATION_TOPOLOGY_BUILDER"
TARGET = "analysis/fpep/FPEP_PRIMARY_TOPOLOGY_CANDIDATE_v1.csv"
INBOX = "automation/inbox/N12_FOUNDATION_AGENT_RESULT.json"

# Immutable P01 identity carried only as provenance metadata. P05 never opens
# or semantically reads the source PDF.
SOURCE_ID = "TAV-01S"
SOURCE_PATH = "archive/originali-alta-risoluzione:archive/documentazione_originaria/tavola1-2.pdf"
SOURCE_BLOB = "64b842fa03b3aa7437e80d2bce90406a66f73827"
SOURCE_SHA256 = "abd6061c305f2e7222f04659f519d7ee73ed0759b815ac994ff66215f060fec8"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def ordered_documented_labels(text: str, identifiers: set[str]) -> list[str]:
    # Match alphanumeric label-like tokens, then retain only identifiers that
    # were already documented by P04. This prevents arbitrary numeric text
    # (dimensions, OCR noise, legacy counts) from becoming endpoints.
    tokens = re.findall(r"(?<![A-Za-z0-9])(?:\d+bis|\d+|[A-Za-z])(?![A-Za-z0-9])", text)
    output: list[str] = []
    for token in tokens:
        normalized = token.lower() if token.lower() in identifiers else token
        if normalized in identifiers and (not output or output[-1] != normalized):
            output.append(normalized)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--reader-a", default="analysis/fpep/FPEP_READER_A_OBSERVATIONS_v1.csv")
    parser.add_argument("--reader-b", default="analysis/fpep/FPEP_READER_B_OBSERVATIONS_v1.csv")
    parser.add_argument("--metric-claims", default="analysis/fpep/FPEP_METRIC_CLAIMS_v1.csv")
    parser.add_argument("--closure-audit", default="analysis/fpep/FPEP_METRIC_CLOSURE_AUDIT_v1.csv")
    parser.add_argument("--output", default=TARGET)
    parser.add_argument("--result", default=INBOX)
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    paths = {
        "reader_a": root / args.reader_a,
        "reader_b": root / args.reader_b,
        "metric_claims": root / args.metric_claims,
        "closure_audit": root / args.closure_audit,
    }
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"P05 missing allowed input {name}: {path}")

    reader_a = read_csv(paths["reader_a"])
    # Reader B is loaded only to attest that the allowed independent read is
    # present; P05 does not manufacture semantic continuity from OCR tokens.
    reader_b = read_csv(paths["reader_b"])
    metric_claims = read_csv(paths["metric_claims"])
    closure_rows = read_csv(paths["closure_audit"])

    id_claims = {
        row["governing_value"]: row
        for row in metric_claims
        if row.get("claim_class") == "SUPPORT_IDENTIFIER"
        and row.get("governing_state") == "DOC"
        and row.get("governing_value")
    }
    identifiers = set(id_claims)

    continuity_rows = [
        row for row in reader_a
        if row.get("semantic_class") == "GRAPHICAL_CONTINUITY"
        and row.get("evidence_state") == "DOC"
    ]
    if not continuity_rows:
        raise SystemExit("P05 found no DOC graphical-continuity observations in Reader A")

    conflict_claims_by_anchor: dict[str, list[str]] = {}
    for row in metric_claims:
        if "CONFLICT" in (row.get("comparison_status") or ""):
            conflict_claims_by_anchor.setdefault(row.get("evidence_anchor", ""), []).append(row["claim_id"])

    closure_watch_by_anchor: dict[str, list[str]] = {}
    for row in closure_rows:
        status = row.get("status", "")
        if "CONFLICT" in status or "AMBIGUOUS" in status:
            for anchor in (row.get("evidence_scope") or "").split("|"):
                if anchor:
                    closure_watch_by_anchor.setdefault(anchor, []).append(row["closure_id"])

    candidates: list[dict[str, str]] = []
    pair_count = 0
    unresolved_count = 0

    for index, observation in enumerate(continuity_rows, start=1):
        anchor = observation.get("evidence_anchor", "")
        labels = ordered_documented_labels(observation.get("raw_value", ""), identifiers)
        metric_watch = sorted(set(conflict_claims_by_anchor.get(anchor, []) + closure_watch_by_anchor.get(anchor, [])))

        endpoint_a = ""
        endpoint_b = ""
        endpoint_a_claim = ""
        endpoint_b_claim = ""

        if len(labels) == 2:
            pair_count += 1
            candidate_class = "PAIR_CANDIDATE"
            endpoint_a, endpoint_b = labels
            endpoint_a_claim = id_claims[endpoint_a]["claim_id"]
            endpoint_b_claim = id_claims[endpoint_b]["claim_id"]
            cross_state = "REQUIRES_P06_SOURCE_LOCAL_CROSS_VALIDATION"
            promotion = "WITHHELD_NOT_CROSS_VALIDATED"
            note = (
                "Exactly two documented labels occur in the Reader-A continuity corridor. "
                "This is not yet a member: P06 must verify that the structural contour actually attaches to both labeled supports."
            )
        else:
            unresolved_count += 1
            if "toward" in observation.get("raw_value", "").lower() or "jog" in observation.get("raw_value", "").lower():
                candidate_class = "BRANCH_OR_JOG_CORRIDOR_UNRESOLVED"
            else:
                candidate_class = "MULTI_LABEL_CORRIDOR_UNRESOLVED"
            cross_state = "REQUIRES_P06_CORRIDOR_DECOMPOSITION"
            promotion = "WITHHELD_AMBIGUOUS_ENDPOINT_PAIRING"
            note = (
                "Continuity is directly observed, but the corridor contains more than two documented labels or an unresolved jog. "
                "No consecutive-pair or endpoint pairing is inferred at P05."
            )

        candidates.append(
            {
                "candidate_id": f"P05-CAND-{index:03d}",
                "candidate_class": candidate_class,
                "labels_sequence": "|".join(labels),
                "endpoint_a": endpoint_a,
                "endpoint_b": endpoint_b,
                "endpoint_a_claim": endpoint_a_claim,
                "endpoint_b_claim": endpoint_b_claim,
                "continuity_obs_id": observation["obs_id"],
                "evidence_anchor": anchor,
                "continuity_state": observation["evidence_state"],
                "metric_watch_claims": "|".join(metric_watch),
                "cross_validation_state": cross_state,
                "promotion_state": promotion,
                "blocking": "false",
                "note": note,
            }
        )

    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "candidate_id",
        "candidate_class",
        "labels_sequence",
        "endpoint_a",
        "endpoint_b",
        "endpoint_a_claim",
        "endpoint_b_claim",
        "continuity_obs_id",
        "evidence_anchor",
        "continuity_state",
        "metric_watch_claims",
        "cross_validation_state",
        "promotion_state",
        "blocking",
        "note",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)

    run_id = "FPEP-P05-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result = {
        "schema_version": "1.0",
        "pipeline_id": PIPELINE_ID,
        "run_id": run_id,
        "work_item_id": WORK_ITEM_ID,
        "stage_id": "P05",
        "agent_role": AGENT_ROLE,
        "decision": "PASS_WITH_WATCH",
        "semantic_gate": "WATCH",
        "input_artifacts": [
            {"path": args.reader_a, "sha256": sha256_file(paths["reader_a"]), "authority": "PRIMARY_READER_OBSERVATIONS", "status": "CURRENT"},
            {"path": args.reader_b, "sha256": sha256_file(paths["reader_b"]), "authority": "INDEPENDENT_READER_OBSERVATIONS", "status": "CURRENT"},
            {"path": args.metric_claims, "sha256": sha256_file(paths["metric_claims"]), "authority": "METRIC_CLAIMS", "status": "CURRENT"},
            {"path": args.closure_audit, "sha256": sha256_file(paths["closure_audit"]), "authority": "METRIC_CLOSURE_AUDIT", "status": "CURRENT"},
        ],
        "primary_sources": [
            {
                "source_id": SOURCE_ID,
                "path": SOURCE_PATH,
                "git_blob_sha": SOURCE_BLOB,
                "sha256": SOURCE_SHA256,
                "evidence_anchor": "P03 graphical-continuity observations and P04 identifier claims; source PDF not reopened by P05",
            }
        ],
        "target_outputs": [args.output],
        "provenance_summary": {
            "continuity_corridors": len(candidates),
            "pair_candidates": pair_count,
            "unresolved_corridors": unresolved_count,
            "promoted_members": 0,
            "coordinates_created": 0,
            "reader_b_semantic_continuity_invented": 0,
            "output_sha256": sha256_file(output_path),
        },
        "residuals": [
            {
                "residual_id": "P05-R001",
                "claim_id": "P05-PAIR-CANDIDATE-ENDPOINT-ATTACHMENT",
                "blocking": False,
                "reason": "Exactly-two-label corridors are not yet cross-validated at the actual structural contour/support attachment.",
                "required_evidence": "P06 source-local reread on each pair-candidate evidence anchor before any member promotion.",
            },
            {
                "residual_id": "P05-R002",
                "claim_id": "P05-MULTI-LABEL-CORRIDOR-DECOMPOSITION",
                "blocking": False,
                "reason": "Multi-label and jog corridors do not uniquely define endpoint pairs.",
                "required_evidence": "P06 local continuity tracing; do not apply consecutive-label or nearest-neighbour assumptions.",
            },
            {
                "residual_id": "P05-R003",
                "claim_id": "P04-METRIC-WATCH-DEPENDENCIES",
                "blocking": False,
                "reason": "P04 reader/closure conflicts remain visible and were not used to create or repair topology.",
                "required_evidence": "P06 adjudication of the minimum conflicting source regions before P07 promotion.",
            },
        ],
        "audit_paths": [args.output],
        "information_barrier_attestation": {
            "forbidden_context_not_used": True,
            "legacy_target_counts_not_used_before_primary_gate": True,
            "downstream_model_not_used_as_primary_evidence": True,
            "majority_vote_not_used_for_authority": True,
        },
        "builder_scope_attestation": {
            "existing_foundation_topology_used": False,
            "legacy_support_member_counts_used": False,
            "M0G_geometry_used": False,
            "PT_master_coordinates_used": False,
            "TAV01A_reinforcement_groups_used": False,
            "historical_calculation_topology_used": False,
            "nearest_support_rule_used": False,
            "two_nearby_supports_imply_member_rule_used": False,
            "members_promoted": 0,
        },
        "notes": [
            "P05 is a candidate ledger, not a canonical member list.",
            "Documented endpoint identifiers are necessary but not sufficient for a member.",
            "Reader B lacks semantic contour classification; P05 therefore does not claim dual-reader continuity agreement.",
            "P06 is the first stage allowed to reopen P02 HiRes evidence to adjudicate the candidate attachments and ambiguous corridors."
        ],
    }

    result_path = root / args.result
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": run_id, "decision": result["decision"], "pair_candidates": pair_count, "unresolved_corridors": unresolved_count, "promoted_members": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
