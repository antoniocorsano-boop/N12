#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ROOT / "data/canonical/CEW_PROMOTION_TARGET_REGISTRY_v1.csv"
FIXTURES = ROOT / "analysis/cew/CEW_F7_PROMOTION_POLICY_FIXTURES_v1.json"


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))

def stable_id(obj: dict) -> str:
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--evaluations",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    ev=json.loads(Path(a.evaluations).read_text(encoding="utf-8"))
    targets={r["target_id"].strip():r for r in rows(TARGETS)}
    fixture_bundle=json.loads(FIXTURES.read_text(encoding="utf-8")); fixtures={f["fixture_id"]:f for f in fixture_bundle["fixtures"]}
    candidates=[]
    for r in ev.get("policy_fixtures",[]):
        if r.get("terminal_action")!="EMIT_CANONICAL_PATCH_CANDIDATE": continue
        fid=r["fixture_id"]; f=fixtures[fid]; target=targets[r["target_id"]]
        payload={
            "fixture_id":fid,
            "decision_id":r["decision_id"],
            "target_id":r["target_id"],
            "target_class":target["target_class"],
            "canonical_locator":target["canonical_locator"],
            "operation":target["allowed_operations"],
            "requested_epistemic_state":r["requested_epistemic_state"],
            "source_authority":"POLICY_FIXTURE_ONLY",
            "canonical_write_authorized":False,
            "note":"Conformance patch candidate only; not an N12 human resolution and not executable by the governed writer."
        }
        candidates.append({"patch_candidate_id":"CEW-PATCH-CAND-"+stable_id(payload),**payload})
    current_candidates=[r for r in ev.get("current_n12",[]) if r.get("terminal_action")=="EMIT_CANONICAL_PATCH_CANDIDATE"]
    if current_candidates: raise AssertionError("current N12 unexpectedly emitted patch candidate")
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    bundle={
        "schema_version":"1.0",
        "milestone":"CEW-F7",
        "authority":"PATCH_CANDIDATE_ONLY_NO_CANONICAL_WRITE",
        "current_n12_patch_candidates":[],
        "policy_fixture_patch_candidates":candidates,
        "canonical_write_performed":False
    }
    (out/"canonical_patch_candidates.json").write_text(json.dumps(bundle,indent=2)+"\n",encoding="utf-8")
    print("CEW_CANONICAL_PATCH_CANDIDATES_BUILT")
    print("CURRENT_N12_PATCH_CANDIDATES=0")
    print(f"POLICY_FIXTURE_PATCH_CANDIDATES={len(candidates)}")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0
if __name__=="__main__": raise SystemExit(main())
