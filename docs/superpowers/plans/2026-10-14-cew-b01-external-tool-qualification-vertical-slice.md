# CEW-B01 External Tool Qualification / N12 Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify the approved external open-source toolchain on one immutable real N12 source and carry a real, non-trivial G4 column set through Source → Evidence → StructuralObject → deterministic parametric geometry without hidden manual reconstruction or epistemic promotion.

**Architecture:** CEW-B01 is a bounded vertical slice inside the approved Master, not a new platform. It materializes one exact archived source (`tavola 5.pdf`), runs replaceable external tools behind thin task-specific adapters, emits provenance-bound Evidence candidates, requires explicit review for ambiguous identity, and generates build123d/OpenCascade geometry in a source/page frame. Historical OAR data may be used only as a post-run audit comparator; it must never seed source coordinates, structural identity, or canonical truth.

**Tech Stack:** Python 3.12.15; Git; Docling/docling-parse; pypdfium2; pdfplumber; OCRmyPDF/Tesseract only when triggered; OpenCV; build123d/OCP; JSON/CSV; GitHub Actions on ubuntu-24.04. `ezdxf` remains an approved CEW tool but is DEFERRED for this slice unless an immutable real DXF source is found. CADCraft remains a separate non-blocking benchmark.

**Spec:** `CEW_MASTER_PLAN.md` and `CEW_CURRENT_STATE.json`

## Global Constraints

- Canonical task is exactly `CEW-B01 — External Tool Qualification / N12 Vertical Slice`; WIP limit remains `1`.
- BUILD LAST — REUSE FIRST: do not implement PDF, OCR, CAD kernel, IFC, FEM, generic viewer, point-cloud, database, or solver engines internally.
- Frozen source repository: `antoniocorsano-boop/N12`.
- Frozen source commit: `78c20a52db4f391ce0d13b9705b9f04737e218c9` on archival history.
- Frozen source path: `archive/documentazione_originaria/tavola 5.pdf`.
- Frozen Git blob SHA: `ec32cd621877e9037cb26ebc083164140a8e3e68`.
- Frozen source SHA-256: `2143b256511788691291cef533559306fc2988c7cb59a16d49cf86d1d7e94c7f`.
- Frozen page index for the slice: `0`.
- Historical OAR reference (`PR #132`, head `b7a25783564c353f0e7aa23775318a3a2d78ea9c`) is comparator-only. Its 34 support identities / 5 family summary is not an input authority.
- No manual coordinate may enter B01 unless it is represented as an explicit reviewed Evidence/Decision object with provenance. The default path must consume source-derived region identifiers, not typed coordinates.
- `DOC/MIS/RIF/INF/INC/ND` semantics remain explicit. No `RIF`, `INF`, `INC`, or `ND` value may be promoted to `DOC` by geometry generation.
- B01 must not authorize or invoke CEW-FEM-01, SolverRun, Result, new solvers, IFC Phase D, or a new Gate Authority.
- PR #147 is read-only: `READ_ONLY_DO_NOT_MODIFY_DO_NOT_CLOSE_DO_NOT_SUPERSEDE`.
- No production qualification dispatch is part of B01.
- B01 completion must stop at `COMPLETED_AWAITING_HUMAN_PHASE_DECISION`; it must not auto-advance to Phase C.
- External dependencies must be exact-pinned before qualification evidence is accepted. PyMuPDF must not be introduced as a required dependency.

## Review Focus

1. **Source substitution / archive drift:** a file at the same path but wrong commit, Git blob, or SHA-256 must fail before parsing.
2. **Historical-oracle leakage:** OAR counts, labels, coordinates, or family assignments must not be read by extraction/identity code before outputs are frozen; comparator access is post-run only.
3. **Coordinate-frame confusion:** PDF points, rendered pixels, page millimetres, and building/model coordinates must remain typed/separate; no implicit px→m or page→building conversion.
4. **Epistemic promotion through geometry:** section, placement, or height marked RIF/INF/INC/ND must retain that state in generated geometry metadata and cannot become canonical DOC.
5. **Missing external source class:** absence of a real immutable DXF must result in an explicit `DEFER_FOR_THIS_SLICE_NO_IMMUTABLE_DXF_SOURCE`, not a fabricated DXF benchmark or synthetic pass.

---

