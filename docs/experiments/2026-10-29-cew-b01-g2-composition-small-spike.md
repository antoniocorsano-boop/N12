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

## Exact small-run result

Running `experiments/cew_b01/g2_composition_small_spike.py` against the qualified `primitive-census.json` produced eight candidates:

| # | Seed primitive | Core count | Main neutral core content |
|---|---|---:|---|
| 1 | `...54769e74` | 3 | 1 closed rectilinear shape + 2 filled/hatched regions |
| 2 | `...947dc2b9` | 24 | closed shape + intersections/cross/T motifs + 3 parallel-line pairs |
| 3 | `...cd3e04a2` | 1 | closed shape only |
| 4 | `...85dd648a` | 2 | closed shape + 1 touching line segment |
| 5 | `...3acd1d9c` | 1 | closed shape only |
| 6 | `...d45f27ad` | 24 | closed shape + complex group + intersections/cross/T motifs |
| 7 | `...52aae053` | 4 | closed shape + 3 line segments |
| 8 | `...5beed9ea` | 10 | closed shape + 9 line segments |

Core-count vector: `3, 24, 1, 2, 1, 24, 4, 10`.

The strongest neutral composition similarities are:

1. candidates `3 ↔ 5`: `0.683`
2. candidates `2 ↔ 6`: `0.598`
3. candidates `7 ↔ 8`: `0.521`

These similarity values are ranking aids only. No acceptance threshold or family promotion is authorized by this spike.

## Finding

The original G2 primitive-level grouping is too coarse to stand in for a symbol family. Instances drawn from only two recurring closed-shape motifs separate into materially different local compositions once their relations are included.

Most importantly:

- two cases become dense 24-member compound configurations;
- two cases remain true singleton-like shapes;
- two cases are line-coupled compositions;
- one case is coupled to filled/hatched regions;
- one case is only a two-member shape/line composition.

Therefore `primitive -> recurring primitive motif` and `primitive -> local compound candidate` are demonstrably different layers on the real qualified TAV.5 data.

## What this proves / does not prove

This spike supports introducing a distinct experimental G2B composition layer with `CORE/CONTEXT` separation.

It does **not** prove that any candidate is a beam, column, node, section, reinforcement symbol, dimension or other technical object. It does not authorize G3, structural identity, canonical writes or merge.

## Next bounded experiment

The next useful step is not to run the whole corpus. It is to generate a human micro-atlas for these eight candidates, showing:

1. source crop;
2. CORE overlay;
3. CONTEXT ring;
4. constituent primitive IDs;
5. relation graph;
6. a human decision limited to `SAME_CONFIGURATION / DIFFERENT_CONFIGURATION / ARTIFACT / NON_SIGNIFICANT / UNCERTAIN`.

Only after that visual review should the composition rule be hardened or generalized.
