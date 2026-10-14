# CEW Gate Authority Task 9 — Trusted Qualification Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Task 9 trusted `workflow_dispatch` qualification control plane that evaluates an exact PR head H as data through the already-promoted G0/A0 trust anchors, preserves the Qualification Receipt across a verified same-run artifact handoff, and fails closed without changing G0/A0 or authorizing CEW-FEM.

**Architecture:** Keep the promoted `cew_gate_authority/` G0 package immutable. Add a separate `cew_gate_control_plane/` B-layer package for dispatch/PR binding, exact bare Candidate acquisition, trust-anchor verification, handoff envelope integrity, and final decision semantics. The production workflow is a thin orchestrator over these tested primitives; a separate PR-validation workflow certifies Task 9 without making the production workflow itself respond to PR events.

**Tech Stack:** Python 3.12.15 standard library, Git CLI, GitHub Actions on `ubuntu-24.04`, `unittest`, actionlint 1.7.12, zizmor 1.30.1, CodeQL, official GitHub Actions pinned by full SHA.

**Spec:** `docs/superpowers/specs/2026-10-14-cew-gate-authority-task9-trusted-workflow-design.md`

## Global Constraints

- Baseline `main`: `692630b3961bff770273e170181c5e025deafdc4`.
- G0 exact reviewed commit: `1f32a24f456e7db18c994096e4c8f5067222a592`.
- G0 source bundle SHA-256: `b56a98461373f59bc54ad3bd88d3047cff45a7f840b862248a99cd33ed3fe766`.
- G0 manifest blob SHA: `318a38199e5d7643e654442b9d92cbf41c94dd7f`.
- A0 authority: `N12_CEW_CONTRACT_01_A0`; blob `d6f71146b5b833650f1943021d956e1a2d742563`; SHA-256 `88ab731c986cef0af474bf567a9bb19a12a43dcdbef2de6cb211107b17f92dbb`.
- Operational Authority O: `d806dcca72779b5a186defe557a7a9b739575a90`.
- Do not modify any file whose bytes contribute to the promoted G0 source bundle, A0, or `G0_MANIFEST.json`.
- Production trigger is **only** `workflow_dispatch`; a CEW-canonical run requires repository `antoniocorsano-boop/N12`, `refs/heads/main`, and `ref_type=branch`.
- Production dispatch inputs are exactly `pr_number` and `candidate_sha`.
- Candidate H is never checked out, imported, executed, used as an Action, used for dependency installation, or used as a working directory.
- Production permissions contain no write scope, no secret, no OIDC, and no attestation permission.
- Production action pins are exact: checkout `3d3c42e5aac5ba805825da76410c181273ba90b1`; setup-python `5fda3b95a4ea91299a34e894583c3862153e4b97`; upload-artifact `cf430e030ddbb5b0abf93d22962f4752f3646cd9`; download-artifact `9000827ccba6bdab643e8b6fd33ac0654aef8333`.
- Artifact handoff uses the upload-returned `artifact-id`; name is not authority. `overwrite: false`, `if-no-files-found: error`, download `digest-mismatch: error`.
- A G0 behavior/schema/invariant change is a G1/A1 stop condition, not a Task 9 remediation.
- PR #147 remains frozen/read-only; no auto-merge; no CEW-FEM work.
- Execute implementation in an isolated worktree created from the approved design branch after loading `superpowers:using-git-worktrees`.

## File Structure

