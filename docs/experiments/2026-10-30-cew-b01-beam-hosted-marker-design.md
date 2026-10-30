# CEW-B01 — Carrier-first hosted-marker pilot

Status: `EXPERIMENT_ONLY / NON_PROMOTING / G3_NOT_AUTHORIZED`

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

The second state requires at least two distinct deduplicated tracks orthogonal to the carrier, crossing the carrier band and lying inside a bounded longitudinal window around the marker. Raw duplicate Hough segments do not count as separate transverse tracks.

## Human semantic hypothesis — not executable authority

For later review only:

- proposed interpretation A: `RECT_ALONE_ON_CARRIER` may correspond to a beam that does not carry the slab;
- proposed interpretation B: `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE` may correspond to a beam that carries the slab.

Status for both: `UNVALIDATED_HUMAN_HYPOTHESIS`.

No code in this pilot may emit either technical meaning.

## Success criteria

The pilot passes only if:

1. carrier reconstruction uses the complete line census and is independent of the existing 220-segment `PARALLEL_LINE_PAIR` cap;
2. Hough duplicates collapse into one provenance-preserving track;
3. C5 and C7 both bind to a carrier candidate;
4. C5 and C7 are distinguishable by the neutral transverse-track signature on exact TAV.5 evidence;
5. all source primitive IDs remain recoverable;
6. input order does not change output;
7. semantic meaning remains `None`; structural identity, canonical write, G3 and merge authorization remain false.

## Non-goals

- no full-corpus classification;
- no automatic beam identity;
- no automatic slab-support meaning;
- no modification of qualified G1 in this pilot;
- no G2C family promotion;
- no G3;
- no merge authorization.
