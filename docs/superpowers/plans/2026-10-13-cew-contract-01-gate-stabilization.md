# CEW-CONTRACT-01 Gate Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stabilize CEW-CONTRACT-01 as a finite, durable, fail-closed qualification gate with deterministic replay, mutation testing, and no permanent dependency on expiring GitHub Actions artifacts.

**Architecture:** Introduce a machine-checkable Frozen Authority Profile, a focused deterministic replay harness, and a consolidated stabilization mutation suite. The closure validator consumes those durable objects; the GitHub workflow materializes only immutable Git objects and runs the replay + validator, while the historical Actions run/artifact are converted once into a versioned transition receipt and are no longer runtime prerequisites.

**Tech Stack:** Python 3.12 standard library, `unittest`, Git/GitHub Actions, JSON/CSV/Markdown repository evidence.

**Spec:** `docs/superpowers/specs/2026-10-13-cew-contract-01-gate-stabilization-design.md`

## Global Constraints

- Do not modify canonical N12 technical data.
- Do not create or authorize a `SolverRun` or `Result`.
- `solver_authorized=false`, `calculation_model_ready=false`, and `synthetic_solver_result=false` must remain invariant.
- The operational authority commit is exactly `d806dcca72779b5a186defe557a7a9b739575a90`.
- The ModelGeneration input set is exactly the six paths already frozen by CEW-CONTRACT-01.
- The registration case uses exactly support IDs `1` and `19` from `data/canonical/PT_METRIC_NETWORK_RESIDUALS_v1.csv`.
- Historical run `32955421352` and artifact `9601773275` may be used only to create/verify the transition receipt; the permanent gate must not require either object to remain available.
- Deterministic replay may control only the volatile execution timestamp already recorded in the frozen manifest; no engineering field may be normalized or replaced.
- No automatic merge. PR #147 remains Draft until the stabilization stop criterion is satisfied.
- Apply TDD RED → GREEN by invariant block, not finding-by-finding.

## Review Focus

- **Replay path identity:** replay from a temporary checkout must still pass repository-relative input paths to the historical builder, otherwise output provenance bytes can drift despite identical engineering data. Task 2 pins this with an exact-output digest test.
- **Timestamp control leakage:** only `generated_at` may be frozen; any harness that rewrites other output fields must fail. Task 2 includes a negative test for non-time mutation.
- **Authority duplication drift:** values repeated in manifest/receipt/profile must disagree fail-closed rather than choosing one silently. Task 3 tests cross-object mismatch.
- **Historical evidence expiration:** deletion/unavailability of Actions artifact/run after transition must not fail the permanent gate. Task 5 tests the workflow for absence of artifact-download/API dependencies.
- **Mutation false positives:** every mandatory mutation must fail for its named taxonomy class, not merely because setup is malformed. Task 4 asserts expected error prefixes per mutation family.

---

### Task 1: Freeze the Stabilization Authority and Historical Transition Receipt

**Files:**
- Create: `evidence/cew-contract-01/stabilization/N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json`
- Create: `evidence/cew-contract-01/stabilization/N12_CEW_MODEL_GENERATION_HISTORICAL_RECEIPT_v1.json`
- Create: `tests/test_cew_contract_01_stabilization_authority.py`

**Interfaces:**
- Consumes: existing ModelGeneration manifest/receipt, registration fixture, gate matrix, historical run `32955421352`, artifact `9601773275`, operational commit `d806dcca...`.
- Produces: `load_frozen_authority(path: Path) -> dict[str, Any]` contract data for Tasks 2–5; durable historical receipt containing run/artifact/output verification facts without granting runtime authority to the artifact.

- [ ] **Step 1: Write RED tests for the frozen authority profile**

Add tests asserting exact values for operational commit, snapshot ID, builder path/blob, exact six input paths/digests, registration source + exact support IDs `1`/`19`, output identity/digest/size, authority-false flags, and C01-T01…T11 evidence references.

- [ ] **Step 2: Run the authority tests and verify RED**

Run: `python -m unittest tests/test_cew_contract_01_stabilization_authority.py -v`