- Create `cew_gate_control_plane/__init__.py` — B-layer package identity only.
- Create `cew_gate_control_plane/contracts.py` — strict dispatch, PR metadata, and trusted-constant contracts.
- Create `cew_gate_control_plane/candidate_fetch.py` — exact bare fetch of `refs/pull/<PR>/head`; no checkout.
- Create `cew_gate_control_plane/trust_anchor.py` — strict promotion record and materialized G0/A0 verification.
- Create `cew_gate_control_plane/handoff.py` — strict handoff envelope, canonical/transport digests, exact artifact directory verification.
- Create `cew_gate_control_plane/decision.py` — final fail-closed state reduction.
- Create `cew_gate_control_plane/cli.py` — thin CLI adapters only; no CEW invariant logic.
- Create `tests/cew_gate_control_plane/test_contracts.py`.
- Create `tests/cew_gate_control_plane/test_candidate_fetch.py`.
- Create `tests/cew_gate_control_plane/test_trust_anchor.py`.
- Create `tests/cew_gate_control_plane/test_handoff.py`.
- Create `tests/cew_gate_control_plane/test_decision.py`.
- Create `tests/cew_gate_control_plane/test_workflow_contract.py`.
- Create `.github/workflows/cew-gate-authority.yml` — production, `workflow_dispatch` only.
- Create `.github/workflows/validate-cew-gate-authority-task9.yml` — PR validation only; never production authority.
- Create `docs/cew-gate-authority/CEW_GATE_AUTHORITY_TASK9_ASSURANCE_REPORT_v1.md` — exact-head assurance evidence.

## Review Focus

The spec's mandatory 34-case matrix is assigned below. Add these five additional regression classes because they are plausible ambiguity/bypass surfaces not separately named in that matrix:

1. **Duplicate JSON keys** in PR metadata, promotion record, receipt, or handoff envelope must fail strict parsing rather than last-key-wins. Covered in Tasks 1, 3, and 4.
2. **Artifact directory shape** with any extra or missing file must fail; only `qualification-receipt.json` and `handoff-envelope.json` are accepted. Covered in Task 4.
3. **Fetched PR ref object type** must be a Git commit, not merely an object whose textual SHA matches. Covered in Task 2.
4. **Run identity type confusion** (`true`, strings, zero/negative values) for `run_id`/`run_attempt` must fail envelope validation. Covered in Task 4.
5. **Missing/null head repository identity** must fail PR binding even if `head.sha` matches. Covered in Task 1.

---

### Task 1: B-layer dispatch and PR binding contracts

**Files:**
- Create: `cew_gate_control_plane/__init__.py`
- Create: `cew_gate_control_plane/contracts.py`
- Create: `tests/cew_gate_control_plane/test_contracts.py`

**Interfaces:**
- Produces `DispatchRequest(pr_number: int, candidate_sha: str)`.
- Produces `PrBinding(pr_number: int, head_repository: str, head_sha: str)`.
- Produces `validate_dispatch_context(repository: str, ref: str, ref_type: str, pr_number: object, candidate_sha: object) -> DispatchRequest`.
- Produces `load_strict_json_bytes(data: bytes, *, label: str) -> dict[str, object]` with duplicate-key rejection.
- Produces `validate_pr_metadata(metadata: dict[str, object], request: DispatchRequest) -> PrBinding`.
- All contract failures raise `ControlPlaneError(code: str)` using the spec's stable failure codes; no CEW I01..I17 logic is implemented here.

- [ ] **Step 1: Write RED dispatch-context tests**

Add named tests asserting exact failure codes for regression cases 1–4:
`test_rejects_non_main_branch`, `test_rejects_tag_ref`, `test_rejects_non_positive_or_non_integral_pr_number`, `test_rejects_noncanonical_candidate_sha`.

Also assert one valid main-branch request produces `DispatchRequest(pr_number=148, candidate_sha=<40-lowercase-hex>)`.

- [ ] **Step 2: Run the RED dispatch tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_contracts.DispatchContractTests -v`
Expected: FAIL because the B-layer package/functions do not exist.

- [ ] **Step 3: Implement dispatch types and `validate_dispatch_context`**

Constants are exact: repository `antoniocorsano-boop/N12`; ref `refs/heads/main`; ref type `branch`; SHA regex `^[0-9a-f]{40}$`; `bool` is not accepted as an integer PR number.

- [ ] **Step 4: Make dispatch tests GREEN**

Run the Step 2 command.
Expected: all `DispatchContractTests` PASS.

- [ ] **Step 5: Write RED strict-JSON and PR-metadata tests**

Cover mandatory cases 5–8 plus Review Focus 1/5:
`test_rejects_unavailable_or_nonobject_pr_metadata`, `test_rejects_closed_pr`, `test_rejects_wrong_base_repository_or_branch`, `test_rejects_pr_head_mismatch`, `test_rejects_missing_head_repository`, `test_rejects_duplicate_json_keys`.

Valid metadata must require: `number=request.pr_number`, `state=open`, base repo `antoniocorsano-boop/N12`, base ref `main`, head SHA exact request SHA, non-empty `head.repo.full_name`.

- [ ] **Step 6: Run RED PR-binding tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_contracts.PrMetadataContractTests -v`
Expected: FAIL for missing strict loader/PR binding.

