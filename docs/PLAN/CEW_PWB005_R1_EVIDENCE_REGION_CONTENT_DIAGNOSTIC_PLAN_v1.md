# CEW PWB-005-R1 — EvidenceRegion Content Diagnostic Plan v1

Status: `AUTHORIZED_IMPLEMENTATION_TRANCHE`

## Purpose

Determine what the four governed B1/F2 EvidenceRegions actually contain at PDF-document level before choosing the next extraction technology for the Professional Evidence Workbench.

This tranche does **not** infer structural identity, does not OCR, does not promote document geometry, and does not write canonical engineering data.

## Inputs

Authority chain is unchanged:

`immutable SourceVersion -> Page -> page transform -> READY EvidenceRegion`

The diagnostic consumes only:

- `CEW_SOURCE_IDENTITY_REGISTRY_v1.csv`;
- `CEW_PAGE_REGISTRY_v1.csv`;
- `CEW_EVIDENCE_REGION_REGISTRY_v1.csv`;
- immutable source PDFs at the frozen archive commit;
- the current build revision.

Target governed regions are the current four READY regions used by B1/F2:

- `CEW-N12-REG-G01-R06`;
- `CEW-N12-REG-G05-R04`;
- `CEW-N12-REG-G07-R07`;
- `CEW-N12-REG-T6A-G03`.

## Deterministic classification vocabulary

Each region receives exactly one primary classification:

- `VECTOR` — vector drawing content is present and no competing raster/text content class dominates;
- `RASTER` — embedded raster content or non-empty rendered content is present without vector/text objects;
- `TEXT` — PDF text objects are present without vector/raster objects;
- `MIXED` — two or more of vector, raster, and text signals are present;
- `REGION_MAPPING_ERROR` — Page Registry / actual PDF dimensions / normalized region mapping are inconsistent;
- `EMPTY` — no vector, raster, text, or meaningful rendered-ink signal is found.

The classification is diagnostic evidence only. It does not authorize scene materialization or technical identity.

## Measurements per region

The build records:

1. immutable source identity and SHA-256;
2. page identity, page index and actual PDF dimensions;
3. Page Registry expected dimensions and dimensional delta;
4. normalized and PDF-point region rectangles;
5. intersecting PyMuPDF drawing-path count and drawing-item count;
6. PDF text span count, character count and a bounded text preview;
7. intersecting embedded-image count and approximate region coverage;
8. deterministic grayscale crop at 150 dpi;
9. crop SHA-256, pixel dimensions and rendered ink ratio;
10. classification and classification signals.

No OCR is used in R1. A raster region therefore remains raster evidence; text inside pixels is not silently converted into recognized text.

## Mapping gate

`NORMALIZED_0_1 -> SOURCE_PAGE_PT` is accepted only when:

- the EvidenceRegion belongs to the same SourceVersion and Page;
- Page Registry dimensions match actual immutable PDF dimensions within 0.5 pt;
- the normalized rectangle is within `[0,1]` bounds;
- the mapped PDF rectangle is non-empty and lies inside the actual page.

Any violation produces `REGION_MAPPING_ERROR` and zero downstream interpretation.

## Artifact

Build-only output:

`.cew_evidence_region_content_diagnostic/`

containing:

- `manifest.json` exact-revision-bound;
- one JSON result per governed EvidenceRegion;
- one diagnostic PNG crop per governed EvidenceRegion.

Artifacts are derived diagnostics, not repository authority and not canonical data.

## Exit criteria

R1 is complete when CI proves on one exact SHA that:

- source coverage is 4/4 and governed region coverage is 4/4;
- every region has exactly one allowed classification;
- crop and result hashes are reproducible and recorded;
- Page/EvidenceRegion provenance is complete;
- no canonical write or engineering-authority effect exists;
- the result is sufficient to select the next R2 path.

## R2 decision table

- `VECTOR` -> improve/extend vector primitive extraction and matching.
- `RASTER` -> introduce raster-geometry **candidate** extraction, never automatic structural identity.
- `TEXT` -> introduce recognized-text/dimension candidate extraction.
- `MIXED` -> compose vector + raster + text candidate layers with separate provenance.
- `REGION_MAPPING_ERROR` -> repair provenance/transform before any extraction work.
- `EMPTY` -> inspect region localization/source selection; do not fabricate content.

## Authority invariants

`document diagnostic != technical candidate != structural identity`

`crop != source authority`

`classification != engineering decision`

`CANONICAL_WRITE_AUTHORIZED = false`

`HVA_EXECUTION_AUTHORIZED = false`

`B1_PROMOTION_AUTHORIZED = false`