### Task 1: Freeze and Materialize the Real N12 Source

**Files:**
- Create: `governance/cew-b01/N12_TAV5_SOURCE_v1.json`
- Create: `cew_b01/__init__.py`
- Create: `cew_b01/source_contract.py`
- Create: `cew_b01/cli.py`
- Test: `tests/cew_b01/test_source_contract.py`
- Test: `tests/cew_b01/test_source_materialization.py`

**Interfaces:**
- Consumes: exact Git repository access to `antoniocorsano-boop/N12`.
- Produces: `SourceContract`, `materialize_source(contract, destination) -> MaterializedSource`, and CLI command `python -m cew_b01.cli materialize-source`.

- [ ] **Step 1: Write source-contract tests**

Assert that the committed source contract contains exactly repository, commit, path, blob SHA, SHA-256, page index and source role. Add negative cases for wrong commit, wrong blob, wrong SHA-256 and mutable branch-only identity.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_source_contract -v`

Expected: FAIL because `cew_b01.source_contract` and the governed source contract do not yet exist.

- [ ] **Step 3: Implement the minimal source contract**

Implement typed validation in `cew_b01/source_contract.py`. The JSON must bind exactly:

```text
repository = antoniocorsano-boop/N12
commit = 78c20a52db4f391ce0d13b9705b9f04737e218c9
path = archive/documentazione_originaria/tavola 5.pdf
git_blob_sha = ec32cd621877e9037cb26ebc083164140a8e3e68
sha256 = 2143b256511788691291cef533559306fc2988c7cb59a16d49cf86d1d7e94c7f
page_index = 0
```

- [ ] **Step 4: Write materialization tests**

Use a temporary local Git repository fixture to prove that materialization verifies commit→path→blob identity and file SHA-256 before returning bytes/path. Add the Review Focus source-substitution cases.

- [ ] **Step 5: Run materialization tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_source_materialization -v`

Expected: FAIL because materialization is not implemented.

- [ ] **Step 6: Implement `materialize_source()` and CLI**

Materialize by exact Git object identity; never follow the current archive branch tip as authority. Fail closed on any identity mismatch.

- [ ] **Step 7: Verify GREEN**

Run: `python -m unittest tests.cew_b01.test_source_contract tests.cew_b01.test_source_materialization -v`

Expected: PASS.

- [ ] **Step 8: Commit**

Commit message: `feat(cew-b01): freeze immutable N12 TAV5 source`

---

### Task 2: Freeze the B01 External Toolchain and License Boundary

**Files:**
- Create: `governance/cew-b01/EXTERNAL_TOOLCHAIN_v1.json`
- Create: `requirements/cew-b01.lock.txt`
- Create: `cew_b01/toolchain.py`
- Test: `tests/cew_b01/test_toolchain_contract.py`

**Interfaces:**
- Consumes: approved tool statuses from `CEW_MASTER_PLAN.md`.
- Produces: `ToolchainContract` and a machine-readable decision/status record per external tool.

- [ ] **Step 1: Write toolchain contract tests**

Require entries for Docling/docling-parse, pypdfium2, pdfplumber, OCRmyPDF/Tesseract, OpenCV, ezdxf, build123d/OCP and CADCraft. Assert that required Python packages are exact-pinned (`==`), PyMuPDF is absent from required dependencies, OCR is conditional, CADCraft is separate/non-blocking, and ezdxf may be `DEFER_FOR_THIS_SLICE_NO_IMMUTABLE_DXF_SOURCE`.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.cew_b01.test_toolchain_contract -v`

Expected: FAIL because the governed toolchain files do not exist.

- [ ] **Step 3: Resolve and freeze exact dependency versions**

Selection rule: choose the newest stable, non-prerelease release compatible with Python 3.12.15 at implementation start, prove imports in a clean environment, then write exact versions to `requirements/cew-b01.lock.txt` and record package name/version/license/source in `EXTERNAL_TOOLCHAIN_v1.json`. Once committed, those versions are immutable for the B01 qualification receipt unless the plan is amended with a new evidence-backed toolchain revision.

- [ ] **Step 4: Implement `ToolchainContract` validation**

Reject missing tools, unpinned required Python packages, prohibited PyMuPDF dependency, unknown status values, and a blocking CADCraft dependency.

- [ ] **Step 5: Verify GREEN**

Run: `python -m unittest tests.cew_b01.test_toolchain_contract -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Commit message: `chore(cew-b01): freeze external toolchain`

