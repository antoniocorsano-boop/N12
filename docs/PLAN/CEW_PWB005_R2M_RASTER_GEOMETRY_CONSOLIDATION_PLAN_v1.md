# CEW PWB-005 — R2M Raster Geometry Consolidation Plan v1

Status: `IMPLEMENTATION_NON_AUTHORITATIVE`

## Purpose

R2A/R2B produced 230 line candidates stable across 200 and 300 dpi. R2Q proved that the set is reproducible but still contains substantial geometric redundancy and fragmentation. R2M consolidates only geometrically compatible candidates before any R2C scene decision.

R2M is not semantic reconstruction. It must not infer beams, columns, axes, dimensions, text, nodes, spans, reinforcement or any other engineering identity.

## Inputs

Same-revision artifacts from:

- `CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1`
- `CEW_PWB005_R2Q_RASTER_GEOMETRY_QUALITY_v1`

All four governed EvidenceRegions must be present.

## Consolidation model

Every R2 `RasterGeometryCandidate` is assigned to exactly one R2M support group. No R2 candidate may disappear and no consolidated candidate may exist without at least one R2 support id.

Two R2 lines may enter the same consolidation group only when all of the following are satisfied:

1. acute orientation difference <= `2.0 deg`;
2. perpendicular separation of both line midpoints from the comparison line <= `0.006` in EvidenceRegion normalized coordinates;
3. projected intervals overlap or their normalized gap <= `0.012`;
4. grouping is complete-link: the candidate must satisfy the compatibility rule against every existing group member. Transitive chaining alone is insufficient.

The consolidated line uses the longest support line as deterministic reference direction. All support endpoints are projected onto that reference; the output endpoints span the minimum and maximum projection while the perpendicular offset is the length-weighted mean of support midpoints.

This is a geometric working artifact only.

## Provenance and information preservation

Each consolidated candidate stores:

- its EvidenceRegion, SourceVersion, Page and Transform identity;
- all contributing R2 `candidate_id` values;
- support count;
- source candidate geometries remain available in the R2 artifact;
- normalized output geometry and mapped `SOURCE_PAGE_PT` geometry;
- deterministic consolidation id derived from the sorted support ids.

Required invariants:

`R2_SUPPORT_RETENTION = 100%`

`ONE_R2_CANDIDATE_TO_ONE_R2M_GROUP = true`

`R2M_WITHOUT_R2_SUPPORT = forbidden`

## Diagnostics

For each EvidenceRegion R2M reports:

- R2 input candidate count;
- consolidated candidate count;
- reduction ratio;
- number of multi-support groups;
- maximum support count per group;
- singleton count;
- total support ids retained;
- endpoint connectivity of consolidated geometry;
- orientation distribution after consolidation.

These metrics do not by themselves authorize R2C.

## Authority boundary

`SEMANTIC_CLASSIFICATION = UNASSIGNED`

`R2C_SCENE_ADAPTER_AUTHORIZED = false`

`TECHNICAL_IDENTITY_AUTHORIZED = false`

`STRUCTURAL_IDENTITY_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`

`ENGINEERING_AUTHORITY_EFFECT = NONE`

R2M cannot modify canonical CEW/N12 records and cannot become a structural or professional decision by passing an automated gate.
