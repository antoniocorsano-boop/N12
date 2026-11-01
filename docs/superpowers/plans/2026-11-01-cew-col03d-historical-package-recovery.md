# CEW-COL-03D Historical Package Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover and qualify the exact historical structural v25 package and its eight governed members as byte-verifiable historical evidence, while preserving all COL-03C authority closures and preventing any automatic structural-identity promotion.

**Architecture:** The exact recovered ZIP becomes the immutable package source. A small `cew_col03d` module verifies package provenance, reconciles the historical inventory, verifies required members, parses CSV/DXF content into deterministic evidence-only structures, and writes five closure artifacts. GitHub Actions replays everything from the exact candidate checkout; if the ZIP is not byte-for-byte repository-replayable, the gate fails closed.

**Tech Stack:** Python 3.12, stdlib `zipfile/csv/hashlib/json`, `ezdxf` only if already available in the frozen CEW toolchain, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-col03d-historical-package-recovery-design.md`

## Global Constraints

- Frozen predecessor: `a9daa18ddfb56eaf1834ad17f329e2f2db0af72e`.
- Exact package SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`.
- Exact package size: `5,345,286` bytes; exact member count: `91`.
- Preserve original package/member bytes; no normalization or reserialization in the archive surface.
- Derive the required-member names from governed inventory/policy; reject the COL-03C synthetic `TABELLA_CORRISPONDENZE_TRAVI_v25.csv` name.
- All historical data remain evidence/reference only; every downstream authority flag remains false.
- No mutation of COL-02/COL-03A/COL-03B/COL-03C governed evidence.
- No M0-S, M0-G, canonical CAD/BIM write, G2C/G3, merge or deploy.

## Review Focus

- Same package filename with changed bytes must become `PROVENANCE_MISMATCH`, never accepted by name.
- Inventory-known required member missing from ZIP must become `INVENTORY_PACKAGE_MISMATCH`.
- Name requested by code but absent from governed inventory must become `NOT_IN_GOVERNED_INVENTORY`.
- CSV delimiter/quoting irregularities must not silently shift columns or rows.
- A recovered row marked `VER`, `RIF`, `ND` or `PROPOSTA_GEOMETRICA` must retain that historical state and never gain promotion authority.

---

### Task 1: Preserve the exact v25 package source and freeze package identity

**Files:**
- Add binary: `archive/historical_packages/v25/Ariano_Irpino_DXF_strutturale_v25.zip`
- Create: `experiments/cew_col03d/__init__.py`
- Create: `experiments/cew_col03d/package_source.py`
- Test: `tests/cew_col03d/test_package_source.py`

**Interfaces:**
- Consumes: exact recovered ZIP bytes supplied by the approved recovery source.
- Produces: `verify_package_source(path: Path) -> dict[str, Any]` with package name, size, SHA-256, member count and `MATERIALIZED_VERIFIED` state.

- [ ] **Step 1: Write failing package-provenance tests**

Tests must assert exact digest, exact size, exact member count, ZIP integrity, and `PROVENANCE_MISMATCH` for altered bytes.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `python -m pytest -q tests/cew_col03d/test_package_source.py`

Expected: FAIL because `cew_col03d.package_source`/package source does not yet exist.

- [ ] **Step 3: Add the exact ZIP byte-for-byte and implement `verify_package_source`**

Use binary-preserving repository transport. Immediately recompute SHA-256 from the checked-out repository file; do not trust upload metadata.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Expected: all package-source tests PASS and checked-out file digest equals the frozen package digest.

- [ ] **Step 5: Commit**

Commit message: `feat: preserve COL-03D historical v25 package source`.

### Task 2: Reconcile governed inventory against the verified ZIP

**Files:**
- Create: `experiments/cew_col03d/inventory_reconciliation.py`
- Test: `tests/cew_col03d/test_inventory_reconciliation.py`

**Interfaces:**
- Consumes: `verify_package_source(...)` result plus exact historical inventory text from commit `643dc8934ec0c8ac37613ec2880cf9e02f5a9df2`.
- Produces: `reconcile_required_members(inventory_text: str, zip_member_names: list[str]) -> list[dict[str, Any]]`.

- [ ] **Step 1: Write failing inventory tests**

Pin the eight registered v25 member names. Assert `ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv` is registered and `TABELLA_CORRISPONDENZE_TRAVI_v25.csv` is `NOT_IN_GOVERNED_INVENTORY`.

- [ ] **Step 2: Verify RED**

Run the focused test file; expected failure is missing reconciliation implementation.

- [ ] **Step 3: Implement inventory parsing/reconciliation**

Do not synthesize inventory records for absent names. An inventory-known missing ZIP member is `INVENTORY_PACKAGE_MISMATCH`.

- [ ] **Step 4: Verify GREEN**

Expected: eight required registered members reconcile exactly and obsolete synthetic name is rejected.

- [ ] **Step 5: Commit**

Commit message: `feat: reconcile COL-03D historical package inventory`.

### Task 3: Verify required members and materialize deterministic member provenance

**Files:**
- Create: `experiments/cew_col03d/member_verification.py`
- Test: `tests/cew_col03d/test_member_verification.py`

**Interfaces:**
- Consumes: exact ZIP path and reconciled required-member descriptors.
- Produces: `verify_required_members(zip_path: Path, required: list[dict[str, Any]]) -> list[dict[str, Any]]` with raw path, size, CRC32, SHA-256, materialization state and role.

- [ ] **Step 1: Write failing tests for all eight exact member digests**

