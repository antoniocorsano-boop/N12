#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "automation/CEW_AI_OBSERVATION_CONTRACT_v1.json"
ADAPTERS = ROOT / "data/canonical/CEW_AI_WORKER_ADAPTER_REGISTRY_v1.csv"
REGIONS = ROOT / "data/canonical/CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
OBS = ROOT / "data/canonical/CEW_OBSERVATION_REGISTRY_v1.csv"
MILESTONES = ROOT / "data/canonical/CEW_SYSTEM_MILESTONES_v1.csv"
KNOWLEDGE = ROOT / "knowledge/KNOWLEDGE_MANIFEST.json"
FIXTURES = ROOT / "analysis/cew/CEW_F4_REFERENCE_WORKER_OUTPUTS_v1.json"
PATCH = "knowledge/ARTIFACT_REGISTRY_CEW_AI_OBSERVATION_PATCH_v1.csv"

ORDER = {"ND": 0, "INF": 1, "RIF": 2, "MIS": 3, "DOC": 4}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def validate_envelope(e: dict, pack: dict, adapter: dict, contract: dict) -> None:
    missing = [k for k in contract["required_worker_envelope_fields"] if k not in e]
    if missing:
        raise AssertionError(f"worker envelope missing fields: {missing}")
    if e["worker_id"] != adapter["worker_id"] or e["worker_type"] != adapter["worker_type"]:
        raise AssertionError("worker adapter identity mismatch")
    if e["evidence_pack_id"] != pack["evidence_pack_id"] or e["evidence_region_id"] != pack["evidence_region_id"]:
        raise AssertionError("worker output escaped supplied EvidencePack")
    if e["output_kind"] not in contract["allowed_output_kinds"] or e["output_kind"] in contract["forbidden_output_kinds"]:
        raise AssertionError("forbidden worker output kind")
    if e["canonical_write_requested"] is not False:
        raise AssertionError("AI direct canonical write forbidden")
    if e["promotion_requested"] is not False:
        raise AssertionError("AI direct promotion forbidden")
    if adapter["may_write_canonical"] != "NO" or adapter["may_modify_f2_geometry"] != "NO":
        raise AssertionError("adapter authority exceeds F4 boundary")
    state = e["epistemic_state"]
    if state not in ORDER:
        raise AssertionError("unknown epistemic state")
    if ORDER[state] > ORDER[pack["epistemic_ceiling"]]:
        raise AssertionError("worker exceeded EvidencePack epistemic ceiling")
    if ORDER[state] > ORDER[adapter["max_epistemic_state"]]:
        raise AssertionError("worker exceeded adapter epistemic ceiling")
    c = e["confidence"]
    if not isinstance(c, (float, int)) or not (0 <= c <= 1):
        raise AssertionError("invalid confidence")
    if pack["structural_binding_state"] == "UNBOUND" and e["structural_binding_state"] != "UNBOUND":
        raise AssertionError("worker may not bind an UNBOUND structural entity")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packs-dir", required=True)
    args = ap.parse_args()
    packs_dir = Path(args.packs_dir)

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "CEW-AI-OBSERVATION-v1":
        raise AssertionError("unexpected AI observation contract")
    inv = contract["authority_invariants"]
    required_false = [
        "worker_may_write_canonical_data", "worker_may_change_f2_geometry",
        "worker_may_promote_epistemic_state", "worker_may_invent_unreadable_values",
        "worker_may_bind_unbound_structural_entity", "derived_asset_is_primary_authority",
        "reference_answer_may_be_exposed_to_worker"
    ]
    if any(inv[k] is not False for k in required_false):
        raise AssertionError("F4 authority boundary weakened")
    if inv["human_or_deterministic_promotion_required"] is not True:
        raise AssertionError("promotion boundary missing")

    milestone = {r["milestone_id"].strip(): r["status"].strip() for r in rows(MILESTONES)}
    if any(milestone.get(x) != "COMPLETE" for x in ("CEW-F0", "CEW-F1", "CEW-F2", "CEW-F3")):
        raise AssertionError("F4 requires F0-F3 COMPLETE")
    f4_open = milestone.get("CEW-F4") == "IN_PROGRESS"
    f4_closed = milestone.get("CEW-F4") == "COMPLETE" and milestone.get("CEW-F5") == "IN_PROGRESS"
    if not (f4_open or f4_closed):
        raise AssertionError("F4 validator requires F4 IN_PROGRESS or post-closure F4 COMPLETE/F5 IN_PROGRESS")

    knowledge = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    if PATCH not in set(knowledge.get("artifact_registry_patches", [])):
        raise AssertionError("F4 artifact patch is not effective in KNOWLEDGE_MANIFEST")

    adapters = {r["worker_id"].strip(): r for r in rows(ADAPTERS)}
    if {r["worker_type"].strip() for r in adapters.values()} != {"LAYOUT", "TEXT", "REINFORCEMENT"}:
        raise AssertionError("all three specialist adapter types are required")
    if any(r["status"].strip() != "ACTIVE" for r in adapters.values()):
        raise AssertionError("inactive F4 worker adapter")

    manifest = json.loads((packs_dir / "manifest.json").read_text(encoding="utf-8"))
    packs = {p["evidence_pack_id"]: p for p in manifest["packs"]}
    if len(packs) != 4:
        raise AssertionError("expected four reference EvidencePacks")
    forbidden = set(contract["forbidden_evidence_pack_fields"])
    regions = {r["evidence_region_id"].strip(): r for r in rows(REGIONS)}
    for p in packs.values():
        missing = [k for k in contract["required_evidence_pack_fields"] if k not in p]
        if missing:
            raise AssertionError(f"EvidencePack missing fields: {missing}")
        if forbidden & set(p):
            raise AssertionError("EvidencePack leaks historical/canonical answer")
        region = regions[p["evidence_region_id"]]
        canonical_bbox = {k: float(region[k]) for k in ("x", "y", "width", "height")}
        if p["bbox"] != canonical_bbox or p["coordinate_space"] != region["coordinate_space"].strip():
            raise AssertionError("EvidencePack changed F2 geometry")

    fixture = json.loads(FIXTURES.read_text(encoding="utf-8"))
    outputs = fixture["outputs"]
    if len(outputs) != 4 or {o["evidence_pack_id"] for o in outputs} != set(packs):
        raise AssertionError("reference worker output set mismatch")
    observations = {r["evidence_region_id"].strip(): r for r in rows(OBS)}

    for e in outputs:
        pack = packs[e["evidence_pack_id"]]
        adapter = adapters[e["worker_id"]]
        validate_envelope(e, pack, adapter, contract)
        baseline = observations[e["evidence_region_id"]]["literal_or_value"].strip()
        candidate = e["candidate_literal"]
        for token in ("quantity=UNREADABLE", "diameter=UNREADABLE", "dimensions=UNREADABLE"):
            if token in baseline and token not in candidate:
                raise AssertionError(f"worker failed to preserve unsupported token {token}")
        if e["evidence_pack_id"] == "CEW-PACK-ERW-N12-004":
            if e["structural_binding_state"] != "UNBOUND" or "no member binding established" not in candidate:
                raise AssertionError("T6A-G03 binding must remain UNBOUND")

    sample = outputs[3]
    sample_pack = packs[sample["evidence_pack_id"]]
    sample_adapter = adapters[sample["worker_id"]]
    rejected = 0
    for mutation in (
        {"canonical_write_requested": True},
        {"promotion_requested": True},
        {"epistemic_state": "DOC"},
        {"structural_binding_state": "BOUND"},
        {"output_kind": "CanonicalAssertion"},
    ):
        bad = copy.deepcopy(sample)
        bad.update(mutation)
        try:
            validate_envelope(bad, sample_pack, sample_adapter, contract)
        except AssertionError:
            rejected += 1
    if rejected != 5:
        raise AssertionError(f"negative authority guard incomplete: rejected={rejected}/5")

    print("AI_OBSERVATION_PASS")
    print("EVIDENCE_PACKS=4")
    print("SPECIALIST_ADAPTERS=LAYOUT,TEXT,REINFORCEMENT")
    print("ANSWER_LEAKAGE=FORBIDDEN")
    print("CANONICAL_WRITES=FORBIDDEN")
    print("DIRECT_PROMOTION=FORBIDDEN")
    print("F2_GEOMETRY_MUTATION=FORBIDDEN")
    print("NEGATIVE_AUTHORITY_GUARDS=5/5_REJECTED")
    print("T6A_G03_BINDING=UNBOUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
