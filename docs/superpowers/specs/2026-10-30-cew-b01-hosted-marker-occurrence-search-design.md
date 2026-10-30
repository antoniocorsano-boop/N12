# CEW-B01 Hosted-Marker Occurrence Search Design

Status: `EXPERIMENT_ONLY / TAV5_ONLY / NON_PROMOTING / G3_NOT_AUTHORIZED`

## Intent

Extend the exact-source C5/C7 hosted-marker pilot into a bounded search for additional occurrences of the same two **neutral graphical configurations** on TAV.5:

- `RECT_ALONE_ON_CARRIER`
- `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`

The purpose is to test whether the C5/C7 graphical distinction recurs consistently enough to justify a later human semantic review. This search does not assign beam identity, slab-support meaning, structural identity, or canonical CAD meaning.

## Frozen basis

The search starts from PR #167 exact qualified head:

`5daa6e1f8dd43654a3627b155c0d6dc0c37c820e`

Qualified exact-source evidence on that head:

- TAV.5 source SHA-256: `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`;
- G1 primitive count: `5,633`;
- axis-aligned `LINE_SEGMENT` observations: `733`;
- C5 exact graphical state: `RECT_ALONE_ON_CARRIER`;
- C7 exact graphical state: `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`, with the pair recovered from `RASTER_LOCAL_PROFILE` while the G1 primitive state remains `RECT_ALONE_ON_CARRIER`;
- final exact-source qualification run: `41016327209` PASS.

## Goal

Scan every `RECTILINEAR_CLOSED_SHAPE` observation on the frozen TAV.5 source through the already-qualified carrier-first + hybrid evidence pipeline, retain every marker that can be bound to a plausible **local** carrier, and present additional occurrences for human review without changing semantic authority.

## Non-goals

- no search outside TAV.5;
- no full-corpus N12 classification;
- no automatic beam identity;
- no automatic `carries slab / does not carry slab` meaning;
- no G2C family promotion;
- no G3;
- no canonical writes;
- no merge authorization.

## Selected approach

Use the existing deterministic pipeline rather than introducing a new model:

`exact TAV.5 raster -> qualified G1 primitives -> complete LineTracks -> local LinearCarrierCandidate -> every rectilinear marker -> primitive transverse evidence + local raster profile -> neutral graphical state -> scale-normalized prototype similarity -> bounded human-review atlas`

### Why this approach

Three approaches were considered:

1. **Search by raw rectangle geometry only.** Rejected because the earlier eight-seed experiment showed that recurrent rectangles can belong to annotation/dimension grammar and are not sufficient evidence of object composition.
2. **Train a visual classifier from C5/C7.** Rejected because two examples are far too weak to justify an opaque learned boundary and would obscure provenance.
3. **Reuse the qualified carrier-first/hybrid grammar and rank neutral matches by scale-normalized resemblance.** Selected because it preserves provenance, tests the same graphical relation already qualified on exact source, and keeps human review in control.

## Candidate discovery

All G1 primitives with family `RECTILINEAR_CLOSED_SHAPE` are eligible seeds. A seed becomes a hosted-marker occurrence only if the existing `build_hybrid_hosted_marker_candidates` pipeline binds it to a local carrier after the overwide-carrier hardening.

The search must not pre-filter by expected technical meaning, location, floor, member name, or annotation text.

Every occurrence retains:

- marker primitive ID and geometry;
- carrier ID, orientation, separation, overlap and source primitive IDs;
- primitive-only graphical state;
- raster local-profile evidence;
- final neutral graphical state;
- pair evidence sources;
- source/page/frame provenance;
- all authority flags false.

## Prototype similarity

C5 and C7 are references for **review ordering only**, never semantic labels.

For each occurrence, compute a deterministic, scale-normalized geometric signature relative to its carrier orientation:

- marker longitudinal span / marker cross-span;
- carrier separation / marker cross-span;
- marker longitudinal span / carrier overlap length;
- for pair-state candidates only: raster pair separation / marker longitudinal span when raster pair evidence exists.

Similarity distance is the sum of absolute log-ratio differences for available positive-valued signature components shared with the same-state reference prototype. Missing optional pair metrics do not create synthetic evidence; they are omitted from that component comparison.

Occurrences are ordered first by final neutral graphical state, then by prototype distance, then by source geometry and primitive ID for deterministic tie-breaking.

## Human-review package

The exact-source workflow must generate:

1. a complete JSON receipt containing every hosted-marker occurrence found on TAV.5;
2. a bounded atlas containing up to **12 additional occurrences per neutral graphical state**, excluding frozen C5/C7 themselves;
3. each atlas panel must show a crop of the original 300-dpi raster with marker/carrier overlay and raster pair strokes when detected;
4. panels must use neutral candidate IDs and graphical states only — no beam/slab semantic labels.

If fewer than 12 additional matches exist in a state, show all of them. If zero additional matches exist, record that explicitly rather than relaxing thresholds.

## Exact-source qualification

The workflow must regenerate TAV.5 from the frozen archival source and replay the occurrence search twice. Qualification requires:

- exact source SHA matches the frozen source;
- G1 replay remains deterministic at 5,633 primitives;
- all 733 axis-aligned line observations remain available;
- C5 and C7 remain present with their already-qualified neutral states;
- the complete occurrence payload is byte-identical across two executions;
- every emitted occurrence remains nonsemantic/nonpromoting;
- the bounded atlas is produced from the original 300-dpi raster.

The workflow must not assert a minimum number of additional occurrences. A valid search may find none.

## Human review after search

Human review may mark each additional occurrence only as:

- `GRAPHICAL_MATCH`
- `GRAPHICAL_NON_MATCH`
- `ARTIFACT`
- `UNCERTAIN`

Only after a representative set of graphical matches exists may a separate semantic review ask whether the two graphical states correspond consistently to the proposed structural meanings.

## Authority boundary

Throughout this experiment:

- `semantic_classification_authorized = false`;
- `structural_identity_authorized = false`;
- `canonical_write_authorized = false`;
- `g2c_promotion_authorized = false`;
- `g3_authorized = false`;
- `merge_authorized = false`.