---

### Task 3: Qualify PDF Parsing and Deterministic Page Rendering

**Files:**
- Create: `cew_b01/pdf_probe.py`
- Create: `cew_b01/records.py`
- Test: `tests/cew_b01/test_pdf_probe.py`
- Evidence output at runtime: `evidence/cew-b01/pdf/`

**Interfaces:**
- Consumes: `MaterializedSource` from Task 1 and exact toolchain from Task 2.
- Produces: `PdfProbeResult` containing source identity, PDF page metrics, extracted text/vector statistics, renderer identity, raster dimensions/digest, and a per-tool result (`PASS`, `LIMITED`, `FAIL`, `NOT_TRIGGERED`).

- [ ] **Step 1: Write RED tests for typed coordinate frames and tool isolation**

Tests must distinguish `PDF_POINT`, `RASTER_PIXEL`, and `PAGE_MM`; reject direct arithmetic/conversion without an explicit transform object; assert that parser results include exact source identity and tool version.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_pdf_probe -v`

Expected: FAIL because PDF probe records and adapters are absent.

- [ ] **Step 3: Implement pypdfium2 render adapter**

Render page 0 at the governed benchmark setting (300 dpi equivalent from PDF points), record dimensions and SHA-256, and persist the explicit PDF-point→pixel transform used. Repeated runs with the same pinned version/source must yield the same recorded raster digest in the qualification environment.

- [ ] **Step 4: Implement pdfplumber probe adapter**

Record page size, text count, line/rect/curve counts and coordinate extents without turning extracted values into structural truth.

- [ ] **Step 5: Implement Docling/docling-parse probe adapter**

Capture structured text/layout availability and any tool limitation. A Docling limitation is a qualification result, not permission to replace provenance with manual reconstruction.

- [ ] **Step 6: Implement the OCR trigger only**

OCRmyPDF/Tesseract runs only when the source lacks a usable text layer for the Evidence task. Define the trigger deterministically from parser output and record `NOT_TRIGGERED` otherwise. Do not add PaddleOCR to the first slice unless a separate benchmark amendment is approved.

- [ ] **Step 7: Verify GREEN and determinism**

Run: `python -m unittest tests.cew_b01.test_pdf_probe -v`

Then execute the probe twice against the exact materialized source and compare receipt-relevant digests.

Expected: tests PASS; repeated governed run identities/digests match.

- [ ] **Step 8: Commit**

Commit message: `feat(cew-b01): qualify TAV5 PDF toolchain`

---

### Task 4: Derive Provenance-Bound G4 Geometric Evidence

**Files:**
- Create: `cew_b01/evidence_extraction.py`
- Create: `cew_b01/evidence_schema.py`
- Test: `tests/cew_b01/test_evidence_extraction.py`
- Test: `tests/cew_b01/test_coordinate_frames.py`
- Evidence output at runtime: `evidence/cew-b01/g4/CEW_B01_G4_EVIDENCE_CANDIDATES_v1.json`

**Interfaces:**
- Consumes: Task 3 source-derived vector/raster outputs only.
- Produces: immutable `EvidenceRegionCandidate` records with IDs, source binding, page/raster frame, source-derived geometry, method/tool version and confidence/status. No StructuralObject IDs are assigned in this task.

- [ ] **Step 1: Write tests for EvidenceRegionCandidate invariants**

Require source SHA-256, page index, coordinate-frame tag, method, exact tool version, geometry digest and deterministic candidate ID. Reject a candidate containing untagged coordinates or building/model-space coordinates without an explicit proven transform.

- [ ] **Step 2: Add historical-oracle leakage tests**

Tests must prove `evidence_extraction.py` does not import/read PR #132/OAR manifests, support IDs, expected count 34 or family count 5. Comparator data is unavailable to extraction code by construction.

- [ ] **Step 3: Run focused tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_evidence_extraction tests.cew_b01.test_coordinate_frames -v`

Expected: FAIL because the extraction layer does not exist.

- [ ] **Step 4: Implement the minimal extraction pipeline using existing tools**

Prefer source vectors when they are sufficient; use OpenCV only on the exact Task 3 source-derived raster for geometric features that require raster processing. Preserve all page↔raster transforms explicitly. Do not hard-code historic support coordinates/counts.

