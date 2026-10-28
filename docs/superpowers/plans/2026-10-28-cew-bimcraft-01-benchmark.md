# CEW-BIMCRAFT-01 Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualificare BIMCraft v0.9.0 come possibile motore BIM/IFC agentico sostituibile per CEW, con fixture non canonica, read-back, provenance e assurance fail-closed, senza promuovere dati N12 o modificare il Master.

**Architecture:** Il benchmark aggiunge un adapter sottile `CEW benchmark fixture -> BIMCraft command plan`, un contratto di toolchain congelato, osservazioni normalizzate e un receipt. L'esecuzione reale usa l'asset ufficiale BIMCraft v0.9.0 vincolato per SHA-256; la proiezione IFC viene validata separatamente con IfcOpenShell. Lo Stage B N12 resta bloccato finché CEW-B01 non dispone di input human-reviewed compatibili con la propria authority.

**Tech Stack:** Python 3.12.15, `unittest`, BIMCraft v0.9.0 exact commit `c7ba8e2db8d7cc9fbf0847f23c8a56c8e02193f5`, GitHub Actions Ubuntu 24.04, IfcOpenShell già previsto dal Master per il confine IFC.

**Spec:** `docs/superpowers/specs/2026-10-28-cew-bimcraft-01-design.md`

## Global Constraints

- Canonical task: `CEW-B01`; CEW-BIMCRAFT-01 non crea un nuovo macro-task.
- Base di implementazione: `9df814471906a1e4ef618dc71563e78813f03075`.
- BIMCraft resta `PROPOSAL / BENCHMARK / NONCANONICAL / NOT ADOPTED`.
- Nessuna modifica a `CEW_MASTER_PLAN.md` o `CEW_CURRENT_STATE.json` in questa tranche.
- Nessuna scrittura in `data/canonical`.
- Nessun dato `INF / INC / ND` può diventare `DOC`.
- Nessun CEW-FEM, SolverRun, Result, verifica NTC o calcolo EdiLus.
- Nessuna modifica a PR #153/#155/#158/#161 e nessun pilot OpenCADStudio.
- Stage A usa esclusivamente fixture `BENCHMARK_ONLY`.
- Stage B N12 resta bloccato fino a input CEW-B01 source-bound e human-reviewed.
- Asset Linux iniziale: `bimcraft-0.9.0-linux-x86_64.AppImage`, SHA-256 `69aef919a17f7916d3d3b5ab278cb16e27875669bf6b11c0815387d769b57c6f`.
- Ogni assenza/cambio di capability richiesta deve fallire chiuso; niente fallback silenzioso.

## Review Focus

1. **Drift upstream:** un asset diverso con lo stesso nome non deve essere eseguito se il digest non coincide — test Task 1.
2. **Authority leak:** una fixture o proprietà con authority canonica/N12 non ammessa deve essere rigettata prima della compilazione — test Task 2.
3. **Nondeterminismo:** stesso input deve produrre identico command-plan digest — test Task 2.
4. **Read-back incompleto:** elementi mancanti, categorie diverse o proprietà perdute devono produrre REWORK/BLOCKED, non PASS — test Task 3.
5. **IFC loss:** classi/proprietà CEW mancanti nell'IFC devono essere registrate esplicitamente nel receipt — test Task 4.

---

## File Structure

- `governance/cew-bimcraft-01/BIMCRAFT_TOOLCHAIN_v1.json` — lock di release/asset/authority.
- `cew_bimcraft/__init__.py` — package boundary.
- `cew_bimcraft/contracts.py` — caricamento e validazione del toolchain lock e fixture.
- `cew_bimcraft/command_plan.py` — compilazione deterministica fixture -> comandi.
- `cew_bimcraft/reconcile.py` — normalizzazione read-back e confronto con atteso.
- `cew_bimcraft/receipt.py` — receipt del benchmark e classificazione finale.
- `governance/cew-bimcraft-01/fixtures/STAGE_A_STRUCTURAL_FIXTURE_v1.json` — fixture sintetica non canonica.
- `tests/cew_bimcraft/test_toolchain_contract.py` — G0/G1 e fail-closed identity.
- `tests/cew_bimcraft/test_command_plan.py` — authority boundary e determinismo.
- `tests/cew_bimcraft/test_reconcile.py` — G3 read-back.
- `tests/cew_bimcraft/test_receipt.py` — stato e authority del receipt.
- `.github/workflows/validate-cew-bimcraft-01.yml` — exact-head contract + live qualification.

---

### Task 1: Frozen upstream/toolchain contract

