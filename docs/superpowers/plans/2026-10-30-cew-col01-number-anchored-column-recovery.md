# CEW-COL-01 Number-Anchored Column Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic exact-source audit that finds support-like numeric anchors on TAV-05S, associates them with local column-footprint evidence without requiring axes, and exports a Human Review package that measures H-COL-01.

**Architecture:** Reuse the qualified TAV-05S source contract, rasterization, zoning and neutral primitive census from CEW-B01. Add a small COL-01 adapter layer: parse frozen Tesseract TSV into text-anchor observations, rank local rectilinear footprint evidence around each anchor, classify axis evidence as optional, then run the whole audit twice on the exact source and export source-only review crops plus a JSON manifest. Historical G4 identifiers are benchmark inputs only and never generate candidates.

**Tech Stack:** Python 3.12.15, OpenCV from `requirements/cew-b01.lock.txt`, existing `cew_b01` source/zoning/primitive modules, system Tesseract 5.3.4, GitHub Actions.

**Spec:** `docs/experiments/2026-10-30-cew-col01-number-anchored-column-recovery-design.md`

## Global Constraints

- Exact TAV-05S SHA-256 must equal `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Candidate generation starts from exact-source OCR/token observations, never from the historical expected support list.
- Symmetry axes are optional evidence and must never be a prerequisite for retaining a plausible number+footprint candidate.
- Historical support IDs and families are benchmark/review evidence only.
- No automatic structural identity, section assignment, fixed-line assignment, canonical geometry/write, G2C, G3 or merge authority.
- Outputs must be deterministic across two runs on the same exact source.

## Review Focus

- OCR token `22'` and punctuation normalization must not collapse into the wrong support ID.
- Duplicate OCR reads of the same identifier must remain explicit ambiguity, not silent deduplication into identity.
- A long `30x110`/`110x30`-like footprint with no axis evidence must remain review-eligible.
- Numbers from dimensions/notes inside the structural workarea must not become confirmed columns solely because they are numeric.
- A plausible footprint whose enclosure is interrupted by beam linework must remain distinguishable from a clean closed rectangle.

---

### Task 1: Support-like text-anchor parser

**Files:**
- Create: `experiments/cew_col01/__init__.py`
- Create: `experiments/cew_col01/number_anchor.py`
- Create: `tests/cew_col01/test_number_anchor.py`
- Create: `.github/workflows/validate-cew-col01-number-anchored-column-recovery.yml`

**Interfaces:**
- Consumes: Tesseract TSV text as `str`.
- Produces: `parse_support_like_tsv(tsv_text: str, *, min_confidence: float = 25.0) -> list[dict[str, object]]` and `normalize_support_identifier(text: str) -> str | None`.

- [ ] **Step 1: Write failing tests**

Tests must prove:
- `18`, `23`, `30` are retained with bbox/confidence;
- `22'` and typographic apostrophe normalize to `22'`;
- ordinary dimension text such as `3.50` and alphabetic text are rejected by the support-token parser;
- duplicate identifier observations at different bboxes remain two observations;
- low-confidence tokens are rejected.

- [ ] **Step 2: Run the dedicated COL-01 workflow and verify RED**

Expected: test job fails only because `experiments.cew_col01.number_anchor` is missing.

- [ ] **Step 3: Implement the minimal parser**

`normalize_support_identifier` accepts only one- or two-digit positive integers optionally followed by one apostrophe. `parse_support_like_tsv` parses Tesseract TSV columns (`text`, `conf`, `left`, `top`, `width`, `height`) and sorts output deterministically by `(top, left, normalized_id, text)`.

- [ ] **Step 4: Run workflow and verify GREEN**

Expected: all COL-01 parser tests PASS; existing repository-memory gate remains green if triggered.

- [ ] **Step 5: Commit**

Commit message: `feat(col01): add support-like text anchor parser`.

---

### Task 2: Local footprint evidence with optional axes

**Files:**
- Create: `experiments/cew_col01/local_footprint.py`
- Create: `tests/cew_col01/test_local_footprint.py`
- Modify: `.github/workflows/validate-cew-col01-number-anchored-column-recovery.yml`

**Interfaces:**
- Consumes: one text-anchor mapping plus neutral primitive mappings from `extract_neutral_primitives`.
- Produces: `describe_local_footprint(anchor: dict[str, object], primitives: list[dict[str, object]]) -> dict[str, object]`.

- [ ] **Step 1: Write failing tests**