- [ ] **Step 5: Add deterministic replay test**

Two extractions from the same frozen source/toolchain must produce the same sorted candidate identifiers and geometry digests.

- [ ] **Step 6: Verify GREEN**

Run: `python -m unittest tests.cew_b01.test_evidence_extraction tests.cew_b01.test_coordinate_frames -v`

Expected: PASS.

- [ ] **Step 7: Commit**

Commit message: `feat(cew-b01): derive provenance-bound G4 evidence`

---

### Task 5: Review Evidence into StructuralObject Candidates Without Hidden Coordinates

**Files:**
- Create: `cew_b01/object_mapping.py`
- Create: `governance/cew-b01/schemas/B01_REVIEW_DECISION_v1.schema.json`
- Create: `evidence/cew-b01/g4/CEW_B01_G4_REVIEW_DECISIONS_v1.json` only after the actual review is performed
- Test: `tests/cew_b01/test_object_mapping.py`
- Test: `tests/cew_b01/test_historical_comparator_boundary.py`

**Interfaces:**
- Consumes: Task 4 `EvidenceRegionCandidate` IDs plus explicit review decisions that may select/label candidates but may not type replacement coordinates.
- Produces: `StructuralObjectCandidate` records and a frozen pre-comparator result bundle.

- [ ] **Step 1: Write review-decision tests**

A decision may reference candidate IDs, assign/confirm semantic label/support identifier and section-family interpretation, or reject/mark ambiguous. It must not contain ad-hoc coordinate fields. Ambiguity must remain explicit and must not be promoted automatically.

- [ ] **Step 2: Write mapping tests and verify RED**

Run: `python -m unittest tests.cew_b01.test_object_mapping -v`

Expected: FAIL because mapping is absent.

- [ ] **Step 3: Implement StructuralObject candidate mapping**

Generate stable B01 candidate identity from reviewed source evidence. Keep `canonical=false` and `structural_identity_authorized=false` throughout B01 unless a later human canonicalization step outside this plan authorizes otherwise.

- [ ] **Step 4: Freeze the B01 pre-comparator bundle**

Serialize and hash the complete source-derived/reviewed candidate result before any historical OAR comparator is loaded.

- [ ] **Step 5: Implement comparator boundary and tests**

Only after the pre-comparator digest exists may a separate comparator read historical OAR reference metadata from PR #132/head `b7a25783564c353f0e7aa23775318a3a2d78ea9c`. It may report agreement/disagreement with the historical 34-support / 5-family summary, but must not mutate B01 candidates, coordinates, labels or status.

- [ ] **Step 6: Perform the actual human review on source-derived candidate IDs**

Review the generated candidate set visually against TAV5 and record only candidate selections/semantic decisions. If evidence is insufficient, leave candidates `AMBIGUOUS` and continue with the qualified subset; do not force 34/5 merely to match history.

- [ ] **Step 7: Verify GREEN**

Run: `python -m unittest tests.cew_b01.test_object_mapping tests.cew_b01.test_historical_comparator_boundary -v`

Expected: PASS and comparator cannot modify the frozen pre-comparator digest.

- [ ] **Step 8: Commit**

Commit message: `feat(cew-b01): map reviewed evidence to structural candidates`

---

### Task 6: Generate Deterministic Parametric Geometry with build123d/OCP

**Files:**
- Create: `cew_b01/geometry_adapter.py`
- Create: `cew_b01/geometry_schema.py`
- Test: `tests/cew_b01/test_geometry_adapter.py`
- Evidence output at runtime: `evidence/cew-b01/geometry/CEW_B01_G4_PARAMETRIC_GEOMETRY_v1.json`

**Interfaces:**
- Consumes: reviewed `StructuralObjectCandidate` records from Task 5.
- Produces: source/page-frame parametric B-Rep profile geometry and a mapping receipt from StructuralObjectCandidate→shape digest. Full building-space 3D placement is explicitly not required for B01.

- [ ] **Step 1: Write geometry tests**

For a documented/reviewed rectangular section, assert build123d/OCP profile dimensions, area and bounding box match source-derived dimensions within a declared deterministic tolerance. Assert shape metadata carries the originating Evidence IDs and epistemic state.

