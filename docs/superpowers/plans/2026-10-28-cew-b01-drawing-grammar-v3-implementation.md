# CEW-B01 Drawing Grammar V3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the narrow Step 4 four-cell-only detector with a high-recall, source-bound candidate system that learns local technical-drawing motif families and supports deterministic `find_similar` without assigning structural identity.

**Architecture:** Keep the qualified V2 compound-cell channel, add a technical-drawing grammar module that derives neutral frame motifs, context fingerprints, prototype/family candidates and similarity matches, then union those candidates in Step 4 with deterministic deduplication. Human review remains the precision/promotion gate; real TAV.5 qualification must regenerate the review surface and expose channel/family evidence.

**Tech Stack:** Python 3.12.15, OpenCV (`opencv-python-headless==5.0.0.93`), existing CEW-B01 evidence/provenance contracts, `unittest`, GitHub Actions exact-SHA qualification.

**Spec:** `docs/superpowers/specs/2026-10-28-cew-b01-drawing-grammar-induction-design.md` and `docs/superpowers/specs/2026-10-28-cew-b01-detector-v3-recall-design.md`

## Global Constraints

- Immutable TAV.5 and the governed Step 3 raster remain evidentiary authority.
- No object-number whitelist, historical count oracle, hand-entered source coordinates or hidden semantic labels in production detection.
- OCR may be diagnostic/confidence evidence only; OCR success is never required for candidate emission.
- Local graphical family/prototype membership never authorizes structural identity or canonical write.
- Unmatched motifs remain explicit `UNKNOWN`; no forced clustering.
- Candidate generation prioritizes recall; human review is the precision gate.

## Review Focus

- Partially closed/hand-drawn frames: recover plausible motifs without requiring perfect rectangles.
- Simple beam-bay rectangles: avoid treating an empty frame or one straight divider as sufficient evidence.
- Rotated/faint internal marks: use topology/ink evidence rather than literal OCR text.
- Repeated variants: group translation/scale-tolerant motifs deterministically while keeping incompatible context separate.
- Dense annotation zones: do not let text/title-block rectangles dominate the candidate surface.

---

### Task 1: Drawing grammar primitives and fingerprints

**Files:**
- Create: `cew_b01/drawing_grammar.py`
- Modify: `tests/cew_b01/test_evidence_extraction.py`

**Interfaces:**
- Produces: `DrawingMotif`, `DrawingGrammarConfig`, `extract_drawing_motifs(binary, config)`, `motif_similarity(left, right)`.
- A motif contains source-local geometry plus non-semantic features: frame quality, aspect ratio, interior ink/components, divider score and four-direction context signature.

- [ ] Write RED tests proving: closed frame + digit-like internal strokes emits a motif; empty frame does not; single full-span divider alone does not qualify; translated variants have high similarity while context-incompatible rectangles do not.
- [ ] Run Step 4 workflow on the exact RED SHA and verify causal failure because the new grammar interfaces do not exist.
- [ ] Implement the minimal grammar primitives/fingerprint extraction and similarity metric.
- [ ] Re-run the focused Step 4 tests and require GREEN.

### Task 2: Prototype/family discovery and find-similar

**Files:**
- Modify: `cew_b01/drawing_grammar.py`
- Modify: `tests/cew_b01/test_evidence_extraction.py`

**Interfaces:**
- Produces: `LocalSymbolFamilyCandidate`, `discover_local_families(motifs, threshold)`, `find_similar(prototype, motifs, threshold)`.
- Family discovery is deterministic and may leave motifs unclustered as `UNKNOWN`.

- [ ] Add RED tests for deterministic family discovery, explicit UNKNOWN residuals, and prototype-driven recovery of a translated/annotated variant without using identifier text or coordinates.
- [ ] Verify RED on GitHub Actions.
- [ ] Implement deterministic clustering/find-similar with stable motif IDs derived from geometry/features.
- [ ] Re-run the focused suite and require GREEN.

### Task 3: Integrate grammar into Step 4 V3 candidate union

**Files:**
- Modify: `cew_b01/evidence_extraction.py`
- Modify: `tests/cew_b01/test_evidence_extraction.py`

**Interfaces:**
- `extract_g4_evidence_candidates(binding, raster_path, config)` remains the public source-bound entry point.
- Candidate generation becomes the deterministic union of `compound_v2` and `drawing_grammar` channels; deduplication remains geometry-based; structural authority flags remain false.

- [ ] Add RED tests proving: a source-like closed numbered motif without four-cell grammar becomes an `EvidenceRegionCandidate`; overlapping V2+grammar detections deduplicate to one region; production code has no number/coordinate oracle.
- [ ] Verify RED.
- [ ] Implement V3 union with method id `OPENCV_DRAWING_GRAMMAR_CANDIDATE_UNION_V3` and deterministic confidence aggregation.
- [ ] Run all Step 4 contract tests and require GREEN.

### Task 4: Real-source qualification and review evidence

**Files:**
- Modify: `.github/workflows/validate-cew-b01-step4.yml`
- Modify: `cew_b01/review_package.py` only if needed to surface channel/family metadata.
- Modify: `tests/cew_b01/test_review_package.py` only if review-package behavior changes.

**Interfaces:**
- Qualification output adds method/channel/family diagnostics without changing source authority.
- Review package remains `PENDING_HUMAN`; no decision file or StructuralObject is created.

- [ ] Extend exact-SHA qualification to record V3 method id, motif count, local family count, UNKNOWN count and candidate count, then replay twice.
- [ ] Generate a fresh Step 4 artifact and Step 5 overview/contact sheets from the V3 candidate set.
- [ ] Inspect the real overview for the omission class exemplified by 19/22; visible compatible symbols left unboxed => REWORK regardless of automated GREEN.
- [ ] Run complete CEW-B01 Step 4/5 workflows on the final exact SHA and record artifacts/digests.

## Completion boundary

Implementation is complete only when exact-SHA automated qualification is GREEN **and** the regenerated TAV.5 overview no longer visibly omits the recurring numbered-symbol class under review. Even then, all candidates remain unreviewed geometric/object candidates until explicit human accept/reject/uncertain decisions are recorded.
