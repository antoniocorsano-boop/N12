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

`CORE` admits nearby nonsemantic primitives only when the local relation is sufficiently strong and the primitive is not geometrically dominant. Long linework, text, dimensions/callouts and geometrically huge neighbours stay in `CONTEXT`.

The `24`-member core cap is an experiment/presentation bound only. It is not a production threshold and carries no structural meaning.

## Exact small-run result before G2A0

Running `experiments/cew_b01/g2_composition_small_spike.py` against the qualified `primitive-census.json` produced eight candidates:

| # | Seed primitive | Raw CORE count | Main neutral core content |
|---|---|---:|---|
| 1 | `...54769e74` | 3 | 1 closed rectilinear shape + 2 filled/hatched regions |
| 2 | `...947dc2b9` | 24 | closed shape + intersections/cross/T motifs + parallel-line pairs |
| 3 | `...cd3e04a2` | 1 | closed shape only |
| 4 | `...85dd648a` | 2 | closed shape + touching line segment |
| 5 | `...3acd1d9c` | 1 | closed shape only |
| 6 | `...d45f27ad` | 24 | closed shape + complex group + intersections/cross/T motifs |
| 7 | `...52aae053` | 4 | closed shape + line segments |
| 8 | `...5beed9ea` | 10 | closed shape + line segments |

Raw CORE vector: `3, 24, 1, 2, 1, 24, 4, 10`.

The strongest neutral composition similarities in the first spike were `3 ↔ 5 = 0.683`, `2 ↔ 6 = 0.598`, `7 ↔ 8 = 0.521`. These are ranking aids only. No acceptance threshold or family promotion is authorized.

## Visual finding from the first micro-atlas

Candidates `2` and `6` both hit the experimental 24-member cap, but many of those members are co-spatial or near-coincident observations such as `INTERSECTION`, `CROSS_MOTIF`, `T_JUNCTION` and `T_SHAPED_MOTIF` derived from the same local strokes.

Therefore raw G1 observation cardinality cannot be treated as physical or symbolic part cardinality. A stricter seed-relative size guard alone does not solve this because redundant derived observations remain co-located and can still inflate the candidate.

The architecture was consequently refined to:

`G1 observations -> G2A0 co-spatial observation bundles -> G2A relation graph -> G2B CORE/CONTEXT SymbolCandidate -> G2C candidate families -> Human Review -> G3 semantic attribution`

G2A0 is provenance-preserving: every bundle retains every original `primitive_id`, detector, geometry and source binding.

## G2A0 implementation and RED→GREEN evidence

The first TDD cycle introduced contracts for:

- fusion of strongly co-spatial derived observations;
- separation of nearby but distinct events;
- exclusion of a long crossing line from a compact local-event bundle;
- deterministic behavior under reversed input order;
- complete primitive-to-bundle provenance;
- expansion of candidate bundles back to original G1 primitive IDs;
- unchanged non-authority flags.

The RED head `4e4d46c3d395f5c16b8c66a371185f9cac5d042b` failed causally because the two G2A0 production modules did not yet exist. After implementation, the focused G2A0 gate and Repository Memory Gate passed.

During final self-review an Important residual was found: the new candidate builder still inherited the old presentation truncation `CONTEXT[:20]`. That contradicted the requirement that rejected nearby geometry remain explicitly available as context.

A second test-first cycle added a fixture with 25 nearby rejected context bundles. The RED head `39f53ab067ac6cf6f0b32c95d7b624909ef69ea7` failed exactly with `20 != 25`. The implementation was then corrected by removing the artificial context cap while leaving the experimental CORE cap unchanged. On fix head `966284535bfab363f9ad74a4b05361acc818f516`, both `CEW-B01 G2A0 Pilot Unit Gate` and `CEW Repository Memory Gate` passed.

## Final exact real-source replay

After the context-preservation repair, the exact `5,633`-primitive census was replayed twice. Both result files were byte-for-byte identical.

Final result SHA-256:

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

The corresponding numbers of original G1 observations recoverable from CONTEXT are `284, 325, 46, 34, 36, 410, 28, 39`.

The important interpretation is not that C2 or C6 have 45 or 29 symbolic parts. The opposite is demonstrated: many G1 observations describe the same local graphic event. G2A0 reduces the graph-node cardinality from `24 -> 5` for both saturated candidates while retaining full provenance back to the original observations.

The expanded counts also show that the old raw `24` cap had truncated membership: after coalescence, the selected bundles expand to more than 24 original G1 observations. Therefore the raw cap cannot be used as a completeness or symbolic-cardinality oracle.

## Remaining residual after G2A0

G2A0 solves observation duplication and now preserves the complete nearby context, but it does **not** by itself solve the CORE/CONTEXT boundary.

The micro-atlas still shows some large `RECTILINEAR_CLOSED_SHAPE` or `COMPLEX_GRAPHIC_GROUP` neighbours entering the candidate CORE because they overlap or touch the seed region. This is deliberately left as a separate G2B problem. Tightening G2A0 to remove those objects would mix two responsibilities: equivalence of observations and composition membership.

## What this proves / does not prove

The eight-seed experiment supports these statements:

1. primitive-level recurrence is not sufficient to define a compound symbol family;
2. graph composition should operate on provenance-preserving coalesced observations rather than raw G1 observation cardinality;
3. observations rejected from CORE must remain explicitly available as CONTEXT rather than being silently truncated.

It does **not** prove that any candidate is a beam, column, node, section, reinforcement symbol, dimension or other technical object. It does not authorize G3, structural identity, canonical writes or merge.

## Next bounded experiment

Do not scale to the full corpus yet.

Keep the same eight seeds and G2A0 bundles frozen. The next experiment is only **G2B CORE/CONTEXT boundary refinement**:

1. distinguish the local symbol nucleus from attached/overlapping long structural geometry and larger closed/complex neighbours;
2. keep every rejected neighbour explicitly in `CONTEXT`, never discard it;
3. regenerate the same eight-candidate micro-atlas;
4. compare candidate nucleus stability, context preservation and envelope growth;
5. submit the eight candidates to human review with decisions limited to `SAME_CONFIGURATION / DIFFERENT_CONFIGURATION / ARTIFACT / NON_SIGNIFICANT / UNCERTAIN`.

Only after that review should candidate-family induction be generalized beyond this eight-element pilot.
