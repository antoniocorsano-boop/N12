# CEW-B01 — Carrier-first hosted-marker pilot

Status: `EXPERIMENT_ONLY / REWORK_UPSTREAM_G1 / NON_PROMOTING / G3_NOT_AUTHORIZED`

## Intent

Test whether the TAV.5 grammar can identify neutral local marker configurations **along a long linear carrier**, instead of starting from an isolated recurring rectangle.

The pilot is motivated by a human observation on TAV.5: a small rectangular marker occurring alone along a beam-like graphic element appears to differ materially from a rectangular marker accompanied by two transverse lines. The proposed technical meanings ("does not carry slab" vs "carries slab") are **human hypotheses only** and are not encoded by this pilot.

## Root-cause finding from the previous eight-seed spike

The previous seed-first composition experiment selected recurring `RECTILINEAR_CLOSED_SHAPE` primitives without first establishing whether they belonged to an object-composition grammar or an annotation/dimension grammar.

A second upstream limitation is concrete: `cew_b01/primitive_census.py` currently constructs `PARALLEL_LINE_PAIR` observations only from the first 220 axis-aligned Hough segments. TAV.5 contains 733 axis-aligned `LINE_SEGMENT` observations. Because those segments are ordered spatially, lower-page geometry can never enter the pair detector. The C7 neighborhood uses line observations around positions 491–545 and therefore cannot rely on G1 `PARALLEL_LINE_PAIR` coverage.

This pilot deliberately does **not** modify qualified G1. It reconstructs neutral carriers from the complete `LINE_SEGMENT` census so the carrier hypothesis can be tested independently.

## Selected approach: carrier-first

`G1 LINE_SEGMENT observations -> deduplicated line tracks -> neutral parallel-track carriers -> hosted rectilinear markers -> transverse-track signature -> Human Review -> later semantic hypothesis validation`

### Why this approach

Three approaches were considered:

1. **Continue seed-first G2B.** Rejected: it only asks what is near a rectangle and does not traverse the host element.
2. **Use existing `PARALLEL_LINE_PAIR` directly as carriers.** Rejected for the pilot: the current 220-segment cap is spatially biased and misses C7-class neighborhoods.
3. **Reconstruct carriers from all `LINE_SEGMENT` observations.** Selected: it is neutral, deterministic, provenance-preserving, and tests exactly the missing relation without changing qualified G1.

## Frozen pilot cases

The first pilot is deliberately limited to two already-inspected TAV.5 cases:

- **C5** seed `CEW-B01-GP-90cefb124e0b97a63acd1d9c` — expected graphical review target: rectangle hosted by a linear carrier with no qualifying transverse pair in its local window.
- **C7** seed `CEW-B01-GP-f5bf9ee85705380152aae053` — expected graphical review target: rectangle hosted by a linear carrier with a candidate pair of orthogonal transverse tracks in its local window.

These expected states are **graphical hypotheses to test**, not semantic labels.

## Neutral objects

### LineTrack

A deterministic coalescence of near-collinear, overlapping Hough `LINE_SEGMENT` observations. It retains all original primitive IDs. Horizontal and vertical tracks are never merged with one another.

### LinearCarrierCandidate

Two distinct, approximately parallel `LineTrack`s with substantial longitudinal overlap and a bounded separation-to-overlap ratio. The candidate retains both track IDs, all contributing primitive IDs, orientation, separation and overlap interval.

### HostedMarkerCandidate

A `RECTILINEAR_CLOSED_SHAPE` whose center and cross-span lie inside one carrier band and whose longitudinal size is local relative to the carrier overlap.

Each hosted marker receives only one of these neutral graphical states:

- `RECT_ALONE_ON_CARRIER`
- `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`

A broad transverse window is retained as context, but it is **not sufficient to form a pair**. After exact-source replay exposed a false positive, pair eligibility was tightened: both orthogonal tracks must cross the carrier and lie locally at or near the marker longitudinal footprint. Remote tracks remain preserved in `transverse_track_ids`/provenance but cannot complete the pair.

Raw duplicate Hough segments never count as separate transverse tracks.

## TDD correction after exact-source inspection

The first hosted-marker implementation passed the synthetic contracts but, on exact C7 evidence, selected one local orthogonal track together with a much more distant orthogonal track from the broad `2.5 ×` window. That yielded a false `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`.

