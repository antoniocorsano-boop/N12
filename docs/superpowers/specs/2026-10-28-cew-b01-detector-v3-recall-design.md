# CEW-B01 Detector V3 — High-Recall Structural Symbol Candidate Design

**Date:** 2026-10-28  
**Parent task:** `CEW-B01`  
**Base:** `impl/cew-b01-step1-source@e20e9daba1dce08f53ddb26f06efc9c5b2745211`  
**Status:** DESIGN — pending human approval

## Intent

Correct the current Step 4 detector so that the human review package is no longer presented as complete when visibly plausible structural symbols remain unselected in the TAV.5 overview.

The detector must prefer **high recall** at candidate-generation time. Human review remains the precision gate: false positives are acceptable within a manageable review set; silent false negatives are not.

## Evidence that motivates the change

The current V2 method, `OPENCV_COMPOUND_RECTANGULAR_CELL_ENVELOPE_V2`, reconstructs a candidate only from a strict four-cell compound-symbol grammar with a qualified outer frame. The existing tests intentionally reject generic rectangles and T-junction/beam-like patterns.

Human inspection of the qualified Step 5 overview identified visible numbered rectangular symbols not enclosed by the V2 candidate overlays. Symbols identified visually as 19 and 22 are concrete examples, and the overview indicates additional similar omissions.

These examples are **verification cases**, not coordinates or hard-coded truth. The implementation must rediscover them from the immutable source raster by a general rule.

## Goals

1. Increase recall for source-like structural symbols that contain a closed rectangular envelope and internal identifying marks/digits but do not satisfy the exact V2 four-cell grammar.
2. Preserve source binding, deterministic replay, provenance, candidate IDs and fail-closed raster identity checks.
3. Preserve the rule that candidate generation assigns no structural identity and performs no canonical promotion.
4. Produce a new overview/contact-sheet package from the new candidate set before any human accept/reject decision is recorded.
5. Make omissions detectable in qualification: a candidate set is not considered review-ready merely because it is deterministic.

## Non-goals

- No manual insertion of symbols 19, 22 or any other candidate by coordinates.
- No use of historical OAR counts, PR #132 support counts, family counts or known N12 object locations as detector inputs.
- No automatic structural identity assignment.
- No automatic interpretation of the internal number as a canonical object identifier.
- No Step 6 promotion in this change.
- No change to BIMCraft adoption or Stage B authority.

## Approaches considered

### A. Relax V2 geometric thresholds only

Keep the four-cell composition model and lower rectangularity, overlap, alignment or side-coverage thresholds.

**Trade-off:** smallest code change, but it does not address the actual failure mode when a legitimate symbol has a different internal subdivision grammar. Rejected.

### B. OCR-first numbered-rectangle detector

Detect rectangles and require OCR/numeric recognition inside them.

**Trade-off:** directly targets the visual cue seen by the reviewer, but handwritten/rotated/faint digits make OCR too brittle to be the sole gate. It also risks coupling candidate generation to semantic text interpretation. Rejected as primary strategy.

### C. Hybrid high-recall candidate union — selected

Generate candidates from multiple independent geometric cues and merge/deduplicate them:

1. retain the current V2 compound-cell detector as a high-confidence channel;
2. add a **closed-envelope channel** for source-like rectangular/square symbols within governed size/aspect bounds;
3. require the closed-envelope channel to contain a minimum amount of internal ink/mark structure inside the frame, excluding a clean empty rectangle;
4. treat digit-like/internal-mark evidence as a confidence feature, not as a semantic requirement and not as a canonical ID;
5. optionally use nearby line/axis/beam context as a confidence feature rather than a hard requirement;
6. union the channels and perform deterministic geometry-based deduplication.

This approach matches the CEW review model: machine proposes plausible source-bound regions; the human decides what they mean.

## Proposed detector contract

Rename the method to a new version, for example:

`OPENCV_STRUCTURAL_SYMBOL_CANDIDATE_UNION_V3`

The public entry point remains:

`extract_g4_evidence_candidates(binding, raster_path, config)`

No historical comparator or manual oracle is added to its interface.

Internally, candidate generation is split into focused channels:

- `compound_cell_envelopes`: existing V2 behavior;
- `closed_numbered_like_envelopes`: closed frames with internal non-frame ink;
- deterministic `candidate_union` + IoU/containment deduplication;
- confidence assembled from geometric frame quality, internal-mark density and contextual line evidence.

A candidate's confidence expresses detector evidence only. It does not authorize structural identity.

## Internal-mark rule

For a candidate outer frame, compute an **interior zone** by shrinking the frame by a configurable border margin. Measure foreground ink in the interior after excluding pixels attributable to the outer frame.

The channel should require:

- a closed or near-closed rectangular frame;
- governed width/height/aspect constraints;
- interior foreground above a minimum density or connected-component count;
- interior structure that is not merely one straight divider spanning the full frame, to avoid re-admitting simple beam-bay rectangles as equivalent evidence;
- no OCR success requirement.

The exact thresholds are implementation parameters and must be pinned by synthetic tests plus real-source diagnostic evidence, not tuned to a desired candidate count.

## Review-readiness rule

Determinism remains necessary but is no longer sufficient to call Step 4 ready for human review.

Qualification must produce:

- deterministic candidate set and bundle digest;
- overview/contact sheets;
- a machine-readable channel breakdown per candidate (`compound_v2`, `closed_internal_mark`, or both);
- diagnostic counts per channel;
- zero structural/canonical promotions.

The human review then assesses the new complete-looking candidate surface. If visible source-like symbols remain unboxed, the detector stays REWORK even if all automated tests are green.

## Required tests

### Preserve current boundaries

Existing tests for deterministic replay, source binding, no historical oracle, V2 compound symbols and beam/T-junction rejection must remain green unless explicitly superseded by a stronger equivalent test.

### New RED→GREEN cases

1. **Closed frame + internal digit-like strokes, no four-cell grammar** → candidate emitted.
2. **Rectangular frame with rotated/internal mark and one-sided structural context** → candidate emitted.
3. **Empty closed rectangle** → not emitted by the new channel.
4. **Single full-span divider only** → not sufficient by itself for the new channel.
5. **Two overlapping channels on the same physical symbol** → one candidate after deterministic deduplication.
6. **Candidate ordering/digests stable across replay** → identical semantic candidate set.
7. **No known object numbers or hand-entered coordinates in production detector code**.

### Real-source qualification

The immutable TAV.5 raster is replayed twice. The resulting overview must be inspected specifically for previously observed omission patterns, including the visual patterns exemplified by symbols 19 and 22. Passing does not require a hard-coded total candidate count.

## Governance and provenance

- Original TAV.5 remains the evidentiary authority.
- The Step 3 governed raster remains the only image input.
- New candidates are still `EvidenceRegionCandidate` only.
- `semantic_identity_assigned = false`.
- `structural_identity_authorized = false`.
- No manual candidate coordinate is permitted in production fixtures or qualification inputs.
- Prior V2 artifacts remain historical evidence and are marked superseded for the next human-review input; they are not deleted or rewritten.

## Expected workflow after implementation

`immutable TAV.5 → governed raster → V3 high-recall candidate union → deterministic evidence bundle → new overview/contact sheets → human accept/reject/uncertain → accepted source-bound IDs only → Step 6`

## Success criterion

The detector is successful when it produces a deterministic, source-bound candidate surface suitable for human review **without visibly omitting the class of numbered structural symbols observed in the current overview**, while keeping structural interpretation and promotion exclusively behind the human gate.
