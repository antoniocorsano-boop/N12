# CEW PWB-005-R1A — Region Mapping Root-Cause Plan v1

Status: `AUTHORIZED_DIAGNOSTIC_TRANCHE`

## Purpose

Explain, without modifying canonical data, why PWB-005-R1 classified:

- `CEW-N12-REG-G01-R06` as `REGION_MAPPING_ERROR`;
- `CEW-N12-REG-G07-R07` as `REGION_MAPPING_ERROR`.

R1A is diagnostic only. It must not repair Page, EvidenceRegion, transform or source records automatically.

## Authority chain

`immutable SourceVersion -> Page -> page transform -> READY EvidenceRegion`

R1A reads the same immutable source material used by R1 and evaluates the exact mapping predicates against the actual PDF page.

## Predicates recorded

For every governed region, and especially the two R1 mapping-error regions, R1A records:

1. Page Registry row present;
2. source-version identity match;
3. page index in actual PDF range;
4. expected vs actual PDF width/height;
5. width/height deltas;
6. normalized bbox validity;
7. mapped source-point rectangle;
8. page rectangle including origin;
9. rectangle area and page-intersection area;
10. intersection-area deficit;
11. left/top/right/bottom edge overhang in PDF points;
12. strict R1 containment predicate;
13. edge-tolerant containment predicate at `0.01 pt`;
14. reproduced root-cause classification.

## Root-cause vocabulary

- `PAGE_REGISTRY_ROW_MISSING`
- `SOURCE_VERSION_MISMATCH`
- `PAGE_INDEX_OUT_OF_RANGE`
- `PAGE_DIMENSION_MISMATCH`
- `NORMALIZED_REGION_OUT_OF_BOUNDS`
- `FLOATING_POINT_CONTAINMENT_TOLERANCE`
- `SOURCE_REGION_OUTSIDE_PAGE`
- `NO_MAPPING_ERROR_REPRODUCED`

`FLOATING_POINT_CONTAINMENT_TOLERANCE` is allowed only when the strict R1 containment test fails but all geometric edge overhangs are within `0.01 pt` and every preceding provenance predicate is valid.

## Artifact

Build-only output:

`.cew_evidence_region_mapping_root_cause/manifest.json`

The artifact is exact-revision-bound and contains no repaired coordinates.

## Decision gate

- If root cause is `FLOATING_POINT_CONTAINMENT_TOLERANCE`, R1 may be corrected by replacing its area-based strict containment check with a documented point-tolerance containment predicate. Canonical Page/EvidenceRegion data must remain unchanged.
- If root cause is any registry, identity, dimension, normalized-bbox or material outside-page failure, extraction work stops for that region until the provenance problem is fixed through the CEW evidence-governance path.
- If `NO_MAPPING_ERROR_REPRODUCED`, the R1 implementation itself is inconsistent and must be investigated before R2.

## Invariants

`DIAGNOSTIC != PROVENANCE_REPAIR`

`VIEWPORT/RENDER COORDINATES != SOURCE GEOMETRY`

`CANONICAL_WRITE_AUTHORIZED = false`

`HVA_EXECUTION_AUTHORIZED = false`

`B1_PROMOTION_AUTHORIZED = false`
