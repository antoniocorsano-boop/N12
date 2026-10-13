# CEW-GATE-AUTHORITY-01 Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap and human-promote a trusted CEW Gate Authority G0/A0 that evaluates an untrusted Candidate H strictly as data, produces a B/G/A/H/O-bound Qualification Receipt, and can run from a trusted GitHub control plane without executing candidate code.

**Architecture:** Build a small Python 3.12 Gate Core with standard-library runtime dependencies only, a bare-Git `CandidateReader`, a trusted Frozen Authority A0, deterministic N12 replay from operational commit O, canonical Receipt generation, and a minimal trusted trigger workflow. Bootstrap assurance is explicitly non-self-validating: external workflow analyzers, adversarial/integration tests, and a human promotion record are required before G0/A0 become trust anchors.

**Tech Stack:** Python 3.12 standard library; Git CLI; GitHub Actions; actionlint; zizmor; GitHub code scanning where available; GitHub Artifact Attestations/Sigstore when repository policy permits.

**Spec:** `docs/superpowers/specs/2026-10-13-cew-gate-authority-01-design.md`

## Global Constraints

- Repository: `antoniocorsano-boop/N12`, public, user-owned.
- Start implementation from `main`, never from PR #147 or its head.
- PR #147 remains frozen; no round-6 parser hardening.
- Operational Authority is exactly `d806dcca72779b5a186defe557a7a9b739575a90`.
- Candidate H is untrusted even when authored by the repository owner.
- No code, local action, hook, package manifest, plugin, or executable configuration from H may be executed.
- Runtime Gate Core dependencies are Python standard library + Git CLI only.
- Candidate access uses Git objects/bare repository; no candidate working tree is used by G0.
- Only regular Git blobs on A0 allowlisted paths are qualification inputs; symlinks and gitlinks fail closed.
- Runtime candidate limits: maximum 256 allowlisted blobs, 8 MiB per blob, 64 MiB aggregate; JSON depth 64; CSV rows 250,000. Any stricter per-file limit in A0 wins.
- `qualify` has at most `contents: read`, no secrets, no `id-token: write`, no `attestations: write`, no PR write permission.
- `attest` is a separate success-only job; it never reads H and verifies the Receipt digest before attesting.
- GitHub Actions used by the trusted workflow must be pinned to reviewed full commit SHAs.
- `pull_request_target` is preferred only after repository Actions Policy is verified; otherwise use trusted `workflow_dispatch`.
- `pull_request_target` `GITHUB_SHA` is B, not H; CEW qualification identity is proven by R, not by the run SHA.
- G0 and A0 cannot self-promote. Human promotion is a mandatory irreversible gate.
- No solver selection, structural analysis, `SolverRun`, `Result`, material/load/geotechnical assumption, or CEW-FEM-01 implementation.
- No auto-merge.

## Review Focus

1. **Force-push/race on H:** once a run records H, every candidate blob must be read from that exact commit even if the PR head moves during the run. Task 3 owns the integration test.
2. **Path/object confusion:** `..`, absolute paths, Unicode-normalization collisions, symlink mode `120000`, gitlink mode `160000`, and duplicate normalized paths must fail closed. Task 3 owns these tests.
3. **Candidate resource abuse:** oversized blobs, too many files, excessive JSON depth, and excessive CSV row count must fail before semantic qualification. Tasks 3 and 5 own these tests.
4. **Receipt handoff substitution:** an altered Receipt or digest between `qualify` and `attest` must be rejected. Task 9 owns the test.
5. **Trusted dependency drift:** a changed action/tool/G/A identity must not silently become trusted. Tasks 7, 8, and 10 own the manifest and assurance checks.

---

## Planned File Structure

### Runtime package

