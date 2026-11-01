# CEW-COL-03F Primary-Source Identity Bridge Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Acquire deterministic, provenance-complete primary TAV.5 label evidence for all 22 governed column occurrences, prioritizing `COL-OCC-0001` and `COL-OCC-0015`, without promoting any structural identity.

**Architecture:** Add a focused COL-03F evidence-acquisition module that consumes replayed COL-03A/B/E evidence and a freshly materialized primary TAV.5 raster. Pure classification logic is separated from exact-source raster/OCR work. The workflow replays the qualified predecessor chain, runs the bounded targeted OCR/read package, writes JSON plus review images, and verifies all authority remains closed.

**Tech Stack:** Python 3.12.15, stdlib `unittest`, OpenCV from the frozen CEW evidence lock, Tesseract 5.3.4, existing B01 source-contract/PDF probe utilities, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-01-cew-col03f-primary-identity-bridge-evidence-design.md`

## Global Constraints

- Exact predecessor: `cbf57e9261228a7376df826baadc79abe2da254c`.
- Primary source: `CEW-N12-SRC-TAV05S-V2143DBCF`, SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Exactly 22 governed occurrences; no occurrence synthesis or renumbering.
- Inspection priority starts `COL-OCC-0001`, `COL-OCC-0015`, then the remaining IDs ascending.
- Historical `N###`, historical coordinates and historical `VER` are forbidden as positive candidate evidence.
- Candidate evidence may come only from direct `INTERNAL`/`INTERSECTING` focused primary-source label observations.
- Candidate state never means identity resolution; `any_identity_resolved` remains `false`.
- No receipt acceptance, structural identity, family/section/fixed-line/vertical-chain/canonical-node assignment, M0-S, M0-G, canonical write, G2C/G3, merge or deploy.

## Review Focus

- Existing candidate `4` or `30` is not silently treated as confirmed when focused OCR observes no direct matching token — Task 1 test.
- A new numeric value seen by only one OCR configuration does not become a bridge candidate — Task 1 test.
- Two different direct values across OCR configurations become `AMBIGUOUS_DIRECT_LABELS`, not a candidate — Task 1 test.
- OCR crop coordinates must map back to page-normalized coordinates without leaving `[0,1]` or changing the governed occurrence bbox — Task 2 test.
- Historical-looking tokens such as `N001` must never enter the positive bridge candidate surface — Task 1 test.

---

### Task 1: Pure acquisition model and fail-closed candidate classification

**Files:**
- Create: `experiments/cew_col03f/__init__.py`
- Create: `experiments/cew_col03f/acquisition.py`
- Create: `tests/cew_col03f/test_acquisition.py`

**Interfaces:**
- Consumes: governed occurrence IDs, COL-03B documentary candidate values, normalized focused observations.
- Produces: `inspection_priority(...)`, `classify_acquisition_state(...)`, `build_primary_bridge_ledger(...)`, authority-closed ledger rows.

- [ ] **Step 1: Write failing classification tests**

Cover exact cases:

- candidate `4` + direct focused `4` => `CORROBORATED_EXISTING_LABEL_CANDIDATE`;
- candidate `4` + no direct observation => `NO_DIRECT_LABEL_OBSERVED`;
- candidate `30` + direct `31` => `CONTRADICTS_EXISTING_DOCUMENTARY_CANDIDATE`;
- no predecessor candidate + direct `12` in PSM6 and PSM11 => `NEW_MULTI_CONFIG_LABEL_CANDIDATE`;
- no predecessor candidate + direct `12` in one PSM only => `SINGLE_CONFIG_DIRECT_OBSERVATION`;
- direct `12` and `13` => `AMBIGUOUS_DIRECT_LABELS`;
- `NEARBY` values do not support a candidate;
- non-numeric / historical-style token `N001` is excluded from positive candidate values.

- [ ] **Step 2: Run Task 1 tests to verify RED**

Run: `python -m unittest tests.cew_col03f.test_acquisition -v`
Expected: FAIL because `experiments.cew_col03f.acquisition` does not yet exist.

- [ ] **Step 3: Implement pure acquisition model**