- [ ] **Step 7: Implement strict JSON loader and `validate_pr_metadata`**

Duplicate object keys fail with the caller-supplied control-plane code; unexpected structural types fail closed. Return only the normalized `PrBinding`; never shell-quote or interpolate metadata values.

- [ ] **Step 8: Run full Task 1 GREEN**

Run: `python -m unittest tests.cew_gate_control_plane.test_contracts -v`
Expected: PASS.

- [ ] **Step 9: Commit Task 1**

```bash
git add cew_gate_control_plane/__init__.py cew_gate_control_plane/contracts.py tests/cew_gate_control_plane/test_contracts.py
git commit -m "feat: add task9 dispatch and PR binding contracts"
```

---

### Task 2: Exact Candidate acquisition as Git data only

**Files:**
- Create: `cew_gate_control_plane/candidate_fetch.py`
- Create: `tests/cew_gate_control_plane/test_candidate_fetch.py`
- Reuse: `tests/cew_gate_authority/test_no_exec_integration.py`

**Interfaces:**
- Consumes `DispatchRequest`/`PrBinding` from Task 1.
- Produces `fetch_candidate(base_repository_url: str, pr_number: int, requested_sha: str, destination: Path) -> str` returning the exact fetched commit SHA.
- Destination must become a bare repository with no working tree; the function never runs a command sourced from H.

- [ ] **Step 1: Write RED exact-fetch tests**

Use temporary local Git repositories to model the base repository and synthetic `refs/pull/<n>/head`.
Cover mandatory cases 9–10: `test_force_push_between_metadata_and_fetch_fails`, `test_fetched_ref_must_equal_requested_h`.
Cover Review Focus 3: `test_fetched_ref_must_resolve_to_commit_object`.

- [ ] **Step 2: Run RED exact-fetch tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_candidate_fetch.CandidateFetchIdentityTests -v`
Expected: FAIL because `candidate_fetch` does not exist.

- [ ] **Step 3: Implement `fetch_candidate` minimally**

Required Git behavior: create destination with `git init --bare`; set a dedicated empty `core.hooksPath`; fetch exactly `refs/pull/<pr_number>/head` without tags/submodules; resolve `FETCH_HEAD`; require object type `commit`; compare SHA exactly to `requested_sha`. Convert Git/process failures to `CANDIDATE_REF_FETCH_FAILED`; identity mismatch to `CANDIDATE_FETCHED_SHA_MISMATCH`.

- [ ] **Step 4: Make exact-fetch tests GREEN**

Run Step 2 command.
Expected: PASS.

- [ ] **Step 5: Write RED no-exec/fork-data tests**

Cover mandatory cases 11–13:
`test_public_fork_candidate_is_accepted_as_data_via_base_pr_ref`, `test_malicious_candidate_files_are_never_executed`, `test_candidate_copies_of_gate_or_authority_do_not_affect_trusted_inputs`.
The malicious fixture must include Python, shell, package scripts, local Action, workflow, executable bit, and marker files; markers must remain absent.

- [ ] **Step 6: Run RED no-exec tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_candidate_fetch.CandidateNoExecTests tests.cew_gate_authority.test_no_exec_integration -v`
Expected: new Task 9 tests RED; existing G0 no-exec tests remain PASS.

- [ ] **Step 7: Complete no-exec implementation without adding checkout paths**

