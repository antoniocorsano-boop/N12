# CEW-CONTRACT-01 Trusted Qualification Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace PR #147 with a minimal qualification-only Candidate H that is evaluated by already-operational CEW Gate Authority G0/A0, receives a B/G/A/H/O-bound Receipt/attestation, and allows #147 to be retired as superseded without losing its audit trail.

**Architecture:** Extract only the CEW-CONTRACT-01 qualification evidence that A0 requires into one bounded candidate root, with no workflow, validator, parser, test harness, or executable candidate code. G0 reads that root as Git blobs, replays O independently, and produces the canonical qualification decision. Promotion/merge remains a separate human decision.

**Tech Stack:** Git; Markdown/CSV/JSON qualification data; operational CEW Gate Authority G0/A0; GitHub pull requests; GitHub Artifact Attestations when enabled by the bootstrap plan.

**Spec:** `docs/superpowers/specs/2026-10-13-cew-gate-authority-01-design.md`

**Prerequisite Plan:** `docs/superpowers/plans/2026-10-13-cew-gate-authority-01-bootstrap.md` must have reached terminal state `CEW-GATE-AUTHORITY-01 G0/A0 = OPERATIONAL` before Task 2 starts.

## Global Constraints

- PR #147 remains the immutable audit source; do not add more parser-hardening commits.
- Audit source head for extraction is `e631b83e22b793c1f5f3740f4f57206ee69f3a93` unless a later metadata-only review event changes no branch content; any different source head must be explicitly reconciled before extraction.
- New qualification branch starts from current `main`, not from #147.
- Candidate root is exactly `qualification/cew-contract-01/n12/`.
- Candidate contains data only: no `.github/workflows`, Python, shell, Makefile, package manifest, local action, Git hook, executable template, or test harness.
- Candidate paths are limited to the exact payload profile listed below; A0 must use the same list.
- No new engineering property, coordinate, material, load, boundary condition, soil parameter, solver selection, `SolverRun`, or `Result` may be introduced.
- Existing `DOC`/`INF`/`ND`/`WATCH` distinctions must be preserved.
- Operational Authority remains exactly `d806dcca72779b5a186defe557a7a9b739575a90`.
- Qualification and promotion are separate; no auto-merge.
- #147 may be closed as `superseded` only after the replacement qualification has a valid Receipt and the replacement PR is human-promoted/merged.

## Exact Candidate Payload Profile

A0 and H must agree on exactly these 21 candidate blobs:

1. `qualification/cew-contract-01/n12/qualification.json`
2. `qualification/cew-contract-01/n12/conformance-matrix.csv`
3. `qualification/cew-contract-01/n12/evidence-index.json`
4. `qualification/cew-contract-01/n12/structural-type-minimality.csv`
5. `qualification/cew-contract-01/n12/source-sufficiency.md`
6. `qualification/cew-contract-01/n12/registration-uncertainty.json`
7. `qualification/cew-contract-01/n12/model-generation.json`
8. `qualification/cew-contract-01/n12/model-generation-receipt.json`
9. `qualification/cew-contract-01/n12/evidence/CASE_01_DOCUMENTED_PROPERTY.md`
10. `qualification/cew-contract-01/n12/evidence/CASE_02_NO_PROMOTION_OF_ND.md`
11. `qualification/cew-contract-01/n12/evidence/CASE_03_MIXED_EPISTEMIC_STATE.md`
12. `qualification/cew-contract-01/n12/evidence/CASE_04_STRUCTURAL_IDENTITY.md`
13. `qualification/cew-contract-01/n12/evidence/CASE_05_RELATIONSHIP_UNCERTAINTY.md`
14. `qualification/cew-contract-01/n12/evidence/CASE_06_REAL_CONFLICT.md`
15. `qualification/cew-contract-01/n12/evidence/CASE_07_NON_DESTRUCTIVE_UPDATE.md`
16. `qualification/cew-contract-01/n12/evidence/CASE_08_SNAPSHOT_SCENARIO.md`
17. `qualification/cew-contract-01/n12/evidence/CASE_09_END_TO_END_ASSURANCE.md`
18. `qualification/cew-contract-01/n12/evidence/CASE_10_VERIFICATION_RECEIPT.md`
19. `qualification/cew-contract-01/n12/evidence/CASE_11_REGISTRATION_UNCERTAINTY.md`
20. `qualification/cew-contract-01/n12/evidence/CASE_12_MODEL_GENERATION.md`
21. `qualification/cew-contract-01/n12/evidence/CASE_13_CORE_END_TO_END_ASSURANCE.md`

No candidate-supplied Frozen Authority file is accepted. No candidate workflow or validator is accepted. The qualification report is produced from trusted Receipt R rather than supplied as candidate authority.

