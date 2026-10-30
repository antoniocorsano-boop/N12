# CEW-B01 — Carrier-first hosted-marker pilot

Status: `EXPERIMENT_ONLY / GRAPHICAL_DISCRIMINATION_PASS / SEMANTIC_VALIDATION_PENDING / NON_PROMOTING / G3_NOT_AUTHORIZED`

## Intent

Test whether exact TAV.5 evidence supports two neutral marker configurations along a long linear carrier: a hosted rectangle with no qualifying local transverse pair, and a hosted rectangle with a qualifying two-stroke transverse pattern. The technical interpretations supplied by the human reviewer — “beam does not carry slab” versus “beam carries slab” — remain **unvalidated human hypotheses** and are not emitted by code.

## Why the previous seed-first experiment was insufficient

The earlier eight-seed spike selected recurrent `RECTILINEAR_CLOSED_SHAPE` primitives before distinguishing object-composition grammar from annotation/dimension grammar. It remains useful as an engineering experiment for G2A0/G2B, but its eight-seed visual benchmark is REWORK and does not authorize G2C.

The carrier-first pilot also established a concrete upstream limitation: qualified G1 builds `PARALLEL_LINE_PAIR` from only the first **220** axis-aligned Hough segments, while exact TAV.5 contains **733**. Because those segments are spatially ordered, lower-page configurations such as C7 cannot rely on complete G1 pair coverage.

## Selected architecture

`all G1 LINE_SEGMENT observations -> deterministic LineTrack -> neutral parallel-track carrier -> hosted rectilinear marker -> primitive local transverse evidence + exact raster local profile -> Human Review -> later semantic validation`

The pilot does not modify qualified G1. It reconstructs carriers from the complete `LINE_SEGMENT` census and retains original primitive provenance.

## Neutral objects

### LineTrack
A deterministic coalescence of near-collinear, overlapping/near-contiguous Hough `LINE_SEGMENT` observations. Horizontal and vertical tracks never coalesce; every original primitive ID is retained.

### LinearCarrierCandidate
Two distinct parallel LineTracks with substantial longitudinal overlap and bounded separation/overlap. A generic pair is accepted as the **local carrier of a marker** only when its separation is no more than `1.6 ×` the marker cross-span.

### HostedMarkerCandidate
A `RECTILINEAR_CLOSED_SHAPE` geometrically bound to a local carrier. It receives only neutral graphical states:

- `RECT_ALONE_ON_CARRIER`
- `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`

Primitive and raster evidence remain explicitly separate. Raster evidence may recover a local stroke missed by Hough, but it never manufactures structural meaning.

## TDD findings and repairs

The work used multiple causal RED→GREEN cycles. The first module RED was `c5e893f6eef41d9ff355f15801c8c39f9b72fec2` / run `41013793695`. A real exact-source false positive later showed that a broad `2.5×` marker window could combine one local transverse track with a remote track. RED `65af148488fab908602daf039787166379187cb8` / run `41014714989` reproduced that failure; pair promotion was tightened while remote tracks remain preserved as context.

Self-review found a second Important boundary defect: a marker could bind to a generic parallel pair much wider than the marker itself. RED `3d6732e95d95e906d332c34ad0bb7e0d268e6ce6` / run `41016177287` passed 23/24 contracts and failed only the new overwide-carrier case. The final code head `5daa6e1f8dd43654a3627b155c0d6dc0c37c820e` adds the local `1.6×` cross-span constraint.

## Final exact-source qualification

The final code head is:

`5daa6e1f8dd43654a3627b155c0d6dc0c37c820e`

Fresh qualification on that exact code head:

- Unit Gate run `41016327090` — **PASS, 24/24 contracts**;
- Repository Memory Gate run `41016327176` — **PASS**;
- Exact-Source Qualification run `41016327209` — **PASS**;
- exact-source artifact `12960036457`, digest `sha256:20a515869b9074ea7847d3348e2393d62ff35a2c382da621ef1b89d4bfb28255`;
- exact replay SHA-256 `2d16982664b702258c2dc3ed15e277ca7db4c29b9fe66fbd4ebacd9ae15800ef`.

The workflow rematerialized the immutable TAV.5 source, regenerated the 300-dpi raster, confirmed the governed G0 zones, regenerated G1 twice, asserted **5,633** primitives and **733** axis-aligned line observations, and executed the C5/C7 hybrid replay twice.

Carrier-first reconstruction produced **158 LineTracks** and **71 neutral carrier candidates**.

## C5 — observed exact-source result

- marker: `CEW-B01-GP-90cefb124e0b97a63acd1d9c`;
- geometry: `(4114, 5135, 44, 116)` px;
- carrier: `CEW-B01-LC-f08c6cf6b6ec2b114bd27e72`;
- orientation: horizontal; separation `122` px;
- primitive local pair: none;
- raster local pair: none;
- final neutral state: **`RECT_ALONE_ON_CARRIER`**.

## C7 — observed exact-source result

- marker: `CEW-B01-GP-f5bf9ee85705380152aae053`;
- geometry: `(2141, 8628, 154, 54)` px;
- carrier: `CEW-B01-LC-e46c764f56e3efdc17905bb8`;
- orientation: horizontal; separation `62.388888` px;
- primitive state: `RECT_ALONE_ON_CARRIER` because G1 exposes only one local pair-eligible Hough track;
- exact-raster local profile: **pair detected** before the carrier cross-axis;
- pair strokes centered at `2257.5` px and `2290.5` px;
- final neutral state: **`RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`**;
- pair evidence source: `RASTER_LOCAL_PROFILE`.

This is the key result: the two cases are now **graphically distinguishable on exact-source evidence without encoding the technical interpretation**.

## Human hypothesis and authorization boundary

Human hypothesis to validate on a broader set:

- `RECT_ALONE_ON_CARRIER` may correspond to a beam that does **not** carry the slab;
- `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE` may correspond to a beam that **does** carry the slab.

Both remain `UNVALIDATED_HUMAN_HYPOTHESIS`. No code emits `BEAM_DOES_NOT_CARRY_SLAB` or `BEAM_CARRIES_SLAB`.

Current authority:

- graphical discrimination on C5/C7: **PASS**;
- broader human validation: **PENDING**;
- semantic classification: **NOT AUTHORIZED**;
- structural identity: **NOT AUTHORIZED**;
- canonical write: **NOT AUTHORIZED**;
- G2C promotion: **NOT AUTHORIZED**;
- G3: **NOT AUTHORIZED**;
- merge: **NOT AUTHORIZED**.

## Remaining limitations

The pilot is intentionally bounded. The line-track union can still require robustness testing against transitive chaining on a larger corpus; the raster local-profile detector needs more negative examples around text/dimensions; generic carrier generation yields many candidates and is only locally constrained at marker binding. An independent code review is still required before any integration.

## Next permitted work

Build a **small human-validation set with multiple occurrences of both graphical variants**, keeping the exact-source carrier/marker/raster evidence visible. Only after the correlation is confirmed should a G2C family hypothesis be considered. G3 remains blocked.
