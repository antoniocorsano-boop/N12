# CEW-OS-00 Open Source Qualification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify the open-source capability stack for CEW-EX and establish a compact persistent project-memory entrypoint without promoting experimental branch state into canonical engineering truth.

**Architecture:** Reuse the existing N12 Knowledge System as authority and add a deterministic compact Context Pack for session bootstrap. Qualify external libraries behind CEW ports/adapters and reconcile experimental branches selectively rather than merging them wholesale.

**Tech Stack:** Python 3.12+, GitHub Actions, JSON/CSV/Markdown contracts, PostgreSQL/PostGIS target, Docling Parse, pypdfium2, PaddleOCR, OpenCV, OpenSeadragon, NetworkX, Three.js, IfcOpenShell, Code_Aster; OpenSees and PyMuPDF remain optional/restricted.

**Spec:** `docs/REFERENCE/CEW_OPEN_SOURCE_PLATFORM_BASELINE_v1.md`

## Global Constraints

- CEW owns identity, evidence, provenance, epistemic state, generations, decisions and receipts.
- No parser, AI model, viewer, IFC artifact or solver result becomes canonical authority by itself.
- Experimental branches are selectively reconciled; no bulk merge is authorized.
- Core operation must not depend on `RESTRICTED_OPTIONAL` or commercial components.
- `DOC/MIS/RIF/INF/INC/ND/MOD/POST` distinctions remain explicit.
- Human engineering authority remains required at semantic/professional decision gates.
- The compact bootstrap is derived and disposable; full manifest/state/registry remain authoritative.

## Review Focus

- A stale Context Pack must fail freshness validation rather than silently orienting an agent from obsolete state.
- Adding a Markdown file to `docs/REFERENCE/` must index it as context only, never grant canonical-data authority.
- A provider/model license change must be detectable without rewriting CEW work-item contracts.
- Solver export/import must preserve CEW stable IDs and report unsupported mappings rather than dropping them.
- Diverged experimental branches must be mined by capability/path/contract, not merged because they are newer.

---

### Task 1: Activate the compact project-memory fast path

**Files:**
- Create: `scripts/build_project_context.py`
- Modify: `scripts/agent_bootstrap.py`
- Create: `knowledge/CONTEXT_PACK_CURRENT.json`
- Create: `docs/REFERENCE/CEW_PROJECT_MEMORY_FASTPATH_v1.md`
- Create: `.github/workflows/refresh-cew-context.yml`
- Test: `tests/test_build_project_context.py`
- Test: `tests/test_agent_bootstrap.py`

**Interfaces:**
- Consumes: `knowledge/KNOWLEDGE_MANIFEST.json`, `knowledge/CURRENT_STATE.json`, `knowledge/ARTIFACT_REGISTRY.csv`, optional `data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json`, `docs/REFERENCE/*.md`.
- Produces: `build_context_pack(root: Path) -> dict`, `write_context_pack(root: Path) -> Path`, default compact `agent_bootstrap.py` output; `--full` preserves authority diagnostics.

- [ ] **Step 1: Add failing tests for compact bootstrap, deterministic size, staleness detection and full diagnostic preservation.**
- [ ] **Step 2: Run `python -m unittest tests/test_build_project_context.py tests/test_agent_bootstrap.py`; expect failure because the new generator/bootstrap behavior is absent.**
- [ ] **Step 3: Implement the generator and compact/full bootstrap split with a 16 KiB reference-case ceiling.**
- [ ] **Step 4: Run the two test modules; expect all tests to pass.**
- [ ] **Step 5: Generate the real Context Pack and run `python scripts/build_project_context.py --check`.**
- [ ] **Step 6: Run existing `python scripts/validate_knowledge_system.py`; any regression is blocking.**
- [ ] **Step 7: Commit `feat: add compact CEW project memory bootstrap`.**

### Task 2: Register the approved open-source program baseline

**Files:**
- Create: `docs/REFERENCE/CEW_OPEN_SOURCE_PLATFORM_BASELINE_v1.md`
- Modify: `knowledge/ARTIFACT_REGISTRY.csv` or a dedicated registry patch following existing conventions.
- Modify: `knowledge/KNOWLEDGE_MANIFEST.json` only if required by the existing registry-patch mechanism.

**Interfaces:**
- Consumes: approved baseline and existing Knowledge System authority classes.
- Produces: a stable program reference that is context-authoritative but not structural-data authoritative.