- `cew_gate_authority/__init__.py` — package/version exports only.
- `cew_gate_authority/types.py` — immutable identities/results/Receipt data types.
- `cew_gate_authority/failure_codes.py` — stable failure-code constants.
- `cew_gate_authority/candidate_reader.py` — bare-Git candidate object access and path/type/size enforcement.
- `cew_gate_authority/authority.py` — load/validate trusted A0 and candidate allowlist.
- `cew_gate_authority/operational.py` — materialize and verify O objects.
- `cew_gate_authority/replay.py` — deterministic ModelGeneration replay using only O.
- `cew_gate_authority/qualification.py` — CEW-CONTRACT-01 invariant evaluation over candidate data + A0 + replay.
- `cew_gate_authority/receipt.py` — canonical Receipt serialization, digest, and verification.
- `cew_gate_authority/event_identity.py` — pure parsing/validation of trusted event metadata into B/H identities.
- `cew_gate_authority/cli.py` — command-line entry point; no GitHub-specific write actions.

### Trusted governance data

- `governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json` — trusted Frozen Authority.
- `governance/cew-gate-authority/gate-core/G0_MANIFEST.json` — Gate Core version/source/dependency identity.
- `governance/cew-gate-authority/schemas/QUALIFICATION_RECEIPT_v1.schema.json` — Receipt contract.
- `governance/cew-gate-authority/TRUSTED_TOOLCHAIN_v1.json` — assurance tool/action pins and digests.
- `governance/cew-gate-authority/G0_PROMOTION_RECORD_v1.json` — initially absent; created only after human promotion decision.

### Workflows

- `.github/workflows/validate-cew-gate-authority-bootstrap.yml` — non-authoritative bootstrap CI for G0/A0 PR.
- `.github/workflows/cew-gate-authority.yml` — trusted qualification trigger, added/activated only after G0/A0 promotion.

### Tests

- `tests/cew_gate_authority/test_types_and_receipt.py`
- `tests/cew_gate_authority/test_candidate_reader.py`
- `tests/cew_gate_authority/test_authority.py`
- `tests/cew_gate_authority/test_operational_replay.py`
- `tests/cew_gate_authority/test_qualification.py`
- `tests/cew_gate_authority/test_candidate_properties.py`
- `tests/cew_gate_authority/test_no_exec_integration.py`
- `tests/cew_gate_authority/test_event_identity.py`
- `tests/cew_gate_authority/test_receipt_handoff.py`

### Evidence / operations

- `docs/cew-gate-authority/CEW_GATE_AUTHORITY_PLATFORM_PREFLIGHT_v1.md`
- `docs/cew-gate-authority/CEW_GATE_AUTHORITY_G0_ASSURANCE_REPORT_v1.md`
- `docs/cew-gate-authority/CEW_GATE_AUTHORITY_DEPLOYMENT_RUNBOOK_v1.md`

---

### Task 1: Platform preflight and bootstrap boundary

**Files:**
- Create: `docs/cew-gate-authority/CEW_GATE_AUTHORITY_PLATFORM_PREFLIGHT_v1.md`
- Test: no code test; evidence must be source-backed and current.

**Interfaces:**
- Consumes: approved design spec and current N12 repository settings.
- Produces: a `PREFERRED_TRIGGER` decision (`pull_request_target` or `workflow_dispatch`), attestation availability status, ruleset target, and any human-only Settings actions required before activation.

- [ ] **Step 1: Re-verify current repository facts**

Record `main` protection/ruleset state, public/user-owned status, and current Actions configuration that is readable through GitHub APIs.

- [ ] **Step 2: Verify account-visible settings that APIs cannot prove**

Document, without changing settings yet: availability of Actions Policies for `pull_request_target`, Artifact Attestations, and repository-level rulesets. If a setting is not observable programmatically, mark it `HUMAN_VERIFICATION_REQUIRED` rather than assuming PASS.

- [ ] **Step 3: Resolve trigger mode**

Set exactly one of:
- `PREFERRED_TRIGGER=pull_request_target` only if explicit event policy can be configured safely;
- `PREFERRED_TRIGGER=workflow_dispatch` otherwise.

- [ ] **Step 4: Commit**

```bash
git add docs/cew-gate-authority/CEW_GATE_AUTHORITY_PLATFORM_PREFLIGHT_v1.md
git commit -m "docs: record CEW Gate Authority platform preflight"
```

Expected: no production workflow is activated by this task.

---

### Task 2: Define trusted identities, Receipt contract, and A0