**Files:**
- Create: `governance/cew-bimcraft-01/BIMCRAFT_TOOLCHAIN_v1.json`
- Create: `cew_bimcraft/__init__.py`
- Create: `cew_bimcraft/contracts.py`
- Create: `tests/cew_bimcraft/__init__.py`
- Create: `tests/cew_bimcraft/test_toolchain_contract.py`

**Interfaces:**
- Consumes: spec upstream identity and CEW authority constraints.
- Produces: `BIMCraftToolchainContract`, `load_toolchain_contract(path)`, `verify_asset_identity(contract, path)`.

- [ ] **Step 1: Write failing contract tests**

Tests must assert:
- exact `release == "v0.9.0"`;
- exact upstream commit;
- exact Linux x86_64 AppImage SHA-256;
- `adoption_state == "BENCHMARK"`;
- all authority flags false;
- a file with wrong bytes raises `BIMCraftContractError("BIMCRAFT_ASSET_SHA256_MISMATCH")`.

- [ ] **Step 2: Run RED**

Run: `python -m unittest tests.cew_bimcraft.test_toolchain_contract -v`  
Expected: FAIL because `cew_bimcraft.contracts` / governed contract does not exist.

- [ ] **Step 3: Implement minimal contract loader and asset verification**

`contracts.py` must expose:

```python
class BIMCraftContractError(ValueError): ...
@dataclass(frozen=True)
class BIMCraftToolchainContract: ...
def load_toolchain_contract(path: str | Path) -> BIMCraftToolchainContract: ...
def verify_asset_identity(contract: BIMCraftToolchainContract, path: str | Path) -> str: ...
```

No download behavior belongs in production code.

- [ ] **Step 4: Run GREEN**

Run: `python -m unittest tests.cew_bimcraft.test_toolchain_contract -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Commit: `feat: freeze BIMCraft benchmark toolchain contract`

---

### Task 2: Noncanonical fixture and deterministic command plan

**Files:**
- Create: `governance/cew-bimcraft-01/fixtures/STAGE_A_STRUCTURAL_FIXTURE_v1.json`
- Modify: `cew_bimcraft/contracts.py`
- Create: `cew_bimcraft/command_plan.py`
- Create: `tests/cew_bimcraft/test_command_plan.py`

**Interfaces:**
- Consumes: `BIMCraftToolchainContract` and Stage A fixture.
- Produces: `BenchmarkFixture`, `BIMCraftCommandPlan`, `compile_command_plan(fixture)` and stable `sha256`.

- [ ] **Step 1: Write failing fixture/command-plan tests**

Tests must assert:
- fixture authority is exactly `BENCHMARK_ONLY`;
- `project == "CEW-BIMCRAFT-01-STAGE-A"` and contains no N12 canonical identity;
- required provenance keys exist on each structural object;
- a fixture declaring `CANONICAL`, `DOC` without source binding, or `structural_identity_authorized=true` is rejected;
- two compilations of the same fixture produce byte-identical canonical JSON and the same digest;
- command plan contains no free-form shell command and no inferred geometric value.

- [ ] **Step 2: Run RED**

Run: `python -m unittest tests.cew_bimcraft.test_command_plan -v`  
Expected: FAIL because fixture/command-plan interfaces are missing.

- [ ] **Step 3: Implement fixture validation and deterministic compiler**

Use typed normalized records and canonical JSON (`sort_keys=True`, compact separators). The compiler maps only explicit fixture fields into BIMCraft command records. Unsupported element classes must raise a typed fail-closed error.

- [ ] **Step 4: Run GREEN + Task 1 regression**

Run: `python -m unittest tests.cew_bimcraft.test_toolchain_contract tests.cew_bimcraft.test_command_plan -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Commit: `feat: compile governed BIMCraft benchmark command plans`

---

### Task 3: Read-back reconciliation and benchmark receipt

**Files:**
- Create: `cew_bimcraft/reconcile.py`
- Create: `cew_bimcraft/receipt.py`
- Create: `tests/cew_bimcraft/test_reconcile.py`
- Create: `tests/cew_bimcraft/test_receipt.py`

**Interfaces:**
- Consumes: `BenchmarkFixture`, command-plan digest, normalized BIMCraft query/inspect observations.
- Produces: `ReconciliationResult`, `BenchmarkReceipt`, `build_benchmark_receipt(...)`.

- [ ] **Step 1: Write failing reconciliation tests**

Cover exact match, missing element, extra element, category mismatch, level mismatch, geometric mismatch and provenance-property loss. PASS is allowed only for complete expected reconciliation; missing/ambiguous observations are REWORK/BLOCKED.

