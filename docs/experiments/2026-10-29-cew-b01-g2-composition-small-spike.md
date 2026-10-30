# CEW-B01 — G2 composition small spike

Status: `EXPERIMENT_ONLY / NON_PROMOTING / G3_NOT_AUTHORIZED`

## Purpose

Test, on a deliberately small real-source sample, whether the current G2 grouping of individual graphic primitives hides materially different local compositions.

This is not semantic recognition. The experiment only asks whether a bounded set of qualified G1 primitives can be assembled into neutral local `SymbolCandidate`-like compositions with an explicit `CORE` and `CONTEXT` boundary.

## Frozen input

- qualified PR head: `e04db7ab21ebb5c1afd69936e17cf13a7421f2af`
- exact qualification run: `40922949263`
- workflow artifact: `12918273768` (`cew-b01-grammar-foundation-review`)
- source TAV.5 SHA-256: `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`
- qualified G1 primitive census: `5,633` observations
- pilot seeds: `8`

The eight seeds are four representative instances from each of the two most recurrent `RECTILINEAR_CLOSED_SHAPE` motifs in the qualified G2 catalog. The frozen seed list lives in `governance/cew-b01/G2_COMPOSITION_SMALL_PILOT_v1.json`.

## Experimental composition rule

The spike builds a local geometric graph around each seed and records neutral relations only:

- `CONTAINS / CONTAINED_BY`
- `OVERLAPS`
- `TOUCHING / NEAR`
- `ALIGNED_H / ALIGNED_V`
- `PARALLEL / ORTHOGONAL` when orientation evidence exists

The original experimental `24`-member CORE cap was a presentation bound only. It was never a production threshold and carried no structural meaning.

## Exact small-run result before G2A0

Running `experiments/cew_b01/g2_composition_small_spike.py` against the qualified `primitive-census.json` produced raw CORE vector:

`3, 24, 1, 2, 1, 24, 4, 10`.

The strongest neutral composition similarities in the first spike were `3 ↔ 5 = 0.683`, `2 ↔ 6 = 0.598`, `7 ↔ 8 = 0.521`. These were ranking aids only. No acceptance threshold or family promotion was authorized.

## Visual finding from the first micro-atlas

Candidates `2` and `6` both hit the experimental 24-member cap, but many of those members were co-spatial or near-coincident observations such as `INTERSECTION`, `CROSS_MOTIF`, `T_JUNCTION` and `T_SHAPED_MOTIF` derived from the same local strokes.

Therefore raw G1 observation cardinality cannot be treated as physical or symbolic part cardinality. The architecture was consequently refined to:

`G1 observations -> G2A0 co-spatial observation bundles -> G2A relation graph -> G2B CORE/CONTEXT boundary -> G2C candidate families -> Human Review -> G3 semantic attribution`

G2A0 is provenance-preserving: every bundle retains every original `primitive_id`, detector, geometry and source binding.

## G2A0 RED→GREEN and exact replay

The first TDD cycle introduced contracts for fusion of strongly co-spatial derived observations, separation of nearby distinct events, long-line exclusion from compact bundles, determinism and complete primitive-to-bundle provenance.

The G2A0 RED head `4e4d46c3d395f5c16b8c66a371185f9cac5d042b` failed causally because the two G2A0 production modules did not yet exist. After implementation the focused gate passed.

A final self-review found an Important residual: CONTEXT still inherited an artificial `[:20]` presentation truncation. A second TDD cycle produced exact RED `20 != 25` on head `39f53ab067ac6cf6f0b32c95d7b624909ef69ea7`; the cap was removed and the G2A0 and Repository Memory gates returned GREEN.

The final exact `5,633`-primitive G2A0 replay was byte-identical across two runs, SHA-256:

`4058b10dcb31594ed345bda3a8f900f0b412e5d5a8f5eed1296b875dee700858`

