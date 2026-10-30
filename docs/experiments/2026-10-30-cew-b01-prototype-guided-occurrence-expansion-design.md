# CEW-B01 Prototype-Guided Occurrence Expansion — Design

## Intent

Extend the TAV.5 search beyond the eight already-approved DOUBLE candidates by reviewing the remaining exact-source hosted-marker occurrences against the two human-approved graphical prototypes T1 and T2.

The extension must increase recall for Human Review without lowering detector thresholds, granting semantic authority, or changing the source corpus.

## Current baseline

The qualified exact-source replay yields 46 review-eligible hosted-marker records:

- 8 `RECT_PLUS_DOUBLE_TRANSVERSE_BAND` — already reviewed and graphically grouped against T1/T2;
- 14 `RECT_PLUS_PARTIAL_TRANSVERSE_TRACES`;
- 24 `RECT_ALONE_ON_CARRIER`.

The eight DOUBLE records are frozen as the approved reference set and are not reclassified by this work.

## Selected approach

Use a **review-expansion shortlist**, not a new classifier.

1. Start only from the existing 46 exact-source review-eligible records.
2. Exclude the 8 already-reviewed DOUBLE candidates.
3. Exclude known negative-control primitives from the approved micro-pilot.
4. For the first expansion pass, retain partial-trace candidates whose carrier topology is `THROUGH_CONTINUOUS`.
5. Do not assign T1 or T2 automatically. Export source-only crops and supporting metadata; Human Review chooses `T1`, `T2`, `NEITHER`, or `UNCERTAIN`.
6. Rank candidates for review without changing detector thresholds:
   - `A`: at least one matched cross-side pair and both `G1_LINE_TRACKS` + `RASTER_LOCAL_PROFILE` evidence;
   - `B`: no matched pair, but both evidence sources and one-sided trace count >= 3;
   - `C`: raster-only one-sided trace count >= 3.

All retained candidates remain `PROTOTYPE_MATCH_PENDING_HUMAN_REVIEW`.

## Why this approach

A new similarity model or loosened DOUBLE rule would silently turn a Human Review aid into a new detector. The existing replay already contains a richer pool of partial evidence. Shortlisting that pool preserves provenance and lets the approved T1/T2 prototypes act as visual references without treating their human labels as executable semantics.

## Goals

- Produce a deterministic shortlist from the existing exact-source record set.
- Preserve all source/review geometries and primitive IDs.
- Export source-only 300-dpi crops for every shortlisted candidate.
- Include T1 and T2 reference crops in the review package for side-by-side comparison.
- Keep `T1/T2/NEITHER/UNCERTAIN` as Human Review decisions only.
- Preserve all authority flags as false for semantic classification, structural identity, canonical write, G2C, G3 and merge.

## Non-goals

- No threshold tuning in `describe_transverse_band`.
- No changes to hosted-marker extraction, carrier detection, topology detection or grounding.
- No embedding/vision model.
- No automatic T1/T2 family assignment.
- No CAD promotion.

## Determinism and exclusions

The shortlist function must be deterministic under input-order reversal. Known prototype anchors, already-reviewed DOUBLE records and negative controls are excluded by primitive ID rather than by image-content heuristics.

`JUNCTION_COMPLEX` partials are not included in the first expansion pass because their support topology is a distinct ambiguity class already identified by the Human Graphical Review. They may be studied later as a separate topology experiment.

## Expected current TAV.5 expansion set

Against the qualified replay, the first-pass shortlist is expected to contain 11 `THROUGH_CONTINUOUS` partial-trace candidates after excluding the existing negative control.

Expected review-priority distribution:

- Tier A: 6 candidates;
- Tier B: 2 candidates;
- Tier C: 3 candidates.

These counts are contract checks for the frozen source only; they are not universal thresholds or semantic assertions.

## Human Review output

For each shortlisted candidate, the reviewer may decide exactly one of:

- `SIMILAR_TO_T1`;
- `SIMILAR_TO_T2`;
- `NEITHER`;
- `UNCERTAIN`.

The review package must show unmodified source-only crops as visual authority and keep any metadata/labels outside the crop.

## Authority boundary

This experiment authorizes only a governed shortlist for Human Review. It does not authorize automatic semantic beam classification, structural identity, canonical CAD writes, G2C promotion, G3, or merge.