- [ ] **Step 2: Add epistemic-promotion regression tests**

A section/placement value marked `RIF`, `INF`, `INC` or `ND` must retain that state. The adapter must refuse to call it `DOC`. Missing height must not be filled with a default extrusion height.

- [ ] **Step 3: Add coordinate-frame regression tests**

Geometry placement must remain in an explicit `SOURCE_PAGE_MM` / local profile frame unless a separately provenance-bound building transform exists. Reject implicit page-mm→building-metre conversion.

- [ ] **Step 4: Run and verify RED**

Run: `python -m unittest tests.cew_b01.test_geometry_adapter -v`

Expected: FAIL because geometry adapter is absent.

- [ ] **Step 5: Implement the minimal build123d adapter**

Generate B-Rep planar profiles / source-frame placement sufficient to prove deterministic parametric generation. Do not manufacture storey height or claim final canonical building geometry. If a sourced RIF vertical value is used for optional visual extrusion, mark the output `BENCHMARK_DERIVED_NOT_CANONICAL` and exclude it from B01 pass criteria.

- [ ] **Step 6: Add repeatability check**

Two runs from the same candidate bundle/toolchain must yield the same normalized geometry metadata and shape-mapping digest.

- [ ] **Step 7: Verify GREEN**

Run: `python -m unittest tests.cew_b01.test_geometry_adapter -v`

Expected: PASS.

- [ ] **Step 8: Commit**

Commit message: `feat(cew-b01): generate parametric G4 geometry`

---

### Task 7: Emit Tool Decisions and the B01 Qualification Receipt

**Files:**
- Create: `cew_b01/qualification.py`
- Create: `governance/cew-b01/schemas/B01_QUALIFICATION_RECEIPT_v1.schema.json`
- Create: `evidence/cew-b01/CEW_B01_TOOL_QUALIFICATION_REPORT_v1.json`
- Create: `evidence/cew-b01/CEW_B01_QUALIFICATION_RECEIPT_v1.json`
- Test: `tests/cew_b01/test_qualification.py`

**Interfaces:**
- Consumes: source, toolchain, PDF, evidence, review/mapping and geometry receipts.
- Produces: final B01 report plus one fail-closed receipt with per-tool `ADOPT`, `BENCHMARK`, `DEFER`, or `REJECT` decision and evidence references.

- [ ] **Step 1: Write qualification reducer tests**

Require all B01 exit criteria to be evidenced before `B01_PASS`. Any missing source identity, nondeterministic replay, hidden coordinate, unresolved required tool failure, or geometry provenance break must reduce to `B01_NOT_QUALIFIED` with stable failure code.

- [ ] **Step 2: Add DXF absence test**

If the frozen source set contains no immutable DXF, ezdxf decision must be exactly `DEFER_FOR_THIS_SLICE_NO_IMMUTABLE_DXF_SOURCE`; this is not a B01 failure. A synthetic/fabricated DXF must be rejected as qualification evidence.

- [ ] **Step 3: Add CADCraft non-blocking test**

CADCraft result may be `BENCHMARK`, `DEFER`, or `REJECT` without changing Source→Evidence→StructuralObject→geometry qualification, because it is explicitly separate in the Master.

- [ ] **Step 4: Run and verify RED**

Run: `python -m unittest tests.cew_b01.test_qualification -v`

Expected: FAIL because qualification reducer/report does not exist.

- [ ] **Step 5: Implement reducer and receipt**

Bind receipt to current implementation commit, frozen source identity, exact toolchain manifest digest and all intermediate evidence digests. Keep solver/FEM/result authority false/absent.

- [ ] **Step 6: Verify GREEN**

Run: `python -m unittest tests.cew_b01.test_qualification -v`

Expected: PASS.

- [ ] **Step 7: Commit**

Commit message: `feat(cew-b01): emit tool qualification receipt`

---

### Task 8: Add Repository-Native B01 Validation Without Expanding Governance Scope

**Files:**
- Create: `.github/workflows/validate-cew-b01.yml`
- Create: `tests/cew_b01/test_workflow_contract.py`

**Interfaces:**
- Consumes: all B01 implementation/tests and exact dependency lock.
- Produces: exact-head CI evidence for B01 only.

- [ ] **Step 1: Write workflow-contract tests**

