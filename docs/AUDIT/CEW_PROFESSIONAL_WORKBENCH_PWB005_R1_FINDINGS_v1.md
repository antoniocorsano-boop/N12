# CEW Professional Workbench — PWB-005-R1 Findings v1

Status: `R1_COMPLETE_VERIFIED_RASTER_4_OF_4`

Initial verified candidate: `12582d0ccbd87de0e6c96bbe1ca33b76ccb59c72`

R1A-remediated verified candidate: `ddfd5826893702c3fc1299cde38c81bd7530b47a`

## Final automated evidence

On the R1A-remediated exact candidate SHA, the B1 Professional Workbench workflow completed successfully through:

- governed document-geometry build and guards;
- R1 EvidenceRegion content diagnostic v1.1;
- R1A mapping root-cause diagnostic;
- Workbench kernel/runtime smoke;
- evidence viewer interaction;
- HVA/promotion fail-closed gates.

The diagnostic covered all four governed READY EvidenceRegions and preserved:

`canonical_write_authorized=false`

`engineering_authority_effect=NONE`

`hva_execution_authorized=false`

## R1A correction basis

The initial R1 run classified `G01-R06` and `G07-R07` as `REGION_MAPPING_ERROR` because it compared rectangle areas with an absolute `1e-6 pt²` threshold.

R1A proved for both regions:

- Page Registry present;
- SourceVersion identity matches;
- page index is valid;
- actual/expected page dimensions match;
- normalized bbox is valid;
- edge overhang is exactly `0` on left/top/right/bottom;
- edge-tolerant containment at `0.01 pt` passes;
- only the floating-point intersection-area calculation caused the strict predicate to fail.

R1A root cause for both cases:

`FLOATING_POINT_CONTAINMENT_TOLERANCE`

No Page, EvidenceRegion, transform or source record was changed. R1 v1.1 now uses explicit source-page edge containment with tolerance `0.01 pt`.

## Final region findings

| EvidenceRegion | Classification | PDF drawings | PDF text spans | Embedded images | Image coverage | Ink ratio |
|---|---|---:|---:|---:|---:|---:|
| `CEW-N12-REG-G01-R06` | `RASTER` | 0 | 0 | 1 | 1.0 | 0.90841616 |
| `CEW-N12-REG-G05-R04` | `RASTER` | 0 | 0 | 1 | 1.0 | 0.90623050 |
| `CEW-N12-REG-G07-R07` | `RASTER` | 0 | 0 | 1 | 1.0 | 0.90465976 |
| `CEW-N12-REG-T6A-G03` | `RASTER` | 0 | 0 | 1 | 1.0 | 0.90273260 |

Final classification totals:

- `RASTER = 4`
- `REGION_MAPPING_ERROR = 0`
- `VECTOR = 0`
- `TEXT = 0`
- `MIXED = 0`
- `EMPTY = 0`

## Interpretation

The four governed regions are portions of embedded raster imagery, not native PDF vector/text content.

Therefore the old Dual Vector outcome (`0` PyMuPDF segments and `0` Docling segments) is not evidence of four geometric conflicts. It is evidence that the governed reading regions contain no comparable native vector segments.

No `DocumentGraphicPrimitive` is authorized from Dual Vector Agreement for these four cases. Zero technical primitives have been published.

## Governance consequence

`PWB-005` remains `PARTIAL` and remains a **P0 blocker**.

The Workbench now has a proven chain:

`SourceVersion -> Page -> READY EvidenceRegion -> verified raster content diagnostic`

but it does not yet have usable technical-document geometry for these real cases.

## Required next work — R2

All four governed regions are eligible for **Raster Geometry Candidate Extraction**.

R2 may create derived candidate geometry only. Every candidate must retain:

- SourceVersion and source SHA-256;
- Page and EvidenceRegion identity;
- crop hash and rendering parameters;
- extraction algorithm/version;
- candidate coordinates in an explicit source/crop coordinate space;
- candidate confidence/stability evidence;
- `technical_identity_authorized=false`;
- `canonical_write_authorized=false`.

R2 must not infer beams, columns, reinforcement or structural identity from image geometry alone.

## Gates

`PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED`

`PWB-005 = PARTIAL_BLOCKED`

`R1_RASTER_REGION_COVERAGE = 4/4`

`HVA_EXECUTION_AUTHORIZED = false`

`B1_PROMOTION_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`
