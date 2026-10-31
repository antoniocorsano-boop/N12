# CEW COL-02 Residual Occurrence Reconciliation — Design

## Intent

Close only the residual graphical-occurrence gap exposed by the completed mobile Human Review of the 10 visible-sibling candidates, without repeating that review and without promoting support identity, text identity, structural identity or canonical geometry.

## Frozen inputs

- COL-02 producer exact SHA: `5664614d813cd11cf357bed40d7cdfaa843720f2`.
- Exact source: `archive/documentazione_originaria/tavola 5.pdf`, SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Prototype-guided replay: `11dc8a03789628c6167a8c7cc10fe41d318c5fa22535065598e1c36aa56fd1ac`.
- Occurrence-sweep replay: `bdf6dbdb6a071312727a3ca8146159d4f47514a7bcaec5225235987b0ccb1070`.
- Human review bundle SHA-256: `896036dd048bac77555b383eb7af8329118dedc7f6dd4b5b7373e489f406a0d7`.

Effective Human Review state:
- `PILASTRO`: `COL02-FP-0581`, `COL02-FP-0605`.
- `INQUADRATO_MALE`: `COL02-FP-0252`, `COL02-FP-0106`.
- `NON_PILASTRO`: `COL02-FP-0515`, `COL02-FP-0028`, `COL02-FP-0577`, `COL02-FP-0490`, `COL02-FP-0572`, `COL02-FP-0243`.
- Four additional graphical occurrence points: one recorded while reviewing `COL02-FP-0605`, three while reviewing `COL02-FP-0572`.

## Goal

Produce a deterministic, target-explicit reconciliation manifest containing only:
1. enlarged whole-footprint reframing tasks for the two `INQUADRATO_MALE` candidates;
2. materialized candidate occurrences corresponding to the four human-added normalized points, deduplicated against the existing exact-source proposal set.

The output is a bounded Human Review input, not a column detector and not a structural register.

## Non-goals

- no global re-detection;
- no change to similarity weights or thresholds;
- no OCR-driven identity inference;
- no support number, family, section, fixed-line or structural identity assignment;
- no canonical CAD/BIM write;
- no G2C/G3 promotion;
- no re-review of the eight already adequately framed residual candidates.

## Approach

### 1. Replay the existing Human Review bundle

Resolve append-only `UNDO_LAST` events first. Accept the receipt only if its source lineage exactly matches the frozen COL-02 producer and replay hashes and if every one of the 10 residual candidate IDs has exactly one effective terminal decision.

### 2. Reframe only the two misframed positives

Use the exact source raster and their existing normalized candidate bboxes. Build larger context crops around the same candidate IDs; preserve the original target bbox and candidate identity. No new semantic inference is introduced.

### 3. Materialize human-added points

For each effective `ADDITIONAL_OCCURRENCE` point:
- convert normalized point coordinates back to exact-source raster coordinates using the source crop geometry from the panel in which the point was recorded;
- search only the frozen 611 neutral footprint proposals for proposals containing the point or whose bbox center is within a bounded local tolerance;
- rank deterministically by containment first, then point-to-bbox-center distance, then proposal ID;
- if exactly one best proposal is clearly separated, bind the point to that existing proposal ID;
- otherwise emit a new `HUMAN_POINT_UNBOUND` review item with the exact point and source context, without inventing an object identity.

### 4. Deduplicate

Do not create a new task when a human-added point resolves to:
- an already reviewed S01-S24 target;
- one of the 10 residual candidate IDs already decided;
- the same proposal selected by another added point.

Such cases remain provenance in the reconciliation report and are marked `DUPLICATE_EXISTING_OCCURRENCE`.

### 5. Human gate

The successor atlas contains only unresolved items after deduplication:
- `REFRAME_CONFIRMATION` for the two misframed positives;
- `ADDITIONAL_OCCURRENCE_CONFIRMATION` for unique point-derived proposals;
- `HUMAN_POINT_UNBOUND` when no existing proposal can be bound safely.

Allowed decisions remain graphical only. A positive decision means only visible column-footprint confirmation.

## Output

Machine-readable reconciliation JSON plus a target-explicit review atlas/crops. The JSON records source lineage, original human event IDs, point coordinates, any matched proposal ID, deduplication outcome and authority boundary.

## Governance

`residual_candidate_review_complete = true` remains preserved.

`occurrence_coverage_complete` remains `false` until every successor reconciliation item has a final Human Review decision and no unresolved human point remains.

The following remain `false` throughout this tranche:
- `support_identity_authorized`
- `text_identity_binding_authorized`
- `family_assignment_authorized`
- `section_assignment_authorized`
- `fixed_line_assignment_authorized`
- `structural_identity_authorized`
- `canonical_geometry_authorized`
- `canonical_write_authorized`
- `g2c_promotion_authorized`
- `g3_authorized`
- `merge_authorized`