Require `ubuntu-24.04`, Python `3.12.15`, read-only permissions, exact checkout of the event SHA, exact dependency lock install, full `tests/cew_b01` suite, source identity verification, deterministic B01 replay, and final receipt validation. Assert no `pull_request_target`, write permissions, secrets/OIDC/attestations, solver commands, CEW-FEM invocation, PR #147 mutation, or auto-merge action.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.cew_b01.test_workflow_contract -v`

Expected: FAIL because the workflow is absent.

- [ ] **Step 3: Implement the minimal validation workflow**

Use pinned GitHub Actions commits rather than floating tags. The workflow is validation infrastructure for current B01 only; do not add a new authority subsystem.

- [ ] **Step 4: Run full local B01 suite**

Run: `python -m unittest discover -s tests/cew_b01 -v`

Expected: PASS.

- [ ] **Step 5: Run compile/static workflow checks available in the repo**

Run the repository's existing Python compile checks plus actionlint/zizmor if already available in the project validation environment. Do not add a separate general-purpose governance framework.

- [ ] **Step 6: Commit**

Commit message: `ci(cew-b01): validate N12 vertical slice`

---

### Task 9: Close B01 Without Auto-Advancing the Master

**Files:**
- Modify only after exact-head B01 PASS: `CEW_CURRENT_STATE.json`
- Create: `docs/cew-b01/CEW_B01_ASSURANCE_REPORT_v1.md`
- Test: `tests/cew_b01/test_current_state_transition.py`

**Interfaces:**
- Consumes: exact-head B01 qualification receipt and CI evidence.
- Produces: B01 assurance report and a state transition to human decision gate only.

- [ ] **Step 1: Write transition tests**

