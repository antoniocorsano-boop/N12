# CEW-B01 — Marker topology and transverse-band repair

Status: `DESIGN_APPROVED_BY_USER / EXPERIMENT_ONLY / HUMAN_GRAPHICAL_REVIEW_REWORK / NON_PROMOTING`

## Intent

Repair three concrete Human Graphical Review findings from the TAV.5 hosted-marker atlas without promoting technical semantics:

1. the current `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE` is too weak because the relevant graphical configuration can contain **two local transverse traces on one side and two on the other**, not merely one generic pair;
2. a non-target support/junction configuration can be bound to the generic parallel-line carrier and then presented as if it belonged to the same beam-like family;
3. at least one red marker overlay is not sufficiently aligned with the actual black rectangle on the source raster.

The human technical interpretation — isolated rectangle versus slab-section traces, and beam versus column/support — remains an **unvalidated human hypothesis**. This repair describes only neutral graphical evidence.

## Approaches considered

### A. Patch thresholds in the existing pair detector

Rejected. Increasing/decreasing transverse windows or carrier thresholds can make the reported panels look better but does not model the four-trace configuration, carrier topology, or marker alignment. It would overfit the current atlas.

### B. Add direct technical classes (`BEAM`, `COLUMN`, `SLAB_SUPPORTED`)

Rejected. It would skip the current governance boundary and encode structural meaning before graphical families are stable and human-validated.

### C. Three independent neutral gates — selected

1. **Marker grounding gate** — distinguish original G1 rectangle geometry from a raster-refined local rectangle; keep both and never silently rewrite provenance.
2. **Carrier topology descriptor** — characterize continuity/termination/junction around the marker without naming the structural object.
3. **Transverse-band signature** — count and group local orthogonal traces by side of the marker/carrier, allowing a complete `2+2` configuration, partial traces, or no traces.

This approach is selected because each Human Review finding gets its own observable contract and can fail independently.

## Neutral data model

### Marker grounding

Every hosted-marker candidate keeps:

- `source_marker_geometry` — immutable G1 `RECTILINEAR_CLOSED_SHAPE` geometry;
- `review_marker_geometry` — raster-refined geometry used for the red review overlay when refinement is qualified;
- `marker_grounding` with:
  - `method` (`G1_EXACT` or `RASTER_REFINED_LOCAL_RECT`),
  - `edge_residual_px`,
  - `center_shift_px`,
  - `iou_with_source`,
  - `qualified`.

A raster refinement may only be accepted when it finds a closed local rectangle near the source marker and improves edge fit without moving outside a bounded neighborhood. The original G1 geometry is never overwritten.

### Carrier topology descriptor

For the selected carrier, record neutral local topology around the marker:

- longitudinal continuation before marker;
- longitudinal continuation after marker;
- nearby orthogonal junction tracks at each marker end;
- whether the carrier terminates locally near the marker;
- topology state:
  - `THROUGH_CONTINUOUS`,
  - `TERMINAL_OR_STEM`,
  - `JUNCTION_COMPLEX`,
  - `AMBIGUOUS`.

Orientation (`HORIZONTAL` / `VERTICAL`) is descriptive only and must never itself decide inclusion or technical meaning.

### Transverse-band signature

Replace the generic “two transverse tracks = pair” review family with a richer neutral signature:

- detect local orthogonal stroke groups relative to the marker center;
- group them into `NEGATIVE_SIDE` and `POSITIVE_SIDE` along the carrier axis;
- preserve primitive-track and raster-profile provenance independently;
- expose counts and centerlines per side.

Neutral graphical states:

- `RECT_ALONE_ON_CARRIER` — no material local transverse band;
- `RECT_PLUS_DOUBLE_TRANSVERSE_BAND` — at least two distinct local traces on each side (`2+2`) with coherent spacing;
- `RECT_PLUS_PARTIAL_TRANSVERSE_TRACES` — material local transverse evidence exists but does not satisfy the complete `2+2` pattern;
- `ANNOTATION_DOMINATED` remains a role from PR #168, not a transverse state.

The human interpretation “complete double transverse band = slab section” is recorded only in Human Review documentation and is not executable authority.

## Review rendering

The repair micro-atlas must show, for each panel:

- black/gray exact-source raster;
- **red solid** = `review_marker_geometry`;
- **red dashed** = original `source_marker_geometry` only when refinement differs materially;
- green = selected carrier tracks;
- magenta = G1 primitive transverse evidence;
- blue = raster transverse evidence;
- compact text: topology state, side counts, grounding shift/residual, provenance sources.

No panel may display `PAIR` without rendering the evidence that caused it.

## Bounded pilot

Do not rerun full semantic classification. Use a bounded exact-source repair set drawn from:

- C5 — known isolated marker prototype;
- C7 — known complete transverse configuration prototype;
- at least one Human Review carrier-topology false positive (the case described by the user as a column/support treated like a beam);
- at least one Human Review marker-alignment failure;
- representative `ANNOTATION_DOMINATED` controls from PR #168.

If exact panel IDs for the two new Human Review findings cannot be recovered deterministically from the atlas metadata, search the 46 review-eligible candidates for the corresponding graphical condition and preserve the matching IDs in a frozen repair manifest before implementation results are judged.

## Success criteria

1. C5 remains `RECT_ALONE_ON_CARRIER`.
2. C7 exposes a complete **2+2** transverse-band signature on the frozen raster and is not reduced to a generic pair.
3. A carrier topology false positive is no longer indistinguishable from `THROUGH_CONTINUOUS`; it is classified neutrally as `TERMINAL_OR_STEM`, `JUNCTION_COMPLEX`, or `AMBIGUOUS`.
4. A known marker-overlay misalignment produces a qualified raster refinement with both source and review geometry preserved; already aligned markers remain `G1_EXACT` or refine within a negligible tolerance.
5. Annotation-dominated controls remain excluded from the review-eligible structural-graphics set.
6. Reordering primitive inputs does not change descriptors or graphical states.
7. Exact-source replay is deterministic.
8. Semantic classification, structural identity, canonical writes, G2C promotion, G3 and merge authority remain `false`.

## Non-goals

- no automatic `BEAM`/`COLUMN` class;
- no automatic `CARRIES_SLAB`/`DOES_NOT_CARRY_SLAB` class;
- no correction of source documents;
- no full-corpus scaling beyond TAV.5;
- no merge or canonical promotion.

## Human Review after repair

The next human gate remains graphical only:

- `GRAPHICAL_MATCH`;
- `GRAPHICAL_NON_MATCH`;
- `ARTIFACT`;
- `UNCERTAIN`.

Only after the neutral graphical families are stable across representative occurrences may a separate governed step test the user’s technical interpretation.