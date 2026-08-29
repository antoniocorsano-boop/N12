# CEW Professional Workbench — PWB-005-R1 Findings v1

Status: `R1_COMPLETE_WITH_FINDINGS`

Verified candidate: `12582d0ccbd87de0e6c96bbe1ca33b76ccb59c72`

## Automated evidence

On the exact candidate SHA, all 19 repository workflows completed successfully, including:

- governed document-geometry build and guards;
- PWB-005-R1 EvidenceRegion content diagnostic;
- Workbench runtime smoke;
- evidence viewer interaction;
- candidate/runtime/governance gates.

The R1 diagnostic covered all four governed READY EvidenceRegions and preserved `canonical_write_authorized=false`, `engineering_authority_effect=NONE`, `hva_execution_authorized=false`.

## Region findings

| EvidenceRegion | Classification | PDF drawings | PDF text spans | Embedded images | Image coverage | Ink ratio |
|---|---|---:|---:|---:|---:|---:|
| `CEW-N12-REG-G01-R06` | `REGION_MAPPING_ERROR` | 0 | 0 | 0 | 0.0 | 0.90841616 |
| `CEW-N12-REG-G05-R04` | `RASTER` | 0 | 0 | 1 | 1.0 | 0.90623050 |
| `CEW-N12-REG-G07-R07` | `REGION_MAPPING_ERROR` | 0 | 0 | 0 | 0.0 | 0.90465976 |
| `CEW-N12-REG-T6A-G03` | `RASTER` | 0 | 0 | 1 | 1.0 | 0.90273260 |

Classification totals:

- `RASTER = 2`
- `REGION_MAPPING_ERROR = 2`
- `VECTOR = 0`
- `TEXT = 0`
- `MIXED = 0`
- `EMPTY = 0`

## Interpretation

The previous Dual Vector result (`0` PyMuPDF segments and `0` Docling segments in all four governed regions) must **not** be interpreted as four geometric disagreements.

R1 proves a more precise situation:

1. `G05-R04` and `T6A-G03` are document-raster regions. Their next extraction path is raster candidate analysis, not vector matching.
2. `G01-R06` and `G07-R07` are not empty: both crops have very high rendered-ink ratios, but the current Page/EvidenceRegion mapping diagnostic fails. They must not enter raster candidate extraction until the mapping failure is explained or repaired.
3. No region currently authorizes a `DocumentGraphicPrimitive` from Dual Vector Agreement; zero technical primitives were published.

## Governance consequence

`PWB-005` advances from `AVAILABLE_NOT_INTEGRATED` to `PARTIAL`, because the Workbench now has:

- governed build-time Dual Vector integration;
- exact-revision document-geometry artifact guards;
- claim-scoped EvidenceRegion diagnostics;
- real-source content classification;
- fail-closed scene materialization.

`PWB-005` remains a **P0 blocker** because usable technical-document geometry is not yet available for the four real cases.

## Required next work

### R1A — Region Mapping Root-Cause

Required for:

- `CEW-N12-REG-G01-R06`
- `CEW-N12-REG-G07-R07`

The diagnostic must expose the exact failed predicate and actual/expected page dimensions, normalized bbox, source-point bbox and clip containment. No extraction remediation is allowed before this is resolved.

### R2 — Raster Geometry Candidate Extraction

Eligible only for currently proven raster regions:

- `CEW-N12-REG-G05-R04`
- `CEW-N12-REG-T6A-G03`

R2 may create derived raster-geometry **candidates** only. Candidate geometry cannot create structural identity, technical authority or canonical writes.

## Gates

`PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED`

`PWB-005 = PARTIAL_BLOCKED`

`HVA_EXECUTION_AUTHORIZED = false`

`B1_PROMOTION_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`