Expected: FAIL because the stabilization authority/receipt files do not exist.

- [ ] **Step 3: Re-verify historical evidence once and create the two durable JSON files**

Before writing the receipt, verify live GitHub evidence for run `32955421352` and artifact `9601773275`: expected workflow/path, head SHA `d806...`, `status=completed`, `conclusion=success`, artifact identity/archive digest, output identity/SHA-256/size. Record those facts plus a field such as `runtime_dependency=false` in the historical receipt. The Frozen Authority Profile must contain only immutable qualification authority needed by the permanent gate.

- [ ] **Step 4: Run the authority tests and verify GREEN**

Run: `python -m unittest tests/test_cew_contract_01_stabilization_authority.py -v`

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```bash
git add evidence/cew-contract-01/stabilization tests/test_cew_contract_01_stabilization_authority.py
git commit -m "test: freeze CEW-CONTRACT-01 stabilization authority"
```

---

### Task 2: Build the Deterministic Replay Harness

**Files:**
- Create: `scripts/cew_contract_01_replay.py`
- Create: `tests/test_cew_contract_01_replay.py`

**Interfaces:**
- Consumes: `N12_CEW_CONTRACT_01_FROZEN_AUTHORITY_v1.json`, a temporary checkout/materialization of commit `d806...` containing builder + six inputs.
- Produces: `run_replay(authority_path: Path, source_root: Path, output_path: Path) -> dict[str, Any]`; result includes replay status, output identity, byte size, SHA-256, and taxonomy errors.

- [ ] **Step 1: Write RED tests for exact deterministic replay behavior**

Tests must cover: historical timestamp sourced from authority/manifest; builder loaded from the frozen source root; exactly six relative input paths; byte-for-byte output SHA-256 `4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`; output size `1068121`; failure when builder bytes/blob differ; failure when the replay timestamp is absent or differs from frozen authority; failure if a harness attempts any normalization beyond the timestamp.

- [ ] **Step 2: Run replay tests and verify RED**

Run: `python -m unittest tests/test_cew_contract_01_replay.py -v`

Expected: FAIL because `scripts/cew_contract_01_replay.py` does not exist.

- [ ] **Step 3: Implement the minimal replay harness**

Implement `run_replay(...)` so it imports the materialized historical builder, supplies repository-relative `Path` arguments from a controlled working root, freezes only the builder module's `datetime.now(timezone.utc)` to the frozen historical `generated_at`, invokes the historical `build_model(...)`, serializes using the same JSON formatting as the historical builder, writes only the temporary output, and compares identity/size/SHA-256 to Frozen Authority.

- [ ] **Step 4: Run replay tests and verify GREEN**

Run: `python -m unittest tests/test_cew_contract_01_replay.py -v`

Expected: PASS, including the exact historical output digest.

- [ ] **Step 5: Commit Task 2**

```bash
git add scripts/cew_contract_01_replay.py tests/test_cew_contract_01_replay.py
git commit -m "feat: add deterministic CEW ModelGeneration replay"
```

---

### Task 3: Refactor Closure Validation Around I01–I17

**Files:**
- Modify: `scripts/validate_cew_contract_01_closure.py`
- Create: `tests/test_cew_contract_01_stabilization_invariants.py`
- Modify: `tests/test_cew_contract_01_closure.py`
- Modify: `tests/test_cew_contract_01_review_regressions.py`
- Modify: `tests/test_cew_contract_01_final_review_regressions.py`

**Interfaces:**
- Consumes: Frozen Authority Profile from Task 1; replay result from Task 2; existing manifest, Verification, Receipt, registration fixture, matrix, evidence, minimality/report.
- Produces: `validate_project(root: Path, operational_source_root: Path | None = None, replay_result: dict[str, Any] | None = None) -> dict[str, Any]` with stable taxonomy errors and `qualified: bool`.

- [ ] **Step 1: Write RED invariant tests for current uncovered cases**

