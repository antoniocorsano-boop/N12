# CEW PWB-005 — R2RV Raster Gap Review View Plan v1

## Purpose

R2RV turns the validated R2BR review inventory into a **human inspection package**. It is a reading/review surface only.

The view MUST show the source raster crop as the visual substrate and overlay the ten R2BR `GapContinuityHypothesis` records using proposal styling. It MUST NOT convert those overlays into document geometry, technical geometry, structural geometry or canonical data.

## Inputs

R2RV consumes, on the same immutable build revision:

- R2 raster crops;
- R2BR review rows;
- source / source-version / page / transform / EvidenceRegion identity carried by the diagnostic chain.

No OCR is required and no new raster geometry extraction is performed by R2RV.

## View semantics

Each EvidenceRegion gets one standalone HTML review view plus a machine-readable JSON companion.

The source crop remains visually primary. Gap overlays are deliberately distinct from source content:

- `HIGH_CONTRAST_REVIEW`: dashed proposal line, emphasized endpoint markers;
- `STANDARD_REVIEW`: dotted proposal line, lower visual emphasis;
- `CONTROL_INCOMPLETE_REVIEW`: review-warning style if ever present.

The view includes toggles for high-priority and standard hypotheses and a table exposing:

- gap hypothesis ID;
- review tier;
- R2S support;
- longest supported run;
- negative-control support contrast;
- negative-control run contrast;
- projected gap and nearest-endpoint distance.

## Authority boundary

R2RV MUST state and encode:

- `review_view_authority = NONE`;
- `overlay_role = HUMAN_INSPECTION_PROPOSAL_ONLY`;
- `review_priority_is_correctness_threshold = false`;
- `gap_overlay_is_geometry = false`;
- `bridge_candidate_authorized = false`;
- `geometry_materialization_authorized = false`;
- `r2c_scene_adapter_authorized = false`;
- `technical_identity_authorized = false`;
- `structural_identity_authorized = false`;
- `canonical_write_authorized = false`;
- `engineering_authority_effect = NONE`.

The view may help a professional decide what to inspect first. It cannot accept a bridge and cannot mutate source or canonical records.

## Artifact handling

The generated package is uploaded by CI as a revision-bound workflow artifact. It is **not** a runtime dependency and does not introduce OpenCV into the managed application runtime.

`R2RV visual overlay != source modification != bridge acceptance != R2C != structural identity != canonical authority`