## Review Focus

1. **Silent evidence rewriting during extraction:** copied cases must preserve meaning/status/provenance from #147; normalization may change paths/format but not technical claims. Task 1 owns byte/semantic reconciliation.
2. **Candidate trying to smuggle control-plane files:** any path outside the 21-file profile, especially workflow/script/test content, must not become part of the qualification bundle. Tasks 2 and 3 own this check.
3. **Authority duplication:** H may repeat identifiers for transparency, but candidate copies never override A0/O. Task 3 owns mismatch tests.
4. **Exact-head drift during review:** every final qualification/review must name the same H as Receipt R; any candidate commit requires a new R. Task 4 owns this gate.
5. **Premature retirement of #147:** supersession occurs only after replacement qualification and human promotion are complete. Task 6 owns this gate.

---

### Task 1: Freeze and reconcile the #147 extraction source

**Files:**
- Create on migration branch: `qualification/cew-contract-01/n12/evidence-index.json`
- Create: `docs/cew-gate-authority/CEW_CONTRACT_01_147_EXTRACTION_RECEIPT_v1.md`

**Interfaces:**
- Consumes: PR #147 exact audit source, A0 payload profile.
- Produces: one-to-one source→destination mapping with source path, source blob SHA, destination path, transformation class (`BYTE_COPY`, `PATH_ONLY_REHOME`, or `STRUCTURED_NORMALIZATION`), and evidence of semantic preservation.

- [ ] **Step 1: Re-read PR #147 exact head and changed-file set**

Expected: no new parser-hardening code beyond the frozen audit source. If branch content differs from `e631b83e...`, stop and classify the delta before extraction.

- [ ] **Step 2: Map source files to the 21-file candidate profile**

Use the 13 `CASE_*` files, `CEW_STRUCTURAL_TYPE_MINIMALITY_v1.csv`, `N12_SOURCE_SUFFICIENCY.md`, `N12_REGISTRATION_UNCERTAINTY_v1.json`, and the two ModelGeneration JSONs as source evidence. Build `qualification.json`, `conformance-matrix.csv`, and `evidence-index.json` from already-qualified #147 records without inventing values.

- [ ] **Step 3: Verify epistemic/authority-sensitive content before rehome**

Explicitly check DOC/INF/ND/WATCH labels, `solver_authorized=false`, `calculation_model_ready=false`, `synthetic_solver_result=false`, `solver_run=false`, `result_entity_created=false`, registration supports, snapshot/generation identities, and CEW-FEM separation.

- [ ] **Step 4: Write extraction receipt**

Every destination file must cite its #147 source path/blob and transformation class. Any transformation beyond structural normalization must be human-readable and reproducible.

- [ ] **Step 5: Commit extraction receipt only if reconciliation is complete**

```bash
git add docs/cew-gate-authority/CEW_CONTRACT_01_147_EXTRACTION_RECEIPT_v1.md
git commit -m "docs: freeze CEW-CONTRACT-01 extraction source"
```

---

### Task 2: Build the minimal qualification-only Candidate H

**Files:**
- Create: all 21 files in `qualification/cew-contract-01/n12/` listed above.
- No executable files.

**Interfaces:**
- Consumes: Task 1 extraction mapping and A0 schema/allowlist.
- Produces: a complete Candidate H bundle that G0 can read without any repository-native candidate code.

- [ ] **Step 1: Create 13 evidence files and four direct structured copies**

Rehome evidence while preserving technical content. The destination path changes; source authority/provenance references remain explicit.

- [ ] **Step 2: Create `conformance-matrix.csv`**

Must contain exactly `C01-T01`…`C01-T11`, each once, with PASS status and evidence references resolving only inside the 21-file profile.

- [ ] **Step 3: Create `qualification.json`**

Machine-readable candidate declaration includes candidate schema/version, canonical snapshot/generation identifiers, authority-boundary declarations, and evidence-index digest/reference. It may declare O/G/A expectations for transparency but cannot select or override trusted G/A/O.

- [ ] **Step 4: Create `evidence-index.json`**

Index all evidence references and source provenance; no glob, URI, absolute path, parent traversal, or path outside candidate root.

- [ ] **Step 5: Run static candidate-surface audit**

Expected: exactly 21 allowlisted blobs; no symlink/gitlink; no executable/code/workflow/test file; all structured data parse; no candidate file attempts to define Frozen Authority.

- [ ] **Step 6: Commit**

```bash
git add qualification/cew-contract-01/n12
git commit -m "data: add clean N12 CEW-CONTRACT-01 qualification payload"
```

---

### Task 3: Adversarial prequalification against operational G0/A0