**Files:**
- Create: `cew_gate_authority/types.py`
- Create: `cew_gate_authority/failure_codes.py`
- Create: `cew_gate_authority/receipt.py`
- Create: `governance/cew-gate-authority/schemas/QUALIFICATION_RECEIPT_v1.schema.json`
- Create: `governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json`
- Test: `tests/cew_gate_authority/test_types_and_receipt.py`
- Test: `tests/cew_gate_authority/test_authority.py`

**Interfaces:**
- Produces: `CandidateIdentity`, `ControlPlaneIdentity`, `GateCoreIdentity`, `AuthorityIdentity`, `OperationalIdentity`, `InvariantResult`, `QualificationReceipt`; `canonical_receipt_bytes(receipt) -> bytes`; `receipt_sha256(receipt) -> str`; `load_authority(path: Path) -> FrozenAuthority`.
- A0 pins O=`d806dcca72779b5a186defe557a7a9b739575a90`, existing six ModelGeneration inputs, builder/source/output identities, registration supports, authority flags, candidate allowlist, and I01–I17 applicability.

- [ ] **Step 1: Write failing identity/Receipt tests**

Tests assert B/G/A/H/O are mandatory, H contains PR + head repository + exact SHA, invariant keys are exactly I01–I17, `qualified=true` is rejected when any applicable invariant fails, and canonical serialization is byte-stable for equivalent dictionary ordering.

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m unittest tests/cew_gate_authority/test_types_and_receipt.py tests/cew_gate_authority/test_authority.py -v`

Expected: FAIL because package/contracts do not yet exist.

- [ ] **Step 3: Implement immutable types, failure codes, canonical Receipt serialization, and A0 loader**

Use `dataclasses(frozen=True)` or equivalent stdlib immutable structures. Canonical JSON uses UTF-8, sorted keys, compact separators, and a terminal newline only where the file representation requires it; the digest function must define whether the newline is included and tests must pin that choice.

- [ ] **Step 4: Build A0 only from already verified #147/O facts**

Do not add engineering values. Copy only authority values that can be reconciled to O/audit evidence; include candidate allowlist and resource limits from Global Constraints.

- [ ] **Step 5: Run tests to verify GREEN**

Run: `python -m unittest tests/cew_gate_authority/test_types_and_receipt.py tests/cew_gate_authority/test_authority.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add cew_gate_authority governance/cew-gate-authority tests/cew_gate_authority
git commit -m "feat: define CEW Gate Authority identities and A0"
```

---

### Task 3: CandidateReader — exact H as non-executable Git data

**Files:**
- Create: `cew_gate_authority/candidate_reader.py`
- Test: `tests/cew_gate_authority/test_candidate_reader.py`
- Test: `tests/cew_gate_authority/test_candidate_properties.py`

**Interfaces:**
- Consumes: `CandidateIdentity`, A0 allowlist/limits.
- Produces: `CandidateReader(repo_git_dir: Path, head_sha: str, limits: CandidateLimits)`; `read_blob(path: str) -> bytes`; `read_text(path: str) -> str`; `verify_allowlisted_surface(paths: Sequence[str]) -> None`.

- [ ] **Step 1: Write failing tests using temporary Git repositories**

Cover exact-commit reads after branch movement, missing path, path outside allowlist, absolute path, `..`, duplicate normalized path, Unicode normalization collision, symlink mode `120000`, gitlink mode `160000`, 8 MiB per-blob overflow, 256-file overflow, and 64 MiB aggregate overflow.

- [ ] **Step 2: Run RED**

Run: `python -m unittest tests/cew_gate_authority/test_candidate_reader.py tests/cew_gate_authority/test_candidate_properties.py -v`

Expected: FAIL because `CandidateReader` does not exist.

- [ ] **Step 3: Implement bare-Git reads with subprocess argument arrays only**

Use Git plumbing commands (`cat-file`, `ls-tree`, or equivalent) with `shell=False`; never create a candidate working tree; always address objects by `head_sha:path` or object SHA resolved from that head; reject non-blob modes/types before reading content.

- [ ] **Step 4: Add deterministic generated path/property corpus**

Use standard-library deterministic generators, not a new runtime dependency, to exercise path separators, normalization, prefix/suffix collisions, boundary sizes, and repeated entries.

- [ ] **Step 5: Run GREEN**

Run the same unittest command.

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add cew_gate_authority/candidate_reader.py tests/cew_gate_authority/test_candidate_reader.py tests/cew_gate_authority/test_candidate_properties.py
git commit -m "feat: read candidate heads as non-executable Git data"
```