Before exact-head `B01_PASS`, state cannot leave `AUTHORIZED_NOT_STARTED` / in-progress status. After exact-head PASS, the only allowed terminal transition in this plan is `COMPLETED_AWAITING_HUMAN_PHASE_DECISION`. `current_phase` remains `B`; no Phase C authorization is emitted.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.cew_b01.test_current_state_transition -v`

Expected: FAIL before transition logic/report exists.

- [ ] **Step 3: Produce assurance report from exact evidence**

Document frozen source identity, exact toolchain, tool decisions, qualified element count actually achieved, ambiguities/residuals, historical comparator result, geometry scope, all test/CI evidence and explicit exclusions.

- [ ] **Step 4: Update current state only after exact-head qualification**

Set B01 status to `COMPLETED_AWAITING_HUMAN_PHASE_DECISION`; preserve `wip_limit=1`, frozen fronts and PR #147 policy. Do not alter future-phase authorization.

- [ ] **Step 5: Verify full suite and state transition**

Run: `python -m unittest discover -s tests/cew_b01 -v`

Expected: PASS.

- [ ] **Step 6: Request fresh independent review on the exact final head**

Review focus: source immutability, comparator isolation, no hidden manual coordinates, epistemic-state preservation, deterministic geometry, external-tool decisions, no FEM/governance scope expansion.

- [ ] **Step 7: Commit**

Commit message: `docs(cew-b01): close vertical slice at human phase gate`

---

## Self-Review Results

- **Spec coverage:** The plan implements only the Master-authorized B01 path and explicitly preserves all frozen fronts. No Phase C/F work is smuggled into B01.
- **Source integrity:** The selected TAV5 source is reachable from an immutable exact archive commit and is bound by Git blob SHA plus SHA-256.
- **Historical data boundary:** PR #132/OAR is comparator-only and can be loaded only after a source-derived result digest is frozen.
- **No fabricated DXF:** The known archive tree has no DXF; ezdxf is therefore deferred for this slice unless a separate immutable real DXF is discovered before execution and added through an approved plan amendment.
- **Geometry scope:** B01 proves deterministic parametric geometry without pretending that page coordinates or uncertain storey heights are canonical building-space 3D geometry. Full canonical geometry remains Phase C.
- **Human review:** Human review selects/labels machine/source-derived candidate IDs; it does not type replacement coordinates.
- **Completion semantics:** B01 ends at `COMPLETED_AWAITING_HUMAN_PHASE_DECISION`; no automatic roadmap advance is possible.

---

## Execution alignment — 2026-11-07 (CEW-B01 / N12)

**Status:** approved operational sequencing inside the existing CEW-B01 macro-task; planning checkpoint, **not** qualification, canonical-state transition, merge or deployment authority. This addendum does not replace historical Task 1–9 instructions or the verified source-anchor amendment.

### Authority and source-of-truth boundaries

- `CEW_MASTER_PLAN.md` remains the approved A–G roadmap; `CEW_CURRENT_STATE.json` remains the formal authorization record; `wip_limit=1` and `current_task.id=CEW-B01` are unchanged.
- The actual B01 technical experiments advanced in stacked **Draft / unmerged** PRs; this does not mean those changes are in `main`, nor that CEW-B01 has passed the final qualification gate.
- Do **not** change `CEW_CURRENT_STATE.json` to a terminal state before exact-head B01 PASS; Task 9 permits only `COMPLETED_AWAITING_HUMAN_PHASE_DECISION`, and no automatic Phase C activation. The older `AUTHORIZED_NOT_STARTED` field on `main` must be described as a formal-state/experimental-evidence discrepancy rather than silently overwritten.
- PR #147 retains `READ_ONLY_DO_NOT_MODIFY_DO_NOT_CLOSE_DO_NOT_SUPERSEDE`; no new Gate Authority, FEM, SolverRun, Result, merge, deployment or canonical-write authorization.
- The TAV.5 frozen SHA-256 is the **verified** `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580` under the authoritative 2026-10-14 source-anchor amendment; the old SHA in this historical plan is invalid.

### Evidence baseline (observed on 2026-11-07, not requalified by this addendum)

| Scope | Current observed evidence | Boundary |
| --- | --- | --- |
| Source and graphic recognition | Frozen TAV.5 source; 5,633 neutral primitives, 1,663 catalogued motifs in PR #165; downstream 22 governed human-positive column occurrences and 22 `StructuralObjectCandidate` in PR #186 | Counts concern the governed sample, not the complete building; no automatic canonical identity |
| Documentary identity | PR #184 closed its bounded evidence acquisition as `TERMINAL_UNRESOLVED`; the historical `N###` and `S-*` data are not primary identity evidence | Keep support identifiers unresolved without independent primary evidence |
| Cross-source homology | PR #187 checkpoint: 22 `UNMATCHED`, 0 approved homologies; eight primary TAV.5 occurrences selected for professional TAV.5 ↔ TAV-02S review | Human decisions **not yet recorded** |
| Metric relations | TAV-01S: 1 validated relation; TAV-02S: 10 validated relations; total 11/34 reviewed and validated across separate source-local graphs | TAV-02S relation network diagnostically sufficient; this is **not** an absolute/local-to-source calibration anchor |
| Primary calibration | `primary_anchor_count=0`; affine fit, independent holdout, current metric projection not authorized | `PRIMARY_ANCHOR_REQUIRED`; no fit or metric/canonical promotion |
| Parametric geometry | Existing build123d/OCP B01 plan and adapters available for qualification | No current source-derived, canonical N12 3D model may be claimed from this checkpoint |

Evidence locations: PR #151 (this plan); #152 (B01 direct source/tool qualification); #165 (drawing grammar); #184 (identity residual); #185 (governed historical DXF); #186 (22 source-derived structural candidates); #187 (primary metric calibration, metric sufficiency and targeted review). The detailed qualified predecessor and exact-SHA evidence remain in the respective PR descriptions and governance checkpoints.

### Single operational sequence (work inside CEW-B01, currently CEW-CAL-01 / PR #187)

