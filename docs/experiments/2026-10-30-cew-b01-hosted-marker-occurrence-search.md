# CEW-B01 — Hosted-marker occurrence search on TAV.5

Status: `EXPERIMENT_ONLY / SEARCH_REWORK_PASS / HUMAN_GRAPHICAL_REVIEW_PENDING / NON_PROMOTING / G3_NOT_AUTHORIZED`

## Purpose

Extend the exact-source C5/C7 carrier-first pilot into a bounded search for additional occurrences of the same two **neutral graphical states** on TAV.5:

- `RECT_ALONE_ON_CARRIER`;
- `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`.

This experiment does not emit beam identity, slab-support meaning, structural identity or canonical CAD meaning. The proposed human interpretations remain outside executable authority.

## Frozen basis

The search branch is stacked on PR #167. Qualified parent code head:

`5daa6e1f8dd43654a3627b155c0d6dc0c37c820e`

Parent documentation-freeze head:

`69ea22a55cef6e3361ce88d80df3ac15a64ea3d0`

TAV.5 source authority remains:

`sha256:2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`

## Search architecture

`exact source -> 300-dpi raster -> qualified G1 -> complete LineTracks -> local carrier -> every RECTILINEAR_CLOSED_SHAPE -> primitive evidence + local raster evidence -> annotation-dominance gate -> neutral graphical state -> scale-normalized prototype ordering -> bounded Human Review atlas`

C5 and C7 remain same-state **review-ordering prototypes** only:

- C5 `CEW-B01-GP-90cefb124e0b97a63acd1d9c` for `RECT_ALONE_ON_CARRIER`;
- C7 `CEW-B01-GP-f5bf9ee85705380152aae053` for `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`.

Similarity is scale-normalized. Missing raster evidence is never synthesized. Pair provenance is displayed separately:

- G1 primitive local-track pair = magenta;
- raster local-profile recovery = blue;
- carrier tracks = green;
- selected marker = red.

## Initial occurrence-search TDD

Discovery RED:

- head `030f7279a7810694d07313cae53b0515c7682ad4`;
- Unit Gate `41022188927` FAIL;
- 24 inherited contracts PASS;
- causal failure: missing `experiments.cew_b01.hosted_marker_occurrence_search`.

Discovery GREEN:

- head `2110178dcf69c4c27c9c3da9bea2c3177f051bcd`;
- Unit Gate `41022244236` PASS.

Ranking RED:

- head `7c82ce425ecb19ec42dcf0ee99281c7224980273`;
- Unit Gate `41022325169` FAIL;
- causal failure: missing `hosted_marker_signature`.

Ranking GREEN:

- head `606097983299127ac2e6a1873e568e6d1655f0cc`;
- Unit Gate `41022401488` PASS.

## Initial exact-source search

Initial governed search produced 50 carrier-bound rectangles from 124 exact-source `RECTILINEAR_CLOSED_SHAPE` observations:

- 28 `RECT_ALONE_ON_CARRIER`;
- 22 `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE`;
- 48 additional candidates after excluding C5/C7.

Human graphical inspection then identified real inconsistencies:

1. old A10 `CEW-B01-GP-cf4860204d8bb1c826d35f40` enclosed the dimension text `50` and was not a structural-marker candidate;
2. old A17 `CEW-B01-GP-8b7eae9c9f25bb1d73c6f504` was annotation/dimension dominated;
3. the atlas displayed raster-recovered pairs but did not display G1-only primitive pair provenance, making some `PAIR` panels visually misleading.

The initial 50-bound count therefore remains evidence of carrier binding, **not** a qualified review set.

## Rework: preserve evidence, separate candidate role

The rework does not delete a bound occurrence. Every carrier-bound rectangle remains in `all_bound_occurrences` and receives one neutral role:

- `REVIEW_ELIGIBLE`;
- `ANNOTATION_DOMINATED`.

Annotation evidence is kept explicitly rather than used as an untraceable filter.

Two independent signals are evaluated:

1. material same-scope `TEXT_BLOCK` evidence overlapping the marker interior;
2. raster ink components fully enclosed inside the marker and disconnected from its border band.

This separates annotation/dimension boxes from empty hosted markers while retaining every primitive and raster observation as provenance.

## Annotation-gate TDD and exact-source debugging

### First RED / GREEN

New contracts required:

- overlapping text to be preserved but excluded from the review-eligible set;
- enclosed internal ink to mark annotation dominance;
- legitimate transverse strokes crossing the marker boundary not to masquerade as internal text;
- G1-only and raster-only pair evidence to render separately.

RED head:

`16cd129744aa84fcf23c974813876d1567d40e06`

Initial implementation head:

`9c19b8209631c9882a67888f993235793a3e4755`

Unit Gate `41025595241` — PASS.

### Exact-source finding: tiny G1 TEXT_BLOCK noise on C7

The first exact-source hardening correctly rejected A10/A17 but incorrectly rejected C7. Exact-source diagnosis established:

- C7 internal raster component: only `4 px`, below the annotation threshold;
- C7 nevertheless contained a spurious G1 `TEXT_BLOCK` of only `2×2 px`;
- therefore “any TEXT_BLOCK overlap” was too permissive.

RED head `82962dc5c41bb0cd0288d0b4d9f31351543f8368`:

- 38 inherited contracts PASS;
- only the two new text-noise contracts FAIL.

GREEN head `9240b006bf008fcf87bfaf21387d55969f8d103c`:

- Unit Gate `41027260241` — 40/40 PASS;
- Memory Gate `41027260273` — PASS;
- exact-source search `41027260242` — PASS.