---

### Task 4: Operational Authority materialization and deterministic replay

**Files:**
- Create: `cew_gate_authority/operational.py`
- Create: `cew_gate_authority/replay.py`
- Test: `tests/cew_gate_authority/test_operational_replay.py`

**Interfaces:**
- Consumes: `FrozenAuthority`, O repository Git objects.
- Produces: `materialize_operational_authority(repo: Path, authority: FrozenAuthority, dest: Path) -> OperationalMaterialization`; `run_model_generation_replay(materialization, authority, output_path) -> ReplayResult`.

- [ ] **Step 1: Write failing tests for O identity and replay**

Assert O exact SHA, builder Git blob SHA, six exact input paths/digests, registration source blob, replay output identity, SHA-256 `4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`, size `1068121`, and historical timestamp `2026-08-26T09:54:00.472520+00:00`.

- [ ] **Step 2: Run RED**

Run: `python -m unittest tests/cew_gate_authority/test_operational_replay.py -v`

Expected: FAIL.

- [ ] **Step 3: Port only reviewed replay logic from #147 into trusted package**

Reference `scripts/cew_contract_01_replay.py` at audit head `e631b83e22b793c1f5f3740f4f57206ee69f3a93`. Do not port workflow/YAML parsing or round-specific regression machinery.

- [ ] **Step 4: Make operational materialization independent of H**

All builder/input/source reads must resolve from O. Tests must fail if an equivalent path exists in Candidate H with different bytes.

- [ ] **Step 5: Run GREEN**

Run the same unittest command.

Expected: PASS with exact historical output identity/digest/size.

- [ ] **Step 6: Commit**

```bash
git add cew_gate_authority/operational.py cew_gate_authority/replay.py tests/cew_gate_authority/test_operational_replay.py
git commit -m "feat: add trusted operational replay"
```

---

### Task 5: Qualification Engine for I01–I17

**Files:**
- Create: `cew_gate_authority/qualification.py`
- Test: `tests/cew_gate_authority/test_qualification.py`
- Extend: `tests/cew_gate_authority/test_candidate_properties.py`

**Interfaces:**
- Consumes: `CandidateReader`, `FrozenAuthority`, `ReplayResult`, B/G/H identities.
- Produces: `evaluate_qualification(...) -> QualificationReceipt` with stable failure codes.

- [ ] **Step 1: Write one positive and one negative test per invariant family**

I02 is implemented as Trusted Gate Invocation: B/G/A identity, H identity, no-exec, fail-closed, and Receipt binding — never by parsing candidate workflows.

- [ ] **Step 2: Add resource-abuse semantic tests**

JSON depth >64, CSV rows >250,000, malformed UTF-8 where text is required, unexpected schema fields where A0 closes schema, and inconsistent Manifest/Verification/Receipt must fail with stable codes before `qualified=true` can be emitted.

- [ ] **Step 3: Run RED**

Run: `python -m unittest tests/cew_gate_authority/test_qualification.py tests/cew_gate_authority/test_candidate_properties.py -v`

Expected: FAIL.

- [ ] **Step 4: Implement invariant evaluators as small pure functions**

Keep each invariant family independently testable. The engine aggregates results and permits `qualified=true` only when all applicable invariants PASS and the CEW-FEM authority boundary is intact.

- [ ] **Step 5: Run GREEN**

