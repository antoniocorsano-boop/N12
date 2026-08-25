#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "data" / "canonical"
TASKS = C / "CEW_ERW_RESOLUTION_TASKS_v1.csv"
RESIDUALS = C / "M1E_B06_REINFORCEMENT_RESIDUALS_CURRENT_v1.csv"
OBSERVATIONS = C / "CEW_OBSERVATION_REGISTRY_v1.csv"
VIEWER = C / "CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
REGIONS = C / "CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
MEMBERS = C / "M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
CONTRACT = ROOT / "automation" / "CEW_ERW_CONTRACT_v1.json"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def one(items: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    matches = [r for r in items if r.get(key, "").strip() == value]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one {key}={value}, got {len(matches)}")
    return matches[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    ref = contract["reference_vertical_slice"]
    task = one(rows(TASKS), "task_id", ref["task_id"])
    residual = one(rows(RESIDUALS), "residual_id", ref["residual_id"])
    observation = one(rows(OBSERVATIONS), "reference_item", ref["source_scheme"])
    viewer = one(rows(VIEWER), "task_id", ref["task_id"])
    region = one(rows(REGIONS), "evidence_region_id", observation["evidence_region_id"].strip())
    member = one(rows(MEMBERS), "source_member_id", ref["candidate_member"])

    if task["residual_id"].strip() != residual["residual_id"].strip():
        raise AssertionError("task/residual identity mismatch")
    if observation["structural_binding"].strip():
        raise AssertionError("F2 observation unexpectedly asserts a structural binding")
    if viewer["binding_state"].strip() != "READY":
        raise AssertionError("source viewer binding is not READY")
    if member["support_i"].strip() != "12" or member["support_j"].strip() != "19":
        raise AssertionError("G5-B017 endpoint topology changed")

    candidates = [
        {
            "candidate_id": "ERW-N12-004-CAND-BIND-G5-B017",
            "interpretation": "Bind T6A-G03 reinforcement scheme to G5-B017",
            "status": "REJECTED_BY_CURRENT_EVIDENCE",
            "model_delta": "Would assign a member-specific reinforcement scheme to G5-B017",
            "supporting_evidence": ["Both records concern G5 roof reinforcement context"],
            "contradicting_evidence": [
                "T6A-G03 is an unlabelled inclined scheme with two support stations plus a free overhang",
                "G5-B017 is a support-to-support member from support 12 to support 19",
                "M1E-B06-R11 explicitly forbids assignment without direct endpoint/topology binding"
            ],
            "epistemic_ceiling": task["epistemic_ceiling"].strip(),
            "selectable": False
        },
        {
            "candidate_id": "ERW-N12-004-CAND-UNBOUND",
            "interpretation": "Retain T6A-G03 as documentary source scheme with structural binding UNBOUND",
            "status": "SUPPORTED_DISPOSITION",
            "model_delta": "None; canonical member reinforcement remains unresolved",
            "supporting_evidence": [
                "F2 Observation explicitly keeps structural binding empty/UNBOUND",
                "Viewer authority note keeps T6A-G03 structurally UNBOUND",
                "Residual M1E-B06-R11 is not closeable by assignment"
            ],
            "contradicting_evidence": [],
            "epistemic_ceiling": "DOC_SOURCE_SCHEME_ONLY",
            "selectable": True
        }
    ]

    decision = {
        "decision_id": "ERW-N12-004-REFERENCE-DECISION-UNBOUND",
        "task_id": task["task_id"].strip(),
        "outcome": "UNBOUND",
        "selected_candidate": "ERW-N12-004-CAND-UNBOUND",
        "human_observation": "REFERENCE_CASE_ONLY_NO_HUMAN_OBSERVATION",
        "reason": "Current primary evidence documents T6A-G03 but does not directly bind its two-support-plus-free-overhang topology to G5-B017 support 12-19.",
        "evidence_regions": [observation["evidence_region_id"].strip()],
        "review_view": viewer["deep_link"].strip(),
        "requested_epistemic_state": "ND_MEMBER_BINDING",
        "reviewer": "DETERMINISTIC_REFERENCE_CASE",
        "timestamp": "REFERENCE_CASE_NO_RUNTIME_TIMESTAMP",
        "canonical_write": False
    }

    bundle = {
        "schema_version": "1.0",
        "workspace_id": "CEW-F6-ERW-N12-004-v1",
        "authority": contract["workspace_authority"],
        "task": task,
        "source": {
            "observation": observation,
            "evidence_region": region,
            "viewer_binding": viewer
        },
        "model": {
            "candidate_member": {
                "member_id": member["member_id"].strip(),
                "source_member_id": member["source_member_id"].strip(),
                "storey_id": member["storey_id"].strip(),
                "support_i": member["support_i"].strip(),
                "support_j": member["support_j"].strip(),
                "geometric_length_m": member["geometric_length_m"].strip(),
                "validation_state": member["validation_state"].strip(),
                "note": member["note"].strip()
            }
        },
        "residual": residual,
        "known_unknown_conflict": {
            "known": task["known_claims"].strip(),
            "unknown": task["unknown_claims"].strip(),
            "conflict": task["conflicts"].strip()
        },
        "candidates": candidates,
        "reference_disposition_receipt": decision,
        "canonical_mutation": "FORBIDDEN"
    }
    bundle_path = out / "erw_n12_004_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

    esc = html.escape
    page = f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>CEW ERW — ERW-N12-004</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;max-width:1100px}}section{{border:1px solid #bbb;padding:1rem;margin:1rem 0}}code{{white-space:pre-wrap}}.bad{{font-weight:700}}.ok{{font-weight:700}}</style></head>
<body><h1>CEW Evidence Resolution Workspace</h1>
<p><strong>Task:</strong> {esc(task['task_id'])} · <strong>Residual:</strong> {esc(residual['residual_id'])} · <strong>Authority:</strong> DERIVED_REVIEW_WORKSPACE_ONLY</p>
<section><h2>Task</h2><p>{esc(task['question'])}</p><p><strong>Blocking scope:</strong> {esc(task['blocking_scope'])}</p></section>
<section><h2>Source context</h2><p><strong>Observation:</strong> {esc(observation['literal_or_value'])}</p><p><strong>Evidence region:</strong> {esc(observation['evidence_region_id'])}</p><p><strong>Viewer deep link:</strong> <code>{esc(viewer['deep_link'])}</code></p><p>{esc(viewer['authority_note'])}</p></section>
<section><h2>Model context</h2><p><strong>Member:</strong> G5-B017 · support 12 → 19 · length {esc(member['geometric_length_m'])} m</p><p>{esc(member['note'])}</p></section>
<section><h2>Known / unknown / conflict</h2><p><strong>Known:</strong> {esc(task['known_claims'])}</p><p><strong>Unknown:</strong> {esc(task['unknown_claims'])}</p><p><strong>Conflict:</strong> {esc(task['conflicts'])}</p></section>
<section><h2>Candidate comparison</h2><p class='bad'>Bind to G5-B017 — REJECTED BY CURRENT EVIDENCE</p><p>Topology mismatch and no direct endpoint/source binding.</p><p class='ok'>Retain UNBOUND — SUPPORTED DISPOSITION</p><p>Preserves documentary source scheme without inventing member reinforcement.</p></section>
<section><h2>Reference disposition receipt</h2><p><strong>Outcome:</strong> UNBOUND</p><p>{esc(decision['reason'])}</p><p><strong>Canonical write:</strong> false</p></section>
</body></html>"""
    (out / "index.html").write_text(page, encoding="utf-8")

    print("ERW_REFERENCE_CASE_BUILT")
    print("TASK=ERW-N12-004")
    print("RESIDUAL=M1E-B06-R11")
    print("CANDIDATE_G5_B017=REJECTED_BY_CURRENT_EVIDENCE")
    print("REFERENCE_DISPOSITION=UNBOUND")
    print("CANONICAL_MUTATION=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
