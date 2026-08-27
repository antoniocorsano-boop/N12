#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ROOT / "data/canonical/CEW_PROMOTION_TARGET_REGISTRY_v1.csv"
FIXTURES = ROOT / "analysis/cew/CEW_F7_PROMOTION_POLICY_FIXTURES_v1.json"
PAYLOAD_CONTRACT = ROOT / "automation/CEW_F7_PATCH_PAYLOAD_CONTRACT_v1.json"

# B1 natural-language compatibility is deliberately narrow: CEW extracts only
# direction, count and diameter when both directional clauses are explicit.
# Prefix/suffix prose is allowed; missing semantics are never inferred.
DIRECTIONAL_REINFORCEMENT = re.compile(
    r"(?<!\d)(\d+)\s*(?:[ΦØφ]|[fF]|phi)\s*(\d+)\s+superiori\s*(?:\+|\be\b)\s*"
    r"(\d+)\s*(?:[ΦØφ]|[fF]|phi)\s*(\d+)\s+inferiori\b",
    re.IGNORECASE,
)


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def stable_id(obj: dict) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def reinforcement_payload(observation: str) -> tuple[dict | None, str | None]:
    matches = list(DIRECTIONAL_REINFORCEMENT.finditer(observation))
    if len(matches) != 1:
        return None, "SEMANTIC_EXPLICIT_DIRECTIONAL_CLAUSES_REQUIRED"
    match = matches[0]
    uc, ud, lc, ld = (int(x) for x in match.groups())
    if min(uc, ud, lc, ld) <= 0:
        return None, "SEMANTIC_DIRECTIONAL_VALUES_MUST_BE_POSITIVE"
    return {
        "kind": "REINFORCEMENT_ASSERTION",
        "raw_human_observation": observation,
        "parser_policy": "EXPLICIT_DIRECTIONAL_REINFORCEMENT_NATURAL_TEXT_V2",
        "upper": {"count": uc, "diameter_mm": ud},
        "lower": {"count": lc, "diameter_mm": ld},
        "directional_separation_preserved": True,
        "semantic_extraction": "EXPLICIT_TOKENS_ONLY_NO_FREE_TEXT_INFERENCE",
    }, None