Run the same command.

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add cew_gate_authority/qualification.py tests/cew_gate_authority/test_qualification.py tests/cew_gate_authority/test_candidate_properties.py
git commit -m "feat: evaluate CEW qualification invariants"
```

---

### Task 6: Event identity, CLI, and no-exec end-to-end proof

**Files:**
- Create: `cew_gate_authority/event_identity.py`
- Create: `cew_gate_authority/cli.py`
- Test: `tests/cew_gate_authority/test_event_identity.py`
- Test: `tests/cew_gate_authority/test_no_exec_integration.py`

**Interfaces:**
- Produces: `candidate_from_pull_request_target_event(event: Mapping) -> CandidateIdentity`; `verify_dispatch_candidate(pr_metadata, requested_sha) -> CandidateIdentity`; CLI command `python -m cew_gate_authority.cli qualify ...` writing canonical R and exiting 0 only for qualified PASS.

- [ ] **Step 1: Write failing event/CLI tests**

Assert `pull_request_target` derives B from trusted base metadata and H from `pull_request.head.sha`; dispatch rejects a requested H that is not current for the specified PR.

- [ ] **Step 2: Write no-exec integration test**

Synthetic candidate contains executable Python, shell, local action, Git hook, malicious package manifest, and modified candidate workflow. The test places observable tripwires in each and asserts none run while candidate evidence blobs are still read and qualified.

- [ ] **Step 3: Add force-push/race test**

Create H1, start/bind reader to H1, move branch to H2, assert R still binds/reads H1 only.

- [ ] **Step 4: Run RED**

Run: `python -m unittest tests/cew_gate_authority/test_event_identity.py tests/cew_gate_authority/test_no_exec_integration.py -v`

Expected: FAIL.

- [ ] **Step 5: Implement event identity and CLI**

CLI never performs candidate checkout and never imports from candidate paths. All failures serialize a non-qualified receipt where enough identity is available, then exit non-zero.

- [ ] **Step 6: Run GREEN**

Run the same command.

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add cew_gate_authority/event_identity.py cew_gate_authority/cli.py tests/cew_gate_authority/test_event_identity.py tests/cew_gate_authority/test_no_exec_integration.py
git commit -m "feat: add trusted event identity and qualification CLI"
```

---

### Task 7: G0 manifest and non-self-validating bootstrap assurance

**Files:**
- Create: `governance/cew-gate-authority/gate-core/G0_MANIFEST.json`
- Create: `governance/cew-gate-authority/TRUSTED_TOOLCHAIN_v1.json`
- Create: `.github/workflows/validate-cew-gate-authority-bootstrap.yml`
- Create: `docs/cew-gate-authority/CEW_GATE_AUTHORITY_G0_ASSURANCE_REPORT_v1.md`

**Interfaces:**
- Consumes: Tasks 2–6.
- Produces: exact source/tool identities and a bootstrap evidence report; does **not** make G0 trusted by itself.

- [ ] **Step 1: Resolve and record assurance tool versions and immutable identities**

Record reviewed actionlint/zizmor versions/checksums and every GitHub Action full SHA used by bootstrap CI. No mutable `@vN` reference may remain in the trusted workflow.

- [ ] **Step 2: Create bootstrap workflow**

Run Python compile/tests, candidate property/adversarial suite, no-exec integration, replay, actionlint, zizmor, and available code scanning. Bootstrap workflow is evidence only, not the final qualification authority.

- [ ] **Step 3: Run bootstrap CI on exact head**

Expected: all tests and analyzers PASS or analyzers have documented non-blocking findings classified against the approved threat model.

- [ ] **Step 4: Materialize assurance report**

Record exact head, G0 source digest/manifest digest, A0 digest, tool versions, test counts, analyzer outcomes, replay result, and unresolved items if any.

- [ ] **Step 5: Commit**

```bash
git add governance/cew-gate-authority .github/workflows/validate-cew-gate-authority-bootstrap.yml docs/cew-gate-authority/CEW_GATE_AUTHORITY_G0_ASSURANCE_REPORT_v1.md
git commit -m "ci: qualify CEW Gate Authority G0 bootstrap"
```

---

### Task 8: Independent G0 review and human promotion record

**Files:**
- Create only after approval: `governance/cew-gate-authority/G0_PROMOTION_RECORD_v1.json`
- Update: `docs/cew-gate-authority/CEW_GATE_AUTHORITY_G0_ASSURANCE_REPORT_v1.md`

**Interfaces:**
- Consumes: exact G0/A0 candidate SHA and Task 7 evidence.
- Produces: human-controlled promotion record that makes G0/A0 eligible to become trusted anchors.

- [ ] **Step 1: Request fresh independent review on exact G0/A0 head**

Reviewer focus: no candidate execution, B/G/A separation, A0 provenance, replay integrity, Receipt binding, supply-chain pins, permission model.

