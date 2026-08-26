#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WB = ROOT / "ui" / "workbench"

REQUIRED = [
    WB / "package.json",
    WB / "src" / "App.tsx",
    WB / "src" / "cew" / "snapshot.json",
    WB / "src" / "cew" / "decision.ts",
    WB / "tests" / "workbench.spec.ts",
    WB / ".storybook" / "main.ts",
    ROOT / "scripts" / "cew_workbench_stage_tav06a.sh",
]

EXPECTED_VERSIONS = {
    "react": "19.2.8",
    "react-dom": "19.2.8",
    "react-aria-components": "1.20.0",
    "openseadragon": "6.1.0",
    "vite": "8.2.2",
    "storybook": "10.5.10",
    "@storybook/react-vite": "10.5.10",
    "@playwright/test": "1.62.1",
    "@axe-core/playwright": "4.13.0",
}

def fail(message: str) -> None:
    raise SystemExit(f"CEW_WORKBENCH_FAIL: {message}")

for path in REQUIRED:
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")

package = json.loads((WB / "package.json").read_text(encoding="utf-8"))
all_deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
for name, version in EXPECTED_VERSIONS.items():
    if all_deps.get(name) != version:
        fail(f"{name} must be pinned exactly to {version}")

snapshot = json.loads((WB / "src" / "cew" / "snapshot.json").read_text(encoding="utf-8"))
if snapshot["canonical_commit"] != "b4356bc78807257901a0b97892a63d9f4c9744c9":
    fail("unexpected canonical snapshot commit")
if snapshot["source"]["archive_commit"] != "78c20a52db4f391ce0d13b9705b9f04737e218c9":
    fail("archive commit is not immutable/pinned")
if snapshot["source"]["archive_blob_sha"] != "c3048472adfdaa5b1e902f84c20ccfb20d679b1f":
    fail("TAV06A primary PDF blob is not pinned")
if snapshot["evidence_region"]["status"] != "READY":
    fail("T6A-G03 EvidenceRegion must remain READY")
if snapshot["structural_context"]["binding_state"] != "UNBOUND":
    fail("T6A-G03 structural binding must remain UNBOUND")
if snapshot["structural_context"]["candidate_target_id"] is not None:
    fail("UX1 must not invent a structural target")
if "CONFIRMED" in snapshot["decision"]["allowed_non_promotive_outcomes"]:
    fail("CONFIRMED cannot be offered without a registered target")

src = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (WB / "src").rglob("*")
    if path.is_file() and path.suffix in {".ts", ".tsx"}
)
if re.search(r"method\s*:\s*['\"](?:POST|PUT|PATCH|DELETE)['\"]", src, re.I):
    fail("frontend contains a write HTTP method")
if "canonical_write: true" in src or '"canonical_write": true' in src:
    fail("frontend contains a canonical-write path")
if "useState<DecisionOutcome | null>(null)" not in src:
    fail("professional decision must start blank")
if "NON_PROMOTIVE_HUMAN_DECISION_PROPOSAL" not in src:
    fail("decision output must remain proposal-only")
if "manifestMatchesSnapshot" not in src:
    fail("source drift guard is missing")

workflow = ROOT / ".github" / "workflows" / "validate-cew-engineering-workbench.yml"
if not workflow.exists():
    fail("missing UX1 CI workflow")

print(json.dumps({
    "status": "PASS",
    "work_item": "UX1-001",
    "canonical_snapshot": snapshot["canonical_commit"],
    "evidence_region": snapshot["evidence_region"]["id"],
    "evidence_status": snapshot["evidence_region"]["status"],
    "structural_binding": snapshot["structural_context"]["binding_state"],
    "canonical_write": False
}, indent=2))