Candidate acquisition exposes only the bare `.git` directory path to the downstream G0 `CandidateReader`; do not add worktree materialization helpers.

- [ ] **Step 8: Run Task 2 GREEN**

Run Step 6 command.
Expected: all PASS; no marker created.

- [ ] **Step 9: Commit Task 2**

```bash
git add cew_gate_control_plane/candidate_fetch.py tests/cew_gate_control_plane/test_candidate_fetch.py
git commit -m "feat: acquire exact candidate head without checkout"
```

---

### Task 3: Promoted G0/A0/O trust-anchor verification

**Files:**
- Create: `cew_gate_control_plane/trust_anchor.py`
- Create: `tests/cew_gate_control_plane/test_trust_anchor.py`
- Read-only fixtures/source: `governance/cew-gate-authority/G0_PROMOTION_RECORD_v1.json`
- Read-only G0 paths at commit `1f32a24f456e7db18c994096e4c8f5067222a592`.

**Interfaces:**
- Produces `TrustAnchor` with exact G0 commit/source-bundle/manifest blob, A0 ID/blob/SHA-256, and O commit.
- Produces `load_and_verify_promotion_record(path: Path) -> TrustAnchor`.
- Produces `verify_materialized_gate(git_dir: Path, anchor: TrustAnchor) -> None`.
- Produces `verify_operational_commit_available(git_dir: Path, anchor: TrustAnchor) -> None`.

- [ ] **Step 1: Write RED promotion-record tests**

Cover mandatory case 14 and Review Focus 1: missing record, duplicate JSON key, wrong schema/version/decision/repository, any non-false authority flag, false `cew_fem_01_required`, or contradictory G/A/O identity must raise `PROMOTION_RECORD_INVALID`.

- [ ] **Step 2: Run RED promotion tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_trust_anchor.PromotionRecordTests -v`
Expected: FAIL for missing module/functions.

- [ ] **Step 3: Implement strict promotion-record verification**

Hard-code only the identities already frozen by the spec. Do not derive new engineering facts. Do not interpret `promotion_state=CANDIDATE` as failure; promotion authority is the external promotion record.

- [ ] **Step 4: Make promotion tests GREEN**

Run Step 2 command.
Expected: PASS.

- [ ] **Step 5: Write RED materialized G0/A0 identity tests**

Cover mandatory cases 15–19 individually:
`test_rejects_wrong_g0_commit`, `test_rejects_wrong_g0_manifest_blob`, `test_rejects_wrong_source_bundle_digest`, `test_rejects_wrong_a0_blob`, `test_rejects_wrong_a0_sha256`.

Tests must use temporary Git repos/commits; no mutation of the promoted repository files.

- [ ] **Step 6: Run RED gate identity tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_trust_anchor.MaterializedGateTests -v`
Expected: FAIL until identity verification exists.

- [ ] **Step 7: Implement `verify_materialized_gate`**

Verify exact commit identity and Git blob identities through Git object commands, then SHA-256 A0 bytes and source-bundle field from the exact manifest. No fallback to branch names/tags.

- [ ] **Step 8: Write RED O availability test**

Mandatory case 20: missing/unfetchable O must produce `OPERATIONAL_AUTHORITY_FETCH_FAILED`; available exact O passes without inspecting Candidate H.

- [ ] **Step 9: Implement and run full Task 3 GREEN**

Run: `python -m unittest tests.cew_gate_control_plane.test_trust_anchor -v`
Expected: PASS.

- [ ] **Step 10: Commit Task 3**

```bash
git add cew_gate_control_plane/trust_anchor.py tests/cew_gate_control_plane/test_trust_anchor.py
git commit -m "feat: verify promoted gate authority trust anchors"
```

---

### Task 4: Receipt handoff envelope and transport integrity

**Files:**
- Create: `cew_gate_control_plane/handoff.py`
- Create: `tests/cew_gate_control_plane/test_handoff.py`
- Read-only reference: `cew_gate_authority/receipt.py` at promoted G0.