- [ ] **Step 2: Resolve only threat-model-valid blockers using TDD**

Any code change creates a new exact head and invalidates the prior bootstrap evidence/review; rerun Task 7 evidence on the new head.

- [ ] **Step 3: Present promotion packet to human**

Packet includes exact head, A0 digest, G0 manifest digest, test/analyzer/replay evidence, independent review result, and any residual explicitly accepted risk.

- [ ] **Step 4: HUMAN GATE — promote G0/A0**

Do not create the promotion record until explicit human approval. No automation may infer approval from green CI.

- [ ] **Step 5: Create promotion record and commit**

Record approver decision, exact G0 commit, A0 SHA-256, assurance evidence references, and `bootstrap_mode=HUMAN_PROMOTION`.

Expected: G0/A0 now have a durable bootstrap trust record, but the production control-plane workflow is not yet activated.

---

### Task 9: Trusted qualification workflow pinned to promoted G0/A0

**Files:**
- Create: `.github/workflows/cew-gate-authority.yml`
- Create: `tests/cew_gate_authority/test_receipt_handoff.py`
- Create: `docs/cew-gate-authority/CEW_GATE_AUTHORITY_DEPLOYMENT_RUNBOOK_v1.md`

**Interfaces:**
- Consumes: human-promoted G0 commit SHA and A0 digest from Task 8; Task 1 trigger decision.
- Produces: trusted `qualify` workflow and same-run digest-bound handoff.

- [ ] **Step 1: Write failing handoff tests**

Test correct R digest accepted; one-byte Receipt mutation rejected; wrong H/G/A digest rejected; stale prior-run receipt rejected by run-scoped metadata.

- [ ] **Step 2: Run RED**

Run: `python -m unittest tests/cew_gate_authority/test_receipt_handoff.py -v`

Expected: FAIL.

- [ ] **Step 3: Implement trusted workflow with minimal permissions**

The workflow must pin the promoted G0 exact SHA and A0 identity outside H, fetch H into bare Git storage, invoke only G0, and propagate non-zero exit fail-closed. `qualify` uses only `contents: read` and no secrets.

- [ ] **Step 4: Implement same-run Receipt handoff**

Use the simplest GitHub-supported same-run mechanism that does not require historical retention as authority; consumer verifies SHA-256 before use. Document the chosen mechanism in runbook.

- [ ] **Step 5: Run GREEN and workflow analyzers**

Expected: unittest PASS; actionlint/zizmor no blocker; permission review matches spec.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/cew-gate-authority.yml tests/cew_gate_authority/test_receipt_handoff.py docs/cew-gate-authority/CEW_GATE_AUTHORITY_DEPLOYMENT_RUNBOOK_v1.md
git commit -m "ci: add trusted CEW qualification control plane"
```

---

### Task 10: Attestation and optional promotion publisher

**Files:**
- Modify: `.github/workflows/cew-gate-authority.yml`
- Modify: `governance/cew-gate-authority/TRUSTED_TOOLCHAIN_v1.json`
- Extend: `tests/cew_gate_authority/test_receipt_handoff.py`
- Modify: `docs/cew-gate-authority/CEW_GATE_AUTHORITY_DEPLOYMENT_RUNBOOK_v1.md`

**Interfaces:**
- Consumes: verified Receipt digest from Task 9.
- Produces: success-only attestation of the canonical Receipt/bundle; optionally a separately governed status publisher for H.

- [ ] **Step 1: Spike the exact GitHub attestation action/API on this public repository**

Resolve current supported action, required permissions, subject/predicate format, and full immutable action SHA. If unavailable under current account policy, record `ATTESTATION_AVAILABLE=false` and leave qualification functional but promotion policy blocked if attestation is mandatory.

- [ ] **Step 2: Add attestation job with least privilege**

`attest` receives only digest-bound R, never reads H, and has `id-token: write` + `attestations: write` only as required.

- [ ] **Step 3: Verify attestation**

Fresh evidence must prove subject digest and CEW predicate contain B/G/A/H/O and `qualified=true` for a synthetic valid candidate.

- [ ] **Step 4: Decide promotion publisher only from Task 1 evidence**

If repository required-check semantics need an H-associated publisher, add a separate minimal `promote` job/action and test it on a disposable PR. Otherwise omit it; R remains canonical qualification proof.

- [ ] **Step 5: Re-run actionlint/zizmor and permission audit**

Expected: no blocker and no privilege creep into `qualify`.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/cew-gate-authority.yml governance/cew-gate-authority/TRUSTED_TOOLCHAIN_v1.json tests/cew_gate_authority/test_receipt_handoff.py docs/cew-gate-authority/CEW_GATE_AUTHORITY_DEPLOYMENT_RUNBOOK_v1.md
git commit -m "ci: attest CEW qualification receipts"
```