1. **B4 — Inter-source primary homology review (NEXT).** Reuse the qualified eight-case package (`COL-OCC-0013`, `0016`, `0005`, `0002`, `0022`, `0020`, `0001`, `0021`). For each, record the exact TAV.5 source occurrence and the homologous labelled TAV-02S lattice node **only if visually/source-documentarily demonstrated**, otherwise explicit `REJECT/UNRESOLVED` with reason. Preserve source/crop digests, reviewer, review decision and conflict status. Do not auto-suggest the nearest target or synthesize human receipts. If review assets expire, rematerialize and verify the exact frozen upstream inputs/digests before reviewing.
2. **B5a — Primary-anchor discovery.** Using only admissible, source-bound axes/intersections and documented metric relationships, identify enough geometrically independent primary correspondences to determine the TAV.5 ↔ governed metric reference transform. Treat the TAV-02S 21-node lattice as `LOCAL_RELATIVE_METRIC`, not a surveyed/global absolute frame. The already-sufficient TAV-02S relation network does **not** remove the `PRIMARY_ANCHOR_REQUIRED` blocker. TAV-01S receives targeted review only when its independent source-local needs justify it; avoid indiscriminate OCR/quote review.
3. **B5b — Independent metric calibration.** Admit the minimum 3 non-collinear fit anchors + 2 spatially separated, pre-frozen holdouts (prefer more). Freeze selection without residual feedback; estimate only a source-derived 2D affine transform, report holdout errors and frame provenance. If insufficient or degenerate, stop with explicit insufficiency. Historical M0-G, historical affine coefficients, historical `S-*` and inferred `N###` cannot seed fit, target identity, or calibration acceptance.
4. **B6 — Structural reconciliation.** After qualified calibration, project the 22 current candidate occurrences into a candidate metric frame with reproducible digests and uncertainty. Preserve a stable CEW candidate identity; promote no historical support identifier or section family without primary evidence. Select a **non-trivial, source-justified subset** for the next geometric proof; do not force 22/22 resolution or a historically expected count.
5. **B7 — Deterministic geometry proof.** Regenerate the selected subset with build123d/OCP and exact Evidence→Object→Shape mapping receipts. Page/local-frame B-Rep proof is acceptable to B01; do **not** invent storey height, metric placement, armatures or full-building 3D placement. Record epistemic state for every uncertain dimension. Phase C canonical geometry remains separate and unauthorized.
6. **B8 — Close the B01 vertical slice.** Issue exact-head reproducibility, provenance, tool decisions (`ADOPT/BENCHMARK/DEFER/REJECT`), residuals, ambiguity ledger, independent review and human decision packet. The only terminal B01 state proposed by the existing Task 9 remains `COMPLETED_AWAITING_HUMAN_PHASE_DECISION`; moving beyond B01 requires explicit owner approval.

### Acceptance checks and stop conditions

- `B4_PASS`: each reviewed homology has exact source binding and a reasoned human decision; zero accepted matches is a valid fail-closed result, **not** a fabricated pass.
- `B5_PASS`: independently reproducible source-derived anchor inventory, non-degenerate fit, pre-frozen excluded holdouts and measured residuals. A metric network alone is not calibration.
- `B6_PASS`: mapping for the chosen subset preserves documentary status, conflicts and provenance; an unresolved `N###` must remain unresolved.
- `B7_PASS`: at least one real **non-trivial set** of N12 elements is replayed as parametric geometry from qualified CEW evidence without unproven manual coordinates and with matching object/shape digests.
- `B8_PASS`: exact commit/toolchain/input/output digests, complete gate evidence and explicit external-tool decisions, followed by professional review; otherwise return `B01_NOT_QUALIFIED` and report blockers.
- At every stage, `structural_identity_authorized=false`, `canonical_geometry_authorized=false`, `canonical_write_authorized=false`, `m0g_authorized=false` unless a **separate explicit human governance decision** later changes the corresponding boundary; no implicit authority from numeric/geometric agreement.

### DXF and technology amendment boundary

PR #185 now records governed recovered **historical DXF** with source-native text; this is a material development after the original B01 plan's `no immutable DXF` assumption. It justifies a narrowly evidenced future tool decision for `ezdxf`, **not** an automatic replacement of TAV.5 source authority or of this plan's verified immutable PDF source. Distinguish historical CEW-generated `S-*` annotations from the original designer's notation. CADCraft remains a separate non-blocking benchmark. RapidStructure is only an external future candidate for reinforcement representation, not an adopted B01 dependency.

### Cross-PR coordination

- This addendum belongs to the **existing B01 plan PR #151**, not a new roadmap or concurrent macro-task. The current technical next step stays in **Draft PR #187**; its result will be referenced by exact SHA and governed review receipts.
- No source, test, product runtime, main, production deployment or authority document is modified by this planning checkpoint. Downstream stacked PRs must not be reported as newly qualified on an upstream documentation SHA without fresh exact-head checks where required.
- Progress and exit criteria are evidence-based, not calendar-based. If an admissible primary anchor or homologous correspondence cannot be established, the correct next artifact is a diagnosed knowledge gap / targeted investigation request, not a guessed geometric model.
