# CEW PWB-005 — R2T Topology Coherence Diagnostic Plan v1

Status: `IMPLEMENTATION_DIAGNOSTIC_ONLY`

## Purpose

R2M reduced the multi-scale raster candidates from 230 to 179 while retaining every R2 support id. Endpoint-only connectivity decreased after consolidation, but that metric does not capture crossings or contacts occurring along the interior of a line. R2T measures the geometric topology of the consolidated set before any R2C preview decision.

R2T does not infer structural topology. A geometric intersection is not a structural node and a connected component is not a structural system.

## Inputs

Same-revision artifacts:

- `CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1`
- `CEW_PWB005_R2Q_RASTER_GEOMETRY_QUALITY_v1`
- `CEW_PWB005_R2M_RASTER_GEOMETRY_CONSOLIDATION_v1`

## Geometric topology metrics

For each EvidenceRegion:

- consolidated line count;
- exact segment-intersection pair count;
- near-contact pair count within normalized distance `0.004`;
- graph edge count;
- connected component count;
- largest component size and fraction;
- isolated candidate count and fraction;
- mean and maximum geometric graph degree;
- distribution of R2 support stability scores carried by R2M groups;
- residual pair count satisfying the conservative R2M collinearity/contact rule but left in different complete-link groups.

The graph is purely geometric and EvidenceRegion-local.

## Interpretation boundary

R2T can establish whether the candidate geometry behaves like a coherent geometric network or a collection of isolated fragments. It cannot decide what any line means.

Forbidden interpretations include:

- intersection = structural node;
- line = beam/column/axis/dimension;
- component = frame/system;
- geometric continuity = engineering connectivity.

## Gates

`R2T_DIAGNOSTIC_AUTHORITY = NONE`

`R2C_SCENE_ADAPTER_AUTHORIZED = false`

`TECHNICAL_IDENTITY_AUTHORIZED = false`

`STRUCTURAL_IDENTITY_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`

The subsequent R2C decision remains a separate governed action after inspection of R2Q, R2M and R2T together.