Create exact signatures:

```python
def inspection_priority(occurrence_ids: list[str], documentary_candidates: dict[str, list[str]]) -> list[str]
def classify_acquisition_state(documentary_candidates: list[str], observations: list[dict[str, Any]]) -> dict[str, Any]
def build_primary_bridge_ledger(*, occurrence_ledger: dict[str, Any], documentary_ledger: dict[str, Any], col03e_dossiers: dict[str, Any], focused_observations: dict[str, list[dict[str, Any]]], source_ref: dict[str, Any], crop_manifests: dict[str, dict[str, Any]]) -> dict[str, Any]
```

Canonical candidate values are decimal-only strings `1..999`; reject prefixed/suffixed historical identifiers from positive candidate evaluation.

- [ ] **Step 4: Run Task 1 tests to GREEN**

Run: `python -m unittest tests.cew_col03f.test_acquisition -v`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `test: define COL-03F bridge acquisition contract` followed by implementation commit `feat: add COL-03F bridge acquisition model`.

### Task 2: Exact-source bounded crop and targeted OCR acquisition

**Files:**
- Create: `experiments/cew_col03f/exact_source.py`
- Create: `tests/cew_col03f/test_exact_source.py`

**Interfaces:**
- Consumes: qualified COL-03A/B/E evidence roots plus exact TAV.5 source contract.
- Produces: normalized OCR observations, deterministic `FOOTPRINT`/`LOCAL`/`CONTEXT` crop manifests, per-occurrence source-only/overlay PNGs, combined atlas.

- [ ] **Step 1: Write failing geometry and normalization tests**

Test exact crop-bound clipping, normalized page-coordinate reconstruction, fixed `PSM6`/`PSM11` identifiers, candidate-first atlas order, deterministic observation sort order and unchanged occurrence bbox.

- [ ] **Step 2: Run Task 2 tests to verify RED**

Run: `python -m unittest tests.cew_col03f.test_exact_source -v`
Expected: FAIL because exact-source functions are missing.

- [ ] **Step 3: Implement deterministic crop helpers**

Create exact signatures:

```python
def bbox_to_pixels(box: dict[str, float], width: int, height: int) -> tuple[int, int, int, int]
def crop_specs(box: dict[str, float], width: int, height: int) -> dict[str, tuple[int, int, int, int]]
def map_crop_bbox_to_page(*, token_bbox: dict[str, int], crop_bounds: tuple[int, int, int, int], scale: float, page_width: int, page_height: int) -> dict[str, float]
```

- [ ] **Step 4: Implement targeted OCR and review image writer**

Create exact signatures:

```python
def run_targeted_ocr(crop: Any, *, occurrence_id: str, region_class: str, page_bounds: tuple[int, int, int, int], page_width: int, page_height: int, occurrence_bbox: dict[str, float]) -> list[dict[str, Any]]
def write_review_images(...)-> dict[str, dict[str, Any]]
```

Use only fixed Tesseract PSM 6 and 11. Every observation maps back to page-normalized coordinates and carries source/raster provenance later in the ledger builder.

- [ ] **Step 5: Implement exact-source orchestration**

Create:

```python
def acquire_primary_bridge_evidence(*, occurrence_ledger: dict[str, Any], documentary_ledger: dict[str, Any], col03e_dossiers: dict[str, Any], raster_path: Path, source_ref: dict[str, Any], output_root: Path) -> dict[str, dict[str, Any]]
```

It produces the three governed JSON artifacts and review image manifest without any identity promotion.

- [ ] **Step 6: Run Task 2 tests to GREEN**

Run: `python -m unittest tests.cew_col03f.test_exact_source -v`
Expected: PASS.

- [ ] **Step 7: Commit**

Commit message: `feat: acquire focused COL-03F primary-source evidence`.

### Task 3: Closure semantics and deterministic writer

**Files:**
- Modify: `experiments/cew_col03f/exact_source.py`
- Modify: `tests/cew_col03f/test_exact_source.py`

**Interfaces:**
- Consumes: completed ledger + inspection queue.
- Produces: `primary-bridge-evidence-ledger.json`, `primary-bridge-inspection-queue.json`, `primary-bridge-closure.json` and review file hashes.

