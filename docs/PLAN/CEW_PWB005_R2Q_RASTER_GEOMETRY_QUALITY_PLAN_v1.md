# CEW PWB-005 — R2Q Raster Geometry Quality Diagnostic Plan v1

Status: `IMPLEMENTATION_DIAGNOSTIC_ONLY`

## Purpose

R2A/R2B proved that all four governed raster EvidenceRegions contain line candidates that recur at 200 and 300 dpi. R2Q measures the geometric quality of those candidates before any R2C Technical Scene materialization.

R2Q is deliberately diagnostic. It does not delete, merge, classify, promote, or materialize a candidate.

## Inputs

Same-build artifacts from `CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1` for:

- `CEW-N12-REG-G01-R06`
- `CEW-N12-REG-G05-R04`
- `CEW-N12-REG-G07-R07`
- `CEW-N12-REG-T6A-G03`

Every input candidate must remain provenance-bound to SourceVersion, Page, Transform and EvidenceRegion.

## Metrics

For each EvidenceRegion R2Q records:

- stable candidate count;
- stable/raw ratios at 200 and 300 dpi;
- normalized line-length distribution: minimum, median, p90 and maximum;
- orientation distribution: horizontal, vertical and oblique, using a 5 degree axis tolerance;
- stability-score distribution: minimum, median and p10;
- near-duplicate candidate pairs, based only on normalized geometry and angle;
- endpoint occupancy/connectivity using a deterministic normalized endpoint grid;
- total normalized line length.

The metrics are descriptive. No threshold in R2Q authorizes technical or structural identity.

## Decision boundary

R2Q may emit only:

- `QUALITY_DIAGNOSTIC_COMPLETE`
- `NO_CANDIDATES`

The subsequent R2C decision is separate and remains blocked until the diagnostic has been inspected and a versioned consolidation/materialization rule is defined.

## Authority

`R2Q_DIAGNOSTIC_AUTHORITY = NONE`

`R2C_SCENE_ADAPTER_AUTHORIZED = false`

`TECHNICAL_IDENTITY_AUTHORIZED = false`

`STRUCTURAL_IDENTITY_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`

No canonical CEW/N12 record is changed by this diagnostic.