**Interfaces:**
- Produces frozen `HandoffContext(run_id: int, run_attempt: int, control_plane_base_sha: str, candidate_pr_number: int, candidate_head_repository: str, candidate_head_sha: str)`.
- Produces `canonical_json_sha256(data: bytes) -> str` using strict JSON parsing and `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"))` bytes with no trailing newline.
- Produces `transport_sha256(data: bytes) -> str` over exact file bytes.
- Produces `build_handoff_envelope(receipt_path: Path, context: HandoffContext, anchor: TrustAnchor, qualification_exit_code: int) -> dict[str, object]`.
- Produces `verify_handoff_directory(directory: Path, envelope_context: HandoffContext, anchor: TrustAnchor) -> dict[str, object]` requiring exactly the two artifact files.

- [ ] **Step 1: Write RED PASS/FAIL receipt handoff tests**

Cover mandatory cases 21–23: PASS receipt survives handoff; qualified=false receipt with G0 exit 1 survives handoff; exit 2/no receipt is rejected as `RECEIPT_NOT_EMITTED` when a receipt is required by the path under test.

- [ ] **Step 2: Run RED base handoff tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_handoff.HandoffHappyAndFailReceiptTests -v`
Expected: FAIL for missing handoff module.

- [ ] **Step 3: Implement strict receipt digest/envelope building**

Envelope fields and schema must be exactly those in spec §10. Reject duplicate JSON keys. `qualification_exit_code` accepts only exact ints 0/1/2, not bool/string.

- [ ] **Step 4: Make base handoff tests GREEN**

Run Step 2 command.
Expected: PASS.

- [ ] **Step 5: Write RED tamper/replay tests**

Cover mandatory cases 24–29:
byte mutation; newline mutation; correct canonical digest but wrong transport digest; wrong `run_id`; previous/wrong `run_attempt`; incoherent B/G/A/H/O.
Cover Review Focus 4: non-positive/non-int/bool run identity fails.

- [ ] **Step 6: Write RED artifact-shape tests**

Cover mandatory case 30 and Review Focus 2: missing expected file, extra file, wrong artifact payload directory, or empty artifact identity all fail. The test names must make clear that artifact **name** alone is never accepted as authority.

- [ ] **Step 7: Implement exact handoff verification**

Require directory filenames set equality with `{qualification-receipt.json, handoff-envelope.json}`; verify current run/attempt, all trusted identities, both receipt digests, and strict schema before returning the parsed receipt.

- [ ] **Step 8: Run full Task 4 GREEN**

Run: `python -m unittest tests.cew_gate_control_plane.test_handoff -v`
Expected: PASS.

- [ ] **Step 9: Commit Task 4**

```bash
git add cew_gate_control_plane/handoff.py tests/cew_gate_control_plane/test_handoff.py
git commit -m "feat: add verified qualification receipt handoff"
```

---

### Task 5: Fail-closed decision reducer and B-layer CLI

**Files:**
- Create: `cew_gate_control_plane/decision.py`
- Create: `cew_gate_control_plane/cli.py`
- Create: `tests/cew_gate_control_plane/test_decision.py`
- Modify tests from Tasks 1–4 only if CLI integration needs assertions; do not change their semantic expectations.

**Interfaces:**
- Produces `FinalDecision(status: str, success: bool, failure_code: str | None)`.
- Produces `reduce_decision(*, qualify_job_result: str, qualification_exit_code: int | None, receipt_emitted: bool, handoff_job_result: str) -> FinalDecision`.
- CLI commands: `preflight`, `fetch-candidate`, `verify-trust`, `build-handoff`, `verify-handoff`, `decision`.
- Every command writes machine-readable outputs to an explicit `--output-json` path and exits `0` on command success, `2` on B-layer invocation/infrastructure failure; `decision` exits `0` only for final qualified success and `1` for a valid non-success final decision.

- [ ] **Step 1: Write RED decision truth-table tests**

Assert exact spec semantics: exit 0 + handoff PASS => success; exit 1 + handoff PASS => `NOT_QUALIFIED`; exit 2 => `CONTROL_PLANE_OR_INVOCATION_ERROR`; missing expected receipt => fail; skipped/failed handoff => fail; unknown result/exit => fail.

- [ ] **Step 2: Run RED decision tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_decision.DecisionReducerTests -v`
Expected: FAIL.