That version preserved all 50 bound occurrences and separated 45 review-eligible / 5 annotation-dominated cases.

### Human visual finding: R03 false rejection

Visual inspection of the five rejected panels found another genuine false positive: `CEW-B01-GP-7c4f026034b4c156b84eacc5` was a valid empty `PAIR` marker but had been rejected because a G1 `TEXT_BLOCK` bounding box measured `19×7 px`.

The underlying text observation contained only `41 px` of actual component ink, approximately `0.51%` of the marker area. Material annotation examples were substantially larger:

- A17 text component: `88 px` on a 4,136 px marker (~2.13%);
- another dimension box: `232 px` (~2.84%);
- another dimension box: `294 px` (~3.55%).

The root cause was therefore use of the TEXT_BLOCK **bounding-box overlap area** instead of the real G1 `component_area`.

### Real-ink component-area repair

New RED head:

`0be177300ee70179fb551a4080a39da778c17308`

Unit Gate `41028405382`:

- 39 previous contracts PASS;
- only the two new component-area contracts FAIL.

Final implementation evidence head:

`2f2b1229df35996f434b2664baa097e2c89f3d8b`

The annotation materiality rule now uses actual `TEXT_BLOCK.feature_signature.component_area` when available, normalized against marker area. Bounding-box intersection remains provenance/localization evidence but no longer determines text materiality by itself. Legacy/synthetic observations without component metadata use a conservative fallback.

Fresh verification on this evidence head:

- Unit Gate `41028668720` — **41/41 PASS**;
- Repository Memory Gate `41028668719` — **PASS**;
- exact-source occurrence search `41028668771` — **PASS**.

Exact-source artifact:

- ID `12965071190`;
- name `cew-b01-hosted-marker-occurrence-search`;
- digest `sha256:d65d9cbea92be7cd150fb5889bb7f6ca79e2884db4605f29cd2f81423ddf5cb9`.

Deterministic replay SHA-256:

`f68cfaccb496bd5c8d6b90ed4dbc68d4a3c242bcb9b905c5d01bfbf7ffd76459`

## Final reworked exact-source counts

| Measure | Result |
|---|---:|
| G1 primitives | 5,633 |
| Axis-aligned `LINE_SEGMENT` | 733 |
| `RECTILINEAR_CLOSED_SHAPE` scanned | 124 |
| Reconstructed LineTracks | 158 |
| Neutral carrier candidates | 71 |
| All carrier-bound rectangles | **50** |
| Review-eligible occurrences | **46** |
| Annotation-dominated occurrences | **4** |
| Review-eligible ALONE | **25** |
| Review-eligible PAIR | **21** |
| Additional review candidates excluding C5/C7 | **44** |
| Additional ALONE | **24** |
| Additional PAIR | **20** |

No bound evidence was discarded: `46 + 4 = 50`.

The formerly rejected valid PAIR marker `CEW-B01-GP-7c4f026034b4c156b84eacc5` is now `REVIEW_ELIGIBLE`; its 41-pixel text component is retained in `ignored_tiny_text_block_ids`.

The four remaining `ANNOTATION_DOMINATED` markers are:

- `CEW-B01-GP-cf4860204d8bb1c826d35f40` — visible `50`, strong enclosed internal ink;
- `CEW-B01-GP-8b7eae9c9f25bb1d73c6f504` — dimension/annotation box, material text + enclosed ink;
- `CEW-B01-GP-dd6f0d8649bb8b6add8e0507` — visible `50`, material text + enclosed ink;
- `CEW-B01-GP-f417c150f3a1b9a8d30c7d03` — visible `50`, material text + enclosed ink.

Visual inspection of the final rejected atlas found no remaining empty structural-marker-like rectangle among these four.

## Revised Human Review package

The exact-source artifact contains:

- `hosted-marker-occurrences.json` — all 50 bound occurrences, including 46 eligible and 4 annotation-dominated cases;
- `hosted-marker-occurrence-atlas.png` — 24 nearest **review-eligible** additional candidates;
- `hosted-marker-annotation-dominated-atlas.png` — the four excluded annotation cases.

Pair provenance is visible in the atlas:

- magenta = G1 primitive local-track pair;
- blue = raster local-profile pair;
- both may coexist;
- green = carrier;
- red = marker.

## Governance freeze

The annotation-hardened result is frozen in:

`governance/cew-b01/HOSTED_MARKER_OCCURRENCE_SEARCH_v1.json`

Receipt schema version: `2`.

The temporary exact-source diagnostic workflow used to isolate the C7/A10/A17 discrepancy was removed after its findings were converted into deterministic regression tests and the governed search gate.

## Current disposition

The **search + annotation-separation rework is technically qualified** on the exact TAV.5 source. The candidate set is still not a structural family and has no beam/slab semantic authority.

The next gate remains Human Graphical Review of the **revised** review-eligible atlas using only:

- `GRAPHICAL_MATCH`;
- `GRAPHICAL_NON_MATCH`;
- `ARTIFACT`;
- `UNCERTAIN`.

Only after that review may a separately authorized experiment test whether validated graphical configurations correspond consistently to the proposed technical meanings.

## Authority boundary

- semantic classification: NOT AUTHORIZED;
- proposed `beam carries slab / does not carry slab` mapping: UNVALIDATED HUMAN HYPOTHESIS;
- structural identity: NOT AUTHORIZED;
- canonical writes: NOT AUTHORIZED;
- G2C promotion: NOT AUTHORIZED;
- G3: NOT AUTHORIZED;
- merge: NOT AUTHORIZED.