Tests must prove:
- a closed rectilinear shape containing/near the anchor returns `P1_NUMBER_FOOTPRINT_AXES` when crossing H/V line evidence also exists;
- the same footprint without axis lines returns `P2_NUMBER_FOOTPRINT_NO_AXES` and remains review-eligible;
- an elongated footprint without axes is still `P2_NUMBER_FOOTPRINT_NO_AXES`;
- an anchor with only nearby short rectilinear fragments returns `P3_NUMBER_PARTIAL_FOOTPRINT`;
- an isolated number returns `NO_PLAUSIBLE_FOOTPRINT` and is not confirmed as a column.

- [ ] **Step 2: Verify RED**

Expected: failure because `local_footprint.describe_local_footprint` is missing.

- [ ] **Step 3: Implement minimal local evidence ranking**

Use only local geometric relationships. Prefer `RECTILINEAR_CLOSED_SHAPE` envelopes that contain the anchor center or whose edge distance is within a bounded multiple of anchor size. Record aspect ratio/orientation and search `LINE_SEGMENT` primitives only to set `axis_evidence_present`; do not gate review eligibility on that flag.

- [ ] **Step 4: Verify GREEN and regression suite**

Expected: both COL-01 test files PASS; no existing CEW-B01 unit regression fails.

- [ ] **Step 5: Commit**

Commit message: `feat(col01): classify local column footprint evidence`.

---

### Task 3: Exact-source H-COL-01 audit and Human Review package

**Files:**
- Create: `experiments/cew_col01/exact_source_audit.py`
- Modify: `.github/workflows/validate-cew-col01-number-anchored-column-recovery.yml`
- Test: extend `tests/cew_col01/test_number_anchor.py` with benchmark evaluation helpers if needed.

**Interfaces:**
- Consumes: existing CEW-B01 TAV-05S source contract/zoning/primitive extraction, Tesseract 5.3.4 TSV output, Task 1 parser, Task 2 local footprint descriptor.
- Produces: `evidence/cew-col01/number-anchored-column-recovery/col01-audit.json`, source-only review crops, and `col01-review-atlas.png` as CI artifact.

- [ ] **Step 1: Add failing contract tests for benchmark evaluation**

Tests must prove the benchmark evaluator reports matched/unmatched IDs without creating missing candidates, keeps duplicates visible, and reports elongated witness states for 18/23/30.

- [ ] **Step 2: Verify RED**

Expected: missing audit/evaluator interface.

- [ ] **Step 3: Implement exact-source runner**

Runner must materialize and hash-check TAV-05S, reuse confirmed zoning and primitive extraction, invoke `tesseract <raster> stdout --psm 11 tsv`, parse anchors, classify local footprint evidence, evaluate historical benchmark coverage, run twice and compare canonical JSON bytes, then write the manifest.

`H-COL-01` status rules:
- `UNVERIFIED` if OCR/exact-source evidence is unavailable or benchmark denominator cannot be established;
- `SUPPORTED` if measured identifier coverage is at least 90%;
- `REJECTED` otherwise.

The percentage is an experimental hypothesis threshold only, not an engineering authority threshold.

- [ ] **Step 4: Export Human Review package**

Review ordering: elongated 18/23/30 first when retrieved, then `P2_NUMBER_FOOTPRINT_NO_AXES`, OCR duplicate/ambiguity cases, then a bounded sample of P1. All image labels stay outside source-only crop interiors.

- [ ] **Step 5: Run exact-source workflow and inspect artifact**

Expected: workflow PASS only if two-run determinism, authority assertions and artifact generation all pass. Record actual H-COL-01 coverage; do not patch missed IDs with hard-coded detections.

- [ ] **Step 6: Commit**

Commit message: `exp(col01): audit number-anchored column recovery on exact TAV5`.

---

### Task 4: Governed checkpoint and PR state

**Files:**
- Create: `governance/cew-col01/COL01_EXACT_SOURCE_AUDIT_v1.json` after a successful exact-source run.
- Modify: PR body only; no product/code changes.

**Interfaces:**
- Consumes: successful Task 3 exact-head run IDs, artifact ID/digest, measured coverage and witness states.
- Produces: auditable non-promoting checkpoint ready for Human Review.

- [ ] **Step 1: Record exact run evidence**

Receipt includes exact SHA, source SHA, workflow run, artifact metadata, actual H-COL-01 status, matched/unmatched benchmark IDs, elongated witness states and authority boundary.

- [ ] **Step 2: Requalify receipt head**

Run fresh COL-01 + repository-memory gates on the receipt exact head.

- [ ] **Step 3: Update Draft PR**

PR remains Draft/open/non-merged and states that Human Review is pending. No merge authorization.

- [ ] **Step 4: Commit**

Commit message: `governance(col01): record exact-source audit checkpoint`.