def semantic_payload_for(evaluation: dict, target: dict) -> tuple[dict | None, str | None]:
    if target["target_class"] != "REINFORCEMENT_ASSERTION":
        return None, "SEMANTIC_TARGET_PAYLOAD_CONTRACT_REQUIRED"
    observation = evaluation.get("human_observation")
    if not isinstance(observation, str) or not observation:
        return None, "SEMANTIC_HUMAN_OBSERVATION_REQUIRED"
    return reinforcement_payload(observation)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluations", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ev = json.loads(Path(a.evaluations).read_text(encoding="utf-8"))
    targets = {r["target_id"].strip(): r for r in rows(TARGETS)}
    contract = json.loads(PAYLOAD_CONTRACT.read_text(encoding="utf-8"))
    if contract.get("authority") != "PATCH_PAYLOAD_VALIDATION_ONLY_NO_CANONICAL_WRITE":
        raise AssertionError("patch payload contract authority drift")
    inv = contract["invariants"]
    for required in (
        "generic_total_is_not_equivalent_to_directional_reinforcement",
        "upper_and_lower_must_remain_separate",
        "free_text_semantic_inference_forbidden",
        "explicit_directional_tokens_may_emit_patch_candidate",
        "raw_human_observation_must_be_preserved_verbatim",
        "payload_candidate_never_authorizes_canonical_write",
    ):
        if inv.get(required) is not True:
            raise AssertionError(f"semantic invariant weakened: {required}")

    fixture_bundle = json.loads(FIXTURES.read_text(encoding="utf-8"))
    fixtures = {f["fixture_id"]: f for f in fixture_bundle["fixtures"]}
    candidates = []
    for r in ev.get("policy_fixtures", []):
        if r.get("terminal_action") != "EMIT_CANONICAL_PATCH_CANDIDATE":
            continue
        fid = r["fixture_id"]
        target = targets[r["target_id"]]
        payload = {
            "fixture_id": fid,
            "decision_id": r["decision_id"],
            "target_id": r["target_id"],
            "target_class": target["target_class"],
            "canonical_locator": target["canonical_locator"],
            "operation": target["allowed_operations"],
            "requested_epistemic_state": r["requested_epistemic_state"],
            "source_authority": "POLICY_FIXTURE_ONLY",
            "canonical_write_authorized": False,
            "note": "Conformance patch candidate only; not an N12 human resolution and not executable by the governed writer.",
        }
        candidates.append({"patch_candidate_id": "CEW-PATCH-CAND-" + stable_id(payload), **payload})

    current_candidates = []
    fixture_human_candidates = []
    semantic_blocks = []
    for r in ev.get("human_receipt_evaluations", []):
        if r.get("terminal_action") != "EMIT_CANONICAL_PATCH_CANDIDATE":
            continue
        target_id = r.get("target_id") or ""
        target = targets.get(target_id)
        if target is None:
            semantic_blocks.append({
                "decision_id": r["decision_id"],
                "fixture_only": r.get("fixture_only") is True,
                "reason_code": "SEMANTIC_REGISTERED_TARGET_REQUIRED",
            })
            continue
        semantic_payload, reason = semantic_payload_for(r, target)
        if semantic_payload is None:
            semantic_blocks.append({
                "decision_id": r["decision_id"],
                "fixture_only": r.get("fixture_only") is True,
                "fixture_id": r.get("fixture_id"),
                "target_id": target_id,
                "raw_human_observation": r.get("human_observation"),
                "reason_code": reason,
                "canonical_write_authorized": False,
            })
            continue
        payload = {
            "decision_id": r["decision_id"],
            "task_id": r.get("task_id"),
            "residual_id": r.get("residual_id"),
            "target_id": target_id,
            "target_class": target["target_class"],
            "canonical_locator": target["canonical_locator"],
            "operation": target["allowed_operations"],
            "requested_epistemic_state": r["requested_epistemic_state"],
            "source_authority": "POLICY_FIXTURE_ONLY" if r.get("fixture_only") is True else "VALIDATED_HUMAN_DIRECT_PRIMARY",
            "evidence_regions": r.get("evidence_regions", []),
            "source_versions": r.get("source_versions", []),
            "semantic_payload": semantic_payload,
            "canonical_write_authorized": False,
            "canonical_write_performed": False,
        }
        if r.get("fixture_id"):
            payload["fixture_id"] = r["fixture_id"]
        candidate = {"patch_candidate_id": "CEW-PATCH-CAND-" + stable_id(payload), **payload}
        if r.get("fixture_only") is True:
            fixture_human_candidates.append(candidate)
        else:
            current_candidates.append(candidate)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    bundle = {
        "schema_version": "1.0",
        "milestone": "CEW-F7",
        "authority": "PATCH_CANDIDATE_ONLY_NO_CANONICAL_WRITE",
        "current_n12_patch_candidates": current_candidates,
        "human_receipt_fixture_patch_candidates": fixture_human_candidates,
        "human_receipt_semantic_blocks": semantic_blocks,
        "policy_fixture_patch_candidates": candidates,
        "canonical_write_performed": False,
    }
    (out / "canonical_patch_candidates.json").write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("CEW_CANONICAL_PATCH_CANDIDATES_BUILT")
    print(f"CURRENT_N12_PATCH_CANDIDATES={len(current_candidates)}")
    print(f"HUMAN_RECEIPT_FIXTURE_PATCH_CANDIDATES={len(fixture_human_candidates)}")
    print(f"HUMAN_RECEIPT_SEMANTIC_BLOCKS={len(semantic_blocks)}")
    print(f"POLICY_FIXTURE_PATCH_CANDIDATES={len(candidates)}")
    print("DIRECTIONAL_REINFORCEMENT_COLLAPSE=FORBIDDEN")
    print("NATURAL_TEXT_EXTRACTION=EXPLICIT_TOKENS_ONLY")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