- [ ] **Step 1: Add a validator case proving a program reference cannot feed structural canonical data merely because it is in `docs/REFERENCE/`.**
- [ ] **Step 2: Register the baseline with `authority=PROCEDURE` (or equivalent existing non-data program-reference role), `status=CURRENT`, and no direct structural canonical promotion.**
- [ ] **Step 3: Refresh Context Pack and verify the baseline appears by path/title/status/hash.**
- [ ] **Step 4: Run knowledge validation and commit `docs: register CEW open-source program baseline`.**

### Task 3: Freeze the machine-readable capability and license registries

**Files:**
- Create: `data/canonical/CEW_OPEN_SOURCE_CAPABILITY_REGISTRY_v1.csv`
- Create: `data/canonical/CEW_LICENSE_OBLIGATION_REGISTRY_v1.csv`
- Create: `automation/CEW_ADAPTER_BOUNDARY_REGISTRY_v1.json`
- Test: `tests/test_cew_os00_registries.py`

**Interfaces:**
- Consumes: official license sources and the approved adoption classes.
- Produces: capability/provider decisions, license class, adapter boundary and verification status.

- [ ] **Step 1: Write schema/enum tests for classification and decision fields.**
- [ ] **Step 2: Run tests and confirm RED for missing registries.**
- [ ] **Step 3: Materialize the three registries using only verified provider/license claims; uncertain obligations remain `*_REVIEW_PENDING`.**
- [ ] **Step 4: Run tests and JSON/CSV parse checks.**
- [ ] **Step 5: Commit `governance: add CEW open-source capability and license registries`.**

### Task 4: Build the N12 open-source benchmark matrix

**Files:**
- Create: `analysis/cew/CEW_OPEN_SOURCE_BENCHMARK_MATRIX_v1.csv`
- Create: `tests/test_cew_os00_benchmark_matrix.py`

**Interfaces:**
- Consumes: N12 real source/model fixtures and adapter boundary registry.
- Produces: benchmark IDs `OSB-01..OSB-10`, pass criteria and evidence locations.

- [ ] **Step 1: Write tests requiring every benchmark to name an N12 fixture, provider, pass criterion and non-promotive status.**
- [ ] **Step 2: Run tests and confirm RED.**
- [ ] **Step 3: Populate the matrix with the T1-T4 vertical-slice cases.**
- [ ] **Step 4: Run tests and commit `test: define N12 open-source qualification benchmarks`.**

### Task 5: Reconcile experimental branches by capability, not by merge

**Files:**
- Create: `analysis/cew/CEW_EXPERIMENTAL_CAPABILITY_RECONCILIATION_v1.csv`
- Create: `docs/PLAN/CEW_EXPERIMENTAL_EXTRACTION_PLAN_v1.md`

**Interfaces:**
- Consumes exact heads `419ae14f...`, `b7a25783...`, `195a2e4b...` and the current canonical base.
- Produces per-capability `ADOPT/REIMPLEMENT/DEFER/REJECT`, source paths, tests/gates and target module.

- [ ] **Step 1: Inventory only files/contracts relevant to Source/Evidence, Document Intelligence, Smart Entity, viewer, IFC/FEM, assessment/degradation/investigation and memory/governance.**
- [ ] **Step 2: Record branch divergence and exact source SHA for every adopted candidate.**
- [ ] **Step 3: Reject bulk-merge actions in the extraction plan.**
- [ ] **Step 4: Validate that every `ADOPT` row has an owning test/gate and target path.**
- [ ] **Step 5: Commit `plan: reconcile CEW experimental capabilities selectively`.**

### Task 6: Close CEW-OS-00 qualification gate

**Files:**
- Create: `automation/CEW_OS00_QUALIFICATION_GATE_v1.json`
- Create: `automation/receipts/cew-product/CEW-OS-00_<timestamp>.json` through the normal receipt mechanism.

**Interfaces:**
- Consumes: Tasks 1-5 outputs and all listed tests/gates.
- Produces: a machine-readable T0 closure state; no engineering-data promotion.

- [ ] **Step 1: Define gate requirements for license, provenance, generation, identity, adapter boundaries and benchmark readiness.**
- [ ] **Step 2: Run the full CEW-OS-00 validation set plus existing knowledge-system validation.**
- [ ] **Step 3: If every required check passes, emit a receipt with exact SHA and set T1 eligible; otherwise leave the gate `BLOCKED` with explicit residuals.**
- [ ] **Step 4: Refresh Context Pack so the next session starts from the new gate/next action.**
- [ ] **Step 5: Commit `CEW: close OS-00 qualification gate` only when fresh verification evidence exists.**