Pin the eight member SHA-256 values from the design; include a negative mismatch fixture and ZIP-order perturbation case.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement byte-level member verification**

Read member bytes directly from `zipfile`; never extract-and-reserialize for hashing.

- [ ] **Step 4: Verify GREEN**

Expected: all eight members `MATERIALIZED_VERIFIED`, deterministic ordering independent of central-directory order.

- [ ] **Step 5: Commit**

Commit message: `feat: verify COL-03D historical package members`.

### Task 4: Parse recovered CSV/DXF evidence without authority promotion

**Files:**
- Create: `experiments/cew_col03d/csv_evidence.py`
- Create: `experiments/cew_col03d/dxf_evidence.py`
- Create: `experiments/cew_col03d/historical_quality.py`
- Test: `tests/cew_col03d/test_csv_evidence.py`
- Test: `tests/cew_col03d/test_dxf_evidence.py`
- Test: `tests/cew_col03d/test_historical_quality.py`

**Interfaces:**
- Produces: `parse_csv_member(name: str, data: bytes) -> dict[str, Any]`, `audit_dxf_member(name: str, data: bytes) -> dict[str, Any]`, and `audit_historical_semantics(parsed_members: list[dict[str, Any]]) -> dict[str, Any]`.

- [ ] **Step 1: Write failing CSV parsing tests**

Assert actual row counts: 57 topology rows, 27 TAV5↔TAV7 association rows, 135 matrix rows, 46 TAV6 beam rows, 46 beam-association rows. Test delimiter/quoted-field failure handling and row-width validation.

- [ ] **Step 2: Verify CSV RED**

- [ ] **Step 3: Implement deterministic CSV parser**

Preserve raw headers, raw row provenance and historical state tokens; no source rewrite.

- [ ] **Step 4: Write failing DXF audit tests**

Assert `AC1027` for the three DXFs and deterministic entity/layer/text inventory. No test may assert structural identity from geometry.

- [ ] **Step 5: Implement read-only DXF audit**

Use the existing frozen CEW toolchain where available; otherwise parse only the minimum deterministic DXF sections required by the tests.

- [ ] **Step 6: Write and implement semantic-quality tests**

Pin preservation of `VER`, `RIF`, `ND`, `PROPOSTA_GEOMETRICA`, and historical notes that explicitly deny demonstrated single-column association.

- [ ] **Step 7: Run all Task 4 tests and verify GREEN**

- [ ] **Step 8: Commit**

Commit message: `feat: audit recovered COL-03D historical evidence`.

### Task 5: Build governed recovery artifacts and closure

**Files:**
- Create: `experiments/cew_col03d/recovery.py`
- Create: `experiments/cew_col03d/exact_source.py`
- Test: `tests/cew_col03d/test_recovery.py`
- Test: `tests/cew_col03d/test_exact_source_writer.py`

**Interfaces:**
- Produces five files under `evidence/cew-col03d/`:
  - `historical-package-recovery-manifest.json`
  - `historical-member-manifest.json`
  - `historical-derived-data-quality.json`
  - `historical-recovery-reconciliation.json`
  - `historical-recovery-closure.json`

- [ ] **Step 1: Write failing closure tests**

Assert package/member recovery complete only from exact verified bytes; row-level recovery separate from structural identity; every downstream authority flag false.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement deterministic recovery builders**

Sort member/row evidence canonically; include exact predecessor SHA and source/package digests.

- [ ] **Step 4: Write deterministic replay test**

Build twice with perturbed member/row input order and assert canonical equality/digests.

- [ ] **Step 5: Verify GREEN**

Run all `tests/cew_col03d` plus COL-03C regression tests.

- [ ] **Step 6: Commit**

Commit message: `feat: build COL-03D historical recovery closure`.

### Task 6: Exact-SHA qualification workflow

**Files:**
- Create: `.github/workflows/validate-cew-col03d-historical-package-recovery.yml`
- Test through GitHub Actions on exact candidate SHA.

**Interfaces:**
- Consumes: exact feature head.
- Produces: one exact-SHA workflow evidence artifact containing only `evidence/cew-col03d/`.

- [ ] **Step 1: Add workflow in an intentional RED state**

The first run must prove the workflow is executing against the exact head and fails at the first not-yet-satisfied COL-03D contract rather than infrastructure setup.

- [ ] **Step 2: Complete workflow checks**

Checkout exact SHA; prove COL-03C ancestry; verify package/member digests; run COL-03D tests; run COL-03C regression; execute exact-source writer; verify five-artifact surface; assert all authority closures; upload evidence.

- [ ] **Step 3: Verify fresh exact-SHA GREEN**

Record workflow run, job results, artifact id and artifact digest.

- [ ] **Step 4: Verify Repository Memory Gate on the same SHA**

- [ ] **Step 5: Commit**

Commit message: `ci: qualify COL-03D historical package recovery`.

### Task 7: Final review and checkpoint

**Files:**
- PR metadata/review only; no product changes unless review finds a defect.

**Interfaces:**
- Produces a qualified checkpoint with no merge/deploy.

- [ ] **Step 1: Freshly inspect PR head/base and compare exact diff**

- [ ] **Step 2: Verify no open review threads and no authority drift**

- [ ] **Step 3: Run final technical review focused on package provenance, inventory naming, parser determinism and fail-closed authority**

- [ ] **Step 4: Record exact qualification receipt in PR conversation/body**

State explicitly that recovery of the v25 package does not resolve current support identity or authorize M0-S/M0-G.

- [ ] **Step 5: Stop**

Leave PR Draft/open/unmerged. Do not continue into identity adjudication without a successor design.