At minimum assert fail-closed behavior for: builder Git blob mismatch; registration examples set not exactly `{1,19}`; unexpected third registration support; manifest/receipt/profile disagreement; missing replay result; replay digest mismatch; authority boundary flag mutation; and CEW-FEM debt removal.

- [ ] **Step 2: Run stabilization invariant tests and verify RED**

Run: `python -m unittest tests/test_cew_contract_01_stabilization_invariants.py -v`

Expected: FAIL on the intentionally uncovered invariants.

- [ ] **Step 3: Implement minimal validator changes using the Frozen Authority Profile**

Centralize frozen constants through the profile rather than adding new scattered literals. Add stable error classes using the spec taxonomy (`AUTHORITY_IDENTITY_*`, `INPUT_SET_*`, `INPUT_DIGEST_*`, `BUILDER_IDENTITY_*`, `REPLAY_*`, `OUTPUT_*`, `REGISTRATION_*`, `RECEIPT_*`, `EVIDENCE_*`, `GATE_MATRIX_*`, `AUTHORITY_BOUNDARY_*`, `CI_BYPASS_*`). Require exact registration support IDs and replay success before `qualified=true`.

- [ ] **Step 4: Run all validator test modules**

Run:
```bash
python -m unittest \
  tests/test_cew_contract_01_closure.py \
  tests/test_cew_contract_01_review_regressions.py \
  tests/test_cew_contract_01_final_review_regressions.py \
  tests/test_cew_contract_01_stabilization_invariants.py -v
```

Expected: PASS. Existing regression intent remains preserved; artifact-runtime-specific assertions may be migrated to durable replay assertions rather than deleted without replacement.

- [ ] **Step 5: Commit Task 3**

```bash
git add scripts/validate_cew_contract_01_closure.py tests/test_cew_contract_01_*.py
git commit -m "refactor: enforce frozen CEW stabilization invariants"
```

---

### Task 4: Consolidate the Adversarial Mutation Suite

**Files:**
- Create: `tests/test_cew_contract_01_stabilization_mutations.py`

**Interfaces:**
- Consumes: Task 1 authority fixtures, Task 2 replay harness, Task 3 validator.
- Produces: one executable threat-model suite covering mandatory mutation categories 9.1–9.7 from the spec.

- [ ] **Step 1: Write mutation helpers that copy fixtures into isolated temporary roots**

Define focused test helpers only; do not mutate repository canonical files. Each test applies one mutation and asserts both `qualified == False` and the expected taxonomy error/prefix.

- [ ] **Step 2: Add mandatory mutation tests**

Cover all spec categories: workflow/execution; frozen authority; exact input set/digests; replay/output; Verification/Receipt; registration uncertainty; gate matrix/evidence. Include all four fresh Codex cases: builder blob false, missing support 1, missing support 19, and no runtime dependency on historical artifact/run.

- [ ] **Step 3: Run the mutation suite and verify any remaining RED cases**

Run: `python -m unittest tests/test_cew_contract_01_stabilization_mutations.py -v`

Expected: any FAIL identifies an I01–I17 hole; fix only the owning validator/replay code, not the test expectation.

- [ ] **Step 4: Re-run until the complete mutation suite is GREEN**

Run: `python -m unittest tests/test_cew_contract_01_stabilization_mutations.py -v`

Expected: PASS for every negative mutation because each mutation is correctly rejected.

- [ ] **Step 5: Commit Task 4**

```bash
git add tests/test_cew_contract_01_stabilization_mutations.py scripts/cew_contract_01_replay.py scripts/validate_cew_contract_01_closure.py
git commit -m "test: add CEW-CONTRACT-01 adversarial mutation suite"
```

---

### Task 5: Make the Repository-Native Workflow Durable

**Files:**
- Modify: `.github/workflows/validate-cew-contract-01-closure.yml`
- Modify: `tests/test_cew_contract_01_ci_gate.py`

**Interfaces:**
- Consumes: immutable Git commit `d806...`, Frozen Authority Profile, replay harness, validator, mutation suite.
- Produces: exact-head CI gate that has no call/download dependency on artifact `9601773275` or historical run `32955421352`.