- [ ] **Step 1: Add failing writer/closure tests**

Assert exactly three top-level JSON outputs, exactly 22 rows, all authority flags false, candidate IDs derived only from allowed states, unresolved IDs explicit, and next action chosen from the two spec-defined values.

- [ ] **Step 2: Run targeted test to verify RED**

Run: `python -m unittest tests.cew_col03f.test_exact_source -v`
Expected: FAIL on missing closure/writer behavior.

- [ ] **Step 3: Implement deterministic JSON writer and closure builder**

Add exact signatures:

```python
def build_primary_bridge_closure(ledger: dict[str, Any], queue: dict[str, Any], predecessor_sha: str) -> dict[str, Any]
def write_col03f_json(output_root: Path, artifacts: dict[str, dict[str, Any]]) -> list[Path]
```

- [ ] **Step 4: Run all COL-03F unit tests**

Run: `python -m unittest discover -s tests/cew_col03f -p 'test_*.py' -v`
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: close COL-03F evidence acquisition surface`.

### Task 4: Exact-SHA qualification workflow and predecessor replay

**Files:**
- Create: `.github/workflows/validate-cew-col03f-primary-identity-bridge-evidence.yml`

**Interfaces:**
- Consumes: exact candidate head, frozen archive commit, qualified COL-03A/B/C/D/E replay chain.
- Produces: exact-source qualification, uploaded `cew-col03f-primary-identity-bridge-evidence` artifact.

- [ ] **Step 1: Add workflow with exact candidate and ancestry checks**

Workflow PR base: `feat/cew-col03e-governed-structural-identity-adjudication`.

Verify `cbf57e9261228a7376df826baadc79abe2da254c` is ancestor of candidate and candidate checkout equals event head SHA.

- [ ] **Step 2: Pin the established evidence toolchain**

Python `3.12.15`, Tesseract `5.3.4-1build5`, `requirements/cew-b01.lock.txt`, plus `pypdfium2==5.14.0` only where predecessor replay requires it.

- [ ] **Step 3: Replay qualified COL-02 → COL-03A → COL-03B → COL-03C → COL-03D → COL-03E**

Reuse existing exact-source commands and frozen digest checks; do not rewrite predecessor outputs.

- [ ] **Step 4: Materialize primary TAV.5 and run COL-03F acquisition**

Assert exact source SHA, exact 22 governed IDs, candidate-first queue, provenance-complete crop/image surface and all authority flags false.

- [ ] **Step 5: Run regressions**

Run COL-03E, COL-03D and COL-03C unit suites after COL-03F qualification.

- [ ] **Step 6: Upload evidence artifact**

Artifact name: `cew-col03f-primary-identity-bridge-evidence`, retention 30 days.

- [ ] **Step 7: Commit**

Commit message: `ci: qualify COL-03F primary bridge evidence`.

### Task 5: Draft stacked PR and fresh qualification review

**Files:**
- No product files beyond prior tasks.
- PR base: `feat/cew-col03e-governed-structural-identity-adjudication`.

**Interfaces:**
- Consumes: Task 1–4 exact candidate.
- Produces: Draft stacked PR, fresh workflow evidence, final checkpoint receipt.

- [ ] **Step 1: Open Draft PR**

Title: `COL-03F — primary-source identity bridge evidence acquisition`.

Body records exact COL-03E predecessor, scope exclusions and current authority closure.

- [ ] **Step 2: Wait only through tool polling performed in this session and inspect fresh workflow result**

Do not merge or deploy.

- [ ] **Step 3: Download and inspect fresh COL-03F artifact**

Report actual state counts, candidate IDs, `0001`/`0015` probe outcomes, unresolved IDs and artifact digest.

- [ ] **Step 4: Check review threads and predecessor concurrency**

Confirm parent PR #183 head unchanged or explicitly report drift; no automatic rebase/merge.

- [ ] **Step 5: Stop at governed checkpoint**

No human receipt synthesis, no identity promotion, no M0-S/M0-G and no canonical write.
