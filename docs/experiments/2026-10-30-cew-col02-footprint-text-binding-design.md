# CEW-COL-02 — Footprint-first column recovery with explicit text binding

**Status:** HUMAN GRAPHICAL REVIEW COMPLETE / PROTOTYPE-GUIDED SEARCH NEXT  
**Date:** 2026-10-30  
**Branch:** `spike/cew-col02-footprint-text-binding`  
**Base:** qualified COL-01 Human Review criterion head `badd2511c1fce8ff9578c6dddfe00fa3f1f86dbc`

## 1. Purpose

COL-02 repairs the residual problem exposed by COL-01 without building another global column detector.

The task is to recover column-footprint candidates **footprint first**, reuse the historical project-local prototype/similarity architecture, and bind OCR/text observations to a footprint only through explicit geometry.

The governing sequence is:

`human/project-local footprint prototype -> page-wide footprint proposals -> local topology -> text-footprint spatial binding -> optional axis evidence -> target-explicit Human Review`

## 2. Why this is a residual repair, not a new subsystem

Repository reconciliation established that CEW already has:

- project-local human prototype teaching and governed receipts (OA-2 / OAR);
- page-wide deterministic similar-object search from a human footprint (PR #136);
- long-axis-suppressed raster envelopes and nested-subcontour suppression (PR #136);
- explainable similarity signals including associated text (OA-3);
- explicit, append-only human cluster review (OA-4);
- a governed 34-support / five-family G4 benchmark (PR #132).

COL-01 adds one new failure class: a crop may contain a true numbered column while the machine OCR anchor is actually an external dimension value. Therefore the missing capability is **target binding**, not generic object detection.

## 3. Scope

COL-02 has five bounded responsibilities:

1. adapt current exact-source footprint proposals to the reusable prototype-search core;
2. compute explicit spatial relations between a text token and a proposed footprint;
3. rank/explain candidates without requiring axes or text;
4. export a Human Review artifact that marks the exact footprint and exact text token separately;
5. persist graphical Human Review decisions without structural/canonical promotion.

## 4. Non-goals

COL-02 does not:

- assign structural identity;
- assign support ID automatically;
- assign section/family automatically;
- compute fixed lines or analytical offsets;
- write canonical CAD/project data;
- use the 34 known support IDs to generate missing detections;
- require symmetry axes;
- treat OCR presence as a candidate prerequisite;
- replace OA-2/OA-3/OA-4 with a new end-to-end subsystem.

## 5. Reused historical slices

### 5.1 Prototype and page-wide similarity

Port/adapt the smallest coherent core from PR #136 `scripts/cew_oar_g4_prototype_search.py`:

- human rectangular footprint as project-local prototype;
- size similarity;
- aspect-ratio similarity;
- rectangularity;
- axis-suppressed envelope preference;
- prototype-region exclusion;
- candidate-level NMS;
- no support identity assignment;
- human review required.

The existing core is coupled to historical support/family binding. COL-02 must decouple **discovery prototype geometry** from pre-known support identity while retaining provenance and human teaching.

### 5.2 Raster footprint proposals

Adapt PR #136 `scripts/cew_oar_g4_snap_worker.py`:

- `LONG_AXIS_SUPPRESSED` proposal channel;
- `RAW_CONTOUR` secondary channel;
- nested sub-contour suppression by geometry;
- rectangularity and envelope evidence.

The historical `FAMILY_RATIOS` may be retained only as benchmark/explanation context if needed; it must not determine object identity or synthesize candidates. Prototype compatibility is the primary retrieval relation.

### 5.3 Human review governance

Reuse OA-4 semantics:

- explicit candidate selection;
- explicit decision per candidate;
- append-only governed receipt;
- receipt lineage to the taught prototype;
- no implicit cluster acceptance;
- structural identity and canonical write false.

The UI/artifact must be adapted because old OA-4 does not visually bind a candidate footprint to a precise OCR token.

## 6. New residual component: text-footprint spatial binder

### 6.1 Input

For each footprint candidate:

- normalized footprint bbox;
- one or more OCR/text observations with bbox and raw/normalized text;
- page/source provenance;
- optional axis/topology evidence.

### 6.2 Required relation states

Every text observation relative to a footprint must be assigned deterministically to exactly one primary relation:

- `INSIDE_FOOTPRINT`
- `INTERSECTS_FOOTPRINT`
- `NEAR_OUTSIDE_FOOTPRINT`
- `UNRELATED_OR_UNBOUND`

The binder must also report quantitative geometry used to derive the relation, including at minimum:

- text bbox area;
- intersection area;
- text-contained fraction;
- center-in-footprint boolean;
- normalized center distance to footprint;
- edge distance where applicable.

### 6.3 Initial deterministic semantics

Proposed initial contract:

- `INSIDE_FOOTPRINT`: text center inside footprint and text-contained fraction >= 0.80;
- `INTERSECTS_FOOTPRINT`: non-zero intersection but not `INSIDE_FOOTPRINT`;
- `NEAR_OUTSIDE_FOOTPRINT`: no intersection, but normalized center/edge distance is within a bounded review radius;
- otherwise `UNRELATED_OR_UNBOUND`.

These thresholds are implementation hypotheses and must be unit-tested and exact-source-qualified; they grant no semantic identity.

### 6.4 Selection of a candidate internal label

A footprint may have zero, one or multiple text observations.

The binder may expose a **review-preferred text observation** only when the relation is `INSIDE_FOOTPRINT`. If multiple internal observations exist, the result must remain explicitly ambiguous unless a deterministic tie-break is justified and review-visible.

No external/nearby number may become a support identifier automatically.

## 7. Candidate model

A COL-02 review candidate should minimally expose:

```text
candidate_id
prototype_id
footprint_bbox
footprint_source_channel
footprint_similarity
rectangularity
axis_evidence_present
text_bindings[]
preferred_internal_text_observation | null
text_binding_state
human_review_state
source_version_id
page_id
page_transform_id
```

Authority fields must explicitly remain false for:

- support identity;
- family confirmation;
- section assignment;
- fixed-line assignment;
- structural identity;
- canonical geometry/write;
- G2C/G3 promotion.

## 8. Target-explicit Human Review artifact

For every selected review candidate produce two paired views:

1. **source-only crop** — untouched pixels;
2. **review overlay crop** — clearly marks:
   - proposed footprint with candidate ID;
   - each OCR/text bbox with token ID;
   - relation state (`INSIDE`, `INTERSECTS`, `NEAR`, `UNBOUND`);
   - preferred internal token, if any;
   - optional axis evidence without obscuring source geometry.

Allowed graphical decisions:

- `COLUMN_GRAPHIC_CONFIRMED`
- `NOT_COLUMN`
- `UNCERTAIN`

Allowed text-binding decisions, separate from column decision:

- `INTERNAL_TEXT_BINDING_CONFIRMED`
- `TEXT_BINDING_REJECTED`
- `TEXT_BINDING_UNCERTAIN`
- `NO_INTERNAL_TEXT_VISIBLE`

A column decision must not implicitly approve the text binding, and a text-binding decision must not create structural identity.

## 9. Exact-source experiment

Source remains immutable TAV-05S:

- path: `archive/documentazione_originaria/tavola 5.pdf`
- page index: `0`
- SHA-256: `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`

Benchmark evidence:

- historical 34-support register is evaluation-only;
- elongated witnesses `18`, `23`, `30` are mandatory reported cases;
- no expected identifier may be injected into OCR or geometry generation.

Primary measurements:

- number of footprint proposals;
- number of prototype-similar review candidates;
- text binding counts by relation state;
- count of candidates with exactly one internal numeric token;
- count with multiple internal tokens;
- count with only near/external numeric tokens;
- human-confirmed column precision in reviewed shortlist;
- human-confirmed text-binding precision;
- benchmark recall, including 18/23/30, reported only after candidate generation.

## 10. TDD order

1. **RED:** pure text-footprint relation classifier does not exist.
2. **GREEN:** implement deterministic relation geometry only.
3. **RED:** multiple/internal/external token selection semantics.
4. **GREEN:** explicit ambiguity and preferred-internal-token contract.
5. **RED:** adapter from current footprint proposals to historical prototype-search core.
6. **GREEN:** reuse/port bounded similarity core with no known-ID dependency.
7. **RED:** target-explicit review manifest contract.
8. **GREEN:** export source-only + overlay review artifacts.
9. exact-source replay and deterministic artifact qualification.
10. Human Review; only then record governed graphical/text-binding receipt.

## 11. Human Review result

The exact-source atlas contained 16 neutral panels. Human Review established:

- `P01 / COL02-FP-0363` → `COLUMN_FOOTPRINT_CONFIRMED`;
- `P02 / COL02-FP-0493` → `COLUMN_FOOTPRINT_CONFIRMED`;
- `P03` through `P16` → `NOT_COLUMN`.

Therefore COL-02 now has **two human-confirmed positive graphical examples and fourteen human-confirmed negatives**.

P01 and P02 are parallel positive examples. The Human Review does not express a preference that one of the two is the unique or primary prototype. A subsequent bounded search may reuse both as the project-local graphical prototype set, provided the matched source prototype is preserved in each candidate's evidence.

The OCR observations internal to P01 (`30`) and P02 (`4`) remain observations only. This review does not confirm them as support identifiers and does not authorize text-to-structural identity binding.

Governed receipt: `governance/cew-col02/COLUMN_FOOTPRINT_HUMAN_REVIEW_v1.json`.

## 12. Success criteria

COL-02 is successful when:

- it demonstrates footprint-first candidate retrieval without requiring OCR or axes;
- a nearby dimension token cannot be silently bound as the internal column identifier;
- the Human Review artifact makes candidate footprint and text target unambiguous;
- elongated witness reporting includes 18/23/30 without using them as production oracles;
- all authority boundaries remain closed;
- exact-source replay is deterministic on a frozen candidate SHA.

COL-02 does **not** require 34/34 automatic recovery to be a useful result. Misses and ambiguous bindings must remain visible and drive the next governed iteration.

## 13. Next gate

`PROTOTYPE_GUIDED_COLUMN_FOOTPRINT_SEARCH_FROM_HUMAN_POSITIVES`

The next bounded search uses P01 and P02 only as human-approved graphical examples. It must not derive support identity, family, section or structural identity from those examples.