**Files:**
- No production Gate Core changes.
- Evidence may be appended to extraction/migration report.

**Interfaces:**
- Consumes: exact H from Task 2 and operational G0/A0.
- Produces: first trusted Receipt R or precise failure codes; migration branch remains candidate-only.

- [ ] **Step 1: Run G0/A0 against exact H**

Expected: G0 reads only the 21 allowed blobs, materializes O independently, and produces R bound to B/G/A/H/O.

- [ ] **Step 2: If FAIL, classify before editing**

A failure caused by candidate data is fixed in H only if supported by #147/O evidence. A failure that proves a Gate Core defect opens the G→G+1 process; do not patch G inside the candidate branch.

- [ ] **Step 3: Run negative candidate mutations on disposable refs/copies**

At minimum: add candidate workflow/script; alter candidate copy of authority identity; set authority-boundary flag true; duplicate/miss gate ID; point evidence outside root; alter registration support; alter model-generation digest. Expected: irrelevant control-plane copies have no authority; prohibited semantic mutations FAIL.

- [ ] **Step 4: Preserve candidate branch purity**

After tests, verify production candidate branch still contains only the intended data/docs and no test harness generated by adversarial work.

---

### Task 4: Exact-head qualification Receipt, attestation, and independent payload review

**Files:**
- Candidate files unchanged unless review finds a valid payload defect.
- Receipt/attestation are control-plane evidence, not candidate-authored authority.

**Interfaces:**
- Consumes: stable exact H.
- Produces: final R for H, attestation if enabled, independent review conclusion scoped to payload correctness.

- [ ] **Step 1: Freeze exact H and run fresh trusted qualification**

Record B/G/A/H/O, bundle digest, replay output digest, I01–I17 results, failure codes, CEW-FEM boundary, and `qualified`.

- [ ] **Step 2: Verify attestation when policy requires it**

Expected subject/predicate match final Receipt and exact H. If qualification is PASS but attestation unavailable, use the bootstrap plan's defined `QUALIFIED_NOT_ATTESTED` handling; do not silently promote.

- [ ] **Step 3: Request fresh independent review of the payload PR**

Review scope is candidate evidence/claims/provenance and consistency with R/A0/O. Candidate cannot be asked to harden trusted workflow syntax because it does not control the workflow.

- [ ] **Step 4: Apply exact-head rule**

Any payload commit after R/review invalidates both for promotion and requires a new trusted run/review on the new H.

Expected terminal evidence: no open finding demonstrates that G0 made an incorrect decision on final H.

---

### Task 5: Human promotion/merge decision for the replacement qualification

**Files:**
- No automatic code/data changes.

**Interfaces:**
- Consumes: final H, R, attestation status, independent review.
- Produces: explicit human decision to merge or hold.

- [ ] **Step 1: Present promotion packet**

Include final H, B/G/A/O identities, qualification bundle digest, replay result, I01–I17 matrix, attestation verification, review conclusion, and any residual accepted risk.

- [ ] **Step 2: HUMAN GATE — approve promotion**

No tool may infer approval from green CI. If not approved, leave PR open/Draft with reason.

- [ ] **Step 3: Merge only after explicit authorization**

No auto-merge. Verify the exact candidate head being merged still matches R/review.

---

### Task 6: Retire PR #147 as superseded and establish the new canonical checkpoint

**Files:**
- Update project/audit documentation only if needed to point to the new Receipt/checkpoint.
- Do not rewrite #147 history.

**Interfaces:**
- Consumes: merged replacement qualification and final R.
- Produces: preserved audit lineage and one canonical CEW-CONTRACT-01 checkpoint for subsequent CEW work.

- [ ] **Step 1: Verify replacement is actually integrated and Receipt remains verifiable**

Expected: merged commit derives from final H; R/attestation still resolve; G/A/O identities remain available.

- [ ] **Step 2: Add final top-level comment to #147**

State that #147 is superseded by the replacement qualification PR/Receipt, explain that its review history remains the audit trail that motivated CEW-GATE-AUTHORITY-01, and link exact identifiers.

- [ ] **Step 3: HUMAN GATE — close #147 as `superseded`**

Do not close until explicit authorization. Do not delete the branch or discussion as part of this plan.

- [ ] **Step 4: Record canonical project checkpoint**

Canonical state must distinguish:
- Gate Authority G0/A0 operational;
- CEW-CONTRACT-01 qualification Receipt for final H;
- #147 superseded/audit-only;
- CEW-FEM-01 still not authorized;
- next CEW step follows the existing canonical chain rather than reopening gate hardening.

Expected terminal state: one trusted qualification path, one clean candidate payload, #147 retained only as historical audit trail, and no further parser-hardening loop.