- [ ] **Step 2: Run RED**

Run: `python -m unittest tests.cew_bimcraft.test_reconcile tests.cew_bimcraft.test_receipt -v`  
Expected: FAIL because reconciliation/receipt interfaces do not exist.

- [ ] **Step 3: Implement reconciliation and receipt**

Receipt must always emit:

```text
canonical_write_authorized=false
structural_identity_authorized=false
fem_authorized=false
master_change_authorized=false
```

and record expected/observed/lost fields rather than hiding them.

- [ ] **Step 4: Run GREEN + full package unit suite**

Run: `python -m unittest discover -s tests/cew_bimcraft -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Commit: `feat: reconcile BIMCraft observations with governed fixture`

---

### Task 4: Exact-head live BIMCraft qualification + IFC boundary

**Files:**
- Create: `.github/workflows/validate-cew-bimcraft-01.yml`
- Modify only if required by observed upstream contract: `cew_bimcraft/command_plan.py`, `cew_bimcraft/reconcile.py`, `cew_bimcraft/receipt.py`, their tests.

**Interfaces:**
- Consumes: exact official v0.9.0 asset, Stage A command plan.
- Produces: Actions artifact `cew-bimcraft-01-stage-a-qualification` with raw observations, IFC when available, and receipt.

- [ ] **Step 1: Add workflow in diagnostic-first mode**

The workflow must:
- checkout exact PR head;
- set Python 3.12.15;
- run all unit tests before external execution;
- download only the exact locked asset URL;
- verify SHA-256 before `chmod`/execution;
- capture `--version`/help/capability output;
- never run an updater;
- write raw diagnostic output even on failure;
- keep all created models under `$RUNNER_TEMP`/artifact paths, never `data/canonical`.

- [ ] **Step 2: Run live workflow and classify the real CLI contract**

Expected first-run outcome may be RED/REWORK if the documented CLI syntax differs from the real binary. That is valid causal evidence; do not broaden permissions or invent compatibility.

- [ ] **Step 3: If RED is caused by a CEW adapter mismatch, add a failing regression test first**

Pin the exact observed upstream response/command contract in a test, verify RED locally/CI, then make the smallest adapter correction.

- [ ] **Step 4: Create/query/save/export only if the exact binary proves those capabilities**

Generate Stage A from the governed command plan; query/inspect it back. If IFC export is available, parse the IFC with IfcOpenShell and record class/property reconciliation. If a capability is absent, classify it `BLOCKED_CAPABILITY` rather than synthesizing success.

- [ ] **Step 5: Run final exact-head qualification**

Required before any positive recommendation:
- unit suite PASS;
- G0 asset identity PASS;
- G1 capabilities PASS for every exercised operation;
- G2 deterministic command plan PASS;
- G3 read-back PASS;
- G4 IFC PASS or explicitly `BLOCKED_CAPABILITY` with no false claim;
- G5 authority boundary PASS.

- [ ] **Step 6: Commit**

Commit: `ci: qualify BIMCraft Stage A on exact upstream binary`

---

### Task 5: Decision report without Master promotion

**Files:**
- Create: `analysis/cew/CEW_BIMCRAFT_01_BENCHMARK_REPORT_v1.md`
- Create: `governance/cew-bimcraft-01/CEW_BIMCRAFT_01_DECISION_INPUT_v1.json`

**Interfaces:**
- Consumes: exact-head qualification receipt/artifacts.
- Produces: one recommendation `ADOPT_CANDIDATE | BENCHMARK_CONTINUE | DEFER | REJECT` for human review.

- [ ] **Step 1: Materialize evidence-backed report**

Report must distinguish documented upstream capability, observed capability, CEW inference, failed/blocked capability and untested capability.

- [ ] **Step 2: Validate no authority escalation**

The machine-readable decision input must keep `master_change_authorized=false`; no edit to Master/current state is allowed.

- [ ] **Step 3: Verify full CEW-BIMCRAFT suite**

Run: `python -m unittest discover -s tests/cew_bimcraft -v`  
Expected: PASS.

- [ ] **Step 4: Commit**

Commit: `docs: record BIMCraft benchmark decision input`

---

## Completion Boundary

`CEW-BIMCRAFT-01` is complete only when a same-SHA benchmark report exists and its supporting qualification evidence is reproducible. Completion does **not** authorize merge, Master modification, N12 canonical mutation, EdiLus import, FEM or tool adoption.

A separate explicit human decision is required before changing BIMCraft from `BENCHMARK` to any canonical toolchain status.