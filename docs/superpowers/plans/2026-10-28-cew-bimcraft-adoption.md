# CEW BIMCraft Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the qualified CEW-BIMCRAFT-01 benchmark into an explicit human-approved CEW toolchain adoption without granting BIMCraft canonical, structural-analysis, FEM, or N12 Stage-B authority.

**Architecture:** Preserve the benchmark contract and receipts as immutable qualification evidence. Record adoption in a new governance decision and a canonical Master amendment, with BIMCraft classified as an optional replaceable projection/agentic-authoring engine behind CEW adapters. Keep build123d as the primary canonical-geometry adapter and IfcOpenShell as the canonical IFC read/query/validation component.

**Tech Stack:** CEW governance Markdown/JSON; BIMCraft v0.9.0; IfcOpenShell 0.9.0.post1; GitHub Actions qualification workflow.

**Spec:** `analysis/cew/CEW_BIMCRAFT_01_BENCHMARK_REPORT_v1.md`

## Global Constraints

- Preserve all CEW-BIMCRAFT-01 benchmark evidence and historical receipts unchanged.
- BIMCraft adoption must not make `.bimcraft` or IFC canonical authority.
- `canonical_write_authorized`, `structural_identity_authorized`, `fem_authorized`, and `n12_stage_b_authorized` remain false.
- build123d remains the primary canonical-geometry adapter.
- IfcOpenShell remains the adopted IFC read/query/validation component.
- Future BIMCraft releases require requalification before promotion.
- Real N12 Stage B remains blocked by the existing CEW-B01 human/source-binding gate.

## Review Focus

- Adoption wording must not imply BIMCraft replaces the CEW Canonical Model.
- Adoption wording must not imply BIMCraft replaces build123d or IfcOpenShell.
- Historical benchmark state must remain distinguishable from the new human adoption decision.
- Stage B N12 and FEM permissions must remain false.
- The adopted version boundary must remain pinned to the qualified v0.9.0 candidate until requalification.

---

### Task 1: Record the human adoption decision

**Files:**
- Create: `governance/cew-bimcraft-01/CEW_BIMCRAFT_ADOPTION_DECISION_v1.json`

**Interfaces:**
- Consumes: qualified benchmark report and decision input.
- Produces: immutable governance record with `decision=ADOPT_OPTIONAL` and authority boundaries.

- [ ] Record the human decision with exact qualified release/commit, roles, and false authority flags.
- [ ] Verify the record is valid JSON and does not mutate historical benchmark evidence.

### Task 2: Amend the canonical Master without rewriting history

**Files:**
- Create: `governance/CEW_MASTER_AMENDMENT_BIMCRAFT_01.md`

**Interfaces:**
- Consumes: Task 1 adoption record.
- Produces: canonical amendment specifying BIMCraft's adopted role and precedence relative to build123d/IfcOpenShell.

- [ ] State `ADOPT — OPTIONAL BIM PROJECTION / AGENTIC AUTHORING ENGINE`.
- [ ] State the adapter chain and non-authority rules.
- [ ] State version/requalification policy and Stage-B gate.

### Task 3: Requalify the exact adoption head and promote PR to reviewable state

**Files:**
- Modify: PR #164 metadata only after CI evidence.

**Interfaces:**
- Consumes: Tasks 1–2.
- Produces: exact-head CI evidence and reviewable adoption PR.

- [ ] Run the existing CEW-BIMCRAFT-01 qualification on the exact adoption head.
- [ ] Require all workflow steps SUCCESS.
- [ ] Update PR body with adoption decision and exact evidence.
- [ ] Mark PR Ready for review; do not merge.
