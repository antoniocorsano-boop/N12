# CEW COL-02 Occurrence Coverage Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a deterministic exact-source closure artifact that turns the bounded COL-02 graphical `occurrence_coverage_complete` state true only when the already-reviewed reconciliation and repair evidence proves every successor item terminal and no human point unresolved.

**Architecture:** Add one pure closure validator/builder that consumes fresh residual reconciliation and repair manifests plus the two governed review receipts. Do not mutate historical manifests. Add one exact-source workflow step after whole-symbol repair to emit and assert the closure artifact.

**Tech Stack:** Python 3.12.15, `unittest`, existing CEW COL-02 JSON evidence, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-31-cew-col02-occurrence-coverage-closure-design.md`

## Global Constraints

- Preserve the frozen 611 neutral proposals and immutable `COL02-FP-*` ID space.
- Residual reconciliation replay SHA-256 must equal `b68526f71e77a072b0849d2d3cd2fcab886b03c86a99681717d7aee5cd13bf3c`.
- Fresh repair manifest file SHA-256 must equal `e688c22753d8804edfdded8e9f89651c60b7a864a016b400a027d708329b1228`.
- Successor task set must be exactly R01–R06.
- R02 / `COL02-FP-0106` remains `MISLOCALIZED_NOT_COLUMN`.
- R01/R03/R04/R05/R06 must map to the five final graphical `PASS` decisions.
- Historical manifests remain unchanged with `occurrence_coverage_complete = false`.
- Support/text/family/section/fixed-line/structural identity, canonical geometry/write, G2C, G3 and merge remain false.

## Review Focus

- A human-added point becomes `HUMAN_POINT_UNBOUND`: closure must fail closed.
- One successor task is missing or duplicated in a receipt: closure must fail closed.
- A repair review decision is `REWORK` or missing: closure must fail closed.
- Fresh repair manifest differs from the reviewed digest: closure must fail closed.
- A downstream authority flag drifts true: closure must fail closed.

---

### Task 1: Pure occurrence-coverage closure contract

**Files:**
- Create: `experiments/cew_col02/occurrence_coverage_closure.py`
- Create: `tests/cew_col02/test_occurrence_coverage_closure.py`

**Interfaces:**
- Consumes: residual reconciliation manifest `dict`, residual reconciliation review receipt `dict`, repair manifest `dict`, final graphical review v2 `dict`, repair manifest raw bytes.
- Produces: `build_occurrence_coverage_closure(...) -> dict[str, Any]` and `validate_occurrence_coverage_closure_inputs(...) -> None`.

- [ ] **Step 1: Write failing closure tests**

Tests must pin:
- fully closed six-item chain returns `occurrence_coverage_complete is True`;
- any `HUMAN_POINT_UNBOUND` fails closed;
- missing/duplicate R01–R06 decision fails closed;
- non-PASS repair review fails closed;
- repair-manifest digest mismatch fails closed;
- downstream authority drift fails closed.

- [ ] **Step 2: Run unit suite and acquire causal RED**

Run: `python -m unittest discover -s tests/cew_col02 -p 'test_*.py' -v`
Expected: existing tests PASS; new closure tests FAIL because the closure module/API does not exist.

- [ ] **Step 3: Implement minimal pure closure validator/builder**

Implement only the checks required by the spec and tests. The output must preserve all downstream authority flags as false and set `occurrence_coverage_complete = true` only after every check succeeds.

- [ ] **Step 4: Run full COL-02 unit suite**

Run: `python -m unittest discover -s tests/cew_col02 -p 'test_*.py' -v`
Expected: PASS, zero failures.

- [ ] **Step 5: Commit**

Commit message: `feat: add COL-02 occurrence coverage closure contract`.

### Task 2: Exact-source closure emission and workflow gate

**Files:**
- Modify: `experiments/cew_col02/occurrence_coverage_closure.py`
- Modify: `.github/workflows/validate-cew-col02-footprint-text-binding.yml`
- Test: `tests/cew_col02/test_occurrence_coverage_closure.py`

**Interfaces:**
- Consumes: fresh exact-source files `col02-residual-occurrence-reconciliation.json` and `col02-axis-aware-whole-symbol-repair.json`, plus the two governed receipts.
- Produces: `evidence/cew-col02/footprint-text-binding/col02-occurrence-coverage-closure.json`.

- [ ] **Step 1: Add failing exact-source emission contract**

Test that the module exposes a file-level builder/writer using the canonical evidence and governance paths and that the emitted artifact contains the exact frozen lineage fields and closed authority boundary.

- [ ] **Step 2: Acquire causal RED**

Run the complete COL-02 unit suite; expected only the new emission contract to fail.

- [ ] **Step 3: Implement minimal exact-source writer and workflow step**

Append a workflow step after `Execute axis-aware whole-symbol repair`:
- run `python -m experiments.cew_col02.occurrence_coverage_closure`;
- assert `occurrence_coverage_complete is True`;
- assert six successor items terminal, four point bindings, five repair PASS decisions, one rejected target;
- assert all downstream authority flags false.

Add the new design/spec/plan paths to the workflow trigger list.

- [ ] **Step 4: Verify unit GREEN and fresh exact-source replay**

Expected:
- unit job PASS;
- exact-source Tav. 5 replay PASS;
- closure step PASS;
- uploaded artifact contains `col02-occurrence-coverage-closure.json`.

- [ ] **Step 5: Verify no historical mutation**

Compare fresh reconciliation and repair manifests against their frozen replays/digests. Confirm their own historical `occurrence_coverage_complete` fields remain false while the new closure artifact alone is true.

- [ ] **Step 6: Commit**

Commit message: `ci: gate COL-02 occurrence coverage closure on exact source`.

### Task 3: Governed checkpoint

**Files:**
- Modify only PR metadata/comment unless verification exposes a defect.

**Interfaces:**
- Consumes: exact-head workflow run and uploaded artifact.
- Produces: auditable checkpoint with exact SHA, run, artifact ID/digest, closure digest and authority boundary.

- [ ] **Step 1: Verify PR exact head, Draft/open/non-merged state and review threads**

- [ ] **Step 2: Download fresh artifact and independently inspect closure JSON**

Confirm:
- `occurrence_coverage_complete = true`;
- proposal count remains 611 upstream;
- no unbound point;
- six terminal successor outcomes;
- five graphical repair PASS + one rejected target;
- all downstream authority false.

- [ ] **Step 3: Record checkpoint comment and update PR description**

Do not mark Ready, merge, deploy, G2C or G3.