---

### Task 11: Repository governance activation

**Files:**
- Modify: `docs/cew-gate-authority/CEW_GATE_AUTHORITY_DEPLOYMENT_RUNBOOK_v1.md`
- Evidence: repository Settings/ruleset/policy state captured in the runbook or dedicated receipt.

**Interfaces:**
- Consumes: Task 1 target governance, trusted workflow identities.
- Produces: documented live configuration for Actions policy and `main` protection/ruleset.

- [ ] **Step 1: Prepare exact desired repository configuration**

Minimum target: PR required for `main`, force-push blocked, deletion blocked, required checks where their commit semantics are verified, bypass list minimized/documented, no auto-merge.

- [ ] **Step 2: HUMAN/ADMIN GATE — apply Settings changes**

Use repository Settings only after presenting the exact changes. Do not broaden `pull_request_target` globally; authorize only what CEW Gate Authority requires.

- [ ] **Step 3: Re-read live settings**

Expected: configured state matches desired state. Any unavailable capability is recorded with approved fallback.

- [ ] **Step 4: Commit evidence/runbook update**

```bash
git add docs/cew-gate-authority/CEW_GATE_AUTHORITY_DEPLOYMENT_RUNBOOK_v1.md
git commit -m "docs: record CEW Gate Authority repository governance"
```

---

### Task 12: End-to-end G0 control-plane acceptance

**Files:**
- Modify: `docs/cew-gate-authority/CEW_GATE_AUTHORITY_G0_ASSURANCE_REPORT_v1.md`
- No new runtime code unless a tested blocker requires G1-style change and requalification.

**Interfaces:**
- Consumes: live trusted control plane, promoted G0/A0, repository governance.
- Produces: acceptance evidence that satisfies spec §29 and authorizes the separate migration plan.

- [ ] **Step 1: Run disposable candidate PASS scenario**

Expected R binds exact B/G/A/H/O; replay output matches historical N12 output; attestation verifies when enabled.

- [ ] **Step 2: Run disposable adversarial scenarios**

Candidate modifies its workflow, modifies a copy of A, adds executable scripts/hooks/local actions, uses symlink/gitlink, mutates authority boundary, and moves branch after H capture. Expected: no candidate code executes; irrelevant candidate workflow/A copies do not affect trusted control plane; prohibited data mutations FAIL.

- [ ] **Step 3: Verify Receipt handoff and attestation tamper failures**

Expected: altered R/digest rejected before attest/promote.

- [ ] **Step 4: Run full G0 suite fresh on exact trusted identities**

Run all `tests/cew_gate_authority`, operational replay, actionlint, zizmor, and available code scanning. Capture exact SHAs/digests and results.

- [ ] **Step 5: Request final independent Gate Authority review**

Finding is blocker only if it violates the approved trust/threat model, demonstrates candidate execution/control-plane substitution/receipt confusion, breaks replay/authority boundary, or invalidates G0 evidence.

- [ ] **Step 6: HUMAN GATE — declare Gate Authority G0 operational**

No merge/promotion automation. Human decision references the final exact identities and evidence.

- [ ] **Step 7: Commit final assurance report**

```bash
git add docs/cew-gate-authority/CEW_GATE_AUTHORITY_G0_ASSURANCE_REPORT_v1.md
git commit -m "docs: certify CEW Gate Authority G0 acceptance"
```

Expected terminal state: `CEW-GATE-AUTHORITY-01 G0/A0 = OPERATIONAL`; CEW-CONTRACT-01 migration may start; PR #147 still frozen and unclosed.