- [ ] **Step 3: Implement `reduce_decision` and make truth table GREEN**

Run Step 2 command.
Expected: PASS; no implicit green state exists.

- [ ] **Step 4: Write RED CLI integration tests**

For each command verify required arguments, JSON output shape, and propagation of stable control-plane failure code. Ensure no CLI command implements or re-evaluates I01..I17.

- [ ] **Step 5: Implement thin CLI adapters**

The CLI delegates only to Tasks 1–4/decision functions. Do not duplicate validation logic in argparse actions or shell snippets.

- [ ] **Step 6: Run Task 5 GREEN plus G0 compile isolation**

Run:
`python -m unittest tests.cew_gate_control_plane.test_decision -v`
`python -m compileall -q cew_gate_control_plane`
`python -m unittest tests.cew_gate_authority.test_g0_manifest -v`
Expected: all PASS; G0 manifest tests demonstrate Task 9 files are outside the promoted source bundle.

- [ ] **Step 7: Commit Task 5**

```bash
git add cew_gate_control_plane/decision.py cew_gate_control_plane/cli.py tests/cew_gate_control_plane/test_decision.py
git commit -m "feat: add task9 fail closed control plane CLI"
```

---

### Task 6: Production workflow as a thin trusted orchestrator

**Files:**
- Create: `.github/workflows/cew-gate-authority.yml`
- Create: `tests/cew_gate_control_plane/test_workflow_contract.py`

**Interfaces:**
- Consumes only the Task 1–5 CLI plus promoted G0/A0/O identities.
- Produces three jobs exactly: `qualify`, `verify-handoff`, `decision`.
- Production workflow event surface is exactly `workflow_dispatch` with exactly two inputs.

- [ ] **Step 1: Write RED workflow static contract tests before YAML**

Use text/structural assertions only as regression checks, not as a trust-boundary parser. Cover mandatory cases 31–34 and these exact requirements:
- production workflow has only `workflow_dispatch`;
- exactly two inputs (`pr_number`, `candidate_sha`);
- permissions contain no write scope/secret/OIDC/attestation;
- `qualify` has only `contents: read`, `pull-requests: read`;
- `verify-handoff` has only `actions: read`;
- H is never passed to `actions/checkout`;
- `download-artifact` uses `artifact-ids` and `digest-mismatch: error`;
- all four production Actions are pinned to the exact §12 SHAs;
- no tag-form `uses:` for those Actions.

- [ ] **Step 2: Run RED workflow contract tests**

Run: `python -m unittest tests.cew_gate_control_plane.test_workflow_contract -v`
Expected: FAIL because production workflow does not exist.

- [ ] **Step 3: Implement production workflow skeleton**

Use runner `ubuntu-24.04`, Python `3.12.15`, exact Action SHAs. `qualify` first validates repository/ref/ref-type/input, then fetches PR metadata, then Candidate H. No Candidate read occurs before non-main rejection.

- [ ] **Step 4: Wire exact trusted materialization and G0 invocation**

Checkout only B at exact `${{ github.sha }}` with `persist-credentials:false`, `submodules:false`, `lfs:false`. Fetch exact G0/O objects from public N12; materialize G0/A0 in a separate trusted directory; call `verify-trust`; invoke promoted G0 CLI with B/G/A/H/O exact identities.

Capture G0 exit code without prematurely failing the job. Preserve a receipt for exits 0/1; classify exit 2 as invocation/control-plane failure.

- [ ] **Step 5: Wire immutable artifact handoff**

Build envelope, upload exactly the two handoff files once with `overwrite:false` and `if-no-files-found:error`; expose `artifact-id`, `artifact-digest`, G0 exit, receipt-emitted flag, and Candidate binding as job outputs.

