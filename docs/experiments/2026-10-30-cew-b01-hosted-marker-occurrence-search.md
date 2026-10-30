# CEW-B01 — Hosted-marker occurrence search on TAV.5

Status: `EXPERIMENT_ONLY / SEARCH_PASS / HUMAN_REVIEW_PENDING / NON_PROMOTING / G3_NOT_AUTHORIZED`

## Purpose

Extend the exact-source C5/C7 carrier-first pilot into a bounded search for additional occurrences of the same two **neutral graphical states** on TAV.5:

- `RECT_ALONE_ON_CARRIER`;
- `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`.

This experiment does not emit beam identity, slab-support meaning, structural identity or canonical CAD meaning. The proposed human interpretations remain outside executable authority.

## Frozen basis

The search branch was created from PR #167 code head `5daa6e1f8dd43654a3627b155c0d6dc0c37c820e`, whose exact-source C5/C7 qualification was PASS. The parent branch subsequently added only the documentation freeze commit `69ea22a55cef6e3361ce88d80df3ac15a64ea3d0`; the occurrence-search implementation does not modify the parent pilot architecture.

TAV.5 source authority remains:

`sha256:2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`

## Search architecture

`exact source -> 300-dpi raster -> qualified G1 -> complete LineTracks -> local carrier -> every RECTILINEAR_CLOSED_SHAPE -> primitive evidence + local raster evidence -> neutral graphical state -> scale-normalized prototype ordering -> bounded Human Review atlas`

The search deliberately reuses the qualified carrier-first/hybrid pipeline. It does not introduce a learned classifier or a new semantic heuristic.

C5 and C7 are used only as **same-state review-ordering prototypes**:

- C5 `CEW-B01-GP-90cefb124e0b97a63acd1d9c` for `RECT_ALONE_ON_CARRIER`;
- C7 `CEW-B01-GP-f5bf9ee85705380152aae053` for `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`.

Similarity is scale-normalized. It compares marker aspect, carrier-separation ratio, marker/overlap ratio and, when both sides actually expose raster pair evidence, pair-separation ratio. Missing raster evidence is never synthesized.

## TDD evidence

Discovery RED:

- head `030f7279a7810694d07313cae53b0515c7682ad4`;
- Unit Gate run `41022188927`;
- all 24 inherited contracts PASS;
- new module fails causally with `ModuleNotFoundError: experiments.cew_b01.hosted_marker_occurrence_search`.

Discovery GREEN:

- head `2110178dcf69c4c27c9c3da9bea2c3177f051bcd`;
- Unit Gate run `41022244236` PASS.

Ranking RED:

- head `7c82ce425ecb19ec42dcf0ee99281c7224980273`;
- Unit Gate run `41022325169`;
- inherited contracts PASS;
- failure is causal because `hosted_marker_signature` is absent.

Ranking GREEN:

- head `606097983299127ac2e6a1873e568e6d1655f0cc`;
- Unit Gate run `41022401488` PASS.

## Exact-source search result

First exact-source occurrence-search evidence head:

`38ddcab4032811635ee289eb0142f2f57b89c3ef`

Qualification:

- `CEW-B01 Beam-Hosted Marker Pilot Unit Gate` run `41022519713` — PASS;
- `CEW Repository Memory Gate` run `41022519482` — PASS;
- `CEW-B01 Hosted-Marker Occurrence Search` run `41022519552` — PASS.

Artifact:

- ID `12962641547`;
- name `cew-b01-hosted-marker-occurrence-search`;
- digest `sha256:71f518e9c4b547dfae9504e20dd3428ee3067fbdbe9c0cdd0b5dd2ec39cfa520`.

The workflow rematerialized the frozen archival source, regenerated the 300-dpi raster and governed zones, replayed G1 twice and replayed the occurrence search twice deterministically.

Observed exact-source counts:

| Measure | Result |
|---|---:|
| G1 primitives | 5,633 |
| Axis-aligned `LINE_SEGMENT` observations | 733 |
| `RECTILINEAR_CLOSED_SHAPE` seeds scanned | 124 |
| Reconstructed LineTracks | 158 |
| Neutral carrier candidates | 71 |
| Hosted-marker occurrences | 50 |
| `RECT_ALONE_ON_CARRIER` | 28 |
| `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE` | 22 |
| Additional occurrences after excluding C5/C7 | 48 |
| Additional ALONE | 27 |
| Additional PAIR | 21 |

Deterministic occurrence replay SHA-256:

`b94f267a50e204712a50e66b731beff2bc29694e80312bc39936ed2bcc427c04`

## Bounded review atlas

The artifact contains `hosted-marker-occurrence-atlas.png`, limited to the 12 nearest additional occurrences per graphical state — 24 panels total. The full JSON retains all 50 occurrences and all 48 additional ranked candidates.

The atlas is intentionally neutral. Panels show the original raster crop, marker rectangle, reconstructed carrier edges and raster pair strokes when present. No panel contains a beam/slab semantic label.

Initial visual inspection confirms why Human Review remains necessary: the search finds several very close repetitions of the C5-like and C7-like geometry, but the broader ranked set is heterogeneous and includes both horizontal and vertical carrier contexts. Geometric similarity is therefore suitable for review ordering, not semantic promotion.

## Review candidates

The first 12 `RECT_ALONE_ON_CARRIER` additional candidates have prototype distances from `0.0405` through `0.4634`. The first six are especially close to C5 in scale-normalized geometry and all retain no pair evidence.

The first 12 `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE` additional candidates have prototype distances from `0.1315` through `2.0829`. Their pair evidence is heterogeneous:

- raster-only local-profile evidence;
- primitive local-track-pair evidence;
- or both.

This distinction is retained explicitly and must be visible during Human Review.

## Current disposition

The bounded search itself is **PASS**: it is deterministic, exact-source grounded, provenance-preserving, and finds a substantial review set without changing thresholds.

The candidate set is **not** a qualified structural family. The correct next gate is Human Review of the 24-panel atlas using only:

- `GRAPHICAL_MATCH`;
- `GRAPHICAL_NON_MATCH`;
- `ARTIFACT`;
- `UNCERTAIN`.

Only a later, separately authorized semantic review may test whether validated graphical matches correspond consistently to the proposed structural meanings.

## Authority boundary

- semantic classification: NOT AUTHORIZED;
- structural identity: NOT AUTHORIZED;
- canonical writes: NOT AUTHORIZED;
- G2C promotion: NOT AUTHORIZED;
- G3: NOT AUTHORIZED;
- merge: NOT AUTHORIZED.
