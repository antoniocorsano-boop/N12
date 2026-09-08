# CEW PWB-005 — R2S Raster Support & Gap Continuity Diagnostic Plan v1

Status: `IMPLEMENTATION_DIAGNOSTIC_ONLY`

## Purpose

R2A/R2B found 230 multi-scale line candidates. R2M conservatively consolidated them to 179 while retaining 100% of R2 support. R2T then showed that most consolidated candidates in the TAV-05A regions are geometrically isolated.

R2S determines whether that isolation is primarily an extraction-fragmentation effect or is actually supported by the underlying raster. It does this without adding, deleting, extending, merging or semantically classifying any line.

## Inputs

Same-revision artifacts:

- `CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1`
- `CEW_PWB005_R2M_RASTER_GEOMETRY_CONSOLIDATION_v1`
- `CEW_PWB005_R2T_TOPOLOGY_COHERENCE_v1`
- the exact 200 dpi and 300 dpi EvidenceRegion crops produced by R2.

All raster inputs are verified by the SHA-256 values already bound into the R2 manifest.

## Raster support measurement

For each R2M line and for each scale:

1. load the exact grayscale crop;
2. compute an Otsu threshold from the crop histogram; no OCR is performed;
3. sample the normalized line at deterministic positions;
4. at each sample inspect a small perpendicular band of pixels;
5. record whether at least one pixel in the band is darker than the crop-specific threshold;
6. derive support fraction and longest continuous supported-run fraction.

Cross-scale support is reported using the minimum of the 200 dpi and 300 dpi values. R2S does not define a scene-authorization threshold.

## Gap continuity diagnostic

R2S also inspects only pairs of R2M lines that are geometrically plausible continuations:

- acute angle difference <= `3.0 deg`;
- mutual perpendicular midpoint separation <= `0.008` normalized units;
- projected positive gap > 0 and <= `0.05` normalized units.

For each such pair R2S samples the straight bridge between the nearest endpoints on both raster scales and reports the cross-scale support of that gap.

A supported gap remains a `GapContinuityHypothesis`. It is not automatically converted into geometry.

## Required outputs

Per EvidenceRegion:

- line count;
- per-line 200/300 support fraction;
- per-line 200/300 longest-run fraction;
- cross-scale minimum support metrics;
- distribution of cross-scale support;
- count of plausible continuation pairs;
- per-gap cross-scale support metrics;
- distribution of gap support;
- exact raster SHA identity used.

## Authority boundary

`OCR_USED = false`

`RASTER_SUPPORT_IS_TECHNICAL_IDENTITY = false`

`GAP_HYPOTHESIS_IS_GEOMETRY = false`

`R2C_SCENE_ADAPTER_AUTHORIZED = false`

`STRUCTURAL_IDENTITY_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`

R2S is a derived, non-authoritative diagnostic. It cannot modify CEW/N12 canonical records or authorize professional engineering interpretation.