`verify-handoff` downloads by `artifact-ids` only, `digest-mismatch:error`, never reads H, then invokes B-layer handoff verification.

- [ ] **Step 6: Wire final `decision` job**

Use `if: always()` and Task 5's reducer. The workflow succeeds only for G0 exit 0 plus verified handoff. Valid G0 exit 1 produces final failure `NOT_QUALIFIED`; all infrastructure/ambiguous states fail.

- [ ] **Step 7: Make workflow contract tests GREEN**

Run Step 2 command.
Expected: PASS.

- [ ] **Step 8: Run actionlint and zizmor locally on production YAML**

Use the already-approved versions/checksums from bootstrap assurance:
- actionlint `1.7.12`, SHA-256 `8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8`;
- zizmor `1.30.1`, SHA-256 `e65324f4430c2717591937edcec90ccbefaf14c174f8ec9415e03ca875b46e1a`.

Expected: actionlint PASS; zizmor no blocker. Any suppression must be explicit, minimal, and reviewed; do not add a suppression merely to get GREEN.

- [ ] **Step 9: Commit Task 6**

```bash
git add .github/workflows/cew-gate-authority.yml tests/cew_gate_control_plane/test_workflow_contract.py
git commit -m "feat: add trusted CEW qualification workflow"
```

---

### Task 7: PR validation workflow and complete anti-churn regression gate

**Files:**
- Create: `.github/workflows/validate-cew-gate-authority-task9.yml`
- Modify: `tests/cew_gate_control_plane/test_workflow_contract.py` only to add validation-workflow safety assertions, not production semantics.

**Interfaces:**
- Validation workflow is not a CEW qualification authority. It may run on `pull_request` because it has no secrets/write scopes and only validates code/workflow text.
- It must never be confused with `.github/workflows/cew-gate-authority.yml` production evidence.

- [ ] **Step 1: Write RED validation-workflow safety tests**

Require PR validation workflow to have read-only permissions, checkout exact PR head, no secrets/write scopes, and no invocation of production `workflow_dispatch` or qualification against a real PR candidate.

- [ ] **Step 2: Create validation workflow**

Jobs:
1. Task 9 unit/integration tests (`tests/cew_gate_control_plane`);
2. existing full `tests/cew_gate_authority` suite;
3. `compileall` both packages;
4. actionlint on production + validation YAML;
5. zizmor on production + validation YAML;
6. CodeQL Python analysis using the existing repository-approved pinned CodeQL action identity unless a separately reviewed update is explicitly authorized.

Use production checkout/setup-python pins from the approved spec. No production qualification is triggered.

- [ ] **Step 3: Run complete local regression ladder**

Run:
`python -m unittest discover -s tests/cew_gate_control_plane -p 'test_*.py' -v`
`python -m unittest discover -s tests/cew_gate_authority -p 'test_*.py' -v`
`python -m compileall -q cew_gate_control_plane cew_gate_authority`

Expected: all PASS. The existing G0 suite count may increase only if intentionally adding no tests there; otherwise its established tests remain unchanged.

- [ ] **Step 4: Verify all 34 mandatory regression cases are named and exercised**

Create a one-to-one checklist in the assurance report draft mapping spec §15 items 1–34 to test method names. No grouped generic test may hide an unexercised required case.

- [ ] **Step 5: Commit Task 7**

```bash
git add .github/workflows/validate-cew-gate-authority-task9.yml tests/cew_gate_control_plane/test_workflow_contract.py
git commit -m "ci: certify task9 trusted control plane"
```

---

### Task 8: Exact-head assurance package before independent review

**Files:**
- Create: `docs/cew-gate-authority/CEW_GATE_AUTHORITY_TASK9_ASSURANCE_REPORT_v1.md`
- Do not modify G0/A0/promotion record.

**Interfaces:**
- Consumes completed Tasks 1–7 and their CI run evidence.
- Produces a human-readable exact-head assurance report; it does not promote/activate Task 9.

- [ ] **Step 1: Verify diff scope before final certification**

