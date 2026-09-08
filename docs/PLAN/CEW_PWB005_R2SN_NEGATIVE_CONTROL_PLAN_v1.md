# CEW PWB-005 — R2SN Raster Gap Negative-Control Plan v1

Status: `IMPLEMENTATION_DIAGNOSTIC_ONLY`

## Purpose

R2S found ten geometrically plausible gap-continuity hypotheses. Their raster support cannot be interpreted safely without a local background control, because the scanned source regions have substantial dark content and nearby linework.

R2SN measures whether the raster signal on each gap is stronger than two parallel offset control paths. It does not define a pass/fail threshold and cannot create bridge geometry.

## Inputs

Same-revision artifacts:

- `CEW_PWB005_R2_RASTER_GEOMETRY_CANDIDATES_v1`
- `CEW_PWB005_R2S_RASTER_SUPPORT_CONTINUITY_v1`
- the exact 200 dpi and 300 dpi crop PNGs bound by R2 SHA-256.

The expected hypothesis inventory is exactly the R2S inventory. No new gap is discovered in R2SN.

## Negative controls

For each R2S gap and each raster scale:

1. reuse the exact R2S bridge endpoints;
2. derive the bridge perpendicular in raster-pixel coordinates;
3. sample two parallel controls at a scale-proportional offset:
   - 12 px at 200 dpi;
   - 18 px at 300 dpi;
4. use the same Otsu threshold and support sampler as R2S;
5. reject an offset side only when one of its endpoints would fall outside the exact crop;
6. require at least one valid control path per scale; otherwise the gap remains `CONTROL_INCOMPLETE`.

For each scale the conservative local control baseline is the maximum support of the valid lateral controls. The diagnostic records:

- actual support fraction;
- control support fraction;
- `support_contrast = actual - control`;
- actual longest supported-run fraction;
- control longest-run fraction;
- `run_contrast = actual_run - control_run`.

Cross-scale values use the minimum contrast across 200 and 300 dpi.

## No threshold fitting

R2SN intentionally defines no value such as `0.70` or `0.20` as sufficient for a bridge proposal. The ten real measurements must be inspected first. A later, separately versioned rule may define a bridge-candidate tier only if the measurements justify one.

## Output vocabulary

- `NEGATIVE_CONTROL_COMPLETE`
- `CONTROL_INCOMPLETE`

These states are diagnostic only.

## Authority boundary

`NEGATIVE_CONTROL_AUTHORITY = NONE`

`GAP_SUPPORT_CONTRAST_IS_GEOMETRY = false`

`R2_BRIDGE_CANDIDATE_AUTHORIZED = false`

`R2C_SCENE_ADAPTER_AUTHORIZED = false`

`TECHNICAL_IDENTITY_AUTHORIZED = false`

`STRUCTURAL_IDENTITY_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`

No CEW/N12 canonical record is changed by R2SN.