A new regression test was added first on exact RED head `65af148488fab908602daf039787166379187cb8`. All previous contracts passed and only the new remote-pair test failed:

`RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE != RECT_ALONE_ON_CARRIER`

The minimal correction keeps broad-window tracks as contextual evidence while restricting `transverse_pair_track_ids` to tracks whose centerline lies within the marker longitudinal interval or within `max(15 px, 0.25 × marker longitudinal span)` from its edge.

On GREEN implementation head `ba39724ce857f2c25476eb56bac16cb91b7aba83`:

- `CEW-B01 Beam-Hosted Marker Pilot Unit Gate` run `41014931858` — PASS;
- `CEW Repository Memory Gate` run `41014931897` — PASS.

## Exact TAV.5 replay result

Input is the exact qualified `5,633`-primitive census from grammar artifact `12918273768` / run `40922949263`.

The carrier-first reconstruction produces:

- **158** deduplicated neutral `LineTrack`s;
- **71** neutral `LinearCarrierCandidate`s;
- deterministic output under reversed primitive input.

Canonical two-candidate replay digest:

`5840bb0f8acb59df35cb30ac0d34e66d61cdd6f7c4a2f25d1ab123a93f6f0710`

### C5 observed result

- marker: `CEW-B01-GP-90cefb124e0b97a63acd1d9c`;
- carrier: `CEW-B01-LC-f08c6cf6b6ec2b114bd27e72`;
- carrier orientation: `HORIZONTAL`;
- broad transverse tracks: `0`;
- local pair-eligible tracks: `0`;
- observed graphical state: `RECT_ALONE_ON_CARRIER`.

C5 is coherent with its graphical hypothesis. No technical meaning is promoted.

### C7 observed result

- marker: `CEW-B01-GP-f5bf9ee85705380152aae053`;
- carrier: `CEW-B01-LC-e46c764f56e3efdc17905bb8`;
- carrier orientation: `HORIZONTAL`;
- broad transverse tracks: `3`, centerlines `2297.5`, `2559.5`, `1863.666667`;
- local pair-eligible tracks: **1** (`CEW-B01-LT-e3e1145e321e8fb0066be55b`);
- qualifying local pair: none;
- observed graphical state: `RECT_ALONE_ON_CARRIER`.

This does **not** validate the expected C7 two-line graphical configuration. Inspection of the local G1 census shows that the visible neighborhood supplies only one deduplicated vertical track crossing the carrier near the marker; its four raw Hough observations coalesce correctly into one track. The second visually expected local transverse element is therefore absent from the current G1 line evidence.

The correct disposition is `REWORK_UPSTREAM_G1`, not a relaxed G2 rule and not a semantic override.

## Human semantic hypothesis — not executable authority

For later review only:

- proposed interpretation A: `RECT_ALONE_ON_CARRIER` may correspond to a beam that does not carry the slab;
- proposed interpretation B: `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE` may correspond to a beam that carries the slab.

Status for both: `UNVALIDATED_HUMAN_HYPOTHESIS`.

No code in this pilot may emit either technical meaning.

## Success criteria disposition

1. complete line census independent of existing 220-segment pair cap — **PASS**;
2. duplicate Hough observations coalesce with provenance — **PASS**;
3. C5 and C7 bind to neutral carriers — **PASS**;
4. C5/C7 distinguishable as expected by local transverse signature — **REWORK**: current G1 supplies only one local C7 transverse track;
5. source primitive provenance recoverable — **PASS**;
6. reversed-input determinism — **PASS**;
7. semantic/structural/canonical/G3/merge authority remains false — **PASS**.

Overall pilot disposition: **REWORK_UPSTREAM_G1**.

## Next permitted work

Investigate the missing local C7 transverse evidence at G1 without changing semantic authority. The next bounded diagnostic should compare the exact raster around C7 against raw Hough `LINE_SEGMENT` observations and establish whether the missing stroke is:

- not detected by Hough at all;
- detected but classified with a non-axis orientation;
- fragmented below the current minimum length/threshold;
- merged/occluded by raster quality or adjacent geometry.

Only after the missing graphical evidence is explained should the hosted-marker pilot be replayed. No G2C or G3 work is authorized from the current result.

## Non-goals

- no full-corpus classification;
- no automatic beam identity;
- no automatic slab-support meaning;
- no G2C family promotion;
- no G3;
- no merge authorization.