Compare Task 9 branch to baseline `692630b3961bff770273e170181c5e025deafdc4`.
Expected changes only in: Task 9 spec/plan, `cew_gate_control_plane/`, `tests/cew_gate_control_plane/`, the two Task 9 workflow files, and Task 9 assurance report. Any G0/A0/promotion-record change is a hard STOP.

- [ ] **Step 2: Run exact-head full certification**

Require the validation workflow on the exact current head to complete success for Task 9 tests, existing G0 suite, compile, actionlint, zizmor, and CodeQL. Record run/job IDs and exact head SHA.

- [ ] **Step 3: Verify trust anchor byte identity against promoted references**

On the exact head assert:
- G0 source bundle identity unchanged;
- `G0_MANIFEST.json` blob still `318a38199e5d7643e654442b9d92cbf41c94dd7f` when read from promoted commit;
- A0 promoted blob/digest still exact;
- promotion record still binds the same G0/A0/O identities.

- [ ] **Step 4: Complete assurance report**

Record:
- exact head;
- Task 9 file scope;
- test counts/results;
- mapping of mandatory cases 1–34 + five Review Focus tests;
- production action pins;
- actionlint/zizmor/CodeQL evidence;
- explicit statement that no production activation, merge, auto-merge, CEW-FEM, or #147 change has occurred.

- [ ] **Step 5: Commit assurance report and rerun exact-head certification**

```bash
git add docs/cew-gate-authority/CEW_GATE_AUTHORITY_TASK9_ASSURANCE_REPORT_v1.md
git commit -m "docs: record task9 control plane assurance"
```

After this commit, rerun the full certification. The new commit becomes the only candidate for independent review.

- [ ] **Step 6: Request one fresh independent Codex review on the exact final head**

Review focus: trust boundary B/G/A/H/O, no-exec Candidate, dispatch ref semantics, race-safe H acquisition, G0/A0 immutability, artifact-id handoff, dual receipt digests, permission minimization, action pins, and fail-closed decision reducer.

Do not modify the branch while review is pending.

- [ ] **Step 7: Handle review result using `superpowers:receiving-code-review`**

If clean: mark technical assurance as `TASK9_ASSURANCE_PASS — HUMAN MERGE/ACTIVATION DECISION REQUIRED` and stop.

If findings: verify each technically. Any finding requiring G0/A0/I01..I17/schema-R changes triggers the Task 9 stop rule and a G1/A1 design cycle. Only genuine B-layer/workflow defects inside this approved design may be remediated with new RED→GREEN tests, followed by full recertification and a new exact-head review.

---

## Execution-time Gate Sequence

Before Task 1 implementation:

1. load `superpowers:using-git-worktrees` and create an isolated worktree/implementation branch from the approved design head;
2. preserve the design branch as the immutable spec/plan review point;
3. load `superpowers:test-driven-development`;
4. execute Tasks 1–8 in order; do not parallelize tasks whose interfaces depend on prior tasks;
5. use `superpowers:verification-before-completion` before any claim of GREEN/complete;
6. never merge or activate production automatically.

## Self-Review Result

- **Spec coverage:** §§1–21 are mapped to Tasks 1–8; all 34 mandatory regressions are assigned explicitly; five additional ambiguity classes are added in Review Focus.
- **Type consistency:** `DispatchRequest`, `PrBinding`, `TrustAnchor`, `HandoffContext`, and `FinalDecision` have one producer and named consumers; the CLI wraps rather than duplicates these interfaces.
- **Boundary consistency:** `cew_gate_control_plane/` is separate from promoted `cew_gate_authority/`; no Task requires a G0/A0 edit.
- **Workflow scope:** production YAML is `workflow_dispatch` only; PR validation is a separate non-authoritative workflow.
- **Proportion/YAGNI:** no attestation, status publisher, ruleset, `pull_request_target`, dependency lockfile, solver, CEW-FEM, or #147 migration is introduced.
- **Stop rule:** any need to change G0/A0/I01..I17/Receipt schema is escalated to G1/A1 instead of patched into Task 9.