- [ ] **Step 1: Write RED CI-contract tests for the stabilized workflow**

Require: checkout PR exact head; pinned action SHAs; `persist-credentials:false`; only `contents: read` permissions unless a strictly necessary read scope is proven; materialize builder + six inputs + registration source from `d806...`; run replay tests, invariant tests, mutation suite, CI self-test, and final validator; reject any `/actions/artifacts/`, artifact ZIP download, historical-run API lookup, `if`, `continue-on-error`, `|| true`, or equivalent bypass.

- [ ] **Step 2: Run the CI-contract self-test and verify RED**

Run: `python -m unittest tests/test_cew_contract_01_ci_gate.py -v`

Expected: FAIL because the current workflow still downloads historical artifact `9601773275` and has not materialized the historical builder for replay.

- [ ] **Step 3: Update the workflow minimally**

Replace `Materialize pinned ModelGeneration artifact` with materialization of `scripts/cew_structural_model_builder.py` plus the already-required immutable inputs/source. Run the replay harness to create a temporary output under `/tmp`; pass that replay result into validation through the stable mechanism chosen in Tasks 2–3. Remove runtime `actions: read` if no longer needed.

- [ ] **Step 4: Run all local CI contract and qualification tests**

Run:
```bash
python -m py_compile scripts/cew_contract_01_replay.py scripts/validate_cew_contract_01_closure.py
python -m unittest discover -s tests -p 'test_cew_contract_01*.py' -v
```

Expected: PASS.

- [ ] **Step 5: Commit Task 5**

```bash
git add .github/workflows/validate-cew-contract-01-closure.yml tests/test_cew_contract_01_ci_gate.py
git commit -m "ci: make CEW-CONTRACT-01 gate durable"
```

---

### Task 6: Exact-Head Qualification, Documentation, Review Triage, and Stop Criterion

**Files:**
- Modify: `docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md`
- Modify only if needed for factual alignment: `evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json`
- Modify only if needed for factual alignment: `evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_RECEIPT_v1.json`
- GitHub metadata: PR #147 body and review threads.

**Interfaces:**
- Consumes: complete stabilized gate from Tasks 1–5.
- Produces: one exact-head qualification record and closure decision against I01–I17; no merge.

- [ ] **Step 1: Run the complete repository-native gate on the resulting exact head**

Verify the GitHub Actions run is `completed/success` on the actual PR head and that Vercel is success/skipped according to the already-corrected deployment perimeter.

- [ ] **Step 2: Verify stop-criterion evidence on the same SHA**

Confirm: Frozen Authority machine-checkable; I01–I17 covered; mutation suite all GREEN as rejection tests; happy path PASS; no runtime artifact dependency; deterministic replay reconstructs expected output; no open blocker thread relative to I01–I17.

- [ ] **Step 3: Update qualification report and PR body factually**

Record the stabilized gate architecture, exact-head run ID/SHA, durable replay result, mutation-suite coverage, historical receipt role, and unchanged CEW-FEM boundary. Do not claim review PASS before fresh review completes.

- [ ] **Step 4: Request one fresh independent review on the exact head**

Classify every new finding using the approved finding-triage policy. Fix only findings that demonstrate an I01–I17 false-positive/bypass, unauthorized data promotion, runtime ephemeral dependency, or CEW-FEM boundary violation. Record other suggestions as backlog/proposed future spec.

- [ ] **Step 5: Re-run exact-head qualification only if blocker code changes**

Any blocker fix creates a new head and therefore requires the full gate again. Metadata-only thread replies do not create a new code head.

- [ ] **Step 6: Promote PR #147 to Ready for review only when the stop criterion is satisfied**

Do not merge. Do not open CEW-FEM-01 yet. Present the final integration state for explicit human merge decision.

- [ ] **Step 7: Commit documentation changes, if any**

```bash
git add docs/cew-contract/CEW_CONTRACT_01_QUALIFICATION_REPORT.md evidence/cew-contract-01/model-generation
git commit -m "docs: record stabilized CEW-CONTRACT-01 qualification"
```