| Candidate | Raw CORE observations | G2A0 CORE bundles | Recoverable original CORE observations | Preserved CONTEXT bundles |
|---|---:|---:|---:|---:|
| C1 | 3 | 3 | 3 | 33 |
| C2 | 24 | 5 | 45 | 47 |
| C3 | 1 | 1 | 1 | 30 |
| C4 | 2 | 2 | 2 | 34 |
| C5 | 1 | 1 | 1 | 16 |
| C6 | 24 | 5 | 29 | 50 |
| C7 | 4 | 4 | 4 | 28 |
| C8 | 10 | 10 | 10 | 39 |

This established that graph composition must operate on provenance-preserving bundles rather than raw G1 cardinality.

## G2B bounded boundary experiment

G2B was then executed only on the same eight frozen candidates. It does not change G2A0 bundles and does not add meaning. It can only retain an incoming CORE bundle or move it into CONTEXT.

The experimental neutral rules are intentionally narrow:

- seed bundle always remains CORE;
- a non-seed bundle related to the seed only by `NEAR` moves to CONTEXT;
- line-only bundles whose major span exceeds `2.0 ×` the seed major span move to CONTEXT;
- non-seed `RECTILINEAR_CLOSED_SHAPE` or `COMPLEX_GRAPHIC_GROUP` bundles move to CONTEXT when area exceeds `1.8 ×` seed area or major span exceeds `1.6 ×` seed major span;
- compact directly contacting derived-event bundles remain CORE;
- moved bundles and all their original primitive IDs remain explicitly preserved in CONTEXT.

These thresholds are experiment rules, not production, semantic or structural criteria.

### G2B first RED→GREEN cycle

The dedicated G2B RED head `28e99717dca4b08a6de218e880eeb2ad9a59da06` failed causally with:

`ModuleNotFoundError: No module named 'experiments.cew_b01.g2b_core_context_refinement'`

After minimal implementation, exact head `89b71d35f4ebb2aaa47e6a0ce867a82ad81e7e04` passed:

- `CEW-B01 G2B Pilot Unit Gate` — PASS;
- `CEW Repository Memory Gate` — PASS;
- `CEW-B01 G2A0 Pilot Unit Gate` — PASS.

The contracts cover NEAR-only demotion, dominant attached-line demotion, dominant closed/complex demotion, compact-contact retention, exact membership/provenance conservation, determinism and unchanged non-authority flags.

### Final self-review correction: directional relations

Final self-review found one Important issue that did not alter membership counts but would have corrupted a future G2C relational signature: when the seed was the second endpoint of a relation edge, directional relations were copied without inversion. For example, if the other bundle `CONTAINS` the seed, the relation from the seed viewpoint must be `CONTAINED_BY`.

A new test-first cycle on head `89c73ef5493d4d611233bfc84d95a5638754cad8` produced the exact RED:

`['CONTAINS', 'OVERLAPS'] != ['CONTAINED_BY', 'OVERLAPS']`

All other seven G2B contracts passed on that RED. The implementation was then corrected so `CONTAINS <-> CONTAINED_BY` is normalized from the seed viewpoint while symmetric relations remain unchanged. On fix head `5e339fa96350cdb8501b835c9fee3ebb0f247615`, G2B, G2A0 and Repository Memory all passed.

### Final exact real-source G2B replay

Two post-fix executions over the exact G2A0 result were byte-identical. Final replay SHA-256:

`5a10ac1aa57411a239e10dfbcf63fd5e1cb836884fc85cb5851b6396fa7701a1`

The membership counts are unchanged by the directional correction:

| Candidate | G2A0 CORE bundles | G2B nucleus bundles | Moved CORE→CONTEXT | Final CONTEXT bundles | Original observations remaining in nucleus |
|---|---:|---:|---:|---:|---:|
| C1 | 3 | 1 | 2 | 35 | 1 |
| C2 | 5 | 3 | 2 | 49 | 43 |
| C3 | 1 | 1 | 0 | 30 | 1 |
| C4 | 2 | 1 | 1 | 35 | 1 |
| C5 | 1 | 1 | 0 | 16 | 1 |
| C6 | 5 | 3 | 2 | 52 | 27 |
| C7 | 4 | 1 | 3 | 31 | 1 |
| C8 | 10 | 1 | 9 | 48 | 1 |

Total moves by neutral reason:

- `DOMINANT_LINEAR_CONTEXT`: `13`;
- `NEAR_ONLY`: `5`;
- `DOMINANT_CLOSED_OR_COMPLEX_CONTEXT`: `1`.

For all eight candidates:

`incoming CORE ∪ incoming CONTEXT == G2B CORE ∪ G2B CONTEXT`

both at bundle-ID level and at expanded original-primitive level. No evidence is dropped.

The corrected replay also verifies the real reversed-containment case in C6: the dominant complex bundle is recorded from the seed viewpoint as `CONTAINED_BY + OVERLAPS`, not `CONTAINS + OVERLAPS`.

## Important G2B finding

G2B succeeds at isolating a compact local nucleus, but the eight-case result also shows why **CORE alone cannot become the G2C family descriptor**.

C1, C3, C4, C5, C7 and C8 reduce to seed-only nuclei, although their attached or nearby graphic configurations are materially different. C7 and C8 are the clearest examples: their long attached linework is correctly excluded from the compact nucleus, but it remains potentially discriminative configuration evidence.

Therefore the output of G2B must be interpreted as:

`NUCLEUS + PRESERVED CONTEXT`

not as a complete symbol definition.

A precise boundary is important here: G2B now preserves **all context bundle IDs and all original primitive provenance**, and it records normalized seed-relative relations for bundles represented by the incoming G2A0 relation graph. It does **not yet expose a complete relational descriptor for every pre-existing CONTEXT bundle**. Complete provenance must not be mistaken for a complete context-relation signature.

Accordingly, a future G2C experiment must first export or reconstruct the selected relations for the preserved attached/near CONTEXT, then combine those neutral relations with the nucleus. Otherwise distinct configurations could collapse into the same family simply because their nuclei are similar.

This remains fully pre-semantic: the descriptor may say how geometry is attached or positioned, not what that geometry means technically.

## Human review boundary

All eight G2B candidates remain `UNREVIEWED`. No automated result is allowed to assign beam/column/node/section/reinforcement or other technical meaning.

Permitted human decisions remain limited to:

- `SAME_CONFIGURATION`
- `DIFFERENT_CONFIGURATION`
- `ARTIFACT`
- `NON_SIGNIFICANT`
- `UNCERTAIN`

The micro-atlas must show the seed, retained G2B nucleus and every bundle moved from G2A0 CORE to CONTEXT so that the reviewer can judge the boundary rather than only the cropped nucleus.

## What this proves / does not prove

The bounded eight-seed evidence now supports:

1. primitive recurrence is insufficient for compound-symbol families;
2. co-spatial G1 observations require provenance-preserving G2A0 bundling;
3. G2B can isolate a compact nucleus while conserving all evidence;
4. binary nucleus membership alone is too lossy for G2C family induction;
5. directional relation evidence must be normalized from the seed viewpoint before it can participate in a neutral family descriptor.

It does **not** prove that any candidate has a particular technical or structural identity. It does not authorize G3, structural identity, canonical writes, corpus-wide generalization or merge.

## Next bounded step

Do not scale beyond these eight candidates yet.

The next permitted action is a **human configuration review of the G2B micro-atlas**, followed by a neutral G2C descriptor experiment only if the review supports the boundaries. Before G2C comparison, the experiment must make the selected preserved-CONTEXT relations explicit. The future descriptor may then combine:

- G2B nucleus topology/proportions;
- attached-context relation signature;
- near-context signature where relevant;
- full provenance links back to G2A0/G1.

No semantic label enters before that review.
